# Seeed XIAO RP2350 NTP via UART

# PURPOSE OF THIS REPO:

Receiving an NTP datetime serial (unixtime) by one device (Pimoroni Pico Plus 2 with external Pimoroni RM2 Module)
and sending this unixtime to a second device (Seeed XIAO RP2350 mounted on top of a Seed Expansion Board Base)

See the folder ```src```
This folder contains two sub-folders: 
```
    Pimoroni_Pico_Plus2
    Seeed_XIAO_RP2350
```

The folder ```src/Pimoroni_Pico_Plus2``` contains:
```
    main.py
    secrets.py
```

The folder ```src/XIAO_RP2350``` contains the following subfolders with file(s):
```
    lib [dir]
        sdcard.py
    sd  [dir]
        lib [dir]
            bme280_f.py
            mcp9808.py
            pcf8563.py
            sdcard.py
            secrets.py
            ssd1306.py
```

Because the XIAO RP2350 has limited memory. Library modules are saved on an SD-Card. 
However in the memory of the XIAO RP2350 I created a folder ```lib```. In it I saved the file ```sdcard.py```.
This is called by ```boot.py``` mount an SD-Card. An SD-Card is necessary (see explanation below).

The current setting of  in file ```secrets.py``` is set for the time zone of Europe/Lisbon
which is GMT +1.

```
TIMEZONE_OFFSET = "1" # One hour for Europe/Lisbon
```

Images. See the folder ```images```.

Shell (serial) output text files: see folder ```docs```.


# THE TRANSMITTING DEVICE

In the global variables section of the script: ```main.py``` 
```
    from secrets import SSID, PASSWORD, TIMEZONE_OFFSET
    tz_offset = int(TIMEZONE_OFFSET)  # convert string to an integer value

```

# THE RECEIVING DEVICE

In the global variables section of the script: ```main.py``` 
```
    from secrets import TIMEZONE_OFFSET
    tz_offset = int(TIMEZONE_OFFSET)  # convert string to an integer value
```

Because the Seeed XIAO RP2350 with Seeed Expansion Board Base has no WiFi capabilities,
I opted to use a second board, in this case a Pimoroni Pico Plus 2 with an external Pimoroni Pico Plus 2 module to furnish the WiFi connection. Upon reset the Pico Plus2 with RM2 module connects to a WiFi access point for which the file ```secrets.py``` contains the neccessary SSID and PASSWORD. At intervals of (in this moment) 1 minute, the Pico Plus 2 will get a unixtime serial from an NTP-server. If this unixtime is received, the Pico Plus 2 will transmit this unixtime via a serial connection (UART) to the XIAO RP2350.

You can connect various sensors to the XIAO Expansion Board Base. In this example I have connected the following two sensors to the Expansion Board Base:
```
    a) a Pimoroni Multi-sensor-stick (PIM 745), containing three sensors. One of them is a BME280 (temperature, pressur and humidity) sensor;
    b) an Adafruit MCP9808 temperature sensor.
```
Only one of these two sensors is used. You can choose which sensor by setting or clearing the following ```global variables```:
```
    use_mcp9808 = False
    use_bme280  = True
```

The Seeed Expansion Board Base has a monochrome OLED display.
The following data will be displayed:
```
    Sensor Temperature in ºC / Pressure in hPa / Humidity in %rH    (in subsequent displays)
    Date: yyyy-mo-dd
    WeekDay hh:mm:ss
```

The serial communication between the transmitting device and the receiving device is set for a speed of 9600 bits-per-second.
The unixtime will be packed before transmission. After reception the unixtime will be unpacked.


# MORE PRINT OUTPUT
Each ```main.py``` has in the global variables secion a variable ```my_debug```. If you set this to ```True```, the script will print more information to the serial monitor output.

# KNOWN ISSUES:
With Micropython it is common that at reset a device will run in this order:
```
    1) boot.py
    2) main.py
```

My experience with the XIAO RP2350 on top of the Seeed Expansion Board Base, at a reset will run ```boot.py```, however it does not run ```main.py```.
I am investigating the cause of this anomaly behaviour.



