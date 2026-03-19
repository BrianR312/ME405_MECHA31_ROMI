## Lab_02 Encoder Class ##


from pyb import Pin, Timer
from time import ticks_us, ticks_diff   # Use to get dt value in update()

class encoder:
    '''A quadrature encoder decoding interface encapsulated in a Python class'''

    def __init__(self, tim_num, chA_pin, chB_pin):
        '''Initializes an Encoder object'''
        self.tim = Timer(tim_num, prescaler=0, period=0xFFFF)
        self.chA = self.tim.channel(1, pin=chA_pin, mode=Timer.ENC_AB)
        self.chB = self.tim.channel(2, pin=chB_pin, mode=Timer.ENC_AB)
    
        self.position   = 0     # Total accumulated position of the encoder
        self.prev_count = 0     # Counter value from the most recent update
        self.delta      = 0     # Change in count between last two updates
        self.dt         = 0     # Amount of time between last two updates
        self.prev_time  = 0     # Time of the most recent update
        self.cur_count  = 0
    
    def update(self):
        '''Runs one update step on the encoder's timer counter to keep
           track of the change in count and check for counter reload'''
        self.cur_count = self.tim.counter()
        self.delta = self.cur_count - self.prev_count
        self.prev_count = self.cur_count
        if self.delta < -32768:             # Overflow
            self.delta += 65536
        elif self.delta > 32768:            # Underflow
            self.delta -= 65536
        self.position += self.delta
        self.dt = ticks_diff(ticks_us(), self.prev_time)
        self.prev_time = ticks_us()
        pass
            
    def get_position(self):
        '''Returns the most recently updated value of position as determined
           within the update() method'''
        return self.position
            
    def get_velocity(self):
        '''Returns a measure of velocity using the the most recently updated
           value of delta as determined within the update() method'''
        if self.dt == 0:
            return 0
        return self.delta/self.dt
    
    def zero(self):
        '''Sets the present encoder position to zero and causes future updates
           to measure with respect to the new zero position'''
        self.position   = 0     # Total accumulated position of the encoder
        self.prev_count = 0     # Counter value from the most recent update
        self.delta      = 0     # Change in count between last two updates
        self.dt         = 0     # Amount of time between last two updates
        self.prev_time  = 0     # Time of the most recent update
        pass