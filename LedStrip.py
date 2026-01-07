import time
import threading
import math
from rpi_ws281x import PixelStrip, Color
from TouchSensor import MCP23017TouchLED, TouchConsumer

class LedStrip:
    def __init__(self, led_count=60, led_pin=18, brightness=30):
        self.strip = PixelStrip(
            led_count, led_pin, 800000, 10, False, brightness, 0)
        self.strip.begin()
        self.led_count = led_count
        self._lock = threading.Lock()
        #monitor what's on and off
        self.state = [False] * self.led_count  # False = OFF, True = ON

    def set_pixel(self, index, color):
        if 0 <= index < self.led_count:
            with self._lock:
                self.strip.setPixelColor(index, color)
                self.state[index] = (color != Color(0, 0, 0))
                self.strip.show()

    def turn_off_pixel(self, index):
        self.set_pixel(index, Color(0, 0, 0))

    def turn_all(self, color):
        with self._lock:
            for i in range(self.led_count):
                self.strip.setPixelColor(i, color)
                self.state[i] = (color != Color(0, 0, 0))
            self.strip.show()

    def turn_all_off(self):
        self.turn_all(Color(0, 0, 0))

    # Color helpers
    def red(self): return Color(255, 0, 0)
    def green(self): return Color(0, 255, 0)
    def blue(self): return Color(0, 0, 255)

class TouchConsumer2:
    def __init__(self, led_strip, strip_led_pins, debounce_ms=300):
        self.led_strip = led_strip
        self.strip_led_pins = strip_led_pins
        self.debounce_ms = debounce_ms
        self.last_touch = [0] * len(strip_led_pins)
        self.test(self.led_strip, self.strip_led_pins)

    #initialize leds 
    def test(self, led_strip, strip_led_pins):
        print("test1")
        for i, led_id in enumerate(strip_led_pins):
            led_strip.set_pixel(led_id, led_strip.green())
            time.sleep(1)
        
    def on_touch(self, sensor_index, pressed):
        if pressed:
            print(f"[CALLBACK] Sensor {sensor_index} PRESSED")
        else:
            print(f"[CALLBACK] Sensor {sensor_index} RELEASED")

        now = time.time() * 500  # ms

        if sensor_index >= len(self.strip_led_pins):
            print(f"sensor_index {sensor_index} >= strip_led_pins count {len(self.strip_led_pins)}")
            return

        if now - self.last_touch[sensor_index] < self.debounce_ms:
            print(f"ignore bounce")
            return  # ignore bounce

        self.last_touch[sensor_index] = now

        led_index = self.strip_led_pins[sensor_index]
        print(f"led_index {led_index} sensor_index {sensor_index}")

        if self.led_strip.state[led_index]:
            print(f"turning off led index")
            self.led_strip.turn_off_pixel(led_index)
        #else:
            #self.led_strip.set_pixel(led_index, self.led_strip.green())

        

def testCallback():
    #PA
    sensor_pins = [2, 3, 4, 5]

    touch_led = MCP23017TouchLED(
        sensor_pins=sensor_pins,
        led_pins=[1]
    )
    # consumer = TouchConsumer()
    # touch_led.set_touch_callback(consumer.on_touch)

    led_strip = LedStrip()
    strip_led_pins = [15, 19, 23, 27]

    consumer = TouchConsumer2(led_strip, strip_led_pins)
    touch_led.set_touch_callback(consumer.on_touch)

    touch_led.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        touch_led.cleanup()


# Main
if __name__ == "__main__":
    #test1()
    testCallback()
