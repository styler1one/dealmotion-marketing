# 🎬 DealMotion Marketing Engine - Handover

> **Doel:** Automated faceless YouTube content generation voor DealMotion
>
> **Laatste update:** 6 januari 2026

---

## 📍 Project Status

| Item | Status |
|------|--------|
| **Fase** | Initial Setup |
| **Focus** | Cloud infrastructure opzetten |
| **Stack** | Next.js + FastAPI + Inngest (zelfde als DealMotion) |

---

## 🏗️ Architectuur

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEALMOTION MARKETING ENGINE                   │
├─────────────────────────────────────────────────────────────────┤
│  FRONTEND (Next.js 14 → Vercel)                                 │
│  ├── Dashboard        → Content overzicht & planning            │
│  ├── Topic Generator  → Interactief topics genereren            │
│  └── Settings         → API keys, schedule configuratie         │
├─────────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI → Railway)                                    │
│  ├── /api/topics      → Topic generatie endpoints               │
│  ├── /api/scripts     → Script generatie endpoints              │
│  ├── /api/videos      → Video generatie status                  │
│  └── /api/youtube     → Upload management                       │
├─────────────────────────────────────────────────────────────────┤
│  INNGEST (Workflow Orchestration)                               │
│  ├── daily-content    → Dagelijkse content pipeline             │
│  ├── generate-video   → Video generatie workflow                │
│  └── upload-youtube   → YouTube upload workflow                 │
├─────────────────────────────────────────────────────────────────┤
│  EXTERNAL SERVICES                                              │
│  ├── Anthropic Claude → Script writing                          │
│  ├── ElevenLabs       → Dutch TTS voice-over                    │
│  ├── NanoBanana       → AI video generation                     │
│  └── YouTube API      → Video uploads                           │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  └── Supabase         → Content tracking, settings              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder Structuur

```
dealmotion-marketing/
├── frontend/                    # Next.js (Vercel)
│   ├── app/
│   │   ├── page.tsx            # Dashboard
│   │   ├── topics/             # Topic management
│   │   ├── videos/             # Video management
│   │   └── settings/           # Settings
│   └── components/
│
├── backend/                     # FastAPI (Railway)
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── routers/            # API endpoints
│   │   ├── services/           # External APIs
│   │   └── inngest/            # Inngest functions
│   └── requirements.txt
│
├── database/                    # Supabase migrations
│   └── schema.sql
│
└── docs/                        # Documentation
    └── HANDOVER.md             # This file
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14 | Dashboard UI |
| **Backend** | FastAPI | API endpoints |
| **Database** | Supabase | Content tracking |
| **Jobs** | Inngest | Scheduled content generation |
| **Hosting** | Vercel + Railway | Cloud deployment |
| **AI** | Claude | Script writing |
| **TTS** | ElevenLabs | Dutch voice-over |
| **Video** | NanoBanana | AI video generation |
| **YouTube** | YouTube API | Video uploads |

---

## 📋 Implementation Roadmap

### Phase 1: Infrastructure ⏳
- [ ] Frontend setup (Next.js + Vercel)
- [ ] Backend setup (FastAPI + Railway)
- [ ] Database setup (Supabase)
- [ ] Inngest integration

### Phase 2: Core Features
- [ ] Topic generation API
- [ ] Script generation API
- [ ] TTS integration (ElevenLabs)
- [ ] Video generation (NanoBanana)
- [ ] YouTube upload

### Phase 3: Dashboard
- [ ] Content calendar view
- [ ] Topic queue management
- [ ] Video status tracking
- [ ] Analytics

### Phase 4: Automation
- [ ] Daily content cron job
- [ ] Auto-publish workflow
- [ ] Error notifications

---

## 🔑 Required API Keys

| Service | Environment Variable | Get Key |
|---------|---------------------|---------|
| Anthropic | `ANTHROPIC_API_KEY` | console.anthropic.com |
| ElevenLabs | `ELEVENLABS_API_KEY` | elevenlabs.io |
| NanoBanana | `NANOBANANA_API_KEY` | nanobananavideo.com |
| YouTube | `YOUTUBE_CLIENT_ID/SECRET` | Google Cloud Console |
| Supabase | `SUPABASE_URL/KEY` | supabase.com |
| Inngest | `INNGEST_SIGNING_KEY` | inngest.com |

---

## 🚀 Quick Start (New Session)

```
Ik wil verder werken aan de DealMotion Marketing Engine.

Lees @HANDOVER.md voor de huidige status.

Na het lezen:
- Vat kort samen waar we zijn
- Ga verder met de volgende stap in de roadmap
```

---

## ✅ Completed

- [x] Initial project structure
- [x] Cloud architecture design (Vercel + Railway + Inngest)
- [x] FastAPI backend with routers & services
- [x] Inngest functions for automated pipeline
- [x] Database schema (Supabase)
- [x] API endpoints (topics, scripts, videos, youtube)
- [x] Frontend Next.js 14 dashboard
- [x] **Full cloud deployment**
  - [x] GitHub repos (code + docs)
  - [x] Vercel (frontend) - `studio.dealmotion.ai`
  - [x] Railway (backend) - live
  - [x] Supabase (database) - schema deployed
  - [x] Inngest (workflows) - 3 functions synced

---

## 🔄 Current Session (6 Jan 2026)

**Voltooid:**
- ✅ Backend herstructurering naar FastAPI (Railway-ready)
- ✅ Inngest integratie voor daily pipeline
- ✅ API routers: /api/topics, /api/scripts, /api/videos, /api/youtube
- ✅ Services: TopicService, ScriptService, TTSService, VideoService, YouTubeService
- ✅ Database schema met 6 tabellen
- ✅ Docs repo opgezet (dealmotion-marketing-docs)
- ✅ ChatGPT review verwerkt (guardrails, QC gates, SEO agent)
- ✅ Frontend Next.js 14 app opgezet
- ✅ **Cloud Infrastructure LIVE:**
  - GitHub: `styler1one/dealmotion-marketing` (public)
  - GitHub: `styler1one/dealmotion-marketing-docs` (private)
  - Frontend: `studio.dealmotion.ai` (Vercel)
  - Backend: `dealmotion-marketing-production.up.railway.app` (Railway)
  - Database: Supabase (schema deployed)
  - Workflows: Inngest (3 functions synced)

**Volgende stappen (Phase 2: Core Pipeline):**
1. [ ] Topic generation werkend maken
2. [ ] Script generation implementeren
3. [ ] TTS integration (ElevenLabs)
4. [ ] Video generation (NanoBanana)
5. [ ] YouTube upload (OAuth)

---

*Dit document wordt bijgehouden voor handover tussen sessies.*

