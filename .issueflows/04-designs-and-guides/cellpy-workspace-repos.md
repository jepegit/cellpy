# cellpy workspace — sibling repositories

The local workspace groups several git checkouts under `cellpy-workspace/`. Agents
working on cellpy v2 or Stage 0 issues should know where each kind of document lives.

## Repositories

| Checkout | Role |
|----------|------|
| `cellpy/` | Main consumer library (loaders, API, plotting, persistence). Issue-flow tracking under `.issueflows/`. |
| `cellpy-core/` | Compute engine (step/summary, schemas, legacy bridge). Integration guides under `.issueflows/04-designs-and-guides/`. |
| `architecture-plan/` | **Authoritative home for cellpy 2 plan documents** (Stage 0–N sequencing, gap analysis, topic plans). |

## Plan documents → `architecture-plan/`

**Do not look in `code-reviews/` for cellpy 2 plans.** That folder is legacy; plans were
moved to the **`architecture-plan`** repository.

When an issue or GitHub text says `code-reviews/cellpy2-…`, read the same filename from
`../architecture-plan/` instead (sibling checkout), e.g.:

- `architecture-plan/cellpy2-architecture-plan.md` — coordinating overview
- `architecture-plan/cellpy2-plans-gap-analysis.md` — gap analysis (F8, G5, G6, …)
- `architecture-plan/cellpy2-loader-port-and-extraction-plan.md`
- `architecture-plan/cellpy-file-loading-refactor-plan.md`
- `architecture-plan/stage0-github-issues.md` — Stage 0 issue breakdown

Local path from the `cellpy` repo root: `../architecture-plan/<file>.md`.

## Related durable docs (in `cellpy`)

- [`cellpy-v2-epic.md`](cellpy-v2-epic.md) — consumer-side v2 epic in this repo
- [`cellpy-v2-branching.md`](cellpy-v2-branching.md) — `master` vs `v2` branch rules

## Stage 0 tracking

GitHub [jepegit/cellpy#439](https://github.com/jepegit/cellpy/issues/439) tracks Stage 0;
local copy: `.issueflows/01-current-issues/issue439_original.md` when active.
