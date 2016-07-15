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
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()
client = ModbusTcpClient('192.168.42.1')    # 192.168.42.1 is our ground truth

TIME_TO_COPY = 10               # Copy from truth every 10 seconds

SLAVE_ID = 0x00
DI_NUM = 20+1
CO_NUM = 20+1
HR_NUM = 5+1
IR_NUM = 5+1

def copy_modbus_source(a):      # Notice that addr=0 is always skipped
    context = a[0]
    try:
        rr = client.read_discrete_inputs(0, DI_NUM)
        context[SLAVE_ID].store['d'] = ModbusSequentialDataBlock(0, [False,] + rr.bits[:DI_NUM])
        print [1 if x else 0 for x in context[SLAVE_ID].store['d'].values]
    except:
        log.warn('Cannot read DI')
    try:
        rr = client.read_coils(0, CO_NUM)
        context[SLAVE_ID].store['c'] = ModbusSequentialDataBlock(0, [False,] + rr.bits[:CO_NUM])
        print [1 if x else 0 for x in context[SLAVE_ID].store['c'].values]
    except:
        log.warn('Cannot read CO')
    try:
        rr = client.read_holding_registers(0, HR_NUM)
        context[SLAVE_ID].store['h'] = ModbusSequentialDataBlock(0, [0,] + rr.registers[:HR_NUM])
        print context[SLAVE_ID].store['h'].values
    except:
        log.warn('Cannot read HR')
    try:
        rr = client.read_input_registers(0, IR_NUM)
        context[SLAVE_ID].store['i'] = ModbusSequentialDataBlock(0, [0,] + rr.registers[:IR_NUM])
        print context[SLAVE_ID].store['i'].values
    except:
        log.warn('Cannot read IR')
    log.info('Copied from modbus server #1')


# Override ModbusSlaveContext to hook our function
class myModbusSlaveContext(ModbusSlaveContext):
    def setValues(self, fx, address, values):
        super(myModbusSlaveContext, self).setValues(fx, address, values)
        log.warn('Someone set values! %s, %s, %s', str(fx), str(address), str(values))


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
loop = LoopingCall(f=copy_modbus_source, a=(context,))
loop.start(TIME_TO_COPY, now=True)
StartTcpServer(context, identity=identity, address=('192.168.42.2', 502))
