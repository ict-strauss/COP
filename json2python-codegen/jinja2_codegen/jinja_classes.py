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
        self.range_end = str(len(values)+1)


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

    def __init__(self, name, path, method_list):
        self.path = path
        self.name = name
        self.method_list = method_list

class CallbackMethodObject(object):
    
    def __init__(self, name, arguments, printstr, web_data_body, json_parser, new_object, response,
                 impl_arguments, response_list):
        self.name = name
        self.arguments = arguments
        self.printstr = printstr
        self.web_data_body = web_data_body
        self.json_parser = json_parser
        self.new_object = new_object
        self.response = response
        self.impl_arguments = impl_arguments
        self.responses = response_list

class ResponseObject(object):
    
    def __init__(self, jotason, handleResp):
        self.jotason = jotason
        self.handleResp = handleResp
