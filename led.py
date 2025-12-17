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

def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def wheel(pos):
    """Generate rainbow colors."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow_cycle(strip, wait_ms=20, iterations=1):
    """Draw rainbow across the strip."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            pixel_index = (i * 256 // strip.numPixels()) + j
            strip.setPixelColor(i, wheel(pixel_index & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)

def test():
    print("Starting LED test...")
    try:
        while True:
            print("Color wipe red")
            color_wipe(strip, Color(255, 0, 0))
            print("Color wipe green")
            color_wipe(strip, Color(0, 255, 0))
            print("Color wipe blue")
            color_wipe(strip, Color(0, 0, 255))
            print("Rainbow cycle")
            rainbow_cycle(strip)

    except KeyboardInterrupt:
        print("Turning off LEDs")
        color_wipe(strip, Color(0, 0, 0), 10)

def test1():
    print("Starting LED test...")
    strip.setPixelColor(LED_COUNT - 1, Color(255, 0, 0))
    strip.show()

def test_all_leds_toggle_with_turnOn():
    on = True  # start with ON

    try:
        while True:
            for i in range(strip.numPixels()):
                if on:
                    turnOn(i, 1.0, Color(255, 255, 255))  # ON
                else:
                    turnOn(i, 0.0, Color(255, 255, 255))  # OFF

                time.sleep(0.05)

            on = not on          # toggle ON/OFF
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Turning off LEDs")
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

# Main program
if __name__ == "__main__":
    #test_all_leds_toggle_with_turnOn()
    #test2()

    on_event = threading.Event()
    on_event.clear()  # LEDs start OFF

    led_thread = threading.Thread(
        target=test_all_leds_toggle_manual,
        args=(on_event,),
        daemon=True
    )
    led_thread.start()



print("LEDs ON")
on_event.set()     # turn LEDs ON

time.sleep(3)

print("LEDs OFF")
on_event.clear()   # turn LEDs OFF