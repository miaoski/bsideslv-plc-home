# -*- coding: utf8 -*-
# This trivial HMI is decoupled from ModBus server

import gevent
import random
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

client = None   # ModBus client

def read_di(num = 20):
    rr = client.read_discrete_inputs(1, num)
    rr = rr.bits[:num]
    di = ['0', ] + ['1' if x else '0' for x in rr]    # No GPIO 1 on RPi
    return di


def read_co(num = 20):
    rr = client.read_coils(1, num)
    rr = rr.bits[:num]
    di = ['0', ] + ['1' if x else '0' for x in rr]
    return di


def read_hr(num = 10):
    rr = client.read_holding_registers(1, num)
    rr = rr.registers[:num]
    di = map(str, rr)
    return di


class wsApp(WebSocketApplication):
    def on_open(self):
        while True:
            try:
                di = read_di()
                co = read_co()
                hr = read_hr()
            except:
                print 'Exception.  Wait for next run.'
                gevent.sleep(1)
                continue
            self.ws.send('\n'.join((','.join(di), ','.join(co), ','.join(hr))))
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
