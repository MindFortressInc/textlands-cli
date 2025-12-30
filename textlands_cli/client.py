"""TextLands API client."""

from typing import Optional, Any
import httpx


class TextLandsClient:
    """Client for TextLands API."""

    def __init__(
        self,
        base_url: str = "https://api.textlands.com",
        api_key: Optional[str] = None,
        guest_id: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.guest_id = guest_id
        self._client: Optional[httpx.Client] = None

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TextLands-CLI/0.1.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if self.guest_id:
            headers["Cookie"] = f"textlands_guest={self.guest_id}"
        return headers

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=60.0,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "TextLandsClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # =========== Session ===========

    def get_session(self) -> dict[str, Any]:
        """Get current session info."""
        resp = self.client.get("/session/current")
        resp.raise_for_status()
        return resp.json()

    def start_session(
        self,
        world_id: str,
        entity_id: str,
    ) -> dict[str, Any]:
        """Start a game session."""
        resp = self.client.post(
            "/session/start",
            json={"world_id": world_id, "entity_id": entity_id},
        )
        resp.raise_for_status()
        return resp.json()

    # =========== Worlds ===========

    def list_worlds(
        self,
        realm: Optional[str] = None,
        include_nsfw: bool = False,
        limit: int = 10,
    ) -> dict[str, Any]:
        """List available worlds."""
        params = {"limit": limit, "include_nsfw": include_nsfw}
        if realm:
            params["realm"] = realm
        resp = self.client.get("/infinite/worlds", params=params)
        resp.raise_for_status()
        return resp.json()

    def list_worlds_grouped(self) -> list[dict[str, Any]]:
        """List realms grouped by land. Returns all lands including adults_only."""
        resp = self.client.get("/infinite/worlds/grouped")
        resp.raise_for_status()
        return resp.json()

    def get_world(self, world_id: str) -> dict[str, Any]:
        """Get world details."""
        resp = self.client.get(f"/infinite/worlds/{world_id}")
        resp.raise_for_status()
        return resp.json()

    def get_campfire(
        self,
        world_id: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Get campfire scene with character options."""
        resp = self.client.get(
            f"/infinite/worlds/{world_id}/campfire",
            params={"limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    # =========== Actions ===========

    def do_action(self, action: str) -> dict[str, Any]:
        """Perform a game action."""
        resp = self.client.post(
            "/actions/do",
            json={"action": action},
        )
        resp.raise_for_status()
        return resp.json()

    def look(self) -> dict[str, Any]:
        """Look around current location."""
        resp = self.client.post("/actions/look")
        resp.raise_for_status()
        return resp.json()

    def move(self, destination: str) -> dict[str, Any]:
        """Move to a destination."""
        resp = self.client.post(
            "/actions/move",
            json={"destination": destination},
        )
        resp.raise_for_status()
        return resp.json()

    def talk(
        self,
        target: str,
        message: Optional[str] = None,
    ) -> dict[str, Any]:
        """Talk to someone."""
        payload = {"target": target}
        if message:
            payload["message"] = message
        resp = self.client.post("/actions/talk", json=payload)
        resp.raise_for_status()
        return resp.json()

    def rest(self) -> dict[str, Any]:
        """Rest and recover."""
        resp = self.client.post("/actions/rest")
        resp.raise_for_status()
        return resp.json()

    def inventory(self) -> dict[str, Any]:
        """Check inventory."""
        resp = self.client.post("/actions/inventory")
        resp.raise_for_status()
        return resp.json()

    # =========== Custom Character ===========

    def create_custom_character(
        self,
        world_id: str,
        concept: str,
    ) -> dict[str, Any]:
        """Create a custom character."""
        resp = self.client.post(
            f"/infinite/worlds/{world_id}/characters/custom",
            json={"concept": concept},
        )
        resp.raise_for_status()
        return resp.json()

    # =========== Chat ===========

    def send_dm(self, recipient: str, content: str) -> dict[str, Any]:
        """Send a direct message to another player."""
        resp = self.client.post(
            "/dm/send-by-key",
            params={"sender_key": self.guest_id or "cli_user", "recipient_key": recipient, "content": content},
        )
        return resp.json()

    def get_pending_messages(self) -> dict[str, Any]:
        """Get pending/unread messages."""
        player_key = self.guest_id or "cli_user"
        resp = self.client.get(f"/dm/pending/{player_key}")
        return resp.json()

    def get_unread_count(self) -> int:
        """Get unread message count."""
        player_key = self.guest_id or "cli_user"
        resp = self.client.get(f"/dm/unread/{player_key}")
        data = resp.json()
        return data.get("count", 0)

    def send_global_chat(self, message: str) -> dict[str, Any]:
        """Send a message to global chat."""
        player_key = self.guest_id or "cli_user"
        resp = self.client.post(
            "/chat/global/send",
            params={"player_key": player_key, "message": message},
        )
        return resp.json()

    def send_land_chat(self, message: str, land_key: str = None) -> dict[str, Any]:
        """Send a message to land chat."""
        player_key = self.guest_id or "cli_user"
        params = {"player_key": player_key, "message": message}
        if land_key:
            params["land_key"] = land_key
        resp = self.client.post("/chat/land/send", params=params)
        return resp.json()

    def get_global_chat(self, limit: int = 10) -> dict[str, Any]:
        """Get recent global chat messages."""
        resp = self.client.get("/chat/global", params={"limit": limit})
        return resp.json()

    def get_land_chat(self, land_key: str, limit: int = 10) -> dict[str, Any]:
        """Get recent land chat messages."""
        resp = self.client.get(f"/chat/land/{land_key}", params={"limit": limit})
        return resp.json()

    def subscribe_chat(self, channel: str) -> dict[str, Any]:
        """Subscribe to a chat channel."""
        player_key = self.guest_id or "cli_user"
        resp = self.client.post(
            "/chat/subscribe",
            params={"player_key": player_key, "channel": channel},
        )
        return resp.json()

    # =========== Auth ===========

    def request_cli_auth(self, email: str) -> dict[str, Any]:
        """Request CLI device authorization. Returns device_code for polling."""
        resp = self.client.post("/auth/cli/request", json={"email": email})
        resp.raise_for_status()
        return resp.json()

    def poll_cli_token(self, device_code: str) -> dict[str, Any]:
        """Poll for CLI session token. Returns status: pending/authorized/expired."""
        resp = self.client.get("/auth/cli/token", params={"device_code": device_code})
        resp.raise_for_status()
        return resp.json()

    # =========== Lands ===========

    def list_lands(self) -> list[dict[str, Any]]:
        """List available lands (genre categories) with their starting realms."""
        resp = self.client.get("/infinite/lands")
        resp.raise_for_status()
        return resp.json()
