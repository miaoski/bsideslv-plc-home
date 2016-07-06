README
======
This honeypot implementation serves as part of my talk in [BSidesLV 2016] (https://www.bsideslv.org/2016agenda/), PLC for Home Automation and How It Is as Hackable as a Honeypot.  The scripts work with Raspberry Pi 2 Model B, such that GPIO 2 = address 0x02, and so forth.

* slave_id = 0
* coils map to GPO 2 .. 26
* discrete inputs map to GPI 2 .. 26

`test-client.py` is an example that sets GPO by ModBus write_coil.

LICENSE
=======
GPLv2.
