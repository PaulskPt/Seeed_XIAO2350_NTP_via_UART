from lib.sdcard import SDCard
from machine import Pin
import os, sys

def mount_sd():
    PIN_SD_SCK  = machine.Pin.board.GP2
    PIN_SD_MOSI = machine.Pin.board.GP3
    PIN_SD_MISO = machine.Pin.board.GP4
    PIN_SD_CS   = machine.Pin.board.GP28

    # Setup for SD Card
    sd_spi = machine.SPI(0, 
        sck=machine.Pin(PIN_SD_SCK,   machine.Pin.OUT),
        mosi=machine.Pin(PIN_SD_MOSI, machine.Pin.OUT),
        miso=machine.Pin(PIN_SD_MISO, machine.Pin.OUT))

    sd = SDCard(sd_spi, machine.Pin(PIN_SD_CS))
    try:
        os.mount(sd, "/sd")
        print("SDCard mounted")
        return True
    except OSError as exc:
        print("mounting SDCard failed")
        sys.print_exception(exc)
        return False

if __name__ == '__main__':
    mount_sd()