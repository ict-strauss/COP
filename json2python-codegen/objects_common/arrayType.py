class ArrayTypeError(Exception):
    pass

class ArrayType(list):

    def __init__(self, klass):
        super(ArrayType, self).__init__()
        self.klass = klass

    def delete_all(self):
        del self[:]

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
        self.append(self.klass(json_struct))

    def serialize_json(self):
        ret = []
        for a in self:
            if hasattr(a, 'serialize_json'):
                ret.append(a.serialize_json())
            else:
                ret.append(a)
        return ret

    def __str__(self):
        return str(self.serialize_json())