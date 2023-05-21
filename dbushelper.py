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
    def __init__(self, inverter, devType, instance):
        self.inverter = inverter
        self.instance = instance
        self.error_count = 0
        self.devType = devType
        self.inverter.role = self.devType
        self._dbusService = VeDbusService("com.victronenergy." + devType + "." + self.inverter.port[self.inverter.port.rfind("/") + 1:], dbusconnection())

    def setup_vedbus(self):
        # formating
        _kwh = lambda p, v: (str(v) + 'KWh')    # lambda p, v: "{:0.1f}A".format(v)
        _a = lambda p, v: (str(v) + 'A')        # lambda p, v: "{:2.3f}A".format(v)
        _w = lambda p, v: (str(v) + 'W')        # lambda p, v: "{:0.0f}W".format(v)
        _v = lambda p, v: (str(v) + 'V')        # lambda p, v: "{:2.2f}V".format(v)
        _h = lambda p, v: (str(v) + 'Hz')        # lambda p, v: "{:2.2f}V".format(v)
        _ms = lambda p, v: (str(v or '') + "ms")
        _x = lambda p, v: (str(v or ''))

        # Set up dbus service and device instance
        # and notify of all the attributes we intend to update
        # This is only called once when a battery is initiated
        short_port = self.inverter.port[self.inverter.port.rfind("/") + 1:]
        logger.info("%s" % ("com.victronenergy." + self.devType + "." + short_port))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusService.add_path("/Mgmt/ProcessName", __file__)
        self._dbusService.add_path("/Mgmt/ProcessVersion", "Python " + platform.python_version())
        self._dbusService.add_path("/Mgmt/Connection", "Bluetooth " + self.inverter.port)

        # Create the mandatory objects
        self._dbusService.add_path("/DeviceInstance", self.instance)
        self._dbusService.add_path("/ProductId", 0x0)
        self._dbusService.add_path("/ProductName", "Outback - SPC III")
        self._dbusService.add_path("/FirmwareVersion", str(DRIVER_VERSION) + DRIVER_SUBVERSION)
        self.inverter.hardware_version = '3KW'
        self._dbusService.add_path("/HardwareVersion", self.inverter.hardware_version)
        self._dbusService.add_path("/Connected", 1)

        if self.devType == 'solarcharger':
            self.inverter.type = 'Solarcharger'
            self._dbusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Pv/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Pv/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path('/State', 0, writeable=True)
            self._dbusService.add_path('/Load/State', 0, writeable=True)
            self._dbusService.add_path('/Load/I', 0, writeable=True)
            self._dbusService.add_path('/ErrorCode', 0)
            self._dbusService.add_path('/Yield/Power', 0, writeable=True)  # Actual input power (Watts)
            self._dbusService.add_path('/Yield/User', 0)  # Total kWh produced (user resettable)
            self._dbusService.add_path('/Yield/System', 0)  # Total kWh produced (not resettable)
            self._dbusService.add_path('/Mode', 0, writeable=True)
            self._dbusService.add_path('/MppOperationMode', 2)

        if self.devType == 'pvinverter':
            self.inverter.type = 'PV Inverter'
            self._dbusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Pv/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Pv/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path('/State', 0, writeable=True)
            self._dbusService.add_path('/Load/State', 0, writeable=True)
            self._dbusService.add_path('/Load/I', 0, writeable=True)
            self._dbusService.add_path('/ErrorCode', 0)
            self._dbusService.add_path('/Yield/Power', 0, writeable=True)  # Actual input power (Watts)
            self._dbusService.add_path('/Yield/User', 0)  # Total kWh produced (user resettable)
            self._dbusService.add_path('/Yield/System', 0)  # Total kWh produced (not resettable)
            self._dbusService.add_path('/Mode', 0, writeable=True)
            self._dbusService.add_path('/MppOperationMode', 2)

        elif self.devType == 'inverter':
            self.inverter.type = 'Inverter'
            self._dbusService.add_path('/Mode', 2)
            self._dbusService.add_path('/State', 9)
            self._dbusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )

        elif self.devType == 'vebus':
            self.inverter.type = 'vebus'
            self._dbusService.add_path("/Ac/State/IgnoreAcIn1", 0)  # 0 = AcIn1 is not ignored; 1 = AcIn1 is being ignored (by assistant configuration).
            self._dbusService.add_path("/Settings/SystemSetup/AcInput1", 2)  # 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)
            self._dbusService.add_path("/Ac/PowerMeasurementType", 2)  #  0 = Apparent power only -> under the /P paths, apparent power is published.
                                                                       #  1 = Real power, but only measured by phase masters, and not synced in time. (And multiplied by number of units in parallel)
                                                                       #  2 = Real power, from all devices, but at different points in time
                                                                       #  3 = Real power, at the same time snapshotted, but only by the phase masters and then multiplied by number of units in parallel.
                                                                       #  4 = Real power, from all devices and at snaphotted at the same moment.
            self._dbusService.add_path("/Ac/ActiveIn/ActiveInput", 0)
            self._dbusService.add_path("/Ac/In/1/CurrentLimit", 0)
            self._dbusService.add_path("/Ac/In/1/CurrentLimitIsAdjustable", None, writeable=True, gettextcallback=_w, )  # <- 0 when inverting, 1 when connected to an AC in
            self._dbusService.add_path("/Ac/ActiveIn/L1", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/ActiveIn/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/ActiveIn/L1/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/ActiveIn/L1/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Ac/ActiveIn/L1/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Ac/ActiveIn/L1/F", None, writeable=True, gettextcallback=_h, )
            self._dbusService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Ac/Out/L1/F", None, writeable=True, gettextcallback=_h, )
            self._dbusService.add_path('/Pv/I', None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path('/Pv/V', None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path('/Pv/P', None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Mode", 3, writeable=True,)  #  1=Charger Only;2=Inverter Only;3=On;4=Off
            self._dbusService.add_path("/ModeIsAdjustable", 3, writeable=True,)  #  0. Switch position cannot be controlled remotely (typically because a VE.Bus BMS is present).
                                                                                   #  1. Switch position can be controlled remotely
            self._dbusService.add_path('/State', 9, writeable=True, )       #  0=Off;1=Low Power Mode;2=Fault;3=Bulk;4=Absorption;5=Float;
                                                                            #  6=Storage;7=Equalize;8=Passthru;9=Inverting;10=Power assist;
                                                                            #  11=Power supply mode;252=External control
            self._dbusService.add_path('/VebusChargeState', 9, writeable=True, )        # <- 1. Bulk
                                                                                        #  2. Absorption
                                                                                        #  3. Float
                                                                                        #  4. Storage
                                                                                        #  5. Repeat absorption
                                                                                        #  6. Forced absorption
                                                                                        #  7. Equalise
                                                                                        #  8. Bulk stopped
            self._dbusService.add_path('/VebusSetChargeState', 9, writeable=True, )     #  1. Force to Equalise. 1 hour 1, 2 or 4 V above absorption (12/24/48V). Charge current is limited to 1/4 of normal value. Will be followed by a normal 24-hour float state.
                                                                                        #  2. Force to Absorption, for maximum absorption time. Will be followed by a normal 24-hour float state.
                                                                                        #  3. Force to Float, for 24 hours. (from "Interfacing with VE.Bus products – MK2 Protocol" doc)

            # LEDs: 0 = Off, 1 = On, 2 = Blinking, 3 = Blinking inverted
            self._dbusService.add_path('/Leds/Mains', 1)
            self._dbusService.add_path('/Leds/Bulk', 0)
            self._dbusService.add_path('/Leds/Absorption', 0)
            self._dbusService.add_path('/Leds/Float', 0)
            self._dbusService.add_path('/Leds/Inverter', 0)
            self._dbusService.add_path('/Leds/Overload', 0)
            self._dbusService.add_path('/Leds/LowBattery', 0)
            self._dbusService.add_path('/Leds/Temperature', 0)


        elif self.devType == 'multi':
            self.inverter.type = 'multi'
            self._dbusService.add_path("/Yield/Power", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Yield/User", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Yield/System", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/In/1/L1/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/In/1/L1/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Ac/In/1/L1/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Ac/In/1/L1/F", None, writeable=True, gettextcallback=_h, )
            self._dbusService.add_path("/Ac/Out/L1/P", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path("/Ac/Out/L1/V", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Ac/Out/L1/I", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Ac/Out/L1/F", None, writeable=True, gettextcallback=_h, )
            self._dbusService.add_path('/Pv/V', None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path('/Pv/P', None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path('/Pv/I', None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Dc/0/Voltage", None, writeable=True, gettextcallback=_v, )
            self._dbusService.add_path("/Dc/0/Current", None, writeable=True, gettextcallback=_a, )
            self._dbusService.add_path("/Dc/0/Power", None, writeable=True, gettextcallback=_w, )
            self._dbusService.add_path('/MppOperationMode', 1, writeable=True,)
            self._dbusService.add_path("/Ac/ActiveIn/ActiveInput", 0)
            self._dbusService.add_path("/Ac/NumberOfPhases", 1)
            self._dbusService.add_path("/Ac/NumberOfAcInputs", 1)
            self._dbusService.add_path("/Ac/In/1/Type", 2)
            self._dbusService.add_path('/NrOfTrackers', 1)
            self._dbusService.add_path('/Mode', 3, writeable=True,)
            self._dbusService.add_path('/State', 9, writeable=True,)
            self._dbusService.add_path('/UpdateIndex', 0, writeable=True, gettextcallback=_x,)

        else:
            self.inverter.type = 'Unknown'

        # muss am schluss stehen da der inverter.type gesetzt sein muss
        self._dbusService.add_path("/CustomName", "Outback " + self.inverter.type + "", writeable=True)

        # ungenutzte Parameter

        # self._dbusService.add_path("/Hub/ChargeVoltage", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}V".format(v), )
        # self._dbusService.add_path("/Load/I", None, writeable=True, gettextcallback=lambda p, v: "{:2.2f}A".format(v), )
        # self._dbusService.add_path("/Ac/L1/Power", None, writeable=True, gettextcallback=lambda p, v: "{:0.0f}W".format(v), )

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
            else:
                self.error_count += 1
                print('error' + str(self.error_count))
                # If the battery is offline for more than 10 polls (polled every second for most batteries)
                if self.error_count >= 10:
                    self.inverter.online = False
                    print('inverter seems to be offline')
                # Has it completely failed
                if self.error_count >= 60:
                    print('loop quited')
                    loop.quit()
        except:
            traceback.print_exc()
            loop.quit()

    def publish_dbus(self):
        logger.info("Publishing to dbus")
        print('devType=' + self.devType)
        if self.devType == 'solarcharger':
            # Update SOC, DC and System items
            # print('solarcharger 1')
            self._dbusService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Dc/0/Power"] = round(self.inverter.a11pvInputPower, 2)
            self._dbusService["/Yield/Power"] = round(self.inverter.a11pvInputPower, 2)
            self._dbusService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
            # print('solarcharger 2')

        if self.devType == 'pvinverter':
            # Update SOC, DC and System items
            # print('solarcharger 1')
            self._dbusService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Dc/0/Power"] = round(self.inverter.a11pvInputPower, 2)
            self._dbusService["/Yield/Power"] = round(self.inverter.a11pvInputPower, 2)
            self._dbusService["/Pv/I"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Pv/V"] = round(self.inverter.a11pvInputVoltage, 2)
            # print('solarcharger 2')

        if self.devType == 'vebus':
            # AC Input measurements:
            # self._dbusService["/Ac/In/1/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)                                               # <- Real power of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)                                                # <- Current of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/V"] = round(self.inverter.a03gridVoltage, 2)               # <- Voltage of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/F"] = round(self.inverter.a03gridFrequency, 2)             # <- Frequency of AC IN1 on L1

            # AC Input settings:
            # self._dbusService["/Ac/In/1/Type"] = 2                                                  # <- AC IN1 type: 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)

            # AC Output measurements:
            # self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)    # <- Frequency of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)    # <- Frequency of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)          # <- Voltage of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)          # <- Current of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)        # <- Real power of AC OUT1 on L1

            # self._dbusService["/Ac/ActiveIn/ActiveInput"] = 1                                       # <- Active input: 0 = ACin-1, 1 = ACin-2,
            # self._dbusService["/Ac/NumberOfPhases"] = 1
            # self._dbusService["/Ac/NumberOfAcInputs"] = 1

            # For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
            # Generic alarms:
            # self._dbusService["/Alarms/LowSoc"] = 0                                               # <- Low state of charge
            # self._dbusService["/Alarms/LowVoltage"] = 0                                           # <- Low battery voltage
            # self._dbusService["/Alarms/HighVoltage "] = 0                                         # <- High battery voltage
            # self._dbusService["/Alarms/LowVoltageAcOut"] = 0                                      # <- Low AC Out voltage
            # self._dbusService["/Alarms/HighVoltageAcOut"] = 0                                     # <- High AC Out voltage
            # self._dbusService["/Alarms/HighTemperature"] = 0                                      # <- High device temperature
            # self._dbusService["/Alarms/Overload"] = 0                                             # <- Inverter overload
            # self._dbusService["/Alarms/Ripple"] = 0                                               # <- High DC ripple

            # Battery Values
            # self._dbusService["/Dc/0/Voltage"] = 1  # round(self.inverter.a11pvInputVoltage, 2)        # <- Battery Voltage
            # self._dbusService["/Dc/0/Current"] = 2  # round(self.inverter.a11pvInputCurrent, 2)        # <- Battery current in Ampere, positive when charging
            # self._dbusService["/Dc/0/Power"] = 2 #  round(self.inverter.a11pvInputPower, 2)            # <- Battery Power
            # self._dbusService["/Dc/0/Temperature "] = round(self.inverter.a11pvInputPower, 2)     # <- Battery temperature in degrees Celsius

            # Additional Data
            # self._dbusService['/Mode'] = 3                                                          # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
            # self._dbusService['/State'] = 252                                                       # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External control
            # self._dbusService['/Soc'] = 100                                                       # <- State of charge of internal battery monitor

            # PV tracker information:
            # self._dbusService['/NrOfTrackers'] = 1                                                  # <- number of trackers
            self._dbusService['/Pv/I'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
            self._dbusService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
            self._dbusService['/Pv/P'] = round(self.inverter.a11pvInputPower, 2)                  # <- PV array power (Watts) from 1st tracker
            self._dbusService['/Yield/Power'] = round(self.inverter.a11pvInputPower, 2)                                                # <- PV array power (Watts)
            # self._dbusService['/Yield/User'] = 1                                                  # <- Total kWh produced (user resettable)
            # self._dbusService['/Yield/System'] = 1                                                # <- Total kWh produced (not resettable)
            # self._dbusService['/MppOperationMode'] = 1                                              # <- 0 = Off 1 = Voltage or Current limited 2 = MPPT Tracker active

        if self.devType == 'multi':
            # AC Input measurements:
            # self._dbusService["/Ac/In/1/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)                                               # <- Real power of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)                                                # <- Current of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/V"] = round(self.inverter.a03gridVoltage, 2)               # <- Voltage of AC IN1 on L1
            # self._dbusService["/Ac/In/1/L1/F"] = round(self.inverter.a03gridFrequency, 2)             # <- Frequency of AC IN1 on L1

            # AC Input settings:
            # self._dbusService["/Ac/In/1/Type"] = 2                                                  # <- AC IN1 type: 0 (Not used), 1 (Grid), 2(Generator), 3(Shore)

            # AC Output measurements:
            # self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acApparentPower - 30, 2)    # <- Frequency of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower, 2)    # <- Frequency of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)          # <- Voltage of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)          # <- Current of AC OUT1 on L1
            self._dbusService["/Ac/Out/L1/F"] = round(self.inverter.a03acFrequency, 2)        # <- Real power of AC OUT1 on L1

            # self._dbusService["/Ac/ActiveIn/ActiveInput"] = 1                                       # <- Active input: 0 = ACin-1, 1 = ACin-2,
            # self._dbusService["/Ac/NumberOfPhases"] = 1
            # self._dbusService["/Ac/NumberOfAcInputs"] = 1

            # For all alarms: 0 = OK; 1 = Warning; 2 = Alarm
            # Generic alarms:
            # self._dbusService["/Alarms/LowSoc"] = 0                                               # <- Low state of charge
            # self._dbusService["/Alarms/LowVoltage"] = 0                                           # <- Low battery voltage
            # self._dbusService["/Alarms/HighVoltage "] = 0                                         # <- High battery voltage
            # self._dbusService["/Alarms/LowVoltageAcOut"] = 0                                      # <- Low AC Out voltage
            # self._dbusService["/Alarms/HighVoltageAcOut"] = 0                                     # <- High AC Out voltage
            # self._dbusService["/Alarms/HighTemperature"] = 0                                      # <- High device temperature
            # self._dbusService["/Alarms/Overload"] = 0                                             # <- Inverter overload
            # self._dbusService["/Alarms/Ripple"] = 0                                               # <- High DC ripple

            # Battery Values
            self._dbusService["/Dc/0/Voltage"] = 1  # round(self.inverter.a11pvInputVoltage, 2)        # <- Battery Voltage
            self._dbusService["/Dc/0/Current"] = 2  # round(self.inverter.a11pvInputCurrent, 2)        # <- Battery current in Ampere, positive when charging
            self._dbusService["/Dc/0/Power"] = 2 #  round(self.inverter.a11pvInputPower, 2)            # <- Battery Power
            # self._dbusService["/Dc/0/Temperature "] = round(self.inverter.a11pvInputPower, 2)     # <- Battery temperature in degrees Celsius

            # Additional Data
            # self._dbusService['/Mode'] = 3                                                          # <- Position of the switch. 1=Charger Only;2=Inverter Only;3=On;4=Off
            # self._dbusService['/State'] = 252                                                       # <- Charger state 0=Off 2=Fault 3=Bulk 4=Absorption 5=Float 6=Storage 7=Equalize 8=Passthrough 9=Inverting 245=Wake-up 25-=Blocked 252=External control
            # self._dbusService['/Soc'] = 100                                                       # <- State of charge of internal battery monitor

            # PV tracker information:
            # self._dbusService['/NrOfTrackers'] = 1                                                  # <- number of trackers
            self._dbusService['/Pv/I'] = round(self.inverter.a11pvInputCurrent, 2)                # <- PV array voltage from 1st tracker
            self._dbusService['/Pv/V'] = round(self.inverter.a11pvInputVoltage, 2)                # <- PV array voltage from 1st tracker
            self._dbusService['/Pv/P'] = round(self.inverter.a11pvInputPower, 2)                  # <- PV array power (Watts) from 1st tracker
            self._dbusService['/Yield/Power'] = round(self.inverter.a11pvInputPower, 2)                                                # <- PV array power (Watts)
            # self._dbusService['/Yield/User'] = 97                                                  # <- Total kWh produced (user resettable)
            # self._dbusService['/Yield/System'] = 96                                                # <- Total kWh produced (not resettable)
            # self._dbusService['/MppOperationMode'] = 1

            index = self._dbusService['/UpdateIndex'] + 1  # increment index
            if index > 255:  # maximum value of the index
                index = 0  # overflow from 255 to 0
            self._dbusService['/UpdateIndex'] = index

        if self.devType == 'inverter':
            # print('grid 1')
            self._dbusService["/Dc/0/Voltage"] = round(self.inverter.a11pvInputVoltage, 2)
            self._dbusService["/Dc/0/Current"] = round(self.inverter.a11pvInputCurrent, 2)
            self._dbusService["/Ac/Out/L1/P"] = round(self.inverter.a03acActivePower - 30, 2)
            self._dbusService["/Ac/Out/L1/V"] = round(self.inverter.a03acOutputVoltage, 2)
            self._dbusService["/Ac/Out/L1/I"] = round(self.inverter.a03acOutputCurrent, 2)
            # self._dbusService["/Yield/Power"] = round(1234, 2) # ist die summe die von der PV Anlage kommt errechnet sich automatisch
            # print('grid 2')

        # logger.debug("logged to dbus [%s]" % str(round(self.inverter.soc, 2)))
