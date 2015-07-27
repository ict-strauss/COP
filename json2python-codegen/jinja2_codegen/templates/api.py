import web
import json
{% if auth -%}
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
        
{% for callback in callback_list %}

#{{callback.path}}
class {{callback.name}}:
    {% for method in callback.method_list %}
    
    def {{method.name}}(self, {{method.arguments|join(', ')}}):
        print "{{method.printstr}}"
        {% if method.web_data_body %}
        data=web.data() #data in body
            {% if method.json_parser %}
        input_json=json.loads(data) #json parser.
        input={{method.new_object}}(input_json) #It creates an object instance from the json_input data."
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
        #raise Successful('Successful operation','{"description":"{{method.printstr}}"}')
    {% endfor %}
{% endfor %}