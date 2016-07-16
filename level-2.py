# -*- coding: utf8 -*-
# Level-2 ModBus proxy
#   Logs when someone calls function 5, 15, 6, 16
#   Copies data from ModBus #1 every tick, but applies delays and fuzzy functions

from pymodbus.server.async import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from twisted.internet.task import LoopingCall
from pymodbus.client.sync import ModbusTcpClient
from identity import identity
from time import sleep

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger()
client = ModbusTcpClient('192.168.42.1')    # 192.168.42.1 is our ground truth

TICK_TIMER = 1      # 1 tick = 1 second
COMPARE_TIMER = 3   # Compare with ground truth every 3 seconds
COPY_TIMER = 0.1    # Copy DI and IR every 0.1s
GMTICK = 0          # Greenwich mean tick :-)
DI_NUM = 20+1       # Number of DI.  Read only and copied 
CO_NUM = 20+1       # Number of CO
IR_NUM = 5+1        # Number of IR, which is read only.
HR_NUM = 5+1        # Number of HR
SLAVE_ID = 0x00

ACTIONS = {}        # pile of actions to execute per tick
s_co = d_co = []    # For debugging
s_hr = d_hr = []    # For debugging
context = None      # global

def setvalue(fx, addr, value):
    global context
    fx_table = {1: 'c', 3: 'h'}
    if fx in fx_table:
        context[SLAVE_ID].store[fx_table[fx]].values[addr] = value
    else:
        logging.error('Unknown fx: %d', fx)


class Delayed(object):
    def __init__(self, fx, addr, sv, dv, ticks):
        self.addr = addr
        self.fx = fx
        self.sv = sv                    # surface or source, which you want :-)
        self.dv = dv                    # deep or destination, which you want :-)
        self.ticks = ticks
        if fx == 1:
            self.func = 'CO'
        elif fx == 3:
            self.func = 'HR'
        else:
            raise ValueError, 'Invalid function code'
    def __call__(self):
        if self.ticks == 0:
            logging.info('%s# %d : %d => %d', self.func, self.addr, self.sv, self.dv)
            setvalue(self.fx, self.addr+1, self.dv)
            return None
        else:
            self.ticks -= 1
        return self
    def __repr__(self):
        return 'Delayed(%s# %d: %d=>%d in %d ticks)' % (self.func, self.addr, self.sv, self.dv, self.ticks)


class Incremental(object):              # Limitation: integer only
    def __init__(self, inc, addr, sv, dv):
        self.addr = addr
        self.sv = sv
        self.dv = dv
        if sv >= dv and inc > 0:
            self.inc = int(-inc)
        else:
            self.inc = int(inc)
    def __call__(self):
        logging.info('HR# %d : %d => %d', self.addr, self.sv, self.sv + self.inc)
        self.sv += self.inc
        if self.inc >= 0 and self.sv >= self.dv:
            self.sv = self.dv
            setvalue(3, self.addr+1, self.sv)
            return None
        if self.inc < 0 and self.sv <= self.dv:
            self.sv = self.dv
            setvalue(3, self.addr+1, self.sv)
            return None
        setvalue(3, self.addr+1, self.sv)
        return self
    def __repr__(self):
        return 'Incremental(HR# %d: %d=>%d, %d per tick)' % (self.addr, self.sv, self.dv, self.inc)


class Scaled(Incremental):              # Limitation: integer only
    def __init__(self, pct, addr, sv, dv):
        print 'Scaled called: %f, %d, %d, %d' % (pct, addr, sv, dv)
        self.pct = pct
        inc = round((dv - sv) * pct)    # round to integer
        super(Scaled, self).__init__(inc, addr, sv, dv)
    def __repr__(self):
        return 'Scaled(HR# %d: %d=>%d, %d%% per tick)' % (self.addr, self.sv, self.dv, int(self.pct*100))


# function pointers to call when a pin changes value
from random import randint
co_dft = lambda a,s,d: Delayed(1, a, s, d, 1)
co_slw = lambda a,s,d: Delayed(1, a, s, d, 3)
co_rnd = lambda a,s,d: Delayed(1, a, s, d, randint(1, 5))  # Random delay, 1 - 5 ticks
hr_dft = lambda a,s,d: Delayed(3, a, s, d, 1)
hr_slw = lambda a,s,d: Delayed(3, a, s, d, 3)
hr_rnd = lambda a,s,d: Delayed(3, a, s, d, randint(1, 5))  # Random delay, 1 - 5 ticks
hr_pct = lambda x: lambda a,s,d: Scaled(x, a, s, d)
hr_inc = lambda x: lambda a,s,d: Incremental(x, a, s, d)
co_change = [co_slw, co_dft, co_slw, co_rnd, co_dft, co_dft, co_dft, co_dft, co_rnd, co_dft, co_slw]
hr_change = [hr_dft, hr_dft, hr_slw, hr_rnd, hr_pct(0.2), hr_inc(3)]


def dump_memory():
    print 'Tick   :', GMTICK
    print 'S_CO   :', [1 if x else 0 for x in s_co]
    print 'D_CO   :', [1 if x else 0 for x in d_co]
    print 'S_HR   :', s_hr
    print 'D_HR   :', d_hr
    print 'Actions:', ACTIONS


def copy_source(a):
    context = a[0]
    try:
        rr = client.read_discrete_inputs(0, DI_NUM)
        context[SLAVE_ID].store['d'] = ModbusSequentialDataBlock(0, [False,] + rr.bits[:DI_NUM])
        log.debug('DI: %s', str([1 if x else 0 for x in context[SLAVE_ID].store['d'].values]))
    except:
        log.warn('Cannot read DI')
    try:
        rr = client.read_input_registers(0, IR_NUM)
        context[SLAVE_ID].store['i'] = ModbusSequentialDataBlock(0, [0,] + rr.registers[:IR_NUM])
        log.debug('IR: %s', str(context[SLAVE_ID].store['i'].values))
    except:
        log.warn('Cannot read IR')
    log.debug('Copied DI and IR from modbus server #1')


def compare_source(a):
    global s_co, s_hr, d_co, d_hr
    context = a[0]
    try:
        d_co = [False,] + client.read_coils(0, CO_NUM).bits[:CO_NUM]
    except:
        log.warn('Cannot read CO')
    try:
        d_hr = [0,] + client.read_holding_registers(0, HR_NUM).registers[:HR_NUM]
    except:
        log.warn('Cannot read HR')
    log.info('Comparing CO and HR to modbus server #1')
    s_co = context[SLAVE_ID].store['c'].values
    s_hr = context[SLAVE_ID].store['h'].values
    for i in range(1, CO_NUM + 1):
        act = 'c%d' % i
        if s_co[i] != d_co[i] and act not in ACTIONS:
            ACTIONS[act] = co_change[i-1](i-1, s_co[i], d_co[i])
    for i in range(1, HR_NUM + 1):
        act = 'i%d' % i
        if s_hr[i] != d_hr[i] and act not in ACTIONS:
            ACTIONS[act] = hr_change[i-1](i-1, s_hr[i], d_hr[i])


def tick():
    global ACTIONS, GMTICK
    ACTIONS = {k:v() for k,v in ACTIONS.iteritems() if v}
    GMTICK += 1
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

    # Copy CO and HR for only once
    rr = client.read_coils(0, CO_NUM)
    context[SLAVE_ID].store['c'] = ModbusSequentialDataBlock(0, [False,] + rr.bits[:CO_NUM])
    print 'CO:', [1 if x else 0 for x in context[SLAVE_ID].store['c'].values]
    rr = client.read_holding_registers(0, HR_NUM)
    context[SLAVE_ID].store['h'] = ModbusSequentialDataBlock(0, [0,] + rr.registers[:HR_NUM])
    print 'HR:', context[SLAVE_ID].store['h'].values

    # Start loop
    loop = LoopingCall(f=copy_source, a=(context,))
    loop.start(COMPARE_TIMER, now=True)
    loop = LoopingCall(f=compare_source, a=(context,))
    loop.start(COMPARE_TIMER, now=True)
    loop = LoopingCall(f=tick)
    loop.start(TICK_TIMER, now=False)
    StartTcpServer(context, identity=identity(), address=('192.168.42.3', 502))
