
from microbit import *
import radio
from time import sleep_us, ticks_us, ticks_diff

radio.config(
    group=91,
    channel=42,
    address=0x7A39C521,
    power=6
)
radio.on()

NORMAL_SPEED = 40
TURBO_SPEED = 80

STOP_DISTANCE = 10
SAFE_DISTANCE = 20
TIMEOUT_MS = 500
DISTANCE_INTERVAL = 100

TURN_MS = 350
SETTLE_MS = 250

TRIG = pin14
ECHO = pin15

speed = NORMAL_SPEED
command = "STOP"
last_command_time = running_time()

distance = -1
last_distance_time = -1000
last_valid_time = -1000

close_count = 0
obstacle_confirmed = False
scan_done = False

scan_stage = 0
stage_time = 0
left_distance = -1
right_distance = -1

last_motor = None


def motors(a, b, c, d):
    global last_motor

    values = (a, b, c, d)

    if values == last_motor:
        return

    try:
        i2c.write(0x30, bytes([1, a]))
        i2c.write(0x30, bytes([2, b]))
        i2c.write(0x30, bytes([3, c]))
        i2c.write(0x30, bytes([4, d]))
        last_motor = values
    except OSError:
        last_motor = None
        display.show("E")


def stop():
    motors(0, 0, 0, 0)


def forward():
    motors(0, speed, speed, 0)


def backward():
    motors(speed, 0, 0, speed)


def left():
    motors(speed, 0, speed, 0)


def right():
    motors(0, speed, 0, speed)


def read_distance():
    TRIG.write_digital(0)
    sleep_us(5)
    TRIG.write_digital(1)
    sleep_us(10)
    TRIG.write_digital(0)

    start = ticks_us()

    while ECHO.read_digital() == 0:
        if ticks_diff(ticks_us(), start) > 30000:
            return -1

    pulse_start = ticks_us()

    while ECHO.read_digital() == 1:
        if ticks_diff(ticks_us(), pulse_start) > 30000:
            return -1

    pulse = ticks_diff(ticks_us(), pulse_start)
    return round(pulse * 0.01715)


def start_scan(now):
    global scan_stage, stage_time, scan_done

    stop()
    scan_done = True
    scan_stage = 1
    stage_time = now

    radio.send("SCAN")


def update_scan(now):
    global scan_stage, stage_time
    global left_distance, right_distance

    elapsed = now - stage_time

    if scan_stage == 1:
        if elapsed >= 200:
            left()
            scan_stage = 2
            stage_time = now

    elif scan_stage == 2:
        if elapsed >= TURN_MS:
            stop()
            scan_stage = 3
            stage_time = now

    elif scan_stage == 3:
        if elapsed >= SETTLE_MS:
            left_distance = read_distance()
            right()
            scan_stage = 4
            stage_time = now

    elif scan_stage == 4:
        if elapsed >= TURN_MS * 2:
            stop()
            scan_stage = 5
            stage_time = now

    elif scan_stage == 5:
        if elapsed >= SETTLE_MS:
            right_distance = read_distance()
            left()
            scan_stage = 6
            stage_time = now

    elif scan_stage == 6:
        if elapsed >= TURN_MS:
            stop()
            scan_stage = 0

            left_ok = left_distance >= SAFE_DISTANCE
            right_ok = right_distance >= SAFE_DISTANCE

            if left_ok and right_ok:
                if left_distance >= right_distance:
                    direction = "LEFT"
                else:
                    direction = "RIGHT"
            elif left_ok:
                direction = "LEFT"
            elif right_ok:
                direction = "RIGHT"
            else:
                direction = "BLOCKED"

            radio.send("NAV:" + direction)


stop()
display.show(Image.YES)
sleep(500)
display.clear()

while True:
    now = running_time()

    message = radio.receive()

    if message and message.startswith("CMD:"):
        parts = message.split(":")

        if len(parts) == 3:
            new_command = parts[1]

            if new_command in (
                "FORWARD", "BACKWARD",
                "LEFT", "RIGHT", "STOP"
            ):
                try:
                    requested_speed = int(parts[2])
                except ValueError:
                    requested_speed = NORMAL_SPEED

                if requested_speed == TURBO_SPEED:
                    speed = TURBO_SPEED
                else:
                    speed = NORMAL_SPEED

                command = new_command
                last_command_time = running_time()

    # Stop on lost radio connection
    if running_time() - last_command_time > TIMEOUT_MS:
        scan_stage = 0
        command = "STOP"
        stop()
        sleep(20)
        continue

    # Complete automatic scan
    if scan_stage != 0:
        update_scan(now)
        sleep(20)
        continue

    # Read ultrasonic sensor
    if now - last_distance_time >= DISTANCE_INTERVAL:
        reading = read_distance()
        last_distance_time = running_time()

        if reading >= 0:
            distance = reading
            last_valid_time = running_time()

            if reading <= STOP_DISTANCE:
                close_count += 1

                if close_count >= 2:
                    obstacle_confirmed = True

            else:
                close_count = 0

                if reading > SAFE_DISTANCE:
                    obstacle_confirmed = False
                    scan_done = False

        else:
            # Invalid reading is not an obstacle
            close_count = 0

        # Send confirmed obstacle status
        if obstacle_confirmed:
            radio.send("OBS:1")
        else:
            radio.send("OBS:0")

    # Drive
    if command == "FORWARD":

        if obstacle_confirmed:
            stop()

            if not scan_done:
                start_scan(now)

        else:
            forward()

    elif command == "BACKWARD":
        backward()

    elif command == "LEFT":
        left()

    elif command == "RIGHT":
        right()

    else:
        stop()

    sleep(20)
