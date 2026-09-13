from __future__ import annotations
from qt_dicom_viewer.i18n import message as _msg

import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class PacsProfile:
    id: str
    name: str
    url: str
    enabled: bool = True
    auth: str = "none"
    username: str = ""
    timeout: int = 15
    # Credentials belong to this session; never serialize them or include in repr.
    secret: str = field(default="", repr=False)

    @classmethod
    def from_dict(cls, data: dict) -> PacsProfile:
        name = str(data.get("name", "")).strip()
        url = str(data.get("url", "")).strip().rstrip("/")
        if not name:
            raise ValueError(_msg('text.0325'))
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError:
            raise ValueError(_msg('text.0326')) from None
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None
                or parts.query or parts.fragment or any(c.isspace() or ord(c) < 32 for c in url)
                or (port is not None and not 1 <= port <= 65535)):
            raise ValueError(_msg('text.0327'))
        auth = str(data.get("auth", "none"))
        if auth not in ("none", "basic", "bearer"):
            raise ValueError(_msg('text.0328'))
        username = str(data.get("username", "")).strip()
        secret = str(data.get("secret", ""))
        if any(c in secret + username for c in "\r\n") or ":" in username:
            raise ValueError(_msg('text.0329'))
        if auth == "basic" and not username:
            raise ValueError(_msg('text.0330'))
        try:
            timeout = int(data.get("timeout", 15))
        except (TypeError, ValueError):
            raise ValueError(_msg('text.0331')) from None
        if not 3 <= timeout <= 120:
            raise ValueError(_msg('text.0331'))
        profile_id = str(data.get("id") or uuid.uuid4())
        try:
            uuid.UUID(profile_id)
        except ValueError:
            raise ValueError(_msg('text.0332')) from None
        return cls(profile_id, name, url, bool(data.get("enabled", True)), auth,
                   username, timeout, secret if auth != "none" else "")

    def public_dict(self) -> dict:
        data = asdict(self)
        data.pop("secret")
        return data


class PacsConfigStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> tuple[list[PacsProfile], str, bool, bool]:
        if not self.path.exists():
            return [], "", True, True
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("version") != 1:
                raise ValueError("unsupported version")
            profiles = [PacsProfile.from_dict(row) for row in data["profiles"]]
            if len({p.id for p in profiles}) != len(profiles):
                raise ValueError("duplicate profile")
            enabled_ids = [p.id for p in profiles if p.enabled]
            default = data.get("defaultId", "")
            if default not in enabled_ids:
                default = next(iter(enabled_ids), "")
            local, pacs = bool(data.get("localEnabled", True)), bool(data.get("pacsEnabled", True))
            return profiles, default, local or not pacs, pacs
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise ValueError(_msg('text.0333')) from exc

    def save(self, profiles: list[PacsProfile], default: str, local: bool, pacs: bool):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "profiles": [p.public_dict() for p in profiles],
                   "defaultId": default, "localEnabled": local, "pacsEnabled": pacs}
        fd, name = tempfile.mkstemp(prefix=".pacs-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
