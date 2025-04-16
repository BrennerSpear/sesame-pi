#!/usr/bin/env python3
"""
Simple event-based triple click test using signal.pause().
Connect a button between GPIO pin 19 and ground (GND).
"""

import threading
from gpiozero import Button
from signal import pause

# Button configuration
BUTTON_PIN = 19  # GPIO pin for the button
TRIPLE_CLICK_TIMEOUT = 0.5  # seconds between clicks to count as triple click

class TripleClickDetector:
    def __init__(self, callback, timeout=TRIPLE_CLICK_TIMEOUT):
        self.callback = callback
        self.timeout = timeout
        self.click_count = 0
        self.timer = None
        self.lock = threading.Lock()
    
    def on_click(self):
        with self.lock:
            # Cancel any existing timer
            if self.timer:
                self.timer.cancel()
            
            # Increment click count
            self.click_count += 1
            print(f"Click detected! Count: {self.click_count}")
            
            # If we've reached 3 clicks, execute callback
            if self.click_count == 3:
                self.callback()
                self.click_count = 0
            else:
                # Start timer to reset click count after timeout
                self.timer = threading.Timer(self.timeout, self.reset_count)
                self.timer.daemon = True
                self.timer.start()
    
    def reset_count(self):
        with self.lock:
            print(f"Timeout reached. Resetting click count from {self.click_count} to 0")
            self.click_count = 0
            self.timer = None

def handle_triple_click():
    """Handle triple click event"""
    print("TRIPLE CLICK DETECTED!")
    print("In a real scenario, this would stop the Sesame voice interaction")

# Initialize triple click detector
triple_click_detector = TripleClickDetector(handle_triple_click)

# Initialize button
button = Button(BUTTON_PIN, bounce_time=0.1, pull_up=True)

# Set up button handlers
button.when_pressed = lambda: triple_click_detector.on_click()

print(f"Starting triple click test on GPIO {BUTTON_PIN}")
print(f"Click the button 3 times within {TRIPLE_CLICK_TIMEOUT} seconds to trigger the triple click event")
print("Press Ctrl+C to exit")

# Keep the script running using signal.pause() instead of a while loop
try:
    pause()
except KeyboardInterrupt:
    print("Triple click test stopped by user")
finally:
    print("Triple click test complete")
