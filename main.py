import subprocess
import paho.mqtt.client as mqtt
import json
import yaml
import argparse

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to the MQTT topic upon successful connection
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    topic = str(msg.topic).split("/")[1] # extract light id from topic
    payload = msg.payload.decode("utf-8")
    packet = json.loads(payload)
    #print(packet)
    if packet.get("state") == "ON":
        # only if the light was off before then send the command to turn it on
        if userdata.get(topic).get("state") == "OFF":
            cmd = f"sudo lampify v {topic} on"
            # print(cmd)
            subprocess.run(cmd, shell=True)

        # save the updated messages into userdata
        userdata["current_id"] = topic  # save current topic to the userdata dictionary
        userdata[topic]["state"] = packet.get("state")
        if packet.get("brightness") is not None: # ensure the values don't get overwritten with None
            userdata[topic]["brightness"] = packet.get("brightness")
        if packet.get("color_temp") is not None:
            userdata[topic]["temp"] = packet.get("color_temp")
        client.user_data_set(userdata)

        #command_maker_simple(userdata)
        command_maker_tempcontrol(userdata)

    elif packet.get("state") == "OFF":
        cmd = f"sudo lampify v {topic} off"
        # print(cmd)
        userdata[topic]["state"] = packet.get("state") # set the userdata off
        subprocess.run(cmd, shell=True)

# function to generate the cold and warm values given desired temperature and brightness
def mix_colours(temp, bright):
    cold_max_temp = 6000
    warm_max_temp = 3000
    threshold = (cold_max_temp + warm_max_temp)/2

    # clamp the allowable values
    if temp < warm_max_temp: temp = warm_max_temp
    if temp > cold_max_temp: temp = cold_max_temp

    if warm_max_temp <= temp <= threshold: # warm
        warm_value = bright
        cold_value = (warm_value * (temp - warm_max_temp)) / (threshold - warm_max_temp)
    else: # cold
        cold_value = bright
        warm_value = cold_value * (cold_max_temp - temp) / (cold_max_temp - threshold)

    # convert to int
    warm_value = int(round(warm_value, 0))
    cold_value = int(round(cold_value,0))

    return (cold_value, warm_value)



# takes mix_colours() and converts it to a command
def command_maker_tempcontrol(pkt):
    id = pkt.get("current_id")

    brightness = pkt.get(id).get("brightness")  # 0 to 255
    temp_mired = pkt.get(id).get("temp")
    temp_kelvin = 1000000 / temp_mired

    brightness_scaled = int(round(brightness * (10/255), 0)) # convert from (0 to 255) to (0 to 10)
    (desired_cold, desired_warm) = mix_colours(temp_kelvin, brightness_scaled)

    if pkt.get(id).get("reversed") == True: # reverse if needed
        (desired_cold, desired_warm) = (desired_warm, desired_cold)

    cmd = f"sudo lampify v {id} dualcustom {desired_cold} {desired_warm}"
    # print(cmd)
    subprocess.run(cmd, shell = True)


# function for the topic parsing from yaml
def convert_to_tuples(lst):
    converted_list = []
    for id in lst:
        topic = f"lsp2mqtt/{id}/set"
        converted_list.append((topic, 0))
    return converted_list

if __name__ == "__main__":
    # parse location of config file
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help = "location of config file", default = "config.yaml")
    args = parser.parse_args()

# read config files
    with open(args.config, "r") as ymlfile: # need to change to absolute path when installing as service
        cfg = yaml.safe_load(ymlfile)

    MQTT_BROKER_HOST = cfg["mqtt_broker"]["host"]
    MQTT_BROKER_PORT = cfg["mqtt_broker"]["port"]
    MQTT_USERNAME = cfg["mqtt_broker"]["username"]
    MQTT_PASSWORD = cfg["mqtt_broker"]["password"]
    MQTT_TOPIC = convert_to_tuples(cfg["light_ids"])

    # add lights to userdata
    client_userdata = {'current_id': None}
    for id in cfg["light_ids"]:
        template_dict = {'state': "OFF", 'brightness': 127, 'temp': 200, 'reversed': False} # default values
        if id in cfg["reversed_colour_ids"]: # if its reversed, set reverse property to True
            template_dict['reversed'] = True
        client_userdata[id] = template_dict

    client = mqtt.Client(userdata=client_userdata)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    #client.user_data_set(dict(state = None, brightness = None, temp = None)) # initialise userdata

    # Connect to the MQTT broker
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

    # Start the MQTT loop in the background
    client.loop_forever()


