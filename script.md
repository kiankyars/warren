# Warren — 60s demo (second screen)

Record **http://localhost:8790** → **warren** → new chat. First send only.

**Paste this, then hit record, then send:**

```
Ingest the bundled ChatGPT export. Research every stale hole against the local corpus with cited paths. Draft the morning plan. Stop before commit_plan.
```

If `commit_plan` asks for approval: **Deny**.

---

## SAY (read this)

**0–8s** — TrueForge chat, warren selected

Warren takes a ChatGPT export, clusters unfinished threads, researches them overnight, and drafts a morning plan I have to commit.

**8–12s** — paste + send

TrueForge is the harness. Warren is an MCP server it calls. The code is on a Qodo-reviewed PR, not pushed to main.

**12–45s** — narrate whatever tools actually appear

Ingest… three holes: GRPO, Japanese, afterclock. Search the local corpus. Record sourced insights. Draft the plan.

**45–60s** — draft on screen, or the approval card

Commit writes the plan file. TrueForge gates that. Qodo gated the code. A human has to approve both.

---

## DO / DON’T

- Full-screen Chrome. `http://localhost:8790` not `127.0.0.1`.
- Click **warren** only. Not rackshift. Not reprofix.
- Do not open GitHub Pages.
- Optional last 5s if the draft is already up: https://github.com/kiankyars/warren/pull/1 (Qodo review thread). Cut if it costs the commit-gate shot.

---

## Form (required fields only)

https://forms.gle/7DWiH2SDCJioWtdeA

Leave optional fields blank (teammates, deployed URL, LinkedIn).

**Email:** *(yours)*

**Team name:** SOLO

**Name of the person submitting:** *(yours)*

**Track you are submitting for:** check these three

- Best Use of TrueForge (NVIDIA DGX Spark)
- Best Code Quality (Mac Mini)
- Best UI (Apple iPads)

**GitHub link to project:** https://github.com/kiankyars/warren

**Video demo link:** *(public YouTube or Drive, after you upload)*

**What does your project do?**

Ingests a ChatGPT export, clusters unfinished threads, researches the stale ones against a local corpus, drafts a morning plan, and does not write that plan until a human commits it.

**How did you use TrueForge in your project?**

Warren runs as a TrueForge agent. The harness calls MCP tools to ingest the export, search `corpus/`, record sourced insights, and draft the plan. Sandbox is on. `commit_plan` is destructive and waits for human approval.

**How did you use Qodo in your project?**

Every substantive change is a GitHub PR reviewed by Qodo before merge. Direct pushes to `main` do not count. On https://github.com/kiankyars/warren/pull/1, Qodo flagged Highs (stale-hole timestamps, ingest leaving an old plan, tests mutating the checkout). Those were fixed on the same PR, then a follow-up `/agentic_review`, then merge. README has `## Qodo Code Review Evidence`.

**How did you use Bright Data in your project?**

Not used.
