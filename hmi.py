# -*- coding: utf8 -*-
import gevent
import random
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource

def read_di():
    di = [random.randint(0, 1) for _ in range(18)]
    return di


def read_re():
    di = [random.random()*100 for _ in range(2)]
    return di


class wsApp(WebSocketApplication):
    def on_open(self):
        while True:
            di = map(str, read_di())
            re = map(str, read_re())
            self.ws.send(','.join(di + re))
            gevent.sleep(3)

    def on_close(self, reason):
        print "Connection Closed!!!", reason


def static_wsgi_app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return open("hmi.html").readlines()


resource = Resource([
    ('/', static_wsgi_app),
    ('/data', wsApp)
])

if __name__ == "__main__":
    server = WebSocketServer(('', 8000), resource, debug=True)
    server.serve_forever()
