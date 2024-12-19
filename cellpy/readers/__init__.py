from cellpy.libs.apipkg import initpkg

initpkg(
    __name__,
    {
        "externals": {
            "numpy": "numpy",
            "openpyxl": "openpyxl",
            "pandas": "pandas",
            "pint": "pint",
            # "pyodbc": "pyodbc",
            # "sqlalchemy": "sqlalchemy",
            # "tqdm": "tqdm",
            # "xlrd": "xlrd",
            "fabric": "fabric",
        },
    },
)
