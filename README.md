README
======
This honeypot implementation serves as part of my talk in [BSidesLV 2016] (https://www.bsideslv.org/2016agenda/), PLC for Home Automation and How It Is as Hackable as a Honeypot.  The scripts work with Raspberry Pi 2 Model B, such that GPIO 2 = address 0x02, and so forth.

* slave\_id = 0
* coils map to GPO 2 .. 26
* discrete inputs map to GPI 2 .. 26

`swap-coil.py` is an example that sets GPO by ModBus `write_coil`.


Architecture
============
* modsrv.py :: Reads GPI and saves the status to discrete inputs.  Sets GPO according to coils.  Bound to 192.168.42.1 as ModBus #1, the ground truth.
* hmi.py :: Reads discrete inputs, coils, and holding registers from ModBus and uses websocket on browser.
* level-1.py :: Client to 192.168.42.1 (ModBus #1) and bound to 192.168.42.2 (ModBus #2).  You may want to expose it to the internet, so that people tweak the coils.  Everything is logged.  Actual values are copied from #1 to #2 every 10 seconds.
* level-2.py :: Level-2 proxy.  It's like level-1 proxy, but applies fuzzy functions and delays to changed values.



LICENSE
=======
GPLv2.
