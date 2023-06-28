import asyncio
import time
from math import ceil
import datetime

from bleak import BleakClient, BleakScanner


address = "24:71:89:cc:09:05"
MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
HEART_RATE_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
BODY_SENSOR_LOC_UUID = "00002a38-0000-1000-8000-00805f9b34fb"

PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8"

current_hr = 0

async def main(address):
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)
        if hasattr(d.name, '__iter__') and "Polar" in d.name:
            print(d.name)
            print(d.address)
            address = d.address


asyncio.run(main(address))

    
