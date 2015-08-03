from arrayType import ArrayTypeError

class JsonObject(object):

    def __init__(self, json_struct=None):
        self.build_child_objects_list()
        self.load_json(json_struct)

    def build_child_objects_list(self):
        self._child_objects = [i for i in dir(self) if not i.startswith('_') and not callable(getattr(self, i))]

    def serialize_json(self):
        ret={}
        for item in self._child_objects:
            if hasattr(getattr(self, item), 'serialize_json'):
                ret[item]=getattr(self, item).serialize_json()
            else:
                ret[item]=getattr(self, item)
        return ret

    def __str__(self):
        return str(self.serialize_json())

    def load_json(self, json_struct):
        if json_struct == None:
            return
        # Run through the keys in the input structure
        for key in json_struct:
            # Check if there is an attribute in this object that has the name of the key
            if key in self._child_objects:
                # Execute different actions depending on the type of the attribute,
                # always check if the type of the key matches the type of the attribute
                #if type(getattr(self, key)) is ArrayType:
                if hasattr(getattr(self, key), 'append_new'):
                    # array
                    if type(json_struct[key]) is list:
                        # clear list
                        getattr(self, key).delete_all()
                        for element in json_struct[key]:
                            # Instantiate new object of the class
                            # Initialize from json
                            # Append to the list
                            try:
                                getattr(self, key).append_new(json_struct=element)
                            except ArrayTypeError as inst:
                                raise TypeError(key + '[...]', inst.args[0], inst.args[1])
                    else:
                        raise TypeError(key, json_struct[key], 'array')
                #if superclass type(getattr(self, key)) == JsonObject:
                elif hasattr(getattr(self, key), 'load_json'):
                    # object
                    if type(json_struct[key]) is dict:
                        getattr(self, key).load_json(json_struct[key])
                    else:
                        raise TypeError(key, json_struct[key], 'object')
                #elif type(getattr(self, key)) is EnumType:
                elif hasattr(getattr(self, key), 'set'):
                    # enum
                    if type(json_struct[key]) in [str, int]:
                        try:
                            getattr(self, key).set(json_struct[key])
                        except ValueError as inst:
                            raise ValueError(key, inst.args[0], inst.args[1])
                    else:
                        raise TypeError(key, json_struct[key], 'enum (integer or string)')
                else:
                    # basic type
                    if type(json_struct[key]) == type(getattr(self, key)):
                        setattr(self, key, json_struct[key])
                    else:
                        raise TypeError(key, json_struct[key], str(type(getattr(self, key)))[7:-2])
            else:
                raise KeyError(key)
