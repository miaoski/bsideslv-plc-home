# -*- coding: utf8 -*-
# Run ipython -i dummy.py if you don't want to run it on Raspberry Pi

from pymodbus.server.async import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from identity import identity

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()


def dump_store(a):
    context  = a[0]
    address  = 0x00
    print "DI values:", context[0].store['d'].values[:20]
    print "CO values:", context[0].store['c'].values[:20]
    print "HR values:", context[0].store['h'].values[:10]
    print "IR values:", context[0].store['i'].values[:10]


# Initialize ModBus Context
store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0,0,0,1,1,1,1,1,1,0,1,0,1,1,1,0,0,1,1,1,1,1]),
    co = ModbusSequentialDataBlock(0, [0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0]),
    hr = ModbusSequentialDataBlock(0, [0,0,37,0,35,0,0] + [0] * 10),
    ir = ModbusSequentialDataBlock(0, [0,0,85,0,0,0,0] + [0] * 10))
context = ModbusServerContext(slaves=store, single=True)

# Start loop
def run(ip='192.168.42.1', port=502):
    StartTcpServer(context, identity=identity(), address=(ip, port))

print 'Type run() to StartTcpServer'
