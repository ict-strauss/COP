import json
import random
import threading
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory

poolThreads = range(1,100)
web_sockets = dict()

class MyClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

        def hello():
            self.sendMessage(u"Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            self.factory.reactor.callLater(1, hello)

        # start sending messages every second ..
        hello()

    def onMessage(self, payload, isBinary):
        print 'On message'
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(json.loads(payload.decode('utf8'))))

    def onClose(self, wasClean, code, reason):
        print code
        print("WebSocket connection closed: {0}".format(reason))


class WSClientFactory(threading.Thread):
    def __init__(self, threadID, uri):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.uri = uri

    def start(self):
        print self.uri
        address = self.uri[7:].split('/')[0]
        path =  self.uri[7:].split('/')[1:]

        ip = address.split(':')[0]
        port = address.split(':')[1]

        factory = WebSocketClientFactory('ws://'+str(self.uri[7:]), debug=True)
        factory.protocol = MyClientProtocol
        factory.setProtocolOptions(openHandshakeTimeout=15)
        reactor.connectTCP(ip, int(port), factory)



def addClient(uri):
    threadId = getValidThread()
    web_sockets[threadId] = WSClientFactory(threadId, uri)
    web_sockets[threadId].start()
    print threadId

def getValidThread():
    valid = False

    while not valid:
        threadId = random.randint(1,100)
        if threadId in poolThreads:
            valid=True
            del poolThreads[poolThreads.index(threadId)]

    return threadId



if __name__ == '__main__':
    addClient('http://localhost:8181/restconf/streams/updateCallService')
    addClient('http://localhost:8181/restconf/streams/removeCallService')
    try:
        reactor.run()
    except KeyboardInterrupt:
        print "Keyboard interrupt"
        reactor.stop()
