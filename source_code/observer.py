## Lab_06 Observer Class ##

from ulab import numpy as np


class observer:

    def __init__(self):

        # # Data from Shares
        # self.VL = 0                 # Voltages (from where?)
        # self.VR = 0
        # self.sL = 0                 # Wheel displacement (encoders)
        # self.sR = 0 
        # self.psi = 0                # Heading (IMU)
        # self.psi_dot = 0

        # State estimate vector
        self.x_hat = np.zeros((4,1))                    # [0; 0; 0; 0]

        # Hardcode MATLAB matrices

        self.A = np.array([
            [0.4170,	0.0000,	0.2278,	0.2278],
            [0.0000,	0.0017,	0.00000,	0.0000],
            [-0.2473,	0.0000,	0.4052, 0.4022],
            [-0.2473,	0.0000,	0.4022,	0.4052]
        ])

        self.B = np.array([
            [0.0039,	0.0039,	0.2915,	0.2915,	-0.0000,	-0.0000],
            [0.0000,	0.0000,	-0.0071,	0.0071,	0.0001,	0.0031],
            [0.0158,	0.0108,	0.1236,	0.1236,	-0.0000,	-1.9595],
            [0.0108,	0.0158,	0.1236,	0.1236,	-0.0000,	1.9595]
        ])

        self.C = np.array([
            [1.0000,	-70.0000,	0,	0],
            [1.0000,	70.0000,	0,	0],
            [0,	1.0000,	0,	0],
            [0,	0,	-0.2500,	0.2500]
        ])

        self.D = np.array([
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0]
        ])


    def update(self, VL, VR, sL, sR, psi, psi_dot):

        # Input vector
        U = np.array([
            [VL],
            [VR],
            [sL],
            [sR],
            [psi],
            [psi_dot]
        ])

        # State update                      [ s, zeta, omega_L, omega_R]
        self.x_hat = (
            np.dot(self.A, self.x_hat) +
            np.dot(self.B, U)
        )

        # Predicted outputs                 [s_L, s_R, zeta, zeta_dot]
        y_hat = (
            np.dot(self.C, self.x_hat) +
            np.dot(self.D, U)
        )

        return self.x_hat, y_hat