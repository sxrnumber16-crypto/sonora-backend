# 🚀 Sonora YouTube Audio Backend — Railway.com Deployment Guide

এই নির্দেশিকায় আপনার Python FastAPI সার্ভারটি **Railway.com**-এ সম্পূর্ণ ফ্রিতে ২৪/৭ হোস্ট করার সহজ ধাপগুলো দেওয়া হলো।

---

## 📋 প্রয়োজনীয় জিনিসপত্র (Prerequisites)

1. একটি **GitHub account**
2. একটি **Railway.com account** (GitHub দিয়ে ১-ক্লিকে লগইন করা যায়)

---

## 🛠️ ধাপ ১: GitHub-এ ব্যাকএন্ড কোড আপলোড করা

1. এই `backend/` ফোল্ডারটির সমস্ত ফাইল (অথবা পুরো Sonora Player রিপোজিটরিটি) আপনার GitHub অ্যাকাউন্টে একটি নতুন **Public/Private Repository** তৈরি করে Push করুন।
   - প্রয়োজনীয় ফাইলসমূহ:
     - `main.py`
     - `requirements.txt`
     - `nixpacks.toml`
     - `Dockerfile`
     - `Procfile`

---

## ☁️ ধাপ ২: Railway.com-এ ডেপ্লয়মেন্ট

1. [https://railway.com](https://railway.com) এ গিয়ে আপনার অ্যাকাউন্ট দিয়ে **Login** করুন।
2. Dashboard-এ **"New Project"** বাটনে ক্লিক করুন।
3. **"Deploy from GitHub repo"** নির্বাচন করুন।
4. আপনার GitHub রিপোজিটরিটি সিলেক্ট করুন।
5. যদি `backend/` একটি সাব-ডিরেক্টরিতে থাকে, তবে **Settings ➔ Root Directory** তে `backend` লিখে দিন। (যদি পুরো রিপোজিটরিই কেবল ব্যাকএন্ড হয় তবে কিছু করতে হবে না)।
6. Railway স্বয়ংক্রিয়ভাবে `nixpacks.toml` অথবা `Dockerfile` শনাক্ত করবে এবং `ffmpeg` সহ Python এনভায়রনমেন্ট ইনস্টল করে ডেপ্লয়মেন্ট শুরু করবে।

---

## 🔗 ধাপ ৩: পাবলিক ডোমেইন (Public URL) সংগ্রহ করা

1. ডেপ্লয়মেন্ট সম্পন্ন হলে (Status: **Active** বা **Success** দেখাবে), Project Dashboard ➔ **Settings**-এ যান।
2. **Networking ➔ Public Networking** সেকশনে **"Generate Domain"** বাটনে ক্লিক করুন।
3. আপনি একটি পাবলিক URL পাবেন, যেমন:
   `https://sonora-backend-production.up.railway.app`

---

## 🧪 ধাপ ৪: সার্ভার ভেরিফিকেশন (Testing)

ব্রাউজার বা Postman-এ নিচের URL-গুলো টেস্ট করুন:

1. **Health Check**:
   `https://your-railway-url.up.railway.app/health`
   ➔ রেসপন্স: `{"status": "ok"}`

2. **Search Test**:
   `https://your-railway-url.up.railway.app/api/search?q=Arijit+Singh`
   ➔ রেসপন্স: ইউটিউবের গানের তালিকা (video_id, title, thumbnail, duration)

3. **Stream Extract Test**:
   `https://your-railway-url.up.railway.app/api/stream?video_id=VIDEO_ID`
   ➔ রেসপন্স: ডাইরেক্ট অডিও স্ট্রিমিং URL (`stream_url`)

---

## 📱 ধাপ ৫: অ্যান্ড্রয়েড অ্যাপের সাথে কানেক্ট করা (Sonora Player Integration)

1. Sonora Player অ্যান্ড্রয়েড প্রজেক্টের `local.properties` ফাইলে আপনার তৈরি Railway URL-টি বসিয়ে দিন:
   ```properties
   backendUrl=https://your-railway-url.up.railway.app
   ```
2. অ্যাপটি পুনর্নির্মাণ (Rebuild) করুন। এখন আপনার Sonora Player অ্যাপটি সরাসরি এই ব্যাকএন্ড ব্যবহার করে ইউটিউবের যেকোনো গান ব্যাকগ্রাউন্ডে অডিও হিসেবে স্ট্রিম করবে!
