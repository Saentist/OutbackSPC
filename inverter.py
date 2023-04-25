# -*- coding: utf-8 -*-
from typing import Union, Tuple, List

from utils import logger
import utils
from abc import ABC, abstractmethod


class Inverter(ABC):
    """
    This Class is the abstract baseclass for all batteries. For each BMS this class needs to be extended
    and the abstract methods need to be implemented. The main program in dbus-serialbattery.py will then
    use the individual implementations as type Battery and work with it.
    """

    def __init__(self, port, baud, address):
        self.port = port
        self.baud_rate = baud
        self.role = None
        self.type = "Generic"
        self.poll_interval = 2000  # 2 Sekunden
        self.online = True

        self.hardware_version = None
        self.voltage = None
        self.current = None


        # OUTBACK
        # A03
        self.a03acvoltage = None
        self.a03acfrequency = None
        self.a03outputvoltage = None
        self.a03outputfrequency = None
        self.a03outputapppower = None
        self.a03outputactpower = None
        self.a03loadpercent = None
        self.a03unknown7 = None
        self.a03batteryvoltage = None
        self.a03chargecurrent = None
        # A11
        self.a11unknown0 = None
        self.a11unknown1 = None
        self.a11unknown2 = None
        self.a11unknown3 = None
        self.a11unknown4 = None
        self.a11unknown5 = None
        self.a11pvInputVoltage = None
        self.a11pvInputPower = None
        self.a11pvInputCurrent = None
        self.a11unknown8 = None
        self.a11unknown9 = None

    @abstractmethod
    def test_connection(self) -> bool:
        """
        This abstract method needs to be implemented for each BMS. It shoudl return true if a connection
        to the BMS can be established, false otherwise.
        :return: the success state
        """
        # Each driver must override this function to test if a connection can be made
        # return false when failed, true if successful
        return False


    @abstractmethod
    def refresh_data(self) -> bool:
        """
        Each driver must override this function to read battery data and populate this class
        It is called each poll just before the data is published to vedbus

        :return:  false when fail, true if successful
        """
        return False

    def log_settings(self) -> None:
        logger.info(f"Battery {self.type} connected to dbus from {self.port}")
        logger.info("=== Settings ===")

        return
