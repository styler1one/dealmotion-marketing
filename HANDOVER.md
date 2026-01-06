# 🎬 DealMotion Marketing Engine - Handover

> **Doel:** Automated faceless YouTube content generation voor DealMotion
>
> **Laatste update:** 6 januari 2026

---

## 📍 Project Status

| Item | Status |
|------|--------|
| **Fase** | ✅ Infrastructure Complete |
| **Focus** | Daily Pipeline Automation |
| **Stack** | Next.js + FastAPI + Inngest + Supabase |

---

## 🎉 ALLES WERKT!

| Service | Status | Test URL |
|---------|--------|----------|
| **Frontend** | ✅ Live | https://studio.dealmotion.ai |
| **Backend API** | ✅ Live | https://apistudio.dealmotion.ai |
| **ElevenLabs TTS** | ✅ Werkend | `/api/tts/generate` |
| **Google Veo 2** | ✅ Werkend | `/api/videos/test` |
| **Creatomate Render** | ✅ Werkend | `/api/render/test` |
| **YouTube Upload** | ✅ Werkend | `/api/youtube/upload` |
| **Inngest Workflows** | ✅ 3 functions synced |

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

## ✅ Completed (6 Jan 2026)

- [x] GitHub repos (code + docs)
- [x] Vercel deployment - `studio.dealmotion.ai`
- [x] Railway deployment - `apistudio.dealmotion.ai`  
- [x] Supabase database + storage
- [x] Inngest workflows (3 functions)
- [x] ElevenLabs TTS integration
- [x] Google Veo 2 video generation
- [x] Creatomate final render met captions
- [x] YouTube OAuth + upload
- [x] **Eerste video live op YouTube!**

---

## 🎯 Volgende Stappen

### Nu te doen:
1. [ ] **Daily Pipeline activeren** - Inngest cron job automatisch starten
2. [ ] **End-to-end pipeline test** - Alles achter elkaar draaien
3. [ ] **Topic → Script → TTS → Video → Render → Upload** als één flow

### Later:
4. [ ] Dashboard uitbouwen met pipeline status
5. [ ] Analytics verzamelen (views, retention)
6. [ ] Content variatie (4 types: sales_tip, ai_news, hot_take, product)
7. [ ] Self-optimization rules

---

## 🚀 Quick Start (New Session)

```
Ik wil verder werken aan de DealMotion Marketing Engine.

Lees @HANDOVER.md voor de huidige status.

Alles staat live:
- Frontend: studio.dealmotion.ai
- Backend: apistudio.dealmotion.ai
- YouTube: Dealmotion channel

Volgende stap: Daily pipeline end-to-end testen
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
