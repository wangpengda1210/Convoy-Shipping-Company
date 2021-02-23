from lxml import etree

root = etree.fromstring(input())
for elem in root:
    print(elem.text)
