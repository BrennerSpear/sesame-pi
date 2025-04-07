# Sesame Pi

## System Requirements

Before installing Python dependencies, ensure you have the following system packages installed on your Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev build-essential

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


sudo nano /etc/asound.conf
defaults.pcm.card 1
defaults.ctl.card 1

speaker-test -D plughw:1,0 -t wav