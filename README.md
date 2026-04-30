<p align="center">
  <img src="docs/screenshots/voice-orb.png" alt="Tobi Arc Reactor Orb" width="600" />
</p>

<h1 align="center">T.O.B.I.</h1>
<h3 align="center">My Personal Intelligence</h3>

<p align="center">
  A state-of-the-art personal AI assistant, evolved from the foundations of JARVIS. Tobi is faster, smarter, and more robust than ever. Featuring cinematic UI, advanced voice interaction, live web searching, and full computer automation.
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

Tobi is a high-performance, fully autonomous AI assistant designed to live on your computer and integrate seamlessly into your life. Whether through voice commands or interactive chat, Tobi manages your digital workspace with unmatched efficiency. It performs live web searches, automates complex browser tasks, manages your files, and learns your preferences through every interaction.

Built for speed and reliability, Tobi uses a multi-tier intelligence routing system to ensure lightning-fast responses while maintaining deep reasoning capabilities for complex projects.

<p align="center">
  <img src="docs/screenshots/chat-view.png" alt="Tobi Chat Interface" width="700" />
</p>

## The Tobi Core (Features)

**⚡ Faster & Smarter**
Tobi has been optimized for sub-second latency. Powered by advanced STT/TTS engines and optimized model routing, it responds like a human, with zero lag and high precision.

**🌐 Live Web Search & Analysis**
No more outdated information. Tobi performs live web searches to give you the most current answers, news, and data available. It doesn't just search; it analyzes and summarizes for you.

**🛡️ Unbreakable & Robust**
Engineered with production-grade hardening, Tobi handles errors gracefully. Whether it's network drops or tool failures, Tobi recovers automatically, ensuring 100% uptime and protection.

**🎙️ Advanced Voice Interaction**
A warm, natural British personality that you can talk to like a friend. Features continuous wake-word detection ("Hey Tobi") and intelligent follow-up windows.

**🖥️ Full System Automation**
Control your entire computer through Tobi. From opening apps and adjusting system settings to managing files and executing shell commands, Tobi is your ultimate digital companion.

**🤖 Multi-Agent Intelligence**
Tobi doesn't just follow instructions; it plans. It decomposes complex requests into subtasks, executes them in parallel, and verifies the quality of every outcome.

**🧠 Semantic Memory & Learning**
Tobi remembers who you are. It stores conversation context, learns your implicit preferences, and adapts its personality and humor to match yours over time.

<p align="center">
  <img src="docs/screenshots/system-dashboard.png" alt="Tobi System Dashboard" width="700" />
</p>

## Suit Up (Quick Start)

### Windows
```batch
# Clone the repository
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

# Run the setup script (installs dependencies and prepares the system)
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

## Intelligence Tiers

| Tier | Model | When Used |
|------|-------|-----------|
| **Fast** | Claude Haiku 4.5 | Quick lookups, simple questions |
| **Brain** | Claude Sonnet 4.6 | General conversation, single tool calls |
| **Deep** | Claude Opus 4.6 | Complex reasoning, multi-step plans |
| **Local** | Ollama (llama3.1:8b) | Free fallback, 100% offline support |

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, WebSockets
- **Frontend**: Next.js 14, Three.js, Tailwind CSS
- **Voice**: Moonshine ONNX, Faster-Whisper, Kokoro TTS, Edge-TTS
- **Automation**: Playwright, Chrome Extension Bridge
- **Intelligence**: Claude API + Ollama (Offline Fallback)
- **Memory**: SQLite Semantic Storage

## License

MIT License. Tobi is open-source and built for the future.

---
<p align="center">
  Built by <b>IG</b>
</p>
