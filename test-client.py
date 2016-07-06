# -*- coding: utf8 -*-
from pymodbus.client.sync import ModbusTcpClient
from time import sleep

client = ModbusTcpClient('192.168.42.1')
v = True
try:
    while True:
        raw_input('Enter to swap...')
        v = not v
        client.write_coil(8, v)
        client.write_coil(10, not v)
        print 'Set coil 8 =', v, ' coil 10 =', (not v)
except KeyboardInterrupt:
    client.close()
