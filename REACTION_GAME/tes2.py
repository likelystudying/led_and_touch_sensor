import RPi.GPIO as GPIO
import time
from rpi_ws281x import PixelStrip, Color
import threading


# LED strip configuration:
LED_COUNT      = 60       # Number of LEDs
LED_PIN        = 18       # GPIO (LED_PIN=18 == 12PIN)
LED_FREQ_HZ    = 800000   # LED signal frequency in Hz
LED_DMA        = 10       # DMA channel
LED_BRIGHTNESS = 1      # 0-255
LED_INVERT     = False    # True if using inverting circuit
LED_CHANNEL    = 0        # PWM channel

# Create PixelStrip object
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()



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


TOUCH_PIN1 = 17  # GPIO17 (Pin 11)
TOUCH_PIN2 = 27  # second one

GPIO.setmode(GPIO.BCM)
GPIO.setup(TOUCH_PIN1, GPIO.IN)
GPIO.setup(TOUCH_PIN2, GPIO.IN)


def turnOn(led_num, intensity, color):
    """
    led_num   : LED index (0-based)
    intensity : 0.0 to 1.0
    color     : Color(r, g, b)
    """
    if not (0 <= led_num < strip.numPixels()):
        return

    intensity = max(0.0, min(1.0, intensity))

    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF

    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)

    strip.setPixelColor(led_num, Color(r, g, b))
    strip.show()

def test_all_leds_toggle_manual(on_event):
    try:
        while True:
            for i in range(strip.numPixels()):
                if on_event.is_set():
                    turnOn(i, 1.0, Color(255, 255, 255))  # ON
                else:
                    turnOn(i, 0.0, Color(255, 255, 255))  # OFF

                time.sleep(0.05)

            time.sleep(0.5)

    except Exception as e:
        print("LED thread error:", e)

    finally:
        for i in range(strip.numPixels()):
            turnOn(i, 0.0, Color(0, 0, 0))

def test_all_leds_toggle_manual(on_event):
    try:
        while True:
            for i in range(strip.numPixels()):
                if on_event.is_set():
                    turnOn(i, 1.0, Color(255, 255, 255))  # ON
                else:
                    turnOn(i, 0.0, Color(255, 255, 255))  # OFF

                time.sleep(0.05)

            time.sleep(0.5)

    except Exception as e:
        print("LED thread error:", e)

    finally:
        for i in range(strip.numPixels()):
            turnOn(i, 0.0, Color(0, 0, 0))



def test0():
    on_event = threading.Event()
    on_event.clear()  # LEDs start OFF

    led_thread = threading.Thread(
        target=test_all_leds_toggle_manual,
        args=(on_event,),
        daemon=True
    )
    led_thread.start()

    print("Touch sensor test (CTRL+C to exit)")

    try:
        while True:
            if GPIO.input(TOUCH_PIN1):
                a = "👆 Touch"
                on_event.set()
            else:
                a = "No touch"
                on_event.clear()

            if GPIO.input(TOUCH_PIN2):
                b = "👆 Touch"
            else:
                b = "No touch"

            print(f"1: {a} 2: {b}")


            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Exiting")

    finally:
        GPIO.cleanup()


#while on touch the led turns on if not turns off
def test1():
    for i in range(strip.numPixels()):
        turnOn(i, 0.0, Color(0, 0, 0))
    print("Touch sensor test (CTRL+C to exit)")
    try:
        i = 0
        while True:
            if GPIO.input(TOUCH_PIN1):
                a = "👆 Touch"
                i = i+1
            else:
                a = "No touch"

            if i%2 == 0:
                on = True
            else:
                on = False

            if on == True:
                turnOn(0, 1.0, Color(255, 255, 255))  # ON
            else:
                turnOn(0, 0.0, Color(255, 255, 255))  # ON
            print(f"1: {a} {on}")
            time.sleep(0.5)

            if i >=100:
                i = 0

    except KeyboardInterrupt:
        print("Exiting")

    finally:
        GPIO.cleanup()


#while on touch the first led turns on if not turns off
def test2():
    for i in range(strip.numPixels()):
        turnOn(i, 0.0, Color(0, 0, 0))
    print("Touch sensor test (CTRL+C to exit)")

    led_on = False
    last_touch_state = False
    current_touch_state = False

    try:
        while True:
            current_touch_state = GPIO.input(TOUCH_PIN1)
    
            if current_touch_state and not last_touch_state:
                led_on = not led_on
                print( "touch -> toggle led")

                if led_on:
                    turnOn(0, 1.0, Color(255, 255, 255))  # ON
                else:
                    turnOn(0, 0.0, Color(255, 255, 255))  # ON
            last_touch_state = current_touch_state
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting")

    finally:
        for i in range (strip.numPixels()):
            turnOn(i, 0.0, Color(0, 0, 0))
        GPIO.cleanup()


#while on touch all the leds turn on if not turn off
def test3():
    for i in range(strip.numPixels()):
        turnOn(i, 0.0, Color(0, 0, 0))
    print("Touch sensor test (CTRL+C to exit)")

    led_on = False
    last_touch_state = False
    current_touch_state = False

    try:
        while True:
            current_touch_state = GPIO.input(TOUCH_PIN1)
    
            if current_touch_state and not last_touch_state:
                led_on = not led_on
                print( "touch -> toggle led")

                if led_on:
                    for i in range(strip.numPixels()):
                        turnOn(i, 1.0, Color(255, 255, 255))
                else:
                    for i in range(strip.numPixels()):
                        turnOn(i, 0.0, Color(255, 255, 255))

            last_touch_state = current_touch_state
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Exiting")

    finally:
        for i in range (strip.numPixels()):
            turnOn(i, 0.0, Color(0, 0, 0))
        GPIO.cleanup()



test3()