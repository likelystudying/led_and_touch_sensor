import RPi.GPIO as GPIO
import time

#test
#sensor #1
#-----------------
#sensor rpi 
#-----------------
#3v     pin1  3V3
#gnd    pin9  GND
#sig    pin11 GPIO17

#sensor #2
#-----------------
#sensor rpi 
#-----------------
#3v     pin17 3V3
#gnd    pin39  GND
#sig    pin13 GPIO27

#python3 touch2.py


TOUCH_PIN1 = 17  # GPIO17 (Pin 11)
TOUCH_PIN2 = 27  # second one

GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN1, GPIO.IN)
GPIO.setup(TOUCH_PIN2, GPIO.IN)

print("Touch sensor test (CTRL+C to exit)")

try:
    while True:
        if GPIO.input(TOUCH_PIN1):
            a = "👆 Touch detected"
        else:
            a = "No touch"

        if GPIO.input(TOUCH_PIN2):
            b = "👆 Touch detected"
        else:
            b = "No touch"

        print(f"1: {a} 2: {b}")


        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting")

finally:
    GPIO.cleanup()
