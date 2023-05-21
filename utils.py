# -*- coding: utf-8 -*-
import logging

import configparser
from pathlib import Path
from typing import List, Any, Callable

import serial
from time import sleep
from struct import unpack_from
import bisect

# Logging
logging.basicConfig()
logger = logging.getLogger("BluetoothOutbackInverter")
logger.setLevel(logging.INFO)

config = configparser.ConfigParser()
path = Path(__file__).parents[0]
default_config_file_path = path.joinpath("default_config.ini").absolute().__str__()
custom_config_file_path = path.joinpath("config.ini").absolute().__str__()
config.read([default_config_file_path, custom_config_file_path])


def _get_list_from_config(
    group: str, option: str, mapper: Callable[[Any], Any] = lambda v: v
) -> List[Any]:
    rawList = config[group][option].split(",")
    return list(
        map(mapper, [item for item in rawList if item != "" and item is not None])
    )

# Constants - Need to dynamically get them in future
DRIVER_VERSION = 0.1
DRIVER_SUBVERSION = ".3"
zero_char = chr(48)
degree_sign = "\N{DEGREE SIGN}"

#LINEAR_LIMITATION_ENABLE = "True" == config["DEFAULT"]["LINEAR_LIMITATION_ENABLE"]
#MAX_BATTERY_CHARGE_CURRENT = float(config["DEFAULT"]["MAX_BATTERY_CHARGE_CURRENT"])
#CELL_VOLTAGES_WHILE_CHARGING = _get_list_from_config("DEFAULT", "CELL_VOLTAGES_WHILE_CHARGING", lambda v: float(v))
#PUBLISH_CONFIG_VALUES = int(config["DEFAULT"]["PUBLISH_CONFIG_VALUES"])
OUTBACK_ADDRESS = config["DEFAULT"]["OUTBACK_ADDRESS"]
DEBUG_MODE = config.getboolean(["DEFAULT"]["DEBUG_MODE"])

def constrain(val, min_val, max_val):
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min(max_val, max(min_val, val))


def mapRange(inValue, inMin, inMax, outMin, outMax):
    return outMin + (((inValue - inMin) / (inMax - inMin)) * (outMax - outMin))


def mapRangeConstrain(inValue, inMin, inMax, outMin, outMax):
    return constrain(mapRange(inValue, inMin, inMax, outMin, outMax), outMin, outMax)


def calcLinearRelationship(inValue, inArray, outArray):
    if inArray[0] > inArray[-1]:  # change compare-direction in array
        return calcLinearRelationship(inValue, inArray[::-1], outArray[::-1])
    else:

        # Handle out of bounds
        if inValue <= inArray[0]:
            return outArray[0]
        if inValue >= inArray[-1]:
            return outArray[-1]

        # else calculate linear current between the setpoints
        idx = bisect.bisect(inArray, inValue)
        upperIN = inArray[idx - 1]  # begin with idx 0 as max value
        upperOUT = outArray[idx - 1]
        lowerIN = inArray[idx]
        lowerOUT = outArray[idx]
        return mapRangeConstrain(inValue, lowerIN, upperIN, lowerOUT, upperOUT)


def calcStepRelationship(inValue, inArray, outArray, returnLower):
    if inArray[0] > inArray[-1]:  # change compare-direction in array
        return calcStepRelationship(inValue, inArray[::-1], outArray[::-1], returnLower)

    # Handle out of bounds
    if inValue <= inArray[0]:
        return outArray[0]
    if inValue >= inArray[-1]:
        return outArray[-1]

    # else get index between the setpoints
    idx = bisect.bisect(inArray, inValue)

    return outArray[idx] if returnLower else outArray[idx - 1]


def is_bit_set(tmp):
    return False if tmp == zero_char else True


def kelvin_to_celsius(kelvin_temp):
    return kelvin_temp - 273.1


def format_value(value, prefix, suffix):
    return (
        None
        if value is None
        else ("" if prefix is None else prefix)
        + str(value)
        + ("" if suffix is None else suffix)
    )


def read_serial_data(
    command, port, baud, length_pos, length_check, length_fixed=None, length_size=None
):
    try:
        with serial.Serial(port, baudrate=baud, timeout=0.1) as ser:
            return read_serialport_data(
                ser, command, length_pos, length_check, length_fixed, length_size
            )

    except serial.SerialException as e:
        logger.error(e)
        return False


# Open the serial port
# Return variable for the openned port
def open_serial_port(port, baud):
    ser = None
    tries = 3
    while tries > 0:
        try:
            ser = serial.Serial(port, baudrate=baud, timeout=0.1)
            tries = 0
        except serial.SerialException as e:
            logger.error(e)
            tries -= 1

    return ser


# Read data from previously openned serial port
def read_serialport_data(
    ser: serial.Serial,
    command,
    length_pos,
    length_check,
    length_fixed=None,
    length_size=None,
):
    try:
        ser.flushOutput()
        ser.flushInput()
        ser.write(command)

        length_byte_size = 1
        if length_size is not None:
            if length_size.upper() == "H":
                length_byte_size = 2
            elif length_size.upper() == "I" or length_size.upper() == "L":
                length_byte_size = 4

        count = 0
        toread = ser.inWaiting()

        while toread < (length_pos + length_byte_size):
            sleep(0.005)
            toread = ser.inWaiting()
            count += 1
            if count > 50:
                logger.error(">>> ERROR: No reply - returning")
                return False

        # logger.info('serial data toread ' + str(toread))
        res = ser.read(toread)
        if length_fixed is not None:
            length = length_fixed
        else:
            if len(res) < (length_pos + length_byte_size):
                logger.error(
                    ">>> ERROR: No reply - returning [len:" + str(len(res)) + "]"
                )
                return False
            length_size = length_size if length_size is not None else "B"
            length = unpack_from(">" + length_size, res, length_pos)[0]

        # logger.info('serial data length ' + str(length))

        count = 0
        data = bytearray(res)
        while len(data) <= length + length_check:
            res = ser.read(length + length_check)
            data.extend(res)
            # logger.info('serial data length ' + str(len(data)))
            sleep(0.005)
            count += 1
            if count > 150:
                logger.error(
                    ">>> ERROR: No reply - returning [len:"
                    + str(len(data))
                    + "/"
                    + str(length + length_check)
                    + "]"
                )
                return False

        return data

    except serial.SerialException as e:
        logger.error(e)
        return False


locals_copy = locals().copy()


def publish_config_variables(dbusservice):
    for variable, value in locals_copy.items():
        if variable.startswith("__"):
            continue
        if (
            isinstance(value, float)
            or isinstance(value, int)
            or isinstance(value, str)
            or isinstance(value, List)
        ):
            dbusservice.add_path(f"/Info/Config/{variable}", value)
