# Sesame Pi

Sesame Pi is a Raspberry Pi-based voice interaction system that can be controlled with a physical button. This README combines information about system setup, button service implementations, and usage instructions.

## System Requirements and Installation

Before installing Python dependencies, ensure you have the following system packages installed on your Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev build-essential
sudo apt-get install -y python3-gpiod
sudo apt-get install -y libasound2-dev
sudo apt install -y jq
```

Set up a Python virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure audio (if needed):

```bash
sudo nano /etc/asound.conf
```

Test the speaker:

```bash
speaker-test -D plughw:1,0 -t wav
```

Install wifi-connect (optional):

```bash
# install wifi-connect
cd /usr/local/sbin
sudo rm -f wifi-connect
sudo curl -L https://github.com/balena-os/wifi-connect/releases/download/v4.4.6/wifi-connect-v4.4.6-linux-aarch64.tar.gz -o wifi-connect.tar.gz
sudo tar -xzf wifi-connect.tar.gz
sudo rm wifi-connect.tar.gz
sudo chmod +x wifi-connect
```

Set up the wifi-connect wrapper script:

```bash
sudo nano /usr/local/bin/wifi-connect-wrapper.sh
sudo chmod +x /usr/local/bin/wifi-connect-wrapper.sh
```

## Button Service Overview

2. **Button Service** (`simplified_button_service.py`): Uses an event-based approach with `signal.pause()`

####  Implementation
- Uses `signal.pause()` to keep the program running (more event-driven)
- Maintains core functionality (triple-click detection and process management)
- Uses simple print statements instead of logging
- Can still run as a systemd service
- Has basic error handling
- Includes proper cleanup when exiting with Ctrl+C

### When to Use Each Approach

- **Use the simplified approach** if you prefer a more event-driven style and don't need extensive logging or error handling.

## Hardware Setup

Connect a momentary push button between GPIO pin 19 and ground (GND) on your Raspberry Pi. The button service uses the internal pull-up resistor, so no external resistor is needed.


## Testing and Usage

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

### Button Service

To test either button service:

```bash


# Simplified implementation
python3 simplified_button_service.py
```

This will:
- Start the Sesame voice interaction when the button is pressed once (if it's not already running)
- Stop the Sesame voice interaction when the button is triple-clicked (if it's running)
- Properly clean up when exited with Ctrl+C

## Triple-Click Detection Implementation

The triple-click detection works as follows:

1. **Click Timeout**: The timeout between clicks is set to 0.5 seconds to count as part of a triple-click sequence.

2. **Pause After Triple-Click**: After a triple-click is detected and Sesame is stopped, the system pauses for 2 seconds to prevent accidental immediate restart.

3. **Click Handling**: When a button press is detected, the click count is incremented. If it reaches 3, Sesame is stopped (if running). If not, a timer is started to reset the count after the timeout.

4. **Single-Click Action**: If only a single click is detected (and the timeout expires), Sesame is started if it's not already running.

5. **Proper Cleanup**: The script includes proper cleanup when exited with Ctrl+C, ensuring that any running processes are stopped and temporary files are removed.

## Installation as a Service

### Original Button Service

1. Make sure the scripts are executable:

```bash
chmod +x sesame_button_service.py
chmod +x voice_interaction.py
```

2. Copy the systemd service file to the system directory:

```bash
sudo cp sesame-button.service /etc/systemd/system/
```

3. Reload systemd to recognize the new service:

```bash
sudo systemctl daemon-reload
```

4. Enable the service to start on boot:

```bash
sudo systemctl enable sesame-button.service
```

5. Start the service:

```bash
sudo systemctl start sesame-button.service
```

### Simplified Button Service

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

## Troubleshooting

### Checking Service Status

```bash
sudo systemctl status simplified-button.service
```

### Viewing Logs

Original button service logs:
```bash
tail -f /home/pi/sesame_button.log
```

Voice interaction logs:
```bash
tail -f /home/pi/sesame-pi/session.log
```

Note: The simplified button service uses print statements rather than logging to a file.

### Restarting the Service

```bash
# For original implementation
sudo systemctl restart sesame-button.service

# For simplified implementation
sudo systemctl restart simplified-button.service
```

### Stopping the Service

```bash
# For original implementation
sudo systemctl stop sesame-button.service

# For simplified implementation
sudo systemctl stop simplified-button.service
```

## Uninstallation

If you want to remove the service:

```bash
# For original implementation
sudo systemctl stop sesame-button.service
sudo systemctl disable sesame-button.service
sudo rm /etc/systemd/system/sesame-button.service
sudo systemctl daemon-reload

# For simplified implementation
sudo systemctl stop simplified-button.service
sudo systemctl disable simplified-button.service
sudo rm /etc/systemd/system/simplified-button.service
sudo systemctl daemon-reload
