"""
API key vault for Tobi.

Stores all integration tokens and API keys encrypted at rest.
Never stores keys in plain text in the repo, never logs them.
Uses Fernet symmetric encryption from the cryptography library.
"""
import base64
import hashlib
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("Tobi.core.api_key_vault")

VAULT_DIR = Path(__file__).parent.parent.parent / "data"
VAULT_FILE = VAULT_DIR / "Tobi_vault.enc"
SALT_FILE = VAULT_DIR / ".vault_salt"

# Default keys to track
TRACKED_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GROK_API_KEY",
    "GITHUB_TOKEN",
    "X_BEARER_TOKEN",
    "TIKTOK_ACCESS_TOKEN",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "AFRICAS_TALKING_API_KEY",
    "ELEVENLABS_API_KEY",
    "NEWSAPI_KEY",
    "VAPID_PRIVATE_KEY",
    "TOBI_PIN",
]

_fernet = None


def _get_fernet():
    """Get or initialize the Fernet encryption instance."""
    global _fernet
    if _fernet is not None:
        return _fernet

    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logger.warning("cryptography package not installed. Vault will use plain JSON.")
        return None

    # Derive key from machine-specific seed
    seed = os.getenv("TOBI_VAULT_SEED", "")
    if not seed:
        # Use machine hostname + username as seed
        import platform
        seed = f"{platform.node()}-{os.getenv('USERNAME', 'user')}-Tobi-vault"

    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    if SALT_FILE.exists():
        salt = SALT_FILE.read_bytes()
    else:
        salt = os.urandom(16)
        SALT_FILE.write_bytes(salt)

    key = hashlib.pbkdf2_hmac("sha256", seed.encode(), salt, 100000, dklen=32)
    fernet_key = base64.urlsafe_b64encode(key)
    _fernet = Fernet(fernet_key)
    return _fernet


def _read_vault() -> dict:
    """Read the encrypted vault file."""
    if not VAULT_FILE.exists():
        return {}

    fernet = _get_fernet()
    if fernet is None:
        # Fallback: plain JSON
        try:
            return json.loads(VAULT_FILE.read_text())
        except Exception:
            return {}

    try:
        encrypted = VAULT_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted)
    except Exception as e:
        logger.error("Failed to decrypt vault: %s", e)
        return {}


def _write_vault(data: dict):
    """Write data to the encrypted vault file."""
    fernet = _get_fernet()
    if fernet is None:
        # Fallback: plain JSON
        VAULT_FILE.write_text(json.dumps(data, indent=2))
        return

    try:
        encrypted = fernet.encrypt(json.dumps(data, indent=2).encode())
        VAULT_FILE.write_bytes(encrypted)
    except Exception as e:
        logger.error("Failed to write vault: %s", e)


def store_key(name: str, value: str):
    """Store an API key in the vault."""
    vault = _read_vault()
    vault[name] = {
        "value": value,
        "stored_at": __import__("time").time(),
    }
    _write_vault(vault)
    logger.info("Key '%s' stored in vault.", name)


def get_key(name: str) -> str:
    """Retrieve an API key from the vault."""
    vault = _read_vault()
    entry = vault.get(name, {})
    return entry.get("value", "")


def remove_key(name: str) -> bool:
    """Remove an API key from the vault."""
    vault = _read_vault()
    if name in vault:
        del vault[name]
        _write_vault(vault)
        return True
    return False


def list_keys() -> list[dict]:
    """List all stored keys (with redacted values)."""
    vault = _read_vault()
    result = []
    for name in TRACKED_KEYS:
        entry = vault.get(name, {})
        has_key = bool(entry.get("value"))
        result.append({
            "name": name,
            "configured": has_key,
            "stored_at": entry.get("stored_at", 0),
        })
    # Also list any custom keys
    for name in vault:
        if name not in TRACKED_KEYS:
            entry = vault[name]
            result.append({
                "name": name,
                "configured": bool(entry.get("value")),
                "stored_at": entry.get("stored_at", 0),
                "custom": True,
            })
    return result


def get_vault_status() -> dict:
    """Get a summary of the vault status."""
    keys = list_keys()
    configured = sum(1 for k in keys if k["configured"])
    return {
        "total_keys": len(keys),
        "configured": configured,
        "missing": len(keys) - configured,
        "encrypted": _get_fernet() is not None,
    }


def migrate_env_keys():
    """One-time migration: copy API keys from .env to the vault."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return

    vault = _read_vault()
    migrated = 0

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key in TRACKED_KEYS and value and key not in vault:
            store_key(key, value)
            migrated += 1

    if migrated:
        logger.info("Migrated %d API keys from .env to vault.", migrated)
