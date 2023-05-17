#!/usr/bin/python
# -*- coding: utf-8 -*-
from typing import Union

from time import sleep
from dbus.mainloop.glib import DBusGMainLoop
from threading import Thread
import sys

if sys.version_info.major == 2:
	import gobject
else:
	from gi.repository import GLib as gobject

# Victron packages
# from ve_utils import exit_on_error

from dbushelper import DbusHelper
from utils import logger
import utils
from inverter import Inverter
from outbackbt import OutbackBt

logger.info("Starting dbus-btoutback")

def main():
	useInverterDevice = False
	useSolarchargerDevice = False
	useVebusDevice = False
	useMultiDevice = True
	usePvInverterDevice = False

	def poll_inverter(loop):
		# Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
		if useInverterDevice:
			poller = Thread(target=lambda: inverterDevice.publish_inverter(loop))
			# Thread will die with us if deamon
			poller.daemon = True
			poller.start()

		if useSolarchargerDevice:
			poller2 = Thread(target=lambda: solarchargerDevice.publish_inverter(loop))
			# Thread will die with us if deamon
			poller2.daemon = True
			poller2.start()

		if useVebusDevice:
			poller3 = Thread(target=lambda: vebusDevice.publish_inverter(loop))
			# Thread will die with us if deamon
			poller3.daemon = True
			poller3.start()

		if useMultiDevice:
			poller4 = Thread(target=lambda: multiDevice.publish_inverter(loop))
			# Thread will die with us if deamon
			poller4.daemon = True
			poller4.start()

		if usePvInverterDevice:
			poller5 = Thread(target=lambda: pvInverterDevice.publish_inverter(loop))
			# Thread will die with us if deamon
			poller5.daemon = True
			poller5.start()

		return True

	def get_btaddr() -> list:
		# Get the bluetooth address we need to use from the argument
		if len(sys.argv) > 1:
			return sys.argv[1:]
		else:
			return [utils.OUTBACK_ADDRESS]

	logger.info(
		"dbus-btoutback v" + str(utils.DRIVER_VERSION) + utils.DRIVER_SUBVERSION
	)

	btaddr = get_btaddr()
	outbackInverterObject: Inverter = OutbackBt(btaddr[0])

	if outbackInverterObject is None:
		logger.error("ERROR >>> No Inverter connection at " + str(btaddr))
		sys.exit(1)

	outbackInverterObject.log_settings()

	# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
	DBusGMainLoop(set_as_default=True)
	if sys.version_info.major == 2:
		gobject.threads_init()
	mainloop = gobject.MainLoop()

	if useInverterDevice:
		# Get the initial values for the battery used by setup_vedbus
		inverterDevice = DbusHelper(outbackInverterObject, 'inverter', 1)

		if not inverterDevice.setup_vedbus():
			logger.error("ERROR >>> Problem with inverter " + str(btaddr))
			sys.exit(1)

	if useSolarchargerDevice:
		# Get the initial values for the battery used by setup_vedbus
		solarchargerDevice = DbusHelper(outbackInverterObject, 'solarcharger', 2)

		if not solarchargerDevice.setup_vedbus():
			logger.error("ERROR >>> Problem with solarcharger " + str(btaddr))
			sys.exit(1)

	if useVebusDevice:
		# Get the initial values for the battery used by setup_vedbus
		vebusDevice = DbusHelper(outbackInverterObject, 'vebus', 3)

		if not vebusDevice.setup_vedbus():
			logger.error("ERROR >>> Problem with vebus " + str(btaddr))
			sys.exit(1)

	if useMultiDevice:
		# Get the initial values for the battery used by setup_vedbus
		multiDevice = DbusHelper(outbackInverterObject, 'multi', 4)

		if not multiDevice.setup_vedbus():
			logger.error("ERROR >>> Problem with multi " + str(btaddr))
			sys.exit(1)

	if usePvInverterDevice:
		# Get the initial values for the battery used by setup_vedbus
		pvInverterDevice = DbusHelper(outbackInverterObject, 'pvinverter', 5)

		if not pvInverterDevice.setup_vedbus():
			logger.error("ERROR >>> Problem with pvinverter " + str(btaddr))
			sys.exit(1)

	# Poll the battery at INTERVAL and run the main loop
	gobject.timeout_add(outbackInverterObject.poll_interval, lambda: poll_inverter(mainloop))
	try:
		mainloop.run()
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	main()
