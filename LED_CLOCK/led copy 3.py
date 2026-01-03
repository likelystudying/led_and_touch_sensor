import time, threading, math
from rpi_ws281x import PixelStrip, Color

# LED strip config
LED_COUNT = 60
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 30
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# Locks
led_lock = threading.Lock()
breathing_lock = threading.Lock()

# Shared globals for breathing LEDs
breathing_minute = 0
breathing_hour = 0

# Thread-safe setPixelColor
def safe_setPixelColor(led_num, color):
    with led_lock:
        strip.setPixelColor(led_num, color)
        strip.show()

# Convert RGB + intensity to Color
def get_color_with_intensity(r, g, b, intensity):
    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)
    return Color(r, g, b)

# Predefined colors
def getColor(name):
    if name == "pink":
        return Color(249, 8, 209)
    elif name == "blue":
        return Color(8, 0, 249)
    elif name == "green":
        return Color(0, 255, 0)
    else:
        return Color(255, 255, 255)

# Breathing function for a shared global LED
def breathe(get_led_func, color=(0,0,255), speed=0.02):
    previous_led = None
    while True:
        current_led = get_led_func()
        # Turn off previous if it changed
        if previous_led is not None and previous_led != current_led:
            safe_setPixelColor(previous_led, Color(0,0,0))
        previous_led = current_led

        for i in range(0, 360, 2):
            current_led = get_led_func()
            if current_led != previous_led:
                break
            intensity = (math.sin(math.radians(i)) + 1) / 2
            c = get_color_with_intensity(color[0], color[1], color[2], intensity)
            safe_setPixelColor(current_led, c)
            time.sleep(speed)

# Clock calculation
def convertTimeToLed():
    now = time.localtime()
    hour, minute, second = now.tm_hour, now.tm_min, now.tm_sec
    led_hour = (hour % 12) * 5
    led_minute = minute
    led_second = second
    return led_hour, led_minute, led_second

# Thread-safe getters for breathing LEDs
def get_breathing_minute():
    global breathing_minute
    with breathing_lock:
        return breathing_minute

def get_breathing_hour():
    global breathing_hour
    with breathing_lock:
        return breathing_hour

# Main clock thread
def clock_thread():
    global breathing_minute, breathing_hour
    while True:
        led_hour, led_minute, led_second = convertTimeToLed()

        # Update shared globals for breathing
        with breathing_lock:
            breathing_minute = led_minute
            breathing_hour = led_hour

        # Update seconds (solid)
        if led_second != led_minute and led_second != led_hour:
            safe_setPixelColor(led_second, getColor("pink"))

        # Optional: turn off second LED when it moves
        time.sleep(1)
        # turn off previous second
        prev_second = (led_second - 1) % 60
        safe_setPixelColor(prev_second, Color(0,0,0))

# Turn off all LEDs
def turn_all_off():
    with led_lock:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0,0,0))
        strip.show()


# Main
if __name__ == "__main__":
    try:
        # Start breathing threads
        t_min = threading.Thread(target=breathe, args=(get_breathing_minute,(0,255,0),0.02), daemon=True)
        t_min.start()
        t_hour = threading.Thread(target=breathe, args=(get_breathing_hour,(0,0,255),0.02), daemon=True)
        t_hour.start()

        # Start clock thread
        t_clock = threading.Thread(target=clock_thread, daemon=True)
        t_clock.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")
        turn_all_off()
