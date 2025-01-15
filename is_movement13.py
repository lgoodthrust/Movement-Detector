import mss
import numpy as np
import pyautogui
import time
import keyboard
import threading
import cv2
from numba import njit
import pyautogui._pyautogui_win

# records
#35.14 ms
#33.81 ms
#21.19 ms

# Screen capture region (adjust for smaller area if possible)
screen_region = {'top': 270, 'left': 480, 'width': 960, 'height': 540}

# Sensitivity settings
sensitivity_size = 30

# Movement and toggles
max_time = 0.075  # Reduced buffer time between movements
detect_movement = False
enable_clicking = False

# Dead zone settings
dead_zone_size = 40  # 40x40 pixels around the cursor

# Initialize pyautogui settings
pyautogui.FAILSAFE = False
pyautogui.FAILSAFE_POINTS = [[1875, 0]]
pyautogui.MINIMUM_DURATION = 0.01
pyautogui.MINIMUM_SLEEP = 0.01
pyautogui.PAUSE = 0.01
pyautogui.DARWIN_CATCH_UP_TIME = 0.01

# Numba-optimized centroid calculation
@njit
def process_frame_delta(prev_gray, current_gray, sensitivity_size):
    delta = np.abs(prev_gray - current_gray)
    thresh = delta > sensitivity_size
    sum_x, sum_y, count = 0, 0, 0

    for y in range(thresh.shape[0]):
        for x in range(thresh.shape[1]):
            if thresh[y, x]:
                sum_x += x
                sum_y += y
                count += 1

    if count > 0:
        return sum_x // count, sum_y // count  # Centroid
    return None

# Frame processing thread
def process_frames():
    global prev_frame, last_event_time

    prev_frame = None
    last_event_time = time.time()
    sct = mss.mss()

    while True:
        if detect_movement:
            frame = np.array(sct.grab(screen_region))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

            if prev_frame is None:
                prev_frame = gray
                continue

            # Calculate the centroid of movement
            centroid = process_frame_delta(prev_frame, gray, sensitivity_size)
            current_time = time.time()

            if centroid:
                cx, cy = centroid
                screen_cx = screen_region['left'] + cx
                screen_cy = screen_region['top'] + cy

                # Get the current cursor position
                cursor_x, cursor_y = pyautogui.position()

                # Check if the centroid is outside the dead zone
                if not (
                    cursor_x - dead_zone_size // 2 <= screen_cx <= cursor_x + dead_zone_size // 2 and
                    cursor_y - dead_zone_size // 2 <= screen_cy <= cursor_y + dead_zone_size // 2
                ):
                    # Process movement if buffer time has passed
                    if current_time - last_event_time >= max_time:
                        pyautogui.moveTo(screen_cx, screen_cy)

                        if enable_clicking:
                            pyautogui.click()

                        last_event_time = current_time

            prev_frame = gray  # Update the previous frame

        time.sleep(0.001)

# Toggle movement detection
def toggle_movement_detection():
    global detect_movement
    detect_movement = not detect_movement
    print(f"Movement detection {'enabled' if detect_movement else 'disabled'}")

# Toggle clicking
def toggle_clicking():
    global enable_clicking
    enable_clicking = not enable_clicking
    print(f"Clicking function {'enabled' if enable_clicking else 'disabled'}")

# Start the frame processing thread
frame_thread = threading.Thread(target=process_frames)
frame_thread.daemon = True
frame_thread.start()

# Bind keyboard shortcuts
keyboard.add_hotkey('insert', toggle_movement_detection)
keyboard.add_hotkey('delete', toggle_clicking)

keyboard.wait('esc')
