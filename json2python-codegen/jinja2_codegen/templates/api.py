import web
import json
{% if auth %}
import base64
import re
{% endif %}

# BACKEND FUNCTIONS
{% for import_object in functions_import_list -%}
from {{import_object.file}} import {{import_object.name}}
{% endfor %}

# CALLABLE OBJECTS
{% for import_object in objects_import_list -%}
from {{import_object.file}} import {{import_object.name}}
{% endfor %}

urls = (
{% for url_object in url_object_list -%}
    "{{url_object.path}}" , "{{url_object.callback}}" ,
{% endfor -%}
)

{% if auth %}
users = {{users}}
{% endif %}

def byteify(input):
    # Convert JSON unicode strings to python byte strings, recursively on a json_struct
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def json_loads(json_string):
    # Try to use json.loads and raise HTTP Error
    try:
        json_struct = json.loads(json_string) #json parser.
    except ValueError:
        raise BadRequestError("Malformed JSON")
    else:
        return byteify(json_struct)

def json_dumps(js):
    # Pretty-print version of json.dumps
    return json.dumps(js, sort_keys=True, indent=4, separators=(',', ': '))

def create_instance(klass, json_struct, id=None):
    # Try to create an object instance and raise HTTP Errors
    try:
        new_object = klass(json_struct) # Creates an object instance of type klass from the json_struct data
    except KeyError as inst:
        raise BadRequestError("Unknown entity name in JSON:" + "<br>" + inst.args[0])
    except TypeError as inst:
        key = inst.args[0]
        value = json.dumps(inst.args[1])
        raise BadRequestError("Incorrect type in JSON:" + "<br>" +
                              key + " was:" + "<br>" +
                              value + "<br>" +
                              "Allowed type:" + "<br>" +
                              inst.args[2])
    except ValueError as inst:
        if type(inst.args[1]) == str:
            raise BadRequestError("Incorrect value in JSON:" + "<br>" +
                                  "Enum " + inst.args[0] + " was:" + "<br>" +
                                  inst.args[1] + "<br>" +
                                  "Allowed values:" + "<br>" +
                                  "[" + ", ".join(inst.args[2]) + "]")
        elif type(inst.args[1]) == int:
            raise BadRequestError("Incorrect value in JSON:" + "<br>" +
                                  "Enum " + inst.args[0] + " was:" + "<br>" +
                                  str(inst.args[1]) + "<br>" +
                                  "Allowed range:" + "<br>" +
                                  "1 - " + str(inst.args[2]))
    else:
        # Check if the id given in the URL matches the id given in the body
        if id != None and id[0] != getattr(new_object, id[1]):
            raise BadRequestError(id[1] + " in body not matching " + id[1] + " in URL")
        else:
            return new_object

class NotFoundError(web.HTTPError):
    def __init__(self,message):
        status = '404 '+message
        headers = {'Content-Type': 'text/html'}
        data = '<h1>'+message+'</h1>'
        web.HTTPError.__init__(self, status, headers, data)

class BadRequestError(web.HTTPError):
    def __init__(self,message):
        status = '400 '+message
        headers = {'Content-Type': 'text/html'}
        data = '<h1>'+message+'</h1>'
        web.HTTPError.__init__(self, status, headers, data)

class Successful(web.HTTPError):
    def __init__(self,message,info=''):
        status = '200 '+message
        headers = {'Content-Type': 'application/json'}
        data = info
        web.HTTPError.__init__(self, status, headers, data)

{% if auth %}
class basicauth:

    @classmethod
    def check(self,auth):
        if auth is not None:
            auth2 = re.sub("^Basic ","", auth)
            user,pswd = base64.decodestring(auth2).split(':')
            if user in users.keys() and pswd == users[user]:
                return True
            else:
                return False
        else:
            return False
{% endif %}

{% for callback in callback_list %}

#{{callback.path}}
class {{callback.name}}:
    {% if callback.methods.put %}

    def PUT({{callback.arguments|join(', ')}}):
        {% if auth %}
        if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return 'Unauthorized'
        {% endif %}
        print "{{callback.methods.put.printstr}}"
        {% if cors %}
        web.header('Access-Control-Allow-Origin','{{url}}')
        {% endif %}
        json_string = web.data()
        json_struct = json_loads(json_string)
        {% if callback.methods.put.check_id %}
        new_object = create_instance({{callback.methods.put.new_object}}, json_struct, ({{callback.arguments|last()}},'{{callback.arguments|last()}}'))
        {% else %}
        new_object=create_instance({{callback.methods.put.new_object}}, json_struct)
        {% endif %}
        {{callback.name}}Impl.put({{callback.impl_arguments|join(', ')}}, new_object)
        js=new_object.serialize_json()
        raise Successful("Successful operation",json_dumps(js))
    {% endif %}
    {% if callback.methods.post %}

    def POST({{callback.arguments|join(', ')}}):
        {% if auth %}
        if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return 'Unauthorized'
        {% endif %}
        print "{{callback.methods.post.printstr}}"
        {% if cors %}
        web.header('Access-Control-Allow-Origin','{{url}}')
        {% endif %}
        json_string=web.data()
        json_struct=json_loads(json_string)
        {% if callback.methods.post.check_id %}
        new_object=create_instance({{callback.methods.post.new_object}}, json_struct, ({{callback.arguments|last()}},'{{callback.arguments|last()}}'))
        {% else %}
        new_object=create_instance({{callback.methods.post.new_object}}, json_struct)
        {% endif %}
        {{callback.name}}Impl.post({{callback.impl_arguments|join(', ')}}, new_object)
        js=new_object.serialize_json()
        raise Successful("Successful operation",json_dumps(js))
    {% endif %}
    {% if callback.methods.delete %}

    def DELETE({{callback.arguments|join(', ')}}):
        {% if auth %}
        if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return 'Unauthorized'
        {% endif %}
        print "{{callback.methods.delete.printstr}}"
        {% if cors %}
        web.header('Access-Control-Allow-Origin','{{url}}')
        {% endif %}
        response={{callback.name}}Impl.delete({{callback.impl_arguments|join(', ')}})
        if response:
            raise Successful('Successful operation')
        else:
            raise NotFoundError("{{callback.thing}} not found")
    {% endif %}
    {% if callback.methods.get %}

    def GET({{callback.arguments|join(', ')}}):
        {% if auth %}
        if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return 'Unauthorized'
        {% endif %}
        print "{{callback.methods['get']['printstr']}}"
        {% if cors %}
        web.header('Access-Control-Allow-Origin','{{url}}')
        {% endif %}
        response = {{callback.name}}Impl.get({{callback.impl_arguments|join(', ')}})
        if response is not None:
            js = response.serialize_json()
            raise Successful("Successful operation",json_dumps(js))
        else:
            raise NotFoundError("{{callback.thing}} not found")
    {% endif %}
    {% if cors %}

    def OPTIONS({{callback.arguments|join(', ')}}):
        web.header('Access-Control-Allow-Origin','{{url}}')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise Successful('Successful operation','{"description":"Options called CORS"}')
    {% endif %}

{% endfor %}