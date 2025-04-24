from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, Key, KeyCode
import time
import threading

# Configuration
TOGGLE_KEY = Key.f6  # Backtick key (`) - you can change this

mouse = Controller()
running = True
clicking = False
click_count = 0
threads_count = 16
click_lock = threading.Lock()


def on_press(key):
    global clicking, click_count
    if key == TOGGLE_KEY:
        clicking = not clicking
        print(f"Clicking {'ON' if clicking else 'OFF'} - Total clicks: {click_count}")
        if clicking:
            # Reset the click counter when starting a new session
            click_count = 0


def clicking_thread():
    global click_count
    local_count = 0

    while running:
        if clicking:
            # Batch multiple clicks together for better performance
            for _ in range(100):  # Smaller batch for more responsive toggling
                if not running or not clicking:
                    break
                mouse.click(Button.left)
                local_count += 1

            # Update the global counter occasionally (reduces thread contention)
            with click_lock:
                click_count += local_count
                local_count = 0
        else:
            # Don't consume CPU when not clicking
            time.sleep(0.1)


def stats_thread():
    start_time = None
    last_count = 0

    while running:
        time.sleep(1)  # Update stats every second

        if clicking:
            if start_time is None:
                start_time = time.time()
                last_count = click_count
            else:
                elapsed = time.time() - start_time
                clicks_since_last = click_count - last_count
                last_count = click_count
                rate = clicks_since_last  # Clicks per second
                print(f"Rate: {rate:.2f} clicks/second, Total: {click_count}")
        else:
            start_time = None  # Reset timer when clicking is off


print("\n=== Auto-Clicker with Toggle ===")
print(f"Press '`' (backtick) key to toggle clicking ON/OFF")
print("Press Ctrl+C in the terminal to exit the program")
print("Ready! Position your mouse where you want to click.")

# Start keyboard listener
keyboard_listener = Listener(on_press=on_press)
keyboard_listener.start()

# Start clicking threads
threads = []
for _ in range(threads_count):
    t = threading.Thread(target=clicking_thread, daemon=True)
    threads.append(t)
    t.start()

# Start stats thread
stats_t = threading.Thread(target=stats_thread, daemon=True)
stats_t.start()

try:
    # Keep the main thread alive
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nExiting...")
    running = False
    keyboard_listener.stop()

    # Final statistics
    if click_count > 0:
        print(f"Performed {click_count} total clicks")

# Wait for threads to finish
for t in threads:
    t.join(timeout=0.5)