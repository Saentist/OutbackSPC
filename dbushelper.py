# -*- coding: utf-8 -*-
import sys
import os
import platform
import dbus
import traceback

# Victron packages
sys.path.insert(
    1,
    os.path.join(
        os.path.dirname(__file__),
        "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    ),
)
from vedbus import VeDbusService
from settingsdevice import SettingsDevice
from utils import *


# Again not all of these needed this is just duplicating the Victron code.
class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)


def dbusconnection():
    return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


class DbusHelper:
    def __init__(self, inverter, devType):
        self.inverter = inverter
        self.instance = 1
        self.settings = None
        self.error_count = 0
        self.devType = devType
        self._dbusService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())

    def setup_instance(self):
        bms_id = self.inverter.port[self.inverter.port.rfind("/") + 1:]
        path = "/Settings/Devices/outbackinverter"
        default_instance = self.devType + ":1"
        settings = {
            "instance": [
                path + "_" + str(bms_id).replace(" ", "_") + "/ClassAndVrmInstance",
                default_instance,
                0,
                0,
            ],
        }

        self.settings = SettingsDevice(dbusconnection(), settings, self.handle_changed_setting)
        self.inverter.role, self.instance = self.get_role_instance()

    def get_role_instance(self):
        val = self.settings["instance"].split(":")
        logger.info("DeviceInstance = %d", int(val[1]))
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == "instance":
            # self.inverter.role, self.instance = self.get_role_instance()
            self.devType, self.instance = self.get_role_instance()
            logger.info("Changed DeviceInstance = %d", self.instance)
            return

    def setup_vedbus(self):
        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        # This is only called once when a battery is initiated
        self.setup_instance()
        short_port = self.inverter.port[self.inverter.port.rfind("/") + 1:]
        logger.info("%s" % ("com.victronenergy." + self.devType + "." + short_port))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusService.add_path("/Mgmt/ProcessName", __file__)
        self._dbusService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
        self._dbusService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)

        # Create the mandatory objects
        self._dbusService.add_path("/DeviceInstance", self.instance)
        self._dbusService.add_path("/ProductId", 0x0)
        self._dbusService.add_path("/ProductName", "Outback (" + self.inverter.type + ")")
        self._dbusService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
        self._dbusService.add_path("/HardwareVersion", self.inverter.hardware_version)
        self._dbusService.add_path("/Connected", 1)
        self._dbusService.add_path("/CustomName", "Outback (" + self.inverter.type + ")", writeable=True)

        # Create System items
        self._dbusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusService.add_path("/Hub/ChargeVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=lambda p, v: "{:2.3f}A".format(v), )
        self._dbusService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )
        self._dbusService.add_path("/Yield/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )
        self._dbusService.add_path("/Pv/I", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}A".format(v), )
        self._dbusService.add_path("/Load/I", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}A".format(v), )
        self._dbusService.add_path("/Pv/V", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )

        return True

    def publish_inverter(self, loop):
        # This is called every battery.poll_interval milli second as set up per battery type to read and update the data
        try:
            # Call the battery's refresh_data function
            success = self.inverter.refresh_data()
            if success:
                self.error_count = 0
                self.inverter.online = True
            else:
                self.error_count += 1
                # If the battery is offline for more than 10 polls (polled every second for most batteries)
                if self.error_count >= 10:
                    self.inverter.online = False
                # Has it completely failed
                if self.error_count >= 60:
                    loop.quit()

            # publish all the data from the battery object to dbus
            self.publish_dbus()

        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        logger.debug("Publishing to dbus")
        print('1234')
        if self.devType == 'solarcharger':
            # Update SOC, DC and System items
            print('solarcharger')
            self._dbusService["/Hub/ChargeVoltage"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Dc/0/Power"] = round(self.inverter.a11pvInputPower, 2)
            self._dbusService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Load/I"] = round(self.inverter.a11pvInputCurrent, 2)
            print('solarcharger')

        if self.devType == 'vebus':
            print('vebus')
            self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03outputapppower - 30, 2)
            print('vebus')
        # logger.debug("logged to dbus [%s]" % str(round(self.inverter.soc, 2)))
