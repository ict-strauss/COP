import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))


class {{class_name}}Impl:

    {% for method in method_list %}
    @classmethod
    def {{method.name}}(cls, {{method.arguments|join(', ')}}):
        {% if method.printstr %}
        print str({{method.printstr}})
        {% endif %}
        print 'handling {{method.name}}'
        
    {% endfor %}