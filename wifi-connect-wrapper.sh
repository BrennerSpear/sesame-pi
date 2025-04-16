#!/bin/bash

# Check if already connected to Wi-Fi
wifi_connected=$(nmcli -t -f DEVICE,TYPE,STATE device | grep "wlan0:wifi:connected")

if [ -n "$wifi_connected" ]; then
	echo "Wi-Fi is already connected. Skipping WiFi Connect."
	exit 0
fi

# Launch WiFi Connect with your options
sudo /usr/local/sbin/wifi-connect -s "SesamePi"