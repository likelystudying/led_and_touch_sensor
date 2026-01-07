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


#todo isolate LED from this class because it's only used for debugging atm


class MCP23017TouchLED:
    def __init__(self, i2c_addr=0x27, bus_id=1, sensor_pins=None, led_pins=None):

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

        self._lock = threading.Lock()

        # Initialize I2C
        self.bus = SMBus(bus_id)
        self._configure_device()

        # add callbacks
        self._touch_callback = None
        self._prev_touched = [False] * len(sensor_pins)

        # Threads
        self.sensor_thread = threading.Thread(target=self._touch_sensor_thread, daemon=True)
        self.led_thread = threading.Thread(target=self._led_thread, daemon=True)
        self.control_thread = threading.Thread(target=self._control_thread, daemon=True)

        print("Touch sensor on PA2 ready")


    def _configure_device(self):
        """Initial configuration of MCP23017."""
        with self._lock:
            # disable sequential addressing
            self.bus.write_byte_data(self.ADDR, self.IOCON, 0x20)       

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
        """Continuously read touch sensor state and emit events."""
        while True:
            callbacks_to_call = []

            with self._lock:
                val = self.bus.read_byte_data(self.ADDR, self.GPIOA)

                for i, mask in enumerate(self.sensor_masks):
                    current = (val & mask) != 0
                    previous = self._prev_touched[i]

                    # Rising edge: not touched -> touched
                    if current and not previous:
                        callbacks_to_call.append((i, True))

                    # Falling edge: touched -> not touched
                    elif not current and previous:
                        callbacks_to_call.append((i, False))

                    self.touched[i] = current
                    self._prev_touched[i] = current

            # Call callbacks OUTSIDE the lock
            if self._touch_callback:
                for sensor_index, pressed in callbacks_to_call:
                    self._touch_callback(sensor_index, pressed)

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


    def set_touch_callback(self, callback):
        self._touch_callback = callback


class TouchConsumer:
    def on_touch(self, sensor_index, pressed):
        if pressed:
            print(f"[CALLBACK] Sensor {sensor_index} PRESSED")
        else:
            print(f"[CALLBACK] Sensor {sensor_index} RELEASED")



# def testCallback():
#     #PA
#     sensor_pins = [2, 3, 4, 5]
#     led_pins = [1]

#     touch_led = MCP23017TouchLED(
#         sensor_pins=sensor_pins,
#         led_pins=led_pins
#     )

#     consumer = TouchConsumer()
#     touch_led.set_touch_callback(consumer.on_touch)

#     touch_led.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Exiting...")
#         touch_led.cleanup()


# if __name__ == "__main__":
#     testCallback()