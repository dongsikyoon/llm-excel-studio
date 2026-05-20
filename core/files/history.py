import json
import uuid
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path("data/histories")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _path(chat_id: str) -> Path:
    return HISTORY_DIR / f"{chat_id}.json"


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def _auto_title(messages: list[dict]) -> str:
    for m in messages:
        if m["role"] == "user":
            text = m["content"].strip().replace("\n", " ")
            return text[:35] + ("…" if len(text) > 35 else "")
    return "새 채팅"


def save(chat_id: str, messages: list[dict]) -> None:
    path = _path(chat_id)
    now = datetime.now().isoformat()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {"id": chat_id, "created_at": now}
    else:
        data = {"id": chat_id, "created_at": now}

    data["title"] = _auto_title(messages)
    data["messages"] = messages
    data["updated_at"] = now
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load(chat_id: str) -> list[dict]:
    path = _path(chat_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("messages", [])
    except Exception:
        return []


def list_chats() -> list[dict]:
    chats = []
    for path in HISTORY_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            chats.append({
                "id": data.get("id", path.stem),
                "title": data.get("title", "새 채팅"),
                "updated_at": data.get("updated_at", ""),
                "created_at": data.get("created_at", ""),
            })
        except Exception:
            pass
    return sorted(chats, key=lambda x: x["updated_at"], reverse=True)


def delete(chat_id: str) -> None:
    _path(chat_id).unlink(missing_ok=True)
