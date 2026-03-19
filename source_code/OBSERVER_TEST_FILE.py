## TEST FILE TO VERIFY OBSERVER CLASS BEHAVIOR ##

## Test file for RomiObserver ##

from observer import Observer
from ulab import numpy as np
import time


def main():

    obs = Observer()

    print("Starting observer test...\n")
    time.sleep(2)

    # Simulated inputs
    VL = 2.0          # left motor voltage
    VR = 2.0          # right motor voltage

    sL = 0.0          # encoder displacement
    sR = 0.0

    psi = 0.0         # yaw
    psi_dot = 0.0     # yaw rate

    for i in range(20):

        # simulate forward motion
        sL += 5
        sR += 5

        # run observer
        x_hat, y_hat = obs.update(VL, VR, sL, sR, psi, psi_dot)

        print("Iteration:", i)
        print("State estimate x_hat:")
        print(x_hat)

        print("Predicted outputs y_hat:")
        print(y_hat)

        print("----------------------")

        time.sleep(0.2)


if __name__ == "__main__":
    main()