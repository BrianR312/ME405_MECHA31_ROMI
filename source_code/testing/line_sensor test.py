# line_sensor test #

from pyb import Pin
from line_sensor import line_sensor
from time import sleep_ms

l = line_sensor(Pin.cpu.B0, Pin.cpu.C0, Pin.cpu.C1, Pin.cpu.C2, Pin.cpu.C3, Pin.cpu.A4)
l.enable()
cal_white_boo = l.calBlack()
print(cal_white_boo)
sleep_ms(5000)
cal_white_yay = l.calWhite()


print(cal_white_yay)


