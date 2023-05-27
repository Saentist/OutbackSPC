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
from vedbus import VeDbusService, VeDbusItemImport
from utils import *
import utils

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

	def __init__(self, inverter, instance):
		self._dbusMulitService = None
		self._dbusVebusService = None
		self._dbusPvinverterService = None
		self._dbusInverterService = None
		self._dbusSolarChargerService = None
		self._dbusGensetService = None
		
		self.inverter = inverter
		self.instance = instance
		self.error_count = 0
		self.debug = utils.DEBUG_MODE
		self.interval = 1
		self._importedDbusValues = {}
		self._dbusConnection = dbusconnection()
		
		# ON / OFF SWITCHES
		self.useInverterDevice = False
		self.useSolarchargerDevice = True
		self.usePvInverterDevice = False
		self.useVebusDevice = True
		self.useMultiDevice = False
		self.useGensetDevice = False
		
	def setup_vedbus(self):
		# formating
		_kwh = lambda p, v: (str(v) + 'KWh')    # lambda p, v: "{:0.1f}A".format(v)
		_a = lambda p, v: (str(v) + 'A')        # lambda p, v: "{:2.3f}A".format(v)
		_w = lambda p, v: (str(v) + 'W')        # lambda p, v: "{:0.0f}W".format(v)
		_v = lambda p, v: (str(v) + 'V')        # lambda p, v: "{:2.2f}V".format(v)
		_h = lambda p, v: (str(v) + 'Hz')        # lambda p, v: "{:2.2f}V".format(v)
		_ms = lambda p, v: (str(v or '') + "ms")
		_x = lambda p, v: (str(v or ''))
		_p = lambda p, v: (str(v) + '%')
		
		short_port = self.inverter.port[self.inverter.port.rfind("/") + 1:]
		
		if self.useInverterDevice:
			devType = "inverter"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusInverterService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusInverterService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusInverterService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusInverterService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusInverterService.add_path("/DeviceInstance", self.instance)
			self._dbusInverterService.add_path("/ProductId", 0x0)
			self._dbusInverterService.add_path("/ProductName", "Outback - SPC III")
			self._dbusInverterService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusInverterService.add_path("/HardwareVersion", '3KW')
			self._dbusInverterService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusInverterService.add_path('/Mode', 2)
			self._dbusInverterService.add_path('/State', 9)
			self._dbusInverterService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusInverterService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusInverterService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
			self._dbusInverterService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
			self._dbusInverterService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
			self._dbusInverterService.add_path("/Ac/Out/L1/S", None, writeable=True, gettextcallback=_a, )
			self._dbusInverterService.add_path("/Ac/Out/L1/F", None, writeable=True, gettextcallback=_a, )
			self._dbusInverterService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusInverterService.add_path("/Pv/V", None, writeable=True, gettextcallback=_v, )
			self._dbusInverterService.add_path('/Soc', 0, writeable=True, gettextcallback=_p, )
			self._dbusInverterService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x, )
			self._dbusInverterService.add_path("/CustomName", "Outback Inverter", writeable=True)
			
		if self.useSolarchargerDevice:
			devType = "solarcharger"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusSolarChargerService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusSolarChargerService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusSolarChargerService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusSolarChargerService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusSolarChargerService.add_path("/DeviceInstance", self.instance)
			self._dbusSolarChargerService.add_path("/ProductId", 0x0)
			self._dbusSolarChargerService.add_path("/ProductName", "Outback - SPC III")
			self._dbusSolarChargerService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusSolarChargerService.add_path("/HardwareVersion", '3KW')
			self._dbusSolarChargerService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusSolarChargerService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusSolarChargerService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusSolarChargerService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusSolarChargerService.add_path("/Pv/I", None, writeable=True, gettextcallback=_a, )
			self._dbusSolarChargerService.add_path("/Pv/V", None, writeable=True, gettextcallback=_v, )
			self._dbusSolarChargerService.add_path('/State', 0, writeable=True)
			self._dbusSolarChargerService.add_path('/Load/State', 0, writeable=True)
			self._dbusSolarChargerService.add_path('/Load/I', 0, writeable=True)
			self._dbusSolarChargerService.add_path('/ErrorCode', 0)
			self._dbusSolarChargerService.add_path('/Yield/Power', 0, writeable=True)  # Actual input power (Watts)
			self._dbusSolarChargerService.add_path('/Yield/User', 0)  # Total kWh produced (user resettable)
			self._dbusSolarChargerService.add_path('/Yield/System', 0)  # Total kWh produced (not resettable)
			self._dbusSolarChargerService.add_path('/Mode', 0, writeable=True)
			self._dbusSolarChargerService.add_path('/MppOperationMode', 2)
			self._dbusSolarChargerService.add_path('/Dc/0/Temperature', None, writeable=True)
			self._dbusSolarChargerService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x, )
			self._dbusSolarChargerService.add_path("/CustomName", "Outback SPCIII", writeable=True)
			
		if self.usePvInverterDevice:
			devType = "pvinverter"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusPvinverterService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusPvinverterService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusPvinverterService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusPvinverterService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusPvinverterService.add_path("/DeviceInstance", self.instance)
			self._dbusPvinverterService.add_path("/ProductId", 0x0)
			self._dbusPvinverterService.add_path("/ProductName", "Outback - SPC III")
			self._dbusPvinverterService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusPvinverterService.add_path("/HardwareVersion", '3KW')
			self._dbusPvinverterService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusPvinverterService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusPvinverterService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusPvinverterService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusPvinverterService.add_path("/Pv/I", None, writeable=True, gettextcallback=_a, )
			self._dbusPvinverterService.add_path("/Pv/V", None, writeable=True, gettextcallback=_v, )
			self._dbusPvinverterService.add_path('/State', 0, writeable=True)
			self._dbusPvinverterService.add_path('/Load/State', 0, writeable=True)
			self._dbusPvinverterService.add_path('/Load/I', 0, writeable=True)
			self._dbusPvinverterService.add_path('/ErrorCode', 0)
			self._dbusPvinverterService.add_path('/Yield/Power', 0, writeable=True)  # Actual input power (Watts)
			self._dbusPvinverterService.add_path('/Yield/User', 0)  # Total kWh produced (user resettable)
			self._dbusPvinverterService.add_path('/Yield/System', 0)  # Total kWh produced (not resettable)
			self._dbusPvinverterService.add_path('/Mode', 0, writeable=True)
			self._dbusPvinverterService.add_path('/MppOperationMode', 2)
			self._dbusPvinverterService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x, )
			self._dbusPvinverterService.add_path("/CustomName", "Outback PV Inverter", writeable=True)
			
		if self.useVebusDevice:
			devType = "vebus"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusVebusService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusVebusService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusVebusService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusVebusService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusVebusService.add_path("/DeviceInstance", self.instance)
			self._dbusVebusService.add_path("/ProductId", 0x0)
			self._dbusVebusService.add_path("/ProductName", "Outback - SPC III")
			self._dbusVebusService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusVebusService.add_path("/HardwareVersion", '3KW')
			self._dbusVebusService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusVebusService.add_path("/Ac/State/IgnoreAcIn1",0)
			self._dbusVebusService.add_path("/Settings/SystemSetup/AcInput1",2)
			self._dbusVebusService.add_path("/Ac/PowerMeasurementType",2)
			self._dbusVebusService.add_path("/Ac/ActiveIn/ActiveInput", 0)
			self._dbusVebusService.add_path("/Ac/In/1/CurrentLimit", 0)
			self._dbusVebusService.add_path("/Ac/In/1/CurrentLimitIsAdjustable", None, writeable=True,gettextcallback=_w, )  # <- 0 when inverting, 1 when connected to an AC in
			self._dbusVebusService.add_path("/Ac/ActiveIn/L1", None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Ac/ActiveIn/P", None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Ac/ActiveIn/L1/P", None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Ac/ActiveIn/L1/I", None, writeable=True, gettextcallback=_a, )
			self._dbusVebusService.add_path("/Ac/ActiveIn/L1/V", None, writeable=True, gettextcallback=_v, )
			self._dbusVebusService.add_path("/Ac/ActiveIn/L1/F", None, writeable=True, gettextcallback=_h, )
			self._dbusVebusService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
			self._dbusVebusService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
			self._dbusVebusService.add_path("/Ac/Out/L1/F", None, writeable=True, gettextcallback=_h, )
			
			self._dbusVebusService.add_path("/Energy/AcIn1ToAcOut", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/AcIn1ToInverter", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/AcIn2ToAcOut", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/AcIn2ToInverter", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/AcOutToAcIn1", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/AcOutToAcIn2", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/InverterToAcIn1", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/InverterToAcIn2", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/InverterToAcOut", None, writeable=True, )
			self._dbusVebusService.add_path("/Energy/OutToInverter", None, writeable=True, )
			
			self._dbusVebusService.add_path('/Pv/I', None, writeable=True, gettextcallback=_a, )
			self._dbusVebusService.add_path('/Pv/V', None, writeable=True, gettextcallback=_v, )
			self._dbusVebusService.add_path('/Pv/P', None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusVebusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusVebusService.add_path("/Dc/0/Temperature", 0, writeable=True, gettextcallback=_w, )
			self._dbusVebusService.add_path('/Soc', 0, writeable=True,)
			self._dbusVebusService.add_path("/Mode", 3, writeable=True, )
			self._dbusVebusService.add_path("/ModeIsAdjustable", 3,writeable=True, )
			self._dbusVebusService.add_path('/State', 9,writeable=True, )
			self._dbusVebusService.add_path('/VebusChargeState', 9, writeable=True, )
			self._dbusVebusService.add_path('/VebusSetChargeState', 9,writeable=True, )
			self._dbusVebusService.add_path('/Leds/Mains', 1)
			self._dbusVebusService.add_path('/Leds/Bulk', 0)
			self._dbusVebusService.add_path('/Leds/Absorption', 0)
			self._dbusVebusService.add_path('/Leds/Float', 0)
			self._dbusVebusService.add_path('/Leds/Inverter', 0)
			self._dbusVebusService.add_path('/Leds/Overload', 0)
			self._dbusVebusService.add_path('/Leds/LowBattery', 0)
			self._dbusVebusService.add_path('/Leds/Temperature', 0)
			self._dbusVebusService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x, )
			self._dbusVebusService.add_path("/CustomName", "Outback Vebus", writeable=True)
			
		if self.useMultiDevice:
			devType = "multi"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusMulitService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusMulitService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusMulitService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusMulitService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusMulitService.add_path("/DeviceInstance", self.instance)
			self._dbusMulitService.add_path("/ProductId", 0x0)
			self._dbusMulitService.add_path("/ProductName", "Outback - SPC III")
			self._dbusMulitService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusMulitService.add_path("/HardwareVersion", '3KW')
			self._dbusMulitService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusMulitService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Yield/User", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Yield/System", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Ac/In/1/L1/P", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Ac/In/1/L1/I", None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Ac/In/1/L1/V", None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path("/Ac/In/1/L1/F", None, writeable=True, gettextcallback=_h, )
			self._dbusMulitService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Ac/Out/L1/F", None, writeable=True, gettextcallback=_h, )
			self._dbusMulitService.add_path("/Energy/AcIn1ToAcOut", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/AcIn1ToInverter", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/AcIn2ToAcOut", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/AcIn2ToInverter", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/AcOutToAcIn1", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/AcOutToAcIn2", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/InverterToAcIn1", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/InverterToAcIn2", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/InverterToAcOut", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/OutToInvertert", None, writeable=True, )
			self._dbusMulitService.add_path('/Pv/V', None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path('/Pv/P', None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path('/Pv/I', None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Dc/0/Temperature", 0, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path('/MppOperationMode', 1, writeable=True,)
			self._dbusMulitService.add_path("/Ac/ActiveIn/ActiveInput", 0)
			self._dbusMulitService.add_path("/Ac/NumberOfPhases", 1)
			self._dbusMulitService.add_path("/Ac/NumberOfAcInputs", 1)
			self._dbusMulitService.add_path("/Ac/In/1/Type", 2)
			self._dbusMulitService.add_path('/NrOfTrackers', 1)
			self._dbusMulitService.add_path('/Mode', 3, writeable=True,)
			self._dbusMulitService.add_path('/State', 9, writeable=True,)
			self._dbusMulitService.add_path('/Soc', 0, writeable=True,)
			self._dbusMulitService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x,)
			self._dbusMulitService.add_path("/CustomName", "Outback Multi", writeable=True)
			
		if self.useGensetDevice:
			devType = "genset"
			logger.info("%s" % ("com.victronenergy." + devType + "." + short_port))
			self._dbusGensetService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())
			
			# Create the management objects, as specified in the ccgx dbus-api document
			self._dbusGensetService.add_path("/Mgmt/ProcessName", __file__)
			self._dbusGensetService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
			self._dbusGensetService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)
			
			# Create the mandatory objects
			self._dbusGensetService.add_path("/DeviceInstance", self.instance)
			self._dbusGensetService.add_path("/ProductId", 0x0)
			self._dbusGensetService.add_path("/ProductName", "Champion Hybrid")
			self._dbusGensetService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
			self._dbusGensetService.add_path("/HardwareVersion", '3KW')
			self._dbusGensetService.add_path("/Connected", 1)
			
			# Create device specific objects
			self._dbusGensetService.add_path("/Engine/Load", 0, writeable=True, gettextcallback=_p, )
			self._dbusGensetService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x, )
			self._dbusGensetService.add_path("/CustomName", "Champion Hybrid", writeable=True)
			
		return True
		
	def publish_inverter(self, loop):
		# This is called every battery.poll_interval milli second as set up per battery type to read and update the data
		try:
			# Call the battery's refresh_data function
			success = self.inverter.refresh_data()
			if success:
				self.error_count = 0
				self.inverter.online = True
				
				# publish all the data from the battery object to dbus
				self.publish_dbus()
				sleep(self.interval)
			else:
				logger.info("INFO >>> Waiting for inverter data")
				logger.info("INFO >>> Waiting for inverter data")
				self.error_count += 1
				# If the battery is offline for more than 10 polls (polled every second for most batteries)
				if self.error_count >= 20:
					self.inverter.online = False
					logger.warning("WARNING >>> Inverter possbily offline")
				# Has it completely failed
				if self.error_count >= 100:
					logger.error("ERROR >>> Loop quited")
					loop.quit()
		except:
			traceback.print_exc()
			loop.quit()
			
	def publish_dbus(self):
		logger.info("Publishing to dbus")
		
		# Battery Values
		hasVictronBMS = 'com.victronenergy.battery.ttyUSB0' in self._dbusConnection.list_names()
		if hasVictronBMS:
			self._importedDbusValues["/Dc/0/Voltage"] = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Voltage')
			self._importedDbusValues["/Dc/0/Current"] = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Current')
			self._importedDbusValues["/Dc/0/Power"] = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Power')
			self._importedDbusValues["/Soc"] = VeDbusItemImport(self._dbusConnection, 'com.victronenergy.battery.ttyUSB0', '/Soc')
			self._importedDbusValues["/Dc/0/Temperature"] = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Temperature')
			
		if self.useInverterDevice:
			logger.info("==> writing inverter data ")
			# self._dbusInverterService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusInverterService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
			self._dbusInverterService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)
			self._dbusInverterService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)
			self._dbusInverterService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)
			self._dbusInverterService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)
			# self._dbusInverterService["/Ac/Out/L1/S"] = round(self.inverter.a03acOutputCurrent, 2)
			# self._dbusInverterService["/Yield/Power"] = round(self.inverter.a11pvInputPower, 2)
			# self._dbusInverterService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
			
			# if hasVictronBMS:
				# self._dbusInverterService["/Dc/0/Voltage"] = round(self._importedDbusValues["/Dc/0/Voltage"].get_value(),2)
				# self._dbusInverterService["/Dc/0/Current"] = round(self._importedDbusValues["/Dc/0/Current"].get_value(),2)
				# self._dbusInverterService["/Dc/0/Temperature"] = round(self._importedDbusValues["/Dc/0/Temperature"].get_value(),2)
				# self._dbusInverterService["/Dc/0/Power"] = round(self._importedDbusValues["/Dc/0/Power"].get_value(),2)
				# self._dbusInverterService["/Soc"] = round(self._importedDbusValues["/Soc"].get_value(), 2)
				
			index = self._dbusInverterService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusInverterService['/UpdateIndex'] = index
			
		if self.useSolarchargerDevice:
			logger.info("==> writing solar charger data ")
			self._dbusSolarChargerService["/Yield/Power"] = round(self.inverter.a11pvInputPower, 2)
			self._dbusSolarChargerService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
			self._dbusSolarChargerService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
			
			if hasVictronBMS:
				self._dbusSolarChargerService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)  # <- Battery Voltage
				self._dbusSolarChargerService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)  # <- Battery current in Ampere, positive when charging
				# self._dbusSolarChargerService["/Dc/0/Temperature"] = round(self._importedDbusValues["/Dc/0/Temperature"].get_value(),2)     # <- Battery temperature in degrees Celsius
				# self._dbusSolarChargerService["/Dc/0/Power"] = round(self._importedDbusValues["/Dc/0/Power"].get_value(),2)  # <- Battery Power
				# self._dbusSolarChargerService["/Soc"] = round(self._importedDbusValues["/Soc"].get_value(),2)  # <- Battery temperature in degrees Celsius
				
			index = self._dbusSolarChargerService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusSolarChargerService['/UpdateIndex'] = index
			
		if self.usePvInverterDevice:
			logger.info("==> writing pv inverter data ")
			self._dbusPvinverterService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
			self._dbusPvinverterService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
			self._dbusPvinverterService["/Dc/0/Power"] = round(self.inverter.a11pvInputPower, 2)
			self._dbusPvinverterService["/Yield/Power"] = round(self.inverter.a11pvInputPower, 2)
			self._dbusPvinverterService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
			self._dbusPvinverterService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
			
			index = self._dbusPvinverterService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusPvinverterService['/UpdateIndex'] = index

###########################
# VEBUS
###########################			
		if self.useVebusDevice:
			logger.info("==> writing vebus data ")
			if hasVictronBMS:
				self._dbusVebusService["/Dc/0/Voltage"] = round(self._importedDbusValues["/Dc/0/Voltage"].get_value(),2)
				self._dbusVebusService["/Dc/0/Current"] = round(self._importedDbusValues["/Dc/0/Current"].get_value(),2)
				self._dbusVebusService["/Dc/0/Temperature"] = round(self._importedDbusValues["/Dc/0/Temperature"].get_value(),2)
				self._dbusVebusService["/Soc"] = round(self._importedDbusValues["/Soc"].get_value(), 2)
				
			# AC Input measurements:
			# self._dbusVebusService["/Ac/In/1/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)                                               # <- Real power of AC IN1 on L1
			# self._dbusVebusService["/Ac/In/1/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)                                                # <- Current of AC IN1 on L1
			# self._dbusVebusService["/Ac/In/1/L1/V"] = round(self.inverter.a03gridVoltage, 2)               # <- Voltage of AC IN1 on L1
			# self._dbusVebusService["/Ac/In/1/L1/F"] = round(self.inverter.a03gridFrequency, 2)             # <- Frequency of AC IN1 on L1
			
			# AC Input settings:
			# self._dbusVebusService["/Ac/In/1/Type"] = 2                                                  # <- AC IN1 type: 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)
			
			# AC Output measurements:
			# self._dbusVebusService["/Ac/Out/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)    # <- Frequency of AC OUT1 on L1
			self._dbusVebusService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)    # <- Frequency of AC OUT1 on L1
			self._dbusVebusService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)          # <- Voltage of AC OUT1 on L1
			self._dbusVebusService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)          # <- Current of AC OUT1 on L1
			self._dbusVebusService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)        # <- Real power of AC OUT1 on L1
			
			# self._dbusVebusService["/Ac/ActiveIn/ActiveInput"] = 1                                       # <- Active input: 0 = ACin-1, 1 = ACin-2,
			# self._dbusVebusService["/Ac/NumberOfPhases"] = 1
			# self._dbusVebusService["/Ac/NumberOfAcInputs"] = 1
			
			# For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
			# Generic alarms:
			# self._dbusVebusService["/Alarms/LowSoc"] = 0                                               # <- Low state of charge
			# self._dbusVebusService["/Alarms/LowVoltage"] = 0                                           # <- Low battery voltage
			# self._dbusVebusService["/Alarms/HighVoltage "] = 0                                         # <- High battery voltage
			# self._dbusVebusService["/Alarms/LowVoltageAcOut"] = 0                                      # <- Low AC Out voltage
			# self._dbusVebusService["/Alarms/HighVoltageAcOut"] = 0                                     # <- High AC Out voltage
			# self._dbusVebusService["/Alarms/HighTemperature"] = 0                                      # <- High device temperature
			# self._dbusVebusService["/Alarms/Overload"] = 0                                             # <- Inverter overload
			# self._dbusVebusService["/Alarms/Ripple"] = 0                                               # <- High DC ripple
			
			# Battery Values
			# self._dbusVebusService["/Dc/0/Voltage"] = 1  # round(self.inverter.a11pvInputVoltage, 2)        # <- Battery Voltage
			# self._dbusVebusService["/Dc/0/Current"] = 2  # round(self.inverter.a11pvInputCurrent, 2)        # <- Battery current in Ampere, positive when charging
			# self._dbusVebusService["/Dc/0/Power"] = 2 #  round(self.inverter.a11pvInputPower, 2)            # <- Battery Power
			# self._dbusVebusService["/Dc/0/Temperature "] = round(self.inverter.a11pvInputPower, 2)     # <- Battery temperature in degrees Celsius
			
			# Additional Data
			# self._dbusVebusService['/Mode'] = 3                                                          # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
			# self._dbusVebusService['/State'] = 252                                                       # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External control
			# self._dbusVebusService['/Soc'] = 100                                                       # <- State of charge of internal battery monitor
			
			# PV tracker information:
			# self._dbusVebusService['/NrOfTrackers'] = 1                                                  # <- number of trackers
			self._dbusVebusService['/Pv/I'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
			self._dbusVebusService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
			self._dbusVebusService['/Pv/P'] = round(self.inverter.a11pvInputPower, 2)                  # <- PV array power (Watts) from 1st tracker
			self._dbusVebusService['/Yield/Power'] = round(self.inverter.a11pvInputPower, 2)                                                # <- PV array power (Watts)
			# self._dbusVebusService['/Yield/User'] = 1                                                  # <- Total kWh produced (user resettable)
			# self._dbusVebusService['/Yield/System'] = 1                                                # <- Total kWh produced (not resettable)
			# self._dbusVebusService['/MppOperationMode'] = 1                                              # <- 0 = Off 1 = Voltage or Current limited 2 = MPPT Tracker active
			
			self._dbusVebusService['/Energy/AcIn1ToAcOut'] = 0 # später generator
			self._dbusVebusService['/Energy/InverterToAcOut'] = round(self.inverter.a03acActivePower, 2)
			# self._dbusVebusService['/Energy/AcIn1ToInverter'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/AcIn2ToAcOut'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/AcIn2ToInverter'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/AcOutToAcIn1'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/AcOutToAcIn2'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/InverterToAcIn1'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/InverterToAcIn2'] = round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusVebusService['/Energy/OutToInverter'] = round(self.inverter.a11pvInputVoltage, 2)
				
			index = self._dbusVebusService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusVebusService['/UpdateIndex'] = index
			
		if self.useMultiDevice:
			logger.info("==> writing multi data ")
			# AC Input measurements:
			# self._dbusMulitService["/Ac/In/1/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)                                               # <- Real power of AC IN1 on L1
			# self._dbusMulitService["/Ac/In/1/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)                                                # <- Current of AC IN1 on L1
			# self._dbusMulitService["/Ac/In/1/L1/V"] = round(self.inverter.a03gridVoltage, 2)               # <- Voltage of AC IN1 on L1
			# self._dbusMulitService["/Ac/In/1/L1/F"] = round(self.inverter.a03gridFrequency, 2)             # <- Frequency of AC IN1 on L1
			
			# AC Input settings:
			# self._dbusMulitService["/Ac/In/1/Type"] = 2                                                  # <- AC IN1 type: 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)
			
			# AC Output measurements:
			# self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)    # <- Frequency of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)    # <- Frequency of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)          # <- Voltage of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)          # <- Current of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)        # <- Real power of AC OUT1 on L1
			
			# self._dbusMulitService["/Ac/ActiveIn/ActiveInput"] = 1                                       # <- Active input: 0 = ACin-1, 1 = ACin-2,
			# self._dbusMulitService["/Ac/NumberOfPhases"] = 1
			# self._dbusMulitService["/Ac/NumberOfAcInputs"] = 1
			
			# For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
			# Generic alarms:
			# self._dbusMulitService["/Alarms/LowSoc"] = 0                                               # <- Low state of charge
			# self._dbusMulitService["/Alarms/LowVoltage"] = 0                                           # <- Low battery voltage
			# self._dbusMulitService["/Alarms/HighVoltage "] = 0                                         # <- High battery voltage
			# self._dbusMulitService["/Alarms/LowVoltageAcOut"] = 0                                      # <- Low AC Out voltage
			# self._dbusMulitService["/Alarms/HighVoltageAcOut"] = 0                                     # <- High AC Out voltage
			# self._dbusMulitService["/Alarms/HighTemperature"] = 0                                      # <- High device temperature
			# self._dbusMulitService["/Alarms/Overload"] = 0                                             # <- Inverter overload
			# self._dbusMulitService["/Alarms/Ripple"] = 0                                               # <- High DC ripple
			
			# Additional Data
			# self._dbusMulitService['/Mode'] = 3                                                          # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
			# self._dbusMulitService['/State'] = 252                                                       # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External control
			# self._dbusMulitService['/Soc'] = 100                                                       # <- State of charge of internal battery monitor
			
			# PV tracker information:
			# self._dbusMulitService['/NrOfTrackers'] = 1                                                  # <- number of trackers
			# self._dbusMulitService['/Pv/I'] = round(self.inverter.a11pvInputCurrent, 2)                # <- PV array voltage from 1st tracker
			# self._dbusMulitService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
			# self._dbusMulitService['/Pv/P'] = round(self.inverter.a11pvInputPower, 2)                  # <- PV array power (Watts) from 1st tracker
			# self._dbusMulitService['/Yield/Power'] = round(self.inverter.a11pvInputPower, 2)                                                # <- PV array power (Watts)
			# self._dbusMulitService['/Yield/User'] = 97                                                  # <- Total kWh produced (user resettable)
			# self._dbusMulitService['/Yield/System'] = 96                                                # <- Total kWh produced (not resettable)
			# self._dbusMulitService['/MppOperationMode'] = 1
			
			index = self._dbusMulitService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusMulitService['/UpdateIndex'] = index
			
		if self.useGensetDevice:
			logger.info("==> writing genset data")
			self._dbusGensetService["/Engine/Load"] = round(self.inverter.a03loadPercent, 2)
			
			index = self._dbusGensetService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusGensetService['/UpdateIndex'] = index

