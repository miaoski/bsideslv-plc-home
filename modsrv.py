# Based on https://github.com/bashwork/pymodbus/blob/master/examples/common/updating-server.py

from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer

from twisted.internet.task import LoopingCall

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def updating_writer(a):
    log.debug("updating the context")
    context  = a[0]
    register = 3
    coil = 0
    slave_id = 0x00
    address  = 0x00
    values   = context[slave_id].getValues(coil, address, count=5)
    values   = [not v for v in values]
    log.debug("new values: " + str(values))
    context[slave_id].setValues(coil, address, values)

store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*100),
    co = ModbusSequentialDataBlock(0, [0]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)

identity = ModbusDeviceIdentification()
identity.VendorName  = 'pymodbus'
identity.ProductCode = 'PM'
identity.VendorUrl   = 'http://github.com/miaoski/'
identity.ProductName = 'pymodbus Server'
identity.ModelName   = 'pymodbus Server'
identity.MajorMinorRevision = '1.0'

time = 5 # 5 seconds delay
loop = LoopingCall(f=updating_writer, a=(context,))
loop.start(time, now=False) # initially delay by time
StartTcpServer(context, identity=identity, address=("localhost", 502))
