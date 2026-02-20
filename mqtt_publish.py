import paho.mqtt.client as mqtt
import json

mqttBroker = "broker.hivemq.com"

# for debugging
def on_publish(client, userdata, mid, reason_codes, properties):
    print("Payload delivered", mid)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT broker")
    else:
        print("Failed to connect, reason:", reason_code)

client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="traffic_data", protocol=mqtt.MQTTv5)
client.on_publish = on_publish
client.on_connect = on_connect

client.connect(mqttBroker)
client.loop_start()

def publish_data(data):
    client.publish("traffic/junction_1/west", json.dumps(data), qos=1)