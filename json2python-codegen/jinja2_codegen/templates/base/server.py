import web
import thread
from notification_factory import NotificationServerFactory
## EXAMPLE IMPORT SERVER MODELS
{% for import_object in import_list %}
import {{import_object.name}}
{% endfor %}

def launch_notification_server():
    return thread.start_new_thread(NotificationServerFactory,())

class MyApplication(web.application):
    def run(self, port={{port}}, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

##EXAMPLE import urls in the server
urls = {{urls_list|join(' + ')}}
app = MyApplication(urls, globals())

if __name__ == "__main__":
    nf = launch_notification_server()
    app.run({{port}})