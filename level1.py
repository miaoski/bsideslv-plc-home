# -*- coding: utf8 -*-
# Level-1 ModBus proxy
#   Logs when someone calls function 5, 15, 6, 16
#   Copies data from ModBus #1 every s seconds

from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from twisted.internet.task import LoopingCall
from pymodbus.client.sync import ModbusTcpClient

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
client = ModbusTcpClient('192.168.42.1')    # 192.168.42.1 is our ground truth

COIL = 1
DISCRETE_INPUTS = 2
HOLDING_REGISTERS = 3
INPUT_REGISTERS = 4
SLAVE_ID = 0x00

DI_NUM = 100
CO_NUM = 100
HR_NUM = 100
IR_NUM = 100

def copy_modbus_source(a):
    context  = a[0]
    try:
        rr = client.read_discrete_inputs(0, DI_NUM - 1)
        context[SLAVE_ID].setValues(DISCRETE_INPUTS, 0, rr.bits)
    except:
        log.warn('Cannot read DI')
    try:
        rr = client.read_coils(0, CO_NUM - 1)
        context[SLAVE_ID].setValues(COIL, 0, rr.bits)
    except:
        log.warn('Cannot read CO')
    try:
        rr = client.read_holding_registers(0, HR_NUM - 1)
        context[SLAVE_ID].setValues(HOLDING_REGISTERS, 0, rr.registers)
    except:
        log.warn('Cannot read HR')
    try:
        rr = client.read_input_registers(0, IR_NUM - 1)
        context[SLAVE_ID].setValues(INPUT_REGISTERS, 0, rr.registers)
    except:
        log.warn('Cannot read HR')


# Override ModbusSlaveContext to hook our function
class myModbusSlaveContext(ModbusSlaveContext):
    def setValues(self, fx, address, values):
        super(myModbusSlaveContext, self).setValues(fx, address, values)
        log.warn('User set values: %s, %s, %s', str(fx), str(address), str(values))


# Initialize ModBus Context
store = myModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*DI_NUM),
    co = ModbusSequentialDataBlock(0, [0]*CO_NUM),
    hr = ModbusSequentialDataBlock(0, [0]*HR_NUM),
    ir = ModbusSequentialDataBlock(0, [0]*IR_NUM))
context = ModbusServerContext(slaves=store, single=True)

# Set identification
identity = ModbusDeviceIdentification()
identity.VendorName  = 'pymodbus'
identity.VendorUrl   = 'http://github.com/miaoski/bsideslv-plc-home'
identity.ProductCode = 'HA'
identity.ProductName = 'Home Automation'
identity.ModelName   = 'PLC'
identity.MajorMinorRevision = '1.0'

# Start loop
TIME_TO_COPY = 10
loop = LoopingCall(f=copy_modbus_source, a=(context,))
loop.start(TIME_TO_COPY, now=True)
StartTcpServer(context, identity=identity, address=('192.168.42.2', 502))
