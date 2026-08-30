from __future__ import annotations

import argparse
import json
import sys

from warren.cycle import commit_plan, draft_plan, ingest, record_insight, stale_holes
from warren.search import search_corpus
from warren.serialize import insight_to_dict, plan_to_dict, snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="warren")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest", help="parse conversations/export.json into holes")
    sub.add_parser("status", help="list holes and the current plan")
    search_p = sub.add_parser("search", help="search the local corpus")
    search_p.add_argument("query")
    rec = sub.add_parser("record", help="store a researched insight for a hole")
    rec.add_argument("hole_id")
    rec.add_argument("content")
    rec.add_argument("--source", action="append", default=[])
    sub.add_parser("draft-plan", help="rank holes into an uncommitted morning plan")
    sub.add_parser("commit-plan", help="write store/plan-YYYY-MM-DD.md; irreversible")
    sub.add_parser("serve", help="operator UI")
    mcp_p = sub.add_parser("mcp", help="MCP endpoint for TrueForge")
    mcp_p.add_argument("--port", type=int, default=8786)

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        ingest()
        json.dump({"holes": stale_holes()}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "status":
        json.dump(snapshot(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "search":
        json.dump(search_corpus(args.query), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "record":
        json.dump(insight_to_dict(record_insight(args.hole_id, args.content, args.source)), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "draft-plan":
        json.dump(plan_to_dict(draft_plan()), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "commit-plan":
        path = commit_plan()
        json.dump({"committed": str(path)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.cmd == "serve":
        from warren.web import serve

        serve()
        return 0
    if args.cmd == "mcp":
        try:
            from warren.mcp_server import serve_mcp
        except ModuleNotFoundError:
            sys.stderr.write("MCP extra missing. Install with: uv sync --extra mcp\n")
            return 1
        serve_mcp(args.port)
        return 0
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
