from gpiozero import DistanceSensor, OutputDevice
from time import sleep

# Setup ultrasonic sensor (HC-SR04)
sensor = DistanceSensor(echo=24, trigger=23, max_distance=2.0)

# Setup relay (GPIO 17)
relay = OutputDevice(17, active_high=False, initial_value=False)  # active_high=False means LOW = ON

# Track pump state
pump_is_on = False

try:
    while True:
        # Read distance and convert to cm
        distance_cm = sensor.distance * 100
        print(f"Object Distance: {distance_cm:.1f} cm")

        # Turn ON pump if distance is 17 cm or more and it's currently off
        if distance_cm <= 5 and not pump_is_on:
            print("Distance >= 17 cm → Turning pump ON.")
            relay.on()
            pump_is_on = True

        # Turn OFF pump if distance is 5 cm or less and it's currently on
        elif distance_cm >= 17 and pump_is_on:
            print("Distance <= 5 cm → Turning pump OFF.")
            relay.off()
            pump_is_on = False

        sleep(0.5)

except KeyboardInterrupt:
    print("Measurement stopped by user.")
    relay.off()
