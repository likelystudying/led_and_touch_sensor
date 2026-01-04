# | MCP23017 | Raspberry Pi    |
# | -------- | --------------- |
# | INTA     | GPIO17 (pin 11) |
# | INTB     | GPIO27 (pin 13) |
# | VDD      | 3.3V            |
# | VSS      | GND             |
# | SDA      | GPIO2           |
# | SCL      | GPIO3           |
# | RESET    | 3.3V            |


# | Register            | Addr        |
# | ------------------- | ----------- |
# | IODIRA / IODIRB     | 0x00 / 0x01 |
# | GPINTENA / GPINTENB | 0x04 / 0x05 |
# | DEFVALA / DEFVALB   | 0x06 / 0x07 |
# | INTCONA / INTCONB   | 0x08 / 0x09 |
# | IOCON               | 0x0A        |
# | INTF                | 0x0E / 0x0F |
# | INTCAP              | 0x10 / 0x11 |
# | GPIO                | 0x12 / 0x13 |

# pi@raspberrypi:~/led $ i2cdetect -y 1
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:                         -- -- -- -- -- -- -- -- 
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 20: -- -- -- -- -- -- -- 27 -- -- -- -- -- -- -- -- 
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
# 70: -- -- -- -- -- -- -- -- 


# pi@raspberrypi:~/led $ python3 mcp23017.py 
# Touch sensor on PA2 ready
# 0 for 39 18
# not touched
# 0 for 39 18
# not touched
# 0 for 39 18
# not touched
# 4 for 39 18
# TOUCHED
# 6 for 39 18
# TOUCHED
# 6 for 39 18


# sens   mcp  SENSOR is input
# ----------
# SIG -> PA2
# VCC -> VCC
# GND -> GND
 
# led (470ohm) LED is output
# ----------
# LED -> PA1 
# GND -> GND

#for pythhon to access linux /dev/i2c-1
from smbus2 import SMBus
import time

#led
OLATA  = 0x14

#sensor
ADDR   = 0x27 #i2c address 
IODIRA = 0x00 #address IODIRA register. 1=input 0=output
GPPUA  = 0x0C #address of internal pull up register for portA 1=enable pull up 0=disable
GPIOA  = 0x12 #address of GPIOA register for PA pins
IOCON  = 0x0A #address of config register to disable sequential addressing

PA1_MASK = 0b11111101  # PA1 output, others input (PA7,PA6...PA)
PA2_MASK = 0b00000100  # binary mask for PA2 76543210 so 0b100 is "2" PA2 is selected

bus = SMBus(1)

# Stable mode
bus.write_byte_data(ADDR, IOCON, 0x20)

# All Port A inputs
# bus.write_byte_data(ADDR, IODIRA, 0xFF)
bus.write_byte_data(ADDR, IODIRA, PA1_MASK)

# Enable pull-up on PA2 to avoid floating
bus.write_byte_data(ADDR, GPPUA, PA2_MASK)

print("Touch sensor on PA2 ready")

while True:
    val = bus.read_byte_data(ADDR, GPIOA)
    print(f"{val} for {ADDR} {GPIOA}")
    bit = (val & PA2_MASK) >> 2

    # Most touch sensors: HIGH when touched
    if bit == 1:
        print("TOUCHED")
        bus.write_byte_data(ADDR, OLATA, 0b00000010)  # PA1 ON
    else:
        print("not touched")
        bus.write_byte_data(ADDR, OLATA, 0b00000000)  # OFF

    time.sleep(0.1)
