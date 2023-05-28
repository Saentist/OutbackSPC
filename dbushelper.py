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
		self.useMultiDevice = True
		self.useGensetDevice = False
		
	def setup_vedbus(self):
		# formating
		_kwh = lambda p, v: (str(v) + 'KWh')    # lambda p, v: "{:0.1f}A".format(v)
		_a = lambda p, v: (str(v) + 'A')        # lambda p, v: "{:2.3f}A".format(v)
		_w = lambda p, v: (str(v) + 'W')        # lambda p, v: "{:0.0f}W".format(v)
		_v = lambda p, v: (str(v) + 'V')        # lambda p, v: "{:2.2f}V".format(v)
		_h = lambda p, v: (str(v) + 'Hz')        # lambda p, v: "{:2.2f}V".format(v)
		_ms = lambda p, v: (str(v) + 'ms')
		_p = lambda p, v: (str(v) + '%')
		
		short_port = self.inverter.port[self.inverter.port.rfind("/") + 1:]
				
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
			self._dbusMulitService.add_path("/Energy/OutToInverter", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/SolarToAcIn1", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/SolarToAcIn2", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/SolarToAcOut", None, writeable=True, )
			self._dbusMulitService.add_path("/Energy/SolarToBattery", None, writeable=True, )
			self._dbusMulitService.add_path('/Pv/V', None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path('/Pv/P', None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path('/Pv/I', None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
			self._dbusMulitService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
			self._dbusMulitService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path("/Dc/0/Temperature", 0, writeable=True, gettextcallback=_w, )
			self._dbusMulitService.add_path('/MppOperationMode', 2)
			self._dbusMulitService.add_path("/Ac/ActiveIn/ActiveInput", 0)
			self._dbusMulitService.add_path("/Ac/NumberOfPhases", 1)
			self._dbusMulitService.add_path("/Ac/NumberOfAcInputs", 1)
			self._dbusMulitService.add_path("/Ac/In/1/Type", 2) # <- AC IN1 type: 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)
			self._dbusMulitService.add_path('/NrOfTrackers', 1)
			self._dbusMulitService.add_path('/Mode', 3, writeable=True,)
			self._dbusMulitService.add_path('/State', 9, writeable=True,)
			self._dbusMulitService.add_path('/Soc', 0, writeable=True,)
			self._dbusMulitService.add_path("/Alarms/LowSoc", 0, writeable=True,)                                              # <- Low state of charge
			self._dbusMulitService.add_path("/Alarms/LowVoltage", 0, writeable=True,)                                         # <- Low battery voltage
			self._dbusMulitService.add_path("/Alarms/HighVoltage", 0, writeable=True,)                                       # <- High battery voltage
			self._dbusMulitService.add_path("/Alarms/LowVoltageAcOut", 0, writeable=True,)                                    # <- Low AC Out voltage
			self._dbusMulitService.add_path("/Alarms/HighVoltageAcOut", 0, writeable=True,)                                    # <- High AC Out voltage
			self._dbusMulitService.add_path("/Alarms/HighTemperature", 0, writeable=True,)                                     # <- High device temperature
			self._dbusMulitService.add_path("/Alarms/Overload", 0, writeable=True,)                                            # <- Inverter overload
			self._dbusMulitService.add_path("/Alarms/Ripple", 0, writeable=True,)  
			self._dbusMulitService.add_path('/UpdateIndex', 0, writeable=True,)
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
			self._dbusGensetService.add_path('/UpdateIndex', 0, writeable=True, )
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
			# self._importedDbusValues["/Dc/0/Temperature"] = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Temperature')

		###########
		# IMPORTING
		###########
		if hasVictronBMS:
			fromBmsDcVoltage = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Voltage').get_value()
			fromBmSDcCurrent = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Current').get_value()
			fromBmsDcPower = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Power').get_value()
			fromBmsDcSoc = VeDbusItemImport(self._dbusConnection, 'com.victronenergy.battery.ttyUSB0', '/Soc').get_value()
			#fromBmsDcTemperature = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Temperature').get_value()
		
		# ToDo complete values
		# no Soc available
		fromOutbackDcVoltage = self.inverter.a03batteryVoltage
		fromOutbackDcCurrent = self.inverter.a03batteryChargeCurrent
		
		fromOutbackAcInputGridPower = 0 # ToDo find out
		fromOutbackAcInputGridVoltage = 0 # ToDo find out
		fromOutbackAcInputGridVoltage = self.inverter.a03gridVoltage
		fromOutbackAcInputGridFrequency = self.inverter.a03gridFrequency
		
		fromOutbackAcOutputApparentPower = self.inverter.a03acApparentPower
		fromOutbackAcOutputActivePower = self.inverter.a03acActivePower
		fromOutbackAcOutputVoltage = self.inverter.a03acOutputVoltage
		fromOutbackAcOutputCurrent = self.inverter.a03acOutputCurrent
		fromOutbackAcOutputFrequency = self.inverter.a03acFrequency
		fromOutbackAcOutputLoadPercentage = self.inverter.a03loadPercent
		
		fromOutbackPvInputPower = self.inverter.a11pvInputPower
		fromOutbackPvInputCurrent = self.inverter.a11pvInputCurrent
		fromOutbackPvInputVoltage = self.inverter.a11pvInputVoltage
		
		###########
		# EXPORTING
		###########
		toVictronDcVoltage = fromBmsDcVoltage
		toVictronDcCurrent = fromBmSDcCurrent
		toVictronDcPower = fromBmsDcPower
		toVictronDcSoc = fromBmsDcSoc
		# toVictronDcTemperature = fromBmsDcTemperature
		
		toVictronAcInputGridPower = fromOutbackAcInputGridPower
		toVictronAcInputGridVoltage = fromOutbackAcInputGridVoltage
		toVictronAcInputGridVoltage = fromOutbackAcInputGridVoltage
		toVictronAcInputGridFrequency = fromOutbackAcInputGridFrequency
		
		toVictronAcOutputApparentPower = fromOutbackAcOutputApparentPower
		toVictronAcOutputActivePower = fromOutbackAcOutputActivePower
		toVictronAcOutputVoltage = fromOutbackAcOutputVoltage
		toVictronAcOutputCurrent = fromOutbackAcOutputCurrent
		toVictronAcOutputFrequency = fromOutbackAcOutputFrequency
		toVictronAcOutputLoadPercentage = fromOutbackAcOutputLoadPercentage
		
		toVictronPvInputPower = fromOutbackPvInputPower
		toVictronPvInputCurrent = fromOutbackPvInputCurrent
		toVictronPvInputVoltage = fromOutbackPvInputVoltage
		
		toVictronAlarmLowSoc = 0
		toVictronAlarmLowVoltage = 0
		toVictronAlarmHighVoltage = 0
		toVictronAlarmLowVoltageAcOut = 0
		toVictronAlarmHighVoltageAcOut = 0
		toVictronAlarmHighTemperture = 0
		toVictronAlarmOverload = 0
		toVictronAlarmRipple = 0
		
		toVictronMultiState = 9 # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External
		toVictronMultiMode = 3 # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
				
		toVictronEnergyAcIn1ToAcOut = 0
		toVictronEnergyAcIn1ToInverter = 0
		toVictronEnergyAcIn2ToAcOut = 0
		toVictronEnergyAcIn2ToInverter = 0
		toVictronEnergyAcOutToAcIn1 = 0
		toVictronEnergyAcOutToAcIn2 = 0
		toVictronEnergyInverterToAcIn1 = 0
		toVictronEnergyInverterToAcIn2 = 0
		toVictronEnergyInverterToAcOut = 0
		toVictronEnergyOutToInverter = 0
		toVictronEnergySolarToAcIn1 = 0
		toVictronEnergySolarToAcIn2 = 0
		toVictronEnergySolarToAcOut = 0
		toVictronEnergySolarToBattery = 0
	
		
		##########
		# CHANGING
		##########
		# PV ARRAY
		# battery discharge amount + pv input amount smaller than pv output amount => needs to correct pv output
		if (int(fromBmsDcPower) + int(fromOutbackPvInputPower)) < int(fromOutbackAcOutputActivePower):
			toVictronPvInputPower = fromOutbackAcOutputActivePower - (fromBmsDcPower * -1)
			toVictronPvInputCurrent = toVictronPvInputPower / toVictronPvInputVoltage
			if self.debug:
				logger.info("==> changing Pv Power to " + str(toVictronPvInputPower))
				logger.info("==> changing Pv Current to " + str(toVictronPvInputCurrent))
		
		# BATTERY
		# battery is charging
		if fromBmsDcPower > 0:
				toVictronEnergySolarToBattery = fromBmsDcPower
				toVictronEnergySolarToAcOut = fromOutbackAcOutputActivePower
				if self.debug:
					logger.info("==> charging battery with " + str(toVictronEnergySolarToBattery))
					logger.info("==> inverting from solar " + str(toVictronEnergySolarToAcOut))
			
		# no charging
		elif fromBmsDcPower == 0:
			if fromOutbackAcOutputActivePower > 0:
				toVictronEnergySolarToAcOut = fromOutbackAcOutputActivePower
				if self.debug:
					logger.info("==> inverting from solar " + str(toVictronEnergySolarToAcOut))
			else:
				logger.info("==> new situation, needs to be solved Case C")
			
		# battery is discharging -10 Watts
		elif fromBmsDcPower < 0:
			# wenn der strom aus der batterie kleiner ist als der strom den wir verbrauchen z.b. -10 Watts / 70 Watts => DIFF 60 Watts
			# muss der rest direkt aus der pv anlage kommen
			if fromBmsDcPower < fromOutbackAcOutputActivePower:
				toVictronEnergySolarToAcOut = fromOutbackAcOutputActivePower - (fromBmsDcPower * -1)
				toVictronEnergyInverterToAcOut = fromBmsDcPower * -1
				if self.debug:
					logger.info("==> discharging battery with " + str(toVictronEnergyInverterToAcOut))
					logger.info("==> inverting from solar " + str(toVictronEnergySolarToAcOut))
			else:
				logger.info("==> new situation, needs to be solved Case B")
		else:
			logger.info("==> new situation, needs to be solved Case A")
						
		###########################
		# WRITING
		###########################				
		if self.useMultiDevice:
			logger.info("==> writing multi data ")
			if hasVictronBMS:
				self._dbusMulitService["/Dc/0/Voltage"] = round(toVictronDcVoltage,2)
				self._dbusMulitService["/Dc/0/Current"] = round(toVictronDcCurrent,2)
				self._dbusMulitService["/Soc"] = round(toVictronDcSoc, 2)
				# self._dbusMulitService["/Dc/0/Temperature"] = round(toVictronDcTemperature,2)
				
			# AC Input measurements:
			self._dbusMulitService["/Ac/In/1/L1/P"] = round(toVictronAcInputGridPower, 2)
			self._dbusMulitService["/Ac/In/1/L1/I"] = round(toVictronAcInputGridVoltage, 2)
			self._dbusMulitService["/Ac/In/1/L1/V"] = round(toVictronAcInputGridVoltage, 2)
			self._dbusMulitService["/Ac/In/1/L1/F"] = round(toVictronAcInputGridFrequency, 2)
			
			# AC Output measurements:
			self._dbusMulitService["/Ac/Out/L1/P"] = round(toVictronAcOutputActivePower, 2)
			self._dbusMulitService["/Ac/Out/L1/V"] = round(toVictronAcOutputVoltage, 2)
			self._dbusMulitService["/Ac/Out/L1/I"] = round(toVictronAcOutputCurrent, 2)
			self._dbusMulitService["/Ac/Out/L1/F"] = round(toVictronAcOutputFrequency, 2)
			
			# For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
			# Generic alarms:
			self._dbusMulitService["/Alarms/LowSoc"] = toVictronAlarmLowSoc
			self._dbusMulitService["/Alarms/LowVoltage"] = toVictronAlarmLowVoltage
			#self._dbusMulitService["/Alarms/HighVoltage "] = toVictronAlarmHighVoltage
			self._dbusMulitService["/Alarms/LowVoltageAcOut"] = toVictronAlarmLowVoltageAcOut
			self._dbusMulitService["/Alarms/HighVoltageAcOut"] = toVictronAlarmHighVoltageAcOut
			self._dbusMulitService["/Alarms/HighTemperature"] = toVictronAlarmHighTemperture
			self._dbusMulitService["/Alarms/Overload"] = toVictronAlarmOverload
			self._dbusMulitService["/Alarms/Ripple"] = toVictronAlarmRipple
			
			# Additional Data
			self._dbusMulitService['/Mode'] = toVictronMultiMode
			self._dbusMulitService['/State'] = toVictronMultiState
			
			self._dbusMulitService['/Energy/AcIn1ToAcOut'] = round(toVictronEnergyAcIn1ToAcOut/1000, 2)
			self._dbusMulitService['/Energy/AcIn1ToInverter'] = round(toVictronEnergyAcIn1ToInverter/1000, 2)
			self._dbusMulitService['/Energy/AcIn2ToAcOut'] = round(toVictronEnergyAcIn2ToAcOut/1000, 2)
			self._dbusMulitService['/Energy/AcIn2ToInverter'] = round(toVictronEnergyAcIn2ToInverter, 2)
			self._dbusMulitService['/Energy/AcOutToAcIn1'] = round(toVictronEnergyAcOutToAcIn1/1000, 2)
			self._dbusMulitService['/Energy/AcOutToAcIn2'] = round(toVictronEnergyAcOutToAcIn2/1000, 2)
			self._dbusMulitService['/Energy/InverterToAcIn1'] = round(toVictronEnergyInverterToAcIn1/1000, 2)
			self._dbusMulitService['/Energy/InverterToAcIn2'] = round(toVictronEnergyInverterToAcIn2/1000, 2)
			self._dbusMulitService['/Energy/InverterToAcIn2'] = round(toVictronEnergyInverterToAcOut/1000, 2)
			self._dbusMulitService['/Energy/OutToInverter'] = round(toVictronEnergyOutToInverter/1000, 2)
			self._dbusMulitService['/Energy/SolarToAcIn1'] = round(toVictronEnergySolarToAcIn1/1000, 2)
			self._dbusMulitService['/Energy/SolarToAcIn2'] = round(toVictronEnergySolarToAcIn2/1000, 2)
			self._dbusMulitService['/Energy/SolarToAcOut'] = round(toVictronEnergySolarToAcOut/1000, 2)
			self._dbusMulitService['/Energy/SolarToBattery'] = round(toVictronEnergySolarToBattery/1000, 2)
				
			# PV tracker information:
			self._dbusMulitService['/NrOfTrackers'] = 1
			self._dbusMulitService['/Pv/P'] = round(toVictronPvInputPower,2)
			self._dbusMulitService['/Pv/I'] = round(toVictronPvInputCurrent, 2)
			self._dbusMulitService['/Pv/V'] = round(toVictronPvInputVoltage, 2) 
			self._dbusMulitService['/Yield/Power'] = round(toVictronPvInputPower, 2)  
						
			index = self._dbusMulitService['/UpdateIndex'] + 1  # increment index
			if index > 255:  # maximum value of the index
				index = 0  # overflow from 255 to 0
			self._dbusMulitService['/UpdateIndex'] = index
			
