"""Restricted local client for cheat_engine_bridge.lua.

Only one request may be outstanding. Requests are session-bound, size-limited,
and exchanged through atomic files below LOCALAPPDATA. No sockets or code
execution are used.
"""
from __future__ import annotations
import json, os, secrets, tempfile, time
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 256 * 1024
TIMEOUT = 2.0

@dataclass(frozen=True)
class BridgeReply:
    ok: bool
    request_id: str
    payload: dict
    error: str = ''

class BridgeClient:
    def __init__(self, root: Path | None = None):
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        self.root = root or base / 'EnshroudedTrainer' / 'bridge'
        self.root.mkdir(parents=True, exist_ok=True)
        self.session = secrets.token_hex(16)
        self.request = self.root / 'request.json'
        self.response = self.root / 'response.json'

    def _write_atomic(self, path: Path, data: dict) -> None:
        # Cheat Engine's bundled Lua decoder preserves UTF-8 bytes but does
        # not combine JSON UTF-16 surrogate-pair escapes. Send real UTF-8 so
        # descriptions such as the emoji in record 1000 round-trip exactly.
        raw = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        if len(raw) > MAX_BYTES: raise ValueError('bridge message exceeds size limit')
        fd, name = tempfile.mkstemp(prefix='.bridge-', dir=self.root)
        try:
            with os.fdopen(fd, 'wb') as f: f.write(raw); f.flush(); os.fsync(f.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name): os.unlink(name)

    def call(self, command: str, payload: dict | None = None, timeout: float = TIMEOUT) -> BridgeReply:
        request_id = secrets.token_hex(16)
        self.response.unlink(missing_ok=True)
        self._write_atomic(self.request, {'protocol': 1, 'session': self.session, 'request_id': request_id, 'command': command, 'payload': payload or {}})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.response.exists():
                try:
                    if self.response.stat().st_size > MAX_BYTES: raise ValueError('bridge response exceeds size limit')
                    data = json.loads(self.response.read_text(encoding='utf-8'))
                    if data.get('session') != self.session or data.get('request_id') != request_id:
                        self.response.unlink(missing_ok=True); time.sleep(.03); continue
                    self.response.unlink(missing_ok=True)
                    return BridgeReply(bool(data.get('ok')), request_id, data.get('payload') or {}, data.get('error',''))
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    return BridgeReply(False, request_id, {}, f'invalid bridge response: {exc}')
            time.sleep(.03)
        return BridgeReply(False, request_id, {}, 'bridge timeout; Cheat Engine bridge is unavailable')

    def close(self) -> BridgeReply:
        return self.call('shutdown')
