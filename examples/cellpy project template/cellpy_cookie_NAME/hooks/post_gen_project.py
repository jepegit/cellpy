import os
print("created:")

startpath = os.getcwd()
for root, dirs, files in os.walk(startpath):
    level = root.replace(startpath, '').count(os.sep)
    indent = ' ' * 4 * (level)
    print('{}{}/'.format(indent, os.path.basename(root)))
    subindent = ' ' * 4 * (level + 1)
    for f in files:
        if not f.startswith("."):
         print('{}{}'.format(subindent, f))