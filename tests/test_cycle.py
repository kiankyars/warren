import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from warren.cycle import commit_plan, draft_plan, ingest, record_insight, stale_holes
from warren.search import search_corpus
from warren.store import load_state


def _root(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parent.parent
    shutil.copytree(src / "conversations", tmp_path / "conversations")
    shutil.copytree(src / "corpus", tmp_path / "corpus")
    (tmp_path / "store").mkdir()
    return tmp_path


def test_ingest_clusters_three_holes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    ingest(root=root)
    holes = stale_holes(root)
    ids = " ".join(h["id"] for h in holes)
    assert "grpo" in ids
    assert "japanese" in ids
    assert "afterclock" in ids
    assert all(h["stale"] for h in holes)


def test_last_active_uses_message_time(tmp_path: Path) -> None:
    root = _root(tmp_path)
    export = json.loads((root / "conversations" / "export.json").read_text())
    export[0]["mapping"]["m9"] = {
        "message": {
            "author": {"role": "user"},
            "content": {"parts": ["new activity after research would have run"]},
            "create_time": 9_999_999_999,
        }
    }
    (root / "conversations" / "export.json").write_text(json.dumps(export))
    ingest(root=root)
    grpo = next(h for h in stale_holes(root) if "grpo" in h["id"])
    expected = datetime.fromtimestamp(9_999_999_999, tz=timezone.utc).isoformat()
    assert grpo["last_active"] == expected


def test_ingest_drops_draft_plan(tmp_path: Path) -> None:
    root = _root(tmp_path)
    ingest(root=root)
    holes = stale_holes(root)
    record_insight(holes[0]["id"], "Plot reward vs KL.", ["corpus/grpo.md"], root=root)
    draft_plan(root=root)
    ingest(root=root)
    assert load_state(root).plan is None


def test_record_requires_corpus_source(tmp_path: Path) -> None:
    root = _root(tmp_path)
    ingest(root=root)
    holes = stale_holes(root)
    with pytest.raises(ValueError, match="corpus"):
        record_insight(holes[0]["id"], "unsourced", [], root=root)
    with pytest.raises(ValueError, match="corpus"):
        record_insight(holes[0]["id"], "unsourced", ["/etc/passwd"], root=root)


def test_search_hits_frozen_corpus(tmp_path: Path) -> None:
    hits = search_corpus("KL term", root=_root(tmp_path))
    assert hits
    assert hits[0]["path"].endswith("grpo.md")


def test_commit_requires_draft_and_writes_markdown(tmp_path: Path) -> None:
    root = _root(tmp_path)
    ingest(root=root)
    holes = stale_holes(root)
    record_insight(holes[0]["id"], "Plot reward vs KL before changing algorithms.", ["corpus/grpo.md"], root=root)
    plan = draft_plan(root=root)
    assert plan.committed is False
    path = commit_plan(root=root)
    assert path.exists()
    text = path.read_text()
    assert "Morning plan" in text
    assert "GRPO" in text.upper() or "grpo" in text.lower()
