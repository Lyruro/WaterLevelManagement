from gpiozero import DistanceSensor
from time import sleep

sensor = DistanceSensor(echo=24, trigger=23, max_distance=2.0)

try:
    while True:
        distance_cm = sensor.distance * 100

        print(f"Object Distance: {distance_cm:.1f} cm")

        sleep(0.5) 

except KeyboardInterrupt:
    print("Measurement stopped by user")
