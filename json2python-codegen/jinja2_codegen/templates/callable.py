import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))
from backend import {{toplevel}}

class {{class_name}}Impl:
    {% if methods['PUT'] %}

    @classmethod
    def put(cls, {{methods['PUT'].arguments|join(', ')}}):
        {% if methods['PUT'].printstr %}
        print str({{methods['PUT'].printstr}})
        {% endif %}
        print 'handling put'
        cls.post({{methods['PUT'].arguments|join(', ')}})
    {% endif %}
    {% if methods['POST'] %}

    @classmethod
    def post(cls, {{methods['POST'].arguments|join(', ')}}):
        {% if methods['POST'].printstr %}
        print str({{methods['POST'].printstr}})
        {% endif %}
        print 'handling post'
        {% if methods['POST'].arguments | length > 2 %}
        if {{methods['POST'].arguments[0]}} in {{object_path[0]}}:
            {% if methods['POST'].arguments | length > 3 %}
            if {{methods['POST'].arguments[1]}} in {{object_path[1]}}:
                {{object_path[2]}}[{{methods['POST'].arguments[2]}}]{{ending}} = {{methods['POST'].arguments[3]}}
            else:
                raise KeyError('{{methods['POST'].arguments[1]}}')
            {% else %}
            {{object_path[1]}}[{{methods['POST'].arguments[1]}}]{{ending}} = {{methods['POST'].arguments[2]}}
            {% endif %}
        else:
            raise KeyError('{{methods['POST'].arguments[0]}}')
        {% else %}
        {{object_path[0]}}[{{methods['POST'].arguments[0]}}]{{ending}} = {{methods['POST'].arguments[1]}}
        {% endif %}
    {% endif %}
    {% if methods['DELETE'] %}

    @classmethod
    def delete(cls, {{methods['DELETE'].arguments|join(', ')}}):
        {% if methods['DELETE'].printstr %}
        print str({{methods['DELETE'].printstr}})
        {% endif %}
        print 'handling delete'
        if {{methods['DELETE'].arguments[0]}} in {{object_path[0]}}:
            {% if methods['DELETE'].arguments | length > 1 %}
            if {{methods['DELETE'].arguments[1]}} in {{object_path[1]}}:
                {% if methods['DELETE'].arguments | length > 2 %}
                if {{methods['DELETE'].arguments[2]}} in {{object_path[2]}}:
                    del({{object_path[2]}}[{{methods['DELETE'].arguments[2]}}]{{ending}})
                else:
                    raise KeyError('{{methods['DELETE'].arguments[2]}}')
                {% else %}
                del({{object_path[1]}}[{{methods['DELETE'].arguments[1]}}]{{ending}})
                {% endif %}
            else:
                raise KeyError('{{methods['DELETE'].arguments[1]}}')
            {% else %}
            del({{object_path[0]}}[{{methods['DELETE'].arguments[0]}}]{{ending}})
            {% endif %}
        else:
            raise KeyError('{{methods['DELETE'].arguments[0]}}')
    {% endif %}
    {% if methods['GET'] %}

    @classmethod
    def get(cls, {{methods['GET'].arguments|join(', ')}}):
        {% if methods['GET'].printstr %}
        print str({{methods['GET'].printstr}})
        {% endif %}
        print 'handling get'
        {% if methods['GET'].arguments | length > 0 %}
        if {{methods['GET'].arguments[0]}} in {{object_path[0]}}:
            {% if methods['GET'].arguments | length > 1 %}
            if {{methods['GET'].arguments[1]}} in {{object_path[1]}}:
                {% if methods['GET'].arguments | length > 2 %}
                if {{methods['GET'].arguments[2]}} in {{object_path[2]}}:
                    return {{object_path[2]}}[{{methods['GET'].arguments[2]}}]{{ending}}
                else:
                    raise KeyError('{{methods['GET'].arguments[2]}}')
                {% else %}
                return {{object_path[1]}}[{{methods['GET'].arguments[1]}}]{{ending}}
                {% endif %}
            else:
                raise KeyError('{{methods['GET'].arguments[1]}}')
            {% else %}
            return {{object_path[0]}}[{{methods['GET'].arguments[0]}}]{{ending}}
            {% endif %}
        else:
            raise KeyError('{{methods['GET'].arguments[0]}}')
        {% else %}
        return {{object_path[0]}}
        {% endif %}
        
    {% endif %}
