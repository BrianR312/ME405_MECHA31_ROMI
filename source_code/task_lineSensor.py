''' This file demonstrates an example motor task using a custom class with a
    run method implemented as a generator
'''
from line_sensor  import line_sensor
from task_share   import Share, Queue
from utime        import ticks_us, ticks_diff
import time
import micropython

S0_INIT = micropython.const(0) # State 0 - initialiation
S1_RUN = micropython.const(1) # State 1 - read line position

class task_lineSensor:
    '''
    A class that represents a motor task. The task is responsible for reading
    data from an encoder, performing closed loop control, and actuating a motor.
    Multiple objects of this class can be created to work with multiple motors
    and encoders.
    '''

    def __init__(self,
                 lin_sen: line_sensor,
                 lineLocation: Share,
                 followFlag):
        '''
        Initializes a motor task object
        
        Args:
            lin_sen (motor_driver): A line_sensor object
            lineLocation (Share)  : A float value representing the current location
                                    of the line. Center = 2000
        '''

        self._state: int        = S0_INIT    # The present state of the task 

        self._sens: line_sensor = lin_sen    # Our sensor object

        self._lineLoc: Share    = lineLocation

        self._prevLoc: float    = 0
        
        self._folllowFlag       = followFlag

    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:

            if self._folllowFlag:

                if self._state == S0_INIT: 
                    self._sens.enable()
                    self._lineLoc.put(3000)
                    self._state = S1_RUN
                    
                elif self._state == S1_RUN: # GET READINGS
                    if self._sens.read_line() == -1:
                        self._lineLoc.put(self._prevLoc)
                    else:
                        val = self._sens.read_line()
                        self._lineLoc.put(val)
                        self._prevLoc = val
                

            yield self._state