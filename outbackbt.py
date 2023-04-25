from bluepy.btle import Peripheral, DefaultDelegate, BTLEException, BTLEDisconnectError
from threading import Thread, Lock
from inverter import Inverter
from utils import *
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
                self.generalDataCallback(data, 1)

                outbackService2 = self.bt.getServiceByUUID('00001811-0000-1000-8000-00805f9b34fb')
                outbackCharacteristicA11 = outbackService2.getCharacteristics("00002a11-0000-1000-8000-00805f9b34fb")[0]
                data = outbackCharacteristicA11.read()
                self.generalDataCallback(data, 0)

                # dritte potentielle characteristikcs uuid
                # 00002a29-0000-1000-8000-00805f9b34fb
                # todo bei zeiten ausprobieren

                print('sleeping 2 sec')
                sleep(2)
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

    def handleNotification(self, cHandle, data):
        print('handleNotification START')
        hex_data = binascii.hexlify(data)
        hex_string = hex_data.decode('utf-8')
        print('handleNotification END')
        print(hex_string)


class OutbackBt(Inverter):
    def __init__(self, address):
        print('=> Outback _init_')
        Inverter.__init__(self, 0, 0, address)

        self.type = "OUTBACK BT"

        # Bluepy stuff
        self.bt = Peripheral()
        self.bt.setDelegate(self)

        self.mutex = Lock()
        self.generalData1 = None
        self.generalData2 = None

        self.address = address
        self.port = "/bt" + address.replace(":", "")
        self.interval = 5

        dev = OutbackBtDev(self.address)
        dev.addGeneralDataCallback(self.generalDataCB)
        dev.connect()
        print('Outback _init_ =>')

    def test_connection(self):
        return False

    def get_settings(self):
        print("=> get_settings")
        result = self.read_gen_data()
        while not result:
            print("get_settings  WHILE")
            result = self.read_gen_data()
            print('sleeping 1 sec')
            time.sleep(1)
        return result

    def refresh_data(self):
        print("=> refresh_data")
        result = self.read_gen_data()
        print("refresh_data =>")
        return result

    def log_settings(self):
        # Override log_settings() to call get_settings() first
        self.get_settings()
        Inverter.log_settings(self)

    def to_fet_bits(self, byte_data):
        tmp = bin(byte_data)[2:].rjust(2, zero_char)
        self.charge_fet = is_bit_set(tmp[1])
        self.discharge_fet = is_bit_set(tmp[0])

    def read_gen_data(self):
        print('=> read_gen_data')
        self.mutex.acquire()
        if self.generalData1 is None or self.generalData2 is None:
            self.mutex.release()
            print('read_gen_data False =>')
            return False

        print('A03')
        a03Bytes = self.getExtractData(self.generalData1)
        print(a03Bytes)

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

        # AUSGABE
        print('a03acvoltage => ' + str(self.a03acvoltage))
        print('acfrequency => ' + str(self.a03acfrequency))
        print('outputvoltage => ' + str(self.a03outputvoltage))
        print('outputfrequency => ' + str(self.a03outputfrequency))
        print('outputapppower => ' + str(self.a03outputapppower))
        print('outputactpower => ' + str(self.a03outputactpower))
        print('loadpercent => ' + str(self.a03loadpercent))
        print('unknown7 => ' + str(self.a03unknown7))
        print('batteryvoltage => ' + str(self.a03batteryvoltage))
        print('chargecurrent => ' + str(self.a03chargecurrent))

        # A11 Bereich
        print('A11')
        a11Bytes = self.getExtractData(self.generalData2)
        print(a11Bytes)

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

        # AUSGABE
        print('unknown0 => ' + str(self.a11unknown0))
        print('unknown1 => ' + str(self.a11unknown1))
        print('unknown2 => ' + str(self.a11unknown2))
        print('unknown3 => ' + str(self.a11unknown3))
        print('unknown4 => ' + str(self.a11unknown4))
        print('unknown5 => ' + str(self.a11unknown5))
        print('pvInputPower => ' + str(self.a11pvInputPower))
        print('pvInputVoltage => ' + str(self.a11pvInputVoltage))
        print('pvInputCurrent => ' + str(self.a11pvInputCurrent))
        print('unknown8 => ' + str(self.a11unknown8))
        print('unknown9 => ' + str(self.a11unknown9))

        self.mutex.release()
        print('sleeping 5 sec')
        sleep(5)
        print('read_gen_data True =>')
        return True

    def getExtractData(self, byteArrayObject):
        tuple_of_shorts = struct.unpack('>' + 'h' * (len(byteArrayObject) // 2), byteArrayObject)
        bytesData = self.byte2short(tuple_of_shorts)
        print(bytesData)

        return bytesData

    def generalDataCB(self, data, index):
        print("=> generalDataCB")
        self.mutex.acquire()
        if index == 1:
            self.generalData1 = data
            print("=> generalDataCB data1 =>")
        else:
            self.generalData2 = data
            print("=> generalDataCB data2 =>")
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
