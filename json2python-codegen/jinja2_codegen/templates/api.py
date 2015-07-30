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
    # Convert JSON unicode strings to python byte strings
    if isinstance(input, dict):
        return {byteify(key):byteify(value) for key,value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def json_loads(input):
    return byteify(json.loads(input))

def create_instance(klass, json_struct):
    try:
        new_object=klass(json_struct) #It creates an object instance from the json_struct data.
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
    {% for method in callback.method_list %}
    
    def {% filter upper %}{{method.name}}{% endfilter %}({{callback.arguments|join(', ')}}):
        {% if auth %}
        if not basicauth.check(web.ctx.env.get("HTTP_AUTHORIZATION")):
            web.header('WWW-Authenticate','Basic realm="Auth example"')
            web.ctx.status = '401 Unauthorized'
            return 'Unauthorized'
        {% endif %}
        print "{{method.printstr}}"
        {% if cors %}
        web.header('Access-Control-Allow-Origin','{{url}}')
        {% endif %}
        {% if method.web_data_body %}
        json_string=web.data() #data in body
            {% if method.json_parser %}
        json_struct=json_loads(json_string) #json parser.
        input={{method.new_object}}(json_struct) #It creates an object instance from the json_struct data."
                {% if method.response %}
        response={{callback.name}}Impl.{{method.name}}({{method.impl_arguments}}, input)
                {% else %}
        response={{callback.name}}Impl.{{method.name}}(input)
                {% endif %}
            {% else %}
            {% endif %}
        {% else %}
        response={{callback.name}}Impl.{{method.name}}({{method.impl_arguments}})
        {% endif %}
        {% for resp in method.responses %}
            {% if resp.jotason %}
        #js={} #Uncomment to create json response
            {% endif %}
        #{{resp.handleResp}} #Uncomment to handle responses
        {% endfor %}
        raise Successful('Successful operation','{"description":"{{method.printstr}}"}')
    {% endfor %}
    {% if cors %}

    def OPTIONS({{callback.arguments|join(', ')}}):
        web.header('Access-Control-Allow-Origin','{{url}}')
        web.header('Access-Control-Allow-Headers','Origin, X-Requested-With, Content-Type, Accept, Authorization')
        raise Successful('Successful operation','{"description":"Options called CORS"}')
    {% endif %}

{% endfor %}