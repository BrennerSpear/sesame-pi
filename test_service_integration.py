#!/usr/bin/env python3
"""
Script to test the integration between the button service and voice interaction.
This script simulates the button service's functionality of starting and stopping
the voice_interaction.py script.
"""

import os
import signal
import subprocess
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

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

def print_menu():
    """Print the menu options"""
    print("\nSesame Service Integration Test")
    print("-------------------------------")
    print("1. Start Sesame")
    print("2. Stop Sesame")
    print("3. Check Sesame Status")
    print("4. Exit")
    print("-------------------------------")
    return input("Enter your choice (1-4): ")

def main():
    """Main function to test the service integration"""
    logging.info("Starting service integration test")
    
    while True:
        choice = print_menu()
        
        if choice == '1':
            start_sesame()
        elif choice == '2':
            stop_sesame()
        elif choice == '3':
            status = "running" if is_sesame_running() else "not running"
            logging.info(f"Sesame is {status}")
        elif choice == '4':
            logging.info("Exiting service integration test")
            # Make sure to stop Sesame if it's running
            if is_sesame_running():
                stop_sesame()
            break
        else:
            logging.warning("Invalid choice. Please enter a number between 1 and 4.")
        
        # Small delay to allow logs to be displayed
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
        # Make sure to stop Sesame if it's running
        if is_sesame_running():
            stop_sesame()
    except Exception as e:
        logging.error(f"Error in service integration test: {e}")
        # Make sure to stop Sesame if it's running
        if is_sesame_running():
            stop_sesame()
