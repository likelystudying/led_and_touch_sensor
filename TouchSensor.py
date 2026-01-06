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
# SIG -> PA2,3,4 and etc
# VCC -> VCC
# GND -> GND
 
# led output
# led (470ohm) LED
# ----------
# LED -> PA1 
# GND -> GND


class MCP23017TouchLED:
    def __init__(self, i2c_addr=0x27, bus_id=1, sensor_pins=None, led_pins=None):

        if sensor_pins is None:
            sensor_pins = [2,3]
        if led_pins is None:
            led_pins = [1]

        # MCP23017 registers
        self.ADDR   = i2c_addr
        self.IODIRA = 0x00
        self.GPPUA  = 0x0C
        self.GPIOA  = 0x12
        self.OLATA  = 0x14
        self.IOCON  = 0x0A


        self.sensor_pins = sensor_pins
        self.led_pins = led_pins

        self.sensor_masks = []
        for pin in sensor_pins:
            self.sensor_masks.append(1 << pin)

        self.led_masks = []
        for pin in led_pins:
            self.led_masks.append(1 << pin)

        self.touched = []
        for _ in range(len(sensor_pins)):
            self.touched.append(False)


        self.led_on = []
        for _ in range(len(led_pins)):
            self.led_on.append(False)


        # Pin masks
        # self.PA1_MASK = 0b11111101  # PA1 output, others input
        # self.PA2_MASK = 0b00000100  # PA2 input ( sensor 1)
        # self.PA3_MASK = 0b00001000  # PA3 input (sensor 2)

        # Shared state
        # self.touched = [False, False]
        # self.led_on = False

        self._lock = threading.Lock()

        # Initialize I2C
        self.bus = SMBus(bus_id)
        self._configure_device()

        # Threads
        self.sensor_thread = threading.Thread(target=self._touch_sensor_thread, daemon=True)
        self.led_thread = threading.Thread(target=self._led_thread, daemon=True)
        self.control_thread = threading.Thread(target=self._control_thread, daemon=True)

        print("Touch sensor on PA2 ready")

    def _configure_device(self):
        """Initial configuration of MCP23017."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.IOCON, 0x20)       # disable sequential addressing
            #self.bus.write_byte_data(self.ADDR, self.IODIRA, self.PA1_MASK)  # PA1 output
            #self.bus.write_byte_data(self.ADDR, self.GPPUA, self.PA2_MASK)   # enable pull-up on PA2
            #self.bus.write_byte_data(self.ADDR, self.GPPUA, self.PA3_MASK)   # enable pull-up on PA3
            #self.bus.write_byte_data(self.ADDR, self.GPPUA, self.PA3_MASK | self.PA2_MASK)   # enable pull-up on PA3

            #set all LED pins to output (0)
            iodir = 0xFF
            for pin in self.led_pins:
                iodir &= ~(1 << pin)
            self.bus.write_byte_data(self.ADDR, self.IODIRA, iodir)
            
            #enable pull up for touch sensors
            all_mask = 0x00
            for mask in self.sensor_masks:
                all_mask = all_mask | mask
            self.bus.write_byte_data(self.ADDR, self.GPPUA, all_mask)

            #turn off
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)

    def start(self):
        """Start all threads."""
        self.sensor_thread.start()
        self.led_thread.start()
        self.control_thread.start()

    def _touch_sensor_thread(self):
        """Continuously read touch sensor state."""
        while True:
            with self._lock:
                val = self.bus.read_byte_data(self.ADDR, self.GPIOA)
                # self.touched[0] = ((val & self.PA2_MASK) >> 2) == 1
                # self.touched[1] = ((val & self.PA3_MASK) >> 3) == 1
                for i, mask in enumerate(self.sensor_masks):
                    self.touched[i] = (val & mask) != 0
                
                for i, touched in enumerate(self.touched):
                    if touched:
                        print(f"touched {i}")
                        
            time.sleep(0.05)

    def _led_thread(self):
        """Simplified LED thread: just sets LED according to led_on state."""
        while True:
            with self._lock:
                olata_val = 0x00
                for i, led_state in enumerate(self.led_on):
                    if led_state:
                        olata_val |= self.led_masks[i]
                self.bus.write_byte_data(self.ADDR, self.OLATA, olata_val)
            time.sleep(0.05)

            # with self._lock:
            #     if self.led_on:
            #         self.bus.write_byte_data(self.ADDR, self.OLATA, 0b00000010)
            #     else:
            #         self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)
            #         time.sleep(0.5)
            # time.sleep(0.05)

    def _control_thread(self):
        while True:
            with self._lock:
                if not self.led_on[0]:
                    self.led_on[0] = True
                    self.start_time = time.time()
                    #print("LED ON")

                elif any(self.touched):
                    elapsed = time.time() - self.start_time
                    self.led_on[0] = False
                    print(f"LED OFF after {int(elapsed * 1000)} ms")
                    self.start_time = None
            time.sleep(0.05)


    def cleanup(self):
        """Turn off LED and close I2C bus."""
        with self._lock:
            self.bus.write_byte_data(self.ADDR, self.OLATA, 0x00)
            self.bus.close()


if __name__ == "__main__":

    #PA
    sensor_pins = [2,3,4]
    led_pins = [1]

    touch_led = MCP23017TouchLED(
        sensor_pins=sensor_pins,
        led_pins=led_pins
    )
    touch_led.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        touch_led.cleanup()