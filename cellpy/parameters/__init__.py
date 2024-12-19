from cellpy.libs.apipkg import initpkg

initpkg(
    __name__,
    {
        "externals": {
            "pandas": "pandas",
            "numpy": "numpy",
            "box": "box",
        },
    },
)
