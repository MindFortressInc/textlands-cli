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
