class EnumType(object):
    # Internal data storage uses integer running from 0 to range_end
    # range_end is set to the number of possible values that the Enum can take on
    # External representation of Enum starts at 1 and goes to range_end + 1

    def __init__(self, initial_value):
        self.set(initial_value)

    def serialize_json(self):
        # Returns a string
        # This could be changed to encode enums as integers when transmitting messages
        return type(self).possible_values[self.value]

    def __str__(self):
        return str(self.serialize_json())

    def get(self):
        # Returns an integer, using the external representation
        return self.value + 1

    def set(self, value):
        # The value to set can be either a string or an integer
        if type(value) is str:
            # This will raise ValueError for wrong assignments
            self.value = type(self).possible_values.index(value)
        elif type(value) is int:
            if value >= 1 and value <= type(self).range_end:
                # External representation of Enum starts at 1, internal at 0
                value = value - 1
                self.value = value
            else:
                raise ValueError
        else:
            raise TypeError
