from bluepy.btle import Peripheral, DefaultDelegate, BTLEException, BTLEDisconnectError
from threading import Thread, Lock
from inverter import Inverter
from utils import *
import time

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
		timer = 0
		connected = False
		while self.running:
			if not connected:
				try:
					logger.info('Connecting ' + self.address)
					self.bt.connect(self.address, addrType="public")
					logger.info('Connected ' + self.address)
					connected = True
				except BTLEException as ex:
					logger.info('Connection failed')
					time.sleep(3)
					continue

			try:
				if self.bt.waitForNotifications(0.5):
					continue

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
		dev.addGeneralDataCallback(self.generalDataCB)
		dev.connect()

	def test_connection(self):
		return False

	def get_settings(self):
		result = self.read_gen_data()
		while not result:
			result = self.read_gen_data()
			time.sleep(1)
		#self.max_battery_charge_current = MAX_BATTERY_CHARGE_CURRENT
		#self.max_battery_discharge_current = MAX_BATTERY_DISCHARGE_CURRENT
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
		self.mutex.acquire()
		if self.generalData1 == None or self.generalData2 == None:
			self.mutex.release()
			return False

		gen_data = self.generalData1 + self.generalData2
		self.mutex.release()

		# write data here
		# sample
		#self.voltage = voltage / 100

		return True

	def generalDataCB(self, data, index):
		self.mutex.acquire()
		if index == 0:
			self.generalData1 = data
		else:
			self.generalData2 = data
		self.mutex.release()


# Testmethode für direkten Aufruf
if __name__ == "__main__":
	outbackInverterTest = OutbackBt("00:35:FF:02:95:99")
	print("1")
	outbackInverterTest.get_settings()
	print("2")
	while True:
		outbackInverterTest.refresh_data()

		print("")
		print("Cells " + str(outbackInverterTest.cell_count))
		print("")

		time.sleep(5)



