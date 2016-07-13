# -*- coding: utf8 -*-
# MITM, client to modbus #1 and server of modbus #2, for level-2.
# Providing a bit fuzzing / procrastination
# It is based on "tick".  Think about turn-based game.

from time import sleep

SERVER = '192.168.42.1'
MYIP = '192.168.42.2'
TICK_TIME = 1       # 1 tick = 1 second
GMTICK = 0          # Greenwich mean tick :-)
NUMBER_DI = 4       # Number of DI

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


if __name__ == '__main__':
    D_STRUCTURE = [1, 0, 0, 1]
    S_STRUCTURE = [1, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    S_STRUCTURE = [1, 1, 0, 1]
    compare_action()
    tick()
    D_STRUCTURE = [0, 0, 0, 1]
    compare_action()
    tick()
    tick()
    tick()
    tick()
    tick()
    tick()
    tick()
    tick()
    tick()
    tick()
