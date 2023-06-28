import asyncio
import datetime
import atexit
import aioconsole
import sys
from bleak import BleakClient, BleakScanner
from bleak.uuids import uuid16_dict
from os import system, name
import datetime as dt
from math import ceil
import time

from distutils.core import setup

currentMarkerECG = ""
currentMarkerHR = ""
currentMarkerRR = ""

subjectId = 0
save = True
stop = False
x = 0
data_ecg = []
xs = []
ys = []

print(f"Starting server...")

""" Predefined UUID (Universal Unique Identifier) mapping are based on Heart Rate GATT service Protocol that most
Fitness/Heart Rate device manufacturer follow (Polar H10 in this case) to obtain a specific response input from 
the device acting as an API """

uuid16_dict = {v: k for k, v in uuid16_dict.items()}

## UUID for model number ##
MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Model Number String")
)

## UUID for manufacturer name ##
MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Manufacturer Name String")
)

HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
BODY_SENSOR_LOC_UUID = "00002a38-0000-1000-8000-00805f9b34fb"

## UUID for battery level ##
BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Battery Level")
)

## UUID for connection establishment with device ##
PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of stream settings ##
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of start stream ##
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

## UUID for Request of ECG Stream ##
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])

## For Polar H10  sampling frequency ##
ECG_SAMPLING_FREQ = 130

OUTLET = []

hr_tab = []
rr_tab = []


def hr_conv(sender, data: bytearray):
    timestampPC = str(time.time_ns())
    global currentMarkerHR
    global currentMarkerRR
    byte0 = data[0]
    uint8_format = (byte0 & 1) == 0

    energy_expenditure = ((byte0 >> 3) & 1) == 1
    rr_interval = ((byte0 >> 4) & 1) == 1

    """if not rr_interval:
        return"""

    first_rr_byte = 2
    if uint8_format:
        hr = data[1]
        current_hr = hr
    else:
        hr = (data[2] << 8) | data[1]  # uint16
        hr = (data[2] << 8) | data[1]  # uint16
        current_hr = hr

    if energy_expenditure:
        ee = (data[first_rr_byte + 1] << 8) | data[first_rr_byte]
        first_rr_byte += 2

    # IBI = Inter-Beat Interval
    for i in range(first_rr_byte, len(data), 2):
        ibi = (data[i + 1] << 8) | data[i]
        # Polar H7, H9, and H10 record IBIs in 1/1024 seconds format.
        # Convert 1/1024 sec format to milliseconds.
        # TODO: move conversion to model and only convert if sensor doesn't
        # transmit data in milliseconds.
        ibi = ceil(ibi / 1024 * 1000)
        rr_tab.append(ibi)
        hr_tab.append(current_hr)

        file_hr.write(timestampPC + ";" + str(current_hr) + ";" + currentMarkerHR + "\n")
        file_rr.write(timestampPC + ";" + str(ibi) + ";" + currentMarkerRR + "\n")

        currentMarkerHR = ""
        currentMarkerRR = ""

        clear()

        print('Heart rate:' + str(current_hr))
        print('RR:' + str(ibi))


def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux
    else:
        _ = system('clear')


## Bit conversion of the Hexadecimal stream
def data_conv(sender, data: bytearray):
    timestampPC = str(time.time_ns())
    global x
    global currentMarkerECG
    # global OUTLET
    if data[0] == 0x00:
        btime = data[1:9]
        timestampPolar = str(int.from_bytes(bytearray(btime), byteorder="little", signed=True))

        # dt = datetime.datetime.fromtimestamp(timestamp / 1e9)
        # print('{}{:03.0f}'.format(dt.strftime('%Y-%m-%dT%H:%M:%S.%f'), timestamp % 1e3))

        step = 3
        samples = data[10:]
        offset = 0

        while offset < len(samples):
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            data_ecg.append(ecg)

            xs.append(x)
            x += 1
            ys.append(ecg)
            file_ecg.write(timestampPolar + ";" + timestampPC + ";" + str(ecg) + ";" + currentMarkerECG + "\n")
            currentMarkerECG = ""


def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset: offset + length]), byteorder="little", signed=True,
    )


def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset: offset + length]), byteorder="little", signed=False,
    )


## ASynchronous task to start the data stream for ECG ##
async def run(client, debug=True):
    print("---------Looking for Device------------ ", flush=True)

    await client.is_connected()
    print("---------Device connected--------------", flush=True)
    print(client)

    model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    print("Model Number: {0}".format("".join(map(chr, model_number))), flush=True)

    manufacturer_name = await client.read_gatt_char(MANUFACTURER_NAME_UUID)
    print("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))), flush=True)

    battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
    print("Battery Level: {0}%".format(int(battery_level[0])), flush=True)

    await client.start_notify(HEART_RATE_UUID, hr_conv)

    print("Collecting ECG data...", flush=True)

    # await aioconsole.ainput('Running: Press a key to quit')

    a = await client.read_gatt_char(PMD_CONTROL)

    #print("Collecting GATT data...")
    b = await client.write_gatt_char(PMD_CONTROL, ECG_WRITE, True)
    #print("Writing GATT data...")

    ## ECG stream started
    await client.start_notify(PMD_DATA, data_conv)
    #await client.start_notify(HEART_RATE_UUID, hr_conv)

    #print("Collecting ECG data...", flush=True)

    # while not stop:
    await aioconsole.ainput('Running: Press a key to quit')

    await client.stop_notify(PMD_DATA)

    print("Stopping ECG data...", flush=True)
    print("[CLOSED] application closed.", flush=True)
    file_hr.close()
    file_ecg.close()
    file_rr.close()
    sys.exit(0)


async def main(ADDRESS):
    try:
        async with BleakClient(ADDRESS) as client:
            tasks = [
                asyncio.ensure_future(run(client, True)),
            ]
            await asyncio.gather(*tasks)
    except:
        pass


def exit_handler():
    file_hr.close()
    file_ecg.close()
    file_rr.close()


list_polar = {
    "25EECC29": "EF:26:15:E6:2E:9F",
    "25EF1825": "FC:40:BC:A4:D5:63",
    "mac": "CBA0632A-D411-A506-D4D1-2037F314ECF8"
}


if __name__ == "__main__":
    anonymat = input('Numéro d\'anonymat: \n')
    now = datetime.datetime.now()
    now = f'{now.day}{now.month}{now.year}{now.hour}{now.minute}{now.second}'
    file_hr = open(f'rawdata/{anonymat}_raw_hr.csv', 'a+')
    file_rr = open(f'rawdata/{anonymat}_raw_rr.csv', 'a+')
    file_ecg = open(f'rawdata/{anonymat}_raw_ecg.csv', 'a+')

    file_rr.write("timestampPC;ibi;marker\n")
    file_hr.write("timestampPC;hr;marker\n")
    file_ecg.write("timestampPolar;timestampPC;ecg;marker\n")

    i = 0
    for key, _ in list_polar.items():
        i += 1
        print(f"{i}: {key}")

    num = input('Choix ?\n')
    address = list(list_polar.values())[int(num)-1]
    print(address)

    atexit.register(exit_handler)
    x = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(address))
