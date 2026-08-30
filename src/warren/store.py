from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

from warren.models import Conversation, Hole, Insight, Message, Plan, PlanItem, State

STOP = frozenset("a an the of and or to for in on vs with how what why my a".split())


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "conversations").is_dir() and (candidate / "corpus").is_dir():
            return candidate
    raise FileNotFoundError("not inside a Warren repository")


def state_path(root: Path) -> Path:
    return root / "store" / "state.json"


def _dt(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    return datetime.fromisoformat(str(value))


def _dt_out(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def parse_chatgpt_export(path: Path) -> list[Conversation]:
    raw = json.loads(path.read_text())
    conversations: list[Conversation] = []
    for conv in raw:
        messages: list[Message] = []
        mapping = conv.get("mapping") or {}
        for node in mapping.values():
            msg = (node or {}).get("message") or {}
            role = (msg.get("author") or {}).get("role")
            if role not in {"user", "assistant"}:
                continue
            parts = (msg.get("content") or {}).get("parts") or []
            text = "\n".join(p for p in parts if isinstance(p, str) and p.strip())
            if not text:
                continue
            messages.append(Message(role=role, content=text, created_at=_dt(msg.get("create_time"))))
        messages.sort(key=lambda m: m.created_at or datetime.min.replace(tzinfo=timezone.utc))
        conversations.append(
            Conversation(
                id=str(conv.get("conversation_id") or conv.get("id") or conv.get("title")),
                title=str(conv.get("title") or "Untitled"),
                created_at=_dt(conv.get("create_time")),
                messages=tuple(messages),
            )
        )
    return conversations


def extract_holes(conversations: list[Conversation]) -> list[Hole]:
    buckets: dict[str, list[Conversation]] = {}
    for conv in conversations:
        if conv.message_count < 2:
            continue
        key = _topic_key(conv.title)
        buckets.setdefault(key, []).append(conv)
    holes: list[Hole] = []
    for key, group in buckets.items():
        last_active = max((t for c in group if (t := _last_activity(c))), default=None)
        holes.append(
            Hole(
                id=key.replace(" ", "-"),
                name=max((c.title for c in group), key=len),
                conversation_ids=[c.id for c in group],
                message_count=sum(c.message_count for c in group),
                last_active=last_active,
            )
        )
    holes.sort(key=lambda h: (-h.message_count, h.name))
    return holes


def _last_activity(conv: Conversation) -> datetime | None:
    times = [m.created_at for m in conv.messages if m.created_at]
    if conv.created_at:
        times.append(conv.created_at)
    return max(times) if times else None


def corpus_sources(root: Path, sources: list[str]) -> list[str]:
    corpus = (root / "corpus").resolve()
    if not sources:
        raise ValueError("research requires at least one corpus/ path")
    out: list[str] = []
    for src in sources:
        raw = Path(src)
        resolved = raw.resolve() if raw.is_absolute() else (root / src).resolve()
        try:
            resolved.relative_to(corpus)
        except ValueError:
            raise ValueError(f"source must be under corpus/: {src}") from None
        if not resolved.is_file():
            raise ValueError(f"missing corpus file: {src}")
        out.append(str(resolved.relative_to(root)))
    return out


@contextmanager
def state_lock(root: Path):
    path = root / "store" / ".lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a+")
    if fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        if fcntl is not None:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def _topic_key(title: str) -> str:
    tokens = [t.lower().strip(".,:?!") for t in title.split() if t.lower().strip(".,:?!")]
    keep = [t for t in tokens if t not in STOP and len(t) > 2]
    if not keep:
        return title.lower().strip()
    return keep[0]


def load_state(root: Path) -> State:
    path = state_path(root)
    if not path.exists():
        return State()
    raw = json.loads(path.read_text())
    conversations = {
        cid: Conversation(
            id=cid,
            title=c["title"],
            created_at=_dt(c.get("created_at")),
            messages=tuple(
                Message(role=m["role"], content=m["content"], created_at=_dt(m.get("created_at")))
                for m in c.get("messages", [])
            ),
        )
        for cid, c in raw.get("conversations", {}).items()
    }
    holes = {
        hid: Hole(
            id=hid,
            name=h["name"],
            conversation_ids=list(h["conversation_ids"]),
            message_count=int(h["message_count"]),
            last_active=_dt(h.get("last_active")),
            last_researched_at=_dt(h.get("last_researched_at")),
        )
        for hid, h in raw.get("holes", {}).items()
    }
    insights = [
        Insight(
            hole_id=i["hole_id"],
            content=i["content"],
            sources=list(i.get("sources", [])),
            created_at=_dt(i["created_at"]) or datetime.now(timezone.utc),
        )
        for i in raw.get("insights", [])
    ]
    plan = None
    if raw.get("plan"):
        p = raw["plan"]
        plan = Plan(
            date=p["date"],
            committed=bool(p.get("committed")),
            items=[
                PlanItem(
                    hole_id=it["hole_id"],
                    hole_name=it["hole_name"],
                    action=it["action"],
                    sources=list(it.get("sources", [])),
                    score=float(it["score"]),
                )
                for it in p.get("items", [])
            ],
        )
    return State(conversations=conversations, holes=holes, insights=insights, plan=plan)


def save_state(root: Path, state: State) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "conversations": {
            cid: {
                "title": c.title,
                "created_at": _dt_out(c.created_at),
                "messages": [
                    {"role": m.role, "content": m.content, "created_at": _dt_out(m.created_at)}
                    for m in c.messages
                ],
            }
            for cid, c in state.conversations.items()
        },
        "holes": {
            hid: {
                "name": h.name,
                "conversation_ids": h.conversation_ids,
                "message_count": h.message_count,
                "last_active": _dt_out(h.last_active),
                "last_researched_at": _dt_out(h.last_researched_at),
            }
            for hid, h in state.holes.items()
        },
        "insights": [
            {
                "hole_id": i.hole_id,
                "content": i.content,
                "sources": i.sources,
                "created_at": _dt_out(i.created_at),
            }
            for i in state.insights
        ],
        "plan": None
        if state.plan is None
        else {
            "date": state.plan.date,
            "committed": state.plan.committed,
            "items": [
                {
                    "hole_id": it.hole_id,
                    "hole_name": it.hole_name,
                    "action": it.action,
                    "sources": it.sources,
                    "score": it.score,
                }
                for it in state.plan.items
            ],
        },
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
