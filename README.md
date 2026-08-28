<p align="center">
  <img src="docs/screenshots/voice-orb.png" alt="TOBI Arc Reactor Orb" width="600" />
</p>

<h1 align="center">T.O.B.I.</h1>
<h3 align="center">Total Omni Brain Intelligence</h3>

<p align="center">
  A personal AI companion and operator — built to know your projects, remember your goals,<br/>
  act on your behalf, and never ask you to repeat yourself.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js 14" />
  <img src="https://img.shields.io/badge/claude-API-D97706?style=flat-square&logo=anthropic&logoColor=white" alt="Claude API" />
  <img src="https://img.shields.io/badge/PWA-installable-5A0FC8?style=flat-square&logo=pwa&logoColor=white" alt="PWA" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-999999?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="MIT License" />
</p>

---

## What is TOBI?

TOBI is not a chatbot. It is an **operator with memory** — a personal AI system that runs on your own machine, knows your projects and goals, takes action through real tools, and proactively stays on top of things without being re-briefed every session.

The core promise: **you talk to TOBI like a co-founder who never forgets and never sleeps.**

Four pillars:

| Pillar | What it means |
|---|---|
| **Memory** | Persistent, structured knowledge of you — projects, people, goals, habits, skill gaps — injected into every response |
| **Presence** | Same brain everywhere — desktop, browser, mobile PWA, voice |
| **Initiative** | TOBI pings *you* — reminders, goal-drift nudges, morning briefings — instead of waiting to be asked |
| **Utility** | Plugs into what you actually run — calendar, email, files, browser, terminal, and your own business data |

<p align="center">
  <img src="docs/screenshots/chat-view.png" alt="TOBI Chat Interface" width="700" />
</p>

---

## Feature Overview

### Core Intelligence

- **Multi-tier LLM routing** — Claude Haiku (fast), Sonnet (brain), Opus (deep) selected automatically per request; Ollama as offline fallback
- **Persistent memory** — ChromaDB vector store + SQLite FTS5 for semantic and keyword recall across all sessions
- **Structured facts** — Automatically extracts facts from every conversation (name, location, preferences, projects, relationships) with confidence scoring and decay
- **Agentic tool-calling loop** — Claude calls real tools (search, shell, filesystem, browser, calendar, email, notes) and iterates until the task is done
- **Multi-agent coordinator** — Seven specialised agent types (researcher, coder, browser, system, communicator, analyst, generalist) routed automatically
- **Task planner** — Decomposes complex requests into subtasks, executes them in parallel where possible, and verifies quality on completion
- **Learning loop** — Tracks tool reliability, plan success rates, and common failure patterns to improve over time

### Reminders and Alarms (Phase 0)

- **Natural language reminder creation** — Say "remind me to follow up with OPES on Friday at 9am" and TOBI parses the date, creates the reminder, and delivers it when due
- **Own-voice playback** — Record a reminder in your own voice; TOBI plays back your exact words at the due time instead of a TTS summary
- **Alarm mode** — Full alarm delivery with snooze and dismiss actions via push notification
- **Recurrence** — Once, daily, weekly, weekdays, or monthly
- **Proactive delivery** — Due reminders are checked every 60 seconds and delivered as spoken or text notifications

### Proactive Engine

- **Calendar alerts** — Upcoming meeting warnings at 15 and 5 minutes
- **Email nudges** — Notifies when unread count reaches a meaningful threshold
- **Morning greeting** — Time-appropriate briefing on first interaction each day
- **Goal-drift detection** — Flags goals and skill-gaps that have not been touched in over 7 days with a candid nudge ("you said auditing was priority 1 — last touched 12 days ago")
- **Reminder delivery** — Background engine checks and fires due reminders every 60 seconds

### Daily Digest and Wake Briefing

- **Daily digest** — On-demand or scheduled: today's date, top priorities, due reminders, stale goals, and a one-sentence LLM-generated coaching insight
- **Wake briefing** — Under 120 words, spoken by TTS immediately after a morning alarm dismisses: date, top 3 priorities, reminders before noon, open mic for immediate voice input

### Voice

- **Whisper STT** — Browser microphone or terminal microphone transcribed via faster-whisper
- **Edge-TTS / Kokoro TTS** — Natural-sounding voice responses
- **Wake-word detection** — "Tobi" or "Hey Tobi" keeps the mic loop alive
- **Clap detection** — 2 claps to wake and summarise where you left off; 3 claps for status check
- **Browser voice** — Full push-to-talk in the PWA; audio streamed in chunks for low latency

### Web and Browser Automation

- **DuckDuckGo search** — Background web search without opening a browser
- **Playwright automation** — Multi-step browser tasks: fill forms, click buttons, navigate pages, upload files
- **Chrome Extension bridge** — Direct DOM access in your real Chrome session (no OCR — reads and writes the actual page)
- **Sync real sessions** — Imports Chrome cookies so Playwright inherits your logged-in state for any site

### System and File Automation

- **Full file system** — List, read, write, copy, move, search, create directories
- **Shell execution** — Run any terminal command; get output back in chat
- **Screen capture and OCR** — Screenshot the current screen; read visible text; AI vision analysis of what is on screen
- **Clipboard** — Read and write the system clipboard
- **App control** — Open, close, and query running applications (macOS AppleScript; Windows PowerShell)
- **Volume and brightness** — Set system audio and display brightness by voice

### Calendar and Email

- **Calendar.app / Google Calendar** — Read upcoming events, create new events, search by title
- **Mail.app** — Read recent emails, get unread count, send emails, search by query
- **Proactive meeting alerts** — Fires 15 and 5 minutes before any calendar event

### Development Tools

- **Claude Code integration** — Delegate coding tasks to an agentic sub-session with full file and shell access
- **Project scaffolding** — Generate project structure, boilerplate, and starter code from a description
- **Smart terminal** — Routes commands through Claude Code for safety checks and multi-step reasoning

### Notes

- **Apple Notes** — Read recent notes, search by keyword, read full note body, create new notes

### PWA — Install on Any Device

TOBI ships as a fully installable Progressive Web App:

- **Android**: Open in Chrome → menu → "Add to Home Screen" — works immediately, no Play Store needed
- **iOS**: Open in Safari → share → "Add to Home Screen" — full standalone mode, no App Store needed
- **Desktop**: Chrome or Edge → install button in address bar
- **Push notifications** — Service worker handles reminder delivery and snooze/dismiss actions even when the app is not open
- **Offline shell** — App shell caches locally so the UI loads instantly even on a slow connection

<p align="center">
  <img src="docs/screenshots/system-dashboard.png" alt="TOBI System Dashboard" width="700" />
</p>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT SURFACES                                │
│   PWA (Android / iOS / Desktop)   Chrome Extension   Desktop Overlay    │
│   Voice (mic + TTS)               Browser Push Notifications             │
└────────────────────────────┬────────────────────────────────────────────┘
                              │  HTTP / WebSocket (streaming)
┌────────────────────────────▼────────────────────────────────────────────┐
│                       TOBI BACKEND  (FastAPI + Python)                   │
├──────────────────┬───────────────────┬───────────────────┬──────────────┤
│   Brain          │   Agent Layer     │   Memory Layer    │  Proactive   │
│                  │                   │                   │  Engine      │
│  LLM routing     │  Task planner     │  ChromaDB vectors │              │
│  (fast/brain/    │  Multi-agent      │  SQLite FTS5      │  Reminders   │
│   deep / Ollama) │  coordinator      │  Fact extraction  │  Goal drift  │
│  Tool-use loop   │  Executor + QA    │  Preferences      │  Calendar    │
│  Streaming       │  Learning loop    │  Reminders store  │  Email       │
├──────────────────┴───────────────────┴───────────────────┴──────────────┤
│                           TOOL LAYER  (99 tools)                         │
│  shell  filesystem  screen  web_search  web_browse  weather  browser    │
│  calendar_email  notes_access  claude_code  chrome_extension             │
│  mac_control  windows_control  reminder_tools                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, WebSockets |
| LLM | Anthropic Claude API (Haiku / Sonnet / Opus) + Ollama fallback |
| STT | faster-whisper, Moonshine ONNX |
| TTS | Kokoro, Edge-TTS |
| Wake word | OpenWakeWord |
| Memory | ChromaDB (vector), SQLite + FTS5, JSON facts |
| Browser automation | Playwright, Chrome Extension (DOM bridge) |
| Frontend | Next.js 14, React 18, Three.js, Tailwind CSS v4 |
| PWA | Web App Manifest, Service Worker, Web Push API |

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)
- `ffmpeg` on your PATH (used for audio format conversion)

### 1. Clone and configure

```bash
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

# Copy the example env file and fill in your API key
cp .env.example .env
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt

# Optional: install dev tools (pytest, ruff, etc.)
pip install -r requirements-dev.txt
```

### 3. Install and build the frontend

```bash
cd Tobi/ui/tobi-ui
npm install
```

### 4. Run

**Backend** (in one terminal):

```bash
# From the repo root
python -m Tobi.main --mode server
# API runs on http://localhost:8741
```

**Frontend** (in a second terminal):

```bash
cd Tobi/ui/tobi-ui
npm run dev
# UI runs on http://localhost:3741
```

Open **http://localhost:3741** in your browser.

### Windows shortcut

```batch
setup.bat   :: first time only
start.bat   :: every time after
```

### macOS / Linux shortcut

```bash
chmod +x setup.sh && ./setup.sh   # first time only
./start.sh full                    # every time after
```

### Installing as a PWA

**Android** — open `http://localhost:3741` in Chrome, tap the menu, tap "Add to Home Screen"

**iOS** — open in Safari, tap the share icon, tap "Add to Home Screen"

**Desktop** — look for the install icon in the Chrome / Edge address bar

---

## Run Modes

The Python backend supports four modes:

| Mode | Command | Description |
|---|---|---|
| `server` | `python -m Tobi.main --mode server` | HTTP + WebSocket API only (for PWA / browser use) |
| `voice` | `python -m Tobi.main --mode voice` | Terminal voice loop (mic in, TTS out) — no server |
| `text` | `python -m Tobi.main --mode text` | Plain terminal chat — no voice, no server |
| `full` | `python -m Tobi.main --mode full` | Server + voice loop together (recommended for desktop) |

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Model tiers (defaults shown)
CLAUDE_FAST_MODEL=claude-haiku-4-5-20251001
CLAUDE_BRAIN_MODEL=claude-sonnet-4-6
CLAUDE_DEEP_MODEL=claude-opus-4-6

# Cost alerts (USD)
COST_DAILY_ALERT=2.00
COST_MONTHLY_ALERT=60.00

# Voice
WHISPER_MODEL=base.en
TTS_ENGINE=edge-tts
TTS_VOICE=af_heart
WHISPER_LANGUAGE=en

# Authentication PIN (auto-generated if not set)
TOBI_PIN=1234

# Ports
API_PORT=8741
UI_PORT=3741

# Ollama fallback (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# ElevenLabs (optional, higher-quality voice)
ELEVENLABS_API_KEY=your-key-here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Web Push (optional, for server-sent push notifications)
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_EMAIL=mailto:you@example.com
```

---

## Memory System

TOBI maintains memory across four layers that compound over time:

| Layer | Storage | What lives here |
|---|---|---|
| Active context | RAM | Current conversation turns (last 100) |
| Semantic recall | ChromaDB | Past conversation chunks, retrieved by embedding similarity |
| Structured facts | SQLite + JSON | Extracted knowledge: name, location, projects, goals, preferences, relationships — with confidence scores and decay |
| Fast keyword lookup | SQLite FTS5 | Tasks, notes, and memories indexed for instant text search |

Facts are extracted automatically from every conversation using pattern matching (high confidence) and Haiku-assisted extraction (lower confidence). They decay slowly when not reinforced, so stale facts fade out naturally.

---

## Reminders

Reminders are created by voice or text:

> *"Remind me to follow up with the client on Friday at 2pm"*
> *"Set a daily alarm for 7am"*
> *"Remind me to deploy the contract before EOD — make it urgent"*

Each reminder stores:

- Content text
- Due timestamp
- Recurrence rule (once / daily / weekly / weekdays / monthly)
- Alarm flag (full alarm vs. soft notification)
- Optional voice recording for own-voice playback
- Playback mode (`tobi_voice` generates TTS; `own_voice` plays your original recording back verbatim)

The proactive engine checks for due reminders every 60 seconds and delivers them as spoken alerts or push notifications. Recurring reminders automatically advance to the next occurrence after firing.

---

## Project Structure

```
Tobi/
├── Tobi/
│   ├── main.py               — Entry point (text / voice / server / full modes)
│   ├── agent/
│   │   ├── coordinator.py    — Multi-agent router (7 specialised agents)
│   │   ├── executor.py       — Agentic tool-use loop with QA verification
│   │   ├── learning.py       — Tool reliability and plan success tracking
│   │   ├── planner.py        — Task decomposition into subtasks
│   │   ├── reminder_tools.py — Reminder tool schemas and async handlers
│   │   └── tools_schema.py   — Master tool registry (99 tools)
│   ├── config/
│   │   └── settings.py       — All configuration with env var overrides
│   ├── core/
│   │   ├── brain.py          — Central orchestrator wiring all subsystems
│   │   ├── digest.py         — Daily digest and morning wake briefing
│   │   ├── llm.py            — Multi-backend LLM engine with streaming
│   │   ├── proactive.py      — Background engine for reminders and nudges
│   │   └── server.py         — FastAPI HTTP + WebSocket server
│   ├── extensions/
│   │   └── chrome/           — Chrome Extension (DOM bridge)
│   ├── memory/
│   │   ├── conversation_store.py  — SQLite-backed conversation history
│   │   ├── facts.py               — Fact extraction with confidence scoring
│   │   ├── preferences.py         — Implicit preference learning
│   │   ├── reminders_store.py     — Reminders SQLite table and CRUD
│   │   ├── sqlite_store.py        — Tasks, notes, memories (FTS5)
│   │   └── store.py               — MemoryStore (ChromaDB + SQLite)
│   ├── tools/
│   │   ├── browser_agent.py  — Playwright browser automation
│   │   ├── calendar_email.py — Calendar.app and Mail.app integration
│   │   ├── chrome_extension.py — Chrome DOM bridge tools
│   │   ├── claude_code.py    — Claude Code sub-agent delegation
│   │   ├── filesystem.py     — File system tools
│   │   ├── mac_control.py    — macOS app and system control
│   │   ├── notes_access.py   — Apple Notes integration
│   │   ├── screen.py         — Screenshot and OCR
│   │   ├── shell.py          — Shell command execution
│   │   ├── weather.py        — Weather via Open-Meteo
│   │   ├── web_browse.py     — Page fetching and link extraction
│   │   ├── web_search.py     — DuckDuckGo search
│   │   └── windows_control.py — Windows app and system control
│   ├── ui/
│   │   └── tobi-ui/          — Next.js 14 frontend
│   │       ├── public/
│   │       │   ├── manifest.json   — PWA manifest
│   │       │   ├── sw.js           — Service worker
│   │       │   └── icon-*.png      — App icons (72–512px)
│   │       └── src/
│   │           ├── app/            — Next.js App Router
│   │           ├── components/
│   │           │   ├── auth/       — Login screen
│   │           │   ├── chat/       — Chat view
│   │           │   ├── cinematic/  — Arc Reactor voice orb (Three.js)
│   │           │   ├── dashboard/  — System stats dashboard
│   │           │   ├── memory/     — Daily digest + facts panel
│   │           │   ├── reminders/  — Reminders management panel
│   │           │   ├── settings/   — Settings panel
│   │           │   └── shared/     — Status bar, toasts, plan progress
│   │           ├── hooks/          — React hooks (auth, WebSocket, API, push)
│   │           └── lib/            — TypeScript types
│   └── voice/
│       ├── listener.py       — Microphone + wake word + STT pipeline
│       └── speaker.py        — TTS + audio output pipeline
├── desktop-overlay/          — macOS Swift overlay (Arc Reactor HUD)
├── docs/                     — Screenshots and architecture docs
├── templates/prompts/        — YAML task templates for the agent
├── tests/                    — pytest test suite
├── .env.example              — Environment variable reference
├── requirements.txt          — Python dependencies
├── setup.bat / setup.sh      — One-time setup scripts
└── start.bat / start.sh      — Launch scripts
```

---

## API Endpoints

All endpoints require authentication (PIN-based session token) except `/auth/login`, `/auth/status`, and `/health/ping`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Verify PIN, get session token |
| `GET` | `/auth/status` | Check if current request is authenticated |
| `GET` | `/` | Status and uptime |
| `GET` | `/health` | Full health report (circuit breakers, perf, cache) |
| `POST` | `/chat` | Send a message, get a response |
| `POST` | `/clear` | Clear conversation history |
| `GET` | `/costs` | Session and monthly cost breakdown |
| `GET` | `/reminders` | List upcoming or all reminders |
| `POST` | `/reminders` | Create a reminder |
| `GET` | `/reminders/{id}` | Get a single reminder |
| `PATCH` | `/reminders/{id}` | Update a reminder |
| `DELETE` | `/reminders/{id}` | Delete a reminder |
| `POST` | `/reminders/{id}/dismiss` | Dismiss or advance a recurring reminder |
| `POST` | `/reminders/{id}/snooze` | Snooze a reminder for N minutes |
| `POST` | `/reminders/{id}/audio` | Upload a voice recording for own-voice playback |
| `GET` | `/reminders/{id}/audio` | Stream the attached voice recording |
| `GET` | `/digest` | Today's full daily digest |
| `GET` | `/digest/wake-briefing` | Short spoken morning briefing text |
| `GET` | `/profile` | Get user profile |
| `PUT` | `/profile` | Update a profile field |
| `GET` | `/plan` | Active task plan status |
| `GET` | `/learning` | Learning loop insights |
| `GET` | `/proactive` | Proactive engine status |
| `POST` | `/proactive/settings` | Enable or disable suggestion categories |
| `GET` | `/agents` | Multi-agent coordinator status |
| `POST` | `/voice/transcribe` | Transcribe uploaded audio (WebM/WAV/OGG) |
| `WS` | `/ws` | Real-time chat with token streaming |
| `WS` | `/ws/extension` | Chrome Extension DOM bridge |
| `WS` | `/ws/overlay` | Desktop overlay state feed |

---

## Security

- **PIN authentication** — All non-local connections require a session token obtained by verifying a PIN. Local connections (`localhost`) bypass auth for developer convenience.
- **CSRF protection** — All mutating requests from non-local origins require an `X-Tobi-Client` header.
- **Security headers** — Every response sets `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, and `Permissions-Policy`.
- **Input sanitisation** — User input is stripped of prompt injection patterns before being passed to the LLM.
- **Circuit breakers** — The Claude API and individual tools have circuit breakers that open after repeated failures to prevent cascading errors.
- **Rate limiting** — The login endpoint is rate-limited per client IP.

---

## Roadmap

### Phase 0 — Core Companion (complete)
- [x] Persistent memory across sessions (ChromaDB + SQLite)
- [x] Natural language reminders with voice recording and own-voice playback
- [x] Daily digest and morning wake briefing
- [x] Goal-drift detection and proactive nudges
- [x] PWA — installable on Android, iOS, and desktop
- [x] Push notification service worker with snooze and dismiss
- [x] Reminders management UI panel
- [x] Memory and daily digest UI panel

### Phase 1 — Contacts and Relationship Layer
- [ ] Import contacts via CSV or Android Contacts API
- [ ] Log last-contacted date per person
- [ ] Relationship check-in nudges ("you haven't spoken to X in 3 weeks")

### Phase 2 — Founder Ops Dashboard
- [ ] Connect to business database (inventory, sales queries via natural language)
- [ ] Client pipeline status rollup
- [ ] Cross-project status: "what's the state of everything?"

### Phase 3 — WhatsApp Business Layer
- [ ] Register a WhatsApp Business number for TOBI
- [ ] Send reminders and receive commands via WhatsApp
- [ ] Relay client messages through the number

### Phase 4 — Agentic Execution
- [ ] Website builder on command (generate and deploy a Vite/React site via Vercel API)
- [ ] Inventory and business management writes (not just reads)
- [ ] Invoice generation and client onboarding document creation

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Test coverage: coordinator routing, cost tracker, hardening (circuit breaker, retries), learning loop, memory store, task planner.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m "feat: description"`
4. Push to the branch: `git push origin feat/your-feature`
5. Open a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built by <a href="https://github.com/GoodnessFx"><b>Goodness Iyamah (GoodnessFx)</b></a>
</p>
