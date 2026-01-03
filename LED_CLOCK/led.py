import time
import math
import asyncio
from rpi_ws281x import PixelStrip, Color

class AsyncLEDClock:
    def __init__(self, led_count=60, led_pin=18, brightness=30):
        self.strip = PixelStrip(led_count, led_pin, 800000, 10, False, brightness, 0)
        self.strip.begin()

        # Locks for thread-safe LED updates (async-safe via asyncio.Lock)
        self.led_lock = asyncio.Lock()
        self.breathing_lock = asyncio.Lock()

        # Shared state for breathing LEDs
        self.breathing_minute = 0
        self.breathing_hour = 0

    # Async-safe setPixelColor
    async def safe_setPixelColor(self, led_num, color):
        async with self.led_lock:
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

    # Breathing effect for a single LED
    async def breathe(self, get_led_func, color=(0,0,255), speed=0.02):
        previous_led = None
        while True:
            current_led = await get_led_func()
            # Turn off previous if it changed
            if previous_led is not None and previous_led != current_led:
                await self.safe_setPixelColor(previous_led, Color(0,0,0)) 
            previous_led = current_led

            for i in range(0, 360, 2):
                current_led = await get_led_func()
                if current_led != previous_led:
                    break
                intensity = (math.sin(math.radians(i)) + 1) / 2
                c = self.get_color_with_intensity(color[0], color[1], color[2], intensity)
                await self.safe_setPixelColor(current_led, c)
                await asyncio.sleep(speed)

    # Clock calculation
    @staticmethod
    def convertTimeToLed():
        now = time.localtime()
        hour, minute, second = now.tm_hour, now.tm_min, now.tm_sec
        return (hour % 12) * 5, minute, second

    # Async getters for breathing LEDs
    async def get_breathing_minute(self):
        async with self.breathing_lock:
            return self.breathing_minute

    async def get_breathing_hour(self):
        async with self.breathing_lock:
            return self.breathing_hour

    # Clock update task
    async def clock_task(self):
        while True:
            led_hour, led_minute, led_second = self.convertTimeToLed()

            # Update breathing LED IDs
            async with self.breathing_lock:
                self.breathing_minute = led_minute
                self.breathing_hour = led_hour

            # Update second LED (solid)
            if led_second != led_minute and led_second != led_hour:
                await self.safe_setPixelColor(led_second, self.getColor("pink"))

            # Turn off previous second after 1 sec
            await asyncio.sleep(1) #
            prev_second = (led_second) % 60
            await self.safe_setPixelColor(prev_second, Color(0,0,0))

    # Turn off all LEDs
    async def turn_all_off(self):
        async with self.led_lock:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(0,0,0))
            self.strip.show()

    # Start all tasks
    async def start(self):
        try:
            await asyncio.gather(
                self.breathe(self.get_breathing_minute, (0,255,0), 0.02),
                self.breathe(self.get_breathing_hour, (0,0,255), 0.02),
                self.clock_task()
            )
        except KeyboardInterrupt:
            print("Exiting...")
            await self.turn_all_off()


# Main
if __name__ == "__main__":
    clock = AsyncLEDClock()
    asyncio.run(clock.start())
