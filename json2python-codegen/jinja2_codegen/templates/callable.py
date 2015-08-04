import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))
from backend import {{toplevel}}

class {{class_name}}Impl:
    {% if methods.put %}

    @classmethod
    def put(cls, {{methods['put'].arguments|join(', ')}}):
        {% if methods.put.printstr %}
        print str({{methods.put.printstr}})
        {% endif %}
        print 'handling put'
        cls.post({{methods['put'].arguments|join(', ')}})
    {% endif %}
    {% if methods.post %}

    @classmethod
    def post(cls, {{methods.post.arguments|join(', ')}}):
        {% if methods.post.printstr %}
        print str({{methods.post.printstr}})
        {% endif %}
        print 'handling post'
        {% if methods['post'].arguments | length > 2 %}
        if {{methods['post'].arguments[0]}} in {{methods['post'].object_path[0]}}:
            {% if methods['post'].arguments | length > 3 %}
            if {{methods['post'].arguments[1]}} in {{methods['post'].object_path[1]}}:
                {{methods['post'].object_path[2]}}[{{methods['post'].arguments[2]}}]{{methods['post'].ending}} = {{methods['post'].arguments[3]}}
            else:
                raise KeyError('{{methods['post'].arguments[1]}}')
            {% else %}
            {{methods['post'].object_path[1]}}[{{methods['post'].arguments[1]}}]{{methods['post'].ending}} = {{methods['post'].arguments[2]}}
            {% endif %}
        else:
            raise KeyError('{{methods['post'].arguments[0]}}')
        {% else %}
        {{methods['post'].object_path[0]}}[{{methods['post'].arguments[0]}}]{{methods['post'].ending}} = {{methods['post'].arguments[1]}}
        {% endif %}
    {% endif %}
    {% if methods.delete %}

    @classmethod
    def delete(cls, {{methods.delete.arguments|join(', ')}}):
        {% if methods.delete.printstr %}
        print str({{methods.delete.printstr}})
        {% endif %}
        print 'handling delete'
        if {{methods['delete'].arguments[0]}} in {{methods['delete'].object_path[0]}}:
            {% if methods['delete'].arguments | length > 1 %}
            if {{methods['delete'].arguments[1]}} in {{methods['delete'].object_path[1]}}:
                {% if methods['delete'].arguments | length > 2 %}
                if {{methods['delete'].arguments[2]}} in {{methods['delete'].object_path[2]}}:
                    del({{methods['delete'].object_path[2]}}[{{methods['delete'].arguments[2]}}]{{methods['delete'].ending}})
                else:
                    raise KeyError('{{methods['get'].arguments[2]}}')
                {% else %}
                del({{methods['delete'].object_path[1]}}[{{methods['delete'].arguments[1]}}]{{methods['delete'].ending}})
                {% endif %}
            else:
                raise KeyError('{{methods['get'].arguments[1]}}')
            {% else %}
            del({{methods['delete'].object_path[0]}}[{{methods['delete'].arguments[0]}}]{{methods['delete'].ending}})
            {% endif %}
        else:
            raise KeyError('{{methods['delete'].arguments[0]}}')
    {% endif %}
    {% if methods['get'] %}

    @classmethod
    def get(cls, {{methods['get'].arguments|join(', ')}}):
        {% if methods['get'].printstr %}
        print str({{methods['get'].printstr}})
        {% endif %}
        print 'handling get'
        {% if methods['get'].arguments | length > 0 %}
        if {{methods['get'].arguments[0]}} in {{methods['get'].object_path[0]}}:
            {% if methods['get'].arguments | length > 1 %}
            if {{methods['get'].arguments[1]}} in {{methods['get'].object_path[1]}}:
                {% if methods['get'].arguments | length > 2 %}
                if {{methods['get'].arguments[2]}} in {{methods['get'].object_path[2]}}:
                    return {{methods['get'].object_path[2]}}[{{methods['get'].arguments[2]}}]{{methods['get'].ending}}
                else:
                    raise KeyError('{{methods['get'].arguments[2]}}')
                {% else %}
                return {{methods['get'].object_path[1]}}[{{methods['get'].arguments[1]}}]{{methods['get'].ending}}
                {% endif %}
            else:
                raise KeyError('{{methods['get'].arguments[1]}}')
            {% else %}
            return {{methods['get'].object_path[0]}}[{{methods['get'].arguments[0]}}]{{methods['get'].ending}}
            {% endif %}
        else:
            raise KeyError('{{methods['get'].arguments[0]}}')
        {% else %}
        return {{methods['get'].object_path[0]}}
        {% endif %}
        
    {% endif %}
