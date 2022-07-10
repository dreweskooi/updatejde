__author__ = 'dkooi'
from logging import exception
import re
import xml.sax.handler
import json

str = str
unicode = str
bytes = bytes
basestring = (str,bytes)
skip_attrs = ['xmlns','lastchangetime','lastusermodifiedtime','createtime','endtime']

def xml2obj(src,objname):
    """
    A simple function to converts XML data into native Python object.
    """

    non_id_char = re.compile('[^_0-9a-zA-Z]')

    def _name_mangle(name):
        return non_id_char.sub('_', name)

    class DataNode(object):
        def __init__(self):
            self._attrs = {}  # XML attributes and child elements
#            self.data = None  # child text data

        def __len__(self):
            # treat single element as a list of 1
            return 1

        def __getitem__(self, key):
            if isinstance(key, basestring):
                return self._attrs.get(key, None)
            else:
                return [self][key]

        def __setitem__(self, key, item):
                self._attrs[key] = item

        def __contains__(self, name):
            return self._attrs.has_key(name)

        def __nonzero__(self):
            return bool(self._attrs or self.data)

        def __getattr__(self, name):
            #if name.startswith('__'):
            #    return None
                # need to do this for Python special methods???
                #raise AttributeError(name)
            return self._attrs.get(name, '')

        def _add_xml_attr(self, name, value):
            if name in self._attrs:
                # multiple attribute of the same name are represented by a list
                children = self._attrs[name]
                if not isinstance(children, list):
                    children = [children]
                    self._attrs[name] = children
                children.append(value)
            else:
                self._attrs[name] = value

        def __str__(self):
            return self.data or ''

        def __repr__(self):
            items = sorted(self._attrs.items())
            if self.data:
                items.append(('data', self.data))
            return u'{%s}' % ', '.join([u'%s:%s' % (k, repr(v)) for k, v in items])

        def __eq__(self, other):
                if (isinstance(other, DataNode)):
                    ret = True
                    for attribute in sorted(self._attrs):
                        if self._attrs.get(attribute,'') == other._attrs.get(attribute,''):
                           pass
                        else:
                            ret = False
                    return ret
                return False

        def toString(self, level=0):
            retval = " " * level
            for attribute in sorted(self._attrs):
                if not  attribute  in skip_attrs:
                    if self._attrs[attribute] != None and self._attrs[attribute] !='':
                        retval += " %s=\"%s\"" % (attribute, self._attrs[attribute])
            c = ""
            if self.children != None:
                for child in self.children:
                    c += child.toString(level + 1)
            if c == "":
                pass
            else:
                retval += ">\n" + c + ("&lt;/%s>\n" % self.name)
            return retval.strip()

        def toJSON(self, skip_cols = []):
            attrs_list = set()
            attrs_list =self._attrs.copy()
            for attribute in attrs_list:
                if attribute  in skip_attrs + skip_cols:
                    self._attrs.pop(attribute)
            jsond = json.dumps(self._attrs, default=lambda o: o.__dict__, sort_keys=True)
            #jsond = json.dumps(self._attrs, default=filter(lambda x: x[0] =='id',  x.__dict__), sort_keys=True, indent=4)
            return jsond
    class TreeBuilder(xml.sax.handler.ContentHandler):
        def __init__(self):
            self.stack = []
            self.root = DataNode()
            self.current = self.root
            self.text_parts = []

        def startElement(self, name, attrs):
            self.stack.append((self.current, self.text_parts))
            self.current = DataNode()
            self.text_parts = []
            # xml attributes --> python attributes
            for k, v in attrs.items():
                self.current._add_xml_attr(_name_mangle(k), v)

        def endElement(self, name):
            text = ''.join(self.text_parts).strip()
            if text:
                self.current.data = text
            if self.current._attrs:
                obj = self.current
            else:
                # a text only node is simply represented by the string
                obj = text or ''
            self.current, self.text_parts = self.stack.pop()
            self.current._add_xml_attr(_name_mangle(name), obj)

        def characters(self, content):
            self.text_parts.append(content)

    builder = TreeBuilder()
    if isinstance(src, basestring):
        xml.sax.parseString(src, builder)
    else:
        xml.sax.parse(src, builder)
    if objname.lower() in builder.root._attrs:
        return builder.root._attrs[str(objname.lower())]
    else:
        return builder.root._attrs[str(objname)]
