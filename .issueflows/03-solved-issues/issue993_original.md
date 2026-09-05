# Issue #993: Docstring cross-references lost their module paths in #968, making them unresolvable

Source: https://github.com/jepegit/cellpy/issues/993

## Original issue text

#968 replaced Sphinx roles in library docstrings with markdown code spans, which fixed the raw `:class:`/`:meth:` markers leaking into the Zensical API pages (#967). But the replacement dropped the **module path** in about half the cases, and the module path was the only thing that made those pointers resolvable.

```diff
- """Gets the capacity for the run. See :func:`cellpy.readers.capacity_curves.get_cap`."""
+ """Gets the capacity for the run. See `get_cap`."""
```

The rewrite was not consistent about this. Across #968:

| | count |
|---|---|
| references that kept a dotted path (`` `cellpy.ica.IcaOptions` ``) | 16 |
| references reduced to a bare name (`` `get_cap` ``) | 24 |

So the good spelling is already in the tree — it just was not applied everywhere.

## Why the bare form costs something real

For the thinnest wrappers, the delegate's docstring *is* the documentation. Measured on 2.1.3.post2:

| call | arguments | documented on the method | documented on the delegate |
|---|---|---|---|
| `CellpyCell.get_cap` | 23 | 0 | 22 of 24 |
| `CellpyCell.to_csv` | 9 | 0 | 9 |
| `CellpyCell.to_excel` | 7 | 0 | 7 |

`get_cap`'s entire docstring is one sentence and a pointer. With `` `cellpy.readers.capacity_curves.get_cap` `` anything can follow it — an IDE, a docs generator, `help()`, a tool. With `` `get_cap` `` nothing can, because the name is ambiguous: it also names the method whose docstring you are already reading.

The rendered Zensical page is fine either way — a reader clicks through or searches. What breaks is every *other* consumer, and those are the ones that reach people who never open the docs site.

Concretely: [cellpy-mcp](https://github.com/cellpy/cellpy-mcp)'s `describe_api` follows these pointers, which on 2.1.3 took argument coverage across the documented API from 51% to 72% with no docstrings rewritten. On 2.1.3.post2 the three calls above stopped resolving — 38 arguments' worth. It now works around this by resolving bare names through an index of module-level functions, which is a heuristic where a dotted path was a fact.

## What would fix it

Keep the markdown code span; put the dotted path back inside it.

```diff
- """Gets the capacity for the run. See `get_cap`."""
+ """Gets the capacity for the run. See `cellpy.readers.capacity_curves.get_cap`."""
```

This does not reintroduce #967: `tests/test_no_sphinx_doc_roles.py` bans the `:role:` prefix, not dotted names, and the 16 references above already pass it in this form.

## Acceptance criteria

- Every cross-reference of the form ``See `name` `` in `cellpy/` that points at another callable names it by its importable dotted path.
- `tests/test_no_sphinx_doc_roles.py` still passes (no roles reintroduced).
- A companion test asserting the property directly: for each such reference in `cellpy/`, the dotted path imports and resolves. That is what stops the next docs pass from quietly undoing it — #967's fix was correct and this regression rode along with it precisely because nothing checked the *targets*, only the syntax.
- `CellpyCell.get_cap`, `to_csv` and `to_excel` resolve to their delegates, since those are the three that carry the most undocumented arguments.

Where a bare name has no single obvious target, leaving it alone and noting it is better than guessing — a wrong path is worse than none.

Found while building the MCP server discussed in #840.
