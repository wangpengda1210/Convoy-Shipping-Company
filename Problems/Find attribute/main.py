from lxml import etree

root = etree.fromstring(input())
attr_name = input()

if attr_name in root.keys():
    print(root.get(attr_name))
else:
    print(None)
