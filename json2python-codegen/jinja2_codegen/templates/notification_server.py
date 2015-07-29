from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS
from autobahn.websocket.http import HttpException


class BaseService:

    def __init__(self, proto):
        self.proto = proto

    def onOpen(self):
        pass

    def onClose(self, wasClean, code, reason):
        pass

    def onMessage(self, payload, isBinary):
        pass

{% for class_name in class_list %}

class {{class_name}}(BaseService):

    def onMessage(self, payload, isBinary):
        pass

{% endfor %}

class ServiceServerProtocol(WebSocketServerProtocol):

    SERVICEMAP = { {{servicemap|join(', ')}} }

    def __init__(self):
        self.service = None

    def onConnect(self, request):
        if request.path in self.SERVICEMAP:
            cls = self.SERVICEMAP[request.path]
            self.service = cls(self)
        else:
            err = "No service under %s" % request.path
            print(err)
            raise HttpException(404, err)

    def onOpen(self):
        if self.service:
            self.service.onOpen()

    def onMessage(self, payload, isBinary):
        if self.service:
            self.service.onMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        if self.service:
            self.service.onClose(wasClean, code, reason)


class NotificationServerFactory():

    def __init__(self):
        factory = WebSocketServerFactory('ws://localhost:8181')
        factory.protocol = ServiceServerProtocol
        listenWS(factory)
        try:
            reactor.run()
        except KeyboardInterrupt:
            reactor.stop()
