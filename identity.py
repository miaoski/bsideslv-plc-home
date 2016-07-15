# -*- coding: utf8 -*-
# Config file for identity

from pymodbus.device import ModbusDeviceIdentification

def identity():
    x = ModbusDeviceIdentification()
    x.VendorName  = 'pymodbus'
    x.VendorUrl   = 'http://github.com/miaoski/bsideslv-plc-home'
    x.ProductCode = 'HA'
    x.ProductName = 'Home Automation'
    x.ModelName   = 'PLC'
    x.MajorMinorRevision = '1.0'
    return x
