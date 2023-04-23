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
                #data = self.bt.getCharacteristics(uuid="00002a03-0000-1000-8000-00805f9b34fb")
                #data = self.bt.getServiceByUUID("00002a03-0000-1000-8000-00805f9b34fb")
                #self.generalDataCallback(data, 1)
                services = self.bt.getServices()
                service = self.bt.getServiceByUUID('00001810-0000-1000-8000-00805f9b34fb')
                characteristics = service.getCharacteristics()
                for characteristic in characteristics:
                    print(characteristic)
                    value = characteristic.read()
                    print(value)
                    properties = characteristic.propertiesToString()
                    print(properties)
                    handle = characteristic.getHandle()
                    print(handle)
                # print('---')
                # test = service.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")
                # print(test)
                # testvalue = test[0]
                # print(testvalue)
                # testvalueData = testvalue.read()
                # print(testvalueData)
                # print('---')
                #
                # data_chrc.write(bytes("\x01"))
                # time.sleep(10)


                service = self.bt.getServiceByUUID('00001810-0000-1000-8000-00805f9b34fb')
                characteristic = service.getCharacteristics("00002a03-0000-1000-8000-00805f9b34fb")[0]
                data = characteristic.read()
                self.generalDataCallback(data, 1)
            except BTLEDisconnectError:
                logger.info('Disconnected')
                connected = False
                continue

    def connect(self):
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
        print("e1")
        dev.addGeneralDataCallback(self.generalDataCB)
        print("e1")
        dev.connect()

    def test_connection(self):
        return False

    def get_settings(self):
        print("b1")
        result = self.read_gen_data()
        print("b2")
        while not result:
            print("b3")
            result = self.read_gen_data()
            time.sleep(1)
        # self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
        # self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
        return result

    def refresh_data(self):
        result = self.read_gen_data()
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
        print('a')
        self.mutex.acquire()
        if self.generalData1 is None:  # or self.generalData2 == None:
            self.mutex.release()
            return False

        #self.mutex.release()
        print('b')
        byteArrayObject = self.generalData1
        print('byteArrayObject')
        for service in self.generalData1:
            print(service)
        tuple_of_shorts = struct.unpack('>' + 'h' * (len(byteArrayObject) // 2), byteArrayObject)
        a03Bytes = self.byte2short(tuple_of_shorts)

        acvoltage = a03Bytes[0]
        acfrequency = a03Bytes[1]
        outputvoltage = a03Bytes[2]
        outputfrequency = a03Bytes[3] * 0.1
        outputapppower = a03Bytes[4]
        outputactpower = a03Bytes[5]
        loadpercent = a03Bytes[6]
        UNKNOWN = a03Bytes[7]
        batteryvoltage = a03Bytes[8] * 0.01
        chargecurrent = a03Bytes[9]
        print('outputfrequency => ' + str(outputfrequency))
        print('outputapppower => ' + str(outputapppower))
        print('outputactpower => ' + str(outputactpower))
        print('loadpercent => ' + str(loadpercent))

        self.mutex.release()

        # chList = p.getCharacteristics()
        # chList = p.getCharacteristics(uuid=service_uuid)
        # print("Handle      UUID        Properties")
        # print("----------------------------------")
        # for ch in chList:

        # write data here
        # sample
        # self.voltage = voltage / 100

        return True

    def generalDataCB(self, data, index):
        print("f1")
        self.mutex.acquire()
        if index == 1:
            print("f2")
            print(data)
            self.generalData1 = data
        else:
            print("f3")
            print(data)
            self.generalData2 = data
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
    print('1')
    peripheral = Peripheral("00:35:FF:02:95:99", iface=0)

    byteArrayObject = peripheral.getCharacteristics(uuid="00002a03-0000-1000-8000-00805f9b34fb")
    print(byteArrayObject)
    print('2')
# for service in peripheral.getServices():
# for characteristic in service.getCharacteristics():
# print("Characteristic - id: %s\tname (if exists): %s\tavailable methods: %s" % (str(characteristic.uuid), str(characteristic), characteristic.propertiesToString()))

# outbackInverterTest = OutbackBt("00:35:FF:02:95:99")
# print("1")
# outbackInverterTest.get_settings()
# print("2")
# while True:
# 	outbackInverterTest.refresh_data()
#
# 	print("")
# 	print("Cells " + str(outbackInverterTest.cell_count))
# 	print("")
#
# 	time.sleep(5)
