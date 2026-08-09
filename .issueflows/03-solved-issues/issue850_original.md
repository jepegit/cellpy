# Issue #850: config: override() is process-global and not thread-safe (cross-talk in threaded apps)

Source: https://github.com/jepegit/cellpy/issues/850

## Original issue text

**cellpy version:** 2.1.2a2

## Summary

`cellpy.config.override()` reads as a scoped, reentrant context manager, but it mutates a module-level `_override_stack` and swaps the global `_session` via `reload()`. In a threaded application, one thread's "scoped" override is visible to every other thread, and the `finally: pop + reload` can land while another thread is still inside its own block.

## Reproduction

```python
import time
from concurrent.futures import ThreadPoolExecutor
from cellpy import config

def worker(mode):
    with config.override(reader={"cycle_mode": mode}):
        time.sleep(0.05)                       # let the two blocks interleave
        return mode, config.get_config().reader.cycle_mode

with ThreadPoolExecutor(max_workers=2) as ex:
    print(list(ex.map(worker, ["anode", "cathode"])))
```

Result:

```
[('anode', 'anode'), ('cathode', 'anode')]
```

The `cathode` worker observes `anode` **inside its own `override()` block**. Each worker should see the value it asked for.

## Why this bites app developers

Any GUI/service that runs cellpy work off the request thread hits this. In [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) loads/exports run in a `ThreadPoolExecutor`, so the natural pattern — "override `reader.cycle_mode` / `units` for *this* job" — is quietly racy: two concurrent jobs can silently compute with each other's settings, and the result is wrong numbers rather than an exception. That failure mode is much worse than a crash, because nothing signals it.

Our workaround is to resolve config on the main thread and pass concrete values into the job, and to treat `override()` as main-thread-only. That works, but it means the config stack can't be used for per-job policy at all.

## Suggested fix

Back the override stack (and ideally the session) with a **`contextvars.ContextVar`** rather than a module global:

- `ContextVar` isolation is per-thread *and* per-async-task, so it fixes threaded apps and any future async usage in one move.
- `copy_context()` semantics also make the intent ("scoped to this unit of work") actually true.
- Worth pairing with a note in the configuration docs about which parts of the stack are process-global (`reload`, `set_load_options`) versus scoped.

If a full `ContextVar` migration is too invasive for a patch release, an interim step would be documenting `override()` as process-global/not thread-safe and adding a `threading.RLock` around the stack mutation + reload, so at least the stack cannot be corrupted.

Happy to send a PR if you'd like the `ContextVar` version.
