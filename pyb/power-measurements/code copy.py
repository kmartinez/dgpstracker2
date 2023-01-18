# Topic: MQTT Subscriber
# Author: Sherif Attia
# Date: 28/02/2022

import ipaddress
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from time import sleep
import json

# import adafruit_requests


JSON_FILE = open("test_json.json")
JSON_CONTENT = json.load(JSON_FILE)

# print("Printing JSON Data\n")
# print(JSON_CONTENT)

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("No WiFi Secrets supplied. Please make sure it's been imported correctly.")
    raise

print("ESP32-32 WebClient Test")
print("Small changes here")


# Connecting to the network.
print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

# topic setup
mqtt_topic = "activity/SENSOR"
mqtt_readings_json = json.dumps(JSON_CONTENT)
load_mqtt = json.loads(mqtt_readings_json)  # top priority
temp_packet = dict(list(JSON_CONTENT.items())[0:10])

def connect(mqtt_client, userdata, flags, rc):
    # called when client is successfully connected to the broker
    print("Connected to MQTT Broker")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # called when the mqtt client disconnects
    print("Disconnected from MQTT Broker!")


def publish(mqtt_client, userdata, topic, pid):
    # callback when the mqtt_client publishes data to a feed
    print("Published to {0} with PID {1}".format(topic, pid))


# create a socketpool
pool = socketpool.SocketPool(wifi.radio)

# Set up miniMQTT Client
mqtt_client = MQTT.MQTT(
    broker="10.9.10.14",
    port=1883,
    username="mqtt_username",
    password="mqtt_password",
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_publish = publish

print("Attempting to connect to %s" % mqtt_client.broker)
mqtt_client.connect()


count = 1
i = 0
# while count != 10:
#     reading = str(count + 20.0)
#     mqtt_client.publish(mqtt_topic, reading)
#     count += 1
#     sleep(0.5)
# reading = 1
# mqtt_client.publish("JSON PAYLOAD", reading)
print("Publishing acquired data")
# mqtt_client.publish(mqtt_topic, mqtt_readings_json)

while i < len(load_mqtt['Data']):
    dumpstr = json.dumps(load_mqtt['Data'][i])
    mqtt_client.loop()
    mqtt_client.publish(mqtt_topic, dumpstr, qos=1)
    i += 1
    sleep(0.5)
#     mqtt_client.publish(mqtt_topic, load_mqtt['Data'][i], qos=1)
#     mqtt_client.publish(mqtt_topic, load_mqtt['Data'][' Pressure'], qos=1)
#     mqtt_client.publish(mqtt_topic, load_mqtt['Data'][' Humidity'], qos=1)
#     mqtt_client.publish(mqtt_topic, load_mqtt['Data'][' Altitude '], qos=1)
#     mqtt_client.publish(mqtt_topic, json.dumps(load_mqtt), qos=1)
#     i += 1
#     sleep(0.5)
# for data in mqtt_topic_json:
#     mqtt_client.publish(mqtt_topic_json, reading)
#     sleep(1)

print("Disconnecting from %s" % mqtt_client.broker)
mqtt_client.disconnect()
