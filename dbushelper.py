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
from dbushelper2 import DbusHelper2
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

def get_bus():
    return (
        dbus.SessionBus()
        if "DBUS_SESSION_BUS_ADDRESS" in os.environ
        else dbus.SystemBus()
    )


class DbusHelper:
    def __init__(self, inverter, devType):
        self.inverter = inverter
        # self.helper2 = DbusHelper2()
        self.instance = 1
        self.settings = None
        self.error_count = 0
        self._dbusSolarchargerService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())

    def setup_instance(self, devType):
        # bms_id = self.battery.production if self.battery.production is not None else \
        #     self.battery.port[self.battery.port.rfind('/') + 1:]
        bms_id = self.inverter.port[self.inverter.port.rfind("/") + 1:]
        path = "/Settings/Devices/outbackinverter"
        default_instance = devType + ":1"
        settings = {
            "instance": [
                path + "_" + str(bms_id).replace(" ", "_") + "/ClassAndVrmInstance",
                default_instance,
                0,
                0,
            ],
        }

        self.settings = SettingsDevice(get_bus(), settings, self.handle_changed_setting)
        self.inverter.role, self.instance = self.get_role_instance()

    def get_role_instance(self):
        val = self.settings["instance"].split(":")
        logger.info("DeviceInstance = %d", int(val[1]))
        return val[0], int(val[1])

    def handle_changed_setting(self, setting, oldvalue, newvalue):
        if setting == "instance":
            self.inverter.role, self.instance = self.get_role_instance()
            logger.info("Changed DeviceInstance = %d", self.instance)
            return

        logger.info("Changed DeviceInstance = %d", float(self.settings["CellVoltageMin"]))
        # self._dbusSolarchargerService['/History/ChargeCycles']

    def setup_vedbus(self, type):
        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        # This is only called once when a battery is initiated
        self.setup_instance(type)
        short_port = self.inverter.port[self.inverter.port.rfind("/") + 1:]
        logger.info("%s" % ("com.victronenergy.solarcharger." + short_port))

        # Get the settings for the battery
        if not self.inverter.get_settings():
            return False

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusSolarchargerService.add_path("/Mgmt/ProcessName", __file__)
        self._dbusSolarchargerService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
        self._dbusSolarchargerService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)

        # Create the mandatory objects
        self._dbusSolarchargerService.add_path("/DeviceInstance", self.instance)
        self._dbusSolarchargerService.add_path("/ProductId", 0x0)
        self._dbusSolarchargerService.add_path("/ProductName", "Outback (" + self.inverter.type + ")")
        self._dbusSolarchargerService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
        self._dbusSolarchargerService.add_path("/HardwareVersion", self.inverter.hardware_version)
        self._dbusSolarchargerService.add_path("/Connected", 1)
        self._dbusSolarchargerService.add_path("/CustomName", "Outback (" + self.inverter.type + ")", writeable=True)

        # Create static battery info
        # self._dbusSolarchargerService.add_path("/Info/BatteryLowVoltage", self.inverter.min_battery_voltage, writeable=True)
        # self._dbusSolarchargerService.add_path("/Info/MaxChargeVoltage", self.inverter.max_battery_voltage, writeable=True, gettextcallback=lambda p, v: "{:0.2f}V".format(v),)
        # self._dbusSolarchargerService.add_path("/Info/MaxChargeCurrent", self.inverter.max_battery_charge_current, writeable=True, gettextcallback=lambda p, v: "{:0.2f}A".format(v),)
        # self._dbusSolarchargerService.add_path("/Info/MaxDischargeCurrent", self.inverter.max_battery_discharge_current, writeable=True, gettextcallback=lambda p, v: "{:0.2f}A".format(v),)
        # self._dbusSolarchargerService.add_path("/System/NrOfCellsPerBattery", self.inverter.cell_count, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/NrOfModulesOnline", 1, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/NrOfModulesOffline", 0, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/NrOfModulesBlockingCharge", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/NrOfModulesBlockingDischarge", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Capacity", self.inverter.get_capacity_remain(), writeable=True, gettextcallback=lambda p, v: "{:0.2f}Ah".format(v),)
        # self._dbusSolarchargerService.add_path("/InstalledCapacity", self.inverter.capacity, writeable=True, gettextcallback=lambda p, v: "{:0.0f}Ah".format(v),)
        # self._dbusSolarchargerService.add_path("/ConsumedAmphours", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}Ah".format(v),)
        # Not used at this stage
        # self._dbusSolarchargerService.add_path('/System/MinTemperatureCellId', None, writeable=True)
        # self._dbusSolarchargerService.add_path('/System/MaxTemperatureCellId', None, writeable=True)

        # Create SOC, DC and System items
        # self._dbusSolarchargerService.add_path("/Soc", None, writeable=True)
        self._dbusSolarchargerService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusSolarchargerService.add_path("/Hub/ChargeVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusSolarchargerService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=lambda p, v: "{:2.3f}A".format(v), )
        self._dbusSolarchargerService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )
        self._dbusSolarchargerService.add_path("/Yield/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )
        self._dbusSolarchargerService.add_path("/Pv/I", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}A".format(v), )
        self._dbusSolarchargerService.add_path("/Load/I", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}A".format(v), )
        self._dbusSolarchargerService.add_path("/Pv/V", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        self._dbusSolarchargerService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )
        # self._dbusSolarchargerService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v),)
        # self._dbusSolarchargerService.add_path("/Dc/0/Temperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Dc/0/MidVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:0.2f}V".format(v),)
        # self._dbusSolarchargerService.add_path("/Dc/0/MidVoltageDeviation", None, writeable=True, gettextcallback=lambda p, v: "{:0.1f}%".format(v),)

        # Create battery extras
        # self._dbusSolarchargerService.add_path("/System/MinCellTemperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/MaxCellTemperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/MaxCellVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:0.3f}V".format(v),)
        # self._dbusSolarchargerService.add_path("/System/MaxVoltageCellId", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/System/MinCellVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:0.3f}V".format(v),)
        # self._dbusSolarchargerService.add_path("/System/MinVoltageCellId", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/History/ChargeCycles", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/History/TotalAhDrawn", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Balancing", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Io/AllowToCharge", 0, writeable=True)
        # self._dbusSolarchargerService.add_path("/Io/AllowToDischarge", 0, writeable=True)
        # self._dbusSolarchargerService.add_path('/SystemSwitch',1,writeable=True)

        # Create the alarms
        # self._dbusSolarchargerService.add_path("/Alarms/LowVoltage", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighVoltage", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/LowCellVoltage", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighCellVoltage", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/LowSoc", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighChargeCurrent", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighDischargeCurrent", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/CellImbalance", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/InternalFailure", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighChargeTemperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/LowChargeTemperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/HighTemperature", None, writeable=True)
        # self._dbusSolarchargerService.add_path("/Alarms/LowTemperature", None, writeable=True)

        # Create TimeToGO item
        # self._dbusSolarchargerService.add_path("/TimeToGo", None, writeable=True)

        # logger.info(f"publish config values = {PUBLISH_CONFIG_VALUES}")
        # if PUBLISH_CONFIG_VALUES == 1:
            # publish_config_variables(self._dbusSolarchargerService)

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

            # This is to mannage CCL\DCL
            # self.inverter.manage_charge_current()

            # This is to mannage CVCL
            # self.inverter.manage_charge_voltage()

            # publish all the data from the battery object to dbus
            self.publish_dbus()

        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):

        # Update SOC, DC and System items
        #self._dbusSolarchargerService["/System/NrOfCellsPerBattery"] = self.inverter.cell_count
        #self._dbusSolarchargerService["/Soc"] = round(self.inverter.soc, 2)
        self._dbusSolarchargerService["/Hub/ChargeVoltage"] = round(self.inverter.a11pvInputVoltage, 2)
        self._dbusSolarchargerService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
        self._dbusSolarchargerService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
        self._dbusSolarchargerService["/Dc/0/Power"] = round(self.inverter.a11pvInputPower, 2)
        # self._dbusSolarchargerService["/Yield/Power"] = round(self.inverter.voltage * self.inverter.current, 2)
        self._dbusSolarchargerService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
        self._dbusSolarchargerService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
        self._dbusSolarchargerService["/Load/I"] = round(self.inverter.a11pvInputCurrent, 2)
        self._dbusSolarchargerService["/Ac/Out/L1/P"] = round(self.inverter.a03outputapppower - 30, 2)

        # self.helper2.getDataFromOutback(round(self.inverter.a03outputapppower - 30, 2))
        # self._dbusSolarchargerService["/Dc/0/Temperature"] = self.inverter.get_temp()
        # self._dbusSolarchargerService["/Capacity"] = self.inverter.get_capacity_remain()
        # self._dbusSolarchargerService["/ConsumedAmphours"] = (
        #     0
        #     if self.inverter.capacity is None
        #        or self.inverter.get_capacity_remain() is None
        #     else self.inverter.capacity - self.inverter.get_capacity_remain()
        # )
        #
        # midpoint, deviation = self.inverter.get_midvoltage()
        # if midpoint is not None:
        #     self._dbusSolarchargerService["/Dc/0/MidVoltage"] = midpoint
        #     self._dbusSolarchargerService["/Dc/0/MidVoltageDeviation"] = deviation
        #
        # # Update battery extras
        # self._dbusSolarchargerService["/History/ChargeCycles"] = self.inverter.cycles
        # self._dbusSolarchargerService["/History/TotalAhDrawn"] = self.inverter.total_ah_drawn
        # self._dbusSolarchargerService["/Io/AllowToCharge"] = (
        #     1 if self.inverter.charge_fet and self.inverter.control_allow_charge else 0
        # )
        # self._dbusSolarchargerService["/Io/AllowToDischarge"] = (
        #     1
        #     if self.inverter.discharge_fet and self.inverter.control_allow_discharge
        #     else 0
        # )
        # self._dbusSolarchargerService["/System/NrOfModulesBlockingCharge"] = (
        #     0
        #     if self.inverter.charge_fet is None
        #        or (self.inverter.charge_fet and self.inverter.control_allow_charge)
        #     else 1
        # )
        # self._dbusSolarchargerService["/System/NrOfModulesBlockingDischarge"] = (
        #     0 if self.inverter.discharge_fet is None or self.inverter.discharge_fet else 1
        # )
        # self._dbusSolarchargerService["/System/NrOfModulesOnline"] = 1 if self.inverter.online else 0
        # self._dbusSolarchargerService["/System/NrOfModulesOffline"] = (
        #     0 if self.inverter.online else 1
        # )
        # self._dbusSolarchargerService["/System/MinCellTemperature"] = self.inverter.get_min_temp()
        # self._dbusSolarchargerService["/System/MaxCellTemperature"] = self.inverter.get_max_temp()
        #
        # # Charge control
        # self._dbusSolarchargerService[
        #     "/Info/MaxChargeCurrent"
        # ] = self.inverter.control_charge_current
        # self._dbusSolarchargerService[
        #     "/Info/MaxDischargeCurrent"
        # ] = self.inverter.control_discharge_current
        #
        # # Voltage control
        # self._dbusSolarchargerService["/Info/MaxChargeVoltage"] = self.inverter.control_voltage
        #
        # # Updates from cells
        # self._dbusSolarchargerService["/System/MinVoltageCellId"] = self.inverter.get_min_cell_desc()
        # self._dbusSolarchargerService["/System/MaxVoltageCellId"] = self.inverter.get_max_cell_desc()
        # self._dbusSolarchargerService[
        #     "/System/MinCellVoltage"
        # ] = self.inverter.get_min_cell_voltage()
        # self._dbusSolarchargerService[
        #     "/System/MaxCellVoltage"
        # ] = self.inverter.get_max_cell_voltage()
        # self._dbusSolarchargerService["/Balancing"] = self.inverter.get_balancing()
        #
        # # Update the alarms
        # self._dbusSolarchargerService["/Alarms/LowVoltage"] = self.inverter.protection.voltage_low
        # self._dbusSolarchargerService[
        #     "/Alarms/LowCellVoltage"
        # ] = self.inverter.protection.voltage_cell_low
        # self._dbusSolarchargerService["/Alarms/HighVoltage"] = self.inverter.protection.voltage_high
        # self._dbusSolarchargerService["/Alarms/LowSoc"] = self.inverter.protection.soc_low
        # self._dbusSolarchargerService[
        #     "/Alarms/HighChargeCurrent"
        # ] = self.inverter.protection.current_over
        # self._dbusSolarchargerService[
        #     "/Alarms/HighDischargeCurrent"
        # ] = self.inverter.protection.current_under
        # self._dbusSolarchargerService[
        #     "/Alarms/CellImbalance"
        # ] = self.inverter.protection.cell_imbalance
        # self._dbusSolarchargerService[
        #     "/Alarms/InternalFailure"
        # ] = self.inverter.protection.internal_failure
        # self._dbusSolarchargerService[
        #     "/Alarms/HighChargeTemperature"
        # ] = self.inverter.protection.temp_high_charge
        # self._dbusSolarchargerService[
        #     "/Alarms/LowChargeTemperature"
        # ] = self.inverter.protection.temp_low_charge
        # self._dbusSolarchargerService[
        #     "/Alarms/HighTemperature"
        # ] = self.inverter.protection.temp_high_discharge
        # self._dbusSolarchargerService[
        #     "/Alarms/LowTemperature"
        # ] = self.inverter.protection.temp_low_discharge

        # logger.debug("logged to dbus [%s]" % str(round(self.inverter.soc, 2)))
