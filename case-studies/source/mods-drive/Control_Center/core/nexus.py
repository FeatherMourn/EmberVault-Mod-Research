"""Nexus Mods API boundary.

No credentials or example catalogue data are bundled. The client stays
disconnected until the user supplies a key through the OS credential store.
"""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable

import requests

class NexusError(RuntimeError): pass

class NexusClient:
    BASE_URL = "https://api.nexusmods.com/v3"
    GAME_DOMAIN = "enshrouded"
    CREDENTIAL_TARGET = "EnshroudedModHub:NexusMods"

    def __init__(self, api_key: str | None = None, session=None, app_version: str = "1.0.0"):
        self.session = session or requests.Session(); self.app_version = app_version; self._api_key = api_key

    @property
    def connected(self) -> bool: return bool(self._api_key)
    def status(self) -> str: return "Connected" if self.connected else "Disconnected — connect a Nexus Mods account to browse live data"

    def set_key(self, api_key: str, persist: bool = True) -> None:
        if not api_key.strip(): raise NexusError("An API key is required.")
        self._api_key = api_key.strip()
        if persist:
            try:
                import keyring
                keyring.set_password(self.CREDENTIAL_TARGET, "api_key", self._api_key)
            except ImportError: raise NexusError("Secure Windows credential storage is unavailable; install the keyring package before saving credentials.")

    def load_key(self) -> bool:
        try:
            import keyring
            self._api_key = keyring.get_password(self.CREDENTIAL_TARGET, "api_key")
        except (ImportError, Exception): self._api_key = None
        return self.connected

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self.connected: raise NexusError("Nexus Mods is disconnected. Connect an account first.")
        headers = {"apikey": self._api_key, "Application-Name": "Enshrouded Mod Hub", "Application-Version": self.app_version, "Accept": "application/json"}
        response = self.session.get(self.BASE_URL + path, headers=headers, params=params or {}, timeout=20)
        if response.status_code == 429: raise NexusError("Nexus Mods rate limit reached; try again later.")
        if response.status_code in (401, 403): raise NexusError("Nexus Mods rejected the credential or account entitlement.")
        if not response.ok: raise NexusError(f"Nexus Mods request failed ({response.status_code}).")
        return response.json()

    def browse(self, page: int = 1, search: str = "") -> list[dict[str, Any]]:
        # Endpoint shape follows the current v3 API. Search/filter support is
        # deliberately passed through only where the API accepts it.
        data = self._request(f"/games/{self.GAME_DOMAIN}/mods", {"page": page, **({"query": search} if search else {})})
        return data if isinstance(data, list) else data.get("results", data.get("mods", []))
    def mod_details(self, mod_id: int) -> dict[str, Any]: return self._request(f"/games/{self.GAME_DOMAIN}/mods/{int(mod_id)}")
    def updates(self, since: str | None = None) -> list[dict[str, Any]]: return self.browse(search="")

    @staticmethod
    def inspect_archive(archive: Path) -> dict[str, Any]:
        import zipfile
        if not archive.is_file(): raise NexusError("Downloaded archive does not exist.")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(archive) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
        supported = any(name.endswith("/mod.json") or name == "mod.json" for name in names)
        return {"path": str(archive), "sha256": digest, "files": names, "supported_loader_package": supported, "requires_manual_install": not supported}
