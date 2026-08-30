from __future__ import annotations

from warren.cycle import commit_plan, draft_plan, ingest, record_insight, stale_holes
from warren.models import Insight, Plan
from warren.search import search_corpus
from warren.store import load_state, repo_root


def snapshot(root=None) -> dict:
    base = repo_root(root)
    state = load_state(base)
    if not state.holes:
        ingest(root=base)
        state = load_state(base)
    return {
        "repo_root": str(base),
        "holes": stale_holes(base),
        "insights": [
            {
                "hole_id": i.hole_id,
                "content": i.content,
                "sources": i.sources,
                "created_at": i.created_at.isoformat(),
            }
            for i in state.insights[-12:]
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
        "plan_path": (
            str(base / "store" / f"plan-{state.plan.date}.md")
            if state.plan and state.plan.committed and (base / "store" / f"plan-{state.plan.date}.md").exists()
            else None
        ),
    }


def insight_to_dict(insight: Insight) -> dict:
    return {
        "hole_id": insight.hole_id,
        "content": insight.content,
        "sources": insight.sources,
        "created_at": insight.created_at.isoformat(),
    }


def plan_to_dict(plan: Plan) -> dict:
    return {
        "date": plan.date,
        "committed": plan.committed,
        "items": [
            {
                "hole_id": it.hole_id,
                "hole_name": it.hole_name,
                "action": it.action,
                "sources": it.sources,
                "score": it.score,
            }
            for it in plan.items
        ],
    }
