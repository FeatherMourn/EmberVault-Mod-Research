"""Small JSON-backed community workflow for local development and review tests."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class CommunityService:
    def __init__(self, root: Path):
        self.path = Path(root) / "community-data.json"

    def _load(self):
        if not self.path.exists():
            return {"users": [], "submissions": [], "threads": [], "moderation": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def create_user(self, display_name: str, roles=None):
        if not display_name.strip():
            raise ValueError("Display name is required")
        roles = roles or ["member"]
        if any(role not in {"member", "creator", "researcher", "moderator", "maintainer"} for role in roles):
            raise ValueError("Unknown role")
        data = self._load(); user = {"id": f"EV-USER-{uuid.uuid4().hex[:8].upper()}", "display_name": display_name.strip(), "roles": sorted(set(roles)), "status": "active"}
        data["users"].append(user); self._save(data); return user

    def submit(self, author_id: str, kind: str, title: str):
        if kind not in {"mod", "research", "knowledge", "project"} or not title.strip():
            raise ValueError("Submission kind and title are required")
        data = self._load(); author = next((u for u in data["users"] if u["id"] == author_id and u["status"] == "active"), None)
        if not author:
            raise ValueError("Active author is required")
        record = {"id": f"EV-SUB-{uuid.uuid4().hex[:8].upper()}", "kind": kind, "title": title.strip(), "author_id": author_id, "status": "submitted", "submitted_at": datetime.now(timezone.utc).isoformat(), "review_notes": ""}
        data["submissions"].append(record); self._save(data); return record

    def review(self, reviewer_id: str, submission_id: str, action: str, notes: str = ""):
        if action not in {"approve", "request-changes", "reject"}:
            raise ValueError("Unknown review action")
        data = self._load(); reviewer = next((u for u in data["users"] if u["id"] == reviewer_id and u["status"] == "active" and ({"moderator", "maintainer"} & set(u["roles"]))), None)
        submission = next((s for s in data["submissions"] if s["id"] == submission_id), None)
        if not reviewer or not submission:
            raise ValueError("Active moderator and submission are required")
        submission["status"] = {"approve": "approved", "request-changes": "changes-requested", "reject": "rejected"}[action]
        submission["review_notes"] = notes.strip(); self._save(data); return submission

    def publish_submission(self, publisher_id: str, submission_id: str):
        data = self._load(); publisher = next((u for u in data["users"] if u["id"] == publisher_id and u["status"] == "active" and ({"moderator", "maintainer"} & set(u["roles"]))), None)
        submission = next((s for s in data["submissions"] if s["id"] == submission_id), None)
        if not publisher or not submission or submission["status"] != "approved":
            raise ValueError("Only an active reviewer can publish an approved submission")
        submission["status"] = "published"; submission["published_at"] = datetime.now(timezone.utc).isoformat(); self._save(data); return submission

    def create_thread(self, author_id: str, title: str, body: str):
        data = self._load(); author = next((u for u in data["users"] if u["id"] == author_id and u["status"] == "active"), None)
        if not author or not title.strip() or not body.strip():
            raise ValueError("Active author, title, and body are required")
        thread = {"id": f"EV-THREAD-{uuid.uuid4().hex[:8].upper()}", "title": title.strip(), "author_id": author_id, "status": "open", "posts": [{"id": f"EV-POST-{uuid.uuid4().hex[:8].upper()}", "author_id": author_id, "body": body.strip(), "created_at": datetime.now(timezone.utc).isoformat()}]}
        data["threads"].append(thread); self._save(data); return thread

    def reply_thread(self, author_id: str, thread_id: str, body: str):
        data = self._load(); author = next((u for u in data["users"] if u["id"] == author_id and u["status"] == "active"), None)
        thread = next((t for t in data["threads"] if t["id"] == thread_id), None)
        if not author or not thread or thread["status"] != "open" or not body.strip():
            raise ValueError("An active author, open thread, and non-empty body are required")
        post = {"id": f"EV-POST-{uuid.uuid4().hex[:8].upper()}", "author_id": author_id, "body": body.strip(), "created_at": datetime.now(timezone.utc).isoformat()}
        thread["posts"].append(post); self._save(data); return post

    def create_project(self, owner_id: str, title: str, visibility: str = "private", linked_records=None):
        if visibility not in {"private", "unlisted", "public"} or not title.strip():
            raise ValueError("Project title and visibility are required")
        data = self._load(); owner = next((u for u in data["users"] if u["id"] == owner_id and u["status"] == "active"), None)
        if not owner:
            raise ValueError("Active project owner is required")
        project = {"id": f"EV-PROJECT-{uuid.uuid4().hex[:8].upper()}", "title": title.strip(), "owner_id": owner_id, "visibility": visibility, "status": "review" if visibility == "public" else "draft", "linked_records": sorted(set(linked_records or []))}
        data.setdefault("projects", []).append(project); self._save(data); return project

    def moderate(self, moderator_id: str, target_id: str, action: str, reason: str):
        if action not in {"hide", "lock", "restore", "suspend"} or not reason.strip():
            raise ValueError("Moderation action and reason are required")
        data = self._load(); moderator = next((u for u in data["users"] if u["id"] == moderator_id and u["status"] == "active" and ({"moderator", "maintainer"} & set(u["roles"]))), None)
        if not moderator:
            raise ValueError("Active moderator is required")
        target_user = next((u for u in data["users"] if u["id"] == target_id), None)
        target_thread = next((t for t in data["threads"] if t["id"] == target_id), None)
        if action == "suspend":
            if not target_user:
                raise ValueError("Suspension target must be a user")
            target_user["status"] = "suspended"
        elif target_thread:
            target_thread["status"] = {"hide": "hidden", "lock": "locked", "restore": "open"}[action]
        else:
            raise ValueError("Moderation target was not found")
        record = {"id": f"EV-MOD-{uuid.uuid4().hex[:8].upper()}", "moderator_id": moderator_id, "target_id": target_id, "action": action, "reason": reason.strip(), "created_at": datetime.now(timezone.utc).isoformat()}
        data["moderation"].append(record); self._save(data); return record
