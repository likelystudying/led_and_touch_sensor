from smbus2 import SMBus
import threading
import time


#initial setup

##raspberry pi
# | MCP23017 | Raspberry Pi    |
# | -------- | --------------- |
# | INTA     | GPIO17 (pin 11) |
# | INTB     | GPIO27 (pin 13) |
# | VDD      | 3.3V            |
# | VSS      | GND             |
# | SDA      | GPIO2           |
# | SCL      | GPIO3           |
# | RESET    | 3.3V            |

##MCP23017
# touch sensor input
# sens   mcp  SENSOR
# ----------
# SIG -> PA2
# VCC -> VCC
# GND -> GND
 
# led output
# led (470ohm) LED
# ----------
# LED -> PA1 
# GND -> GND

from smbus2 import SMBus
import threading
import time


class MCP23017MultiTouchLED:
    def __init__(self, i2c_addr=0x27, bus_id=1, sensor_pins=None, led_pins=None):
        """
        sensor_pins: list of PA pin numbers for touch sensors (e.g., [2, 3])
        led_pins: list of PA pin numbers for LEDs (e.g., [1])
        """
        if sensor_pins is None:
            sensor_pins = [2, 3]  # default sensors
        if led_pins is None:
            led_pins = [1]  # default LED

        # MCP23017 registers
        self.ADDR   = i2c_addr
        self.IODIRA = 0x00
        self.GPPUA  = 0x0C
        self.GPIOA  = 0x12
        self.OLATA  = 0x14
        self.IOCON  = 0x0A

        # Store pin info
        self.sensor_pins = sensor_pins
        self.led_pins = led_pins

        # Compute masks
        self.sensor_masks = [1 << pin for pin in sensor_pins]
        self.led_masks = [1 << pin for pin in led_pins]

        # Shared state
        self.touched = [False] * len(sensor_pins)
        self.led_on = [False] * len(led_pins)
        self._lock = threading.Lock()

        # Initialize I2C
        self.bus = SMBus(bus_id)
        self._configure_device()

        # Threads
        self.sensor_thread = threading.Thread(target=self._touch_sensor_thread, daemon=True)
        self.led_thread = threading.Thread(target=self._led_thread, daemon=True)
        self.control_thread = threading.Thread(target=self._control_thread, daemon=True)

        print(f"Touch sensors on PA{sensor_pins} ready. LEDs on PA{led_pins} ready.")

    def _configure_device(self):
        """Initial configuration of MCP23017."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.IOCON, 0x20)  # disable sequential addressing

            # All pins default to input (1)
            iodir = 0xFF
            # Set LED pins to output (0)
            for pin in self.led_pins:
                iodir &= ~(1 << pin)
            self.bus.write_byte_data(self.ADDR, self.IODIRA, iodir)

            # Enable pull-ups on sensor pins
            gppu = 0x00
            for mask in self.sensor_masks:
                gppu |= mask
            self.bus.write_byte_data(self.ADDR, self.GPPUA, gppu)

            # Turn all LEDs off
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)

    def start(self):
        """Start all threads."""
        self.sensor_thread.start()
        self.led_thread.start()
        self.control_thread.start()

    def _touch_sensor_thread(self):
        """Continuously read all touch sensor states."""
        while True:
            with self._lock:
                val = self.bus.read_byte_data(self.ADDR, self.GPIOA)
                for i, mask in enumerate(self.sensor_masks):
                    self.touched[i] = (val & mask) != 0
            # Debug prints
            for i, t in enumerate(self.touched):
                if t:
                    print(f"PA{self.sensor_pins[i]} TOUCHED")
            time.sleep(0.05)

    def _led_thread(self):
        """Update all LEDs according to led_on states."""
        while True:
            with self._lock:
                olata_val = 0x00
                for i, led_state in enumerate(self.led_on):
                    if led_state:
                        olata_val |= self.led_masks[i]
                self.bus.write_byte_data(self.ADDR, self.OLATA, olata_val)
            time.sleep(0.05)

    def _control_thread(self):
        """
        Control logic:
        - Turn LEDs on
        - If any sensor is touched, corresponding LED turns off
        - Show elapsed time in milliseconds for each LED
        """
        start_times = [None] * len(self.led_on)

        while True:
            with self._lock:
                for i, led_state in enumerate(self.led_on):
                    if not led_state:
                        # Turn LED on
                        self.led_on[i] = True
                        start_times[i] = time.time()
                        print(f"LED on PA{self.led_pins[i]} turned ON")
                    elif led_state:
                        elapsed = time.time() - start_times[i]
                        # If any sensor is touched, turn off corresponding LED
                        if i < len(self.touched) and self.touched[i]:
                            self.led_on[i] = False
                            print(f"LED on PA{self.led_pins[i]} turned OFF due to touch after {int(elapsed*1000)} ms")
                            start_times[i] = None

            time.sleep(0.05)

    def cleanup(self):
        """Turn off all LEDs and close I2C bus."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)
            self.bus.close()


if __name__ == "__main__":
    # Example: 2 sensors on PA2 & PA3, 2 LEDs on PA1 & PA4
    touch_led = MCP23017MultiTouchLED(sensor_pins=[2, 3], led_pins=[1, 4])
    touch_led.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        touch_led.cleanup()
