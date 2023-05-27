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
		
		# IMPORTING
		if hasVictronBMS:
			fromBmsDcVoltage = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Voltage')
			fromBmSDcCurrent = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Current')
			fromBmsDcPower = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Power')
			fromBmsDcSoc = VeDbusItemImport(self._dbusConnection, 'com.victronenergy.battery.ttyUSB0', '/Soc')
			#fromBmsDcTemperature = VeDbusItemImport(self._dbusConnection,'com.victronenergy.battery.ttyUSB0', '/Dc/0/Temperature')
		
		# ToDo complete values
		# no Soc available
		fromOutbackDcVoltage = self.inverter.a03batteryVoltage
		fromOutbackDcCurrent = self.inverter.a03batteryChargeCurrent
		
		fromOutbackAcInputGridVoltage = self.inverter.a03gridVoltage
		fromOutbackAcInputGridFrequency = self.inverter.a03gridFrequency
		
		fromOutbackAcOutputApparentPower = self.inverter.a03acApparentPower
		fromOutbackAcOutputActivePower = self.inverter.a03acActivePower
		fromOutbackAcOutputVoltage = self.inverter.a03acOutputVoltage
		fromOutbackAcOutputCurrent = self.inverter.a03acOutputCurrent
		fromOutbackAcOutputFrequency = self.inverter.a03acFrequency
		fromOutbackAcOutputLoadPercentage = self.inverter.a03loadPercent
		
		fromOutbackPvInputPower = self.inverter.a11pvInputPower
		formOutbackPvInputCurrent = self.inverter.a11pvInputCurrent
		fromOutbackPcInputVoltage = self.inverter.a11pvInputVoltage
		
		
		# CALCULATED
		calculatedOutbackSelfconsumption = fromOutbackAcOutputApparentPower - fromOutbackAcOutputActivePower
		
		
		# EXPORTING
		toVictronDcVoltage = fromBmsDcVoltage
		toVictronDcCurrent = fromBmSDcCurrent
		toVictronDcPower = fromBmsDcPower
		toVictronDcSoc = fromBmsDcSoc
		# toVictronDcTemperature = fromBmsDcTemperature
			
###########################
# MULTI
###########################				
		if self.useMultiDevice:
			logger.info("==> writing multi data ")
			if hasVictronBMS:
				self._dbusMulitService["/Dc/0/Voltage"] = round(toVictronDcVoltage,2)
				self._dbusMulitService["/Dc/0/Current"] = round(toVictronDcCurrent,2)
				self._dbusMulitService["/Soc"] = round(toVictronDcSoc, 2)
				# self._dbusMulitService["/Dc/0/Temperature"] = round(toVictronDcTemperature,2)
				
			# Additional values 
			selfConsumption = self.inverter.a03acApparentPower - self.inverter.a03acActivePower
			currentBatteryValue = self._importedDbusValues["/Dc/0/Power"].get_value()
			
			# AC Input measurements:
			self._dbusMulitService["/Ac/In/1/L1/P"] = 0 # round(self.inverter.a03acApparentPower, 2)      # <- Real power of AC IN1 onL1
			self._dbusMulitService["/Ac/In/1/L1/I"] = 0 # round(self.inverter.a03acOutputCurrent, 2)           # <- Current of AC IN1 on L1
			self._dbusMulitService["/Ac/In/1/L1/V"] = round(self.inverter.a03gridVoltage, 2)               # <- Voltage of AC IN1 on L1
			self._dbusMulitService["/Ac/In/1/L1/F"] = round(self.inverter.a03gridFrequency, 2)             # <- Frequency of AC IN1 on L1
			
			# AC Output measurements:
			self._dbusMulitService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)    # <- Frequency of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)          # <- Voltage of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)          # <- Current of AC OUT1 on L1
			self._dbusMulitService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)        # <- Real power of AC OUT1 on L1
			
			# For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
			# Generic alarms:
			self._dbusMulitService["/Alarms/LowSoc"] = 0                                               # <- Low state of charge
			self._dbusMulitService["/Alarms/LowVoltage"] = 0                                           # <- Low battery voltage
			#self._dbusMulitService["/Alarms/HighVoltage "] = 0                                         # <- High battery voltage
			self._dbusMulitService["/Alarms/LowVoltageAcOut"] = 0                                      # <- Low AC Out voltage
			self._dbusMulitService["/Alarms/HighVoltageAcOut"] = 0                                     # <- High AC Out voltage
			self._dbusMulitService["/Alarms/HighTemperature"] = 0                                      # <- High device temperature
			self._dbusMulitService["/Alarms/Overload"] = 0                                             # <- Inverter overload
			self._dbusMulitService["/Alarms/Ripple"] = 0                                               # <- High DC ripple
			
			# Additional Data
			self._dbusMulitService['/Mode'] = 3                                                        # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
			self._dbusMulitService['/State'] = 9                                                       # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External control          # <- State of charge of internal battery monitor
			
			self._dbusMulitService['/Energy/AcIn1ToAcOut'] = 0 # später generator
			self._dbusMulitService['/Energy/AcIn1ToInverter'] = 0 # round(self.inverter.a11pvInputVoltage, 2)
			self._dbusMulitService['/Energy/AcIn2ToAcOut'] = round(self.inverter.a11pvInputVoltage/1000, 2)
			# self._dbusMulitService['/Energy/AcIn2ToInverter'] = round(self.inverter.a11pvInputVoltage, 2)
			self._dbusMulitService['/Energy/AcOutToAcIn1'] = 0 # round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusMulitService['/Energy/AcOutToAcIn2'] = round(self.inverter.a11pvInputVoltage, 2)
			self._dbusMulitService['/Energy/InverterToAcIn1'] = 0 # round(self.inverter.a11pvInputVoltage, 2)
			# self._dbusMulitService['/Energy/InverterToAcIn2'] = round(self.inverter.a11pvInputVoltage, 2)
			
			if currentBatteryValue > 0:
				# Batterie erhält Strom
				fromYield = self.inverter.a03acActivePower
				self._dbusMulitService['/Energy/AcIn2ToAcOut'] = round(fromYield/1000, 2) # direkt von pv in ac
				self._dbusMulitService['/Energy/OutToInverter'] =  currentBatteryValue/1000 # round(self.inverter.a11pvInputVoltage, 2)
				logger.info("==> Alles von PV mit " + str(fromYield))
				logger.info("==> Batterie wird zusätzlich geladen mit " + str(currentBatteryValue))
			
			# wenn batterie 0 weder gibt noch nimmt
			elif currentBatteryValue == 0:
				# wenn wir strom verbrauchen
				if self.inverter.a03acActivePower > 0:
					fromYield = self.inverter.a03acActivePower
					logger.info("==> Alles von PV mit " + str(fromYield))
					self._dbusMulitService['/Energy/AcIn2ToAcOut'] = round(fromYield/1000, 2) # direkt von pv in ac
				else:
					logger.info("==> new situation, needs to be solved Case C")
			
			# wenn wir strom aus der batterie ziehen z.b -10 Watts
			elif currentBatteryValue < 0:
				# wenn der strom aus der batterie kleiner ist als der strom den wir verbrauchen z.b. -10 Watts / 70 Watts => DIFF 60 Watts
				# muss der rest direkt aus der pv anlage kommen
				if currentBatteryValue < self.inverter.a03acActivePower:
					completePower = self.inverter.a03acActivePower
					fromBattery = currentBatteryValue * -1 # is a negative value and will be substracted
					fromYield = completePower - fromBattery
					logger.info("==> Batterie hilf aus mit " + str(fromBattery) + "/" + str(completePower) + "/" + str(currentBatteryValue))
					logger.info("==> Rest von PV mit " + str(fromYield))
					self._dbusMulitService['/Energy/InverterToAcOut'] =  round(fromBattery/1000, 2) # von batterie zu ac
					self._dbusMulitService['/Energy/AcIn2ToAcOut'] = round(fromYield/1000, 2) # direkt von pv in ac
				else:
					logger.info("==> new situation, needs to be solved Case B")
			else:
				logger.info("==> new situation, needs to be solved Case A")
				
			# PV tracker information:
			self._dbusMulitService['/NrOfTrackers'] = 1   
			logger.info("==> Werte  " + str(currentBatteryValue) + "/" + str(self.inverter.a11pvInputPower) + "/" + str(self.inverter.a03acActivePower))
			if (currentBatteryValue + self.inverter.a11pvInputPower) < self.inverter.a03acActivePower:
				logger.info("PV Wert zu niedrig trotz output ohne genügend abnahme von batterie")
				self._dbusMulitService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)    
				calculatedPvPower = self.inverter.a03acActivePower - (currentBatteryValue * -1)
				self._dbusMulitService['/Pv/P'] = round(calculatedPvPower,2)
				self._dbusMulitService['/Pv/I'] = round(calculatedPvPower / self.inverter.a11pvInputVoltage, 2)
				self._dbusMulitService['/Yield/Power'] = round(calculatedPvPower, 2) 
			else: 
				self._dbusMulitService['/Pv/I'] = round(self.inverter.a11pvInputCurrent, 2)                # <- PV array voltage from 1st tracker
				self._dbusMulitService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
				self._dbusMulitService['/Pv/P'] = round(self.inverter.a11pvInputPower, 2)                  # <- PV array power (Watts) from 1st tracker
				self._dbusMulitService['/Yield/Power'] = round(self.inverter.a11pvInputPower, 2)           # <- PV array power (Watts)
				# self._dbusMulitService['/Yield/User'] = round(self.inverter.a11pvInputPower, 2)            # <- Total kWh produced (user resettable)
			
				
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

