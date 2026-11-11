"""Cross-platform read access to Gmail and Google Calendar."""
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from Tobi.config import settings
from Tobi.core import api_key_vault

logger = logging.getLogger("Tobi.tools.google_workspace")

TOKEN_KEY = "GOOGLE_WORKSPACE_TOKEN"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GoogleWorkspaceNotConfiguredError(RuntimeError):
    """Raised when Google OAuth has not been configured or connected."""


def _persist_credentials(credentials: Any) -> None:
    if not api_key_vault.get_vault_status()["encrypted"]:
        raise RuntimeError("Google OAuth tokens cannot be stored because encrypted storage is unavailable.")
    api_key_vault.store_key(TOKEN_KEY, credentials.to_json())


def _credentials() -> Any:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

    token_data = api_key_vault.get_key(TOKEN_KEY)
    if token_data:
        credentials = Credentials.from_authorized_user_info(json.loads(token_data), SCOPES)
        if credentials.valid:
            return credentials
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            _persist_credentials(credentials)
            return credentials

    client_secrets = Path(os.path.expandvars(settings.GOOGLE_OAUTH_CLIENT_SECRETS)).expanduser()
    if not settings.GOOGLE_OAUTH_CLIENT_SECRETS or not client_secrets.is_file():
        raise GoogleWorkspaceNotConfiguredError(
            "Google Workspace is not connected. Set GOOGLE_OAUTH_CLIENT_SECRETS to your "
            "OAuth installed-app client JSON file, then connect Google Workspace."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
    credentials = flow.run_local_server(port=0, open_browser=True, access_type="offline", prompt="consent")
    _persist_credentials(credentials)
    logger.info("Google Workspace OAuth connection completed.")
    return credentials


def _service(api_name: str, version: str) -> Any:
    from googleapiclient.discovery import build  # type: ignore[import-untyped]

    return build(api_name, version, credentials=_credentials(), cache_discovery=False)


def _format_calendar_event(event: dict[str, Any]) -> str:
    start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "time unknown"))
    end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))
    details = [event.get("summary", "(untitled event)"), f"{start} - {end}".rstrip(" -")]
    if event.get("location"):
        details.append(f"Location: {event['location']}")
    return " | ".join(details)


def _format_gmail_message(message: dict[str, Any]) -> str:
    headers = {
        item.get("name", "").lower(): item.get("value", "")
        for item in message.get("payload", {}).get("headers", [])
    }
    return (
        f"From: {headers.get('from', 'unknown')} | "
        f"Subject: {headers.get('subject', '(no subject)')} | "
        f"Date: {headers.get('date', 'unknown')} | "
        f"{message.get('snippet', '')}"
    )


def _search_gmail(query: str, count: int) -> str:
    service = _service("gmail", "v1")
    response = service.users().messages().list(userId="me", q=query, maxResults=count).execute()
    messages = response.get("messages", [])
    if not messages:
        return "No Gmail messages matched that search."

    lines = []
    for item in messages:
        message = service.users().messages().get(
            userId="me", id=item["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        lines.append(_format_gmail_message(message))
    return "\n".join(lines)


async def gmail_search_messages(query: str, count: int = 10) -> str:
    """Search Gmail using Gmail query syntax and return message headers/snippets."""
    count = max(1, min(count, 25))
    try:
        return await asyncio.to_thread(_search_gmail, query, count)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)


def _gmail_unread_count() -> str:
    service = _service("gmail", "v1")
    inbox = service.users().labels().get(userId="me", id="INBOX").execute()
    return f"Gmail inbox has {inbox.get('messagesUnread', 0)} unread message(s)."


async def gmail_unread_count() -> str:
    """Return the Gmail inbox unread count."""
    try:
        return await asyncio.to_thread(_gmail_unread_count)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)


def _calendar_events(days: int, query: str = "") -> str:
    service = _service("calendar", "v3")
    now = datetime.now(timezone.utc)  # noqa: UP017
    response = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=(now + timedelta(days=days)).isoformat(),
        q=query or None,
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()
    events = response.get("items", [])
    if not events:
        return "No upcoming Google Calendar events found."
    return "\n".join(_format_calendar_event(event) for event in events)


async def google_calendar_upcoming_events(days: int = 1) -> str:
    """Read upcoming events from the primary Google Calendar."""
    days = max(1, min(days, 31))
    try:
        return await asyncio.to_thread(_calendar_events, days)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)


async def google_calendar_search_events(query: str, days: int = 30) -> str:
    """Search upcoming Google Calendar events by text."""
    days = max(1, min(days, 90))
    try:
        return await asyncio.to_thread(_calendar_events, days, query)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)


def _calendar_list() -> str:
    service = _service("calendar", "v3")
    response = service.calendarList().list(maxResults=100).execute()
    calendars = response.get("items", [])
    if not calendars:
        return "No Google Calendars found."
    return "\n".join(
        f"{calendar.get('summary', '(untitled calendar)')} ({calendar.get('id', 'unknown id')})"
        for calendar in calendars
    )


async def google_calendar_list() -> str:
    """List calendars available to the connected Google account."""
    try:
        return await asyncio.to_thread(_calendar_list)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)


async def connect_google_workspace() -> str:
    """Start the installed-app OAuth flow and persist encrypted credentials."""
    try:
        await asyncio.to_thread(_credentials)
    except GoogleWorkspaceNotConfiguredError as exc:
        return str(exc)
    return "Google Workspace connected. Gmail and Google Calendar read access is ready."
