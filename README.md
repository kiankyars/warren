# Warren

Unfinished ChatGPT threads, clustered, researched against `corpus/`, then a morning plan that does not write until you commit it.

Demo data is already in the repo: `conversations/export.json` is a synthetic ChatGPT export (not a real user dump). `uv run warren ingest` loads it. Nothing to upload.

TrueForge runs the cycle (MCP, sandbox, subagents, approval on `commit_plan`). Qodo reviews the PRs.

## Run

Live demo (static, no TrueForge): https://kiankyars.github.io/warren/

```sh
uv sync --extra dev --extra mcp
uv run pytest -q
uv run warren ingest
uv run warren status
uv run warren serve          # http://127.0.0.1:8785
uv run warren mcp --port 8786
```

TrueForge: `npx @truefoundry/trueforge` → http://localhost:8790. Agent spec: `trueforge/agent.json`.

`commit_plan` writes `store/plan-YYYY-MM-DD.md`. That is the irreversible step.

## Qodo Code Review Evidence

Substantive changes go through a PR. Direct pushes to `main` do not count.

- Representative PR: _after first reviewed merge_
- What Qodo surfaced: _after the review thread exists_
- Follow-up review: same PR, second `/agentic_review`

## License

MIT
