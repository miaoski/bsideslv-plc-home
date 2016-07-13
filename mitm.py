# -*- coding: utf8 -*-
# MITM, client to modbus #1 and server of modbus #2
# Providing a bit fuzzing / procrastination
# It is based on "tick".  Think about turn-based game.

from time import sleep

SERVER = '192.168.42.1'
MYIP = '192.168.42.2'
TICK_TIME = 1       # 1 tick = 1 second
CUR_TICK = 0        # Greenwich mean tick :-)
NUMBER_DI = 4       # Number of DI
MAX_PILES = 5       # t-5 = readings to output
                    # t-1 = waiting for ticks
                    # t   = the newest readings, compared with t-1

memory = []         # piles in tuple (reading when T=t, ticking)

def dft():
    return 1        # changes after 1 tick

def slw():
    return 3        # changes after 3 ticks

def rnd():
    "Random should not exceed MAX_PILES"
    from random import randint
    return randint(1, MAX_PILES-1)

# function pointers to call when a pin changes value
pin_change_p = [dft, dft, slw, rnd, dft, dft, dft, dft, dft, dft]


def pile_up(newvals):
    global memory
    if len(newvals) != NUMBER_DI:
        raise ValueError, "Piled readings should have %d items" % NUMBER_DI
    if len(memory) == 0:                # pile up new things
        for i in range(MAX_PILES):
            memory.append((newvals[:], [f() for f in pin_change_p]))
    else:
        memory.append((newvals[:], [f() for f in pin_change_p]))
    dump_memory()


def dump_memory():
    for i in range(len(memory)):
        print 'meomry %d:' % i, memory[i]


def emit_readings():
    global CUR_TICK, memory
    CUR_TICK += 1
    print 'Tick advanced to %d' % CUR_TICK,
    t = memory[0][1]
    emit = []
    for i in range(NUMBER_DI):
        emit.append(memory[t[i]][0][i])
    print emit
    memory = memory[-MAX_PILES:]        # remove the oldest


if __name__ == '__main__':
    v = 0
    while True:
        v = abs(v-1)
        pile_up([v, 0, 0, 1])
        emit_readings()
        sleep(1)
