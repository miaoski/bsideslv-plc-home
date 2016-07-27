# -*- coding: utf8 -*-
from pymodbus.client.sync import ModbusTcpClient
from time import sleep
import sys

try:
    client = ModbusTcpClient('192.168.42.3')
except IndexError:
    print 'Usage: set-waterlevel.py level'
    sys.exit(1)

client.write_register(4, int(sys.argv[1]))
