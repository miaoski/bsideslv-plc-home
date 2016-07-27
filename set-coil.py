# -*- coding: utf8 -*-
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

try:
    client = ModbusTcpClient('192.168.42.3')
except IndexError:
    print 'Usage: set-coil.py CO 1|0'
    sys.exit(1)

client.write_coil(int(sys.argv[1]), int(sys.argv[2]))
client.close()
