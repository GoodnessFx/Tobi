"""
Tobi FastAPI Server
HTTP + WebSocket API for interacting with Tobi.
Used by the UI and can also be used by iPhone/external clients.
"""
import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from Tobi.config import settings
from Tobi.core import auth, cost_tracker
from Tobi.core import profile as user_profile
from Tobi.core.brain import TobiBrain
from Tobi.core.settings_api import settings_router
from Tobi.tools import chrome_extension, google_workspace

logger = logging.getLogger("Tobi.server")

# Global brain instance
brain = TobiBrain()

# Voice components set by run_full for browser TTS triggering
_speaker = None
_listener = None

# Desktop overlay WebSocket clients (lightweight, no auth required for localhost)
_overlay_clients: List[WebSocket] = []
_overlay_state: str = "idle"  # idle, listening, thinking, speaking
_overlay_text: str = ""  # latest assistant response text for overlay display
_overlay_user_text: str = ""  # latest user utterance for overlay display


async def broadcast_overlay_state(new_state: str, text: str | None = None, user_text: str | None = None):
    """Broadcast state change to all connected desktop overlay clients.

    Args:
        new_state: One of idle, listening, thinking, speaking.
        text: Optional assistant response text to display on the overlay.
        user_text: Optional user utterance to display on the overlay.
    """
    global _overlay_state, _overlay_text, _overlay_user_text
    _overlay_state = new_state
    if text is not None:
        _overlay_text = text
    if user_text is not None:
        _overlay_user_text = user_text
    if not _overlay_clients:
        return
    payload = {"state": new_state, "text": _overlay_text, "userText": _overlay_user_text}
    dead = []
    for ws in _overlay_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _overlay_clients.remove(ws)


def set_voice_components(speaker, listener=None):
    """Register voice speaker/listener for WebSocket TTS triggering."""
    global _speaker, _listener
    _speaker = speaker
    _listener = listener
    logger.info("Voice components registered with server (speaker=%s, listener=%s)",
                type(speaker).__name__ if speaker else None,
                type(listener).__name__ if listener else None)


class ClientInfo:
    """Metadata about a connected WebSocket client."""

    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.device_type: str = "unknown"  # "phone", "tablet", "desktop", "unknown"
        self.device_name: str = ""         # user-friendly name, e.g. "iPhone 15"
        self.wants_audio: bool = True      # whether this client wants TTS audio
        self.connected_at: float = time.time()
        self.last_activity: float = time.time()

    def to_dict(self) -> dict:
        """Serialize client info for API responses."""
        return {
            "device_type": self.device_type,
            "device_name": self.device_name,
            "wants_audio": self.wants_audio,
            "connected_at": self.connected_at,
            "last_activity": self.last_activity,
            "uptime_seconds": round(time.time() - self.connected_at, 1),
        }


class ConnectionManager:
    """Tracks active WebSocket clients with device metadata for smart routing.

    Each client can register with device type and audio preferences.
    Supports device-targeted audio routing, audio interruption, and
    connection health monitoring.
    """

    def __init__(self):
        self.active: List[WebSocket] = []
        self._clients: dict[WebSocket, ClientInfo] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        await self._prune_stale()
        self.active.append(ws)
        self._clients[ws] = ClientInfo(ws)
        logger.info("WebSocket client connected. Total: %d", len(self.active))

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)
        self._clients.pop(ws, None)
        logger.info("WebSocket client disconnected. Total: %d", len(self.active))

    def register_client(self, ws: WebSocket, info: dict):
        """Update client metadata after a registration message.

        Expected fields in info:
            device_type: "phone" | "tablet" | "desktop"
            device_name: human-readable name (optional)
            wants_audio: bool (default True)
        """
        client = self._clients.get(ws)
        if not client:
            return
        if "device_type" in info:
            client.device_type = str(info["device_type"])
        if "device_name" in info:
            client.device_name = str(info["device_name"])
        if "wants_audio" in info:
            client.wants_audio = bool(info["wants_audio"])
        logger.info(
            "Client registered: type=%s, name='%s', wants_audio=%s",
            client.device_type, client.device_name, client.wants_audio,
        )

    def get_client_info(self, ws: WebSocket) -> ClientInfo | None:
        """Get metadata for a connected client."""
        return self._clients.get(ws)

    def get_audio_clients(self, exclude: WebSocket | None = None) -> list[WebSocket]:
        """Return all clients that want audio, optionally excluding one."""
        return [
            ws for ws, info in self._clients.items()
            if info.wants_audio and ws is not exclude and ws in self.active
        ]

    def get_connected_devices(self) -> list[dict]:
        """Return a summary of all connected devices."""
        return [info.to_dict() for info in self._clients.values()]

    def touch(self, ws: WebSocket):
        """Update last_activity timestamp for a client."""
        client = self._clients.get(ws)
        if client:
            client.last_activity = time.time()

    async def _prune_stale(self):
        """Remove connections that are no longer alive."""
        stale = []
        for ws in self.active:
            try:
                await ws.send_json({"ping": True})
            except Exception:
                stale.append(ws)
        for ws in stale:
            if ws in self.active:
                self.active.remove(ws)
            self._clients.pop(ws, None)
        if stale:
            logger.info("Pruned %d stale WebSocket connection(s). Active: %d",
                        len(stale), len(self.active))

    async def broadcast_json(self, data: dict, exclude: WebSocket | None = None):
        """Send a JSON message to all connected clients.

        Args:
            data: JSON-serializable dict to send
            exclude: Optional WebSocket to skip (used for device-targeted routing)
        """
        disconnected = []
        for ws in self.active:
            if ws is exclude:
                continue
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_to_audio_clients(
        self, data: dict, exclude: WebSocket | None = None
    ):
        """Send a JSON message only to clients that want audio.

        Used for terminal-originated voice responses where we want to send
        audio to all clients that opted in, but skip animation-only clients.
        """
        disconnected = []
        for ws, info in list(self._clients.items()):
            if ws is exclude or not info.wants_audio or ws not in self.active:
                continue
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    async def send_to(self, ws: WebSocket, data: dict):
        """Send a JSON message to a specific client only."""
        try:
            await ws.send_json(data)
        except Exception:
            self.disconnect(ws)


ws_manager = ConnectionManager()


async def broadcast_voice_interaction(user_text: str, response: str):
    """
    Called by the voice pipeline to push voice interactions to the UI.
    Sends the complete response immediately (no word-by-word simulation)
    since the voice is already speaking it aloud.
    """
    if not ws_manager.active:
        logger.info("No active WebSocket clients; skipping voice broadcast.")
        return

    logger.info("Broadcasting voice interaction to %d UI client(s).", len(ws_manager.active))

    await ws_manager.broadcast_json({
        "voice_user_message": user_text,
    })

    await asyncio.sleep(0.05)

    await ws_manager.broadcast_json({
        "token": response,
        "done": False,
    })

    await asyncio.sleep(0.02)

    await ws_manager.broadcast_json({
        "token": "",
        "done": True,
        "full_response": response,
        "backend": brain.llm.active_backend,
        "session_cost": brain.llm.get_cost_summary(),
        "source": "voice",
    })


async def broadcast_voice_state(
    speaking: bool,
    amplitude_envelope: list[float] | None = None,
    audio_duration: float = 0.0,
    audio_base64: str | None = None,
    target_ws: WebSocket | None = None,
    audio_format: str = "audio/wav",
):
    """Signal to the UI whether TTS is actively speaking aloud.

    Called before speaker.speak() starts (speaking=True) and after
    it finishes (speaking=False). The UI uses this to keep the
    orb in the speaking animation for the full duration of the voice.

    When speaking=True, optionally includes:
    - amplitude_envelope: for audio-reactive visualization
    - audio_base64: WAV audio encoded as base64 for browser playback

    Device-targeted audio routing (smart routing):
    - voice_speaking + amplitude_envelope are broadcast to ALL clients (orb animation)
    - voice_audio (the heavy WAV payload) routing depends on the origin:
      1. Browser-originated (target_ws set): audio to requesting client only
      2. Terminal-originated (target_ws=None): audio to all clients that
         registered with wants_audio=True (respects per-device preferences)
    """
    if not ws_manager.active:
        return

    base_payload: dict = {"voice_speaking": speaking}
    if speaking and amplitude_envelope:
        base_payload["amplitude_envelope"] = amplitude_envelope
        base_payload["audio_duration"] = audio_duration

    if speaking and audio_base64 and target_ws:
        audio_size_kb = len(audio_base64) // 1024
        logger.info(
            "Sending voice_audio (%d KB) to target client. "
            "Broadcasting animation to %d other client(s).",
            audio_size_kb, len(ws_manager.active) - 1,
        )
        audio_payload = {**base_payload, "voice_audio": audio_base64, "audio_format": audio_format}
        await ws_manager.send_to(target_ws, audio_payload)
        await ws_manager.broadcast_json(base_payload, exclude=target_ws)
    elif speaking and audio_base64:
        audio_size_kb = len(audio_base64) // 1024
        audio_clients = ws_manager.get_audio_clients()
        non_audio_count = len(ws_manager.active) - len(audio_clients)

        if audio_clients and non_audio_count > 0:
            logger.info(
                "Sending voice_audio (%d KB) to %d audio client(s), "
                "animation to %d non-audio client(s).",
                audio_size_kb, len(audio_clients), non_audio_count,
            )
            audio_payload = {**base_payload, "voice_audio": audio_base64, "audio_format": audio_format}
            for ws in audio_clients:
                await ws_manager.send_to(ws, audio_payload)
            for ws in ws_manager.active:
                if ws not in audio_clients:
                    await ws_manager.send_to(ws, base_payload)
        else:
            logger.info(
                "Broadcasting voice_audio (%d KB) to ALL %d client(s) (terminal voice).",
                audio_size_kb, len(ws_manager.active),
            )
            base_payload["voice_audio"] = audio_base64
            base_payload["audio_format"] = audio_format
            await ws_manager.broadcast_json(base_payload)
    else:
        await ws_manager.broadcast_json(base_payload)


async def broadcast_voice_chunk(
    chunk_base64: str,
    chunk_index: int,
    is_last: bool,
    chunk_envelope: list[float],
    chunk_duration: float,
    target_ws: WebSocket | None = None,
    audio_format: str = "audio/wav",
):
    """Send a streamed audio chunk to browser clients.

    Called by the speaker as each chunk of audio becomes available,
    enabling faster time-to-first-audio. The browser queues chunks
    and plays them sequentially.

    Args:
        chunk_base64: audio chunk encoded as base64 (WAV or Opus/WebM)
        chunk_index: sequential chunk number (0-based)
        is_last: True if this is the final chunk
        chunk_envelope: amplitude envelope for this chunk
        chunk_duration: duration of this chunk in seconds
        target_ws: send only to this client (browser-originated), or all if None
        audio_format: MIME type of the audio (e.g., "audio/wav", "audio/webm;codecs=opus")
    """
    if not ws_manager.active:
        return

    payload = {
        "voice_audio_chunk": {
            "audio": chunk_base64,
            "index": chunk_index,
            "is_last": is_last,
            "envelope": chunk_envelope,
            "duration": chunk_duration,
            "format": audio_format,
        }
    }

    if target_ws:
        await ws_manager.send_to(target_ws, payload)
    else:
        # Terminal-originated: send to audio-enabled clients only
        audio_clients = ws_manager.get_audio_clients()
        if audio_clients:
            for ws in audio_clients:
                await ws_manager.send_to(ws, payload)
        else:
            await ws_manager.broadcast_json(payload)


async def broadcast_plan_progress(event: dict):
    """Broadcast a task plan progress event to all connected UI clients.

    Called by TobiBrain when a plan is created, subtasks start/complete/fail,
    or the overall plan finishes. The UI can render a progress indicator.

    Event types:
        plan_created, subtask_started, subtask_completed,
        subtask_failed, subtask_skipped, plan_completed
    """
    if not ws_manager.active:
        return
    payload = {"plan_progress": event}
    await ws_manager.broadcast_json(payload)


async def _deliver_proactive_suggestion(suggestion):
    """Deliver a proactive suggestion from the background engine.

    Broadcasts the suggestion text to all connected UI clients via WebSocket.
    Optionally speaks it aloud via TTS if the suggestion is marked as spoken
    and a voice speaker is available.
    """
    from Tobi.core.proactive import Suggestion

    if not ws_manager.active:
        logger.debug("No WebSocket clients for proactive suggestion; skipping.")
        return

    logger.info(
        "Delivering proactive suggestion [%s]: %s",
        suggestion.category.value,
        suggestion.message[:80],
    )

    await ws_manager.broadcast_json({
        "proactive_suggestion": {
            "category": suggestion.category.value,
            "message": suggestion.message,
            "priority": suggestion.priority,
            "spoken": suggestion.spoken,
            "timestamp": suggestion.timestamp,
        }
    })

    if suggestion.spoken and _speaker:
        try:
            async def on_audio_ready(envelope, duration, audio_b64=None):
                await broadcast_voice_state(
                    True,
                    amplitude_envelope=envelope,
                    audio_duration=duration,
                    audio_base64=audio_b64,
                )

            await _speaker.speak(
                suggestion.message,
                on_audio_ready=on_audio_ready,
            )
            await broadcast_voice_state(False)
        except Exception as e:
            logger.error("TTS failed for proactive suggestion: %s", e)
            await broadcast_voice_state(False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with signal handling for graceful termination."""
    import signal

    logger.info("Starting Tobi server...")
    success = await brain.initialize()
    if not success:
        logger.warning(
            "Brain initialization incomplete. Some features may be unavailable."
        )
    brain._on_plan_progress = broadcast_plan_progress
    brain.proactive._on_suggestion = _deliver_proactive_suggestion
    # Register memory store for goal-drift checks
    brain.proactive.set_memory(brain.memory)

    # Start the always-on intel engine
    from Tobi.core.intel_engine import intel_engine
    intel_engine.start()

    cleanup_task = asyncio.create_task(_session_cleanup_loop())

    # Register signal handlers for graceful shutdown. When uvicorn receives
    # SIGTERM (e.g., from Docker, systemd, or launchd) or SIGINT (Ctrl+C),
    # we want to persist state before the process exits.
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _signal_handler(sig: signal.Signals):
        sig_name = sig.name if hasattr(sig, "name") else str(sig)
        logger.info("Received %s, initiating graceful shutdown...", sig_name)
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_handler, sig)
        except NotImplementedError:
            # Windows does not support add_signal_handler; fall through
            # to uvicorn's default handler.
            pass

    yield

    # Stop the intel engine on shutdown
    from Tobi.core.intel_engine import intel_engine
    intel_engine.stop()

    cleanup_task.cancel()
    await brain.shutdown()
    logger.info("Tobi server shut down.")


app = FastAPI(
    title="J.A.R.V.I.S.",
    description="Just A Rather Very Intelligent System",
    version="0.3.0",
    lifespan=lifespan,
)

_cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3741",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3741",
    f"http://localhost:{settings.API_PORT}",
    f"http://127.0.0.1:{settings.API_PORT}",
]

# Also allow any localhost port so Next.js auto-port shifting never breaks CORS
_LOCAL_PORT_REGEX = r"http://(localhost|127\.0\.0\.1):\d+"

_tunnel_domain = os.environ.get("Tobi_TUNNEL_DOMAIN", "")
if _tunnel_domain:
    _cors_origins.append(f"https://{_tunnel_domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"(https://.*\.trycloudflare\.com|http://(localhost|127\.0\.0\.1):\d+)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["authorization", "content-type", "x-requested-with"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all HTTP responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' ws://localhost:* wss://localhost:* ws://127.0.0.1:* wss://127.0.0.1:*; "
        "media-src 'self' blob:; "
        "frame-ancestors 'none'"
    )
    response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
    return response


_CSRF_EXEMPT_PATHS = {"/auth/login", "/auth/status", "/auth/logout", "/voice/transcribe"}

@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Require X-Tobi-Client header on state-changing requests from non-local origins."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        if request.url.path not in _CSRF_EXEMPT_PATHS:
            client_host = request.client.host if request.client else ""
            if not auth.is_local_request(client_host):
                Tobi_header = request.headers.get("x-Tobi-client", "")
                if not Tobi_header:
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Missing X-Tobi-Client header. CSRF protection."},
                    )
    return await call_next(request)


# Mount settings API router (configuration, status, integration tests)
app.include_router(settings_router)

_startup_pin = auth.initialize_pin()


class PinRequest(BaseModel):
    pin: str


class SetPinRequest(BaseModel):
    current_pin: str
    new_pin: str


async def require_auth(request: Request) -> bool:
    """FastAPI dependency for PIN auth. Local connections bypass auth.

    Remote connections require valid session token via header, cookie, or query param.
    """
    client_host = request.client.host if request.client else ""

    if auth.is_local_request(client_host):
        return True

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if auth.validate_token(token):
            return True

    token = request.cookies.get("Tobi_token", "")
    if token and auth.validate_token(token):
        return True

    token = request.query_params.get("token", "")
    if token and auth.validate_token(token):
        logger.warning("Auth via query param token (less secure). Use Authorization header or cookie instead.")
        return True

    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Authentication required. Please log in with your PIN.")


@app.post("/auth/login")
async def auth_login(request: Request, body: PinRequest):
    """Verify the PIN and return a session token.

    This endpoint is always accessible (no auth required).
    Rate-limited by client IP.
    """
    client_host = request.client.host if request.client else ""
    token = auth.verify_pin(body.pin, client_ip=client_host)

    if token is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid PIN or rate limit exceeded."},
        )

    response = JSONResponse(content={"token": token, "expires_in": auth.SESSION_TOKEN_EXPIRY})
    response.set_cookie(
        key="Tobi_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=auth.SESSION_TOKEN_EXPIRY,
    )
    return response


@app.get("/auth/status")
async def auth_status(request: Request):
    """Check whether the current request is authenticated."""
    client_host = request.client.host if request.client else ""

    if auth.is_local_request(client_host):
        return {"authenticated": True, "local": True}

    for token_source in [
        request.headers.get("authorization", "").removeprefix("Bearer "),
        request.cookies.get("Tobi_token", ""),
        request.query_params.get("token", ""),
    ]:
        if token_source and auth.validate_token(token_source):
            return {"authenticated": True, "local": False}

    return {"authenticated": False, "local": False}


@app.post("/auth/logout")
async def auth_logout(request: Request):
    """Revoke the current session token."""
    # Find and revoke the token from any source
    for token_source in [
        request.headers.get("authorization", "").removeprefix("Bearer "),
        request.cookies.get("Tobi_token", ""),
        request.query_params.get("token", ""),
    ]:
        if token_source:
            auth.revoke_token(token_source)

    response = JSONResponse(content={"status": "logged out"})
    response.delete_cookie("Tobi_token")
    return response


@app.post("/auth/set-pin", dependencies=[Depends(require_auth)])
async def auth_set_pin(request: Request, body: SetPinRequest):
    """Change the PIN. Requires current PIN verification first."""
    client_host = request.client.host if request.client else ""

    token = auth.verify_pin(body.current_pin, client_ip=client_host)
    if token is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Current PIN is incorrect."},
        )
    auth.revoke_token(token)

    if not auth.set_pin(body.new_pin):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid PIN format. Must be 4-8 digits."},
        )

    return {"status": "PIN updated. All sessions invalidated. Please log in again."}


def get_startup_pin() -> str:
    """Return the PIN generated at startup, or empty if loaded from previous session."""
    return _startup_pin


async def _session_cleanup_loop():
    while True:
        await asyncio.sleep(300)
        auth.cleanup_expired_sessions()


# ============================================================
# Request/Response Models
# ============================================================
class ChatRequest(BaseModel):
    message: str
    tier: str = ""


class ChatResponse(BaseModel):
    response: str
    elapsed_ms: float
    tier_used: str
    backend: str


class StatusResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    active_backend: str
    active_model: str
    memory_stats: dict
    conversation_turns: int
    session_cost: dict


_start_time = time.time()


@app.get("/", response_model=StatusResponse, dependencies=[Depends(require_auth)])
async def status():
    """Health check and status."""
    return StatusResponse(
        status="online",
        version="0.3.0",
        uptime_seconds=round(time.time() - _start_time, 1),
        active_backend=brain.llm.active_backend,
        active_model=brain.llm.get_active_model(),
        memory_stats=brain.memory.get_stats(),
        conversation_turns=len(brain.conversation),
        session_cost=brain.llm.get_cost_summary(),
    )


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_auth)])
async def chat(request: ChatRequest):
    """Send a text message and get a response."""
    if len(request.message) > 50000:
        return JSONResponse(
            status_code=400,
            content={"error": "Message too long (max 50,000 characters)."},
        )
    start = time.time()
    response = await brain.process(request.message)
    elapsed = (time.time() - start) * 1000

    tier_used = "unknown"
    if brain.conversation:
        last = brain.conversation[-1]
        if last.role == "assistant":
            tier_used = last.tier_used or "brain"

    return ChatResponse(
        response=response,
        elapsed_ms=round(elapsed, 1),
        tier_used=tier_used,
        backend=brain.llm.active_backend,
    )


@app.post("/clear", dependencies=[Depends(require_auth)])
async def clear_conversation():
    """Clear the current conversation."""
    brain.clear_conversation()
    return {"status": "conversation cleared"}


@app.get("/health/ping")
async def health_ping():
    """Lightweight unauthenticated liveness probe.

    Used by the Chrome extension's alarm-based keepalive to detect
    whether the server is running before attempting a WebSocket connection.
    Returns minimal data to avoid leaking internal state.
    """
    return {"status": "ok"}


@app.get("/health", dependencies=[Depends(require_auth)])
async def health():
    """Simple health check for monitoring."""
    from Tobi.core.hardening import get_health_report
    from Tobi.core.perf import perf_tracker
    from Tobi.core.cache import tool_cache
    return {
        "healthy": brain.llm.active_backend != "none",
        "backend": brain.llm.active_backend,
        "model": brain.llm.get_active_model(),
        "memory": brain.memory.get_stats(),
        "hardening": get_health_report(),
        "perf_summary": perf_tracker.get_summary_line(),
        "cache": tool_cache.get_stats(),
    }


@app.get("/perf", dependencies=[Depends(require_auth)])
async def perf():
    """Get performance metrics and latency data."""
    from Tobi.core.perf import perf_tracker
    return perf_tracker.get_stats()


@app.get("/cache", dependencies=[Depends(require_auth)])
async def cache_stats():
    """Get tool result cache statistics."""
    from Tobi.core.cache import tool_cache
    return tool_cache.get_stats()


@app.post("/cache/clear", dependencies=[Depends(require_auth)])
async def cache_clear():
    """Clear the entire tool result cache."""
    from Tobi.core.cache import tool_cache
    await tool_cache.invalidate()
    return {"status": "ok", "message": "Cache cleared."}


@app.get("/devices", dependencies=[Depends(require_auth)])
async def connected_devices():
    """Get list of connected WebSocket clients with device info."""
    return {
        "count": len(ws_manager.active),
        "devices": ws_manager.get_connected_devices(),
    }


@app.post("/audio/stop", dependencies=[Depends(require_auth)])
async def stop_audio():
    """Stop all active TTS playback on all devices."""
    if _speaker:
        _speaker.stop_speaking()
    await ws_manager.broadcast_json({"voice_stop": True})
    await broadcast_voice_state(False)
    if _listener and _listener._is_speaking:
        _listener.set_speaking(False, open_followup=False)
    return {"status": "ok", "message": "Audio stopped on all devices."}


@app.get("/costs", dependencies=[Depends(require_auth)])
async def costs():
    """Get cost tracking data."""
    return {
        "session": brain.llm.get_cost_summary(),
        "today": cost_tracker.get_today_summary(),
        "month": cost_tracker.get_month_summary(),
    }


@app.get("/models", dependencies=[Depends(require_auth)])
async def models():
    """Get available model tiers and their configuration."""
    from Tobi.core.llm import TIER_CONFIG
    return {
        "active_backend": brain.llm.active_backend,
        "tiers": {
            tier: {
                "model": config["model"],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
            }
            for tier, config in TIER_CONFIG.items()
        },
        "ollama_model": settings.OLLAMA_MODEL,
        "prefer_claude": settings.PREFER_CLAUDE,
    }


class ProfileUpdateRequest(BaseModel):
    key: str
    value: str


@app.get("/profile", dependencies=[Depends(require_auth)])
async def get_profile():
    """Get the full user profile."""
    return user_profile.get_profile()


_ALLOWED_PROFILE_KEYS = {
    "name", "nickname", "location", "timezone", "language",
    "communication_style", "interests", "occupation",
    "wake_time", "sleep_time", "theme", "voice", "character",
    "voice_input_enabled",
}


@app.put("/profile", dependencies=[Depends(require_auth)])
async def update_profile_endpoint(body: ProfileUpdateRequest):
    """Update a profile field or preference."""
    if body.key not in _ALLOWED_PROFILE_KEYS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown profile key: '{body.key}'. Allowed: {sorted(_ALLOWED_PROFILE_KEYS)}"},
        )
    updated = user_profile.update_profile({body.key: body.value})
    return {"status": "updated", "profile": updated}


@app.get("/integrations/google/status", dependencies=[Depends(require_auth)])
async def google_workspace_status_endpoint():
    """Return whether Google Workspace can be connected without exposing credentials."""
    return google_workspace.google_workspace_connection_status()


@app.post("/integrations/google/connect", dependencies=[Depends(require_auth)])
async def connect_google_workspace_endpoint():
    """Start the user-requested Google OAuth installed-app flow."""
    try:
        await google_workspace.connect_google_workspace_account()
    except google_workspace.GoogleWorkspaceNotConfiguredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return google_workspace.google_workspace_connection_status()


@app.get("/profile/{key}", dependencies=[Depends(require_auth)])
async def get_profile_preference(key: str):
    """Get a single profile preference."""
    value = user_profile.get_preference(key)
    if value is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Preference '{key}' not found."},
        )
    return {"key": key, "value": value}


@app.get("/plan", dependencies=[Depends(require_auth)])
async def get_active_plan():
    """Get the active task plan status, if any."""
    plan = brain.planner.get_active_plan()
    if plan is None:
        return {"active": False, "plan": None}
    return {
        "active": True,
        "plan": plan.to_dict(),
        "progress": plan.progress_pct,
        "summary": plan.progress_summary(),
    }


@app.get("/plan/history", dependencies=[Depends(require_auth)])
async def get_plan_history():
    """Get recent completed task plans."""
    plans = brain.planner.tracker.load_recent_plans(limit=10)
    return {"plans": plans, "count": len(plans)}


@app.get("/learning", dependencies=[Depends(require_auth)])
async def get_learning_insights():
    """Get a comprehensive summary of learning loop insights."""
    return brain.learning.get_insights_summary()


@app.get("/learning/tools", dependencies=[Depends(require_auth)])
async def get_tool_reliability():
    """Get tool reliability scores and statistics."""
    return {
        "tools": brain.learning.get_tool_reliability_report(),
        "unreliable": brain.learning.get_unreliable_tools(),
    }


@app.get("/learning/failures", dependencies=[Depends(require_auth)])
async def get_failure_patterns():
    """Get common failure patterns identified by the learning loop."""
    return {
        "patterns": brain.learning.get_common_failure_patterns(limit=10),
        "plan_stats": brain.learning.get_plan_success_rate(),
    }


@app.get("/calendar", dependencies=[Depends(require_auth)])
async def get_calendar_today():
    """Quick access to today's calendar events."""
    from Tobi.tools.calendar_email import get_upcoming_events
    events = await get_upcoming_events(days=1)
    return {"events": events}


@app.get("/mail/unread", dependencies=[Depends(require_auth)])
async def get_mail_unread():
    """Quick access to unread email count."""
    from Tobi.tools.calendar_email import get_unread_count
    count = await get_unread_count()
    return {"unread": count}


class ProactiveSettingsRequest(BaseModel):
    enabled: bool | None = None
    category: str | None = None
    category_enabled: bool | None = None


@app.get("/proactive", dependencies=[Depends(require_auth)])
async def get_proactive_status():
    """Get the proactive suggestions engine status."""
    return brain.proactive.get_status()


@app.get("/agents", dependencies=[Depends(require_auth)])
async def get_agents_status():
    """Get the multi-agent coordinator status and all agent profiles."""
    return brain.coordinator.get_status()


@app.get("/agents/active", dependencies=[Depends(require_auth)])
async def get_active_agents():
    """Get currently running agent tasks."""
    return {
        "active": brain.coordinator.get_active_agents(),
        "count": len(brain.coordinator.get_active_agents()),
    }


@app.get("/agents/history", dependencies=[Depends(require_auth)])
async def get_agent_history():
    """Get recent agent execution history."""
    return {
        "history": brain.coordinator.get_execution_history(limit=20),
    }


@app.post("/proactive/settings", dependencies=[Depends(require_auth)])
async def update_proactive_settings(body: ProactiveSettingsRequest):
    """Update proactive engine settings.

    Toggle the entire engine on/off, or enable/disable specific categories.
    """
    from Tobi.core.proactive import SuggestionCategory

    if body.enabled is not None:
        brain.proactive.set_enabled(body.enabled)

    if body.category and body.category_enabled is not None:
        try:
            cat = SuggestionCategory(body.category)
            brain.proactive.set_category_enabled(cat, body.category_enabled)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Unknown category: {body.category}. "
                    f"Valid: {[c.value for c in SuggestionCategory]}"
                },
            )

    return brain.proactive.get_status()


_whisper_model = None
_whisper_lock = asyncio.Lock()


async def _get_whisper_model():
    """Lazy-load the Whisper model for browser voice transcription."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    async with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model

        try:
            from faster_whisper import WhisperModel
            loop = asyncio.get_event_loop()
            _whisper_model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    settings.WHISPER_MODEL,
                    device="cpu",
                    compute_type="int8",
                ),
            )
            logger.info("Whisper model loaded for browser transcription: %s", settings.WHISPER_MODEL)
        except ImportError:
            logger.error("faster-whisper not installed. Browser voice input disabled.")
        except Exception as e:
            logger.error("Failed to load Whisper model: %s", e)

        return _whisper_model


@app.post("/voice/transcribe", dependencies=[Depends(require_auth)])
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio from the browser microphone.

    Accepts WebM/WAV/OGG audio files from MediaRecorder.
    Returns the transcribed text.
    """
    import tempfile
    import subprocess
    import numpy as np

    model = await _get_whisper_model()
    if model is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Speech-to-text model not available"},
        )

    allowed_types = {"audio/webm", "audio/wav", "audio/ogg", "audio/mpeg", "audio/mp4", "audio/x-wav"}
    # Strip codec parameters (e.g. "audio/webm;codecs=opus" -> "audio/webm")
    base_content_type = (audio.content_type or "").split(";")[0].strip()
    if base_content_type and base_content_type not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported audio format: {audio.content_type}. Accepted: webm, wav, ogg, mp3, mp4."},
        )

    MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await audio.read()
        if len(content) > MAX_AUDIO_SIZE:
            return JSONResponse(
                status_code=413,
                content={"error": f"Audio file too large (max {MAX_AUDIO_SIZE // 1024 // 1024} MB)."},
            )
        tmp.write(content)
        tmp_path = tmp.name

    try:
        wav_path = tmp_path + ".wav"
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-i", tmp_path,
            "-ar", "16000", "-ac", "1", "-f", "wav", wav_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()

        if proc.returncode != 0:
            return JSONResponse(
                status_code=400,
                content={"error": "Failed to process audio file"},
            )

        loop = asyncio.get_event_loop()

        def run_transcribe():
            segments, info = model.transcribe(
                wav_path,
                language=settings.WHISPER_LANGUAGE,
                beam_size=3,
                vad_filter=False,
            )
            parts = []
            for seg in segments:
                seg_text = seg.text if isinstance(seg.text, str) else " ".join(seg.text)
                parts.append(seg_text)
            return " ".join(parts).strip()

        text = await loop.run_in_executor(None, run_transcribe)

        logger.info("Browser voice transcription: '%s'", text[:100] if text else "(empty)")
        return {"text": text, "language": settings.WHISPER_LANGUAGE}

    except Exception as e:
        logger.error("Transcription failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={"error": "Transcription failed. Check server logs for details."},
        )
    finally:
        import os
        for p in [tmp_path, tmp_path + ".wav"]:
            try:
                os.unlink(p)
            except OSError:
                pass


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with token streaming."""
    client_host = websocket.client.host if websocket.client else ""
    is_local = auth.is_local_request(client_host)

    if not is_local:
        ws_token = websocket.query_params.get("token", "")
        if not ws_token or not auth.validate_token(ws_token):
            await websocket.close(code=4001, reason="Authentication required")
            return

    await ws_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if "client_register" in data:
                ws_manager.register_client(websocket, data["client_register"])
                await websocket.send_json({
                    "client_registered": True,
                    "connected_devices": ws_manager.get_connected_devices(),
                })
                continue

            if "audio_preference" in data:
                pref = data["audio_preference"]
                client_info = ws_manager.get_client_info(websocket)
                if client_info:
                    client_info.wants_audio = bool(pref.get("wants_audio", True))
                    logger.info(
                        "Client audio preference updated: wants_audio=%s",
                        client_info.wants_audio,
                    )
                await websocket.send_json({
                    "audio_preference_updated": True,
                    "wants_audio": client_info.wants_audio if client_info else True,
                })
                continue

            if data.get("stop_audio"):
                logger.info("Audio stop requested by client")
                if _speaker:
                    _speaker.stop_speaking()
                await ws_manager.broadcast_json({"voice_stop": True})
                await broadcast_voice_state(False)
                if _listener and _listener._is_speaking:
                    _listener.set_speaking(False, open_followup=False)
                continue

            if "browser_mic" in data:
                if _listener:
                    recording = data["browser_mic"]
                    _listener.set_speaking(recording, open_followup=False)
                    logger.info("Browser mic %s, terminal listener %s",
                                "started" if recording else "stopped",
                                "paused" if recording else "resumed")
                continue

            ws_manager.touch(websocket)

            message = data.get("message", "")

            if not message:
                await websocket.send_json({"error": "Empty message"})
                continue

            if len(message) > 50000:
                await websocket.send_json({"error": "Message too long (max 50,000 characters)"})
                continue

            if _listener:
                _listener.set_speaking(True)

            full_response = []
            async for token in brain.process_stream(message):
                full_response.append(token)
                await websocket.send_json({
                    "token": token,
                    "done": False,
                })

            complete = "".join(full_response)
            await websocket.send_json({
                "token": "",
                "done": True,
                "full_response": complete,
                "backend": brain.llm.active_backend,
                "session_cost": brain.llm.get_cost_summary(),
            })

            if _speaker and complete.strip():
                try:
                    requesting_ws = websocket

                    async def on_audio_ready(envelope, duration, audio_b64=None):
                        await broadcast_voice_state(
                            True,
                            amplitude_envelope=envelope,
                            audio_duration=duration,
                            audio_base64=audio_b64,
                            target_ws=requesting_ws,
                        )

                    async def on_audio_chunk(chunk_b64, idx, is_last, env, dur):
                        await broadcast_voice_chunk(
                            chunk_b64, idx, is_last, env, dur,
                            target_ws=requesting_ws,
                        )

                    await _speaker.speak(
                        complete,
                        on_audio_ready=on_audio_ready,
                        on_audio_chunk=on_audio_chunk,
                        skip_local_playback=True,
                    )
                    await broadcast_voice_state(False)
                except Exception as e:
                    logger.error("TTS failed for browser message: %s", e)
                    await broadcast_voice_state(False)

            if _listener:
                _listener.set_speaking(False, open_followup=False)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        ws_manager.disconnect(websocket)


@app.websocket("/ws/extension")
async def websocket_extension(websocket: WebSocket):
    """WebSocket endpoint for Tobi Chrome Extension browser automation."""
    client_host = websocket.client.host if websocket.client else ""
    is_local = auth.is_local_request(client_host)

    if not is_local:
        ws_token = websocket.query_params.get("token", "")
        if not ws_token or not auth.validate_token(ws_token):
            await websocket.close(code=4001, reason="Authentication required")
            return

    await websocket.accept()
    logger.info("Chrome extension connected from %s", client_host)

    chrome_extension.set_extension_ws(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await chrome_extension.handle_extension_message(data)

    except WebSocketDisconnect:
        logger.info("Chrome extension disconnected.")
    except Exception as e:
        logger.error("Chrome extension WebSocket error: %s", e)
    finally:
        chrome_extension.clear_extension_ws()

from Tobi.tools.vscode_bridge import vscode_bridge

@app.websocket("/ws/vscode")
async def websocket_vscode(websocket: WebSocket):
    """WebSocket endpoint for Tobi VS Code Extension."""
    client_host = websocket.client.host if websocket.client else ""
    if not auth.is_local_request(client_host):
        await websocket.close(code=4003, reason="VS Code extension only available locally")
        return

    await websocket.accept()
    logger.info("VS Code extension connected.")
    vscode_bridge.set_ws(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await vscode_bridge.handle_message(data)
    except WebSocketDisconnect:
        logger.info("VS Code extension disconnected.")
    except Exception as e:
        logger.error("VS Code extension WebSocket error: %s", e)
    finally:
        vscode_bridge.clear_ws()


@app.websocket("/ws/overlay")
async def websocket_overlay(websocket: WebSocket):
    """Lightweight WebSocket for desktop overlay state (localhost only, no auth).

    Sends JSON messages: {"state": "idle"|"listening"|"thinking"|"speaking"}
    The overlay uses these to animate the particle orb.
    """
    client_host = websocket.client.host if websocket.client else ""
    if not auth.is_local_request(client_host):
        await websocket.close(code=4003, reason="Overlay only available locally")
        return

    await websocket.accept()
    _overlay_clients.append(websocket)
    logger.info("Desktop overlay connected. Sending current state: %s", _overlay_state)

    # Send current state immediately on connect
    try:
        await websocket.send_json({
            "state": _overlay_state,
            "text": _overlay_text,
            "userText": _overlay_user_text,
        })
    except Exception:
        pass

    try:
        while True:
            # Keep connection alive; overlay is read-only but we need to consume pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Desktop overlay disconnected.")
    except Exception:
        pass
    finally:
        if websocket in _overlay_clients:
            _overlay_clients.remove(websocket)


# ============================================================
# Reminders API  (Phase 0)
# ============================================================
from Tobi.memory.reminders_store import (
    create_reminder as _create_reminder_db,
    get_reminder,
    get_all_reminders,
    get_upcoming_reminders as _get_upcoming_reminders_db,
    update_reminder_status,
    update_reminder_audio as _update_reminder_audio_db,
    delete_reminder as _delete_reminder_db,
    ReminderStatus,
    PlaybackMode,
    Recurrence,
    AUDIO_DIR,
)
import uuid as _uuid


class ReminderCreateRequest(BaseModel):
    content: str
    due_at_iso: str           # ISO-8601 datetime string
    is_alarm: bool = False
    recurrence: str = "none"
    playback_mode: str = "tobi_voice"


class ReminderUpdateRequest(BaseModel):
    content: str | None = None
    due_at_iso: str | None = None
    is_alarm: bool | None = None
    recurrence: str | None = None
    playback_mode: str | None = None


@app.get("/reminders", dependencies=[Depends(require_auth)])
async def list_reminders_endpoint(upcoming: bool = True, hours: int = 48):
    """List reminders. upcoming=true (default) → next N hours only."""
    if upcoming:
        reminders = _get_upcoming_reminders_db(hours=hours)
    else:
        reminders = get_all_reminders(include_deleted=False)
    return {"reminders": [r.to_dict() for r in reminders], "count": len(reminders)}


@app.post("/reminders", dependencies=[Depends(require_auth)])
async def create_reminder_endpoint(body: ReminderCreateRequest):
    """Create a new reminder."""
    from datetime import datetime
    try:
        due_ts = datetime.fromisoformat(body.due_at_iso).timestamp()
    except (ValueError, TypeError):
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid due_at_iso: '{body.due_at_iso}'. Use ISO-8601."},
        )
    try:
        rec = Recurrence(body.recurrence)
    except ValueError:
        rec = Recurrence.NONE
    try:
        pm = PlaybackMode(body.playback_mode)
    except ValueError:
        pm = PlaybackMode.TOBI_VOICE

    reminder = _create_reminder_db(
        content=body.content,
        due_at=due_ts,
        playback_mode=pm,
        is_alarm=body.is_alarm,
        recurrence=rec,
    )
    return reminder.to_dict()


@app.get("/reminders/{reminder_id}", dependencies=[Depends(require_auth)])
async def get_reminder_endpoint(reminder_id: int):
    """Get a single reminder by ID."""
    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})
    return reminder.to_dict()


@app.patch("/reminders/{reminder_id}", dependencies=[Depends(require_auth)])
async def update_reminder_endpoint(reminder_id: int, body: ReminderUpdateRequest):
    """Update content, time, recurrence, alarm mode, or playback mode."""
    import sqlite3
    from datetime import datetime
    from Tobi.memory.reminders_store import DB_PATH

    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})

    fields: list[str] = []
    values: list = []

    if body.content is not None:
        fields.append("content = ?")
        values.append(body.content)

    if body.due_at_iso is not None:
        try:
            due_ts = datetime.fromisoformat(body.due_at_iso).timestamp()
            fields.append("due_at = ?")
            values.append(due_ts)
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content={"error": f"Invalid due_at_iso: '{body.due_at_iso}'"})

    if body.recurrence is not None:
        try:
            rec_val = Recurrence(body.recurrence).value
        except ValueError:
            rec_val = Recurrence.NONE.value
        fields.append("recurrence = ?")
        values.append(rec_val)

    if body.is_alarm is not None:
        fields.append("is_alarm = ?")
        values.append(int(body.is_alarm))

    if body.playback_mode is not None:
        try:
            pm_val = PlaybackMode(body.playback_mode).value
        except ValueError:
            pm_val = PlaybackMode.TOBI_VOICE.value
        fields.append("playback_mode = ?")
        values.append(pm_val)

    if not fields:
        return JSONResponse(status_code=400, content={"error": "No fields to update."})

    values.append(reminder_id)
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(f"UPDATE reminders SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    return get_reminder(reminder_id).to_dict()


@app.delete("/reminders/{reminder_id}", dependencies=[Depends(require_auth)])
async def delete_reminder_endpoint(reminder_id: int):
    """Soft-delete a reminder."""
    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})
    _delete_reminder_db(reminder_id)
    return {"status": "deleted", "id": reminder_id}


@app.post("/reminders/{reminder_id}/dismiss", dependencies=[Depends(require_auth)])
async def dismiss_reminder_endpoint(reminder_id: int):
    """Dismiss a fired reminder (or advance a recurring one)."""
    from Tobi.memory.reminders_store import advance_recurring_reminder
    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})

    if reminder.recurrence != Recurrence.NONE:
        updated = advance_recurring_reminder(reminder)
        if updated:
            return {"status": "advanced", "next": updated.to_dict()}

    update_reminder_status(reminder_id, ReminderStatus.DISMISSED)
    return {"status": "dismissed", "id": reminder_id}


class SnoozeRequest(BaseModel):
    minutes: int = 10


@app.post("/reminders/{reminder_id}/snooze", dependencies=[Depends(require_auth)])
async def snooze_reminder_endpoint(reminder_id: int, body: SnoozeRequest):
    """Snooze a reminder for N minutes."""
    import time
    from datetime import datetime

    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})

    if reminder.status not in (ReminderStatus.PENDING, ReminderStatus.FIRED, ReminderStatus.SNOOZED):
        return JSONResponse(
            status_code=400,
            content={"error": f"Reminder {reminder_id} is {reminder.status.value} and cannot be snoozed."},
        )

    snooze_until = time.time() + body.minutes * 60
    update_reminder_status(reminder_id, ReminderStatus.SNOOZED, snooze_until=snooze_until)
    wake_fmt = datetime.fromtimestamp(snooze_until).strftime("%I:%M %p")
    return {"status": "snoozed", "id": reminder_id, "wake_at": wake_fmt, "snooze_until": snooze_until}


@app.post("/reminders/{reminder_id}/audio", dependencies=[Depends(require_auth)])
async def upload_reminder_audio(reminder_id: int, audio: UploadFile = File(...)):
    """
    Upload a voice recording to attach to a reminder.

    When playback_mode is 'own_voice', this audio clip is played back
    verbatim when the reminder fires instead of generating TTS.

    Accepts WebM/WAV/OGG. Max 10 MB.
    """
    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": f"Reminder {reminder_id} not found."})

    MAX_AUDIO = 10 * 1024 * 1024  # 10 MB
    allowed_types = {"audio/webm", "audio/wav", "audio/ogg", "audio/mpeg", "audio/mp4"}
    base_ct = (audio.content_type or "").split(";")[0].strip()
    if base_ct and base_ct not in allowed_types:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported audio type: {audio.content_type}"},
        )

    content = await audio.read()
    if len(content) > MAX_AUDIO:
        return JSONResponse(
            status_code=413,
            content={"error": f"Audio too large (max {MAX_AUDIO // 1024 // 1024} MB)."},
        )

    ext = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    filename = f"reminder_{reminder_id}_{_uuid.uuid4().hex[:8]}{ext}"
    audio_path = AUDIO_DIR / filename
    audio_path.write_bytes(content)

    _update_reminder_audio_db(reminder_id, filename, PlaybackMode.OWN_VOICE)
    return {
        "status": "uploaded",
        "reminder_id": reminder_id,
        "audio_url": filename,
        "playback_mode": "own_voice",
    }


@app.get("/reminders/{reminder_id}/audio", dependencies=[Depends(require_auth)])
async def serve_reminder_audio(reminder_id: int):
    """Stream a reminder's voice recording back to the client."""
    from fastapi.responses import FileResponse
    reminder = get_reminder(reminder_id)
    if reminder is None:
        return JSONResponse(status_code=404, content={"error": "Reminder not found."})
    if not reminder.audio_url:
        return JSONResponse(status_code=404, content={"error": "No audio attached to this reminder."})

    audio_path = AUDIO_DIR / reminder.audio_url
    if not audio_path.exists():
        return JSONResponse(status_code=404, content={"error": "Audio file not found on disk."})

    media_type = "audio/webm" if reminder.audio_url.endswith(".webm") else "audio/wav"
    return FileResponse(str(audio_path), media_type=media_type)


# ── Digest endpoint ───────────────────────────────────────────────────────────

@app.get("/digest", dependencies=[Depends(require_auth)])
async def get_daily_digest():
    """Generate and return today's morning digest (facts + reminders + nudges)."""
    from Tobi.core.digest import build_digest
    digest = await build_digest(brain)
    return digest


@app.get("/digest/wake-briefing", dependencies=[Depends(require_auth)])
async def get_wake_briefing():
    """
    Short spoken wake briefing: today's date, top 3 priorities, reminders before noon.
    Called by the alarm dismiss handler on mobile to play the morning TTS brief.
    """
    from Tobi.core.digest import build_wake_briefing
    briefing = await build_wake_briefing(brain)
    return briefing


# ============================================================
# Multi-Provider LLM
# ============================================================

@app.get("/providers", dependencies=[Depends(require_auth)])
async def get_providers():
    """Get available AI providers and their status."""
    from Tobi.core.multi_llm import multi_llm
    return {"providers": multi_llm.get_available_providers()}


@app.post("/providers/chat", dependencies=[Depends(require_auth)])
async def provider_chat(request: ChatRequest, provider: str = "", tier: str = "brain"):
    """Chat with a specific provider or auto-select."""
    from Tobi.core.multi_llm import multi_llm
    system_prompt = settings.get_system_prompt()
    response = await multi_llm.chat(
        message=request.message,
        provider=provider,
        tier=tier,
        system_prompt=system_prompt,
    )
    if response is None:
        # Fall back to main brain
        response = await brain.process(request.message)
    return {"response": response, "provider": provider or "auto"}


# ============================================================
# GitHub Integration
# ============================================================

@app.get("/github/repos", dependencies=[Depends(require_auth)])
async def github_repos():
    """Get the user's GitHub repositories."""
    from Tobi.tools.github_tools import get_my_repos
    return {"repos": await get_my_repos()}


@app.get("/github/prs", dependencies=[Depends(require_auth)])
async def github_prs(repo: str = ""):
    """Get open pull requests."""
    from Tobi.tools.github_tools import get_open_prs
    return {"prs": await get_open_prs(repo)}


@app.get("/github/issues", dependencies=[Depends(require_auth)])
async def github_issues(repo: str = ""):
    """Get open issues."""
    from Tobi.tools.github_tools import get_open_issues
    return {"issues": await get_open_issues(repo)}


@app.get("/github/summary", dependencies=[Depends(require_auth)])
async def github_summary():
    """Get a full GitHub summary for the daily brief."""
    from Tobi.tools.github_tools import get_github_summary
    return {"summary": await get_github_summary()}


# ============================================================
# Job Search
# ============================================================

@app.get("/jobs/search", dependencies=[Depends(require_auth)])
async def job_search(query: str = "web development", limit: int = 15):
    """Search for jobs across multiple boards."""
    from Tobi.tools.job_search import search_jobs
    return {"results": await search_jobs(query, limit)}


@app.get("/jobs/daily", dependencies=[Depends(require_auth)])
async def daily_jobs():
    """Get daily job brief."""
    from Tobi.tools.job_search import get_daily_job_brief
    return {"brief": await get_daily_job_brief()}


# ============================================================
# Market Intelligence
# ============================================================

@app.get("/market/crypto", dependencies=[Depends(require_auth)])
async def market_crypto():
    """Get crypto prices."""
    from Tobi.tools.market_intel import get_crypto_prices
    return {"prices": await get_crypto_prices()}


@app.get("/market/forex", dependencies=[Depends(require_auth)])
async def market_forex():
    """Get forex rates."""
    from Tobi.tools.market_intel import get_forex_rates
    return {"rates": await get_forex_rates()}


@app.get("/market/news", dependencies=[Depends(require_auth)])
async def market_news():
    """Get AI/tech news."""
    from Tobi.tools.market_intel import get_ai_tech_news
    return {"news": await get_ai_tech_news()}


@app.get("/market/brief", dependencies=[Depends(require_auth)])
async def market_brief():
    """Get combined market brief."""
    from Tobi.tools.market_intel import get_market_brief
    return {"brief": await get_market_brief()}


@app.get("/market/niche/{niche}", dependencies=[Depends(require_auth)])
async def market_niche(niche: str):
    """Get niche-specific market updates."""
    from Tobi.tools.market_intel import get_niche_update
    return {"update": await get_niche_update(niche)}


# ============================================================
# Social Media
# ============================================================

@app.get("/social/trending", dependencies=[Depends(require_auth)])
async def social_trending():
    """Get trending topics across social platforms."""
    from Tobi.tools.social_media import get_social_brief
    return {"brief": await get_social_brief()}


@app.get("/social/search", dependencies=[Depends(require_auth)])
async def social_search(query: str, platform: str = "x"):
    """Search social media."""
    from Tobi.tools.social_media import search_x
    if platform == "x":
        return {"results": await search_x(query)}
    return {"error": f"Platform '{platform}' not supported yet."}


# ============================================================
# CRM Lite
# ============================================================

@app.get("/crm/summary", dependencies=[Depends(require_auth)])
async def crm_summary():
    """Get CRM summary."""
    from Tobi.tools.crm import get_crm_brief
    return {"brief": await get_crm_brief()}


@app.get("/crm/contacts", dependencies=[Depends(require_auth)])
async def crm_contacts(query: str = ""):
    """Search or list contacts."""
    from Tobi.tools.crm import search_contacts, get_all_contacts
    if query:
        return {"contacts": [c.to_dict() for c in search_contacts(query)]}
    return {"contacts": [c.to_dict() for c in get_all_contacts()]}


@app.post("/crm/contacts", dependencies=[Depends(require_auth)])
async def crm_add_contact(request: Request):
    """Add a new contact."""
    from Tobi.tools.crm import add_contact
    data = await request.json()
    contact = add_contact(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        company=data.get("company", ""),
        role=data.get("role", ""),
        source=data.get("source", ""),
        notes=data.get("notes", ""),
    )
    return contact.to_dict()


@app.get("/crm/deals", dependencies=[Depends(require_auth)])
async def crm_deals():
    """Get open deals."""
    from Tobi.tools.crm import get_open_deals
    return {"deals": [d.to_dict() for d in get_open_deals()]}


@app.get("/crm/stale", dependencies=[Depends(require_auth)])
async def crm_stale(days: int = 14):
    """Get stale contacts not contacted in N days."""
    from Tobi.tools.crm import get_stale_contacts
    return {"contacts": [c.to_dict() for c in get_stale_contacts(days)]}


# ============================================================
# Content Pipeline
# ============================================================

@app.get("/content/summary", dependencies=[Depends(require_auth)])
async def content_summary():
    """Get content pipeline summary."""
    from Tobi.tools.content_pipeline import get_content_brief
    return {"brief": await get_content_brief()}


@app.get("/content/{venture}", dependencies=[Depends(require_auth)])
async def content_by_venture(venture: str):
    """Get content items by venture."""
    from Tobi.tools.content_pipeline import get_content_by_venture
    return {"items": [c.to_dict() for c in get_content_by_venture(venture)]}


@app.post("/content", dependencies=[Depends(require_auth)])
async def content_add(request: Request):
    """Add a content item."""
    from Tobi.tools.content_pipeline import add_content
    data = await request.json()
    item = add_content(
        venture=data.get("venture", ""),
        title=data.get("title", ""),
        content_type=data.get("content_type", "product"),
        status=data.get("status", "idea"),
        platform=data.get("platform", ""),
        price=data.get("price", 0),
        cost=data.get("cost", 0),
        notes=data.get("notes", ""),
    )
    return item.to_dict()


# ============================================================
# Coursework Tracker
# ============================================================

@app.get("/academic/brief", dependencies=[Depends(require_auth)])
async def academic_brief():
    """Get academic brief."""
    from Tobi.tools.coursework import get_academic_brief
    return {"brief": await get_academic_brief()}


@app.get("/academic/upcoming", dependencies=[Depends(require_auth)])
async def academic_upcoming(days: int = 14):
    """Get upcoming assignments."""
    from Tobi.tools.coursework import get_upcoming_assignments
    return {"assignments": [a.to_dict() for a in get_upcoming_assignments(days)]}


@app.get("/academic/overdue", dependencies=[Depends(require_auth)])
async def academic_overdue():
    """Get overdue assignments."""
    from Tobi.tools.coursework import get_overdue_assignments
    return {"assignments": [a.to_dict() for a in get_overdue_assignments()]}


@app.post("/academic/courses", dependencies=[Depends(require_auth)])
async def academic_add_course(request: Request):
    """Add a course."""
    from Tobi.tools.coursework import add_course
    data = await request.json()
    course = add_course(
        code=data.get("code", ""),
        name=data.get("name", ""),
        lecturer=data.get("lecturer", ""),
        semester=data.get("semester", ""),
        credits=data.get("credits", 3),
    )
    return course.to_dict()


@app.post("/academic/assignments", dependencies=[Depends(require_auth)])
async def academic_add_assignment(request: Request):
    """Add an assignment."""
    from Tobi.tools.coursework import add_assignment
    data = await request.json()
    assignment = add_assignment(
        course_id=data.get("course_id", 0),
        title=data.get("title", ""),
        due_date=data.get("due_date", ""),
        description=data.get("description", ""),
        priority=data.get("priority", 3),
        notes=data.get("notes", ""),
    )
    return assignment.to_dict()


# ============================================================
# Earnings Projection
# ============================================================

@app.get("/earnings/brief", dependencies=[Depends(require_auth)])
async def earnings_brief():
    """Get earnings projection brief."""
    from Tobi.tools.earnings import get_earnings_brief
    return {"brief": await get_earnings_brief()}


# ============================================================
# API Key Vault
# ============================================================

@app.get("/vault/status", dependencies=[Depends(require_auth)])
async def vault_status():
    """Get vault status."""
    from Tobi.core.api_key_vault import get_vault_status
    return get_vault_status()


@app.get("/vault/keys", dependencies=[Depends(require_auth)])
async def vault_keys():
    """List all tracked keys (redacted values)."""
    from Tobi.core.api_key_vault import list_keys
    return {"keys": list_keys()}


@app.post("/vault/keys", dependencies=[Depends(require_auth)])
async def vault_store_key(request: Request):
    """Store an API key."""
    from Tobi.core.api_key_vault import store_key
    data = await request.json()
    store_key(data.get("name", ""), data.get("value", ""))
    return {"status": "stored", "name": data.get("name")}


@app.delete("/vault/keys/{key_name}", dependencies=[Depends(require_auth)])
async def vault_remove_key(key_name: str):
    """Remove an API key."""
    from Tobi.core.api_key_vault import remove_key
    removed = remove_key(key_name)
    return {"status": "removed" if removed else "not_found", "name": key_name}


# ============================================================
# Focus Mode
# ============================================================

@app.get("/focus/status", dependencies=[Depends(require_auth)])
async def focus_status():
    """Get focus mode status."""
    from Tobi.core.focus_mode import get_focus_status
    return get_focus_status()


@app.post("/focus/start", dependencies=[Depends(require_auth)])
async def focus_start(request: Request):
    """Start focus mode."""
    from Tobi.core.focus_mode import start_focus
    data = await request.json()
    return start_focus(data.get("minutes", 25))


@app.post("/focus/stop", dependencies=[Depends(require_auth)])
async def focus_stop():
    """Stop focus mode."""
    from Tobi.core.focus_mode import stop_focus
    return stop_focus()


# ============================================================
# Weekly Retro
# ============================================================

@app.get("/retro/weekly", dependencies=[Depends(require_auth)])
async def weekly_retro():
    """Get weekly retrospective."""
    from Tobi.core.weekly_retro import build_weekly_retro
    return await build_weekly_retro(brain)


# ============================================================
# Intel Engine (always-on background jobs)
# ============================================================

@app.get("/intel/status", dependencies=[Depends(require_auth)])
async def intel_status():
    """Get intel engine status."""
    from Tobi.core.intel_engine import intel_engine, get_all_latest
    return {
        "engine": intel_engine.get_status(),
        "latest": get_all_latest(),
    }


@app.get("/intel/latest/{category}", dependencies=[Depends(require_auth)])
async def intel_latest(category: str):
    """Get latest intel for a category."""
    from Tobi.core.intel_engine import get_latest
    if category not in ("crypto", "forex", "news", "trending", "jobs"):
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown category: {category}. Valid: crypto, forex, news, trending, jobs"},
        )
    return get_latest(category)


@app.post("/intel/refresh/{category}", dependencies=[Depends(require_auth)])
async def intel_refresh(category: str):
    """Force refresh intel for a category."""
    from Tobi.core import intel_engine as ie
    if category not in ie.DEFAULT_INTERVALS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unknown category: {category}"},
        )
    data = await ie._collect(category)
    if data:
        ie._results[category] = {"data": data, "collected_at": __import__("time").time()}
        ie._save_state()
        return {"status": "refreshed", "category": category, "data": data}
    return JSONResponse(status_code=500, content={"error": f"Collection failed for {category}"})


@app.post("/intel/intervals", dependencies=[Depends(require_auth)])
async def intel_set_interval(request: Request):
    """Change collection interval for a category."""
    from Tobi.core.intel_engine import intel_engine
    data = await request.json()
    category = data.get("category", "")
    seconds = data.get("seconds", 0)
    if category not in intel_engine._intervals or seconds < 300:
        return JSONResponse(status_code=400, content={"error": "Invalid category or interval (min 300s)."})
    intel_engine.set_interval(category, seconds)
    return intel_engine.get_status()


# ============================================================
# Combined Daily Brief (everything in one message)
# ============================================================

@app.get("/daily/brief", dependencies=[Depends(require_auth)])
async def daily_brief(sections: str = "all"):
    """Build a combined daily brief across all modules.

    sections: comma-separated list or 'all'. Valid: digest, github, market,
    social, crm, content, academic, jobs, earnings, intel.
    """
    allowed = {"digest", "github", "market", "social", "crm", "content", "academic", "jobs", "earnings", "intel"}
    if sections == "all":
        requested = set(allowed)
    else:
        requested = set(s.strip() for s in sections.split(",") if s.strip())
        requested = requested.intersection(allowed)

    brief: dict[str, str] = {}

    if "digest" in requested:
        from Tobi.core.digest import build_digest
        digest = await build_digest(brain)
        brief["digest"] = digest

    if "github" in requested:
        from Tobi.tools.github_tools import get_github_summary
        brief["github"] = await get_github_summary()

    if "market" in requested:
        from Tobi.tools.market_intel import get_market_brief
        brief["market"] = await get_market_brief()

    if "social" in requested:
        from Tobi.tools.social_media import get_social_brief
        brief["social"] = await get_social_brief()

    if "crm" in requested:
        from Tobi.tools.crm import get_crm_brief
        brief["crm"] = await get_crm_brief()

    if "content" in requested:
        from Tobi.tools.content_pipeline import get_content_brief
        brief["content"] = await get_content_brief()

    if "academic" in requested:
        from Tobi.tools.coursework import get_academic_brief
        brief["academic"] = await get_academic_brief()

    if "jobs" in requested:
        from Tobi.tools.job_search import get_daily_job_brief
        brief["jobs"] = await get_daily_job_brief()

    if "earnings" in requested:
        from Tobi.tools.earnings import get_earnings_brief
        brief["earnings"] = await get_earnings_brief()

    if "intel" in requested:
        from Tobi.core.intel_engine import get_all_latest
        intel = get_all_latest()
        brief["intel"] = {
            cat: entry.get("data", "No data collected yet.") if entry else "No data yet."
            for cat, entry in intel.items()
        }

    return {"brief": brief, "sections": sorted(requested), "generated_at": time.time()}
