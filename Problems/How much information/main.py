from lxml import etree

root = etree.fromstring(input())
print(len(root.getchildren()), len(root.keys()))
