# -*- coding: utf8 -*-
# Based on https://github.com/bashwork/pymodbus/blob/master/examples/common/updating-server.py

import RPi.GPIO as GPIO
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

# For GPIO http://www.raspberrypi-spy.co.uk/wp-content/uploads/2012/06/Raspberry-Pi-GPIO-Layout-Model-B-Plus-rotated-2700x900.png
# GPI = Discrete input
# GPO = Coil
#   1  2  3  4  5  6  7  8  9 10    0 = Don't set, 1 = GPI (low), 2 = GPI (high), 3 = GPO (low), 4 = GPO (high)
GPIO_TABLE = [ 0,
    0, 2, 2, 2, 2, 2, 2, 2, 2, 2,   # +  0
    2, 2, 2, 0, 0, 2, 2, 2, 2, 2,   # + 10, 14 = TX, 15 = RX
    2, 2, 2, 2, 2, 2, ]             # + 20
COIL = 1
DISCRETE_INPUTS = 2
HOLDING_REGISTERS = 3
INPUT_REGISTERS = 4
SLAVE_ID = 0x00
OLD_GPIO = [0] * len(GPIO_TABLE)

def get_gpio(context):
    for i in range(1, len(GPIO_TABLE)):
        if GPIO_TABLE[i] == 1 or GPIO_TABLE[i] == 2:
            v = GPIO.input(i)
            if v != OLD_GPIO[i]:
                log.info('GPI %d : %d => %d', i, OLD_GPIO[i], v)
                context[SLAVE_ID].setValues(DISCRETE_INPUTS, i, [v, ])
                OLD_GPIO[i] = v

def set_gpio(context):
    for i in range(1, len(GPIO_TABLE)):
        if GPIO_TABLE[i] == 3 or GPIO_TABLE[i] == 4:
            v = context[SLAVE_ID].getValues(COIL, i, 1)
            if v != GPIO_TABLE[i] + 3:          # 3 = GPO (low)
                log.info('Set GPO %d : %d => %d', i, GPIO_TABLE[i], v)
                GPIO.output(i, v)
                GPIO_TABLE[i] = v + 3

def updating_writer(a):
    log.debug("updating the context")
    context  = a[0]
    address  = 0x00
    get_gpio(context)
    set_gpio(context)
    values   = context[SLAVE_ID].getValues(DISCRETE_INPUTS, 0, count=len(GPIO_TABLE))
    log.debug("DI values: " + str(values))
    values   = context[SLAVE_ID].getValues(COIL, 0, count=len(GPIO_TABLE))
    log.debug("Coil values: " + str(values))


# Set GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for i in range(len(GPIO_TABLE)):
    v = GPIO_TABLE[i]
    if v == 0:   continue
    elif v == 1: GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    elif v == 2: GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    elif v == 3: GPIO.setup(i, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
    elif v == 4: GPIO.setup(i, GPIO.OUT, pull_up_down=GPIO.PUD_UP)
    else:
        raise ValueError, "Invalid GPIO setup, pin %d" % i

# Initialize ModBus Context
store = ModbusSlaveContext(
    di = ModbusSequentialDataBlock(0, [0]*100),
    co = ModbusSequentialDataBlock(0, [0]*100),
    hr = ModbusSequentialDataBlock(0, [0]*100),
    ir = ModbusSequentialDataBlock(0, [0]*100))
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
time = 5
loop = LoopingCall(f=updating_writer, a=(context,))
loop.start(time, now=False) # initially delay by time
StartTcpServer(context, identity=identity, address=('0.0.0.0', 502))
