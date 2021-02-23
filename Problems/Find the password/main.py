from lxml import etree


def find_password(xml_string):
    root = etree.fromstring(xml_string)

    if "password" in root.keys():
        return root.get("password")
    elif len(root.getchildren()) == 0:
        return None
    else:
        password_list = []
        for child in root.getchildren():
            child_str = str(etree.tostring(child), encoding='utf-8')
            if not child_str.startswith('<!--'):
                password_list.append(find_password(str(etree.tostring(child),
                                                       encoding='utf-8')))
        for password in password_list:
            if password is not None:
                return password
