from bluepy.btle import Peripheral, DefaultDelegate, BTLEException, BTLEDisconnectError
from threading import Thread, Lock
from inverter import Inverter
from utils import *
import utils
import time
import binascii
import struct


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
                outbackService1 = self.bt.getServiceByUUID('00001810-0000-1000-8000-00805f9b34fb')
                outbackCharacteristicA03 = outbackService1.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")[0]
                data = outbackCharacteristicA03.read()
                self.generalDataCallback(data, "a03")

                outbackService2 = self.bt.getServiceByUUID('00001811-0000-1000-8000-00805f9b34fb')
                outbackCharacteristicA11 = outbackService2.getCharacteristics("00002a11-0000-1000-8000-00805f9b34fb")[0]
                data = outbackCharacteristicA11.read()
                self.generalDataCallback(data, "a11")

                #outbackService3 = self.bt.getServiceByUUID('00001811-0000-1000-8000-00805f9b34fb')
                #outbackCharacteristicA29 = outbackService3.getCharacteristics("00002a29-0000-1000-8000-00805f9b34fb")[0]
                #data = outbackCharacteristicA29.read()
                #self.generalDataCallback(data, "a29")

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
        if self.a03Data is None or self.a11Data is None or self.a29Data is None:
            self.mutex.release()
            return False

        # print('A03')
        a03Bytes = self.getExtractData(self.a03Data)
        # print(a03Bytes)

        self.a03acvoltage = a03Bytes[0]
        self.a03acfrequency = a03Bytes[1]
        self.a03outputvoltage = a03Bytes[2] * 0.1
        self.a03outputfrequency = a03Bytes[3] * 0.1
        self.a03outputapppower = a03Bytes[4]
        self.a03outputactpower = a03Bytes[5]
        self.a03loadpercent = a03Bytes[6]
        self.a03unknown7 = a03Bytes[7]
        self.a03batteryvoltage = a03Bytes[8] * 0.01
        self.a03chargecurrent = a03Bytes[9]
        self.a03outputcurrent = self.a03outputapppower / self.a03outputvoltage

        # AUSGABE
        if self.debug:
            print('a03 acvoltage => ' + str(self.a03acvoltage))
            print('a03 acfrequency => ' + str(self.a03acfrequency))
            print('a03 outputvoltage => ' + str(self.a03outputvoltage))
            print('a03 outputfrequency => ' + str(self.a03outputfrequency))
            print('a03 outputapppower => ' + str(self.a03outputapppower))
            print('a03 outputactpower => ' + str(self.a03outputactpower))
            print('a03 loadpercent => ' + str(self.a03loadpercent))
            print('a03 unknown7 => ' + str(self.a03unknown7))
            print('a03 batteryvoltage => ' + str(self.a03batteryvoltage))
            print('a03 chargecurrent => ' + str(self.a03chargecurrent))
            print('a03 outputcurrent => ' + str(self.a03outputcurrent))

        # A11 Bereich
        # print('A11')
        a11Bytes = self.getExtractData(self.a11Data)
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
            print('a11 unknown0 => ' + str(self.a11unknown0))
            print('a11 unknown1 => ' + str(self.a11unknown1))
            print('a11 unknown2 => ' + str(self.a11unknown2))
            print('a11 unknown3 => ' + str(self.a11unknown3))
            print('a11 unknown4 => ' + str(self.a11unknown4))
            print('a11 unknown5 => ' + str(self.a11unknown5))
            print('a11 pvInputPower => ' + str(self.a11pvInputPower))
            print('a11 pvInputVoltage => ' + str(self.a11pvInputVoltage))
            print('a11 unknown8 => ' + str(self.a11unknown8))
            print('a11 unknown9 => ' + str(self.a11unknown9))
            print('a11 calculated pvInputCurrent => ' + str(self.a11pvInputCurrent))

        # A29 Bereich
        # print('A29')
        #a29Bytes = self.getExtractData(self.a29Data)
        # print(a29Bytes)

        # self.a29unknown0 = a29Bytes[0]  #
        # self.a29unknown1 = a29Bytes[1]  #
        # self.a29unknown2 = a29Bytes[2]  #
        # self.a29unknown3 = a29Bytes[3]  #
        # self.a29unknown4 = a29Bytes[4]  #
        # self.a29unknown5 = a29Bytes[5]  #
        # self.a29unknown6 = a29Bytes[6]  #
        # self.a29unknown7 = a29Bytes[7]  #
        # self.a29unknown8 = a29Bytes[8]  #
        # self.a29unknown9 = a29Bytes[9]  #

        # if self.debug:
        #     # AUSGABE
        #     print('a29 unknown0 => ' + str(self.a29unknown0))
        #     print('a29 unknown1 => ' + str(self.a29unknown1))
        #     print('a29 unknown2 => ' + str(self.a29unknown2))
        #     print('a29 unknown3 => ' + str(self.a29unknown3))
        #     print('a29 unknown4 => ' + str(self.a29unknown4))
        #     print('a29 unknown5 => ' + str(self.a29unknown5))
        #     print('a29 unknown6 => ' + str(self.a29unknown6))
        #     print('a29 unknown7 => ' + str(self.a29unknown7))
        #     print('a29 unknown8 => ' + str(self.a29unknown8))
        #     print('a29 unknown9 => ' + str(self.a29unknown9))

        self.mutex.release()
        return True

    def getExtractData(self, byteArrayObject):
        tuple_of_shorts = struct.unpack('>' + 'h' * (len(byteArrayObject) // 2), byteArrayObject)
        bytesData = self.byte2short(tuple_of_shorts)
        print(bytesData)

        return bytesData

    def generalDataCB(self, data, charType):
        self.mutex.acquire()
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
