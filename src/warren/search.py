from __future__ import annotations

from pathlib import Path

from warren.store import repo_root


def search_corpus(query: str, root: Path | None = None, limit: int = 8) -> list[dict]:
    base = repo_root(root)
    terms = [t.lower() for t in query.split() if len(t) > 2]
    if not terms:
        return []
    hits: list[dict] = []
    for path in sorted((base / "corpus").glob("*.md")):
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            if any(term in low for term in terms):
                hits.append({"path": str(path.relative_to(base)), "line": i, "text": line.strip()})
                if len(hits) >= limit:
                    return hits
    return hits
