"""Internal helpers (paths, lazy optional deps)."""

# Kept for historical import compatibility; Fabric is no longer a dependency.
from cellpy.libs.apipkg import initpkg

initpkg(
    __name__,
    {
        "externals": {},
    },
)
