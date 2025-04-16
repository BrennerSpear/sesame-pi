#!/usr/bin/env python3
"""
Simple event-based button test using the approach suggested by the user.
Connect a button between GPIO pin 19 and ground (GND).
"""

from gpiozero import Button
from signal import pause

# Use BCM pin number (GPIO19)
button = Button(19, pull_up=True)  # active_low = True by default

def on_press():
    print("Button pressed!")

def on_release():
    print("Button released!")

button.when_pressed = on_press
button.when_released = on_release

print("Listening for button on GPIO 19...")
print("Press Ctrl+C to exit")

# Keep the script running using signal.pause()
try:
    pause()  # Keeps the program running
except KeyboardInterrupt:
    print("Button test stopped by user")
finally:
    print("Button test complete")
