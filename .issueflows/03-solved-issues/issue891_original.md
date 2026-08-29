# Issue #891: Improve feedback during cli sessions

Source: https://github.com/jepegit/cellpy/issues/891

Milestone: v.2.1.3

## Original issue text

Some of the stuff cellpy outputs when running CLI commands are not very well
thought through. Both with respect to content and visual impression. Let's make
it better.

## Session framing (agreed with the maintainer)

The issue text is deliberately open. The scope settled at the start of the
session:

- **Visual treatment:** restrained — colour plus a symbol column, width-aware
  rules, aligned key/value detail lines. No rich `Panel`s, no `Table`s for
  prose output.
- **Included:** global `--quiet` / `--verbose` / `--no-color`, and making the
  existing per-command `--silent` actually silence.
- **Deferred:** progress feedback for long `cellpy run` batch jobs (own issue).
