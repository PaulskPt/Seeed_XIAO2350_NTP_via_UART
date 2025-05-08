'''
 PCF8563 Real Time Clock Driver
 for the BBC micro:bit

 Based on DS3231 driver by: shaoziyang
 Date: 2018.2
 http://www.micropython.org.cn

 Modified & Extended by fredscave.com
 DATE: 2024.9
'''

# from machine import i2c
from micropython import const

I2C_ADDR   = const(0x51)
REG_CTRL2  = const(0x01)
REG_SEC    = const(0x02)
REG_MIN   = const(0x03)
REG_HR    = const(0x04)
REG_DAY   = const(0x05)
REG_WDAY  = const(0x06)
REG_MON   = const(0x07)
REG_YR    = const(0x08)
REG_ALMIN = const(0x09)
REG_ALHR  = const(0x0A)
REG_ALDAY = const(0x0B)
REG_ALWDAY = const(0x0C)
REG_TIMER  = const(0x0F)
REG_TIMER_CTRL = const(0x0E)

class PCF8563():
    def __init__(self, i2c=None, addr=I2C_ADDR):
        if i2c is None:
            raise ValueError("parameter i2c has to be an object")
        else:
            self._i2c = i2c
        
        self._addr = addr

        self.setReg(REG_CTRL2, 0b00000011)

    def DecToHex(self, dat):
        return (dat//10) * 16 + (dat%10)

    def HexToDec(self, dat):
        return (dat//16) * 10 + (dat%16)

    def setReg(self, reg, dat):
        self._i2c.writeto(self._addr, bytearray([reg, dat]))

    def getReg(self, reg):
        self._i2c.writeto(self._addr, bytearray([reg]))
        return self._i2c.readfrom(self._addr, 1)[0]

    def CLOCKstatus(self):
        if (self.getReg(REG_SEC) >> 7) == 0:
            return True
        else:
            return False

    def Sec(self, sec = None):
        if sec == None:
            return self.HexToDec(self.getReg(REG_SEC) & 0b01111111)
        else:
            self.setReg(REG_SEC, self.DecToHex(sec%60))

    def Mins(self, mins = None):
        if mins == None:
            return self.HexToDec(self.getReg(REG_MIN) & 0b01111111)
        else:
            self.setReg(REG_MIN, self.DecToHex(mins%60))

    def Hr(self, hr = None):
        if hr == None:
            return self.HexToDec(self.getReg(REG_HR) & 0b00111111)
        else:
            self.setReg(REG_HR, self.DecToHex(hr%24))

    def Wday(self, wday = None):
        if wday == None:
            return self.HexToDec(self.getReg(REG_WDAY) & 0b00000111)
        else:
            self.setReg(REG_WDAY, self.DecToHex(wday%7))

    def Day(self, day = None):
        if day == None:
            return self.HexToDec(self.getReg(REG_DAY) & 0b00111111)
        else:
            self.setReg(REG_DAY, self.DecToHex(day%32))

    def Mon(self, mon = None):
        if mon == None:
            return self.HexToDec(self.getReg(REG_MON) & 0b00011111)
        else:
            self.setReg(REG_MON, self.DecToHex(mon%13))

    def Yr(self, yr = None):
        if yr == None:
            return self.HexToDec(self.getReg(REG_YR)) + 2000
        else:
            self.setReg(REG_YR, self.DecToHex(yr%100))

    def DateTime(self, dat = None):
        if dat == None:
            return [self.Yr(), self.Mon(),
                    self.Day(),self.Wday(),
                    self.Hr(), self.Mins(), self.Sec()]
        else:
            self.Yr(dat[0])
            self.Mon(dat[1])
            self.Day(dat[2])
            self.Wday(dat[3])
            self.Hr(dat[4])
            self.Mins(dat[5])
            self.Sec(dat[6])

    def Time(self, h=None, m=None, s=None):
        if (h==None) and (m==None) and (s==None):
            str_sec = "%02d" % self.Sec()
            str_min = "%02d" % self.Mins()
            str_hr = "%02d" % self.Hr()
            return str_hr + ':' + str_min + ':' + str_sec
        if (s != None):
            self.Sec(s)
        if (m != None):
            self.Mins(m)
        if (h != None):
            self.Hr(h)

    def Date(self, y=None, m=None, d=None, fmt=1):
        # fmt = 1; YMD
        # fmt = 2; DMY
        # fmt = 3; MDY
        if (y==None) and (m==None) and (d==None):
            str_day = "%02d" % self.Day()
            str_mon = "%02d" % self.Mon()
            str_yr = "%04d" % self.Yr()
            if fmt == 1:
                return str_yr + '-' + str_mon + '-' + str_day
            if fmt == 2:
                return str_day + '-' + str_mon + '-' + str_yr
            if fmt == 3:
                return str_mon + '-' + str_day + '-' + str_yr
            return None
        if (d != None):
            self.Day(d)
        if (m != None):
            self.Mon(m)
        if (y != None):
            self.Yr(y)

    def ALARMset(self, mins=None, hr=None):
        if (mins == None) and (hr == None):
            return
        self.ALARMclear()
        self.ALARMoff()
        if mins != None:
            self.setReg(REG_ALMIN, self.DecToHex(mins%60))
        if hr != None:
            self.setReg(REG_ALHR, self.DecToHex(hr%24))


    def ALARMclear(self):
        reg = self.getReg(REG_CTRL2)
        self.setReg(REG_CTRL2, reg & 0b00000111)

    def ALARMtriggered(self):
        trig = (self.getReg(REG_CTRL2) & 0b00001000) >> 3
        if trig:
            self.TIMERclear()
        return trig

    def ALARMoff(self):
        self.setReg(REG_ALMIN, 0b10000000)
        self.setReg(REG_ALHR, 0b10000000)
        self.setReg(REG_ALDAY, 0b10000000)
        self.setReg(REG_ALWDAY, 0b10000000)

    def TIMERset(self, s=None):
        if s == None:
            return
        self.TIMERoff()
        self.setReg(REG_TIMER, s)
        self.setReg(REG_TIMER_CTRL, 0b10000010)

    def TIMERtriggered(self):
        trig = (self.getReg(REG_CTRL2) & 0b00000100) >> 2
        if trig:
            self.TIMERclear()
        return trig

    def TIMERoff(self):
        self.setReg(REG_TIMER_CTRL, 0b00000011)
        self.setReg(REG_TIMER, 0x00)
        self.TIMERclear()

    def TIMERclear(self):
        reg = self.getReg(REG_CTRL2)
        self.setReg(REG_CTRL2, reg & 0b00001011)
