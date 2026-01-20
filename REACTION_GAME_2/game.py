from machine import Pin, I2C
import uasyncio as asyncio
import random
import json
from ssd1306 import SSD1306_I2C

# countdown 60 sec
# user needs to answer 
# questiosn are read from questions.json
# 
# ---------------- OLED ----------------
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

def display(question, numbers, time_left, msg=""):
    oled.fill(0)
    oled.text("Q: " + question, 0, 0)
    oled.text("Nums:", 0, 16)
    oled.text(f"{numbers[0]}-{numbers[1]}-{numbers[2]}-{numbers[3]}", 0, 28)
    oled.text(f"Time: {time_left}s", 0, 48)
    if msg:
        oled.text(msg, 0, 56)
    oled.show()

# --------------- MCP23017 ---------------
ADDR = 0x27
GPIOA = 0x12
GPPUA = 0x0C
sensor_pins = [2, 3, 4, 5]

mask = 0
for p in sensor_pins:
    mask |= (1 << p)
i2c.writeto_mem(ADDR, GPPUA, bytes([mask]))

prev_state = [0]*4

# --------------- Load Questions ---------------
with open("questions.json") as f:
    QUESTIONS = json.load(f)

# --------------- Game State ---------------
current_question = None
current_answer = None
sensor_values = []
time_left = 60
score = 0
waiting_for_answer = True

def pick_new_question():
    global current_question, current_answer, sensor_values, waiting_for_answer
    q = random.choice(QUESTIONS)
    current_question = q["question"]
    current_answer = q["answer"]
    sensor_values = q["sensors"]
    waiting_for_answer = True
    display(current_question, sensor_values, time_left)

# --------------- Sensor Polling ---------------
async def poll_sensors():
    global prev_state, time_left, score, waiting_for_answer

    while time_left > 0:
        val = i2c.readfrom_mem(ADDR, GPIOA, 1)[0]

        for i, pin in enumerate(sensor_pins):
            current = (val >> pin) & 1

            # Rising edge = touch
            if current == 1 and prev_state[i] == 0 and waiting_for_answer:
                pressed_value = sensor_values[i]

                if pressed_value == current_answer:
                    score += 1
                    waiting_for_answer = False
                    display(current_question, sensor_values, time_left, "Correct!")
                    await asyncio.sleep(1)
                    pick_new_question()
                else:
                    time_left += 3
                    waiting_for_answer = False
                    display(current_question, sensor_values, time_left, "Wrong! +3s")
                    await asyncio.sleep(1)
                    pick_new_question()

            prev_state[i] = current

        await asyncio.sleep(0.05)

# --------------- Countdown ---------------
async def countdown():
    global time_left
    while time_left > 0:
        display(current_question, sensor_values, time_left)
        await asyncio.sleep(1)
        time_left -= 1

    oled.fill(0)
    oled.text("GAME OVER", 20, 20)
    oled.text(f"Score: {score}", 20, 40)
    oled.show()

# --------------- Main ---------------
async def main():
    pick_new_question()
    await asyncio.gather(
        poll_sensors(),
        countdown()
    )

asyncio.run(main())
