# Issue #876: CI: the docs-mock 'essential' check also runs on code PRs (duplicate check name)

Source: https://github.com/jepegit/cellpy/issues/876

## Original issue text

Noticed while merging #110 on cellpy/cellpy-simple-gui and copied to jepegit/cellpy

First check if this problem also might exist for the cellpy repository. If so, find a good solution. Notice that the text below is for the cellpy/cellpy-simple-gui so for example the time for running essential tests for jepegit/cellpy might be much longer.

## What happens

There are two workflows, both named `Essential tests` with a job named `essential`:

- `essential-tests.yml` — real run, `paths:` code/test/lockfile
- `essential-tests-docs.yml` — mock, `paths-ignore:` the same list

`paths-ignore` is evaluated per changed file: a workflow runs if **any** changed file is outside the ignore list. So a PR that touches code **and** docs — which most of ours do, since we update `CELLPY_PAINPOINTS.md` alongside the change — satisfies *both* trigger sets, and both workflows run under the same check name.

On #110 both ran:

| run | steps |
|---|---|
| `31338736677` | Sync dependencies → **Run essential tests** (27s) |
| `31338736695` | "Document-only change — mock essential tests" (4s) |

## Why it matters

`gh pr checks 110` surfaced only the 4-second mock. Nothing in that output distinguishes "tests passed" from "tests were skipped" — the check name, the conclusion and the UI row are identical. Anyone reading it, human or agent, sees a green `essential` and reasonably concludes the suite ran.

**Nothing is currently broken:** the real run did execute on #110 and passed. The hazard is that a green mock is indistinguishable from a green real run, so a failing real run could be easy to overlook — and it makes the check untrustworthy as evidence.

## Suggested fix

Collapse to a single always-triggered workflow that decides internally, e.g. `dorny/paths-filter` gating the pytest step, so exactly one check run reports per PR.

Simplest alternative: drop the mock entirely and always run the real suite. It takes ~27s; the mock saves that at the cost of an ambiguous signal, which is a poor trade.
