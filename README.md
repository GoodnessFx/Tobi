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
  <img src="https://img.shields.io/badge/next.js-15-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js 15" />
  <img src="https://img.shields.io/badge/claude-API-D97706?style=flat-square&logo=anthropic&logoColor=white" alt="Claude API" />
  <img src="https://img.shields.io/badge/PWA-installable-5A0FC8?style=flat-square&logo=pwa&logoColor=white" alt="PWA" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-999999?style=flat-square" alt="Platform" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="MIT License" />
</p>

---

## What is TOBI?

TOBI is not a chatbot. It is an **operator with memory** — a personal AI system that runs on your own machine, knows your projects and goals, takes real action through tools, and proactively stays on top of things without being re-briefed every session.

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

## Modes

TOBI ships with a mode toggle that controls which feature layer is active. Modes are additive — Dev mode does not remove anything from Personal mode.

| Mode | Who it is for | What it adds |
|---|---|---|
| `personal` | Founders, executives, anyone | Reminders, voice, nudges, digest, goal tracking, relationship layer |
| `dev` | Developers and engineers | Code sessions with narrated reasoning, smart contract audit mode, concept checkpoints, voice pair-programming, SMS delivery, desktop alarm |
| `both` | Developer-founders | Everything from both layers running simultaneously |

Set your mode in your profile via chat: *"switch to dev mode"* or *"set mode to both."*

---

## Feature Overview

### Core Intelligence

- **Multi-provider LLM routing** — Claude stays the primary brain, but the router can hand off task types to OpenAI GPT, Google Gemini, or Grok when configured. Ollama remains the offline fallback.
- **Persistent memory** — ChromaDB vector store plus SQLite FTS5 for semantic and keyword recall across all sessions
- **Structured facts** — Automatically extracts facts from every conversation (name, location, preferences, projects, relationships) with confidence scoring and decay
- **Agentic tool-calling loop** — Claude calls real tools (search, shell, filesystem, browser, calendar, email, notes) and iterates until the task is done
- **Multi-agent coordinator** — Seven specialised agent types (researcher, coder, browser, system, communicator, analyst, generalist) routed automatically
- **Task planner** — Decomposes complex requests into subtasks, executes them in parallel where possible, and verifies quality on completion
- **Learning loop** — Tracks tool reliability, plan success rates, and common failure patterns to improve over time
- **Encrypted API key vault** — Extra API keys (GPT, Gemini, Grok, GitHub, X, TikTok) are held in a Fernet-encrypted vault locally, never in plaintext `.env`

### Business and Life Ops (the "second brain" layer)

These tools run alongside the core assistant and connect to what you actually do day to day:

| Area | What it does |
|---|---|
| **GitHub** | List repos, open PRs, recent commits, issues, stale branches; one summary of a repo or org |
| **Job and gig search** | RemoteOK and ArbeitNow lookups via official APIs; a daily job brief for active goals |
| **Market intelligence** | Live crypto prices and trending coins (CoinGecko), forex rates, AI/tech news via RSS — no scraping |
| **Social monitoring** | X trending topics and search via the official API; TikTok Research/API trends. No scraping |
| **CRM lite** | Contacts, deals, stages, activity log, stale-contact detection ("you haven't spoken to X in 3 weeks") |
| **Content pipeline** | Tracks posts per venture (Growth Network, KDP, Vibe District, Tersor Concept), publish cadence, and revenue log |
| **Coursework** | Courses and assignments with due dates, overdue flags, and a weekly academic brief |
| **Earnings projection** | 3/6/12-month projection from logged income with a confidence level attached |
| **Weekly retrospective** | One summary over memory, pipeline, CRM, GitHub, costs, and earnings |
| **Focus mode** | Silences the proactive engine's nudges and pauses intel collection during a focus block |
| **Intel engine** | Always-on background jobs that refresh crypto, forex, news, trending, and job briefs on intervals — stored between restarts and served through `/intel/*` |

### Reminders and Alarms

- **Natural language creation** — Say "remind me to follow up with OPES on Friday at 9am" and TOBI parses the date, creates the reminder, and delivers it when due
- **Own-voice playback** — Record a reminder in your own voice; TOBI plays back your exact words at the due time instead of generating a TTS summary
- **Alarm mode** — Full alarm delivery with snooze and dismiss actions via push notification
- **Recurrence** — Once, daily, weekly, weekdays, or monthly
- **SMS delivery** (Dev mode) — Reminders delivered as text messages via Twilio or Africa's Talking API so they reach you even when the app is closed
- **Desktop alarm** (Dev mode) — Native OS notification via an Electron system-tray companion — fires on your PC, where developers actually work
- **Proactive delivery** — Due reminders are checked every 60 seconds and delivered as spoken or text notifications

### Proactive Engine

- **Calendar alerts** — Upcoming meeting warnings at 15 and 5 minutes
- **Email nudges** — Notifies when unread count reaches a meaningful threshold
- **Morning greeting** — Time-appropriate briefing on first interaction each day
- **Goal-drift detection** — Flags goals and skill-gaps untouched for over 7 days with a candid nudge
- **Reminder delivery** — Background engine fires due reminders every 60 seconds

### Daily Digest and Wake Briefing

- **Daily digest** — On-demand or scheduled: today's date, top priorities, due reminders, stale goals, and a one-sentence LLM-generated coaching insight
- **Wake briefing** — Under 120 words, spoken by TTS after a morning alarm dismisses: date, top 3 priorities, reminders before noon, open mic for immediate voice input

### Dev Mode — Code Companion

This layer is additive. A developer using TOBI still gets all personal reminders, voice, nudges, and alarms. The coding layer adds context on top.

**Narrated code sessions**

Before writing or editing any code, TOBI always:
1. States the approach in plain language
2. Names the tradeoff or risk being addressed (e.g. "using a reentrancy guard here because the external call precedes the state update")
3. Asks "build it this way, or explain more first?" — it never silently writes code without narrating first

This is the default behaviour, not a setting. It is the core differentiator from pasting code into Claude.

**Smart contract audit mode**

Given a contract or file, TOBI walks through it the way a senior auditor explains findings to a junior — one issue at a time, in plain language, with the vulnerability class named (reentrancy, integer overflow, access control, oracle manipulation, front-running) and the fix reasoning explained. Not a raw linter dump.

**Concept checkpoints**

For users who opt into learning mode, TOBI pauses at key implementation decisions and asks a short check-question before continuing. Mirrors the ChainCodeCamp teaching model. Correct and incorrect answers are stored as facts (`type=skill_gap`) so nudges can later surface patterns: "you've missed 3 reentrancy-guard checkpoints this month — want a refresher?"

**Voice pair-programming**

While coding, you can talk through logic out loud using the existing Whisper pipeline. TOBI responds with both a spoken explanation and the code change. The own-voice audio storage schema for reminders is untouched — the two features share the same pipeline without conflicting.

**Coding context bridge**

Connect TOBI's tool-calling layer to a local CLI bridge or VS Code extension that streams the current file and repo context to the backend. TOBI reads what is on your screen and acts on it directly.

**Coding-context relationship nudges**

Dev mode adds a coding lens on top of the existing relationship nudge system. TOBI can correlate "you've been heads-down coding for 6 hours" with "you said don't let this happen again with [person]" using existing fact timestamps. No new data model is required.

### Voice

- **Whisper STT** — Browser microphone or terminal microphone transcribed via faster-whisper
- **Edge-TTS / Kokoro TTS** — Natural-sounding voice responses
- **Wake-word detection** — "Tobi" or "Hey Tobi" keeps the mic loop alive *(Note: Optional, requires Python <= 3.11)*
- **Clap detection** — 2 claps to wake and summarise where you left off; 3 claps for status check
- **Browser voice** — Full push-to-talk in the PWA; audio streamed in chunks for low latency *(Verified working on all supported Python versions)*

### Web and Browser Automation

- **DuckDuckGo search** — Background web search without opening a browser
- **Playwright automation** — Multi-step browser tasks: fill forms, click buttons, navigate pages, upload files
- **Chrome Extension bridge** — Direct DOM access in your real Chrome session (no OCR — reads and writes the actual page)
- **Sync real sessions** — Imports Chrome cookies so Playwright inherits your logged-in state for any site

### System and File Automation

- **Full file system** — List, read, write, copy, move, search, create directories
- **Shell execution** — Run any terminal command and get output back in chat
- **Screen capture and OCR** — Screenshot the current screen; read visible text; AI vision analysis of what is on screen
- **Clipboard** — Read and write the system clipboard
- **App control** — Open, close, and query running applications (macOS AppleScript; Windows PowerShell)
- **Volume and brightness** — Set system audio and display brightness by voice

### Calendar and Email

- **Calendar.app / Google Calendar** — macOS Calendar.app remains the platform fallback. Optional Google Workspace OAuth provides cross-platform Gmail search/unread counts and Google Calendar reads; OAuth tokens are stored in the encrypted local vault.
- **Mail.app** — Read recent emails, get unread count, send emails, search by query
- **Proactive meeting alerts** — Fires 15 and 5 minutes before any calendar event

### Development Tools

- **Claude Code integration** — Delegate coding tasks to an agentic sub-session with full file and shell access
- **Project scaffolding** — Generate project structure, boilerplate, and starter code from a description
- **Smart terminal** — Routes commands through Claude Code for safety checks and multi-step reasoning

### Notes

- **Apple Notes** — The AppleScript integration is a desktop Notes.app feature. In the PWA, users can explicitly paste selected note text or choose a plain-text/Markdown export and send it to TOBI for review. The PWA cannot read Notes in the background.

### Install TOBI on a phone or desktop

TOBI's web client is a Progressive Web App (PWA). After TOBI is deployed to a
reachable **HTTPS** address with its API and WebSocket routes configured, users
can add it to their home screen. This installs a web app shortcut; it is not an
App Store or Play Store native application.

- **Android**: Open the HTTPS address in Chrome, open the browser menu, and
  choose **Install app** or **Add to Home screen**.
- **iPhone/iPad**: Open the HTTPS address in Safari, tap **Share**, then **Add
  to Home Screen**.
- **Desktop**: Use the install icon in the Chrome or Edge address bar when
  offered.
- After signing in, **Settings → Phone and app access** also shows the browser's
  install prompt when supported, or device-specific install instructions.

The app and backend must both be reachable from the phone. The development URL
`http://localhost:3741` refers to the phone itself, not a TOBI server running on
another computer, and is only suitable for same-device development. Public
deployment must use HTTPS and securely proxy the API and WebSocket endpoints;
do not expose the development server directly to the internet.

The service worker caches the app shell and static assets, not live API data or
the assistant backend. Push notifications require server push configuration
and browser support. An installed PWA does not provide an always-on microphone,
an avatar floating over other apps, or unrestricted access to phone notes and
other apps. Those require separate platform integrations and explicit user
permission.

TOBI's web-supported phone access is deliberately user-driven:

- The PWA asks for microphone permission only when the user starts voice input.
- Browser notifications are for TOBI reminders; they do not expose notification
  history from other phone apps.
- On browsers that implement the Contact Picker API, users can select specific
  contacts, review the selection, and confirm importing them into TOBI CRM.
- Google Calendar/Gmail access uses the existing read-only Google OAuth scopes.
  The OAuth flow currently runs on the computer hosting the backend; connect it
  there before using that backend from a phone.
- iPhone users can copy selected Apple Notes text or choose a text export in
  TOBI's Chat **Share a note** dialog. iOS does not permit a PWA to read private
  Notes data automatically.

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
│                        TOOL LAYER  (99 tools)                            │
│  shell  filesystem  screen  web_search  web_browse  weather  browser    │
│  calendar_email  notes_access  claude_code  chrome_extension             │
│  mac_control  windows_control  reminder_tools  audit_mode               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, WebSockets |
| LLM | Anthropic Claude (primary) + optional OpenAI GPT, Google Gemini, Grok via router; Ollama fallback |
| Market data | CoinGecko, ExchangeRate API, niche RSS feeds |
| Job search | RemoteOK, ArbeitNow (official APIs) |
| Social | X API (v2), TikTok Research/API |
| STT | faster-whisper, Moonshine ONNX |
| TTS | Kokoro, Edge-TTS |
| Wake word | Optional OpenWakeWord extra (`requirements-wakeword.txt`); terminal falls back to Enter-to-talk and the PWA has push-to-talk |
| Memory | ChromaDB (vector), SQLite + FTS5, JSON facts |
| Browser automation | Playwright, Chrome Extension (DOM bridge) |
| Frontend | Next.js 14, React 18, Three.js, Tailwind CSS v4 |
| PWA | Web App Manifest, Service Worker, Web Push API |
| SMS | Twilio / Africa's Talking (Dev mode) |

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

First deploy TOBI to an HTTPS address that your phone can reach, with the API
and WebSocket endpoints securely routed to the backend. `localhost` on a phone
does not point to your development computer.

**Android** — open the HTTPS address in Chrome, tap the menu, then **Install
app** or **Add to Home screen**.

**iOS/iPadOS** — open the HTTPS address in Safari, tap **Share**, then **Add to
Home Screen**.

**Desktop** — look for the install icon in the Chrome or Edge address bar.

This installs TOBI's web app shortcut, not a native App Store/Play Store app.
The installed PWA does not run an avatar over other apps or grant access to
Apple Notes or other apps. See the [feature audit](./FEATURES.md) for verified
capabilities and platform limitations.

### Production PWA launch checklist

This repository is **not deployed**. Complete and verify these items before
sharing a TOBI URL with users:

- [ ] Choose a hosting provider and domain; terminate TLS so the site is served
  over HTTPS.
- [ ] Deploy the Next.js UI and Python 3.11+ backend. Keep the backend private
  behind the HTTPS reverse proxy/firewall; do not expose its development port
  directly to the public internet.
- [ ] Route same-origin `https://<domain>/Tobi-api/*` requests to the backend's
  HTTP API with the prefix removed, and route `wss://<domain>/Tobi-ws` to the
  backend `/ws` endpoint with WebSocket upgrades enabled.
- [ ] Configure production authentication/PIN, secrets, allowed origins, and
  encrypted token storage. Never put API keys or OAuth client secrets in the
  frontend bundle.
- [ ] Configure Google OAuth for the actual deployment environment. The
  current installed-app sign-in flow opens a browser on the backend host, so
  connect Google on that host before using its account from a phone.
- [ ] Verify `https://<domain>/`, `/manifest.json`, `/sw.js`, login, an
  authenticated API request, and the WebSocket chat connection.
- [ ] Install and test from Android Chrome and iPhone Safari over the public
  HTTPS URL. Confirm home-screen launch, safe-area layout, microphone
  permission, and expected offline behavior on real devices.
- [ ] Confirm browser push configuration separately if reminder push is needed;
  app-shell caching alone does not deliver push or run the assistant offline.

Do not mark phone launch complete until these checks pass. The installed PWA
does not have access to other apps' private notes/notification history or
system-wide overlays; note sharing and contact picking are explicit,
browser-limited actions.

---

## Run Modes

| Mode | Command | Description |
|---|---|---|
| `server` | `python -m Tobi.main --mode server` | HTTP + WebSocket API only (for PWA and browser use) |
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

# Multi-provider routing (all optional — Claude works without them)
OPENAI_API_KEY=...
GEMINI_API_KEY=...
GROK_API_KEY=...

# Business tools
GITHUB_TOKEN=...
X_BEARER_TOKEN=...
TIKTOK_ACCESS_TOKEN=...
NEWSAPI_KEY=...
FOCUS_DEFAULT_MINUTES=45
RETRO_DAY=7

# Optional Google Workspace OAuth installed-app client JSON file path
GOOGLE_OAUTH_CLIENT_SECRETS=...

# Authentication PIN (auto-generated if not set)
TOBI_PIN=1234

# Ports
API_PORT=8741
UI_PORT=3741

# Ollama fallback (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# ElevenLabs (optional — higher-quality voice output)
ELEVENLABS_API_KEY=your-key-here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Web Push (optional — required for server-sent push to mobile)
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_EMAIL=mailto:you@example.com

# SMS delivery — Dev mode (optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
# Or Africa's Talking:
AFRICAS_TALKING_API_KEY=...
AFRICAS_TALKING_USERNAME=...
```

---

## Memory System

TOBI maintains memory across four layers that compound over time:

| Layer | Storage | What lives here |
|---|---|---|
| Active context | RAM | Current conversation turns (last 100) |
| Semantic recall | ChromaDB | Past conversation chunks retrieved by embedding similarity |
| Structured facts | SQLite + JSON | Extracted knowledge: name, location, projects, goals, preferences, relationships — with confidence scores and decay |
| Fast keyword lookup | SQLite FTS5 | Tasks, notes, and memories indexed for instant text search |

Facts are extracted automatically from every conversation using pattern matching (high confidence) and Haiku-assisted extraction (lower confidence). They decay slowly when not reinforced, so stale facts fade out naturally. Concept checkpoint answers from Dev mode are stored as `type=skill_gap` facts and feed directly into goal-drift nudges.

---

## Reminders

Reminders are created by voice or text:

> *"Remind me to follow up with the client on Friday at 2pm"*
>
> *"Set a daily alarm for 7am"*
>
> *"Remind me to deploy the contract before EOD — make it urgent"*

Each reminder stores:

- Content text and due timestamp
- Recurrence rule (once / daily / weekly / weekdays / monthly)
- Alarm flag (full alarm vs. soft notification)
- Delivery channel: `push` (default), `sms`, or `desktop_alarm` (Dev mode)
- Optional voice recording for own-voice playback
- Playback mode (`tobi_voice` generates TTS at delivery time; `own_voice` plays your original recording back verbatim)

The proactive engine checks for due reminders every 60 seconds and delivers them as spoken alerts, push notifications, SMS messages, or desktop alarms depending on the channel setting. Recurring reminders automatically advance to the next occurrence after firing.

---

## Project Structure

```
Tobi/
├── Tobi/
│   ├── main.py                    — Entry point (text / voice / server / full modes)
│   ├── agent/
│   │   ├── coordinator.py         — Multi-agent router (7 specialised agents)
│   │   ├── executor.py            — Agentic tool-use loop with QA verification
│   │   ├── learning.py            — Tool reliability and plan success tracking
│   │   ├── planner.py             — Task decomposition into subtasks
│   │   ├── reminder_tools.py      — Reminder tool schemas and async handlers
│   │   └── tools_schema.py        — Master tool registry (90+ tools)
│   ├── config/
│   │   └── settings.py            — All configuration with env var overrides
│   ├── core/
│   │   ├── api_key_vault.py       — Encrypted storage for optional API keys
│   │   ├── brain.py               — Central orchestrator wiring all subsystems
│   │   ├── digest.py              — Daily digest and morning wake briefing
│   │   ├── focus_mode.py          — Focus blocks (silences nudges and intel)
│   │   ├── intel_engine.py        — Always-on scheduled intel collection
│   │   ├── llm.py                 — Multi-backend LLM engine with streaming
│   │   ├── multi_llm.py           — Task-type provider router (GPT/Gemini/Grok)
│   │   ├── proactive.py           — Background engine for reminders and nudges
│   │   ├── server.py              — FastAPI HTTP + WebSocket server
│   │   └── weekly_retro.py        — Weekly retrospective builder
│   ├── extensions/
│   │   └── chrome/                — Chrome Extension (DOM bridge)
│   ├── memory/
│   │   ├── conversation_store.py  — SQLite-backed conversation history
│   │   ├── facts.py               — Fact extraction with confidence scoring
│   │   ├── preferences.py         — Implicit preference learning
│   │   ├── reminders_store.py     — Reminders SQLite table and CRUD
│   │   ├── sqlite_store.py        — Tasks, notes, memories (FTS5)
│   │   └── store.py               — MemoryStore (ChromaDB + SQLite)
│   ├── tools/
│   │   ├── browser_agent.py       — Playwright browser automation
│   │   ├── calendar_email.py      — Calendar.app and Mail.app integration
│   │   ├── chrome_extension.py    — Chrome DOM bridge tools
│   │   ├── claude_code.py         — Claude Code sub-agent delegation
│   │   ├── content_pipeline.py    — Content publishing tracker per venture
│   │   ├── coursework.py          — Courses and assignment tracking
│   │   ├── crm.py                 — Contacts, deals, and activity log
│   │   ├── earnings.py            — Income log and projections
│   │   ├── filesystem.py          — File system tools
│   │   ├── github_tools.py        — GitHub repos, PRs, issues, commits
│   │   ├── job_search.py          — RemoteOK / ArbeitNow job search
│   │   ├── mac_control.py         — macOS app and system control
│   │   ├── market_intel.py        — Crypto, forex, and AI/tech news
│   │   ├── notes_access.py        — Apple Notes integration
│   │   ├── screen.py              — Screenshot and OCR
│   │   ├── shell.py               — Shell command execution
│   │   ├── social_media.py        — X and TikTok official API monitoring
│   │   ├── weather.py             — Weather via Open-Meteo
│   │   ├── web_browse.py          — Page fetching and link extraction
│   │   ├── web_search.py          — DuckDuckGo search
│   │   └── windows_control.py     — Windows app and system control
│   ├── ui/
│   │   └── tobi-ui/               — Next.js 14 frontend
│   │       ├── public/
│   │       │   ├── manifest.json  — PWA manifest
│   │       │   ├── sw.js          — Service worker
│   │       │   └── icon-*.png     — App icons (72 to 512px)
│   │       └── src/
│   │           ├── app/           — Next.js App Router
│   │           ├── components/
│   │           │   ├── auth/      — Login screen
│   │           │   ├── chat/      — Chat view
│   │           │   ├── cinematic/ — Arc Reactor voice orb (Three.js)
│   │           │   ├── dashboard/ — System stats dashboard
│   │           │   ├── memory/    — Daily digest and facts panel
│   │           │   ├── reminders/ — Reminders management panel
│   │           │   ├── settings/  — Settings panel
│   │           │   └── shared/    — Status bar, toasts, plan progress
│   │           ├── hooks/         — React hooks (auth, WebSocket, API, push)
│   │           └── lib/           — TypeScript types
│   └── voice/
│       ├── listener.py            — Microphone + wake word + STT pipeline
│       └── speaker.py             — TTS + audio output pipeline
├── desktop-overlay/               — macOS Swift overlay (Arc Reactor HUD)
├── docs/                          — Screenshots and architecture docs
├── templates/prompts/             — YAML task templates for the agent
├── tests/                         — pytest test suite
├── .env.example                   — Environment variable reference
├── requirements.txt               — Python dependencies
├── setup.bat / setup.sh           — One-time setup scripts
└── start.bat / start.sh           — Launch scripts
```

---

## API Endpoints

All endpoints require authentication (PIN-based session token) except `/auth/login`, `/auth/status`, and `/health/ping`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Verify PIN, get session token |
| `GET` | `/auth/status` | Check if the current request is authenticated |
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
| `GET` | `/profile` | Get user profile (includes `mode` field) |
| `PUT` | `/profile` | Update a profile field |
| `GET` | `/plan` | Active task plan status |
| `GET` | `/learning` | Learning loop insights |
| `GET` | `/proactive` | Proactive engine status |
| `POST` | `/proactive/settings` | Enable or disable suggestion categories |
| `GET` | `/agents` | Multi-agent coordinator status |
| `POST` | `/voice/transcribe` | Transcribe uploaded audio (WebM / WAV / OGG) |
| `GET` | `/providers` | Multi-provider LLM routing status |
| `POST` | `/providers/chat` | Chat pinned to a specific provider (openai / gemini / grok / claude / ollama) |
| `GET` | `/github/repos` | List GitHub repos |
| `GET` | `/github/prs` | Open PRs |
| `GET` | `/github/issues` | Open issues |
| `GET` | `/github/summary` | One-shot repo summary (includes recent commits) |
| `GET` | `/jobs/search` | Search jobs (RemoteOK / ArbeitNow) |
| `GET` | `/jobs/daily` | Daily job brief |
| `GET` | `/market/crypto` | Live crypto prices + trending |
| `GET` | `/market/forex` | Forex rates |
| `GET` | `/market/news` | AI/tech news headlines |
| `GET` | `/market/brief` | Combined market brief |
| `GET` | `/market/niche/{niche}` | Niche-specific update |
| `GET` | `/social/trending` | X + TikTok trending |
| `GET` | `/social/search` | Search X |
| `GET` | `/crm/summary` | CRM overview (contacts, deals, stale) |
| `GET` | `/crm/contacts` | List contacts |
| `POST` | `/crm/contacts` | Add a contact |
| `GET` | `/crm/deals` | List deals |
| `GET` | `/crm/stale` | Stale contacts (no activity in N days) |
| `GET` | `/content/summary` | Content pipeline summary |
| `GET` | `/content/{venture}` | Per-venture content update |
| `GET` | `/academic/brief` | Coursework brief |
| `GET` | `/academic/upcoming` | Upcoming assignments |
| `GET` | `/academic/overdue` | Overdue assignments |
| `GET` | `/earnings/brief` | Earnings projection brief |
| `GET` | `/vault/status` | API key vault status |
| `GET` | `/vault/keys` | Stored key names |
| `GET` | `/focus/status` | Focus mode status |
| `POST` | `/focus/start` | Start a focus block |
| `POST` | `/focus/stop` | Stop the focus block |
| `GET` | `/retro/weekly` | Weekly retrospective |
| `GET` | `/intel/status` | Intel engine + latest stored results |
| `GET` | `/intel/latest/{category}` | Latest intel for one category (crypto/forex/news/trending/jobs) |
| `POST` | `/intel/refresh/{category}` | Force a collection now |
| `POST` | `/intel/intervals` | Change a category's collection interval (min 300s) |
| `GET` | `/daily/brief` | Combined brief across all modules (`?sections=digest,github,market`) |
| `WS` | `/ws` | Real-time chat with token streaming |
| `WS` | `/ws/extension` | Chrome Extension DOM bridge |
| `WS` | `/ws/overlay` | Desktop overlay state feed |

---

## Security

- **PIN authentication** — All non-local connections require a session token obtained by verifying a PIN. Local connections bypass auth for developer convenience.
- **CSRF protection** — All mutating requests from non-local origins require an `X-Tobi-Client` header.
- **Security headers** — Every response sets `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, and `Permissions-Policy`.
- **Input sanitisation** — User input is stripped of prompt injection patterns before being passed to the LLM.
- **Circuit breakers** — The Claude API and individual tools have circuit breakers that open after repeated failures to prevent cascading errors.
- **Rate limiting** — The login endpoint is rate-limited per client IP.
- **Confirmation on destructive actions** — Financial and data-deletion operations require explicit confirmation before execution. A compromised or injected session cannot silently delete data or trigger payments.

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

### Business Ops Layer (complete)
- [x] Encrypted API key vault for optional providers and services
- [x] Multi-provider LLM routing (GPT / Gemini / Grok on top of Claude)
- [x] GitHub integration — repos, PRs, commits, issues, summaries
- [x] Job and gig search (RemoteOK, ArbeitNow) with daily brief
- [x] Market intelligence — crypto, forex, AI/tech news
- [x] Social monitoring via X and TikTok official APIs
- [x] CRM lite — contacts, deals, stale-contact nudges
- [x] Content pipeline tracker per venture
- [x] Coursework tracker with overdue detection
- [x] Earnings log and 3/6/12-month projections
- [x] Weekly retrospective
- [x] Focus mode (silences nudges + pauses intel engine)
- [x] Always-on intel engine with stored, periodic results
- [x] Combined `/daily/brief` endpoint across all modules

### Dev Mode (in progress)
- [ ] Mode toggle in user profile (`personal` / `dev` / `both`)
- [ ] Narrated code sessions — approach, tradeoffs, confirmation before writing
- [ ] Smart contract audit mode — one finding at a time, plain language
- [ ] Concept checkpoints with skill-gap fact storage
- [ ] Voice pair-programming (Whisper pipeline + code output)
- [ ] SMS reminder delivery (Twilio / Africa's Talking)
- [ ] Desktop alarm via Electron system-tray companion

### Phase 1 — Contacts and Relationship Layer
- [ ] Import contacts via CSV or Android Contacts API
- [ ] Log last-contacted date per person
- [ ] Relationship check-in nudges ("you haven't spoken to X in 3 weeks")

### Phase 2 — Founder Ops Dashboard
- [ ] Connect to business database for natural-language inventory and sales queries
- [ ] Client pipeline status rollup
- [ ] Cross-project status: "what's the state of everything?"

### Phase 3 — WhatsApp Business Layer
- [ ] Register a WhatsApp Business number for TOBI
- [ ] Send reminders and receive commands via WhatsApp
- [ ] Relay client messages through the number

### Phase 4 — Agentic Execution
- [ ] Website builder on command — generate and deploy a site via Vercel API
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
