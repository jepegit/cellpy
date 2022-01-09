# How to make a cellpy template

1. Replace NAME in the folder name (e.g. change from cellpy_cookie_NAME to cellpy_cookie_my_great_template).
2. Edit the notebook in the folder, and add more if you want.
3. Create a zip file of the folder (the name of the zip-file should be the same as the folder name, e.g. cellpy_cookie_my_great_template.zip)
4. Copy/move the zip file to the cellpy Templates folder.


# Things to know

1. The `cellpy new` cli command uses 'cookiecutter' for generating the folders and the files from the templates.
2. Variables/parameters you want from the user is defined in the `cookiecutter.json` file.
3. You can then use these variables/parameters inside your notebooks by surrounding them with double squirly brackets and pre-pending with `cookiecutter`. For example, if the variable `project_name` is defined in the `cookiecutter.json` file, you can use this inside the notebook(s) by writing `{{cookiecutter.project_name}}.