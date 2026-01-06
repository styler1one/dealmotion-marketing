# 🎬 DealMotion Marketing Engine

Automated faceless YouTube content generation for DealMotion.

## Features

- 🤖 AI-powered topic & script generation
- 🎙️ Text-to-speech voice-overs (Dutch)
- 🎬 Automated video creation
- 📺 YouTube upload automation
- ⚡ Daily content pipeline

## Tech Stack

| Component | Technology | Hosting |
|-----------|------------|---------|
| **Frontend** | Next.js 14 | Vercel |
| **Backend** | FastAPI | Railway |
| **Database** | PostgreSQL | Supabase |
| **Jobs** | Inngest | Cloud |
| **AI** | Claude, ElevenLabs, NanoBanana | - |

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/topics/generate` | POST | Generate topic ideas |
| `/api/scripts/generate` | POST | Generate video scripts |
| `/api/videos/generate` | POST | Trigger video creation |
| `/api/youtube/upload` | POST | Upload to YouTube |

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# AI
ANTHROPIC_API_KEY=

# Text-to-Speech
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=

# Video Generation
NANOBANANA_API_KEY=

# YouTube
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=

# Database
SUPABASE_URL=
SUPABASE_ANON_KEY=

# Inngest
INNGEST_SIGNING_KEY=
```

## Project Structure

```
dealmotion-marketing/
├── backend/
│   ├── app/
│   │   ├── routers/      # API endpoints
│   │   ├── services/     # Business logic
│   │   └── inngest/      # Workflow functions
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js pages
│   └── components/       # React components
├── database/
│   └── schema.sql        # Supabase schema
└── assets/
    ├── fonts/
    ├── music/
    └── templates/
```

## License

Proprietary - DealMotion

---

Built for [DealMotion](https://dealmotion.ai)
