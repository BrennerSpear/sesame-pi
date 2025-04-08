#!/usr/bin/env python3

import asyncio
import evdev
import logging
import signal
import sys
from evdev import categorize, ecodes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class KeyboardMonitor:
    def __init__(self):
        self.running = True
        self.device = None

    async def find_keyboard(self):
        """Find the first keyboard device"""
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            # Look for keyboard-like devices
            if evdev.ecodes.EV_KEY in device.capabilities():
                logging.info(f'Found keyboard device: {device.name}')
                return device
        return None

    async def monitor_keyboard(self):
        """Monitor keyboard events"""
        try:
            self.device = await self.find_keyboard()
            if not self.device:
                logging.error('No keyboard device found!')
                return

            logging.info('Starting keyboard test...')
            logging.info('Press keys to see events')
            logging.info('Press Spacebar to test space detection')
            logging.info('Press Q to quit')
            logging.info('Press Ctrl+C to exit')

            async for event in self.device.async_read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    key_event = categorize(event)
                    if key_event.keystate == key_event.key_down:
                        key_name = key_event.keycode.replace('KEY_', '')
                        logging.info(f'Key pressed: {key_name}')
                        
                        # Check for Q to quit
                        if key_name == 'Q':
                            logging.info('Q pressed - stopping...')
                            self.running = False
                            break
                        # Check for spacebar
                        elif key_name == 'SPACE':
                            logging.info('Spacebar was pressed!')

        except Exception as e:
            logging.error(f'Error monitoring keyboard: {e}')
        finally:
            if self.device:
                self.device.close()

    def signal_handler(self, signum, frame):
        """Handle Ctrl+C"""
        logging.info('Received interrupt signal - stopping...')
        self.running = False
        if self.device:
            self.device.close()
        sys.exit(0)

async def main():
    monitor = KeyboardMonitor()
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, monitor.signal_handler)
    await monitor.monitor_keyboard()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Application terminated by user')
    except Exception as e:
        logging.error(f'Application error: {e}')
