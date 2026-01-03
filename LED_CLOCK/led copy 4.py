import time
import threading
import math
from rpi_ws281x import PixelStrip, Color

class LEDClock:
    def __init__(self, led_count=60, led_pin=18, brightness=30):
        # LED strip
        self.strip = PixelStrip(led_count, led_pin, 800000, 10, False, brightness, 0)
        self.strip.begin()

        # Locks
        self.led_lock = threading.Lock()
        self.breathing_lock = threading.Lock()

        # Shared state for breathing LEDs
        self.breathing_minute = 0
        self.breathing_hour = 0

    # Thread-safe setPixelColor
    def safe_setPixelColor(self, led_num, color):
        with self.led_lock:
            self.strip.setPixelColor(led_num, color)
            self.strip.show()

    # Convert RGB + intensity to Color
    @staticmethod
    def get_color_with_intensity(r, g, b, intensity):
        r = int(r * intensity)
        g = int(g * intensity)
        b = int(b * intensity)
        return Color(r, g, b)

    # Predefined colors
    @staticmethod
    def getColor(name):
        if name == "pink":
            return Color(249, 8, 209)
        elif name == "blue":
            return Color(8, 0, 249)
        elif name == "green":
            return Color(0, 255, 0)
        else:
            return Color(255, 255, 255)

    # Breathing effect for a single LED (uses instance variable for LED ID)
    def breathe(self, get_led_func, color=(0, 0, 255), speed=0.02):
        previous_led = None
        while True:
            current_led = get_led_func()
            # Turn off previous if it changed
            if previous_led is not None and previous_led != current_led:
                self.safe_setPixelColor(previous_led, Color(0, 0, 0))
            previous_led = current_led

            for i in range(0, 360, 2):
                current_led = get_led_func()
                if current_led != previous_led:
                    break
                intensity = (math.sin(math.radians(i)) + 1) / 2
                c = self.get_color_with_intensity(color[0], color[1], color[2], intensity)
                self.safe_setPixelColor(current_led, c)
                time.sleep(speed)

    # Clock calculation
    @staticmethod
    def convertTimeToLed():
        now = time.localtime()
        hour, minute, second = now.tm_hour, now.tm_min, now.tm_sec
        return (hour % 12) * 5, minute, second

    # Thread-safe getters for breathing LEDs
    def get_breathing_minute(self):
        with self.breathing_lock:
            return self.breathing_minute

    def get_breathing_hour(self):
        with self.breathing_lock:
            return self.breathing_hour

    # Clock update thread
    def clock_thread(self):
        while True:
            led_hour, led_minute, led_second = self.convertTimeToLed()

            # Update breathing LED IDs
            with self.breathing_lock:
                self.breathing_minute = led_minute
                self.breathing_hour = led_hour

            # Update seconds (solid) So skip if they are the same
            if led_second != led_minute and led_second != led_hour:
                self.safe_setPixelColor(led_second, self.getColor("pink"))

            # Turn off previous second
            time.sleep(1)
            #bug display 2 leds
            #prev_second = (led_second - 1) % 60
            prev_second = (led_second) % 60

            self.safe_setPixelColor(prev_second, Color(0, 0, 0))

    # Turn off all LEDs
    def turn_all_off(self):
        with self.led_lock:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()

    # Start all threads
    def start(self):
        # Minute breathing thread
        t_min = threading.Thread(target=self.breathe, args=(self.get_breathing_minute, (0, 255, 0), 0.02), daemon=True)
        t_min.start()

        # Hour breathing thread
        t_hour = threading.Thread(target=self.breathe, args=(self.get_breathing_hour, (0, 0, 255), 0.02), daemon=True)
        t_hour.start()

        # Clock update thread
        t_clock = threading.Thread(target=self.clock_thread, daemon=True)
        t_clock.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Exiting...")
            self.turn_all_off()


# Main
if __name__ == "__main__":
    clock = LEDClock()
    clock.start()
