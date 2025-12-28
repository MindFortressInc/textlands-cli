"""Configuration and credential management."""

import os
import json
from pathlib import Path
from typing import Optional

# Try to use keyring for secure storage, fall back to file
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


CONFIG_DIR = Path.home() / ".textlands"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "textlands-cli"


def ensure_config_dir() -> None:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load config from file."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict) -> None:
    """Save config to file."""
    ensure_config_dir()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_api_url() -> str:
    """Get API URL from config or environment."""
    if url := os.environ.get("TEXTLANDS_API_URL"):
        return url
    config = load_config()
    return config.get("api_url", "https://api.textlands.com")


def set_api_url(url: str) -> None:
    """Set API URL in config."""
    config = load_config()
    config["api_url"] = url
    save_config(config)


def get_api_key() -> Optional[str]:
    """Get API key from keyring or environment."""
    # Environment takes precedence
    if key := os.environ.get("TEXTLANDS_API_KEY"):
        return key
    # Try keyring
    if HAS_KEYRING:
        try:
            return keyring.get_password(KEYRING_SERVICE, "api_key")
        except Exception:
            pass
    # Fall back to config file (less secure)
    config = load_config()
    return config.get("api_key")


def set_api_key(api_key: str) -> None:
    """Store API key securely."""
    if HAS_KEYRING:
        try:
            keyring.set_password(KEYRING_SERVICE, "api_key", api_key)
            return
        except Exception:
            pass
    # Fall back to config file
    config = load_config()
    config["api_key"] = api_key
    save_config(config)


def clear_api_key() -> None:
    """Remove stored API key."""
    if HAS_KEYRING:
        try:
            keyring.delete_password(KEYRING_SERVICE, "api_key")
        except Exception:
            pass
    config = load_config()
    config.pop("api_key", None)
    save_config(config)


def get_guest_id() -> Optional[str]:
    """Get guest ID for anonymous play."""
    config = load_config()
    return config.get("guest_id")


def set_guest_id(guest_id: str) -> None:
    """Store guest ID."""
    config = load_config()
    config["guest_id"] = guest_id
    save_config(config)


def get_current_session() -> Optional[dict]:
    """Get current game session info."""
    config = load_config()
    return config.get("current_session")


def set_current_session(session: dict) -> None:
    """Store current game session."""
    config = load_config()
    config["current_session"] = session
    save_config(config)


def clear_current_session() -> None:
    """Clear current game session."""
    config = load_config()
    config.pop("current_session", None)
    save_config(config)


def is_authenticated() -> bool:
    """Check if user has stored credentials."""
    return get_api_key() is not None
