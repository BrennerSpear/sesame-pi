# Sesame Pi Button Service

This service allows you to control the Sesame voice interaction using a physical button connected to GPIO pin 19 on your Raspberry Pi.

## Features

- Single button press: Starts the Sesame voice interaction if it's not already running
- Triple button press: Stops the Sesame voice interaction if it's running
- Automatically starts on boot
- Handles clean shutdown of the voice interaction process

## Installation

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

## Hardware Setup

Connect a momentary push button between GPIO pin 19 and ground (GND) on your Raspberry Pi. The button service uses the internal pull-up resistor, so no external resistor is needed.

## Usage

- Press the button once to start the Sesame voice interaction
- Press the button three times in quick succession to stop the Sesame voice interaction

## Troubleshooting

### Checking Service Status

```bash
sudo systemctl status sesame-button.service
```

### Viewing Logs

Button service logs:
```bash
tail -f /home/pi/sesame_button.log
```

Voice interaction logs:
```bash
tail -f /home/pi/sesame-pi/session.log
```

### Restarting the Service

```bash
sudo systemctl restart sesame-button.service
```

### Stopping the Service

```bash
sudo systemctl stop sesame-button.service
```

## Uninstallation

If you want to remove the service:

```bash
sudo systemctl stop sesame-button.service
sudo systemctl disable sesame-button.service
sudo rm /etc/systemd/system/sesame-button.service
sudo systemctl daemon-reload
