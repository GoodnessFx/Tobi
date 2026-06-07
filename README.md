<p align="center">
  <img src="docs/screenshots/voice-orb.png" alt="Tobi Arc Reactor Orb" width="600" />
</p>

<h1 align="center">T.O.B.I.</h1>
<h3 align="center">Total Omniscient Brain Interface</h3>

<p align="center">
  A state-of-the-art personal AI operating system, evolved from the foundations of JARVIS. Tobi is faster, smarter, and more robust than ever. Featuring cinematic UI, advanced voice interaction, live web searching, and full computer automation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/next.js-14-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/three.js-0.183-049EF4?style=flat-square&logo=threedotjs&logoColor=white" alt="Three.js" />
  <img src="https://img.shields.io/badge/platform-Windows%20%2F%20macOS-999999?style=flat-square&logo=apple&logoColor=white" alt="Platform" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License" />
</p>

---

## "How can I help you today, boss?"

Tobi is a **fully autonomous personal AI operating system** designed to live on your computer and integrate seamlessly into your life. Whether through voice commands or interactive chat, Tobi manages your digital workspace with unmatched efficiency. It performs live web searches, automates complex browser tasks, manages your files, and learns your preferences through every interaction.

Built for speed and reliability, Tobi uses a multi-tier intelligence routing system to ensure lightning-fast responses while maintaining deep reasoning capabilities for complex projects.

<p align="center">
  <img src="docs/screenshots/chat-view.png" alt="Tobi Chat Interface" width="700" />
</p>

---

## ⚡ The Tobi Core (Features)

| Capability | Status |
|------------|--------|
| 🎤 Always-on voice ("Tobi" wake word) | ✅ Core |
| 👏 Clap detection (wake / status mode) | ✅ Core |
| 🧠 Full memory (session + persistent) | ✅ Core |
| 💻 Full computer control (files, apps, terminal) | ✅ Core |
| 🌐 Browser automation (forms, scraping, posts) | ✅ Core |
| 📧 Email read/write/manage | ✅ Core |
| 📅 Calendar management | ✅ Core |
| 📱 Social media automation (X, IG, TG, WA) | ✅ Core |
| 🔍 Deep research + web search | ✅ Core |
| 🎯 Proactive suggestions + learning | ✅ Core |
| 🌅 Morning briefing | ✅ Core |
| 💾 Session restore on laptop wake | ✅ Core |

**⚡ Faster & Smarter**
Tobi has been optimized for sub-second latency. Powered by advanced STT/TTS engines and optimized model routing, it responds like a human, with zero lag and high precision.

**🎙️ Advanced Voice & Gesture Interaction**
A warm, natural British personality that you can talk to like a friend. Features continuous wake-word detection ("Hey Tobi" or just "Tobi"), intelligent follow-up windows, and **clap detection** (2 claps to wake and summarize, 3 claps for status).

**🖥️ Full System Automation**
Control your entire computer through Tobi. From opening apps and adjusting system settings to managing files and executing shell commands. Optimized for both **Windows (PowerShell)** and **macOS (AppleScript)**.

**🤖 Multi-Agent Intelligence**
Tobi doesn't just follow instructions; it plans. It decomposes complex requests into subtasks, executes them in parallel, and verifies the quality of every outcome.

**🧠 Semantic Memory & Learning**
Tobi remembers who you are. It stores conversation context, learns your implicit preferences, and adapts its personality and humor to match yours over time.

<p align="center">
  <img src="docs/screenshots/system-dashboard.png" alt="Tobi System Dashboard" width="700" />
</p>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          TOBI CORE                               │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  EARS    │   │  BRAIN   │   │  HANDS   │   │  MEMORY  │    │
│  │          │   │          │   │          │   │          │    │
│  │ Moonshine│──▶│  Claude  │──▶│PowerShell│   │ SQLite   │    │
│  │ Whisper  │   │   API    │   │ AppScript│   │ JSON     │    │
│  │ Clap Det.│   │ Ollama   │   │ Shell    │   │ Vector DB│    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  EYES    │   │  VOICE   │   │  SOCIAL  │   │  WEB     │    │
│  │          │   │          │   │          │   │          │    │
│  │ Screenshot│  │ Edge-TTS │   │ Playwright│  │ DDGS     │    │
│  │ OCR      │   │ Kokoro   │   │ Chrome Ext│  │ Scraper  │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Suit Up (Quick Start)

### Windows
```batch
# Clone the repository
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

# Run the setup script
setup.bat

# Launch Tobi
start.bat
```

### macOS / Linux
```bash
# Clone
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

# Setup
chmod +x setup.sh && ./setup.sh

# Launch
./start.sh full
```

Open **http://localhost:3000** in your browser. Say "Hey Tobi" or click the mic.

---

## 🧠 Memory System

TOBI remembers everything across 4 tiers:
- **Tier 1 — Active Session (RAM)**: What's happening RIGHT NOW.
- **Tier 2 — Recent Context (72 hours)**: Projects in progress, recent decisions.
- **Tier 3 — Deep Knowledge (Persistent)**: Your profile, goals, habits, and preferences.
- **Tier 4 — World Knowledge (External)**: Real-time web search and API data.

---

## 🎤 Voice Commands (Examples)

- *"Tobi, what's on my calendar today?"*
- *"Tobi, open VS Code and the Tobi repo"*
- *"Tobi, summarize my last 10 emails"*
- *"Tobi, set my volume to 50 percent"*
- *"Tobi, what was I working on yesterday?"*
- *"Tobi, research the top 5 AI projects right now"*

---

## 👏 Clap Detection

TOBI listens for clap patterns even when your screen is off:
- **2 claps**: Wake Tobi and summarize "where I stopped".
- **3 claps**: System status check and standby confirmation.

---

## 🌅 Morning Briefing (Auto, 7:00 AM)

Every morning TOBI can provide a spoken briefing covering your schedule, overnight alerts (emails, socials), and current project status to help you hit the ground running.

---

## 🗺️ Roadmap

### Phase 1 — Foundation (Current)
- [x] Voice wake + clap detection
- [x] Core computer control (Windows/macOS)
- [x] Memory system (all 4 tiers)
- [x] Email + calendar integration
- [x] Session restore on wake

### Phase 2 — Intelligence Layer
- [ ] Presence detection via camera
- [ ] Gesture recognition
- [ ] Semantic memory search (vector DB)
- [ ] Mobile companion app (iOS + Android)

---

## 🧱 Tech Stack

- **Backend**: Python 3.11+, FastAPI, WebSockets
- **Frontend**: Next.js 14, Three.js, Tailwind CSS
- **Voice**: Moonshine ONNX, Faster-Whisper, Kokoro TTS, Edge-TTS
- **Automation**: Playwright, Chrome Extension Bridge
- **Intelligence**: Claude API + Ollama (Offline Fallback)
- **Memory**: SQLite Semantic Storage

---

## 💡 Philosophy

> **The space between a thought and its execution should be zero.**

Tobi is built to eliminate the friction of digital life. You shouldn't have to manage your tools; your tools should manage themselves.

---

## 📜 License

MIT License. Tobi is open-source and built for the future.

---
<p align="center">
  Built by <b>GoodnessFx</b>
</p>
