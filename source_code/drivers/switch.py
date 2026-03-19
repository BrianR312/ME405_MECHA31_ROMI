## Switch Class ##

from pyb import Pin


class Switch:
    
    def __init__(self, pin):
        '''
        pin          - Pin object (same one passed to task_crash)
        crash_detect - Shared Queue from task_crash that receives ISR events
        '''
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._pressed = False
    
    
    def is_pressed(self):
        '''Returns True if a debounced press event occurred this update'''
        return self._pressed
    
    def set_pressed(self, state):
        self._pressed = state
    