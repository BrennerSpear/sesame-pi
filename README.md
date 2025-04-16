# Sesame Pi

## System Requirements

Before installing Python dependencies, ensure you have the following system packages installed on your Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install portaudio19-dev python3-dev build-essential
sudo apt-get install -y python3-gpiod
sudo apt-get install -y libasound2-dev
sudo apt install -y jq

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


sudo nano /etc/asound.conf
```


```bash
speaker-test -D plughw:1,0 -t wav
```

```bash
# install wifi-connect
cd /usr/local/sbin
sudo rm -f wifi-connect
sudo curl -L https://github.com/balena-os/wifi-connect/releases/download/v4.4.6/wifi-connect-v4.4.6-linux-aarch64.tar.gz -o wifi-connect.tar.gz
sudo tar -xzf wifi-connect.tar.gz
sudo rm wifi-connect.tar.gz
sudo chmod +x wifi-connect
```


```bash
sudo nano /usr/local/bin/wifi-connect-wrapper.sh
```

```bash
sudo chmod +x /usr/local/bin/wifi-connect-wrapper.sh
```