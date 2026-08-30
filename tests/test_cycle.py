from pathlib import Path

from warren.cycle import commit_plan, draft_plan, ingest, record_insight, stale_holes
from warren.search import search_corpus
from warren.store import repo_root


def test_ingest_clusters_three_holes() -> None:
    root = repo_root(Path(__file__).resolve().parent.parent)
    ingest(root=root)
    holes = {h["id"]: h for h in stale_holes(root)}
    assert "grpo" in str(holes.keys()) or any("grpo" in h["id"] for h in holes.values())
    assert any("japanese" in h["id"] for h in holes.values())
    assert any("afterclock" in h["id"] for h in holes.values())
    assert all(h["stale"] for h in holes.values())


def test_search_hits_frozen_corpus() -> None:
    hits = search_corpus("KL term", root=Path(__file__).resolve().parent.parent)
    assert hits
    assert hits[0]["path"].endswith("grpo.md")


def test_commit_requires_draft_and_writes_markdown(tmp_path: Path, monkeypatch) -> None:
    root = repo_root(Path(__file__).resolve().parent.parent)
    ingest(root=root)
    holes = stale_holes(root)
    record_insight(holes[0]["id"], "Plot reward vs KL before changing algorithms.", ["corpus/grpo.md"], root=root)
    plan = draft_plan(root=root)
    assert plan.committed is False
    path = commit_plan(root=root)
    assert path.exists()
    text = path.read_text()
    assert "Morning plan" in text
    assert holes[0]["name"] in text or "GRPO" in text.upper() or "grpo" in text.lower()
