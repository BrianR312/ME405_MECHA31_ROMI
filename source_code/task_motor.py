''' This file demonstrates an example motor task using a custom class with a
    run method implemented as a generator
'''
from motor_driver import motor_driver
from encoder      import encoder
from task_share   import Share, Queue
from utime        import ticks_us, ticks_diff
from math import pi
import micropython

S0_INIT = micropython.const(0) # State 0 - initialiation
S1_WAIT = micropython.const(1) # State 1 - wait for go command
S2_RUN  = micropython.const(2) # State 2 - run closed loop control
S3_FLLW = micropython.const(3) # State 3 - follow flag
S4_ESTM = micropython.const(4) # State 4 - estimate flag

S5_TURN = micropython.const(5) # State 4 - estimate flag
S6_TURN_PLACE = micropython.const(6) # State 4 - estimate flag
S7_STRAIGHT = micropython.const(7) # State 4 - estimate flag




class task_motor:
    '''
    A class that represents a motor task. The task is responsible for reading
    data from an encoder, performing closed loop control, and actuating a motor.
    Multiple objects of this class can be created to work with multiple motors
    and encoders.
    '''

    def __init__(self,
                 mot: motor_driver, enc: encoder, side,
                 goFlag: Share, dataValues: Queue, timeValues: Queue, kpVal: Share, wRef: Share, 
                 followFlag: Share, lineLocation: Share,
                 estimateFlag, stopFlag, VL, VR, sL, sR, psi, psi_dot, psi_out,
                 trialFlag, radius, turnFlag, turnPlaceFlag, startAngle, straightFlag, lineKP, lineKI
                 ):
        '''
        Initializes a motor task object
        
        Args:
            mot (motor_driver): A motor driver object
            enc (encoder):      An encoder object
            goFlag (Share):     A share object representing a boolean flag to
                                start data collection       
            kpVal (Share):      A share object holding the proportional gain                    
                                value
            wRef (Share):       A share object holding the ideal angular                        
                                velocity which will be used as a setpoint
            dataValues (Queue): A queue object used to store collected encoder
                                position values
            timeValues (Queue): A queue object used to store the time stamps
                                associated with the collected encoder data
        '''

        self._state: int        = S0_INIT    # The present state of the task

        self._side: str        = side       
        
        self._mot: motor_driver = mot        # A motor object
        
        self._enc: encoder      = enc        # An encoder object
        
        self._goFlag: Share     = goFlag     # A share object representing a
                                             # flag to start data collection

        self._followFlag: Share   = followFlag   # Flag representing full closed loop control

        self._wRef: Share     = wRef       # Share object for setpoint value

        self._KP: int         = 500      # Share object for KP gain

        self._KI: int           = 1500       # KI gain (will be share in future)

        self._lineLocation: Share   = lineLocation # Share Object for Line sensor output
        
        self._dataValues: Queue = dataValues # A queue object used to store
                                             # collected encoder position
        
        self._timeValues: Queue = timeValues # A queue object used to store the
                                             # time stamps associated with the
                                             # collected encoder data
        
        self._startTime: int    = 0          # The start time (in microseconds)

        self._prevTime: int     = 0
                                             # for a batch of collected data4  
        self._errorTotal: int   = 0     

        self._lineErrorTotal: int = 0        # Line sensor Error 

        # self._lineKp:     int = 0.0000001
        self._lineKp:     Share = lineKP

        self._lineKI:     Share = lineKI

        self._offset:     int = 0

        self._posTotal        = 0
        self._prevPos         = 0
        self._curPos          = 0

        # Observer related shares
        self._estimateFlag      = estimateFlag
        self._stopFlag          = stopFlag
        self._VL                = VL
        self._VR                = VR
        self._sL                = sL
        self._sR                = sR
        self._psi               = psi
        self._psi_dot           = psi_dot
        self._psi_out           = psi_out

        self._trialFlag         = trialFlag
        self._radius            = radius
        self._turnFlag          = turnFlag
        self._turnPlaceFlag     = turnPlaceFlag
        self._startAngle        = startAngle
        self._straightFlag      = straightFlag

        self._tiltErrorTotal    = 0
        self._tiltOffset        = 0
        self._tiltKI            = 0
        self._tiltKP            = 0.002

        self._warmup = 0

        print("Motor Task object instantiated")
        
    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:
            
            if self._state == S0_INIT: # Init state (can be removed if unneeded)
                # print("Initializing motor task")
                self._state = S1_WAIT
                
            elif self._state == S1_WAIT: # Wait for "go command" state
                if self._goFlag.get():
                    # print("Starting motor loop")
                    
                    # Capture a start time in microseconds so that each sample
                    # can be timestamped with respect to this start time. The
                    # start time will be off by however long it takes to
                    # transition and run the next state, so the time values may
                    # need to be zeroed out again during data processing.
                    self._startTime = ticks_us()
                    self._errorTotal = 0
                    self._state = S2_RUN
                    self._mot.set_effort(0)
                    self._mot.enable()
                elif self._followFlag.get():
                    self._startTime = ticks_us()
                    self._errorTotal = 0
                    self._lineErrorTotal = 0
                    self._state = S3_FLLW
                    self._mot.set_effort(0)
                    self._mot.enable()  
                elif self._estimateFlag.get():
                    self._state = S4_ESTM
                    self._errorTotal = 0
                    self._mot.set_effort(0)
                    self._mot.enable() 
                elif self._turnFlag.get():
                    self._state = S5_TURN
                    self._errorTotal = 0
                    self._mot.set_effort(0)
                    self._mot.enable() 
                elif self._turnPlaceFlag.get():
                    self._state = S6_TURN_PLACE
                    self._errorTotal = 0
                    self._mot.set_effort(0)
                    self._mot.enable() 
                elif self._straightFlag.get():
                    self._state = S7_STRAIGHT
                    self._errorTotal = 0
                    self._tiltErrorTotal = 0
                    self._mot.set_effort(0)
                    self._mot.enable()

            elif self._state == S2_RUN: # Closed-loop control state
                # print(f"Running motor loop, cycle {self._dataValues.num_in()}")
                
                # Run the encoder update algorithm and then capture the present
                # position of the encoder. You will eventually need to capture
                # the motor speed instead of position here.
                self._enc.update()

                pos = self._enc.get_position()
                vel = self._enc.get_velocity()
                
                # Collect a timestamp to use for this sample, all time is in microseconds (us)
                t   = ticks_us()
                dt = ticks_diff(t, self._prevTime)
                self._prevTime = t
                
                # Actuate the motor using a control law. The one used here in
                # the example is a "bang bang" controller, and will work very
                # poorly in practice. Note that the set position is zero. You
                # will replace this with the output of your PID controller that
                # uses feedback from the velocity measurement.
                # self._mot.set_effort(100 if pos < 0 else -100)    

                setpoint = self._wRef.get() * (1420/60/(10**(6)))                  # setpoint = [ticks/us]              
                error = setpoint - vel                                             # vel is units of ticks/microsecond
                self._errorTotal = error + self._errorTotal                     
                
                self._mot.set_effort(self._KP*error + self._KI*self._errorTotal)     
                
                # Store the sampled values in the queues
                self._dataValues.put(vel*60*10**(6)/1420)                                  # units of encoder ticks/second
                self._timeValues.put(ticks_diff(t, self._startTime))
                
                # When the queues are full, data collection is over
                if self._dataValues.full():
                    # print("Exiting motor loop")
                    self._state = S1_WAIT
                    self._mot.disable()
                    self._goFlag.put(False)
            
            elif self._state == S3_FLLW:

                self._enc.update()

                self._posTotal = self._enc.get_position()*219.9/1440     # [mm]
                vel = self._enc.get_velocity()
                
                # Collect a timestamp to use for this sample
                t   = ticks_us()
                dt = ticks_diff(t, self._prevTime)
                self._prevTime = t

                tilt = self._lineLocation.get()                                       
                lineError = max(-6000, min(6000, (3000 - tilt)))                                              # Positive error means turn left

                self._lineErrorTotal = lineError + self._lineErrorTotal
                self._offset = (self._lineErrorTotal * self._lineKI.get() + lineError * self._lineKp.get())

                if self._side == "L":
                    setpoint = self._wRef.get() * (1420/60/(10**(6))) - self._offset         # setpoint = [ticks/us]   
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal

                    # print(lineError)

                    effort = self._KP*error + 1500*self._errorTotal
                
                    self._mot.set_effort(effort) 

                    self._VL.put(effort/100*4.5)
                    self._sL.put(self._posTotal)
   

                elif self._side == "R":
                    setpoint = self._wRef.get() * (1420/60/(10**(6))) + self._offset         # setpoint = [ticks/us]    
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal

                    effort = self._KP*error + 1500*self._errorTotal

                    self._VR.put(effort/100*4.5)
                    self._sR.put(self._posTotal)
                
                    self._mot.set_effort(effort)

                if self._stopFlag.get():
                    self._mot.set_effort(0)
                    self._state = S1_WAIT
                
         
            elif self._state == S4_ESTM:            # actually the straight state
                self._enc.update()
                self._posTotal = self._enc.get_position()*219.9/1440     # [mm]



                vel = self._enc.get_velocity()
                

                setpoint = self._wRef.get() * (1420/60/(10**(6)))                  # setpoint = [ticks/us]              
                error = setpoint - vel                                             # vel is units of ticks/microsecond
                self._errorTotal = error + self._errorTotal                
                effort = self._KP*error + self._KI*self._errorTotal     
                
                self._mot.set_effort(effort)
                if self._side == "L":
                    self._VL.put(effort/100*4.5)
                    self._sL.put(self._posTotal)
                    # self._mot.set_effort(effort)            # CIRCLE TEST

                elif self._side == "R":
                    self._VR.put(effort/100*4.5)
                    self._sR.put(self._posTotal)
                    # self._mot.set_effort(0)                 # CIRCLE TEST


                if self._stopFlag.get():
                    self._mot.set_effort(0)
                    self._state = S1_WAIT 

            elif self._state == S5_TURN:
                w       = 141  # wheelbase [mm]
                r_wheel = 35  # wheel radius [mm]

                self._enc.update()
                self._posTotal = self._enc.get_position()*219.9/1440     # [mm]
                vel = self._enc.get_velocity()
                
                if self._radius.get() < 0:
                    radius = -self._radius.get()

                    speed = self._wRef.get() * (2*pi*r_wheel) / 60              # [mm/s]
                    omega_robot = speed / radius                    # [rad/s]

                    #print(speed)

                    # CONTROL THEORY

                    if self._side == "L":
                        omega_L = (speed - (w/2) * omega_robot) / r_wheel * 60/2/pi    # rpm
                        setpoint = omega_L * (1420/60/(10**(6)))                       # setpoint = [ticks/us]       
                        error = setpoint - vel        
                        self._errorTotal = error + self._errorTotal                
                        effort = self._KP*error + self._KI*self._errorTotal  

                        self._VL.put(effort/100*4.5)
                        self._sL.put(self._posTotal)
                        self._mot.set_effort(effort)

                    elif self._side == "R":
                        omega_R = (speed + (w/2) * omega_robot) / r_wheel * 60/2/pi    # rpm
                        setpoint = omega_R * (1420/60/(10**(6)))                       # setpoint = [ticks/us] 
                        error = setpoint - vel              
                        self._errorTotal = error + self._errorTotal                
                        effort = self._KP*error + self._KI*self._errorTotal  

                        self._VR.put(effort/100*4.5)
                        self._sR.put(self._posTotal)
                        self._mot.set_effort(effort)

                else:

                    speed = self._wRef.get() * (2*pi*r_wheel) / 60              # [mm/s]
                    omega_robot = speed / self._radius.get()                    # [rad/s]

                    #print(speed)

                    # CONTROL THEORY

                    if self._side == "L":
                        omega_L = (speed + (w/2) * omega_robot) / r_wheel * 60/2/pi    # rpm
                        setpoint = omega_L * (1420/60/(10**(6)))                       # setpoint = [ticks/us]       
                        error = setpoint - vel        
                        self._errorTotal = error + self._errorTotal                
                        effort = self._KP*error + self._KI*self._errorTotal  

                        self._VL.put(effort/100*4.5)
                        self._sL.put(self._posTotal)
                        self._mot.set_effort(effort)

                    elif self._side == "R":
                        omega_R = (speed - (w/2) * omega_robot) / r_wheel * 60/2/pi    # rpm
                        setpoint = omega_R * (1420/60/(10**(6)))                       # setpoint = [ticks/us] 
                        error = setpoint - vel              
                        self._errorTotal = error + self._errorTotal                
                        effort = self._KP*error + self._KI*self._errorTotal  

                        self._VR.put(effort/100*4.5)
                        self._sR.put(self._posTotal)
                        self._mot.set_effort(effort)

                if self._stopFlag.get():
                    self._mot.set_effort(0)
                    self._state = S1_WAIT 

            elif self._state == S6_TURN_PLACE:
                self._enc.update()
                self._posTotal = self._enc.get_position()*219.9/1440     # [mm]



                vel = self._enc.get_velocity()
                
                # Collect a timestamp to use for this sample, all time is in microseconds (us)
                t   = ticks_us()
                dt = ticks_diff(t, self._prevTime)
                self._prevTime = t
                
                # Actuate the motor using a control law. The one used here in
                # the example is a "bang bang" controller, and will work very
                # poorly in practice. Note that the set position is zero. You
                # will replace this with the output of your PID controller that
                # uses feedback from the velocity measurement.
                # self._mot.set_effort(100 if pos < 0 else -100)    

                if self._side == "L":
                    setpoint = self._wRef.get() * (1420/60/(10**(6)))                  # setpoint = [ticks/us]              
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal                
                    effort = self._KP*error + self._KI*self._errorTotal     
                                        
                    self._VL.put(effort/100*4.5)
                    self._sL.put(self._posTotal)
                    self._mot.set_effort(effort)            

                elif self._side == "R":
                    setpoint = -self._wRef.get() * (1420/60/(10**(6)))                  # setpoint = [ticks/us]              
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal                
                    effort = self._KP*error + self._KI*self._errorTotal 

                    self._VR.put(effort/100*4.5)
                    self._sR.put(self._posTotal)
                    self._mot.set_effort(effort)                 


                if self._stopFlag.get():
                    self._mot.set_effort(0)
                    self._state = S1_WAIT 

            elif self._state == S7_STRAIGHT:

                self._enc.update()

                self._posTotal = self._enc.get_position()*219.9/1440     # [mm]
                vel = self._enc.get_velocity()
                

                tilt = self._psi_out.get()                                       
                tiltError = self._startAngle.get() - tilt                                              # Positive error means turn left

                self._tiltErrorTotal = tiltError + self._lineErrorTotal
                self._tiltOffset = (self._tiltErrorTotal * self._tiltKI + tiltError * self._tiltKP)

                if self._side == "L":
                    setpoint = self._wRef.get() * (1420/60/(10**(6))) - self._tiltOffset         # setpoint = [ticks/us]   
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal

                    # print(tilt, tiltError)

                    effort = self._KP*error + 1500*self._errorTotal
                
                    self._mot.set_effort(effort) 

                    self._VL.put(effort/100*4.5)
                    self._sL.put(self._posTotal)
   

                elif self._side == "R":
                    setpoint = self._wRef.get() * (1420/60/(10**(6))) + self._tiltOffset         # setpoint = [ticks/us]   
                    error = setpoint - vel                                             # vel is units of ticks/microsecond
                    self._errorTotal = error + self._errorTotal

                    effort = self._KP*error + 1500*self._errorTotal

                    self._VR.put(effort/100*4.5)
                    self._sR.put(self._posTotal)
                
                    self._mot.set_effort(effort)

                if self._stopFlag.get():
                    self._mot.set_effort(0)
                    self._state = S1_WAIT

            yield self._state

            