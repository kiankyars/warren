from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from warren.models import Insight, Plan, PlanItem, State
from warren.store import extract_holes, load_state, parse_chatgpt_export, repo_root, save_state


def ingest(export_path: Path | None = None, root: Path | None = None) -> State:
    base = repo_root(root)
    path = export_path or (base / "conversations" / "export.json")
    conversations = parse_chatgpt_export(path)
    state = load_state(base)
    researched = {hid: h.last_researched_at for hid, h in state.holes.items()}
    state.conversations = {c.id: c for c in conversations}
    state.holes = {h.id: h for h in extract_holes(conversations)}
    for hid, hole in state.holes.items():
        hole.last_researched_at = researched.get(hid)
    save_state(base, state)
    return state


def stale_holes(root: Path | None = None) -> list[dict]:
    state = load_state(repo_root(root))
    holes = sorted(state.holes.values(), key=lambda h: (-h.message_count, h.name))
    return [
        {
            "id": h.id,
            "name": h.name,
            "message_count": h.message_count,
            "conversations": len(h.conversation_ids),
            "stale": h.stale,
            "last_active": None if h.last_active is None else h.last_active.isoformat(),
        }
        for h in holes
    ]


def record_insight(hole_id: str, content: str, sources: list[str], root: Path | None = None) -> Insight:
    base = repo_root(root)
    state = load_state(base)
    if hole_id not in state.holes:
        raise ValueError(f"unknown hole {hole_id!r}")
    if not content.strip():
        raise ValueError("empty insight")
    insight = Insight(
        hole_id=hole_id,
        content=content.strip(),
        sources=list(sources),
        created_at=datetime.now(timezone.utc),
    )
    state.insights.append(insight)
    state.holes[hole_id].last_researched_at = insight.created_at
    save_state(base, state)
    return insight


def draft_plan(root: Path | None = None) -> Plan:
    base = repo_root(root)
    state = load_state(base)
    items: list[PlanItem] = []
    by_hole: dict[str, list[Insight]] = {}
    for insight in state.insights:
        by_hole.setdefault(insight.hole_id, []).append(insight)
    for hole in sorted(state.holes.values(), key=lambda h: -h.message_count):
        latest = by_hole.get(hole.id, [])
        latest.sort(key=lambda i: i.created_at, reverse=True)
        if not latest:
            action = f"Open the {hole.message_count}-message thread on {hole.name} and write the next concrete step."
            sources: list[str] = []
            score = float(hole.message_count)
        else:
            insight = latest[0]
            action = insight.content
            sources = insight.sources
            score = float(hole.message_count) + 10.0
        items.append(PlanItem(hole_id=hole.id, hole_name=hole.name, action=action, sources=sources, score=score))
    items.sort(key=lambda it: -it.score)
    state.plan = Plan(date=date.today().isoformat(), items=items, committed=False)
    save_state(base, state)
    return state.plan


def commit_plan(root: Path | None = None) -> Path:
    base = repo_root(root)
    state = load_state(base)
    if state.plan is None or not state.plan.items:
        raise ValueError("no draft plan to commit")
    state.plan.committed = True
    save_state(base, state)
    out = base / "store" / f"plan-{state.plan.date}.md"
    lines = [f"# Morning plan {state.plan.date}", ""]
    for i, item in enumerate(state.plan.items, start=1):
        src = ", ".join(item.sources) if item.sources else "chat history"
        lines.append(f"{i}. **{item.hole_name}** — {item.action} ({src})")
    out.write_text("\n".join(lines) + "\n")
    return out
