from collections import OrderedDict
from arrayType import ArrayTypeError

class KeyedArrayKeyError(Exception):
    pass

class KeyedArrayType(OrderedDict):

    def __init__(self, klass, key):
        super(KeyedArrayType, self).__init__()
        self.klass = klass
        self.key = key

    def delete_all(self):
        self.clear()

    def append_new(self, json_struct):
        if hasattr(self.klass, 'load_json'):
            # object
            if type(json_struct) != dict:
                raise ArrayTypeError(json_struct, 'object')
        elif hasattr(self.klass, 'set'):
            # enum
            if type(json_struct) not in [str, int]:
                raise ArrayTypeError(json_struct, 'enum (integer or string)')
        else:
            # basic type
            if type(json_struct) != self.klass:
                raise ArrayTypeError(json_struct, str(self.klass)[7:-2])
        # checks passed
        if self.key in json_struct:
            self[json_struct[self.key]] = self.klass(json_struct)
        else:
            raise KeyedArrayKeyError(json_struct, self.key)

    def serialize_json(self):
        ret = []
        for a in self.values():
            if hasattr(a, 'serialize_json'):
                ret.append(a.serialize_json())
            else:
                ret.append(a)
        return ret

    def __str__(self):
        return str(self.serialize_json())