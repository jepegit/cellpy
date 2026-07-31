# cellpy workspace — sibling repositories

The local workspace groups several git checkouts under `cellpy-workspace/`. Agents
working on cellpy v2 or Stage issues should know where each kind of document lives.

## Repositories

| Checkout | Role |
|----------|------|
| `cellpy/` | Main consumer library (loaders, API, plotting, persistence). Issue-flow tracking under `.issueflows/`. |
| `cellpy-core/` | Compute engine (step/summary, schemas, legacy bridge). Integration guides under `.issueflows/04-designs-and-guides/`. |
| `cellpy-design-and-development/` | **Authoritative home for cellpy 2 plan documents** (Stage 0–N sequencing, gap analysis, topic plans). Canonical remote: `cellpy/cellpy-design-and-development`. Formerly `architecture-plan`. |
| `cellpy-examples/` | Example notebooks/scripts. Canonical remote: `cellpy/cellpy-examples`. Formerly `Examples`. |
| `cellpy-simple-gui/` | Desktop explorer app (FastAPI + pywebview) on cellpy ≥ 2.1. Canonical remote: `cellpy/cellpy-simple-gui`. |

## `cellpy-design-and-development` fork mirror (cloud agents)

Cursor Cloud and similar tools often cannot use two GitHub orgs in one session. A read
mirror exists at **[jepegit/cellpy-design-and-development](https://github.com/jepegit/cellpy-design-and-development)**.

| Remote | Use |
|--------|------|
| `cellpy/cellpy-design-and-development` | **Source of truth** — open PRs and merge plan changes here |
| `jepegit/cellpy-design-and-development` | **Mirror** — clone target for cloud agents; `main` synced from upstream |

Sync: GitHub Action `sync-upstream.yml` on the fork (every 6h + manual *Run workflow*).
Do **not** commit plan changes directly to the fork's `main`.

Local canonical checkout (as in this workspace):

```bash
git clone https://github.com/cellpy/cellpy-design-and-development.git
```

Cloud / single-org checkout:

```bash
git clone https://github.com/jepegit/cellpy-design-and-development.git
```

## Plan documents → `cellpy-design-and-development/`

**Do not look in `code-reviews/` for cellpy 2 plans.** That folder is legacy; plans live
in the **`cellpy-design-and-development`** repository (formerly `architecture-plan`).

**Start at** [`../cellpy-design-and-development/CURRENT.md`](../../../cellpy-design-and-development/CURRENT.md)
for the active stage and open plans.

Layout:

| Path | Role |
|------|------|
| `cellpy-design-and-development/CURRENT.md` | What we’re working through now |
| `cellpy-design-and-development/PATHS.md` | Old flat basename → current path |
| `cellpy-design-and-development/ecosystem/` | Durable cellpy + cellpy-core overview, module layout, conventions |
| `cellpy-design-and-development/roadmap/` | Coordinator + gap analysis + `stages/` issue sets |
| `cellpy-design-and-development/active/` | Plans still guiding open / near-term work |
| `cellpy-design-and-development/archive/` | Executed topic plans (`foundations/`, `redesigns/`) |
| `cellpy-design-and-development/research/` | Scans and evidence |

Common entry points:

- `cellpy-design-and-development/CURRENT.md` — active work
- `cellpy-design-and-development/roadmap/cellpy2-architecture-plan.md` — coordinating overview + stage dashboard
- `cellpy-design-and-development/roadmap/cellpy2-plans-gap-analysis.md` — gap analysis
- `cellpy-design-and-development/roadmap/stages/stage5-github-issues.md` — current stage issue set
- `cellpy-design-and-development/ecosystem/overview.md` — two-package primer

When an issue or GitHub text says `code-reviews/cellpy2-…`,
`architecture-plan/…`, or a **flat** plan basename, look it up in
[`cellpy-design-and-development/PATHS.md`](../../../cellpy-design-and-development/PATHS.md).

Local path from the `cellpy` repo root: `../cellpy-design-and-development/…`.

## Related durable docs (in `cellpy`)

- [`cellpy-v2-epic.md`](cellpy-v2-epic.md) — consumer-side v2 epic in this repo
- [`cellpy-v2-branching.md`](cellpy-v2-branching.md) — `master` vs `v2` branch rules

## Stage tracking

Stage 0–4 are complete (v2.0.0 / v2.1.0 shipped). Current planning stage is **Stage 5
(2.2)** — see `cellpy-design-and-development/CURRENT.md` and GitHub
[jepegit/cellpy#783](https://github.com/jepegit/cellpy/issues/783).
