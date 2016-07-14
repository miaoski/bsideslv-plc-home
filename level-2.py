# -*- coding: utf8 -*-
# Level-2 ModBus proxy
#   Logs when someone calls function 5, 15, 6, 16
#   Copies data from ModBus #1 every tick, but applies delays and fuzzy functions

from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from twisted.internet.task import LoopingCall
from pymodbus.client.sync import ModbusTcpClient
from time import sleep

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()
client = ModbusTcpClient('192.168.42.1')    # 192.168.42.1 is our ground truth

TICK_TIME = 1       # 1 tick = 1 second
GMTICK = 0          # Greenwich mean tick :-)
NUM_CO = 20         # Number of CO, since DI is read only.
NUM_HR = 10         # Number of HR, since IR is read only.
SLAVE_ID = 0x00

S_STRUCTURE = []    # readings in modbus #2
D_STRUCTURE = []    # ground truth in modbus #1
ACTIONS = []        # pile of actions to execute per tick

class Delayed:
    def __init__(self, pin, sv, dv, ticks):
        self.pin = pin
        self.sv = sv
        self.dv = dv
        self.ticks = ticks
    def __call__(self):
        global S_STRUCTURE
        if self.ticks == 0:
            print 'pin %d : %d => %d' % (self.pin, self.sv, self.dv)
            S_STRUCTURE[self.pin] = self.dv
            return None
        self.ticks -= 1
        return self
    def __repr__(self):
        return 'Delayed(pin %d: %d=>%d)' % (self.pin, self.sv, self.dv)

from random import randint
dft = lambda p, s, d: Delayed(p, s, d, 1)
slw = lambda p, s, d: Delayed(p, s, d, 3)
rnd = lambda p, s, d: Delayed(p, s, d, randint(1, 5))  # Max 5 ticks

# function pointers to call when a pin changes value
pin_change = [slw, dft, slw, rnd, dft, dft, dft, dft, dft, dft]


def dump_memory():
    print 'Tick   :', GMTICK
    print 'S / D  :', S_STRUCTURE, '\t', D_STRUCTURE
    print 'Actions:', ACTIONS


def compare_action():
    for i in range(len(D_STRUCTURE)):
        if S_STRUCTURE[i] != D_STRUCTURE[i]:
            ACTIONS.append(pin_change[i](i, S_STRUCTURE[i], D_STRUCTURE[i]))


def tick():
    global GMTICK, ACTIONS
    GMTICK += 1
    ACTIONS = filter(lambda x: x(), ACTIONS)
    dump_memory()


# Override ModbusSlaveContext to hook our function
class myModbusSlaveContext(ModbusSlaveContext):
    def setValues(self, fx, address, values):
        super(myModbusSlaveContext, self).setValues(fx, address, values)
        log.warn('Someone set values! %s, %s, %s', str(fx), str(address), str(values))


if __name__ == '__main__':
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
    StartTcpServer(context, identity=identity, address=('192.168.42.3', 502))
