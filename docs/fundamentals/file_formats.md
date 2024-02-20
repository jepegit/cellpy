# File formats
The `cellpy`-file format contains all the data contained in the Data object together with additional relevant metadata, including information about the file version.

As default, cellpy stores files in the HDF5 format. Simple methods for export to .csv
(`c.to_csv(out_folder)`) or excel (`c.to_excel(out_folder)`) are also available.