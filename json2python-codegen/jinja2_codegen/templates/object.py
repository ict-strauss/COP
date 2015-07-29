{% for import_object in import_list %}
from {{import_object.file}} import {{import_object.name}}
{% endfor %}

class {{class_name}}({{superclass_name}}):

    def __init__(self, json_struct=None):
        {% for attribute_object in attribute_list %}
        self.{{attribute_object.name}}={{attribute_object.value}}
        {% endfor %}
        super({{class_name}}, self).__init__(json_struct)

{% for enum_object in enum_list %}
class {{enum_object.name}}:
    {{enum_object.values|join(', ')}} = range(1, {{enum_object.range_end}})
{% endfor %}
