from bluepy.btle import Peripheral, DefaultDelegate, BTLEException, BTLEDisconnectError
from threading import Thread, Lock
from inverter import Inverter
from utils import *
import utils
import time
import binascii
import struct

# QPIGS
# ac_input_frequency              50.0            Hz
# ac_input_voltage                235.7           V
# ac_output_active_power          940             W
# ac_output_apparent_power        942             VA
# ac_output_frequency             49.9            Hz
# ac_output_load                  31              %
# ac_output_voltage               229.9           V
# battery_capacity                100             %
# battery_charging_current        0               A
# battery_discharge_current       3               A
# battery_voltage                 28.9            V
# battery_voltage_from_scc        0.0             V
# bus_voltage                     449             V
# inverter_heat_sink_temperature  29              Deg_C
# is_ac_charging_on               0               True - 1/False - 0
# is_battery_voltage_to_steady_while_charging     0               True - 1/False - 0
# is_charging_on                  0               True - 1/False - 0
# is_charging_to_float            0               True - 1/False - 0
# is_configuration_changed        0               True - 1/False - 0
# is_load_on                      1               True - 1/False - 0
# is_reserved                     0               True - 1/False - 0
# is_sbu_priority_version_added   0               True - 1/False - 0
# is_scc_charging_on              0               True - 1/False - 0
# is_scc_firmware_updated         0               True - 1/False - 0
# is_switched_on                  1               True - 1/False - 0
# pv_input_current_for_battery    3.0             A
# pv_input_power                  909             W
# pv_input_voltage                298.9           V
# rsv1                            0               A
# rsv2                            0               A


# battery_voltage_from_scc        0.0             V
# inverter_heat_sink_temperature  29              Deg_C
# pv_input_current_for_battery    3.0             A
# pv_input_power                  909             W
# pv_input_voltage                298.9           V

class OutbackBtDev(DefaultDelegate, Thread):
    def __init__(self, address):
        DefaultDelegate.__init__(self)
        Thread.__init__(self)

        self.generalDataCallback = None
        self.generalDataP2Len = 0
        self.address = address
        self.interval = 5

        # Bluepy stuff
        self.bt = Peripheral()
        self.bt.setDelegate(self)

    def run(self):
        self.running = True
        connected = False
        while self.running:
            if not connected:
                try:
                    logger.info('Connecting ' + self.address)
                    self.bt.connect(self.address, iface=0)
                    logger.info('Connected ' + self.address)
                    connected = True
                except BTLEException as ex:
                    print(ex)
                    logger.info('Connection failed')
                    time.sleep(3)
                    continue
            try:
                #outbackService00001801 = self.bt.getServiceByUUID('00001801-0000-1000-8000-00805f9b34fb')
                outbackService00001810 = self.bt.getServiceByUUID('00001810-0000-1000-8000-00805f9b34fb')
                outbackService00001811 = self.bt.getServiceByUUID('00001811-0000-1000-8000-00805f9b34fb')
                outbackService0000180a = self.bt.getServiceByUUID('0000180a-0000-1000-8000-00805f9b34fb')

                # kann  nicht gelesen werden, daher auskommentiert
                #outbackService00001801a01 = outbackService00001801.getCharacteristics("00002a05-0000-1000-8000-00805f9b34fb")[0]
                #outbackService00001801a01Data = outbackService00001801a01.read()
                #print(outbackService00001801a01Data)

                outbackService00001810a01 = outbackService00001810.getCharacteristics("00002a01-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a02 = outbackService00001810.getCharacteristics("00002a02-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a03 = outbackService00001810.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a04 = outbackService00001810.getCharacteristics("00002a04-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a05 = outbackService00001810.getCharacteristics("00002a05-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a06 = outbackService00001810.getCharacteristics("00002a06-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a07 = outbackService00001810.getCharacteristics("00002a07-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a08 = outbackService00001810.getCharacteristics("00002a08-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a09 = outbackService00001810.getCharacteristics("00002a09-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a0a = outbackService00001810.getCharacteristics("00002a0a-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a0b = outbackService00001810.getCharacteristics("00002a0b-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a0c = outbackService00001810.getCharacteristics("00002a0c-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a0d = outbackService00001810.getCharacteristics("00002a0d-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a01Data = self.getExtractData(outbackService00001810a01.read())
                outbackService00001810a02Data = self.getExtractData(outbackService00001810a02.read())
                outbackService00001810a03Data = self.getExtractData(outbackService00001810a03.read())
                outbackService00001810a04Data = self.getExtractData(outbackService00001810a04.read())
                outbackService00001810a05Data = self.getExtractData(outbackService00001810a05.read())
                outbackService00001810a06Data = self.getExtractData(outbackService00001810a06.read())
                outbackService00001810a07Data = self.getExtractData(outbackService00001810a07.read())
                outbackService00001810a08Data = self.getExtractData(outbackService00001810a08.read())
                outbackService00001810a09Data = self.getExtractData(outbackService00001810a09.read())
                outbackService00001810a0aData = self.getExtractData(outbackService00001810a0a.read())
                outbackService00001810a0bData = self.getExtractData(outbackService00001810a0b.read())
                outbackService00001810a0cData = self.getExtractData(outbackService00001810a0c.read())
                outbackService00001810a0dData = self.getExtractData(outbackService00001810a0d.read())
                print(outbackService00001810a01Data)
                print(outbackService00001810a02Data)
                print(outbackService00001810a03Data)
                print(outbackService00001810a04Data)
                print(outbackService00001810a05Data)
                print(outbackService00001810a06Data)
                print(outbackService00001810a07Data)
                print(outbackService00001810a08Data)
                print(outbackService00001810a09Data)
                print(outbackService00001810a0aData)
                print(outbackService00001810a0bData)
                print(outbackService00001810a0cData)
                print(outbackService00001810a0dData)

                outbackService00001811a11 = outbackService00001811.getCharacteristics("00002a11-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001811a12 = outbackService00001811.getCharacteristics("00002a12-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001811a13 = outbackService00001811.getCharacteristics("00002a13-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001811a14 = outbackService00001811.getCharacteristics("00002a14-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001811a11Data = self.getExtractData(outbackService00001811a11.read())
                outbackService00001811a12Data = self.getExtractData(outbackService00001811a12.read())
                outbackService00001811a13Data = self.getExtractData(outbackService00001811a13.read())
                outbackService00001811a14Data = self.getExtractData(outbackService00001811a14.read())
                print(outbackService00001811a11Data)
                print(outbackService00001811a12Data)
                print(outbackService00001811a13Data)
                print(outbackService00001811a14Data)


                outbackService0000180aa29 = outbackService0000180a.getCharacteristics("00002a29-0000-1000-8000-00805f9b34fb")[0]
                outbackService0000180aa2a = outbackService0000180a.getCharacteristics("00002a2a-0000-1000-8000-00805f9b34fb")[0]
                outbackService0000180aa29Data = outbackService0000180aa29.read()
                outbackService0000180aa2aData = outbackService0000180aa2a.read()
                print(outbackService0000180aa29Data)
                print(outbackService0000180aa2aData)

                # read our data
                #outbackCharacteristicA03 = outbackService00001810.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")[0]
                #data = outbackCharacteristicA03.read()
                self.generalDataCallback(outbackService00001810a03Data, "a03")

                #outbackCharacteristicA11 = outbackService00001811.getCharacteristics("00002a11-0000-1000-8000-00805f9b34fb")[0]
                #data = outbackCharacteristicA11.read()
                self.generalDataCallback(outbackService00001811a11Data, "a11")

            except BTLEDisconnectError:
                logger.info('Disconnected')
                connected = False
                continue

    def connect(self):
        print('=> connect')
        self.start()

    def stop(self):
        self.running = False

    def addGeneralDataCallback(self, func):
        self.generalDataCallback = func

    def getExtractData(self, byteArrayObject):
        #print(byteArrayObject)
        tuple_of_shorts = struct.unpack('>' + 'h' * (len(byteArrayObject) // 2), byteArrayObject)
        #print(tuple_of_shorts)
        myResult = []
        for s in tuple_of_shorts:
            newVal = (((s >> 8) & 255) + (((s & 255) << 8) & 65280))
            resultValue = newVal  # * 0.01
            myResult.append(resultValue)
        return myResult

class OutbackBt(Inverter):
    def __init__(self, address):
        Inverter.__init__(self, 0, 0, address)

        self.type = ""
        self.debug = utils.OUTBACK_ADDRESS

        # Bluepy stuff
        self.bt = Peripheral()
        self.bt.setDelegate(self)

        self.mutex = Lock()
        self.a03Data = None
        self.a11Data = None
        self.a29Data = None

        self.address = address
        self.port = "/bt" + address.replace(":", "")
        self.interval = 5

        dev = OutbackBtDev(self.address)
        dev.addGeneralDataCallback(self.generalDataCB)
        dev.connect()

    def test_connection(self):
        return False

    def refresh_data(self):
        print("=> refresh_data")
        result = self.read_gen_data()
        while not result:
            result = self.read_gen_data()
        return result

    def read_gen_data(self):
        # print('=> read_gen_data')
        self.mutex.acquire()
        #if self.a03Data is None or self.a11Data is None or self.a29Data is None:
        if self.a03Data is None or self.a11Data is None:
            self.mutex.release()
            return False

        if self.a03Data:
            # print('A03')
            # // QPIGS
            a03Bytes = self.getExtractData(self.a03Data)
            a03Bytes = self.a03Data
            print(a03Bytes)

            self.a03gridVoltage = a03Bytes[0]
            self.a03gridFrequency = a03Bytes[1]
            self.a03acOutputVoltage = a03Bytes[2] * 0.1
            self.a03acFrequency = a03Bytes[3] * 0.1
            self.a03acApparentPower = a03Bytes[4]
            self.a03acActivePower = a03Bytes[5]
            self.a03loadPercent = a03Bytes[6]
            self.a03busVoltage = a03Bytes[7]
            self.a03batteryVoltage = a03Bytes[8] * 0.01
            self.a03batteryChargeCurrent = a03Bytes[9]
            self.a03acOutputCurrent = self.a03acActivePower / self.a03acOutputVoltage

            # AUSGABE
            if self.debug:
                print('collected values')
                print('a03gridVoltage => ' + str(self.a03gridVoltage))
                print('a03gridFrequency => ' + str(self.a03gridFrequency))
                print('a03acOutputVoltage => ' + str(self.a03acOutputVoltage))
                print('a03acFrequency => ' + str(self.a03acFrequency))
                print('a03acApparentPower => ' + str(self.a03acApparentPower))
                print('a03acActivePower => ' + str(self.a03acActivePower))
                print('a03loadPercent => ' + str(self.a03loadPercent))
                print('a03busVoltage => ' + str(self.a03busVoltage))
                print('a03batteryVoltage => ' + str(self.a03batteryVoltage))
                print('a03batteryChargeCurrent => ' + str(self.a03batteryChargeCurrent))
                print('calculated values')
                print('a03acOutputCurrent => ' + str(self.a03acOutputCurrent))

        if self.a11Data:
            # A11 Bereich
            # print('A11')
            a11Bytes = self.getExtractData(self.a11Data)
            a11Bytes = self.a11Data
            # print(a11Bytes)

            self.a11unknown0 = a11Bytes[0]  #
            self.a11unknown1 = a11Bytes[1]  #
            self.a11unknown2 = a11Bytes[2]  #
            self.a11unknown3 = a11Bytes[3]  #
            self.a11unknown4 = a11Bytes[4]  #
            self.a11unknown5 = a11Bytes[5]  #
            self.a11pvInputVoltage = a11Bytes[6] * 0.1  # Volt
            self.a11pvInputPower = a11Bytes[7]  # Watt
            self.a11unknown8 = a11Bytes[8]  #
            self.a11unknown9 = a11Bytes[9]  #

            if self.a11pvInputPower > 0:
                self.a11pvInputCurrent = self.a11pvInputPower / self.a11pvInputVoltage
            else:
                self.a11pvInputCurrent = 0

            if self.debug:
                # AUSGABE
                print('collected values')
                print('a11 unknown0 => ' + str(self.a11unknown0))
                print('a11 unknown1 => ' + str(self.a11unknown1))
                print('a11 unknown2 => ' + str(self.a11unknown2))
                print('a11 unknown3 => ' + str(self.a11unknown3))
                print('a11 unknown4 => ' + str(self.a11unknown4))
                print('a11 unknown5 => ' + str(self.a11unknown5))
                print('a11pvInputPower => ' + str(self.a11pvInputPower))
                print('a11pvInputVoltage => ' + str(self.a11pvInputVoltage))
                print('a11 unknown8 => ' + str(self.a11unknown8))
                print('a11 unknown9 => ' + str(self.a11unknown9))
                print('calculated values')
                print('a11pvInputCurrent => ' + str(self.a11pvInputCurrent))

        if self.a29Data:
            # A29 Bereich
            print('A29')
            a29Bytes = self.getExtractData(self.a29Data)
            a29Bytes = self.a29Data
            print(a29Bytes)

            self.a29unknown0 = a29Bytes[0]  #
            self.a29unknown1 = a29Bytes[1]  #
            self.a29unknown2 = a29Bytes[2]  #
            self.a29unknown3 = a29Bytes[3]  #
            self.a29unknown4 = a29Bytes[4]  #
            self.a29unknown5 = a29Bytes[5]  #
            self.a29unknown6 = a29Bytes[6]  #
            self.a29unknown7 = a29Bytes[7]  #
            self.a29unknown8 = a29Bytes[8]  #
            self.a29unknown9 = a29Bytes[9]  #

            if self.debug:
                # AUSGABE
                print('a29 unknown0 => ' + str(self.a29unknown0))
                print('a29 unknown1 => ' + str(self.a29unknown1))
                print('a29 unknown2 => ' + str(self.a29unknown2))
                print('a29 unknown3 => ' + str(self.a29unknown3))
                print('a29 unknown4 => ' + str(self.a29unknown4))
                print('a29 unknown5 => ' + str(self.a29unknown5))
                print('a29 unknown6 => ' + str(self.a29unknown6))
                print('a29 unknown7 => ' + str(self.a29unknown7))
                print('a29 unknown8 => ' + str(self.a29unknown8))
                print('a29 unknown9 => ' + str(self.a29unknown9))

        self.mutex.release()
        return True

    def getExtractData(self, byteArrayObject):
        print(byteArrayObject)
        tuple_of_shorts = struct.unpack('>' + 'h' * (len(byteArrayObject) // 2), byteArrayObject)
        print(tuple_of_shorts)
        bytesData = self.byte2short(tuple_of_shorts)
        print(bytesData)

        return bytesData

    def generalDataCB(self, data, charType):
        self.mutex.acquire()
        print('setting data' + "" + charType)
        if charType == "a03":
            self.a03Data = data
        elif charType == "a11":
            self.a11Data = data
        elif charType == "a29":
            self.a29Data = data
        else:
            print("no characteristic given")
        self.mutex.release()

    def byte2short(self, integers):
        myResult = []
        for s in integers:
            newVal = (((s >> 8) & 255) + (((s & 255) << 8) & 65280))
            resultValue = newVal  # * 0.01
            myResult.append(resultValue)
        return myResult


# Testmethode für direkten Aufruf
if __name__ == "__main__":
    peripheral = Peripheral("00:35:FF:02:95:99", iface=0)
    for service in peripheral.getServices():
        print(service)
        print(service.uuid)
        for characteristic in service.getCharacteristics():
            print("Characteristic - id: %s\tname (if exists): %s\tavailable methods: %s" % (str(characteristic.uuid), str(characteristic), characteristic.propertiesToString()))
