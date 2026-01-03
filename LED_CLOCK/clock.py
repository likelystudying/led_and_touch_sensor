import threading
import time

second = 0
minute = 0
hour = 0
running = True

# this is a bad design for ESP32 or rasbperry pi zero 
# because
# -  with sleep() CPU wakes every delay. power drain is high.
# - counting loop high power consumption.
# - if not sync then out of sync

# btter way
# - esp32 - use built in RTC
# - rtc + deep sleep low pwr consumption



def test2():
    for _ in range(10):
        now = time.localtime()
        hour, minute, second = now.tm_hour, now.tm_min, now.tm_sec
        print(f" alala {hour:02}:{minute:02}:{second:02}")
        time.sleep(1)


def clock(delay=1):

    global second, minute, hour

    while(running):
        time.sleep(delay)
        second += 1

        if second >= 60:
            second = 0
            minute += 1
        
        if minute >= 60:
            minute = 0
            hour += 1

        if hour >= 12:
            hour =0



def test1():
    global running
    threads = []
    t = threading.Thread(target=clock, kwargs={"delay":1}, daemon= True)

    t.start()

    for i in range(10):
        print(f"{hour}:{minute}:{second}")
        time.sleep(1)

    t.join()

def run_test():
    print("test")
    test1()

def run_test2():
    print("test23")
    test2()


run_test2()