from collections import OrderedDict

class KeyedArrayKeyError(Exception):
    pass

class KeyedArrayType(OrderedDict):

    def __init__(self, klass, key):
        super(KeyedArrayType, self).__init__()
        self.klass = klass
        self.key = key

    def load_json(self, json_struct):
        if type(json_struct) is list:
            self.clear()
            for element in json_struct:
                if self.key in element:
                    self[element[self.key]] = self.klass(element)
                else:
                    raise KeyedArrayKeyError('', element, self.key)
        else:
            raise TypeError('', json_struct, 'list')

    def json_serializer(self):
        return [a.json_serializer() for a in self.values()]

    def __str__(self):
        return str(self.json_serializer())
