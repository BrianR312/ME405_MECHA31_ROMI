## Lab_02 Driver Class ##

# Motor L: Tim4_Ch1 (PB6), Motor Enable (PB1), Motor Direction (PB2)
# left = Motor(Pin.cpu.B6, Pin.cpu.B2, Pin.cpu.B1, 4)

from pyb import Timer
from pyb import Pin

class motor_driver:
    '''A motor driver interface encapsulated in a Python class. Works with
       motor drivers using separate PWM and direction inputs such as the DRV8838
       drivers present on the Romi chassis from Pololu.'''
    
    def __init__(self, tim_num, tim_chan, PWM, DIR, nSLP):
        '''Initializes a Motor object'''
        self.tim = Timer(tim_num, freq=20000)                       
        self.Dir = Pin(DIR, mode=Pin.OUT_PP, value=0)
        self.nSLP_pin = Pin(nSLP, mode=Pin.OUT_PP, value=0)
        self.tim_ch = self.tim.channel(tim_chan, pin=PWM, mode=Timer.PWM, pulse_width_percent=0)

    def set_effort(self, effort):
        '''Sets the present effort requested from the motor based on an input value
           between -100 and 100'''
        effort = max(-100, min(100, effort))

        if effort >= 0:
            self.Dir.low()
            self.tim_ch.pulse_width_percent(effort)
        else:
            self.Dir.high()
            self.tim_ch.pulse_width_percent(-effort)

            
    def enable(self):
        '''Enables the motor driver by taking it out of sleep mode into brake mode'''
        self.nSLP_pin.high()
            
    def disable(self):
        '''Disables the motor driver by taking it into sleep mode'''
        self.nSLP_pin.low()
        self.set_effort(0)