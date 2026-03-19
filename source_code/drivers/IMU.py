## Lab_06 IMU Class##

from pyb import Pin, Timer, I2C
from time import sleep_ms
import struct

class IMU:
    '''A 9 DOF IMU decoding interface encapsulated in a Python class'''

    def __init__(self, i2c):
        '''Initializes BNO055 in High mode'''
        self.i2c = i2c
        self.address = (0x28)                # Configured in HIGH mode, 5V pin


    def configure(self):
        '''Configures BNO055 in IMU mode'''
        self.i2c.mem_write(0b1100, self.address, 0x3D)   # Hardcoded into IMU mode 0b1000, 1100 is other
        pass

    def getStatus(self):
        print((self.i2c.mem_read(1, self.address, 0x35)))

    def calRead(self):
        '''Read and parse calibration status'''
        self.calStatus = self.i2c.mem_read(1, self.address, 0x35)
        self.sysStatus = self.calStatus[0]>>6 & 0b11
        self.gyroStatus = self.calStatus[0]>>4 & 0b11
        self.accelStatus = self.calStatus[0]>>2 & 0b11
        self.magStatus = self.calStatus[0] & 0b11
        return self.sysStatus, self.gyroStatus, self.accelStatus, self.magStatus

    def coefRead(self):
        '''Read Calibration Coefficients'''
        self.i2c.mem_write(0b0000, self.address, 0x3D)                   # Put device into config mode
        sleep_ms(25)
        self.calCoeffs = (self.i2c.mem_read(22, self.address, 0x55))
        sleep_ms(25)
        self.i2c.mem_write(0x0C, self.address, 0x3D)                   # Put device back into NDOF mode
        return self.calCoeffs

    def coefWrite(self, coeffs):
        '''Write Calibration Coefficients from a stored Byte Array'''
        self.i2c.mem_write(0b0000, self.address, 0x3D)                   # Put device into config mode
        sleep_ms(25)
        self.writeCalCoeffs = self.i2c.mem_write(coeffs, self.address, 0x55)
        sleep_ms(25)
        self.i2c.mem_write(0x0C, self.address, 0x3D)                   # Put device back into NDOF mode
        pass

    def eulRead(self):
        '''Read Euler Angles and Use as Measurements'''
        self.rawHead  = self.i2c.mem_read(2, self.address, 0x1A)
        self.rawRoll  = self.i2c.mem_read(2, self.address, 0x1C)
        self.rawPitch = self.i2c.mem_read(2, self.address, 0x1E)

        self.eulHead  = struct.unpack('<h', self.rawHead)[0]  / 16.0    # Change Outputs into deg
        self.eulRoll  = struct.unpack('<h', self.rawRoll)[0]  / 16.0
        self.eulPitch = struct.unpack('<h', self.rawPitch)[0] / 16.0
        return self.eulHead, self.eulRoll, self.eulPitch
    
    def rateRead(self):
        '''Read Rate of Rotation'''
        self.rawX = self.i2c.mem_read(2, self.address, 0x14)
        self.rawY = self.i2c.mem_read(2, self.address, 0x16)
        self.rawZ = self.i2c.mem_read(2, self.address, 0x18)

        self.xRead = struct.unpack('<h', self.rawX)[0] / 16.0   # Change Outputs into deg/s
        self.yRead = struct.unpack('<h', self.rawY)[0] / 16.0
        self.zRead = struct.unpack('<h', self.rawZ)[0] / 16.0
        return self.xRead, self.yRead, self.zRead
    
