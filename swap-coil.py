# -*- coding: utf8 -*-
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

try:
    client = ModbusTcpClient(sys.argv[1])
except IndexError:
    print 'Usage: swap-coil.py IP'
    sys.exit(1)

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
