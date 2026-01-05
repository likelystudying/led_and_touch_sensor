from smbus2 import SMBus
import threading
import time

class MCP23017TouchLED:
    def __init__(self, i2c_addr=0x27, bus_id=1):
        # MCP23017 registers
        self.ADDR   = i2c_addr
        self.IODIRA = 0x00
        self.GPPUA  = 0x0C
        self.GPIOA  = 0x12
        self.OLATA  = 0x14
        self.IOCON  = 0x0A

        # Pin masks
        self.PA1_MASK = 0b11111101  # PA1 output, others input
        self.PA2_MASK = 0b00000100  # PA2 input (touch sensor)

        # Shared state
        self.touched = False
        self._lock = threading.Lock()

        # Initialize I2C
        self.bus = SMBus(bus_id)
        self._configure_device()

        # Threads
        self.sensor_thread = threading.Thread(target=self._touch_sensor_thread, daemon=True)
        self.led_thread = threading.Thread(target=self._led_control_thread, daemon=True)

        print("Touch sensor on PA2 ready")

    def _configure_device(self):
        """Initial configuration of MCP23017."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.IOCON, 0x20)       # disable sequential addressing
            self.bus.write_byte_data(self.ADDR, self.IODIRA, self.PA1_MASK)  # PA1 output
            self.bus.write_byte_data(self.ADDR, self.GPPUA, self.PA2_MASK)   # enable pull-up on PA2
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)       # LED off

    def start(self):
        """Start sensor and LED threads."""
        self.sensor_thread.start()
        self.led_thread.start()

    def _touch_sensor_thread(self):
        """Thread to read touch sensor state continuously."""
        while True:
            with self._lock:
                val = self.bus.read_byte_data(self.ADDR, self.GPIOA)
            self.touched = ((val & self.PA2_MASK) >> 2) == 1
            print("TOUCHED" if self.touched else "not touched")
            time.sleep(0.05)

    def _led_control_thread(self):
        """Thread to control LED based on touch sensor state."""
        while True:
            with self._lock:
                if self.touched:
                    self.bus.write_byte_data(self.ADDR, self.OLATA, 0b00000010)  # LED ON
                else:
                    self.bus.write_byte_data(self.ADDR, self.OLATA, 0b00000000)  # LED OFF
            time.sleep(0.05)

    def cleanup(self):
        """Turn off LED and close I2C bus."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)
            self.bus.close()


if __name__ == "__main__":
    touch_led = MCP23017TouchLED()
    touch_led.start()

    try:
        while True:
            time.sleep(1)  # Keep main thread alive
    except KeyboardInterrupt:
        print("Exiting...")
        touch_led.cleanup()
