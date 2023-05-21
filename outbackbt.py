from bluepy.btle import Peripheral, DefaultDelegate, BTLEException, BTLEDisconnectError
from threading import Thread, Lock
from inverter import Inverter
from utils import *
import utils
import time
import struct
import sys
import os

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
        self.interval = 1

        self.debug = utils.DEBUG_MODE

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
                    logger.info("There was an error in this run! Waiting 5 seconds")
                    e = sys.exc_info()
                    logger.info(e)
                    time.sleep(2)
                    logger.info('restarting and reseting bluetooth')
                    os.system('/etc/init.d/bluetooth restart; hciconfig hci0 reset')
                    time.sleep(3)
                    continue
            try:
                outbackService00001810 = self.bt.getServiceByUUID('00001810-0000-1000-8000-00805f9b34fb')
                outbackService00001811 = self.bt.getServiceByUUID('00001811-0000-1000-8000-00805f9b34fb')
                #outbackService0000180a = self.bt.getServiceByUUID('0000180a-0000-1000-8000-00805f9b34fb')

                # kann  nicht gelesen werden, daher auskommentiert
                #outbackService00001801 = self.bt.getServiceByUUID('00001801-0000-1000-8000-00805f9b34fb')
                #outbackService00001801a01 = outbackService00001801.getCharacteristics("00002a05-0000-1000-8000-00805f9b34fb")[0]
                #outbackService00001801a01Data = outbackService00001801a01.read()
                #print(outbackService00001801a01Data)

                # outbackService00001810a01 = outbackService00001810.getCharacteristics("00002a01-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a02 = outbackService00001810.getCharacteristics("00002a02-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001810a03 = outbackService00001810.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a04 = outbackService00001810.getCharacteristics("00002a04-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a05 = outbackService00001810.getCharacteristics("00002a05-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a06 = outbackService00001810.getCharacteristics("00002a06-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a07 = outbackService00001810.getCharacteristics("00002a07-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a08 = outbackService00001810.getCharacteristics("00002a08-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a09 = outbackService00001810.getCharacteristics("00002a09-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a0a = outbackService00001810.getCharacteristics("00002a0a-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a0b = outbackService00001810.getCharacteristics("00002a0b-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a0c = outbackService00001810.getCharacteristics("00002a0c-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a0d = outbackService00001810.getCharacteristics("00002a0d-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001810a01Data = self.getExtractData(outbackService00001810a01.read())
                # outbackService00001810a02Data = self.getExtractData(outbackService00001810a02.read())
                outbackService00001810a03Data = self.getExtractData(outbackService00001810a03.read())
                # outbackService00001810a04Data = self.getExtractData(outbackService00001810a04.read())
                # outbackService00001810a05Data = self.getExtractData(outbackService00001810a05.read())
                # outbackService00001810a06Data = self.getExtractData(outbackService00001810a06.read())
                # outbackService00001810a07Data = self.getExtractData(outbackService00001810a07.read())
                # outbackService00001810a08Data = self.getExtractData(outbackService00001810a08.read())
                # outbackService00001810a09Data = self.getExtractData(outbackService00001810a09.read())
                # outbackService00001810a0aData = self.getExtractData(outbackService00001810a0a.read())
                # outbackService00001810a0bData = self.getExtractData(outbackService00001810a0b.read())
                # outbackService00001810a0cData = self.getExtractData(outbackService00001810a0c.read())
                # outbackService00001810a0dData = self.getExtractData(outbackService00001810a0d.read())
                if self.debug:
                    # print(outbackService00001810a01Data)
                    # print(outbackService00001810a02Data)
                    print("a03: " + str(outbackService00001810a03Data))
                    # print(outbackService00001810a04Data)
                    # print(outbackService00001810a05Data)
                    # print(outbackService00001810a06Data)
                    # print(outbackService00001810a07Data)
                    # print(outbackService00001810a08Data)
                    # print(outbackService00001810a09Data)
                    # print(outbackService00001810a0aData)
                    # print(outbackService00001810a0bData)
                    # print(outbackService00001810a0cData)
                    # print(outbackService00001810a0dData)

                outbackService00001811a11 = outbackService00001811.getCharacteristics("00002a11-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001811a12 = outbackService00001811.getCharacteristics("00002a12-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001811a13 = outbackService00001811.getCharacteristics("00002a13-0000-1000-8000-00805f9b34fb")[0]
                # outbackService00001811a14 = outbackService00001811.getCharacteristics("00002a14-0000-1000-8000-00805f9b34fb")[0]
                outbackService00001811a11Data = self.getExtractData(outbackService00001811a11.read())
                # outbackService00001811a12Data = self.getExtractData(outbackService00001811a12.read())
                # outbackService00001811a13Data = self.getExtractData(outbackService00001811a13.read())
                # outbackService00001811a14Data = self.getExtractData(outbackService00001811a14.read())
                if self.debug:
                    print("a11: " + str(outbackService00001811a11Data))
                    # print(outbackService00001811a12Data)
                    # print(outbackService00001811a13Data)
                    # print(outbackService00001811a14Data)

                #outbackService0000180aa29 = outbackService0000180a.getCharacteristics("00002a29-0000-1000-8000-00805f9b34fb")[0]
                #outbackService0000180aa2a = outbackService0000180a.getCharacteristics("00002a2a-0000-1000-8000-00805f9b34fb")[0]
                #outbackService0000180aa29Data = outbackService0000180aa29.read()
                #outbackService0000180aa2aData = outbackService0000180aa2a.read()
                #if self.debug:
                    #print(outbackService0000180aa29Data)
                    #print(outbackService0000180aa2aData)

                # read our data
                self.generalDataCallback(outbackService00001810a03Data, "a03")
                self.generalDataCallback(outbackService00001811a11Data, "a11")
                sleep(self.interval)

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
        self.debug = utils.DEBUG_MODE

        # Bluepy stuff
        self.bt = Peripheral()
        self.bt.setDelegate(self)

        self.mutex = Lock()
        self.a03Data = None
        self.a11Data = None
        self.a29Data = None

        #self.newData = False

        self.address = address
        self.port = "/bt" + address.replace(":", "")
        self.interval = 2

        dev = OutbackBtDev(self.address)
        dev.addGeneralDataCallback(self.generalDataCB)
        dev.connect()

    def test_connection(self):
        return False

    def refresh_data(self):
        #if self.newData:
        print("=> refresh_data2")
        result = self.read_gen_data()
        while not result:
            result = self.read_gen_data()
            return result
        #else:
            #return False

    def read_gen_data(self):
        self.mutex.acquire()

        if self.a03Data is None and self.a11Data is None and self.a29Data is None:
            self.mutex.release()
            print('all NONE')
            return False

        if self.a03Data:
            self.a03gridVoltage = self.a03Data[0]
            self.a03gridFrequency = self.a03Data[1]
            self.a03acOutputVoltage = self.a03Data[2] * 0.1
            self.a03acFrequency = self.a03Data[3] * 0.1
            self.a03acApparentPower = self.a03Data[4]
            self.a03acActivePower = self.a03Data[5]
            self.a03loadPercent = self.a03Data[6]
            self.a03busVoltage = self.a03Data[7]
            self.a03batteryVoltage = self.a03Data[8] * 0.01
            self.a03batteryChargeCurrent = self.a03Data[9]
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
            self.a11unknown0 = self.a11Data[0]  #
            self.a11unknown1 = self.a11Data[1]  #
            self.a11unknown2 = self.a11Data[2]  #
            self.a11unknown3 = self.a11Data[3]  #
            self.a11unknown4 = self.a11Data[4]  #
            self.a11unknown5 = self.a11Data[5]  #
            self.a11pvInputVoltage = self.a11Data[6] * 0.1  # Volt
            self.a11pvInputPower = self.a11Data[7]  # Watt
            self.a11unknown8 = self.a11Data[8]  #
            self.a11unknown9 = self.a11Data[9]  #

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
            self.a29unknown0 = self.a29Data[0]  #
            self.a29unknown1 = self.a29Data[1]  #
            self.a29unknown2 = self.a29Data[2]  #
            self.a29unknown3 = self.a29Data[3]  #
            self.a29unknown4 = self.a29Data[4]  #
            self.a29unknown5 = self.a29Data[5]  #
            self.a29unknown6 = self.a29Data[6]  #
            self.a29unknown7 = self.a29Data[7]  #
            self.a29unknown8 = self.a29Data[8]  #
            self.a29unknown9 = self.a29Data[9]  #

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
        #self.newData = False
        return True


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

        #self.newData = True
        self.mutex.release()


# Testmethode für direkten Aufruf
if __name__ == "__main__":
    peripheral = Peripheral("00:35:FF:02:95:99", iface=0)
    for service in peripheral.getServices():
        print(service)
        print(service.uuid)
        for characteristic in service.getCharacteristics():
            print("Characteristic - id: %s\tname (if exists): %s\tavailable methods: %s" % (str(characteristic.uuid), str(characteristic), characteristic.propertiesToString()))
