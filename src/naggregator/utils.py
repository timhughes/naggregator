import base64
import re


def auth_header(username, password):
    value = 'Basic ' + base64.b64encode("%s:%s" % (username, password)).strip()
    return {'Authorization': [value], }


def slugify(value):
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    return re.sub('[-\s]+', '-', value)
