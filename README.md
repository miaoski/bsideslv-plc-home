README
======
This honeypot implementation serves as part of my talk in [BSidesLV 2016] (https://www.bsideslv.org/2016agenda/), PLC for Home Automation and How It Is as Hackable as a Honeypot.  The scripts work with Raspberry Pi 2 Model B, such that GPIO 2 = address 0x02, and so forth.

* slave_id = 0
* coils map to GPO 2 .. 26
* discrete inputs map to GPI 2 .. 26

`test-client.py` is an example that sets GPO by ModBus write_coil.


Architecture
============
* modsrv.py :: Reads GPIO and saves the status to discrete inputs.  Sets GPIO according to coils.  Bind it to 192.168.42.1
* mitm.py :: Client to 192.168.42.1, this is the man in the middle and a ModBus server.  Bind it to 192.168.42.2.
* hmi.py :: Reads discrete inputs from ModBus and use web socket to update it on the browser.  It's not coupled with ModBus IP and could display multiple buses.


LICENSE
=======
GPLv2.
