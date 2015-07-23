class JsonObject(object):

    def __init__(self, json_string=None):
        self.build_child_objects_list()
        self.load_json(json_string)

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

    def load_json(self, json_string):
        if json_string in [None, '']:
            return
        for key in self._child_objects:
            if key in json_string:
                if type(json_string[key]) is list:
                    for element in json_string[key]:
                        if type(element) is dict:
                            # Instantiate new object of the class
                            # Initialize from json
                            # Append to the list
                            getattr(self, key).append_new(json_string=element)
                        else:
                            getattr(self, key).append(element)
                elif type(json_string[key]) is dict:
                    getattr(self, key).load_json(json_string[key])
                else:
                    setattr(self, key, json_string[key])