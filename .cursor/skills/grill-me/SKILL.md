---
name: grill-me
description: >-
  Interview the user relentlessly about a plan or design until every branch of
  the decision tree is resolved, then feed the conclusions into the issue plan.
  Use when the user wants to stress-test a plan, asks to "grill me", or during
  /iflow-plan when grilling is turned on. Off via "stop grilling" / "normal mode".
---

# Grill me — relentless planning interview

Interview the user about every aspect of the plan until you reach a shared,
unambiguous understanding. Walk down each branch of the design tree, resolving
dependencies between decisions one at a time. The goal is to surface hidden
assumptions and edge cases **before** they get encoded in code or written into
`.issueflows/01-current-issues/issue<N>_plan.md`.

## When to use

- The user asks to be grilled / stress-tested ("grill me", "poke holes in this").
- During `/iflow-plan`, when grilling is active (see *Activation* below), to
  pressure-test the approach before the plan file is drafted.

## How to grill

- **One question at a time.** Never batch questions. Wait for the answer before
  moving to the next branch.
- **Always recommend an answer.** For each question, give your recommended option
  and a one-line rationale, so the user can accept quickly or push back.
- **Explore before asking.** If a question can be answered by reading the code,
  the issue text, or `.issueflows/04-designs-and-guides/`, explore first
  and confirm what you found instead of asking the user to do your homework.
- **Follow the decision tree.** Resolve upstream decisions before the ones that
  depend on them; let earlier answers prune later branches.
- **Stay on scope.** Grill the issue at hand. Park genuinely separate concerns as
  follow-up notes rather than expanding the interview indefinitely.
- **Know when to stop.** End when every open branch is resolved (or explicitly
  deferred) and you can restate the plan without ambiguity. Summarize the agreed
  decisions so they can flow straight into the plan.

## Activation

This skill is **dormant by default**: it engages only when the user asks for it
("grill me") or when a project turns it on for planning.

Turn it off again for the rest of a session with **"stop grilling"** or
**"normal mode"**. (To make grilling on by default during planning for this
project, set `grill_me_default = true` under `[issueflow]` in
`.issueflows/config.toml` and re-run `issue-flow update`.)


## Boundaries

- Grilling is a **planning** aid: it questions and aligns, it does not write code.
- Hand the agreed decisions to `/iflow-plan` so they land in `issue<N>_plan.md`;
  implementation still goes through `/iflow-start`.
