class ImportObject(object):

    def __init__(self, file, name):
        self.file = file
        self.name = name


class AttributeObject(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value


class EnumObject(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.range_end = str(len(values))


class MethodObject(object):

    def __init__(self, name, arguments, printstr):
        self.name = name
        self.arguments = arguments
        self.printstr = printstr


class UrlObject(object):

    def __init__(self, path, callback):
        self.path = path
        self.callback = callback


class CallbackObject(object):

    def __init__(self, name, path, methods, arguments, thing):
        self.name = name
        self.path = path
        self.methods = methods
        self.arguments = arguments
        self.thing = thing


class ResponseObject(object):
    
    def __init__(self, jotason, handleResp):
        self.jotason = jotason
        self.handleResp = handleResp
