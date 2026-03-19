from pyb import ADC
from pyb import Timer
from pyb import Pin

class line_sensor:
    '''Line sensor class for ROMI project. Interfaces with QTR-HD-05A Reflectance Sensor Array
       from Polulu.'''
    
    # NOTES FROM WEBSITE #

    # CTRL ODD and CTRL EVEN pins are connected and can take 2 inputs OR 1 input
    # CTRL LOW = emitters off 
    # PIN = PB0
    # 
    # Set up timer for consistent readings? Interrupt? Check max late value when run
    #
    # Need 5 ADC_IN pins for output (see STM32L476 Datasheet)
    # Pins will be PC0, PC1, PC2, PC3, PA4

    # NOTES FROM TESTING #
    # @ ROMI CHASIS BOTTOM HEIGHT....
    # MAX = 2000 MIN = 250

    
    def __init__(self, CTRL, S0, S1, S2, S3, S4):
        '''Initializes a line_sensor object'''
        self.CTRL = Pin(CTRL, mode=Pin.OUT_PP, value=0)
        self.ADC0 = ADC(Pin(S0))
        self.ADC1 = ADC(Pin(S1))
        self.ADC2 = ADC(Pin(S2))
        self.ADC3 = ADC(Pin(S3))
        self.ADC4 = ADC(Pin(S4))

        # Calibration values - defaults until calibrate() is called
        self.white = [1598, 634, 343, 348, 1010]   # your measured values
        self.black = [3183, 2965, 2809, 2777, 2987]   # your measured values

        # self.tim = Timer(tim_num, freq=20000)                       
        # self.Dir = Pin(DIR, mode=Pin.OUT_PP, value=0)
        # self.nSLP_pin = Pin(nSLP, mode=Pin.OUT_PP, value=0)
        # self.tim_ch = self.tim.channel(tim_chan, pin=PWM, mode=Timer.PWM, pulse_width_percent=0)
           
    def enable(self):
        '''Enables the line sensor emitter lights'''
        self.CTRL.high()
            
    def disable(self):
        '''Disables the line sensor emitter lights. No need to use '''
        self.CTRL.low()

    def readRaw(self):
        return [self.ADC0.read(),
                self.ADC1.read(),
                self.ADC2.read(),
                self.ADC3.read(),
                self.ADC4.read()]
    
    def read_line(self):
        '''Reads location of line using weighted average of normalized sensors.
        
        Returns position 0-4000 where 2000 is center.
        Returns -1 if no line detected.
        '''
        raw = self.readRaw()
        norm = self.normalize(raw)  # 0.0 = white, 1.0 = black (line)

        # Weighted average - high norm value means line is there
        weights = [1000, 2000, 3000, 4000, 5000]
        num   = sum(norm[i] * weights[i] for i in range(5))
        denom = sum(norm)
        
        loc =  max(0, num / denom)  
        if loc == 0:
            return -1
        else:
            return loc
        
    def normalize(self, raw):
        '''Normalize raw readings relative to white/black calibration.
        0.0 = white, 1.0 = black, values outside range are allowed.'''
        normalized = []
        for i in range(5):
            span = self.black[i] - self.white[i]
            if span == 0:
                normalized.append(0.0)
            else:
                val = (raw[i] - self.white[i]) / span
                normalized.append(val)  # no clamping
        return normalized

    def calWhite(self):
        
        s0 = self.ADC0.read()
        s1 = self.ADC1.read()
        s2 = self.ADC2.read()
        s3 = self.ADC3.read()
        s4 = self.ADC4.read()

        self.white = [s0, s1, s2, s3, s4]
        return self.white

    def calBlack(self):
        
        s0 = self.ADC0.read()
        s1 = self.ADC1.read()
        s2 = self.ADC2.read()
        s3 = self.ADC3.read()
        s4 = self.ADC4.read()

        self.black = [s0, s1, s2, s3, s4]
        return self.black
