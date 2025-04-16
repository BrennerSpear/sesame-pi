# Simplified Sesame Pi Button Service

This is a simplified version of the Sesame button service that uses an event-based approach with `signal.pause()` instead of a while loop.

## Comparison with Original Implementation

### Original Implementation
- Uses a while loop with `time.sleep(1)` to keep the program running
- Includes comprehensive logging to file and console
- Runs as a systemd service
- Has extensive error handling and cleanup

### Simplified Implementation
- Uses `signal.pause()` to keep the program running (more event-driven)
- Maintains core functionality (triple-click detection and process management)
- Uses simple print statements instead of logging
- Can still run as a systemd service
- Has basic error handling
- Includes proper cleanup when exiting with Ctrl+C (stops voice interaction process and removes PID file)

## Files Included

1. `simple_button_test.py` - A very basic button test that just prints when the button is pressed or released
2. `test_triple_click.py` - A test for triple-click detection using the event-based approach
3. `simplified_button_service.py` - The simplified button service with triple-click detection and process management
4. `simplified-button.service` - A systemd service file for the simplified button service

## Testing

### Basic Button Test

To test basic button functionality:

```bash
python3 simple_button_test.py
```

This will print a message when the button is pressed or released.

### Triple Click Test

To test the triple-click detection:

```bash
python3 test_triple_click.py
```

This will detect when you press the button three times in quick succession (within 0.5 seconds) and print a message.

### Simplified Button Service

To test the simplified button service:

```bash
python3 simplified_button_service.py
```

This will:
- Start the Sesame voice interaction when the button is pressed (if it's not already running)
- Stop the Sesame voice interaction when the button is triple-clicked (if it's running)
- Properly clean up when exited with Ctrl+C (stops any running voice interaction process and removes PID file)

## Installation as a Service

If you want to use the simplified button service as a systemd service:

1. Make sure the script is executable:

```bash
chmod +x simplified_button_service.py
```

2. Copy the systemd service file to the system directory:

```bash
sudo cp simplified-button.service /etc/systemd/system/
```

3. Reload systemd to recognize the new service:

```bash
sudo systemctl daemon-reload
```

4. Enable the service to start on boot:

```bash
sudo systemctl enable simplified-button.service
```

5. Start the service:

```bash
sudo systemctl start simplified-button.service
```

## Hardware Setup

Connect a momentary push button between GPIO pin 19 and ground (GND) on your Raspberry Pi. The button service uses the internal pull-up resistor, so no external resistor is needed.

## Triple-Click Detection Implementation

The triple-click detection works as follows:

1. **Click Timeout**: The timeout between clicks is set to 0.5 seconds to count as part of a triple-click sequence.

2. **Pause After Triple-Click**: After a triple-click is detected and Sesame is stopped, the system pauses for 2 seconds to prevent accidental immediate restart.

3. **Click Handling**: When a button press is detected, the click count is incremented. If it reaches 3, Sesame is stopped (if running). If not, a timer is started to reset the count after the timeout.

4. **Single-Click Action**: If only a single click is detected (and the timeout expires), Sesame is started if it's not already running.

5. **Proper Cleanup**: The script includes proper cleanup when exited with Ctrl+C, ensuring that any running processes are stopped and temporary files are removed.

## Advantages of the Simplified Approach

1. **More Event-Driven**: Using `signal.pause()` is more in line with the event-driven nature of button handling.
2. **Cleaner Code**: The simplified approach can lead to cleaner, more readable code.
3. **Resource Efficiency**: The event-driven approach can be more resource-efficient than polling with a while loop.

## When to Use Each Approach

- **Use the simplified approach** if you prefer a more event-driven style and don't need extensive logging or error handling.
- **Use the original approach** if you need comprehensive logging, more robust error handling, or if you need to perform periodic tasks in the while loop.

Both approaches are valid and can accomplish the same core functionality. The choice depends on your specific requirements and coding style preferences.
