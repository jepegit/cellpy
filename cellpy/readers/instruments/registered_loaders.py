"""All internal instrument loaders must be registered here. Remark! there should be only one loader pr. python file.
"""

instruments = {
    "arbin_res": "DataLoader",
    "arbin_sql": "DataLoader",
    "arbin_sql_csv": "DataLoader",
    "arbin_sql_xlsx": "DataLoader",
    "pec_csv": "DataLoader",
    "biologics_mpr": "DataLoader",
    "maccor_txt": "DataLoader",
    "custom": "DataLoader",
    "old_custom": "DataLoader",
    "local_instrument": "DataLoader",
}
