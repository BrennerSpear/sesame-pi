#!/usr/bin/env python3

import logging
from pynput import keyboard
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class KeyboardTester:
    def __init__(self):
        self.running = True
        
        # Setup keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        
        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _on_press(self, key):
        """Handle key press events"""
        try:
            # For regular characters
            if hasattr(key, 'char'):
                logging.info(f'Key pressed: {key.char}')
            # For special keys
            else:
                logging.info(f'Special key pressed: {key}')
                
            # Check for spacebar
            if key == keyboard.Key.space:
                logging.info('Spacebar was pressed!')
            
            # Check for Q to quit
            elif hasattr(key, 'char') and key.char == 'q':
                logging.info('Q was pressed - stopping...')
                self.running = False
                return False  # Stop listener
                
        except Exception as e:
            logging.error(f'Error handling key press: {e}')

    def _on_release(self, key):
        """Handle key release events"""
        try:
            if hasattr(key, 'char'):
                logging.info(f'Key released: {key.char}')
            else:
                logging.info(f'Special key released: {key}')
        except Exception as e:
            logging.error(f'Error handling key release: {e}')

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        logging.info('Received interrupt signal - stopping...')
        self.running = False
        self.keyboard_listener.stop()
        sys.exit(0)

    def start(self):
        """Start the keyboard tester"""
        logging.info('Starting keyboard test...')
        logging.info('Press keys to see events (Spacebar and Q are special cases)')
        logging.info('Press Ctrl+C to exit')
        
        # Start the listener
        self.keyboard_listener.start()
        
        # Keep the main thread running
        self.keyboard_listener.join()

if __name__ == '__main__':
    tester = KeyboardTester()
    tester.start()
