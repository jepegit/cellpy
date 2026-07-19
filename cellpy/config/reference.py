"""Generate the configuration reference from the models (config plan Step 7).

Every setting cellpy has, with its type, default and section, rendered straight
from the pydantic models — so the documentation cannot drift from the code.
A test asserts that regenerating produces no diff; if you add a field, run:

```shell
uv run python -m cellpy.config.reference
```

Secrets are listed but never valued: the ``[secrets]`` section is env-only and
its members are documented by the environment variable that supplies them
(config plan decision 5).
"""

from __future__ import annotations

from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel

from cellpy.config.credentials import ENV_VARS
from cellpy.config.models import CellpyConfig

DOC_PATH = Path("docs") / "getting_started" / "configuration_reference.md"

_HEADER = """# Configuration reference

Auto-generated from the configuration models. Do not edit by hand — regenerate with:

```shell
uv run python -m cellpy.config.reference
```

Settings are resolved in layers, later winning over earlier: **defaults → user
`cellpy.toml` → project `cellpy.toml` → environment / `.env` → runtime
overrides**. Ask where a value came from with `cellpy.config.sources()`.

Environment variables use the pattern `CELLPY_<SECTION>__<FIELD>` (two
underscores between section and field), e.g. `CELLPY_READER__AUTO_DIRS=0`.
"""

_SECRETS_NOTE = """
## secrets

Credentials are read from the **environment only** — never from a config file.
A `[secrets]` section in a `cellpy.toml` is an error, not a silent override, so
that a credential you thought was configured cannot quietly fail to be.

| Setting | Environment variable | Notes |
| --- | --- | --- |
"""


def _type_name(annotation: Any) -> str:
    name = getattr(annotation, "__name__", None)
    if name and name not in {"Union", "Optional"}:
        return name
    # Unions and Optionals: the bare __name__ ("Union") says nothing useful.
    return str(annotation).replace("typing.", "").replace("NoneType", "None")


def _placeholders() -> list[tuple[str, str]]:
    """Machine-specific prefixes and the tokens that stand in for them.

    Several path defaults are computed from the current directory or the user's
    home. Rendering them literally would put the generating machine's directory
    layout (and user name) into published documentation, and would make the
    no-diff check fail for everyone else.

    The prefixes are read from the model's *own* defaults rather than from a
    live ``Path.cwd()`` / ``Path.home()``: those defaults are evaluated when
    ``models.py`` is imported, so a later ``chdir`` (pytest does this) would
    make a live lookup miss and leak the real path into the file.
    """
    paths = CellpyConfig.model_fields["paths"].annotation.model_fields
    cwd_at_import = str(paths["outdatadir"].default)
    home_at_import = str(Path(str(paths["env_file"].default)).parent)
    return [
        (cwd_at_import, "<current directory>"),
        (home_at_import, "<home>"),
    ]


def _is_path_like(value: Any) -> bool:
    # OtherPath is not a PurePath subclass, so go by protocol as well.
    return isinstance(value, PurePath) or hasattr(value, "raw_path")


def _format_default(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, str) and not value:
        return '`""`'
    text = str(value)
    # Longest prefix first, so a home inside cwd (or vice versa) resolves to
    # the more specific token.
    for actual, token in sorted(_placeholders(), key=lambda p: -len(p[0])):
        if text.startswith(actual):
            text = token + text[len(actual) :]
            break
    if _is_path_like(value):
        # Normalise separators: otherwise the file generated on Windows differs
        # from the one generated on Linux and the no-diff check can never hold
        # on both. Only for path values — `localhost\SQLEXPRESS` is a literal
        # backslash that must survive.
        text = text.replace("\\", "/")
    return f"`{text}`"


def _render_section(name: str, model: type[BaseModel]) -> list[str]:
    lines = [
        f"## {name}",
        "",
        (model.__doc__ or "").strip().splitlines()[0] if model.__doc__ else "",
        "",
        "| Setting | Type | Default |",
        "| --- | --- | --- |",
    ]
    for field_name, field in model.model_fields.items():
        default = field.get_default(call_default_factory=True)
        if isinstance(default, BaseModel):
            # Nested model: its own fields are documented in their own section.
            default = None
        lines.append(
            f"| `{field_name}` | `{_type_name(field.annotation)}` | "
            f"{_format_default(default)} |"
        )
    lines.append("")
    return lines


def render_reference_md() -> str:
    """Render the whole configuration reference as markdown."""
    lines = _HEADER.splitlines()

    for section_name, field in CellpyConfig.model_fields.items():
        model = field.annotation
        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            continue
        if section_name == "secrets":
            continue  # rendered separately, without defaults
        lines.append("")
        lines.extend(_render_section(section_name, model))

    lines.extend(_SECRETS_NOTE.splitlines())
    for field_name in CellpyConfig.model_fields["secrets"].annotation.model_fields:
        env = ENV_VARS.get(field_name, "—")
        note = (
            "never echoed in reprs, dumps or logs"
            if field_name == "password"
            else "not secret material; grouped here because it arrives with them"
        )
        lines.append(f"| `{field_name}` | `{env}` | {note} |")
    lines.append("")
    return "\n".join(lines)


def write_reference_md(path: str | Path) -> None:
    """Write the rendered reference to *path*."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_reference_md(), encoding="utf-8")


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[2] / DOC_PATH
    write_reference_md(target)
    print(f"wrote {target}")
