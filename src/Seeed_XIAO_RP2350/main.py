import time
import struct
import array, random
from machine import Pin, UART
import rp2
import utime
import os

use_bme280 = True
use_mcp9808 = False
my_debug = False
 
# Micropython script for a Seeed XIAO RP2350 attached to a Seeed Expansion Board Base
# Test to receive ntp unixtime from another device: Pimoroni Pico Plus 2 with RM2 module attached
# also display/print sensor values from either mcp9808 or bme280 (see global flags below).
# by Paulus Schulinck (Github handle: @PaulskPt)
# 2025-05-08
# License: MIT
# Note: script uses modules in /sd/lib. The script in boot.py tries to mount the SDCard
#
# See: https://github.com/orgs/micropython/discussions/15292
# Post: "SOLUTION" by @wbeebe
# UPDATE 18 June 2024


"""
   Notes PaulskPt:
   After reading the "SOLUTION" by @wbeebe, I tried the following in Thonny Shell:
   >>> import machine
   >>> i0=machine.I2C(0)
   >>> i0
   I2C(0, freq=400000, scl=5, sda=4, timeout=50000)
   >>> 
   >>> i1=machine.I2C(1)
   >>> i1
   I2C(1, freq=100000, scl=7, sda=6, timeout=50000)
   >>>
   So, instead of:
     PIN_WIRE1_SCL = machine.Pin.board.GP7
     PIN_WIRE1_SDA = machine.Pin.board.GP6
    i2c = machine.I2C(id=1, scl=machine.Pin(PIN_WIRE1_SCL), 
        sda=machine.Pin(PIN_WIRE1_SDA), freq=100000)
   I used:
       i2c=machine.I2C(1)
   That worked!
"""

i2c=machine.I2C(1)

try:
    os.chdir('/sd')

    from lib.pcf8563 import *
    if use_mcp9808:
        from lib.mcp9808 import MCP9808
    if use_bme280:
        from lib.bme280_f import BME280
    from lib.ssd1306 import SSD1306_I2C
    tz_offset = 0
    from lib.secrets import TIMEZONE_OFFSET # get the local timezone offset from GMT
    tz_offset = int(TIMEZONE_OFFSET)
    print(f"TIMEZONE_OFFSET = {TIMEZONE_OFFSET}")
    
    os.chdir('/')
    
except OSError as exc:
    print(f"Error: {exc}")
    raise


if use_mcp9808:
    sensor = MCP9808(i2c) # create an instance of the MCP9808 sensor object
if use_bme280:
    bme280 = BME280(i2c=i2c)

oled = SSD1306_I2C(128, 32, i2c) # create an instance of the OLED object
 
rtc = PCF8563(i2c) # create an instance of the rtc object
if my_debug:
    print(f"type(rtc) = {type(rtc)}")

monthsLst = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

wdDict = {0: "Mon",
          1: "Tue",
          2: "Wed",
          3: "Thu",
          4: "Fri",
          5: "Sat",
          6: "Sun"}

brill = 10  # Let the RGB Led shine just a bit

RED   = (0,   brill,     0)
BLUE  = (brill,   0,     0)
GREEN = (0,       0, brill)
BLACK = (0,       0,     0)


uart = UART(0, 9600, tx = machine.Pin.board.GP0, rx= machine.Pin.board.GP1)
if my_debug:
    print(f"type(uart) = {type(uart)}")

local_time_lst = []
weekdayStr = ""
yearday = 0
#    yy, mo, dd, wd, hh, mm, ss
# dt = (25, 5, 5, 0, 18, 20, 40) # pro-forma datetime tuple
# rtc.DateTime(dt) # set the rtc
if my_debug:
    print(rtc.DateTime())

# setup for RGB Led:
NUM_LEDS = 1
LED_PIN = 22    # PICO_DEFAULT_WS2812_PIN
POWER_PIN = 23  # PICO_DEFAULT_WS2812_POWER_PIN

# Global brightness variable (0.0 to 1.0)
BRIGHTNESS = 0.1

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)

def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

# Set up the power pin
power_pin = Pin(POWER_PIN, Pin.OUT)
power_pin.value(1)  # Turn on power to the LED

# Create the StateMachine with the ws2812 program, outputting on LED_PIN
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(LED_PIN))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)

def set_led_color(color):
    #TAG = "set_led_color(): "
    color2 = 0
    if isinstance(color, tuple):
        color2 = color[0] | (color[1] << 8) | (color[2] << 16)
        #print(TAG + "color = ({:d},{:d},{:d})".format(color[0], color[1], color[2]))
        #print(TAG + "color2 = 0x{:02x}".format(color2))
    else:
        color2 = color
    sm.put(array.array("I", [color2]), 8)

#--- end of setup for RGB Led ---


def handle_rx_buf(rx_buf):
    global unixtime, weekdayStr, yearday
    t1 = "Unable to get time from NTP server.\n\nCheck your network and try again."
    TAG = "handle_rx_buf(): "
    ret = False
    line = 67 * '-'
    # Handle the received unixtime
    ux_val = 0

    if isinstance(rx_buf, bytes):
        set_led_color(GREEN)
        print(line)
        print(TAG + "unixtime data received via UART")
        # print(f"rx_buf = {rx_buf}, list(rx_buf) = {list(rx_buf)}")
        try:
            for i in range(3, 0, -1):
                if rx_buf[i] == 0:
                    break
        except IndexError: # occurred when something erratically occurred,
            #                for instance that the other device was reset.
            set_led_color(BLACK)
            return ret
        if i > 0:
            if my_debug:
                print(TAG + f"nr of bytes (with a value > 0) = {i}")
            # Convert bytearray back to integer
            ux_val = struct.unpack(">L", rx_buf)[0]  # 'L' is for a 32-bit integer (unsigned long)
            if my_debug:
                print(TAG + f"rx_buf = {rx_buf}, ux_val = {ux_val}")
            if ux_val <= 0:
                set_led_color(BLACK)
                return ret
                
        time.sleep(0.01)
    if ux_val > 0:
        unixtime = ux_val + (tz_offset * 3600)
        if my_debug:
            print(TAG + f"ux_val = {ux_val}, unixtime (+ timezone offset) = {unixtime}")
        #unix_to_rtc()
        gmtTime = utime.localtime(ux_val)
        loctime = utime.localtime(unixtime)
        if my_debug:
            print(TAG + f"gmtTime = {gmtTime}")
            print(TAG + f"loctime = {loctime}")
        upd_time = ( loctime[0], loctime[1], loctime[2],
                     loctime[6],
                     loctime[3], loctime[4], loctime[5])
        weekdayStr = wdDict[loctime[6]]
        yearday = loctime[7]
        rtc.DateTime(upd_time)
        if not my_debug:
            print(TAG + f"rtc updated from ntp: {rtc.DateTime()}")
        print(line)
        time.sleep(1) # leave the RGB Led on for a while!
        
        ret = True

    set_led_color(BLACK)
    return ret

def weekday():
    dt = rtc.DateTime()
    # print(f"weekday(): dt = {dt}")
    if dt[3] in wdDict.keys():
        wDay = wdDict[dt[3]]
    else:
        wDay = "?"
    return wDay
 
def dtToStr():
    loctime = rtc.DateTime()
    if not my_debug:
        print(f"dtToStr(): rtc.DateTime() = {loctime}")
    return "{:s} {:4d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        wdDict[loctime[3]],
        loctime[0], loctime[1], loctime[2],
        loctime[4], loctime[5], loctime[6])

def intro_msg():
    t_lst = ["XIAO RP2350 ", "NTP unixtime ", "via UART ", "from ", "Pimoroni ", "Pico Plus 2"]
    oled.fill(0)
    oled.text(t_lst[0], 0, 0)
    print(t_lst[0], end='')
    oled.text(t_lst[1], 0, 10)
    print(t_lst[1], end='')
    oled.text(t_lst[2], 0, 20)
    print(t_lst[2], end='')
    oled.show()
    time.sleep(3)
    oled.fill(0)
    oled.text(t_lst[3], 0, 0)
    print(t_lst[3], end='')
    oled.text(t_lst[4], 0, 10)
    print(t_lst[4], end='')
    oled.text(t_lst[5], 0, 20)
    print(t_lst[5], end='\n')
    oled.show()
    time.sleep(3)

def main():
    buflen = 10
    if use_bme280:
        bme_val_idx = 0

    show_keep_cnt = 0
    show_keep_max = 4
    intro_msg()
    t2 = ""
    while True:
        try:
            rx_buf = bytearray(buflen) # create a clean buffer
            rx_buf = uart.read()
            # print(f"type(rx_buf) = {type(rx_buf)}")
            if isinstance(rx_buf, bytes):
                handle_rx_buf(rx_buf)
            if use_mcp9808:
                tempC = sensor.get_temp()
                if isinstance(tempC, float):
                    t = "Temp: {:<5.2f}C".format(tempC)
            if use_bme280:
                if not my_debug:
                    v = bme280.values
                    print(f"\nbme280.values = {v}")
                    # example: bme280.values = ('22.40C', '1000.68hPa', '43.85%')

  
                t = ""
                if bme_val_idx == 0:
                    t = "Temp: {:s}".format(v[0])
                if bme_val_idx == 1:
                    t = "Press:{:s}".format(v[1])
                if bme_val_idx == 2:
                    t = "Hum: {:s}".format(v[2])
            if show_keep_cnt == 0:
                # leave the value the same for five iterations
                # to keep the view less nervous
                t2 = t
            dt = rtc.Date()
            print(f"date    = {dt}")
            tm = rtc.Time()
            print(f"time    = {tm}")
            print(f"weekday = {weekdayStr}")
            print(f"yearday = {yearday}")
            print(dtToStr(), end ='')
            print(' ', end='')
            print(t2)
            
            oled.fill(0)
            oled.text(t2,  0,  0)
            oled.text(dt, 0, 10)
            oled.text(weekday(), 0, 20)
            oled.text(tm, 30, 20)

            oled.show()
            if use_bme280 and show_keep_cnt == 0:
                bme_val_idx += 1
                if bme_val_idx >=3:
                    bme_val_idx = 0
            show_keep_cnt += 1
            if show_keep_cnt > show_keep_max:
                show_keep_cnt = 0
            time.sleep(1)
            
        except OSError as exc:
            print(f"Error: {exc.args[0]}")
            
if __name__ == '__main__':
    main()
