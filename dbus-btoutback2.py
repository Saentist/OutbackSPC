#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from threading import Thread
from dbus.mainloop.glib import DBusGMainLoop

if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject

from outbackbt import OutbackBtDev, OutbackBt
from dbushelper import DbusHelper
from utils import *
import utils
from inverter import Inverter

logger = utils.setup_logger()  # Ensure logger is initialized

def get_btaddr() -> list:
    # Get the Bluetooth address from the argument
    if len(sys.argv) > 1:
        return sys.argv[1:]
    else:
        return [utils.OUTBACK_ADDRESS]

def setup_outback_connection(btaddr: list) -> Inverter:
    outbackBtDevConnection = OutbackBtDev(btaddr[0])
    outbackInverterObject = OutbackBt(outbackBtDevConnection, btaddr[0])
    outbackBtDevConnection.connect()

    if outbackInverterObject is None:
        logger.error("ERROR >>> No Inverter connection at " + str(btaddr))
        sys.exit(1)
    
    return outbackInverterObject

def poll_inverter(loop, inverterDevice):
    poller = Thread(target=lambda: inverterDevice.publish_inverter(loop))
    poller.daemon = True
    poller.start()
    return True

def main():
    logger.info("Starting dbus-btoutback")
    logger.info("dbus-btoutback v" + str(utils.DRIVER_VERSION) + utils.DRIVER_SUBVERSION)

    btaddr = get_btaddr()
    outbackInverterObject = setup_outback_connection(btaddr)
    outbackInverterObject.log_settings()

    DBusGMainLoop(set_as_default=True)
    if sys.version_info.major == 2:
        gobject.threads_init()
    mainloop = gobject.MainLoop()

    inverterDevice = DbusHelper(outbackInverterObject, 1)
    if not inverterDevice.setup_vedbus():
        logger.error("ERROR >>> Problem with inverter " + str(btaddr))
        sys.exit(1)

    gobject.timeout_add(outbackInverterObject.poll_interval, lambda: poll_inverter(mainloop, inverterDevice))
    try:
        mainloop.run()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
