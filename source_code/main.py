from motor_driver import motor_driver
from IMU          import IMU
from line_sensor  import line_sensor
from pyb          import Pin, Timer
from encoder      import encoder
from observer     import observer
from task_motor   import task_motor
from task_user    import task_user
from task_lineSensor import task_lineSensor
from task_observer import task_observer
from task_share   import Share, Queue, show_all
from cotask       import Task, task_list
from gc           import collect
from pyb          import I2C
from task_debouncer import task_crash
from task_switch  import task_switch
from switch       import Switch

# Build all driver objects first
leftMotor    = motor_driver(4, 1, Pin.cpu.B6, Pin.cpu.B2, Pin.cpu.B1)
rightMotor   = motor_driver(4, 2, Pin.cpu.B7, Pin.cpu.H1, Pin.cpu.H0)
leftEncoder  = encoder(2, Pin.cpu.A1, Pin.cpu.A0)
rightEncoder = encoder(3, Pin.cpu.B5, Pin.cpu.B4)
lineSensor   = line_sensor(Pin.cpu.B0, Pin.cpu.C0, Pin.cpu.C1, Pin.cpu.C2, Pin.cpu.C3, Pin.cpu.A4)
observer     = observer()
i2c          = I2C(1, I2C.CONTROLLER)
imu          = IMU(i2c)
crash_detect  = Queue("B", 10, name="Queue for crash detection events")
leftSwitch   = Switch(Pin.cpu.C8)
rightSwitch  = Switch(Pin.cpu.C9)

# Build shares and queues
leftMotorGo   = Share("B",     name="Left Mot. Go Flag")
rightMotorGo  = Share("B",     name="Right Mot. Go Flag")
dataValues    = Queue("f", 80, name="Data Collection Buffer")
timeValues    = Queue("L", 80, name="Time Buffer")
kpVal         = Share("f",     name="Proportional Gain Value")                  
wRef          = Share("f",     name="Reference Angular Velocity") 
lineLocation  = Share("f",     name="Line Location; center = 2000")
followFlag    = Share("B",     name="Flag for line following") 
radius        = Share("f",     name="radius for turn function") 
turnFlag      = Share("B",     name="flag for turning") 
turnPlaceFlag = Share("B",     name="flag for turning") 
straightFlag  = Share("B",     name="flag for turning") 
startAngle    = Share("f",     name="flag for turning") 

lineKP        = Share("f",     name="line follower KP val") 
lineKI        = Share("f",     name="line follower KI val") 




estimateFlag  = Share("B",     name="Flag for state estimation") 
stopFlag      = Share("B",     name="Flag to stop state estimation") 
VL            = Share("f",     name="right motor voltage") 
VR            = Share("f",     name="left motor voltage") 
sL            = Share("f",     name="left motor displacemet [mm]") 
sR            = Share("f",     name="right motor displacement [mm]") 
psi           = Share("f",     name="heading [rad] [+ in counterclockwise direction]") 
psi_dot       = Share("f",     name="heading change") 

sL_out            = Share("f",     name="left motor displacemet [mm]") 
sR_out            = Share("f",     name="right motor displacement [mm]") 
s_out             = Share("f",     name="ROMI displacement [mm]") 
psi_out           = Share("f",     name="heading [rad] [+ in counterclockwise direction]") 

trialFlag    = Share("B",     name="Flag for time trial") 




# Build task class objects
leftMotorTask  = task_motor(leftMotor,  leftEncoder, "L", 
                            leftMotorGo, dataValues, timeValues, kpVal, wRef, followFlag, lineLocation,
                            estimateFlag, stopFlag, VL, VR, sL, sR, psi, psi_dot, psi_out,
                            trialFlag, radius, turnFlag, turnPlaceFlag, startAngle, straightFlag, lineKP, lineKI)
rightMotorTask = task_motor(rightMotor, rightEncoder, "R",
                            rightMotorGo, dataValues, timeValues, kpVal, wRef, followFlag, lineLocation,
                            estimateFlag, stopFlag, VL, VR, sL, sR, psi, psi_dot, psi_out,
                            trialFlag, radius, turnFlag, turnPlaceFlag, startAngle, straightFlag, lineKP, lineKI)
userTask = task_user(leftMotorGo, rightMotorGo, dataValues, timeValues, kpVal, wRef, followFlag, estimateFlag, stopFlag, trialFlag, radius, turnFlag, crash_detect, turnPlaceFlag,
                     sL_out, sR_out, s_out, psi_out, startAngle, straightFlag, lineKP, lineKI)
lineSensorTask = task_lineSensor(lineSensor, lineLocation, followFlag)
observerTask = task_observer(observer, imu, estimateFlag, dataValues, timeValues, VL, VR, sL, sR, psi, psi_dot,
                             sL_out, sR_out, s_out, psi_out)
debounceTask = task_crash(crash_detect, [Pin.cpu.C8, Pin.cpu.C9])
switchTask   = task_switch(crash_detect, left_pin=8, right_pin=9)

# Add tasks to task list
task_list.append(Task(leftMotorTask.run, name="Left Mot. Task",
                      priority = 1, period = 15, profile=True))
task_list.append(Task(rightMotorTask.run, name="Right Mot. Task",
                      priority = 1, period = 15, profile=True))
task_list.append(Task(lineSensorTask.run, name="Line Sensor Task",
                      priority = 2, period = 30, profile=True))
task_list.append(Task(observerTask.run, name="Observer Task",
                      priority = 1, period = 40, profile=True))
task_list.append(Task(switchTask.run, name="Switch Task",
                      priority = 0, period = 100, profile=True))
task_list.append(Task(debounceTask.run, name="Debounce Task",
                      priority = 0, period = 80, profile=True))   
task_list.append(Task(userTask.run, name="User Int. Task",
                      priority = 0, period = 0, profile=False))

# Run the garbage collector preemptively
collect()

# Run the scheduler until the user quits the program with Ctrl-C
while True:
    try:
        task_list.pri_sched()
        
    except KeyboardInterrupt:
        print("Program Terminating")
        leftMotor.disable()
        rightMotor.disable()
        break

print("\n")
print(task_list)
print(show_all())