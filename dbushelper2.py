#!/usr/bin/python3

import dbus
import sys
import os

import asyncio
import platform

# Victron packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusService
from dbusmonitor import DbusMonitor

dbusMonitor = None

class DbusHelper2:
    debug = False
    ubit = None
    state = None
    connected = None
    _dbsmonitor = None
    _tankService = None
    _vebusService = None
    _batteryService = None
    _solarchargerService = None
    bus = None
    device = None
    mngr = None
    adapter = None

    def __init__(self):
        dummy = {'code': None, 'whenToLog': 'configChange', 'accessLevel': None}
        dbus_tree = {
            'com.victronenergy.solarcharger': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Dc/0/Voltage': dummy,
                '/Dc/0/Current': dummy,
                '/Load/I': dummy,
                '/FirmwareVersion': dummy},
            'com.victronenergy.pvinverter': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Ac/L1/Power': dummy,
                '/Ac/L2/Power': dummy,
                '/Ac/L3/Power': dummy,
                '/Position': dummy,
                '/ProductId': dummy},
            'com.victronenergy.battery': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/DeviceInstance': dummy,
                '/Dc/0/Voltage': dummy,
                '/Dc/1/Voltage': dummy,
                '/Dc/0/Current': dummy,
                '/Dc/0/Power': dummy,
                '/Soc': dummy,
                '/Sense/Current': dummy,
                '/TimeToGo': dummy,
                '/ConsumedAmphours': dummy,
                '/ProductId': dummy,
                '/CustomName': dummy},
            'com.victronenergy.vebus': {
                '/Ac/ActiveIn/ActiveInput': dummy,
                '/Ac/ActiveIn/L1/P': dummy,
                '/Ac/ActiveIn/L2/P': dummy,
                '/Ac/ActiveIn/L3/P': dummy,
                '/Ac/Out/L1/P': dummy,
                '/Ac/Out/L2/P': dummy,
                '/Ac/Out/L3/P': dummy,
                '/Connected': dummy,
                '/ProductId': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Mode': dummy,
                '/State': dummy,
                '/Dc/0/Voltage': dummy,
                '/Dc/0/Current': dummy,
                '/Dc/0/Power': dummy,
                '/Soc': dummy},
            'com.victronenergy.charger': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Dc/0/Voltage': dummy,
                '/Dc/0/Current': dummy,
                '/Dc/1/Voltage': dummy,
                '/Dc/1/Current': dummy,
                '/Dc/2/Voltage': dummy,
                '/Dc/2/Current': dummy},
            'com.victronenergy.grid': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/ProductId': dummy,
                '/DeviceType': dummy,
                '/Ac/L1/Power': dummy,
                '/Ac/L2/Power': dummy,
                '/Ac/L3/Power': dummy},
            'com.victronenergy.genset': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/ProductId': dummy,
                '/DeviceType': dummy,
                '/Ac/L1/Power': dummy,
                '/Ac/L2/Power': dummy,
                '/Ac/L3/Power': dummy,
                '/StarterVoltage': dummy},
            'com.victronenergy.settings': {
                '/Settings/SystemSetup/AcInput1': dummy,
                '/Settings/SystemSetup/AcInput2': dummy,
                '/Settings/CGwacs/RunWithoutGridMeter': dummy,
                '/Settings/System/TimeZone': dummy},
            'com.victronenergy.temperature': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy},
            'com.victronenergy.tank': {
                '/Capacity': dummy,
                '/FluidType': dummy,
                '/Level': dummy,
                '/Remaining': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Status': dummy},
            'com.victronenergy.inverter': {
                '/Connected': dummy,
                '/ProductName': dummy,
                '/Mgmt/Connection': dummy,
                '/Dc/0/Voltage': dummy,
                '/Dc/0/Current': dummy,
                '/Ac/Out/L1/P': dummy,
                '/Ac/Out/L1/V': dummy,
                '/Ac/Out/L1/I': dummy,
                '/Yield/Power': dummy,
                '/Soc': dummy,
            }
        }
        global dbusMonitor
        if dbusMonitor is None:
            self._dbusmonitor = self._create_dbus_monitor(dbus_tree, valueChangedCallback=self._dbus_value_changed,
                                                          deviceAddedCallback=self._device_added,
                                                          deviceRemovedCallback=self._device_removed)
            if self.debug:
                print('dbsmonitor')
                print(self._dbusmonitor)
            dbusMonitor = self._dbusmonitor
        else:
            self._dbusmonitor = dbusMonitor
            if self.debug:
                print('reusing dbusmonitor')

        print('Starting Main ...')
        self._tankService = self._get_service_having_lowest_instance('com.victronenergy.tank')
        self._vebusService = self._get_service_having_lowest_instance('com.victronenergy.vebus')
        self._batteryService = self._get_service_having_lowest_instance('com.victronenergy.battery')
        self._solarchargerService = self._get_service_having_lowest_instance('com.victronenergy.solarcharger')

    def getDataFromOutback(self, inverterData):
        self.writeToDbus(self._vebusService, '/Ac/Out/L1/P', inverterData)
        #self.writeToDbus(self._solarchargerService, '/Dc/0/Current', pvInputCurrent)
        #self.writeToDbus(self._solarchargerService, '/Yield/Power ', 10)
        #self.writeToDbus(self._solarchargerService, '/Pv/I', pvInputCurrent)
        #self.writeToDbus(self._solarchargerService, '/Load/I', pvInputCurrent)
        #self.writeToDbus(self._solarchargerService, '/Pv/V', pvInputVoltage)

    def writeToDbus(self, service, path, value):
        if self.debug:
            print(service)
            print(path)
            print(value)
        if service and self._dbusmonitor.get_value(service[0], path) is not None:
            if self.debug:
                print(self._dbusmonitor.get_value(service[0], path))
            self._dbusmonitor.set_value(service[0], path, value)

    def getValueFromDbus(self, service, path):
        return self._dbusmonitor.get_value(service[0], path)

    def _dbus_value_changed(self, dbusServiceName, dbusPath, dict, changes, deviceInstance):
        self._changed = True

        # Workaround because com.victronenergy.vebus is available even when there is no vebus product
        # connected.
        if (dbusPath in ['/Connected', '/ProductName', '/Mgmt/Connection'] or
                (dbusPath == '/State' and dbusServiceName.split('.')[0:3] == ['com', 'victronenergy', 'vebus'])):
            self._handleservicechange()

        # Track the timezone changes
        if dbusPath == '/Settings/System/TimeZone':
            tz = changes.get('Value')
            if tz is not None:
                os.environ['TZ'] = tz

    def _device_added(self, service, instance, do_service_change=True):
        if do_service_change:
            self._handleservicechange()

    def _device_removed(self, service, instance):
        self._handleservicechange()

    def _get_connected_service_list(self, classfilter=None):
        services = self._dbusmonitor.get_service_list(classfilter=classfilter)
        return services

    # returns a tuple (servicename, instance)
    def _get_first_connected_service(self, classfilter=None):
        services = self._get_connected_service_list(classfilter=classfilter)
        if len(services) == 0:
            return None
        return services.items()[0]

    # returns a tuple (servicename, instance)
    def _get_service_having_lowest_instance(self, classfilter=None):
        services = self._get_connected_service_list(classfilter=classfilter)
        if len(services) == 0:
            return None

        # sort the dict by value; returns list of tuples: (value, key)
        s = sorted((value, key) for (key, value) in services.items())
        return (s[0][1], s[0][0])

    def _get_readable_service_name(self, servicename):
        return '%s on %s' % (
            self._dbusmonitor.get_value(servicename, '/ProductName'),
            self._dbusmonitor.get_value(servicename, '/Mgmt/Connection'))

    def _get_instance_service_name(self, service, instance):
        return '%s/%s' % ('.'.join(service.split('.')[0:3]), instance)

    def _handleservicechange(self):
        self._changed = True

    def _create_dbus_monitor(self, *args, **kwargs):
        return DbusMonitor(*args, **kwargs)

    def _create_settings(self, *args, **kwargs):
        bus = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()
        return SettingsDevice(bus, *args, timeout=10, **kwargs)

    def _create_dbus_service(self):
        # dbusservice = VeDbusService('com.victronenergy.system')
        dbusservice = VeDbusService('dummyForNow')
        dbusservice.add_mandatory_paths(
            processname=__file__,
            processversion=softwareVersion,
            connection='data from other dbus processes',
            deviceinstance=0,
            productid=None,
            productname=None,
            firmwareversion=None,
            hardwareversion=None,
            connected=1)
        return dbusservice

class SystemBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)


class SessionBus(dbus.bus.BusConnection):
    def __new__(cls):
        return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)

