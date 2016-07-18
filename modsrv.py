# -*- coding: utf8 -*-
# Based on https://github.com/bashwork/pymodbus/blob/master/examples/common/updating-server.py

import RPi.GPIO as GPIO
from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from twisted.internet.task import LoopingCall
from identity import identity

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()

# For GPIO http://www.raspberrypi-spy.co.uk/wp-content/uploads/2012/06/Raspberry-Pi-GPIO-Layout-Model-B-Plus-rotated-2700x900.png
# GPI = Discrete input
# GPO = Coil
#   1  2  3  4  5  6  7  8  9 10    0 = Don't set, 1 = GPI (low), 2 = GPI (high), 3 = GPO (low), 4 = GPO (high)
GPIO_TABLE = [ 0,
    0, 1, 2, 2, 2, 2, 2, 3, 3, 4,   # +  0
    2, 2, 2, 0, 0, 2, 2, 2, 2, 2,   # + 10, 14 = TX, 15 = RX
    2, 2, 2, 2, 2, 2, ]             # + 20
COIL = 1
DISCRETE_INPUTS = 2
HOLDING_REGISTERS = 3
INPUT_REGISTERS = 4
SLAVE_ID = 0x00
OLD_GPIO = [0] * len(GPIO_TABLE)
GPO_SHIFT = 3
HEART_BEAT = 1

def dump_store(a):
    context  = a[0]
    address  = 0x00
    print "DI values:", context[SLAVE_ID].store['d'].values[:20]
    print "CO values:", context[SLAVE_ID].store['c'].values[:20]
    print "HR values:", context[SLAVE_ID].store['h'].values[:10]
    print "IR values:", context[SLAVE_ID].store['i'].values[:10]


def scan_gpi():
    for i in range(len(OLD_GPIO)):
        if GPIO_TABLE[i] == 1 or GPIO_TABLE[i] == 2:
            v = GPIO.input(i)
            if v != OLD_GPIO[i]:
                log.info('GPI %d : %d => %d', i, OLD_GPIO[i], v)
                context[SLAVE_ID].setValues(DISCRETE_INPUTS, i, [v, ])
                OLD_GPIO[i] = v


def set_gpo(pin, v):
    if GPIO_TABLE[pin] == 3 or GPIO_TABLE[pin] == 4:
        log.info('Set GPO %d : %d', pin, v)
        GPIO.output(pin, v)
        GPIO_TABLE[pin] = v + GPO_SHIFT


def heart_beat(a):
    "Send heart beat via CO#9"
    global HEART_BEAT
    context = a[0]
    HEART_BEAT = abs(HEART_BEAT - 1)
    context[SLAVE_ID].setValues(COIL, 9, [HEART_BEAT, ])


# Override ModbusSlaveContext to hook our function
class myModbusSlaveContext(ModbusSlaveContext):
    def setValues(self, fx, address, values):
        super(myModbusSlaveContext, self).setValues(fx, address, values)
        if self.decode(fx) == 'c':
            for i in range(len(values)):
                set_gpo(address + i, values[i])
        if self.decode(fx) == 'h':
            log.warn('HR %s => %s', str(address), str(values))


# Set GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for i in range(len(GPIO_TABLE)):
    v = GPIO_TABLE[i]
    if v == 0:
        continue
    elif v == 1:
        GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        OLD_GPIO[i] = 0
    elif v == 2: 
        GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        OLD_GPIO[i] = 1
    elif v == 3:
        GPIO.setup(i, GPIO.OUT, initial=GPIO.LOW)
        OLD_GPIO[i] = GPO_SHIFT
    elif v == 4:
        GPIO.setup(i, GPIO.OUT, initial=GPIO.HIGH)
        OLD_GPIO[i] = GPO_SHIFT + 1
    else:
        raise ValueError, "Invalid GPIO setup, pin %d" % i

# Initialize ModBus Context
store = myModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*100),
    co = ModbusSequentialDataBlock(0, [0]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100))
context = ModbusServerContext(slaves=store, single=True)
context[0].setValues(DISCRETE_INPUTS, 0, [(1 if x == 1 else 0) for x in OLD_GPIO])
for i in range(len(GPIO_TABLE)):
    if GPIO_TABLE[i] == 3:
        context[0].setValues(COIL, i, [0,]);
    elif GPIO_TABLE[i] == 4:
        context[0].setValues(COIL, i, [1,]);


# Start loop
loop = LoopingCall(f=dump_store, a=(context,))
loop.start(10, now=True)
loop_scan_gpi = LoopingCall(f=scan_gpi)
loop_scan_gpi.start(0.1, now=True)
loop_heart_beat = LoopingCall(f=heart_beat, a=(context,))
loop_heart_beat.start(1, now=True)
StartTcpServer(context, identity=identity(), address=('192.168.42.1', 502))
