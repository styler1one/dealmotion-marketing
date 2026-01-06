# 🎬 DealMotion Marketing Engine - Handover

> **Doel:** Automated faceless YouTube content generation voor DealMotion
>
> **Laatste update:** 7 januari 2026

---

## 📍 Project Status

| Item | Status |
|------|--------|
| **Fase** | ✅ APP COMPLETE |
| **Focus** | Fine-tuning & Optimization |
| **Stack** | Next.js + FastAPI + Inngest + Supabase |

---

## 🎉 ALLES WERKT!

| Service | Status | URL |
|---------|--------|-----|
| **Frontend** | ✅ Live | https://studio.dealmotion.ai |
| **Backend API** | ✅ Live | https://apistudio.dealmotion.ai |
| **Dashboard** | ✅ Real-time data | `/api/dashboard/*` |
| **ElevenLabs TTS** | ✅ Werkend | `/api/tts/generate` |
| **Google Veo 2** | ✅ Werkend | `/api/videos/test` |
| **Creatomate Render** | ✅ Werkend | `/api/render/test` |
| **YouTube Upload** | ✅ Werkend | `/api/youtube/upload` |
| **Inngest Workflows** | ✅ 4 functions synced |
| **Database** | ✅ Full CRUD | Topics, Scripts, Videos, Uploads |

---

## 🏗️ Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEALMOTION MARKETING ENGINE                   │
├─────────────────────────────────────────────────────────────────┤
│  FRONTEND (Next.js 14 → Vercel)                                 │
│  └── Dashboard        → studio.dealmotion.ai                    │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI → Railway)                                    │
│  ├── /api/topics      → Topic generatie (Claude)                │
│  ├── /api/scripts     → Script generatie (Claude)               │
│  ├── /api/tts         → Voice-over (ElevenLabs)                 │
│  ├── /api/videos      → Video generatie (Google Veo 2)          │
│  ├── /api/render      → Final video + captions (Creatomate)     │
│  └── /api/youtube     → YouTube upload                          │
├─────────────────────────────────────────────────────────────────┤
│  INNGEST (Workflow Orchestration)                               │
│  ├── daily-content    → Dagelijkse content pipeline (10:00)     │
│  ├── generate-video   → Video generatie workflow                │
│  └── upload-youtube   → YouTube upload workflow                 │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL SERVICES                                              │
│  ├── Anthropic Claude → Topic & Script writing                  │
│  ├── ElevenLabs       → Dutch TTS voice-over                    │
│  ├── Google Veo 2     → AI video generation (Gemini API)        │
│  ├── Creatomate       → Final render met animated captions      │
│  └── YouTube API      → Video uploads                           │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  └── Supabase         → PostgreSQL + Storage (audio/video)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Geconfigureerde API Keys (Railway)

| Service | Variable | Status |
|---------|----------|--------|
| Anthropic | `ANTHROPIC_API_KEY` | ✅ |
| ElevenLabs | `ELEVENLABS_API_KEY` | ✅ |
| ElevenLabs | `ELEVENLABS_VOICE_ID` | ✅ (Daniel) |
| Google Veo | `GOOGLE_GEMINI_API_KEY` | ✅ |
| Creatomate | `CREATOMATE_API_KEY` | ✅ |
| Creatomate | `CREATOMATE_TEMPLATE_ID` | ✅ |
| YouTube | `YOUTUBE_CLIENT_ID` | ✅ |
| YouTube | `YOUTUBE_CLIENT_SECRET` | ✅ |
| YouTube | `YOUTUBE_REFRESH_TOKEN` | ✅ |
| YouTube | `YOUTUBE_CHANNEL_ID` | ✅ |
| Supabase | `SUPABASE_URL` | ✅ |
| Supabase | `SUPABASE_ANON_KEY` | ✅ |
| Supabase | `SUPABASE_SERVICE_KEY` | ✅ |
| Inngest | `INNGEST_SIGNING_KEY` | ✅ |
| Inngest | `INNGEST_EVENT_KEY` | ✅ |

---

## 📺 YouTube Channel

| Item | Value |
|------|-------|
| **Channel** | Dealmotion |
| **Channel ID** | `UC5xiiRBpUll_umBAngD9GXg` |
| **Type** | Brand Account (privacy) |
| **Eerste Video** | https://youtube.com/shorts/Ef2CBH79VW0 |

---

## 🎬 Content Pipeline Flow

```
1. TOPIC AGENT (Claude)
   ↓ Genereert trending B2B sales topic
   
2. SCRIPT AGENT (Claude)  
   ↓ Schrijft 35-60s script met hook + CTA
   
3. TTS AGENT (ElevenLabs)
   ↓ Nederlandse voice-over → Supabase Storage
   
4. VIDEO AGENT (Google Veo 2)
   ↓ Genereert 8s background video clips
   
5. RENDER AGENT (Creatomate)
   ↓ Combineert video + audio + animated captions
   
6. YOUTUBE AGENT
   ↓ Upload naar YouTube als Short
   
7. ANALYTICS AGENT (toekomst)
   → Verzamelt metrics voor optimalisatie
```

---

## ✅ Completed (7 Jan 2026)

- [x] GitHub repos (code + docs)
- [x] Vercel deployment - `studio.dealmotion.ai`
- [x] Railway deployment - `apistudio.dealmotion.ai`  
- [x] Supabase database + storage
- [x] Inngest workflows (4 functions)
- [x] ElevenLabs TTS integration
- [x] Google Veo 2 video generation
- [x] Creatomate final render met captions
- [x] YouTube OAuth + upload
- [x] **Eerste video live op YouTube!**
- [x] Database service (full CRUD)
- [x] Dashboard API endpoints
- [x] Frontend met real-time data
- [x] Pipeline opslag in database
- [x] Viral Shorts optimalisatie (15-25 sec)
- [x] Human-centric video prompts

---

## 🎯 Volgende Stappen (Fine-tuning)

### Content Quality:
1. [ ] **Video stijl fine-tunen** - Meer specifieke scene prompts
2. [ ] **A/B test hooks** - Verschillende hook types testen
3. [ ] **Thumbnail generatie** - Automatische thumbnails

### Automation:
4. [ ] **Daily cron activeren** - 10:00 dagelijks
5. [ ] **Analytics integratie** - YouTube Analytics API
6. [ ] **Self-optimization rules** - Performance-based aanpassingen

### Dashboard:
7. [ ] **Pipeline history view** - Alle runs bekijken
8. [ ] **Video management** - Edit/delete videos
9. [ ] **Settings page** - Content mix aanpassen

---

## 🚀 Quick Start (New Session)

```
Ik wil verder werken aan de DealMotion Marketing Engine.

Lees @HANDOVER.md voor de huidige status.

De app is COMPLEET en werkt:
- Frontend: studio.dealmotion.ai (real-time dashboard)
- Backend: apistudio.dealmotion.ai (alle APIs)
- YouTube: Dealmotion channel
- Database: Supabase (alle data wordt opgeslagen)

Focus: Fine-tuning video kwaliteit en automation
```

---

## 💰 Kosten Schatting (per video)

| Service | Kosten |
|---------|--------|
| Claude (topic + script) | ~$0.01 |
| ElevenLabs (TTS) | ~$0.10 |
| Google Veo 2 (8s video) | ~$0.30 |
| Creatomate (render) | ~$0.15 |
| **Totaal per video** | **~$0.56** |
| **Maandelijks (30 videos)** | **~$17** |

---

*Dit document wordt bijgehouden voor handover tussen sessies.*
