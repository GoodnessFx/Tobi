import json
from datetime import datetime, timedelta, timezone

import pytest

from Tobi.core import api_key_vault
from Tobi.tools import google_workspace


def test_format_gmail_message_uses_headers_and_snippet():
    message = {
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "Project update"},
                {"name": "Date", "value": "Tue, 10 Nov 2026 10:00:00 +0000"},
            ]
        },
        "snippet": "The project is ready for review.",
    }

    formatted = google_workspace._format_gmail_message(message)

    assert "sender@example.com" in formatted
    assert "Project update" in formatted
    assert "The project is ready for review." in formatted


def test_format_calendar_event_supports_all_day_events():
    formatted = google_workspace._format_calendar_event({
        "summary": "Holiday",
        "start": {"date": "2026-12-25"},
        "end": {"date": "2026-12-26"},
    })

    assert formatted == "Holiday | 2026-12-25 - 2026-12-26"


def test_persist_credentials_refuses_unencrypted_storage(monkeypatch):
    stored = []
    monkeypatch.setattr(api_key_vault, "get_vault_status", lambda: {"encrypted": False})
    monkeypatch.setattr(api_key_vault, "store_key", lambda *args: stored.append(args))

    with pytest.raises(RuntimeError, match="encrypted storage is unavailable"):
        google_workspace._persist_credentials(object())

    assert stored == []


def test_credentials_refreshes_expired_token_and_persists_it(monkeypatch):
    from google.oauth2.credentials import Credentials

    token_data = {
        "token": "expired-token",
        "refresh_token": "refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "scopes": google_workspace.SCOPES,
        "expiry": "2000-01-01T00:00:00Z",
    }
    saved = []

    def refresh(credentials, request):
        credentials.token = "refreshed-token"
        credentials.expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # noqa: UP017

    monkeypatch.setattr(api_key_vault, "get_key", lambda key: json.dumps(token_data))
    monkeypatch.setattr(api_key_vault, "get_vault_status", lambda: {"encrypted": True})
    monkeypatch.setattr(api_key_vault, "store_key", lambda key, value: saved.append((key, value)))
    monkeypatch.setattr(Credentials, "refresh", refresh)

    credentials = google_workspace._credentials()

    assert credentials.token == "refreshed-token"
    assert len(saved) == 1
    assert saved[0][0] == google_workspace.TOKEN_KEY
    assert json.loads(saved[0][1])["token"] == "refreshed-token"


@pytest.mark.asyncio
async def test_calendar_upcoming_events_clamps_days(monkeypatch):
    captured = []
    monkeypatch.setattr(
        google_workspace,
        "_calendar_events",
        lambda days, query="": captured.append((days, query)) or "No upcoming Google Calendar events found.",
    )

    result = await google_workspace.google_calendar_upcoming_events(days=90)

    assert captured == [(31, "")]
    assert "No upcoming" in result
