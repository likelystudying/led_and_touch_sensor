import time
from rpi_ws281x import PixelStrip, Color
import threading
import math

# it starts from 0

# LED strip configuration:
LED_COUNT      = 60       # Number of LEDs
LED_PIN        = 18       # GPIO (LED_PIN=18 == 12PIN)
LED_FREQ_HZ    = 800000   # LED signal frequency in Hz
LED_DMA        = 10       # DMA channel
#LED_BRIGHTNESS = 1      # 0-255
LED_BRIGHTNESS = 30   # Make it visible for breathing
LED_INVERT     = False    # True if using inverting circuit
LED_CHANNEL    = 0        # PWM channel

# Create PixelStrip object
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def getColor(color_name):
    if color_name == "pink":
        return Color(249,8,209)
    elif color_name == "blue":
        return Color(8,0,249)
    elif color_name == "green":
        return Color(0,255,0)
    else:
        return Color(255,255,255)


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

def turn_all(num):
    try:
        for i in range(strip.numPixels()):
            turnOn(i, num, Color(255, 255, 255))  #off 
    except Exception as e:
        print("LED error:", e)

# FROM 
# time.localtiime() =>  led #
# second = 0 ~ 61    0 ~ 59
# minute = 0 ~ 59    0 ~ 59
# hour =   0 ~ 23    0 ~ 59
def convertTimeToLed():
    now = time.localtime()
    hour, minute, second = now.tm_hour, now.tm_min, now.tm_sec

    ret_hour = (hour %12) * 5
    ret_min = minute
    if second >= 60:
        ret_sec = 0
    else:
        ret_sec = second

    return ret_hour, ret_min, ret_sec



def test4():
    turn_all(0.0)

    for _ in range(120):
        led_hour, led_min, led_sec = convertTimeToLed()
        print(f"{led_hour}:{led_min}:{led_sec} ")

        #second
        if led_sec != led_min and led_sec != led_hour:
            turnOn(led_sec, 1.0, getColor("pink"))  # ON
        else:
            print(f"led_sec not applied {led_hour}:{led_min}:{led_sec} ")

        #minute
        if led_min != led_hour:
            turnOn(led_min, 1.0, getColor("green"))
        else:
            print(f"led_min not applied {led_hour}:{led_min}:{led_sec} ")

        #hour
        turnOn(led_hour, 1.0, getColor("blue"))

        if led_sec <= 0:
            turn_all(0.0)

        time.sleep(1)

    turn_all(0.0)



# Function to convert RGB + intensity to Color
def get_color_with_intensity(r, g, b, intensity):
    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)
    return Color(r, g, b)

# Breathing effect
def breathe(led_id, color=(0, 0, 255), speed=0.02):
    """
    color : tuple(r,g,b) for the LED color
    speed : float, delay between brightness steps
    """
    try:
        while True:
            # Use a sine wave for smooth breathing
            for i in range(0, 360, 2):
                intensity = (math.sin(math.radians(i)) + 1) / 2  # 0.0 to 1.0
                c = get_color_with_intensity(color[0], color[1], color[2], intensity)
                strip.setPixelColor(led_id, c)
                strip.show()
                time.sleep(speed)
    except KeyboardInterrupt:
        # Turn off all LEDs on exit
        strip.setPixelColor(led_id, Color(0,0,0))
        strip.show()



def test5():
    # Run breathing in a separate thread
    led_id = 59
    breathe_thread = threading.Thread(target=breathe, args=(led_id, (0, 0, 255), 0.02), daemon=True)
    breathe_thread.start()

    # Main loop can do other things while breathing continues
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

# Main program
if __name__ == "__main__":
    test5()