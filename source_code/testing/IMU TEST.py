# TEST IMU

from pyb import I2C, Pin
from IMU import IMU
import struct
import time

temp = 0

i2c = I2C(1, I2C.CONTROLLER)
s = IMU(i2c)

print("INPUT COEFFS")
time.sleep(0.5)

print("START")
s.configure()
time.sleep(0.5)
while True:
    sys, gyro, accel, mag = s.calRead()
    print(f"Sys:{sys} Gyro:{gyro} Accel:{accel} Mag:{mag}")
   
    if gyro == 3 and accel == 3:
        print("Fully calibrated! Saving coefficients...")
        coeffs = s.coefRead()
        print(coeffs)
        break
   
    time.sleep(.5)  # check every 500ms




# bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe0\x01')

