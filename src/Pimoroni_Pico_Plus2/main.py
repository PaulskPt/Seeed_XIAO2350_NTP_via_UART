#
# 2025-05-08 main.py
# by Paulus Schulinck (Github handle: @PaulskPt)
# for the Pimoroni pico plus 2 with connected a Pimoroni RM2 WiFi/BT module
# sending ntp unixtime via UART to another device (XIAO RP2350 on top of a Seed Expansion Board Base)
# License: MIT
import network
import ntptime
from machine import Pin, UART
from rp2 import country
from time import sleep, ticks_ms
import utime
from secrets import SSID, PASSWORD, TIMEZONE_OFFSET
import struct
        
unixtime = 0
tz_offset = int(TIMEZONE_OFFSET)

led = Pin(25, Pin.OUT)
led.value(0)

tx = Pin(0, Pin.OUT)
rx = Pin(1, Pin.IN)
uart = UART(0, 9600, tx = machine.Pin.board.GP0, rx= machine.Pin.board.GP1)
#uart.init(9600, bits=8, parity=None, stop=1)

# connect to wifi
wlan = network.WLAN(network.STA_IF, pin_on=32, pin_out=35, pin_in=35, pin_wake=35, pin_clock=34, pin_cs=33)

#rp2.country('PT')

monthsLst = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

wdDict = {0: "Mon",
          1: "Tue",
          2: "Wed",
          3: "Thu",
          4: "Fri",
          5: "Sat",
          6: "Sun"}

def do_connect():
    wlan.active(True)
    try_cnt = 0
    try:
        wlan.connect(SSID, PASSWORD)
    except OSError as error:
        print(f'error is {error}')

    msg_shown = False
    stop = False
    while wlan.isconnected() is False:
        led.value(0)
        if not msg_shown:
            msg_shown = True
            print('Waiting for connection...')
        try_cnt += 1
        if try_cnt > 10:
            print(f"WiF connection failed.")
            wlan.active(False)
            stop = True
            break
        sleep(1)
    if not stop:
        led.value(1)
        print("wlan connected to: \"{}\"".format(SSID), end="\n")
        print("IP address = \"{}\"".format(wlan.ifconfig()[0]), end="\n\n")

def cleanup():
    if wlan.isconnected() == True:
        wlan.disconnect()
    led.value(0)
    
def handle_ntp():
    global unixtime
    ntp_time = 0
    local_time = tuple() # create an empty tuple
    yy = 0 # 2025   ( when unixtime = 1746474098)
    mo = 1 # 5
    dd = 2 # 5
    hh = 3 # 19
    mi = 4 # 41
    ss = 5 # 38
    wd = 6 # 0 = monday
    yd = 7 # 125 day of the year
    
    try:
        ntp_time = ntptime.time()  # get datetime (UNIX TIME) (EPOCH)
    except OSError as exc:
        print(f"OSError: {exc.args[0]}, {exc}")

    # Example Unix time (seconds since January 1, 1970)
    # unix_time = 1672531199   Equivalent to 2023-01-01 00:00:00

    # Convert Unix time to a tuple representing the local time
    unixtime = ntp_time
    local_time = utime.localtime(unixtime) # GMT +/- tz_offset

    # Format the local time as a datetime string
    datetimeStr = "{:s} {:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z yday {:d}".format(
        wdDict[local_time[wd]],
        local_time[yy], local_time[mo], local_time[dd], 
        local_time[hh], local_time[mi], local_time[ss],
        local_time[yd]
    )

    print("datetime from NTP server = {}".format(datetimeStr), end='\n')
    #datetimeStr = "2024-12-10T00:31:18Z"
    
def send_unix():
    global unixtime
    if unixtime > 0:
        led.value(1)
        # Example Unix timestamp
        # unixtime = 1714936871  # Replace this with your actual Unix timestamp
        # 1714936871 dec = 6637 DC37 hex = 0110 0110 0011 0111 1101 1100 0010 0111 = 8 bytes = 32bits

        # Convert to bytearray (4 non-packed bytes for a 32-bit integer, 8 non-packed bytes for a 64-bit integer)
        tx_buf = struct.pack(">L", unixtime)  # Use 'L' for a 32-bit (unsigned long int)

        uart.write(tx_buf)
        print(f"unixtime {unixtime}, tx_buf = {tx_buf}, list(tx_buf) = {list(tx_buf)} sent via UART")
        sleep(1) # leave led on for one second
        led.value(0)

start_t = ticks_ms()

def main():
    global start_t
    curr_t = 0
    interval_t = 1 * 60 * 1000 # 5 minutes
    elapsed_t = 0
    start = True
    print(f"main(): unixtime send interval = {int(interval_t/60000)} minutes")
    while True:
        if wlan.isconnected() == False:
            do_connect()
        # Check again at interval
        curr_t = ticks_ms()
        elapsed_t = curr_t - start_t
        if start or elapsed_t >= interval_t:
            start = False
            start_t = curr_t
            if wlan.isconnected() == True:
                handle_ntp()
                send_unix()
 
        sleep(10)
    
if __name__ == "__main__":
    main()
