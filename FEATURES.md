# TOBI feature audit

This is a source-based baseline for the requested product brief. A feature is
not marked `WORKING` merely because a module or endpoint exists.

## Verification snapshot

- Frontend production build: passed on Next.js 15.5.29 with onboarding changes.
- Frontend lint: passed with three existing React hook dependency warnings.
- Frontend TypeScript check: passed.
- Frontend production dependency audit: 0 vulnerabilities. The full development
  dependency audit still reports 6 moderate findings in the ESLint TypeScript
  dependency tree.
- Frontend `/` route: returned HTTP 200 from the production server; the browser
  shell rendered, but the backend API was not running.
- PWA installation assets: manifest, home-screen icons, and service-worker
  registration are present. Phone installation was not tested; reachable HTTPS
  hosting with secure API and WebSocket routing is still required.
- Phase 1 UI: locally bundled Inter and JetBrains Mono fonts and TOBI icon are
  present. Full visual and accessibility review remains outstanding.
- Backend tests: 270 passed in a previous recorded run. In this environment,
  6 Google Workspace tests passed; the new settings API tests cannot be
  collected because FastAPI is not installed.
- Python dependency audit: `pip-audit -r requirements.txt` reports 32 findings
  across `chromadb`, `cryptography`, and `filelock`. The current Python 3.10
  package index has no `filelock` 4.2.1+ release (those releases require Python
  3.11); the audit lists no fixed versions for the reported ChromaDB findings.
  Remediation and a clean audit remain outstanding.
- Targeted mypy: passed for the touched integration modules after suppressing
  missing upstream type-stub metadata for the Google API client libraries.
  Full-repository mypy remains blocked by pre-existing errors and missing
  dependencies.
- Backend runtime/API checks: not run. The available Python is 3.10.11 (the
  project requires 3.11+) and FastAPI is not installed in the current
  environment.
- Browser smoke check: the frontend returned HTTP 200, but onboarding could
  not be completed because the API was unavailable. Full login/onboarding/PWA
  validation remains outstanding.
- The passing unit tests cover coordinator, cost tracking, hardening, learning,
  memory, and planning. They do not prove the individual integrations listed
  below.

Status meanings: `WORKING` requires a reproducible test or recorded manual
check; `PARTIAL` means some related implementation exists, but the stated
capability is incomplete or unverified; `MISSING` means no implementation was
found; `BLOCKED` means an OS or external constraint prevents the requested
behavior on that platform.

## Owner's notes

| Feature | Where it lives (file) | Status | How verified | Notes |
|---|---|---|---|---|
| Play music in Spotify or other song apps | — | MISSING | Source scan; no Spotify connector found | No OAuth, playback, or deep-link integration found. |
| Connect to GitHub | `Tobi/tools/github_tools.py`; `Tobi/core/server.py` | PARTIAL | Source inspection only | Token-based repo, PR, commit, issue, and summary calls exist; no OAuth flow or live API check. |
| Push to GitHub / understand work and act | `Tobi/tools/github_tools.py`; `Tobi/tools/shell.py` | PARTIAL | Source inspection only | GitHub read operations and issue creation exist. No dedicated confirmed-push workflow was found; shell use is not equivalent to that feature. |
| Find jobs and make CVs | `Tobi/tools/job_search.py` | PARTIAL | Source inspection only | RemoteOK/ArbeitNow search exists; CV generation, exports, and application tracking were not found. |
| Warn about attacks, fraud, and spam emails | `Tobi/tools/calendar_email.py`; `Tobi/tools/chrome_extension.py` | PARTIAL | Source inspection only | Email access exists through platform/browser tools; no phishing or fraud analysis workflow was found. |
| Custom form of address | `Tobi/core/profile.py`; `Tobi/ui/tobi-ui/src/components/onboarding/OnboardingWizard.tsx` | PARTIAL | Source inspection; frontend build passed | First-run setup saves a nickname and uses it for the startup greeting; a later profile-edit control is not available. |
| Sports-betting analysis | — | MISSING | Source scan; no sports-analysis tool found | No sports stats or bankroll feature was found. |
| Forex analysis | `Tobi/tools/market_intel.py` | PARTIAL | Source inspection only | Market data exists; indicator analysis and paper-trading journal were not verified. |
| Collect online data and game data | `Tobi/core/intel_engine.py`; `Tobi/tools/market_intel.py` | PARTIAL | Source inspection only | Scheduled market/news/job collection exists; game-data collection was not found. |
| Visual activity feed | `Tobi/core/server.py`; `Tobi/ui/tobi-ui/src` | PARTIAL | Source inspection; frontend build passed | Agent and plan status APIs/components exist; a complete live tool-call activity feed was not found. |
| Movie recommendations from taste | — | MISSING | Source scan; no TMDB/movie feature found | No taste profile, recommendation, or watchlist implementation was found. |
| Import chat history | — | MISSING | Source scan | No exported chat-history importer was found. |
| Voice replies and voice choices | `Tobi/voice/listener.py`; `Tobi/voice/speaker.py`; `Tobi/ui/tobi-ui/src/components/onboarding/OnboardingWizard.tsx` | PARTIAL | Source inspection; frontend build passed | First-run setup offers Kokoro voice selection and applies the selected voice; spoken output was not runtime-tested. |
| Wake word and locked-phone listening | `Tobi/voice/listener.py`; `requirements-wakeword.txt` | PARTIAL | Source inspection only | Desktop wake-word support is optional and guarded. Locked-phone operation needs a native companion; no Android app exists. |
| Siri-like assistant behavior | `Tobi/agent/coordinator.py`; `Tobi/core/server.py` | PARTIAL | Source inspection only | In-app chat/voice and tools exist; OS-wide assistant integration was not found. |
| On-screen roaming avatar / overlay | `Tobi/ui/tobi-ui/src/components/cinematic` | PARTIAL | Production build passed; browser rendered the face view | The PWA has a full-screen animated orb, expressive face, or static TOBI mark. No floating overlay exists; iOS does not allow third-party apps to draw over other apps, and Android needs a native companion with user-granted overlay permission. |
| Open apps and perform tasks | `Tobi/tools/mac_control.py`; `Tobi/tools/windows_control.py`; `Tobi/tools/shell.py` | PARTIAL | Source inspection only | Desktop controls exist; Android accessibility automation is absent and no end-to-end action check was run. |
| Voice-recorded reminders | `Tobi/agent/reminder_tools.py`; `Tobi/memory/reminders_store.py`; `Tobi/core/server.py` | PARTIAL | Source inspection; general backend tests passed | Reminder and audio endpoints exist; reminder-specific runtime/voice tests were not found. |
| Notes and personal assistant | `Tobi/tools/notes_access.py`; `Tobi/memory`; `Tobi/ui/tobi-ui/src/components/chat/ChatView.tsx` | PARTIAL | Source inspection; production build passed | Desktop Apple Notes access exists. PWA users can explicitly paste or upload plain-text/Markdown note content in Chat; it is sent only after confirmation and is not an automatic sync. iOS does not grant a PWA general access to private app data. |
| IDE coding features | `Tobi/extensions/vscode` | PARTIAL | Source inspection only | A VS Code extension exists; the full narrated-coding, audit, and concept-checkpoint workflow was not verified. |
| Learn about the owner over time | `Tobi/memory/facts.py`; `Tobi/memory/preferences.py`; `Tobi/agent/learning.py` | PARTIAL | General memory/learning tests passed | Memory and learning logic have unit coverage; nightly review and an editable weekly learning card were not found. |
| Connect multiple AI providers | `Tobi/core/multi_llm.py`; `Tobi/core/api_key_vault.py` | PARTIAL | Source inspection only | Provider selection and local key storage exist; end-to-end provider routing, per-task controls, and chat import were not verified. |
| Alarms, reminders, calendar, study | `Tobi/agent/reminder_tools.py`; `Tobi/tools/calendar_email.py`; `Tobi/tools/google_workspace.py`; `Tobi/core/digest.py` | PARTIAL | Reminder tests not present; 5 mocked Google Workspace unit tests pass | Reminder/digest and macOS Calendar tools exist. Google Calendar read APIs are implemented but not live-verified; spaced-repetition study mode and chained reminders were not found. |
| Daily memory snapshot (“you, today”) | — | MISSING | Source scan | No encrypted snapshot/restore history was found. |
| Back up phone and files | — | MISSING | Source scan | Local file tools are not backup/restore; scheduled encrypted backup to user storage and Android backup are absent. |
| Security-first protections | `Tobi/core/auth.py`; `Tobi/core/hardening.py`; `Tobi/core/api_key_vault.py`; `Tobi/core/server.py` | PARTIAL | Hardening tests passed; production npm audit is clean; static inspection | Auth/hardening code exists, but the full requested permission center, audit log, deletion workflow, and security gate are absent. GitHub reported 41 dependency alerts on the default branch (6 critical, 18 high, 15 moderate, 2 low) when the prior commit was pushed. |
| Connect and sync across devices | `Tobi/core/server.py` | PARTIAL | Source inspection only | A connected-devices endpoint exists; shared-account sync and “send to my other device” were not found. |
| “Connect to your county/country” | — | MISSING | Source scan | The requirement is unclear; no country-specific service integration was found. |
| Daily task plan | `Tobi/core/digest.py`; `Tobi/agent/planner.py`; `Tobi/core/server.py` | PARTIAL | Planning tests passed; source inspection | Task planning and digest exist; no editable, automatically generated daily plan with recap was verified. |
| Forgot detector | `Tobi/core/digest.py`; `Tobi/memory` | PARTIAL | Source inspection only | Reminders, goals, and facts feed digest-related logic. The requested daily cross-source loose-ends detector and one-tap conversion were not found. |
| WhatsApp messages / phone notifications | — | MISSING | Source scan | No WhatsApp import or Android notification listener exists. Native Android notification access requires an opt-in companion app. |
| Capture and save photos | — | MISSING | Source scan | No camera-capture or photo-description workflow was found. |
| Emergency call and location message | — | MISSING | Source scan | No confirmed emergency-contact calling or location-SMS workflow was found. |
| Directions and saved places | — | MISSING | Source scan | Routing, saved places, and leave-by alerts were not found. |
| Contacts | `Tobi/tools/crm.py`; `Tobi/ui/tobi-ui/src/components/settings/PwaInstallCard.tsx` | PARTIAL | Source inspection; production build passed | CRM contacts exist. The PWA offers Contact Picker API selection where a browser supports it, followed by user review and explicit import; iOS Safari does not expose this API. |
| Translation / interpreter mode | — | MISSING | Source scan | No translation or live interpreter workflow was found. |
| Opt-in brutal-honesty mode | `Tobi/core/weekly_retro.py`; `Tobi/core/profile.py` | PARTIAL | Source inspection only | Retrospective and profile logic exist; the opt-in tone setting and goal-vs-activity behavior were not found. |
| “First to do everything a human wants” | — | BLOCKED | Not a testable feature | This is an unbounded vision claim, not an implementable or verifiable capability. |
| Web-first PWA | `Tobi/ui/tobi-ui/src/app/layout.tsx`; `Tobi/ui/tobi-ui/public/manifest.json`; `Tobi/ui/tobi-ui/public/sw.js`; `Tobi/ui/tobi-ui/src/components/settings/PwaInstallCard.tsx` | PARTIAL | Manifest/service worker inspected; production build passed; `/` returned HTTP 200; install guidance rendered in browser | Install metadata, icons, app-shell caching, and an in-app install/help entry point are present. Phone installation is not verified; HTTPS hosting with secure API/WebSocket routing is not configured. Offline use does not include live assistant/backend functionality. |
| White clean UI, shared layout, and TOBI icon | `Tobi/ui/tobi-ui/src/app/layout.tsx`; `Tobi/ui/tobi-ui/src/styles/globals.css`; `Tobi/ui/tobi-ui/public` | PARTIAL | Frontend build passed; source inspection | A white/slate/blue palette, self-hosted fonts, and existing TOBI icon are in place. A complete visual/accessibility review remains outstanding; no claim is made that this is a newly designed geometric logo. |
| First-run onboarding | `Tobi/ui/tobi-ui/src/components/onboarding/OnboardingWizard.tsx`; `Tobi/core/server.py` | PARTIAL | Frontend lint, TypeScript, and production build passed; Google status unit test passed | Guided setup persists nickname, orb/face/mark character, voice-input preference, and Kokoro voice; it can request browser notification permission and offers optional Google Workspace connection. Full login/onboarding API verification remains outstanding because the backend was unavailable. |
| Permission center | `Tobi/core/server.py`; `Tobi/ui/tobi-ui/src` | MISSING | Source scan | No per-tool permission management screen was found. |
| User-visible action/audit log | `Tobi/core/server.py`; `Tobi/agent/learning.py` | PARTIAL | Source inspection only | Agent/learning history exists; a complete user-visible record of every tool action and reason was not found. |
| Panic button | `Tobi/ui/tobi-ui/src` | MISSING | Source scan | No stop-all-agents and sensitive-context clearing control was found. |
| LLM cost meter | `Tobi/core/cost_tracker.py`; `Tobi/core/server.py`; `Tobi/ui/tobi-ui/src/components/dashboard/DashboardView.tsx` | PARTIAL | Cost-tracker tests passed; source inspection | Cost tracking and dashboard data exist; a daily UI meter/alert was not manually verified. |
| Offline reminders, notes, and alarms | `Tobi/ui/tobi-ui/public/sw.js`; `Tobi/memory/reminders_store.py` | PARTIAL | Source inspection only | Service-worker shell caching exists; offline reminder execution/storage was not verified. |
| Quiet hours and focus mode | `Tobi/core/focus_mode.py`; `Tobi/core/proactive.py` | PARTIAL | Source inspection only | Focus mode exists; quiet-hour scheduling and its UI were not verified. |
| Export all user data | `Tobi/memory`; `Tobi/core/api_key_vault.py` | MISSING | Source scan | No complete data export/import workflow was found. |
| Command palette and shortcuts | `Tobi/ui/tobi-ui/src` | MISSING | Source scan | No command palette was found. |
| Weekly review card | `Tobi/core/weekly_retro.py`; `Tobi/ui/tobi-ui/src` | PARTIAL | Source inspection only | Retrospective generation exists; a review card with the requested activity/dodged-goal view was not found. |
| Android companion app | — | MISSING | Repository inventory | No `android/` project exists. Wake-word background service, overlay, notification listener, accessibility service, and Android backup are unimplemented. The PWA is not a native Android package. |
| Deployment pipeline and status/onboarding pages | `.github/workflows/ui-build.yml`; `Tobi/ui/tobi-ui/src` | PARTIAL | Workflow/source inspection | A UI-only build workflow exists. The requested full CI gate, Docker/cloud deployment setup, and status page are absent. |
