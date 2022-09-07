"""All internal instrument loaders must be registered here. Remark! there should be only one loader pr. python file.
"""

instruments = {
    "arbin_res": "ArbinLoader",
    "arbin_sql": "ArbinSQLLoader",
    "arbin_sql_csv": "ArbinCsvLoader",
    "arbin_sql_xlsx": "ArbinXLSXLoader",
    "pec_csv": "PECLoader",
    "biologics_mpr": "MprLoader",
    "maccor_txt": "MaccorTxtLoader",
    "custom": "CustomTxtLoader",
    "old_custom": "CustomLoader",
    "local_instrument": "LocalTxtLoader",
}
