# ME405_MECHA31_ROMI

## Overview and Competition Description

This project implements an autonomous robot, named ROMI, optimized to complete a competition racetrack in as little time as possible. For navigation, our ROMI was equipped with a line follower to track its position relative to a fixed line on the racetrack, a state observer to estimate its position and orientation, and a set of bump sensors for tactile feedback when making contact with obstacles. The software and hardware implementation of these features will be discussed within the following sections. 

The rules of the competition were kept relatively simple with the provided racetrack being split into 4 checkpoints and a finish position. These can be seen in the figure below. The first portion of the track was a straight line that required line-following up until checkpoint #1. Between checkpoint #1 and #2 was the "garage" section with a steel enclosure simulating a parking garage environment. There was no black line to follow for this section meaning all navigation had to be done without the line following feature. The only requirement for this section was that an element of sensing - either tactile with a bump sensor or with IR/ultrasonic proximity sensors - was used to detect the wall before responding. This meant that teams could not rely on their state observer for all of section 2. The section between checkpoints #2 and #3 was referred to as the "slalom" section and required line following to pass through obstacles. The next segment of the track was a simple turn into checkpoint #4, followed by a turn into the finish position. To count a checkpoint as "complete", ROMI had to completeley cover the checkpoint dot with its chassis. 

![Figure 1. Competition racetrack and checkpoints](images/ME405_Racetrack.png)

---

## Demo Video and Competition Results

The following videos document our three trial runs. For the competition, each team was allowed three attempts to finish. Completing the course three times demonstrated consistency and resulted in higher scoring. The best time of the three attempts was used for the final score. 

We are proud to say that our ROMI was not only one of the most consistent performers, but also the fastest in the entire competition. Whereas most teams took between 40 to 100 seconds to complete the course, our robot finished in 26.3 seconds. All three trials can be found on youtube and are linked below.

### Trial 1 (26.9 seconds)
<p align="center">
  <a href="https://youtu.be/BLMAuTk7GWE">
    <img src="https://img.youtube.com/vi/BLMAuTk7GWE/0.jpg" width="400">
  </a>
</p>

### Trial 2 (26.3 seconds)
<p align="center">
  <a href="https://youtu.be/7kmqAkYPIVk">
    <img src="https://img.youtube.com/vi/7kmqAkYPIVk/0.jpg" width="400">
  </a>
</p>

### Trial 3 (26.6 seconds)
<p align="center">
  <a href="https://youtu.be/af3TSzDRKpg">
    <img src="https://img.youtube.com/vi/af3TSzDRKpg/0.jpg" width="400">
  </a>
</p>

## Hardware Design

This section will discuss our choice of components, mounting system, and wiring. No custom hardware was manufactured for this project.

### Components

Shoe of Brian and NUCLEO board

    The Shoe of Brian is a custom IO shield that was designed by Professor Ridgeley and attaches to our STM32 NUCLEO board. This board comes equipped with an STM32 microcontroller. 

QTR-MD-05A Reflectance Sensor Array

    For our line follower, a Polulu analog 5 sensor array was used. This sensor package uses IR LED/phototransistor pairs to illuminate the ground and detect reflectance. Originally, we used a QTR-HD-05A sensor array where the HD stands for high density. With only 5 sensors, we quickly found the high density package to be too narrow in focus for the track's line width. By changing to a medium density (MD) sensor with the same number of IR emitters, we were able to keep the same wiring and pin configurations while expanding our maximum sensable width by over 75%. This came at the expense of some fidelity between sensors, but this had a negligible effect on our line following.

TI DRV8838 Motor Drivers and Encoders

    Our ROMI chassis came equipped with two TI DRV8838 motor drivers. At no-load conditions, these motor drivers had a speed of 150 RPM at a nominal voltage of 4.5V. They also had a gear ratio of 120:1.

    For reading displacement, these motor drivers also came with magnetic quadrature encoders that could read 12 counts per revolution. This resolution is extremely low, but with the gear ratio the true resolution is 1440 counts per revolution. For our use case, this resolution is adequate. 

Polulu Bump Sensor

BNO055 IMU





* Reflectance sensor array (QTR)

### Mechanical Design and Mounting

All components were mounted using the provided M2 screws and matching hex nuts. For our IMU, two standoffs were used to ensure the IMU was parallel to the ground. We used another two standoffs for our refelctance line sensor. This enabled it to get closer to the ground for more precise readings. All standoffs were mounted using M2 screws.

### Wiring Diagram

<img width="708" height="821" alt="WiringDiagram" src="https://github.com/user-attachments/assets/cd71af1f-a435-4da4-8e7c-d9a3cbc8e63c" />


---

## 💻 Software Design

The software is modular and organized into the following components:

Drivers: Classes that include the methods for each object that will be used in higher levels
    - Ex: 'encoder.py', 'motor_driver.py', 'observer.py'
Task Files: Classes that represent each task that needs to run
    - Ex: 'task_motor.py', 'task_observer.py'
Libraries: Files given to us by the instructor that set up inter-file communication and the scheduler
    - Ex: 'task_share.py', 'cotask.py'
Main: The main file that initializes all the objects, shares, queues, and tasks
    - Ex: 'main.py'

The system operates using a structured control loop that continuously:


I AM ADDING THIS WE NEED TO DELETE IT


1. Reads sensor input
2. Computes error
3. Updates control output
4. Commands motors

---

## 🧮 Control System

A feedback controller was implemented to minimize the error between the robot’s position and the line.

* **Error Definition:** Difference between desired line position and measured position
* **Control Method:** (e.g., PID / proportional / other)

Control equation:

```
u(t) = Kp * e(t) + Ki * ∫e(t)dt + Kd * de(t)/dt
```

Controller gains were tuned experimentally to achieve stable and responsive performance.

---

## 📊 Results

The robot successfully followed the line under normal operating conditions.

**Performance observations:**

* Stable tracking with minimal oscillation
* Responsive to changes in line curvature
* Maximum speed: (add value)

(Optional: include plots if available)
![Performance Plot](docs/results.png)

---

## ⚠️ Challenges

Some challenges encountered during development included:

* Sensor noise and inconsistent readings
* Tuning control gains for stability
* Mechanical alignment of sensors

These issues were addressed through filtering, iterative tuning, and hardware adjustments.

---

## 🔁 Future Improvements

* Implement more advanced control (e.g., adaptive or state-based control)
* Improve sensor calibration
* Increase speed while maintaining stability
* Enhance mechanical robustness

---

## 📂 Repository Structure

```
.
├── src/        # Python source code
├── hardware/   # Wiring diagrams and CAD files
├── images/     # Photos of the robot
├── docs/       # Diagrams and additional documentation
├── main.py     # Main execution file
└── README.md   # Project documentation
```

---

## 📸 Project Photos

![Robot](images/robot.jpg)
![Setup](images/setup.jpg)

---

## 👥 Contributors

* Your Name
* Teammate Name

---

## 📎 Additional Notes

This project demonstrates the integration of sensing, control systems, and embedded programming to achieve autonomous behavior in a robotic platform.
