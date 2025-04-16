#!/usr/bin/env python3
"""
Simple script to test the button functionality.
Connect a button between GPIO pin 19 and ground (GND).
"""

import time
import logging
from gpiozero import Button

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

def handle_button_press():
    """Handle button press event"""
    logging.info("Button pressed")

def handle_button_release():
    """Handle button release event"""
    logging.info("Button released")

def main():
    """Main function to test the button"""
    logging.info(f"Starting button test on GPIO {BUTTON_PIN}")
    logging.info("Press Ctrl+C to exit")
    
    # Initialize button
    button = Button(BUTTON_PIN, bounce_time=0.1)
    
    # Set up button handlers
    button.when_pressed = handle_button_press
    button.when_released = handle_button_release
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Button test stopped by user")
    finally:
        logging.info("Button test complete")

if __name__ == "__main__":
    main()
