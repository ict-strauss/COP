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
                # Execute different actions depending on the type of the key,
                # always check if the type of the key matches the type of the attribute
                if type(json_struct[key]) is list:
                    # array
                    #if type(getattr(self, key)) is ArrayType:
                    if hasattr(getattr(self, key), 'append_new'):
                        for element in json_struct[key]:
                            # Instantiate new object of the class
                            # Initialize from json
                            # Append to the list
                            getattr(self, key).append_new(json_struct=element)
                    else:
                        raise TypeError
                elif type(json_struct[key]) is dict:
                    # object
                    if type(getattr(self, key)) == JsonObject:
                        getattr(self, key).load_json(json_struct[key])
                    else:
                        raise TypeError
                #elif type(getattr(self, key)) is EnumType:
                elif hasattr(getattr(self, key), 'set'):
                    # enum
                    getattr(self, key).set(json_struct[key])
                else:
                    # basic type
                    if type(json_struct[key]) == type(getattr(self, key)):
                        setattr(self, key, json_struct[key])
                    else:
                        raise TypeError
            else:
                raise KeyError
