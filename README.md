# lsp2mqtt
lampify to mqtt

## Quick Setup Guide
 - Install `lampify`, the custom_temp branch. i.e. https://github.com/Justin8428/lampify/tree/custom_temp
 - Setup your lights using `lampify`. **Remember the ID you use for each light, you will need to provide these IDs to lsp2mqtt**
 - Manually add your [lights to MQTT in HA](https://www.home-assistant.io/integrations/light.mqtt/). Use the .json schema and the light IDs must match the ones you provided to `lampify` earlier. See the `example_mqtt.yaml` example, replace `LIGHTID` with the ID you provided earlier. If you want to add more lights add a separate `- light` entry in the yaml as described in the link.
 - Clone this repo and edit `config.yaml` to match your configuration
 - Run `main.py`

If on debian, may need to install `python3-paho-mqtt`, i.e. the paho-mqtt package for python

## `config.yaml` setup
 - Under `mqtt_broker:`, put the IP address and credentials for your MQTT broker
 - Under `light_ids:`, put the light IDs that you have paired with via `lampify setup` and that you have added to HA.
 - Under `reversed_colour_ids:`, put the light IDs that have reversed colour temperatures. Leave this section blank if you don't need to reverse any IDs. Also, any IDs you put here must also be present under `light_ids:` otherwise it will be ignored.

## arguments for config file
If you are planning to run this as a systemctl service, you can provide a custom location for your `config.yaml` as an argument.
e.g. `python3 ~/lsp2mqtt/main.py "/path/to/config.yaml"`

## Extra instructions for auto-start if your bluetooth dongle is connected over usbip
1. Create a systemctl service to start lsp2mqtt on boot. Set it to start after `multi-user.target`
2. Create a shell file to connect to the usbip. e.g.
   
`sudo usbip attach -r "remote_ip" -b "port-id"`

`sudo hciconfig -a`

3. Register this shell file as a systemctl service, and enable to so it starts on boot. Also set it to start after multi-user.target
4. Add `vhci-hcd` to the list of kernel modules to start at startup, located at `/etc/modules-load.d/modules.conf`

