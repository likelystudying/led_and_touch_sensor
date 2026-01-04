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

#PA1 → 330Ω → LED → GND


from smbus2 import SMBus
import time

ADDR   = 0x27 
IODIRA = 0x00
OLATA  = 0x14
IOCON  = 0x0A

bus = SMBus(1)

bus.write_byte_data(ADDR, IOCON, 0x20)

# PA1 output, others input
bus.write_byte_data(ADDR, IODIRA, 0b11111101)

while True:
    bus.write_byte_data(ADDR, OLATA, 0b00000010)  # PA1 ON
    print("on")
    time.sleep(1)
    bus.write_byte_data(ADDR, OLATA, 0b00000000)  # OFF
    print("off")
    time.sleep(1)
