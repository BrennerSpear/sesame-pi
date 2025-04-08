#!/usr/bin/env python3

import keyboard
import logging
import time
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def on_space(event):
    if event.event_type == 'down':
        logging.info('Spacebar was pressed!')

def on_q(event):
    if event.event_type == 'down':
        logging.info('Q was pressed - stopping...')
        sys.exit(0)

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    logging.info('Received interrupt signal - stopping...')
    sys.exit(0)

def main():
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    logging.info('Starting keyboard test...')
    logging.info('Press keys to see events')
    logging.info('Press Spacebar to test space detection')
    logging.info('Press Q to quit')
    logging.info('Press Ctrl+C to exit')

    # Register handlers for specific keys
    keyboard.on_press(lambda e: logging.info(f'Key pressed: {e.name}'))
    keyboard.on_release(lambda e: logging.info(f'Key released: {e.name}'))
    
    # Special handlers for space and q
    keyboard.hook_key('space', on_space)
    keyboard.hook_key('q', on_q)

    # Keep the script running
    while True:
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f'Error: {e}')
