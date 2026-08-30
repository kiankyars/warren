from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from warren.cycle import commit_plan, draft_plan, ingest, record_insight, stale_holes
from warren.search import search_corpus
from warren.serialize import insight_to_dict, plan_to_dict, snapshot

mcp = FastMCP(
    "warren",
    instructions=(
        "Ingest the ChatGPT export, research stale holes against the local corpus, "
        "record sourced insights, draft a morning plan, and stop. commit_plan is irreversible."
    ),
)


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
def ingest_export() -> dict:
    """Parse conversations/export.json and rebuild rabbit holes."""
    ingest()
    return {"holes": stale_holes()}


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False})
def list_holes() -> dict:
    """List clustered unfinished threads and whether they still need research."""
    return snapshot()


@mcp.tool(annotations={"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False})
def search_notes(query: str) -> list[dict]:
    """Search corpus/*.md for passages matching the query."""
    return search_corpus(query)


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
def record_research(hole_id: str, content: str, sources: list[str]) -> dict:
    """Store a sourced insight on a hole. Does not commit the morning plan."""
    return insight_to_dict(record_insight(hole_id, content, sources))


@mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
def draft_morning_plan() -> dict:
    """Rank holes into an uncommitted plan from chat volume plus latest insights."""
    return plan_to_dict(draft_plan())


@mcp.tool(
    name="commit_plan",
    annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False},
)
def commit_plan_tool() -> dict:
    """Write store/plan-YYYY-MM-DD.md. Pause for a human before this."""
    path = commit_plan()
    return {"committed": str(path)}


def serve_mcp(port: int = 8786) -> None:
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
