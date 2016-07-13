# -*- coding: utf8 -*-
# This trivial HMI is decoupled from ModBus server

import gevent
import random
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

client = None   # ModBus client

def read_di():
    num_di = 17
    rr = client.read_discrete_inputs(1, num_di)
    rr = rr.bits[:num_di]
    di = ['0', ] + ['1' if x else '0' for x in rr]    # No GPIO 1 on RPi
    return di


def read_re():
    di = ['%0.2f' % (random.random()*100) for _ in range(2)]
    return di


class wsApp(WebSocketApplication):
    def on_open(self):
        while True:
            di = read_di()
            re = read_re()
            self.ws.send(','.join(di + re))
            gevent.sleep(0.3)

    def on_close(self, reason):
        print "Connection Closed!!!", reason


def homepage(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    return open("hmi.html").readlines()


def icons(environ, start_response):
    if environ['PATH_INFO'] == '/turn-on.png':
        fn = 'turn-on.png'
    else:
        fn = 'turn-off.png'
    start_response("200 OK", [("Content-Type", "image/png")])
    return open(fn, 'rb').read()


resource = Resource([
    ('/data', wsApp),
    ('/.+.png$', icons),
    ('/', homepage),
])

if __name__ == "__main__":
    try:
        myip = sys.argv[1]
    except IndexError:
        print 'Usage python hmi.py 192.168.42.1'
        sys.exit(1)
    client = ModbusTcpClient(myip)
    server = WebSocketServer((myip, 8000), resource, debug=False)
    server.serve_forever()
