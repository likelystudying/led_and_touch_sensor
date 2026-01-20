import time

def stopwatch():
    print("Press Ctrl+C to stop the stopwatch.")
    start_time = time.time()
    
    try:
        while True:
            elapsed_time = time.time() - start_time
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            # \r returns the cursor to the start of the line
            print(f"\r{hours:02}:{minutes:02}:{seconds:02}", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopwatch stopped.")

if __name__ == "__main__":
    stopwatch()
