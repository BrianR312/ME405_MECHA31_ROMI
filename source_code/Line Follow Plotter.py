import serial
import time
import csv
import os
from datetime import datetime
from matplotlib import pyplot
import numpy as np

# =========================
# USER SETTINGS
# =========================

PORT = 'COM12'
BAUD = 115200

test_matrix = [

    {"sp": 10, "kp": 500.0},

]

# =========================
# SETUP
# =========================

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

os.makedirs("Collection_Log", exist_ok=True)

# =========================
# MAIN LOOP
# =========================

for test in test_matrix:

    reading_data = False
    sp = test["sp"]
    kp = test["kp"]

    print(f"Running: SP={sp}, Kp={kp}")

    # Send parameters
    ser.write(b'\x03')
    ser.write(b'\x04')
    ser.write("k\n".encode())
    ser.write(f"{kp}\n".encode())
    time.sleep(1)
    ser.write("s\n".encode())
    ser.write(f"{sp}\n".encode())
    time.sleep(1)
    ser.write("f\n".encode())
    time.sleep(10)

    data = []

    while True:
        line = ser.readline().decode()
        if not line:
            continue

        # Start reading numeric data after header
        if "Time" in line and "Velocity" in line:
            reading_data = True
            continue

        # Stop reading when MCU prints prompt
        if line.startswith("Waiting for go command") or line.startswith(">") and reading_data:
            break

        if reading_data:
            try:
                t_str, v_str, *_ = line.split(',')  # handle trailing comma
                t = float(t_str)/(10**6)
                v = float(v_str)
                data.append([t, v])
            except ValueError:
                continue

    # =========================
    # SAVE FILES
    # =========================

    timestamp = datetime.now().strftime("%m_%d_%H_%M_%S")
    base_name = f"{timestamp}_sp{sp}_kp{kp}"

    csv_path = f"Collection_Log/{base_name}.csv"
    png_path = f"Collection_Log/{base_name}.png"

    # Save CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["time", "velocity"])
        writer.writerows(data)

    # Convert to numpy
    t_vals = np.array([row[0] for row in data])
    v_vals = np.array([row[1] for row in data])

    # # =========================
    # # Caclulate time constant
    # # =========================

    # idx_tau = np.where(v_vals >= sp*.632)[0][0]
    # tau = t_vals[idx_tau]

    # print("Time constant τ =", tau, "seconds")

    # # =========================
    # # Caclulate steady-state error
    # # =========================

    # # take the average of the last 5 values to calc steady state
    # ss_error = sp - np.mean(v_vals[-5:])
    # print("Steady-State Error =", ss_error, "RPM")


    # =========================
    # Plot data
    # =========================

    lin_num = 0
    x = []                                  # list of x-values
    y = []                                  # list of y-values

    with open(csv_path, "r") as file:       # no need to manually close - with block auto closes after indented block is done running
        for line in file:
            lin_num +=1
            clean = line.split(",")
            if len(clean) < 2:              # checks for whitespace or non-readable numbers
                print("ERROR: NONREADABLE NUMBERS OR WHITESPACE, LINE: " + str(lin_num))
                continue
            test1 = clean[0].split("#")
            test2 = clean[1].split("#")
            if test1[0].strip() == "" or test2[0].strip() == "":        # checks for # BEFORE column
                print("ERROR: COMMENT (#) FOUND, LINE: " + str(lin_num))
                continue
            if lin_num == 1:                # get labels for axes
                x_label = test1[0].strip()
                y_label = test2[0].strip()
            else:                           # working with data
                x.append(float(test1[0].strip()))
                y.append(float(test2[0].strip()))


    pyplot.plot(x, y)
    pyplot.xlabel("Time, t [s]")
    pyplot.ylabel("Angular Velocity, ω [RPM]")
    pyplot.title(f"Setpoint={sp} RPM KP={kp}")
    # pyplot.axhline(0.632*sp, color='orange', linestyle='--', label="63.2% of SP")
    # pyplot.text(0.6, 3+0.632*sp, f"τ ≈ {tau:.3f} s, ss_error = {ss_error:.3f} RPM", color='red')
    pyplot.savefig(png_path)
    pyplot.close()

print("Test and plots are complete :)")
