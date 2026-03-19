
from observer     import observer
from IMU          import IMU
from task_share   import Share, Queue
from utime        import ticks_us, ticks_diff
import micropython

S0_INIT = micropython.const(0) # State 0 - initialiation
S1_WAIT = micropython.const(1) # State 1 - wait for go command
S2_RUN  = micropython.const(2) # State 2 - run closed loop control
S3_FLLW = micropython.const(3) # State 3 - follow flag

class task_observer:
    '''
    A class that represents an observer task.
    '''

    def __init__(self,
                 obs: observer, IMU,
                 estimateFlag: Share, dataValues: Queue, timeValues: Queue, VL, VR, sL, sR, psi, psi_dot,
                 sL_out, sR_out, s_out, psi_out):
        '''
        Initializes an observer task object
        
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

        self._estimateFlag      = estimateFlag      # Share representing a flag that says when to run state estimator

        self._obs               = obs               # Observer object

        self._IMU               = IMU               # IMU object

        # Share objects

        self._VL                = VL
        self._VR                = VR
        self._sL                = sL
        self._sR                = sR
        self._psi               = psi
        self._psi_dot           = psi_dot

        self._sL_out            = sL_out
        self._sR_out            = sR_out
        self._s_out             = s_out
        self._psi_out           = psi_out

        print("Observer Task object instantiated")
        
    def run(self):
        '''
        Runs one iteration of the task
        '''
        
        while True:
            
            if self._state == S0_INIT: # Init state (can be removed if unneeded)
                # state variables, x: [s, psi, omega_L, omega_R]
                # output variables, y: [s_L, s_R, psi, psi_dot]
                self._IMU.configure()
                self._state = S1_WAIT
                
            elif self._state == S1_WAIT: 
                self._psi = self._IMU.eulRead()
                self._psi_dot = self._IMU.rateRead()
                x_hat, y_hat = self._obs.update(self._VL.get(), self._VR.get(), self._sL.get(), self._sR.get(), self._psi[0], self._psi_dot[0])
                self._sL_out.put(y_hat[0,0])
                self._sR_out.put(y_hat[1,0])
                self._s_out.put(x_hat[0,0])
                self._psi_out.put(y_hat[2,0])
                # print(self._psi[0], self._psi_dot[0], x_hat[0,0], y_hat[2,0])
                # print(self._IMU.calRead())


                # print(y_hat[0,0], y_hat[1,0])                    

            yield self._state

            