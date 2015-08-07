from keyedArrayType import KeyedArrayKeyError

class JsonObject(object):

    def __init__(self, json_struct=None):
        self.build_child_objects_list()
        if json_struct is not None:
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
        if type(json_struct) != dict:
            raise TypeError('', json_struct, 'object')
        # Run through the keys in the input structure
        for key in json_struct:
            # Check if there is an attribute in this object that has the name of the key
            if key in self._child_objects:
                if hasattr(getattr(self, key), 'load_json'):
                    try:
                        getattr(self, key).load_json(json_struct[key])
                    except KeyError as inst:
                        raise KeyError(key + '/' + inst.args[0])
                    except ValueError as inst:
                        raise ValueError(key + '/' + inst.args[0], inst.args[1], inst.args[2])
                    except TypeError as inst:
                        raise TypeError(key + '/' + inst.args[0], inst.args[1], inst.args[2])
                    except KeyedArrayKeyError as inst:
                        raise KeyedArrayKeyError(key + '/' + inst.args[0], inst.args[1], inst.args[2])
                else:
                    # basic type
                    if type(json_struct[key]) == type(getattr(self, key)):
                        setattr(self, key, json_struct[key])
                    else:
                        raise TypeError(key, json_struct[key], str(type(getattr(self, key)))[7:-2])
            else:
                raise KeyError(key)
