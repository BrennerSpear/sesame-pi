#!/usr/bin/env python3
import os
import signal
import subprocess
import time
import logging
from gpiozero import Button
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/sesame_button.log'),
        logging.StreamHandler()
    ]
)

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
        logging.info("Sesame is already running")
        return
    
    logging.info("Starting Sesame connection...")
    # Start the voice interaction script as a subprocess
    proc = subprocess.Popen([PYTHON_PATH, SESAME_SCRIPT])
    
    # Store the PID
    with open(SESAME_PID_FILE, "w") as f:
        f.write(str(proc.pid))
    
    logging.info(f"Sesame started with PID {proc.pid}")

def stop_sesame():
    """Stop the Sesame voice interaction process"""
    if not is_sesame_running():
        logging.info("Sesame is not running")
        return
    
    logging.info("Stopping Sesame connection...")
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
                time.sleep(1)
            except ProcessLookupError:
                break  # Process has terminated
        
        # If process still exists, force kill
        try:
            os.kill(pid, 0)
            logging.warning(f"Process {pid} didn't terminate gracefully, sending SIGKILL")
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # Process has terminated
        
        # Remove PID file
        if os.path.exists(SESAME_PID_FILE):
            os.remove(SESAME_PID_FILE)
        
        logging.info("Sesame stopped")
    except Exception as e:
        logging.error(f"Error stopping Sesame: {e}")
        # Clean up PID file in case of error
        if os.path.exists(SESAME_PID_FILE):
            os.remove(SESAME_PID_FILE)

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
            self.click_count = 0
            self.timer = None

def handle_button_press():
    """Handle button press - start Sesame if not running"""
    if not is_sesame_running():
        start_sesame()

def handle_triple_click():
    """Handle triple click - stop Sesame if running"""
    logging.info("Triple click detected")
    if is_sesame_running():
        stop_sesame()

def main():
    """Main function to run the button service"""
    logging.info("Starting Sesame Button Service")
    
    # Initialize triple click detector
    triple_click_detector = TripleClickDetector(handle_triple_click)
    
    # Initialize button
    button = Button(BUTTON_PIN, bounce_time=0.1)
    
    # Set up button handlers
    button.when_pressed = lambda: triple_click_detector.on_click()
    button.when_released = handle_button_press
    
    logging.info(f"Button service started. Monitoring button on GPIO {BUTTON_PIN}.")
    logging.info("Single press: Start Sesame if not running")
    logging.info("Triple press: Stop Sesame if running")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Button service stopped by user")
    except Exception as e:
        logging.error(f"Error in button service: {e}")
        raise
    finally:
        logging.info("Button service shutting down")

if __name__ == "__main__":
    main()
