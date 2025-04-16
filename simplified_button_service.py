#!/usr/bin/env python3
"""
Simplified version of the Sesame button service using an event-based approach.
This maintains the core functionality (triple-click detection and process management)
but uses a simpler implementation with signal.pause().

Connect a button between GPIO pin 19 and ground (GND).
"""

import os
import signal
import subprocess
import threading
from gpiozero import Button
from signal import pause

# Button configuration
BUTTON_PIN = 19  # GPIO pin for the button
TRIPLE_CLICK_TIMEOUT = 0.5  # seconds between clicks to count as triple click

# File to store the PID of the running Sesame process
SESAME_PID_FILE = "/tmp/sesame_ws.pid"
# Path to the voice interaction script
SESAME_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_interaction.py")
# Python interpreter path (use venv if available)
VENV_PYTHON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv/bin/python")
PYTHON_PATH = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "/usr/bin/python3"

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

def is_sesame_running():
    """Check if the Sesame process is running"""
    if os.path.exists(SESAME_PID_FILE):
        try:
            with open(SESAME_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, ValueError, FileNotFoundError, PermissionError):
            # Process doesn't exist or PID file is invalid
            if os.path.exists(SESAME_PID_FILE):
                os.remove(SESAME_PID_FILE)
            return False
    return False

def start_sesame():
    """Start the Sesame voice interaction process"""
    if is_sesame_running():
        print("Sesame is already running")
        return
    
    print("Starting Sesame connection...")
    # Start the voice interaction script as a subprocess
    proc = subprocess.Popen([PYTHON_PATH, SESAME_SCRIPT])
    
    # Store the PID
    with open(SESAME_PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    print(f"Sesame started with PID {proc.pid}")

def stop_sesame():
    """Stop the Sesame voice interaction process"""
    if not is_sesame_running():
        print("Sesame is not running")
        return
    
    print("Stopping Sesame connection...")
    try:
        with open(SESAME_PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # Send SIGTERM to gracefully terminate
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        max_wait = 5  # seconds
        for _ in range(max_wait):
            try:
                os.kill(pid, 0)  # Check if process exists
                import time
                time.sleep(1)
            except ProcessLookupError:
                break  # Process has terminated
        
        # If process still exists, force kill
        try:
            os.kill(pid, 0)
            print(f"Process {pid} didn't terminate gracefully, sending SIGKILL")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Process has terminated
        
        # Remove PID file
        if os.path.exists(SESAME_PID_FILE):
            os.remove(SESAME_PID_FILE)
        
        print("Sesame stopped")
    except Exception as e:
        print(f"Error stopping Sesame: {e}")
        # Clean up PID file in case of error
        if os.path.exists(SESAME_PID_FILE):
            os.remove(SESAME_PID_FILE)

def handle_button_press():
    """Handle button press - start Sesame if not running"""
    if not is_sesame_running():
        start_sesame()

def handle_triple_click():
    """Handle triple click - stop Sesame if running"""
    print("Triple click detected")
    if is_sesame_running():
        stop_sesame()

# Initialize triple click detector
triple_click_detector = TripleClickDetector(handle_triple_click)

# Initialize button
button = Button(BUTTON_PIN, bounce_time=0.1, pull_up=True)

# Set up button handlers
button.when_pressed = lambda: triple_click_detector.on_click()
button.when_released = handle_button_press

print(f"Button service started. Monitoring button on GPIO {BUTTON_PIN}.")
print("Single press: Start Sesame if not running")
print("Triple press: Stop Sesame if running")
print("Press Ctrl+C to exit")

# Keep the script running using signal.pause() instead of a while loop
try:
    pause()
except KeyboardInterrupt:
    print("Button service stopped by user")
except Exception as e:
    print(f"Error in button service: {e}")
    raise
finally:
    print("Button service shutting down")
