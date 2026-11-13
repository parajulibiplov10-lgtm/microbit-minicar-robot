
from microbit import *
import radio

radio.config(
    group=91,
    channel=42,
    address=0x7A39C521,
    power=6
)
radio.on()

NORMAL_SPEED = 40
TURBO_SPEED = 80
DEADBAND = 200

SWITCH = pin1
SWITCH.set_pull(SWITCH.PULL_UP)

SERVO = pin2
SERVO.set_analog_period(20)

SERVO_LEFT = 65
SERVO_CENTER = 77
SERVO_RIGHT = 90

turbo = False
last_button = False
last_press_time = -1000

obstacle = False
last_status_time = -5000

scanning = False
scan_time = -5000

navigation = ""
navigation_time = -5000

fan_side = False
last_fan_time = running_time()
last_servo = -1

previous_command = "STOP"


def set_fan(position):
    global last_servo

    if position != last_servo:
        SERVO.write_analog(position)
        last_servo = position


def update_fan(now):
    global fan_side, last_fan_time

    if scanning:
        if now - last_fan_time >= 400:
            fan_side = not fan_side
            last_fan_time = now

        if fan_side:
            set_fan(SERVO_LEFT)
        else:
            set_fan(SERVO_RIGHT)

    elif navigation == "LEFT":
        set_fan(SERVO_LEFT)

    elif navigation == "RIGHT":
        set_fan(SERVO_RIGHT)

    else:
        set_fan(SERVO_CENTER)


def show_direction(command):
    if scanning:
        display.show(Image.DIAMOND)

    elif navigation == "LEFT":
        display.show(Image.ARROW_W)

    elif navigation == "RIGHT":
        display.show(Image.ARROW_E)

    elif navigation == "BLOCKED":
        display.show(Image.NO)

    elif obstacle:
        display.show(Image.NO)

    elif command == "BACKWARD":
        display.show(Image.ARROW_S)

    elif command == "LEFT":
        display.show(Image.ARROW_W)

    elif command == "RIGHT":
        display.show(Image.ARROW_E)

    else:
        display.show(Image.ARROW_N)


set_fan(SERVO_CENTER)

while True:
    now = running_time()

    # White switch toggles turbo
    pressed = SWITCH.read_digital() == 0

    if pressed and not last_button:
        if now - last_press_time > 250:
            turbo = not turbo
            last_press_time = now

    last_button = pressed

    speed = TURBO_SPEED if turbo else NORMAL_SPEED

    # Original driving controls
    a = button_a.is_pressed()
    b = button_b.is_pressed()

    if a and b:
        tilt = accelerometer.get_y()

        if tilt < -DEADBAND:
            command = "FORWARD"
        elif tilt > DEADBAND:
            command = "BACKWARD"
        else:
            command = "STOP"

    elif a:
        command = "LEFT"

    elif b:
        command = "RIGHT"

    else:
        command = "STOP"

    radio.send("CMD:{}:{}".format(command, speed))

    # Receive messages
    for i in range(5):
        message = radio.receive()

        if message is None:
            break

        if message == "OBS:1":
            obstacle = True
            last_status_time = now

        elif message == "OBS:0":
            obstacle = False
            last_status_time = now

        elif message == "SCAN":
            scanning = True
            scan_time = now
            navigation = ""

        elif message.startswith("NAV:"):
            navigation = message[4:]
            navigation_time = now
            scanning = False

    # Scan timeout
    if scanning and now - scan_time > 7000:
        scanning = False
        navigation = "BLOCKED"
        navigation_time = now

    # Clear old recommendation after steering
    if navigation:
        if (
            command in ("LEFT", "RIGHT", "BACKWARD")
            and command != previous_command
        ):
            navigation = ""

    if navigation and now - navigation_time > 15000:
        navigation = ""

    previous_command = command

    # Do not treat missing messages as obstacles
    if now - last_status_time > 1500:
        obstacle = False

    update_fan(now)
    show_direction(command)

    sleep(50)
