from machine import Pin, I2C
import uasyncio as asyncio
import ujson
from ssd1306 import SSD1306_I2C


# countdown 60 sec
# user needs to answer 
# questiosn are read from questions.json
# 


# ----------------------------
# OLED Setup
# ----------------------------
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

def display_game(question, numbers, time_left, message=""):
    oled.fill(0)
    oled.text("Q:", 0, 0)
    oled.text(question, 20, 0)
    oled.text(f"{numbers[0]}-{numbers[1]}-{numbers[2]}-{numbers[3]}", 0, 24)
    oled.text(f"Time: {time_left}s", 0, 48)
    if message:
        oled.text(message, 0, 56)
    oled.show()

# ----------------------------
# MCP23017 Setup
# ----------------------------
ADDR = 0x27
GPIOA = 0x12
GPPUA = 0x0C
sensor_pins = [2, 3, 4, 5]  # PA2–PA5

# Enable pull-ups
mask = 0
for pin in sensor_pins:
    mask |= (1 << pin)
i2c.writeto_mem(ADDR, GPPUA, bytes([mask]))

prev_state = [0] * len(sensor_pins)

# ----------------------------
# Load questions from JSON
# ----------------------------
def load_questions(filename="questions.json"):
    with open(filename, "r") as f:
        return ujson.load(f)

questions = load_questions()
current_index = 0
current_question = ""
current_answer = 0
sensor_values = [0, 0, 0, 0]

# ----------------------------
# Game variables
# ----------------------------
time_left = 60
score = 0
message = ""

# ----------------------------
# Load next question
# ----------------------------
def next_question():
    global current_index, current_question, current_answer, sensor_values
    q = questions[current_index]
    current_question = q["question"]
    current_answer = q["answer"]
    sensor_values = q["sensors"]
    current_index = (current_index + 1) % len(questions)

# ----------------------------
# Poll sensors
# ----------------------------
async def poll_sensors():
    global prev_state, time_left, score, message
    while time_left > 0:
        val = i2c.readfrom_mem(ADDR, GPIOA, 1)[0]
        for i, pin in enumerate(sensor_pins):
            current = (val >> pin) & 1
            if current == 1 and prev_state[i] == 0:
                pressed_value = sensor_values[i]
                if pressed_value == current_answer:
                    score += 1
                    message = "Correct!"
                else:
                    time_left += 3
                    message = "Wrong! +3s"

                display_game(current_question, sensor_values, time_left, message)
                await asyncio.sleep(1)
                message = ""
                next_question()
                display_game(current_question, sensor_values, time_left)

            prev_state[i] = current
        await asyncio.sleep(0.05)

# ----------------------------
# Countdown timer
# ----------------------------
async def countdown():
    global time_left
    while time_left > 0:
        display_game(current_question, sensor_values, time_left, message)
        await asyncio.sleep(1)
        time_left -= 1
    display_game("Game Over!", sensor_values, 0, f"Score: {score}")

# ----------------------------
# Main game loop
# ----------------------------
async def main():
    next_question()
    display_game(current_question, sensor_values, time_left)
    await asyncio.gather(
        poll_sensors(),
        countdown()
    )

# ----------------------------
# Run game
# ----------------------------
asyncio.run(main())
