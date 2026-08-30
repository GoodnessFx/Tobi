# Installing TOBI

**Total Omni Brain Intelligence** — personal AI companion and operator.

GitHub: [github.com/GoodnessFx/Tobi](https://github.com/GoodnessFx/Tobi)

---

## What you need

| Requirement | Minimum | Where to get it |
|---|---|---|
| Python | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) (Note: Wake-word detection requires Python <= 3.11; push-to-talk works on any supported version) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Anthropic API key | — | [console.anthropic.com](https://console.anthropic.com) |
| ffmpeg | any | [ffmpeg.org/download](https://ffmpeg.org/download.html) — add to PATH |

TOBI runs on **Windows** and **macOS**. Linux works too but is untested.

---

## Windows — Quick install

```batch
:: 1. Clone the repo
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

:: 2. Run setup (installs everything)
setup.bat

:: 3. Open .env and paste your Anthropic API key
notepad .env

:: 4. Launch
start.bat
```

Then open **http://localhost:3741** in your browser.
Default PIN: **1234**

---

## macOS / Linux — Quick install

```bash
# 1. Clone the repo
git clone https://github.com/GoodnessFx/Tobi.git
cd Tobi

# 2. Run setup
chmod +x setup.sh && ./setup.sh

# 3. Add your API key
nano .env   # or open in any text editor

# 4. Launch
./start.sh full
```

Then open **http://localhost:3741** in your browser.

---

## Setting your API key

Open the `.env` file in any text editor and replace the placeholder:

```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

with your real key from [console.anthropic.com](https://console.anthropic.com).

Without this, TOBI starts and the UI works but AI responses are disabled.

---

## Install as a PWA (phone / tablet)

Once TOBI is running on a machine on your network, open its URL on your phone:

**Android** — open in Chrome → tap the three-dot menu → "Add to Home Screen"

**iOS** — open in Safari → tap the share icon → "Add to Home Screen"

TOBI will appear as a standalone app with its own icon. Push notifications work on Android (iOS 16.4+) once installed.

To access from another device on the same network, use your machine's local IP instead of `localhost`:

```
http://192.168.x.x:3741
```

Find your IP with `ipconfig` (Windows) or `ifconfig` (Mac/Linux).

---

## Run modes

| Command | What it does |
|---|---|
| `start.bat` | Server + UI (default, recommended) |
| `start.bat text` | Text-only terminal chat, no server or voice |
| `start.bat voice` | Voice loop in terminal (mic + speakers), no UI |
| `start.bat full` | Server + UI + voice loop (requires microphone) |

---

## Stopping TOBI

Press `Ctrl+C` in the terminal window running the backend. The UI window will also close.

---

## Troubleshooting

**"Module not found" on startup** — run `pip install -r requirements.txt` again.

**UI shows blank page** — wait 10 seconds after starting for Next.js to compile, then refresh.

**AI says it cannot respond** — your `ANTHROPIC_API_KEY` in `.env` is missing or invalid.

**Voice transcription not working** — check that `ffmpeg` is installed and on your PATH. Test with `ffmpeg -version` in a terminal.

**Port already in use** — something else is on port 8741 or 3741. Change `API_PORT` and `UI_PORT` in `.env`.

---

## Optional features

| Feature | What to add to `.env` |
|---|---|
| Better voice (ElevenLabs) | `ELEVENLABS_API_KEY=...` |
| Offline AI (no API key needed) | Install [Ollama](https://ollama.com), then set `PREFER_CLAUDE=false` |
| Custom wake PIN | `TOBI_PIN=your-pin` |

---

Built by [Goodness Iyamah](https://github.com/GoodnessFx)
