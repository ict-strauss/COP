import web
## EXAMPLE IMPORT SERVER MODELS
{% for import_object in import_list -%}
import {{import_object.name}}
{% endfor %}

class MyApplication(web.application):
    def run(self, port={{port}}, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

##EXAMPLE import urls in the server
urls = {{urls_list|join(' + ')}}
app = MyApplication(urls, globals())

if __name__ == "__main__":
    app.run({{port}})