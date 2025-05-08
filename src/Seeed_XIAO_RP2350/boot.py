# boot.py
# created for Seeed XIAO RP2350 with Seeed Epansion Board Base
# for MicroPython
# 2025-05-05 by Paulus Schulinck (Github handle: @PaulskPt)
# The idea is to call this script after booting
# and then use library files that are on the SDCard in folder /sd/lib
#
import os

my_debug = False

curDir = os.listdir()
if my_debug:
    print(f"at start: current dir = \"{curDir}\"")
isLib = False
for _ in os.ilistdir():
    # print(_)
    if _[0] == 'lib':
        isLib = True
        if my_debug:
            print("system dir \"lib\" found")
        break

try:
    if isLib:
        os.chdir("lib")
    else:
        os.chdir("/")
    if my_debug:
        print(f"changed to system dir: \"{os.getcwd()}\"")
    from sdcard import SDCard
    if my_debug:
        print("module sdcard.SDCard imported")
except OSError as exc:
    print(f"Error: {exc}")
except ImportError:
    raise

import machine
import time
import sys

fileTypeDir  = 0x4000
fileTypeFile = 0x8000

PIN_SD_SCK  = machine.Pin.board.GP2
PIN_SD_MOSI = machine.Pin.board.GP3
PIN_SD_MISO = machine.Pin.board.GP4
PIN_SD_CS   = machine.Pin.board.GP28 # A2/D2

# Setup for SD Card
sd_spi = machine.SPI(0, 
        sck=machine.Pin(PIN_SD_SCK,   machine.Pin.OUT),  # for Presto it was pin 34
        mosi=machine.Pin(PIN_SD_MOSI, machine.Pin.OUT),  # same, pin 35
        miso=machine.Pin(PIN_SD_MISO, machine.Pin.OUT))  # same, pin 36

os.chdir("/")
if my_debug:
    print(f"changed to system dir: \"{os.getcwd()}\"")

sd = SDCard(sd_spi, machine.Pin(PIN_SD_CS))       # same, pin 39

try:
    # Mount the SD to the directory 'sd'
    os.mount(sd, "/sd")
    os.chdir("/sd")
    
    print("SDCard mounted")
    if my_debug:
        print(f"Changed to SDCard directory: \"{os.getcwd()}\"")
    ret = True
except OSError as exc:
    print("mounting SDCard failed")
    sys.print_exception(exc)

