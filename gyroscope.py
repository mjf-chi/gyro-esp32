import struct


class L3GD20:

    I2C_ADDR = 0x6B
    REG_CTRL1 = 0x20
    REG_CTRL4 = 0x23
    REG_OUT_XL = 0x28
    REG_OUT_YL = 0x2A
    REG_OUT_ZL = 0x2C

    RANGE_250DPS = 0x00
    RANGE_500DPS = 0x10
    RANGE_2000DPS = 0x20

    def __init__(self, bus, rng=None):
        self._bus = bus
        self._range = None
        self._dps = 0
        # enable all three channels (x,y, z) and reset to normal mode
        self._bus.writeto(self.I2C_ADDR, bytearray([self.REG_CTRL1, 0b00000000,]))
        self._bus.writeto(self.I2C_ADDR, bytearray([self.REG_CTRL1, 0b00001111,]))
        if range is not None:
            self.range = rng
        else:
            self.range = self.RANGE_2000DPS
        
    @property
    def range(self):
        return self._range
    
    @range.setter
    def range(self, new_range):
        self._range = new_range
        if self._range == self.RANGE_250DPS:
            self._dps = 0.00875
        elif self._range == self.RANGE_500DPS:
            self._dps = 0.0175
        elif self._range == self.RANGE_2000DPS:
            self._dps = 0.07
        self._bus.writeto(self.I2C_ADDR, bytearray([self.REG_CTRL4, self._range]))

    def read_register(self, addr, l):
        data = bytearray()
        for i in range(0, l):
            self._bus.writeto(self.I2C_ADDR, bytearray([addr + i,]))
            data += bytearray(self._bus.readfrom(self.I2C_ADDR, 1))
        return data

    def sample(self):
        # self._bus.writeto(self.I2C_ADDR, bytearray([self.REG_OUT_XL,]))
        # data = self._bus.readfrom(self.I2C_ADDR, 2)
        
        data = self.read_register(self.REG_OUT_XL, 2)
        data += self.read_register(self.REG_OUT_YL, 2)
        data += self.read_register(self.REG_OUT_ZL, 2)

        measurement = struct.unpack('<hhh', bytearray(data))
        
        return (
            measurement[0] * self._dps, 
            measurement[1] * self._dps, 
            measurement[2] * self._dps)