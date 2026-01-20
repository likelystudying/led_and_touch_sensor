import time
import threading
import math
from rpi_ws281x import PixelStrip, Color
from TouchSensor import MCP23017TouchLED
import random

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
    def __init__(self, led_strip, strip_led_pins, debounce_ms=300, tries=10):
        self.led_strip = led_strip
        self.strip_led_pins = strip_led_pins
        self.debounce_ms = debounce_ms
        self.last_touch = [0] * len(strip_led_pins)

        # Track which LED is currently active
        self.current_led_index = None
        self.led_pressed_event = threading.Event()
        self.reaction_time = None
        self.total_reaction_time = 0.0
        self.total_wrong_touches = 0

        #start/reset 
        self.start_combo = (0,1)
        self.start_hold_time = 1.0 # 1 sec of hold time
        self.start_press_time = None

        #combo to reset. onTouch() is called separately so we need a thread to keep a track
        self.sensor_pressed = [False] * len(strip_led_pins)
        self.combo_thread = threading.Thread(target=self._combo_monitor)
        self.combo_thread.daemon = True
        self.combo_thread.start()

        #restart the game
        self.running = True
        self.tries = tries

        # Start reaction game thread
        self.game_thread = threading.Thread(target=self.reaction_game_loop)
        self.game_thread.daemon = True
        self.game_thread.start()

    def reaction_game_loop(self):
        while True:
            #restart the game
            self.running = True
            self.total_reaction_time = 0.0
            self.total_wrong_touches = 0

            for _ in range(self.tries):
                if not self.running:
                    break

                # Choose a random LED
                self.current_led_index = random.choice(self.strip_led_pins)
                print(f"[GAME] LED {self.current_led_index} ON")
                self.led_strip.set_pixel(self.current_led_index, self.led_strip.green())
                led_on_time = time.time()  # start time
                self.led_pressed_event.clear()

                # Wait until LED is pressed
                # self.led_pressed_event.wait()  # blocked until touch callback sets it
                while not self.led_pressed_event.is_set():
                    if not self.running:
                        break
                    time.sleep(0.01)
                
                if not self.running:
                    break


                # LED was pressed → measure reaction
                self.reaction_time = time.time() - led_on_time
                print(f"[GAME] LED {self.current_led_index} pressed! Reaction: {self.reaction_time:.3f}s")

                # add up the total time
                self.total_reaction_time = self.reaction_time + self.total_reaction_time

                # Turn off LED
                self.led_strip.turn_off_pixel(self.current_led_index)

                #sleep for between 0 to 3 seconds
                time.sleep(random.uniform(0, 3))
            
            print(f"total time: {self.total_reaction_time}")
            print(f"wrong touches: {self.total_wrong_touches} / {self.tries}")

    def on_touch(self, sensor_index, pressed=True):
        if sensor_index >= len(self.strip_led_pins):
            return

        self.sensor_pressed[sensor_index] = pressed

        # Check start/reset combo
        self._check_start_reset()

        if not pressed:
            return  # only react on press for the game logic

        now = time.time()
        if now - self.last_touch[sensor_index] < self.debounce_ms / 1000:
            return

        self.last_touch[sensor_index] = now
        led_index = self.strip_led_pins[sensor_index]

        if led_index == self.current_led_index:
            #unblocks the while not self.led_pressed_event.is_set()
            self.led_pressed_event.set()
        else:
            self.total_wrong_touches += 1
            print(f"[GAME] Wrong touch ({self.total_wrong_touches})")
            threading.Thread(target=self._blink_red, args=(sensor_index,), daemon=True).start()
   
    def _blink_red(self, sensor_index, duration=0.2):
        """Blink the LED corresponding to sensor_index red briefly without affecting others."""
        led_index = self.strip_led_pins[sensor_index]

        # Save current color
        current_state = self.led_strip.state[led_index]
        # Set to red
        self.led_strip.set_pixel(led_index, self.led_strip.red())
        time.sleep(duration)

        # Restore previous state
        if current_state:
            # LED was on, restore green (active LED)
            if led_index == self.current_led_index:
                self.led_strip.set_pixel(led_index, self.led_strip.green())
            else:
                # If it was on for some other reason, just leave red off
                self.led_strip.turn_off_pixel(led_index)
        else:
            self.led_strip.turn_off_pixel(led_index)
            

    def _check_start_reset(self):
        s1, s2 = self.start_combo
        now = time.time()

        if self.sensor_pressed[s1] and self.sensor_pressed[s2]:
            if self.start_press_time is None:
                self.start_press_time = now
            elif now - self.start_press_time >= self.start_hold_time:
                self._reset_game()
                self.start_press_time = None
        else:
            self.start_press_time = None

    def _reset_game(self):
        print("\n[GAME] RESET triggered!")
        self.running = False

        self.total_reaction_time = 0.0
        self.total_wrong_touches = 0
        self.reaction_time = None

        self.led_pressed_event.set()  # unblock game loop if waiting

        self.led_strip.turn_all(self.led_strip.blue())
        time.sleep(0.2)

        self.led_strip.turn_all_off()

    #not sure if is ideal but it keeps checking every 50ms if two buttons are pressed
    #pressed states are stored in sensor_pressed[]
    # eg. 
    # use touches 1
    # on_touch(1,True)
    # sensor_pressed[1]=True
    # _check_start_reset() #do nothing. no reset.
    # start_press_time = None

    # user touches 0
    # on_touch(0, True)
    # sensor_pressed[0] = True
    # _check_start_reset()
    # start_press_time = now and 

    #user presses both for 1 sec
    #combo_thread checks every 50ms
    #both pressed ?
    #if now - start_press_time >= 1
    #  reset_game
    def _combo_monitor(self):
        while True:
            self._check_start_reset()
            time.sleep(0.05)  # 50 ms resolution

def testCallback():
    #PA
    sensor_pins = [2, 3, 4, 5]

    touch_led = MCP23017TouchLED(
        sensor_pins=sensor_pins,
        led_pins=[1]
    )

    led_strip = LedStrip()
    strip_led_pins = [15, 19, 23, 27]
    tries = 3

    consumer = TouchConsumer2(led_strip, strip_led_pins, tries=10)
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
