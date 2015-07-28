class ArrayType(list):

    def __init__(self, klass):
        super(ArrayType, self).__init__()
        self.klass = klass

    def append_new(self, *args, **kwargs):
        self.append(self.klass(*args, **kwargs))

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