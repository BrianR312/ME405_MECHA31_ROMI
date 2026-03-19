## Task Switch ##

from switch import Switch
from task_share import Queue


class task_switch:

    def __init__(self, crash_detect, left_pin, right_pin):
        self._crash_detect = crash_detect
        self._left_pin  = left_pin
        self._right_pin = right_pin

    def run(self):
        while True:
            if self._crash_detect.any():
                pin = self._crash_detect.get()
                if pin == self._left_pin:
                    print("Left bumper hit")
                elif pin == self._right_pin:
                    print("Right bumper hit")
            yield