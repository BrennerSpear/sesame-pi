#!/usr/bin/env python3
"""
Script to test the triple click detection functionality.
Connect a button between GPIO pin 19 and ground (GND).
"""

import time
import logging
from gpiozero import Button
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

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
            logging.info(f"Click detected! Count: {self.click_count}")
            
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
            logging.info(f"Timeout reached. Resetting click count from {self.click_count} to 0")
            self.click_count = 0
            self.timer = None

def handle_triple_click():
    """Handle triple click event"""
    logging.info("TRIPLE CLICK DETECTED!")
    logging.info("In a real scenario, this would stop the Sesame voice interaction")

def main():
    """Main function to test the triple click detection"""
    logging.info(f"Starting triple click test on GPIO {BUTTON_PIN}")
    logging.info(f"Click the button 3 times within {TRIPLE_CLICK_TIMEOUT} seconds to trigger the triple click event")
    logging.info("Press Ctrl+C to exit")
    
    # Initialize triple click detector
    triple_click_detector = TripleClickDetector(handle_triple_click)
    
    # Initialize button
    button = Button(BUTTON_PIN, bounce_time=0.1)
    
    # Set up button handlers
    button.when_pressed = lambda: triple_click_detector.on_click()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Triple click test stopped by user")
    finally:
        logging.info("Triple click test complete")

if __name__ == "__main__":
    main()
