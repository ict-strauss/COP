class ImportObject(object):

    def __init__(self, file, name):
        self.file = file
        self.name = name

class AttributeObject(object):

    def __init__(self, name, value):
        self.name=name
        self.value=value

class EnumObject(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.range_end = str(len(values)+1)

class MethodObject(object):

    def __init__(self, name, arguments, printstr):
        self.name = name
        self.arguments = arguments
        self.printstr = printstr
