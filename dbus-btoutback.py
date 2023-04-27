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
	helper1 = True
	helper2 = False
	helper3 = False

	def poll_inverter(loop):
		# Run in separate thread. Pass in the mainloop so the thread can kill us if there is an exception.
		if helper1:
			poller = Thread(target=lambda: helper.publish_inverter(loop))
			# Thread will die with us if deamon
			poller.daemon = True
			poller.start()

		if helper2:
			poller2 = Thread(target=lambda: helper2.publish_inverter(loop))
			# Thread will die with us if deamon
			poller2.daemon = True
			poller2.start()

		if helper3:
			poller3 = Thread(target=lambda: helper3.publish_inverter(loop))
			# Thread will die with us if deamon
			poller3.daemon = True
			poller3.start()

		return True

	def get_btaddr() -> str:
		# Get the bluetooth address we need to use from the argument
		if len(sys.argv) > 1:
			return sys.argv[1:]
		else:
			return ["00:35:FF:02:95:99"]

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

	if helper1:
		# Get the initial values for the battery used by setup_vedbus
		helper = DbusHelper(outbackInverterObject, 'inverter', 1)

		if not helper.setup_vedbus():
			logger.error("ERROR >>> Problem with inverter " + str(btaddr))
			sys.exit(1)

	if helper2:
		# Get the initial values for the battery used by setup_vedbus
		helper2 = DbusHelper(outbackInverterObject, 'solarcharger', 2)

		if not helper2.setup_vedbus():
			logger.error("ERROR >>> Problem with inverter " + str(btaddr))
			sys.exit(1)

	if helper3:
		# Get the initial values for the battery used by setup_vedbus
		helper3 = DbusHelper(outbackInverterObject, 'multi', 3)

		if not helper3.setup_vedbus():
			logger.error("ERROR >>> Problem with inverter " + str(btaddr))
			sys.exit(1)

	# Poll the battery at INTERVAL and run the main loop
	gobject.timeout_add(outbackInverterObject.poll_interval, lambda: poll_inverter(mainloop))
	try:
		mainloop.run()
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	main()
