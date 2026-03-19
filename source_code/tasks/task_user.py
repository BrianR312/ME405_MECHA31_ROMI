''' This file demonstrates an example UI task using a custom class with a
    run method implemented as a generator
'''
from pyb import USB_VCP
from task_share import Share, Queue
import micropython
from math import pi
from time import ticks_diff, ticks_us
from pyb import ExtInt, Pin

S0_INIT = micropython.const(0) # State 0 - initialiation
S1_CMD  = micropython.const(1) # State 1 - wait for character input
S2_COL  = micropython.const(2) # State 2 - wait for data collection to end
S3_DIS  = micropython.const(3) # State 3 - display the collected data
S4_MULT = micropython.const(4) # State 4 - take number input
S5_WAIT = micropython.const(5) # State 5 - idle
S6_TRIAL_START = micropython.const(6) # State 5 - idle
S7_TRIAL_TURN = micropython.const(7) # State 5 - idle
S8_GARAGE = micropython.const(8) # State 8 - Parking Garage plus bump
S9_GARAGE_REVERSE = micropython.const(9)
S10_GARAGE_TURN = micropython.const(10)
S11_GARAGE_EXIT = micropython.const(11)
S12_SLALOM_PREP = micropython.const(12)
S13_SLALOM = micropython.const(13)
S14_PRE_REVERSE = micropython.const(14)
S15_SHORT_STRAIGHT = micropython.const(15)
S16_V_APPROACH = micropython.const(16)
S17_REVERSE = micropython.const(17)
S18_REV_STRAIGHT = micropython.const(18)


UI_prompt = ">: "

class task_user:
    '''
    A class that represents a UI task. The task is responsible for reading user
    input over a serial port, parsing the input for single-character commands,
    and then manipulating shared variables to communicate with other tasks based
    on the user commands.
    '''

    def __init__(self, leftMotorGo, rightMotorGo, dataValues, timeValues, kpVal, wRef, followFlag, estimateFlag, stopFlag, 
                 trialFlag, radius, turnFlag, crash_detect, turnPlaceFlag,
                 sL_out, sR_out, s_out, psi_out, startAngle, straightFlag, lineKP, lineKI
                 ):
        '''
        Initializes a UI task object

        To Do:
        1) Implement share for sending reference speed (currently set my motor task to 67% for step response testing)
        
        Args:
            leftMotorGo (Share):  A share object representing a boolean flag to
                                  start data collection on the left motor
            rightMotorGo (Share): A share object representing a boolean flag to
                                  start data collection on the right motor
            dataValues (Queue):   A queue object used to store collected encoder
                                  position values
            timeValues (Queue):   A queue object used to store the time stamps
                                  associated with the collected encoder data
            wRef (Share):         A share object representing the setpoint 
                                  angular velocity in RPM
            followFlag (Share):   A share object for the line following boolean

            estimateFlag (Share): A share object for the state estimation boolean
        '''
        
        self._state: int          = S0_INIT      # The present state
        self.kPress = False
        self.setPress = False
        self.digits = set(map(str, range(10)))
        self.char_buf = ""
        self.char_in = ""
        
        self._leftMotorGo: Share  = leftMotorGo  # The "go" flag to start data
                                                 # collection from the left
                                                 # motor and encoder pair
        
        self._rightMotorGo: Share = rightMotorGo # The "go" flag to start data
                                                 # collection from the right
                                                 # motor and encoder pair
        
        self._ser: stream         = USB_VCP()    # A serial port object used to
                                                 # read character entry and to
                                                 # print output
        
        self._dataValues: Queue   = dataValues   # A reusable buffer for data
                                                 # collection
        
        self._timeValues: Queue   = timeValues   # A reusable buffer for time
                                                 # stamping collected data

        self._Kp: Share           = kpVal

        self._wRef: Share         = wRef

        self._followFlag: Share    = followFlag
        
        self._estimateFlag: Share  = estimateFlag

        self._stopFlag             = stopFlag

        self._sL_out                   = sL_out

        self._sR_out                   = sR_out
        self._s_out                    = s_out
        self._psi_out                  = psi_out

        self._trialFlag                = trialFlag
        self._radius                   = radius
        self._turnFlag                 = turnFlag
        self._startPos                 = 0
        self._stopTime                 = 0
        self._crash_detect             = crash_detect
        self._turnPlaceFlag            = turnPlaceFlag
        self._startAngle               = startAngle
        self._straightFlag             = straightFlag
        self._newStart                 = 0

        self._lineKP                   = lineKP
        self._lineKI                   = lineKI
        
        # Button callback - same as pressing 'g'
        self._buttonPressed = False
        self._button = ExtInt(Pin.cpu.C13, ExtInt.IRQ_FALLING, Pin.PULL_NONE, 
                              lambda p: self._set_button())        
        self._ser.write("User Task object instantiated\r\n")
    
    def _set_button(self):
        self._buttonPressed = True

    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:
            
            if self._state == S0_INIT: # Init state (can be removed if unneeded)
                self._ser.write(
                    "+------------------------------------------------------------------------------+\r\n"
                    "| ME 405 Romi Tuning Interface Help Menu                                       |\r\n"
                    "+---+--------------------------------------------------------------------------+\r\n"
                    "| h | Print help menu                                                          |\r\n"
                    "| k | Enter new gain values                                                    |\r\n"
                    "| s | Choose a new setpoint                                                    |\r\n"
                    "| l | Trigger step response in left motor and print results                    |\r\n"
                    "| r | Trigger step response in right motor and print results                   |\r\n"
                    "| f | Begin line following process                                             |\r\n" 
                    "| e | Begin state estimation process                                           |\r\n"  
                    "| g | GO GO GO GO GO GO GO GO                                                  |\r\n"               
                    "| z | Straight line test                                                       |\r\n"                                                         
                    "+---+--------------------------------------------------------------------------+\r\n"
                    )
                self._state = S1_CMD

            elif self._state == S1_CMD: # Wait for UI commands
                if self._buttonPressed:
                    self._trialFlag.put(True)
                    self._ser.write("Time Trial begins...\r\n")
                    self._state = S6_TRIAL_START
                    self._startPos = self._psi_out.get()
                    self._lineKP.put(0.0000001)
                    self._lineKI.put(0.00000000001)
                    self._startAngle.put(self._startPos)
                    self._buttonPressed = False          # clear the flag!

                # Wait for at least one character in serial buffer
                elif self._ser.any():
                    # Read the character and decode it into a string
                    inChar = self._ser.read(1).decode()
                    # If the character is an upper or lower case "l", start data
                    # collection on the left motor and if it is an "r", start
                    # data collection on the right motor
                    if inChar in {"h", "H"}:
                        self._ser.write("No help for you :)\r\n")
                        self._state = S1_CMD
                    elif inChar in {"k", "K"}:
                        self._ser.write("Input new gain value...\r\n")
                        self.kPress = True
                        self._state = S4_MULT            
                    elif inChar in {"s", "S"}:
                        self._ser.write("Input new setpoint...\r\n")
                        self.setPress = True
                        self._state = S4_MULT           
                    elif inChar in {"l", "L"}:
                        self._ser.write(f"{inChar}\r\n")
                        self._leftMotorGo.put(True)
                        self._ser.write("--------------------\r\n")
                        self._ser.write(f"setpoint [rpm] = {self._wRef.get()}\r\n")
                        self._ser.write(f"gain = {self._Kp.get()}\r\n")
                        self._ser.write("--------------------\r\n")
                        self._ser.write("Starting left motor loop...\r\n")
                        self._ser.write("Starting data collection...\r\n")
                        self._ser.write("Please wait... \r\n")
                        self._state = S2_COL
                    elif inChar in {"r", "R"}:
                        self._ser.write(f"{inChar}\r\n")
                        self._rightMotorGo.put(True)
                        self._ser.write("Starting right motor loop...\r\n")
                        self._ser.write("Starting data collection...\r\n")
                        self._ser.write("Please wait... \r\n")
                        self._state = S2_COL
                    elif inChar in {"f", "F"}:
                        self._followFlag.put(True)
                        self._ser.write("Following line...\r\n")
                        self._ser.write("Click 'Ctrl C' to stop...\r\n")
                        self._lineKP.put(0.0000006)
                        self._lineKI.put(0.000000005)
                        self._state = S5_WAIT
                    elif inChar in {"e", "E"}:
                        self._estimateFlag.put(True)
                        self._ser.write("Estimating State...\r\n")
                        self._ser.write("Click 'Ctrl C' to stop...\r\n")
                        self._state = S5_WAIT
                    elif inChar in {"g", "G"}:
                        self._trialFlag.put(True)
                        self._ser.write("Time Trial begins...\r\n")
                        self._state = S6_TRIAL_START
                        self._startPos = self._psi_out.get()
                        self._lineKP.put(0.0000001)
                        self._startAngle.put(self._startPos)
                    elif inChar in {"z", "Z"}:
                        self._straightFlag.put(True)
                        self._ser.write("Time Trial begins...\r\n")
                        self._state = S5_WAIT
                        self._startPos = self._psi_out.get()
                        self._startAngle.put(self._startPos)
                
            elif self._state == S2_COL:
                # While the data is collecting (in the motor task) block out the
                # UI and discard any character entry so that commands don't
                # queue up in the serial buffer
                if self._ser.any(): self._ser.read(1)
                
                # When both go flags are clear, the data collection must have
                # ended and it is time to print the collected data.
                if not self._leftMotorGo.get() and not self._rightMotorGo.get():
                    self._ser.write("Data collection complete...\r\n")
                    self._ser.write("Printing data...\r\n")
                    self._ser.write("--------------------\r\n")
                    self._ser.write("Time, Velocity\r\n")
                    self._state = S3_DIS
            
            elif self._state == S3_DIS:
                # While data remains in the buffer, print that data in a command
                # separated format. Otherwise, the data collection is finished.
                if self._dataValues.any():
                    self._ser.write(f"{self._timeValues.get()},{self._dataValues.get()},\r\n")
                else:
                    self._ser.write("--------------------\r\n")
                    self._ser.write("Waiting for go command: 'l' for left, 'r' for right\r\n")
                    self._ser.write(UI_prompt)
                    self._state = S1_CMD
            
            elif self._state == S4_MULT:
                    if self._ser.any():
                        # Read the character and decode it into a string
                        self.char_in = self._ser.read(1).decode()
                        if self.char_in in self.digits:
                            self._ser.write(self.char_in)
                            self.char_buf += self.char_in

                    elif self.char_in == "." and "." not in self.char_buf:
                        self._ser.write(self.char_in)
                        self.char_buf += self.char_in

                    elif self.char_in == "-" and len(self.char_buf) == 0:
                        self._ser.write(self.char_in)
                        self.char_buf += self.char_in

                    elif self.char_in == "\x7f" and len(self.char_buf) > 0:           # ASCII for backspace
                        self._ser.write(self.char_in)
                        self.char_buf = self.char_buf[:-1]

                    elif self.char_in in {"\r", "\n"}:                           # terminator characters
                        if len(self.char_buf) == 0:
                            self._ser.write("\r\n")
                            self._ser.write("Value not changed\r\n")
                            self.char_buf = "" 
                            self.char_in = ""
                            self._state = S1_CMD  
                        elif self.char_buf not in {"-", "."}:
                            self._ser.write("\r\n")
                            value = float(self.char_buf)
                            self._ser.write(f"Value set to {value}\r\n")
                            if self.kPress:
                                self._Kp.put(value)
                                self.kPress = False
                            elif self.setPress:
                                self._wRef.put(value)
                                self.setPress = False
                            self._state = S1_CMD  
                            self.char_buf = ""
                            self.char_in = ""
            elif self._state == S5_WAIT:
                # straight line test
                if self._s_out.get() > 1075:
                    self._stopFlag.put(True)
                    self._estimateFlag.put(False)
                    self._straightFlag.put(False)
                    self._followFlag.put(False)

                # # circle test
                # if self._psi_out.get() < -6.28:
                #     self._stopFlag.put(True)
                #     self._estimateFlag.put(False)



## START OF THE COMPETITION TRIAL  ##



            elif self._state == S6_TRIAL_START:
                # Straight line start
                self._followFlag.put(True)
                if self._s_out.get() < 1275:
                    self._wRef.put(180)
                else:
                    self._wRef.put(40)
                #if not self._s_out.get() > 1375:
                    #print(self._s_out.get())


                if self._s_out.get() > 1375:
                    self._wRef.put(0)
                    self._stopFlag.put(True)
                    self._followFlag.put(False)
                    self._state = S7_TRIAL_TURN
                    self._stopTime = ticks_us()


            elif self._state == S7_TRIAL_TURN:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._turnFlag.put(True)
                    self._wRef.put(120)
                    #print(self._startPos)
                    if self._psi_out.get() > (self._startPos - pi/2):
                        self._radius.put(190)
                    elif self._psi_out.get() > (self._startPos - pi):           # underturn here
                        self._wRef.put(70)
                        self._radius.put(100)
                    if self._psi_out.get() < (self._startPos - pi-.1):             # underturn here
                        self._wRef.put(0)
                        self._stopFlag.put(True)
                        self._turnFlag.put(False)
                        self._stopTime = ticks_us()
                        self._state = S8_GARAGE                                     # CHANGE THIS
                        self._startAngle.put(self._startPos - pi-.05)

            elif self._state == S8_GARAGE:
                if ticks_diff(ticks_us(), self._stopTime) < 100000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(60)
                    self._straightFlag.put(True)
                    if self._crash_detect.any():
                        self._wRef.put(0)
                        self._stopFlag.put(True)
                        self._straightFlag.put(False)
                        self._state = S9_GARAGE_REVERSE
                        self._newStart = self._s_out.get()
                        self._stopTime = ticks_us()


            elif self._state == S9_GARAGE_REVERSE:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(-60)
                    self._straightFlag.put(True)
                    # print(self._s_out.get() - self._newStart)
                    if self._s_out.get() - self._newStart < -10:
                        self._stopFlag.put(True)
                        self._straightFlag.put(False)
                        self._stopTime = ticks_us()
                        self._state = S10_GARAGE_TURN

            elif self._state == S10_GARAGE_TURN:
                # print(self._psi_out.get(), self._startPos - pi/2)
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(-40)
                    self._turnPlaceFlag.put(True)
                    if self._psi_out.get() > (self._startPos - pi/2 - .3):
                        self._stopFlag.put(True)
                        self._turnPlaceFlag.put(False)
                        self._state = S11_GARAGE_EXIT
                        self._stopTime = ticks_us()
                        self._newStart = self._s_out.get()
                        self._startAngle.put(self._startPos - pi/2-.05)


            elif self._state == S11_GARAGE_EXIT:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(50)
                    self._straightFlag.put(True)
                    if self._s_out.get() - self._newStart > 365:
                        self._stopFlag.put(True)
                        self._straightFlag.put(False)
                        self._stopTime = ticks_us()
                        self._state = S12_SLALOM_PREP

            elif self._state == S12_SLALOM_PREP:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(40)
                    self._turnPlaceFlag.put(True)
                    if self._psi_out.get() < (self._startPos - pi + 0.05):
                        self._stopFlag.put(True)
                        self._turnPlaceFlag.put(False)
                        self._lineKP.put(0.0000002)
                        self._lineKI.put(0.000000005)
                        self._newStart = self._s_out.get()
                        self._stopTime = ticks_us()
                        self._state = S13_SLALOM

            elif self._state == S13_SLALOM:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(28)
                    self._followFlag.put(True)
                    if self._psi_out.get() < (self._startPos - pi) and self._s_out.get() - self._newStart > 1075:
                        self._stopFlag.put(True)
                        self._followFlag.put(False)
                        self._stopTime = ticks_us()
                        self._state = S14_PRE_REVERSE

            elif self._state == S14_PRE_REVERSE:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(140)
                    self._radius.put(190)
                    self._turnFlag.put(True)
                    if self._psi_out.get() < (self._startPos - 2*pi):
                        self._stopFlag.put(True)
                        self._turnFlag.put(False)
                        self._wRef.put(0)
                        self._newStart = self._s_out.get()
                        self._stopTime = ticks_us()
                        self._state = S15_SHORT_STRAIGHT
                        fwd = True
                        self._startAngle.put(self._startPos-2*pi-0.05)
                        

            elif self._state == S15_SHORT_STRAIGHT:
                if ticks_diff(ticks_us(), self._stopTime) < 50000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    if fwd:
                        self._stopFlag.put(False)
                        self._wRef.put(50)
                        self._straightFlag.put(True)
                        if self._s_out.get() - self._newStart > 150:
                            self._wRef.put(-50)
                            self._newStart = self._s_out.get()
                            fwd = False
                    else:
                        if self._s_out.get() - self._newStart < -90:
                            self._stopFlag.put(True)
                            self._straightFlag.put(False)
                            self._stopTime = ticks_us()
                            self._state = S17_REVERSE

            # elif self._state == S16_V_APPROACH:
            #     if ticks_diff(ticks_us(), self._stopTime) < 100_000:
            #         pass  # wait 100ms for motors to reach S1_WAIT
            #     else:
            #         self._stopFlag.put(False)
            #         self._wRef.put(40)
            #         self._radius.put(200)
            #         self._turnFlag.put(True)
            #         if self._psi_out.get() < (self._startPos - 2*pi):
            #             self._stopFlag.put(True)
            #             self._turnFlag.put(False)
            #             self._newStart = self._s_out.get()
            #             self._stopTime = ticks_us()
            #             self._state = S17_REVERSE

            elif self._state == S17_REVERSE:
                if ticks_diff(ticks_us(), self._stopTime) < 100_000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(-100)                         # BRIAN SEE THIS!! I think it might work backwards with
                    self._radius.put(-170)                      #  a combo of negative setpoint and gain
                    self._turnFlag.put(True)
                    if self._psi_out.get() < (self._startPos - 2.5*pi):
                        self._stopFlag.put(True)
                        self._turnFlag.put(False)
                        self._newStart = self._s_out.get()
                        self._stopTime = ticks_us()
                        self._state = S18_REV_STRAIGHT
                        self._startAngle.put(self._startPos-2.5*pi)


            elif self._state == S18_REV_STRAIGHT:
                if ticks_diff(ticks_us(), self._stopTime) < 100_000:
                    pass  # wait 100ms for motors to reach S1_WAIT
                else:
                    self._stopFlag.put(False)
                    self._wRef.put(-50)
                    self._straightFlag.put(True)
                    if self._s_out.get() - self._newStart < -110:
                        self._stopFlag.put(True)
                        self._straightFlag.put(False)
                        self._stopTime = ticks_us()
                        self._state = S5_WAIT

            yield self._state