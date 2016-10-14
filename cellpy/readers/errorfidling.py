import collections
import pandas as pd

table = collections.OrderedDict()
table["first"] = 1.0
table["second"] = 2.0
table["none"] = None
table["true"] = True





table = {k: [x,] for k,x in table.items()}

for key, item in table.items():
    print key, item

print

# print table2
#
# for key, item in table2.items():
#     print key, item

print
print "creating pandas DataFrame"

df = pd.DataFrame(table)
print df
