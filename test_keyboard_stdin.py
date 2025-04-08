#!/usr/bin/env python3

import sys
import logging
import select
import termios
import tty

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def is_data():
    """Check if there's data ready to be read"""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def main():
    logging.info('Starting keyboard test...')
    logging.info('Press SPACE to test space detection')
    logging.info('Press Q to quit')
    
    # Save the terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    try:
        # Set the terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        while True:
            if is_data():
                char = sys.stdin.read(1)
                if char == ' ':
                    logging.info('Spacebar was pressed!')
                elif char.lower() == 'q':
                    logging.info('Q was pressed - stopping...')
                    break
                else:
                    logging.info(f'Key pressed: {char}')
                    
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print()  # Add a newline at the end

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info('Application terminated by user')
