import asyncio
import os
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import yt_dlp

app = FastAPI(
    title="Sonora YouTube Audio API",
    description="FastAPI + yt-dlp backend server for Sonora Player Android App.",
    version="1.0.0",
)

# Enable CORS for mobile app requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory stream cache (video_id -> (timestamp, data))
STREAM_CACHE: Dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 7200  # 2 hours


class SearchResultItem(BaseModel):
    video_id: str
    title: str
    channel: str
    thumbnail: str
    duration_seconds: int
    duration_formatted: str


class SearchResponse(BaseModel):
    query: str
    count: int
    results: List[SearchResultItem]


class StreamResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    thumbnail: str
    duration_seconds: int
    stream_url: str
    mime_type: Optional[str] = "audio/mp4"


def format_duration(seconds: int) -> str:
    if not seconds or seconds <= 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Sonora YouTube Audio API",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


def yt_search_sync(query: str, limit: int = 15) -> List[dict]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
    }
    search_term = f"ytsearch{limit}:{query}"
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_term, download=False)
        entries = info.get("entries", []) if info else []
        for entry in entries:
            if not entry:
                continue
            video_id = entry.get("id")
            if not video_id:
                continue
            title = entry.get("title") or "Unknown Song"
            channel = entry.get("uploader") or entry.get("channel") or "YouTube Artist"
            duration = int(entry.get("duration") or 0)
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            results.append({
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "thumbnail": thumbnail,
                "duration_seconds": duration,
                "duration_formatted": format_duration(duration),
            })
    return results


def yt_extract_stream_sync(video_id: str) -> dict:
    # Check cache first
    now = time.time()
    if video_id in STREAM_CACHE:
        cached_time, cached_data = STREAM_CACHE[video_id]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "skip_download": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise Exception("Could not extract YouTube video info")

        stream_url = info.get("url")
        if not stream_url:
            formats = info.get("formats", [])
            audio_formats = [
                f for f in formats
                if f.get("vcodec") == "none" and f.get("url")
            ]
            if audio_formats:
                best_audio = max(audio_formats, key=lambda f: f.get("abr") or 0)
                stream_url = best_audio.get("url")
            elif formats:
                stream_url = formats[-1].get("url")

        if not stream_url:
            raise Exception("No playable audio stream URL found for this video")

        title = info.get("title") or "Unknown Song"
        channel = info.get("uploader") or info.get("channel") or "YouTube Artist"
        duration = int(info.get("duration") or 0)
        thumbnail = info.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        mime_type = "audio/mp4"
        if "ext=webm" in stream_url or ".webm" in stream_url:
            mime_type = "audio/webm"

        result = {
            "video_id": video_id,
            "title": title,
            "channel": channel,
            "thumbnail": thumbnail,
            "duration_seconds": duration,
            "stream_url": stream_url,
            "mime_type": mime_type,
        }

        # Store in cache
        STREAM_CACHE[video_id] = (now, result)
        return result


@app.get("/api/search", response_model=SearchResponse)
async def search_youtube(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(15, ge=1, le=50, description="Max search results"),
):
    try:
        results = await asyncio.to_thread(yt_search_sync, q, limit)
        return SearchResponse(query=q, count=len(results), results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/stream", response_model=StreamResponse)
async def get_stream_url(
    video_id: str = Query(..., min_length=1, description="YouTube Video ID"),
):
    try:
        data = await asyncio.to_thread(yt_extract_stream_sync, video_id)
        return StreamResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {str(e)}")


@app.get("/api/stream/{video_id}", response_model=StreamResponse)
async def get_stream_url_path(video_id: str):
    return await get_stream_url(video_id=video_id)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
