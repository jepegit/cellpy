from cellpy.libs.apipkg import initpkg

initpkg(
    __name__,
    {
        "externals": {
            "numpy": "numpy",
            "openpyxl": "openpyxl",
            "pandas": "pandas",
            "pint": "pint",
        },
        # "core": {
        #     "Data": "cellpy.readers.core:Data",
        #     "BaseDbReader": "cellpy.readers.core:BaseDbReader",
        #     "FileID": "cellpy.readers.core:FileID",
        #     "Q": "cellpy.readers.core:Q",
        #     "convert_from_simple_unit_label_to_string_unit_label": "cellpy.readers.core:convert_from_simple_unit_label_to_string_unit_label",
        #     "generate_default_factory": "cellpy.readers.core:generate_default_factory",
        #     "identify_last_data_point": "cellpy.readers.core:identify_last_data_point",
        #     "instrument_configurations": "cellpy.readers.core:instrument_configurations",
        #     "interpolate_y_on_x": "cellpy.readers.core:interpolate_y_on_x",
        #     "pickle_protocol": "cellpy.readers.core:pickle_protocol",
        #     "xldate_as_datetime": "cellpy.readers.core:xldate_as_datetime",
        # },
        # "internals": {
        #     "OtherPath": "cellpy.internals.core:OtherPath",
        # },
    },
)
