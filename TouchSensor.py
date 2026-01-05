from smbus2 import SMBus
import threading
import time

# MCP23017 registers
ADDR   = 0x27
IODIRA = 0x00
GPPUA  = 0x0C
GPIOA  = 0x12
OLATA  = 0x14
IOCON  = 0x0A

PA1_MASK = 0b11111101  # PA1 output, others input
PA2_MASK = 0b00000100  # PA2 input

# Shared state
touched = False
i2c_lock = threading.Lock()  # Make all I2C access thread-safe

# Initialize I2C bus
bus = SMBus(1)

# Configure MCP23017
with i2c_lock:
    bus.write_byte_data(ADDR, IOCON, 0x20)        # disable sequential addressing
    bus.write_byte_data(ADDR, IODIRA, PA1_MASK)   # PA1 output
    bus.write_byte_data(ADDR, GPPUA, PA2_MASK)    # enable pull-up on PA2
    bus.write_byte_data(ADDR, OLATA, 0x00)        # make sure LED is off

print("Touch sensor on PA2 ready")

# Touch sensor thread
def touch_sensor_thread():
    global touched
    while True:
        with i2c_lock:
            val = bus.read_byte_data(ADDR, GPIOA)
        bit = (val & PA2_MASK) >> 2
        touched = (bit == 1)
        # Debug print
        print("TOUCHED" if touched else "not touched")
        time.sleep(0.05)  # 50ms polling

# LED control thread
def led_thread():
    while True:
        with i2c_lock:
            if touched:
                bus.write_byte_data(ADDR, OLATA, 0b00000010)  # PA1 ON
            else:
                bus.write_byte_data(ADDR, OLATA, 0b00000000)  # PA1 OFF
        time.sleep(0.05)

# Start threads
sensor_thread = threading.Thread(target=touch_sensor_thread, daemon=True)
led_ctrl_thread = threading.Thread(target=led_thread, daemon=True)

sensor_thread.start()
led_ctrl_thread.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    with i2c_lock:
        bus.write_byte_data(ADDR, OLATA, 0x00)  # Turn off LED
    bus.close()
