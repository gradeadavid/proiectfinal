import json
import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TITLE_MAX_LEN = 40


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(normalize_email(email)))


def _file_for(email: str) -> Path:
    normalized = normalize_email(email)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
    return DATA_DIR / f"{digest}.json"


def _load_user_data(email: str) -> dict:
    path = _file_for(email)
    if not path.exists():
        return {"email": normalize_email(email), "conversations": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_user_data(email: str, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(_file_for(email), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_conversations(email: str) -> list[dict]:
    """Lightweight list for the sidebar (id, title, created_at),
    newest first."""
    data = _load_user_data(email)
    conversations = [
        {"id": c["id"], "title": c["title"], "created_at": c["created_at"]}
        for c in data["conversations"]
    ]
    conversations.sort(key=lambda c: c["created_at"], reverse=True)
    return conversations


def load_conversation_messages(email: str, conversation_id: str) -> list[dict]:
    data = _load_user_data(email)
    for conversation in data["conversations"]:
        if conversation["id"] == conversation_id:
            return conversation["messages"]
    return []


def create_conversation(email: str, first_message: str) -> str:
    """Create a new conversation, titled from the first message,
    and return its id."""
    data = _load_user_data(email)
    conversation_id = uuid.uuid4().hex

    title = " ".join(first_message.strip().split())
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN].rstrip() + "..."

    data["email"] = normalize_email(email)
    data["conversations"].append({
        "id": conversation_id,
        "title": title or "Conversatie noua",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": []
    })
    _save_user_data(email, data)
    return conversation_id


def get_conversation(email: str, conversation_id: str) -> dict | None:
    """Full conversation record (id, title, created_at, messages)
    for export."""
    data = _load_user_data(email)
    for conversation in data["conversations"]:
        if conversation["id"] == conversation_id:
            return conversation
    return None


def import_conversation(email: str, title: str, messages: list[dict]) -> str:
    """Create a new conversation from imported messages and return its id.

    Always assigns a fresh id/created_at, regardless of what the imported
    file contains, so an import can never collide with or overwrite an
    existing conversation.
    """
    data = _load_user_data(email)
    conversation_id = uuid.uuid4().hex

    title = " ".join((title or "").strip().split())
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN].rstrip() + "..."

    now = datetime.now(timezone.utc).isoformat()
    data["email"] = normalize_email(email)
    data["conversations"].append({
        "id": conversation_id,
        "title": title or "Conversatie importata",
        "created_at": now,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "timestamp": m.get("timestamp", now)
            }
            for m in messages
        ]
    })
    _save_user_data(email, data)
    return conversation_id


def delete_conversation(email: str, conversation_id: str) -> None:
    data = _load_user_data(email)
    data["conversations"] = [
        c for c in data["conversations"] if c["id"] != conversation_id
    ]
    _save_user_data(email, data)


def rename_conversation(email: str, conversation_id: str,
                        new_title: str) -> None:
    title = " ".join(new_title.strip().split())
    if not title:
        return
    if len(title) > TITLE_MAX_LEN:
        title = title[:TITLE_MAX_LEN].rstrip() + "..."

    data = _load_user_data(email)
    for conversation in data["conversations"]:
        if conversation["id"] == conversation_id:
            conversation["title"] = title
            break
    _save_user_data(email, data)


def append_messages(email: str, conversation_id: str,
                    messages: list[dict]) -> None:
    """Append one or more {role, content, response_time?} messages to an
    existing conversation. response_time (seconds) is optional and only
    set for assistant messages."""
    data = _load_user_data(email)
    now = datetime.now(timezone.utc).isoformat()

    for conversation in data["conversations"]:
        if conversation["id"] == conversation_id:
            for message in messages:
                entry = {
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": now
                }
                if message.get("response_time") is not None:
                    entry["response_time"] = message["response_time"]
                conversation["messages"].append(entry)
            break

    _save_user_data(email, data)
