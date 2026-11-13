# Wireless Micro:bit Robotic Car with Obstacle Detection

A wireless robotic car built using **two BBC micro:bits**, a **Keyestudio KS4036 MiniCar**, and **MicroPython**.

The project uses radio communication to control the car remotely. The handheld controller supports motion-based driving, button steering, and two speed modes. The car uses an ultrasonic sensor to detect nearby obstacles and automatically scans left and right to recommend a safer direction.

## Project Overview

The system consists of two micro:bits:

- **Car Micro:bit:** Controls the motors, measures obstacle distances, performs directional scanning, and communicates with the controller.
- **Controller Micro:bit:** Reads button presses, accelerometer movement, and a physical speed switch. It also displays driving directions and obstacle warnings using the LED matrix and controls an SG90 servo indicator.

The project combines embedded programming, wireless communication, sensor integration, and robotic navigation.

## Features

### 1. Wireless Remote Control

The car communicates with the handheld controller using the built-in micro:bit radio module.

The controller continuously sends movement commands and the selected speed to the car.

Supported movements:

- Forward
- Backward
- Turn left
- Turn right
- Stop

### 2. Motion-Based Driving

The controller uses its accelerometer to detect forward and backward tilting.

| Controller Input               | Car Action    |
| ------------------------------ | ------------- |
| Hold A + B and tilt forward    | Move forward  |
| Hold A + B and tilt backward   | Move backward |
| Hold A                         | Turn left     |
| Hold B                         | Turn right    |
| Release both buttons           | Stop          |
| Hold A + B without enough tilt | Stop          |

A deadband of 200 accelerometer units prevents small movements from accidentally activating the motors.

### 3. Normal and Turbo Speed

The controller includes a physical switch connected to pin P1.

Pressing the switch toggles between two speed modes.

| Speed Mode | Motor Speed Value |
| ---------- | ----------------- |
| Normal     | 40                |
| Turbo      | 80                |

The controller sends the selected speed with each movement command.

### 4. Ultrasonic Obstacle Detection

An ultrasonic sensor measures the distance between the car and objects in front of it.

The sensor uses:

- Trigger: P14
- Echo: P15

The car checks the distance approximately every 100 milliseconds during normal operation.

**Obstacle detection settings:**

| Parameter                           | Value  |
| ----------------------------------- | ------ |
| Stop distance                       | 10 cm  |
| Safe distance                       | 20 cm  |
| Distance measurement interval       | 100 ms |
| Consecutive close readings required | 2      |

An obstacle is confirmed after two consecutive valid readings at or below 10 cm.

When an obstacle is confirmed during forward movement, the car stops and begins its automatic scanning process.

Invalid ultrasonic readings are not treated as confirmed obstacles.

### 5. Automatic Left and Right Scanning

When the car encounters a confirmed obstacle while moving forward, it automatically performs a directional scan.

**Scanning sequence:**

1. Stop the motors.
2. Wait 200 milliseconds.
3. Turn left for 350 milliseconds.
4. Stop and wait 250 milliseconds.
5. Measure the distance on the left.
6. Turn right for 700 milliseconds to reach the opposite side.
7. Stop and wait 250 milliseconds.
8. Measure the distance on the right.
9. Turn left for 350 milliseconds to return toward the original direction.
10. Compare the measured distances.
11. Send a navigation recommendation to the controller.

The car recommends one of three results:

| Result  | Meaning                                               |
| ------- | ----------------------------------------------------- |
| LEFT    | Left direction has sufficient space and is preferred  |
| RIGHT   | Right direction has sufficient space and is preferred |
| BLOCKED | Neither direction meets the safe-distance requirement |

If both directions are safe, the car recommends the direction with the greater measured distance. If the measurements are equal, it recommends LEFT.

The scan uses timed motor rotations rather than measured heading angles. Actual turning angles depend on the motors, surface, and battery condition.

**Note:** The car does not automatically drive in the recommended direction. The user manually controls the next movement.

### 6. LED Direction Display

The controller uses the micro:bit's 5×5 LED matrix to display movement directions, obstacle warnings, and scanning status.

| LED Display | Meaning                               |
| ----------- | ------------------------------------- |
| Up arrow    | Forward/default direction             |
| Down arrow  | Backward                              |
| Left arrow  | Turn left or recommended left         |
| Right arrow | Turn right or recommended right       |
| Diamond     | Automatic scanning in progress        |
| X symbol    | Obstacle warning or blocked direction |

Navigation recommendations take priority over normal movement arrows while they remain active.

The default display is an up arrow, including when the controller is stopped without an active warning.

### 7. SG90 Servo Direction Indicator

An SG90 servo motor is connected to P2 on the handheld controller.

The servo acts as a visual direction indicator.

| Servo State | PWM Value |
| ----------- | --------- |
| Left        | 65        |
| Center      | 77        |
| Right       | 90        |

During scanning, the servo alternates between its left and right positions approximately every 400 milliseconds.

After scanning, it points toward the recommended direction.

The servo returns to its center position when there is no active left or right recommendation and scanning is not in progress.

These values are MicroPython PWM duty values, not servo angles in degrees.

### 8. Wireless Communication

Both micro:bits use identical radio settings.

| Setting       | Value        |
| ------------- | ------------ |
| Radio group   | 91           |
| Radio channel | 42           |
| Radio address | `0x7A39C521` |
| Radio power   | 6            |

The controller sends movement commands in the following format:

`CMD:FORWARD:40`

The car sends obstacle status messages:

- `OBS:1` — Confirmed obstacle
- `OBS:0` — No confirmed obstacle

The car also sends:

- `SCAN` — Scanning has started
- `NAV:LEFT` — Left direction recommended
- `NAV:RIGHT` — Right direction recommended
- `NAV:BLOCKED` — Neither direction is considered safe

The controller processes these messages to update its LED display and servo indicator.

### 9. Radio Connection Safety

The car includes a radio communication timeout.

If it does not receive a valid movement command for more than 500 milliseconds, it:

- Stops the motors.
- Cancels any active scanning sequence.
- Sets the movement command to STOP.

The controller also clears stale obstacle information after 1,500 milliseconds without an obstacle-status update.

A scanning timeout of 7 seconds is used on the controller. If scanning does not finish within this period, the controller displays a blocked warning.

## Hardware Requirements

| Component                         | Quantity    | Purpose                             |
| --------------------------------- | ----------- | ----------------------------------- |
| BBC micro:bit                     | 2           | Car control and handheld controller |
| Keyestudio KS4036 MiniCar         | 1           | Robotic car platform                |
| Motor driver (I2C address `0x30`) | 1           | Controls the car motors             |
| Ultrasonic distance sensor        | 1           | Detects obstacles                   |
| SG90 servo motor                  | 1           | Controller direction indicator      |
| Physical push-button switch       | 1           | Toggles normal/turbo speed          |
| Power supplies                    | As required | Powers the car and controller       |
| Connecting wires                  | As required | Hardware connections                |

## Hardware Connections

### Car Micro:bit

| Component        | Connection                              |
| ---------------- | --------------------------------------- |
| Motor driver     | I2C address `0x30`                      |
| Ultrasonic TRIG  | P14                                     |
| Ultrasonic ECHO  | P15                                     |
| Ultrasonic power | Compatible power and ground connections |

The motor driver receives commands through I2C.

Motor direction mappings used in the code:

| Movement | Motor Values (1, 2, 3, 4) |
| -------- | ------------------------- |
| Stop     | `(0, 0, 0, 0)`            |
| Forward  | `(0, speed, speed, 0)`    |
| Backward | `(speed, 0, 0, speed)`    |
| Left     | `(speed, 0, speed, 0)`    |
| Right    | `(0, speed, 0, speed)`    |

### Controller Micro:bit

| Component         | Connection                |
| ----------------- | ------------------------- |
| Speed switch      | P1 and GND                |
| SG90 servo signal | P2                        |
| SG90 servo power  | Compatible power supply   |
| SG90 servo ground | Common ground             |
| Button A          | Built-in micro:bit button |
| Button B          | Built-in micro:bit button |
| Accelerometer     | Built-in micro:bit sensor |
| LED matrix        | Built-in 5×5 display      |

The speed switch uses the internal pull-up resistor on P1.

## Software Requirements

- BBC micro:bit Python Editor
- MicroPython for BBC micro:bit
- Two compatible BBC micro:bits
- USB connection for programming

The programs use these MicroPython modules:

```python
from microbit import *
import radio
from time import sleep_us, ticks_us, ticks_diff
```

The programs are designed for the BBC micro:bit MicroPython environment.

They cannot be executed directly using standard desktop Python because they depend on micro:bit-specific hardware modules.

VS Code can be used to view and edit the Python source files, but it is not required to flash the programs.

## Installation and Setup

### Step 1: Prepare the Car

1. Open the BBC micro:bit Python Editor.
2. Open the car's MicroPython source code.
3. Verify the ultrasonic sensor and motor-driver connections.
4. Download the car program as a `.hex` file.
5. Connect the car micro:bit to the computer.
6. Flash the car `.hex` file onto the car micro:bit.

### Step 2: Prepare the Controller

1. Open the BBC micro:bit Python Editor.
2. Open the controller's MicroPython source code.
3. Connect the speed switch to P1 and GND.
4. Connect the SG90 servo signal to P2.
5. Download the controller program as a `.hex` file.
6. Connect the controller micro:bit to the computer.
7. Flash the controller `.hex` file onto the controller micro:bit.

### Step 3: Test the System

1. Power on both micro:bits.
2. Verify that both programs use matching radio settings.
3. Place the car on a clear, flat surface.
4. Test the left and right buttons.
5. Test forward and backward tilt controls.
6. Toggle the speed switch.
7. Place an obstacle in front of the car.
8. Verify that the car stops and performs directional scanning.
9. Check the navigation recommendation on the controller's LED display.
10. Verify the SG90 servo indicator.

## Project File Structure

```text
microbit-minicar-robot/
├── README.md
├── source-code/
│   ├── car.py
│   └── controller.py
└── hex-files/
    ├── car.hex
    └── controller.hex
```

- `car.py` — MicroPython program for the robotic car.
- `controller.py` — MicroPython program for the handheld controller.
- `car.hex` — Compiled program for the car micro:bit.
- `controller.hex` — Compiled program for the controller micro:bit.
- `README.md` — Project documentation.

## Current Limitations

- The car provides navigation recommendations but does not autonomously follow them.
- Scanning turns are controlled by time, not by precise compass measurements.
- Turning accuracy depends on battery voltage, wheel speed, and the driving surface.
- Ultrasonic measurements can fail or return invalid values.
- The code does not continuously display the measured distance in centimeters on the controller.
- The servo indicates scanning activity and navigation recommendations, not the car's absolute compass heading.
- The radio timeout is a basic software safety mechanism and is not a substitute for a physical emergency stop.

## Skills Demonstrated

This project demonstrates practical experience with:

- MicroPython programming
- Embedded systems
- Wireless radio communication
- I2C motor control
- Ultrasonic distance sensing
- Accelerometer-based input
- PWM servo control
- State-machine programming
- Real-time sensor monitoring
- Obstacle detection
- Robotics troubleshooting
- Hardware and software integration

## Future Improvements

Potential future improvements include:

- Autonomous movement toward the recommended direction
- More accurate turning using compass feedback
- Improved motor speed balancing
- Continuous distance visualization
- More reliable handling of invalid sensor measurements
- Automatic maze navigation
- Additional obstacle sensors
- Improved radio communication feedback

## Author

**Biplov Parajuli**

Computer Science Student | Software Development | Embedded Systems | Robotics

GitHub: [parajulibiplov10-lgtm](https://github.com/parajulibiplov10-lgtm)

## Project Summary

This project demonstrates a wireless robotic car controlled through a handheld micro:bit device.

It integrates radio communication, accelerometer-based driving, ultrasonic obstacle detection, automatic directional scanning, and servo-based visual feedback.

The project focuses on embedded programming, hardware integration, and robotic navigation using MicroPython.
