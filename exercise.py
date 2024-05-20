#!/usr/bin/env python3

import random
import time

import paho.mqtt.client as mqtt
import yaml


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code: {reason_code}")


def on_publish(client, userdata, mid, reason_code, properties):
    print(f"Published message: {mid}")


def publish():
    temperature = random.randint(0, 10)
    mqttc.publish("s/us", f"211,{temperature}")


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")

    c8yType = ""
    if payload.startswith("511"):
        print(f"Received shell command: {payload}")
        c8yType = "c8y_Command"
    elif payload.startswith("513"):
        print(f"Received config change: {payload}")
        c8yType = "c8y_Configuration"
    else:
        print(f"Received unrecognized payload: {payload}")

    client.publish("s/us", f"501,{c8yType}", qos=1).wait_for_publish(1)
    client.publish("s/us", f"503,{c8yType},Success", qos=1)


with open("exercise.yaml", "r") as f:
    config = yaml.safe_load(f)

serverUrl = config["serverUrl"]
clientId = config["clientId"]
device_name = config["device_name"]
tenant = config["tenant"]
username = config["username"]
password = config["password"]
ca_certs = config["ca_certs"]
certfile = config["certfile"]
keyfile = config["keyfile"]

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, clientId)

mqttc.username_pw_set(tenant + "/" + username, password)
# port = 1883
mqttc.tls_set(
    ca_certs=ca_certs,
    # certfile=certfile,
    # keyfile=keyfile,
)
port = 8883

mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_message = on_message

mqttc.connect(serverUrl, port)
mqttc.loop_start()

mqttc.publish("s/us", f"100,{device_name},c8y_MQTTDevice", qos=1).wait_for_publish(1)
print("Device registered.")

mqttc.publish("s/us", "114,c8y_Command,c8y_Configuration", qos=1)
print("Command and configuration enabled.")

mqttc.subscribe("s/ds")
print("Subscribed.")

try:
    while True:
        publish()
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    pass


mqttc.disconnect()
mqttc.loop_stop()

exit(0)
