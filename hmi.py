# -*- coding: utf8 -*-
# This trivial HMI is decoupled from ModBus server

import gevent
from flask import Flask, render_template
from flask_sockets import Sockets
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

app = Flask(__name__)
sockets = Sockets(app)

try:
    myip = sys.argv[1]
except IndexError:
    print 'Usage python hmi.py 192.168.42.1'
    sys.exit(1)
client = ModbusTcpClient(myip)

def read_di(num = 20):
    rr = client.read_discrete_inputs(1, num).bits[:num]
    di = ['0', ] + ['1' if x else '0' for x in rr]    # No GPIO 1 on RPi
    return di

def read_co(num = 20):
    rr = client.read_coils(1, num).bits[:num]
    di = ['0', ] + ['1' if x else '0' for x in rr]
    return di

def read_ir(num = 5):
    rr = client.read_input_registers(1, num).registers[:num]
    di = map(str, rr)
    return di

def read_hr(num = 5):
    rr = client.read_holding_registers(1, num).registers[:num]
    di = map(str, rr)
    return di


@sockets.route('/data')
def read_data(ws):
    while not ws.closed:
        try:
            di = read_di()
            co = read_co()
            ir = read_ir()
            hr = read_hr()
        except:
            print 'Exception.  Wait for next run.'
            gevent.sleep(1)
            continue
        ws.send('\n'.join((','.join(di), ','.join(co), ','.join(ir), ','.join(hr))))
        gevent.sleep(0.3)
    print "Connection Closed!!!", reason


@app.route('/')
def homepage():
    return render_template('hmi.html')


# main
if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer((myip, 8000), app, handler_class=WebSocketHandler)
    server.serve_forever()
