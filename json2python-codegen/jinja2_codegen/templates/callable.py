import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))


class {{class_name}}Impl:

    {% for method in method_list -%}
    @classmethod
    def {{method.name}}(cls, {% for argument in method.arguments %}{{argument}}{% if not loop.last %}, {% endif %}{% endfor %}):
        {% if method.printstr -%}
        print str({{method.printstr}})
        {% endif -%}
        print 'handling {{method.name}}'
        
    {% endfor %}