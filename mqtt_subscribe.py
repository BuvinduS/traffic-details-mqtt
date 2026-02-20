import paho.mqtt.client as mqtt
import time

def on_message(client, userdata, message):
    print("Message received", str(message.payload.decode("utf-8")))

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected with reason code:", reason_code)
    if reason_code == 0:
        print("Connecting...")
        client.subscribe("traffic/junction_1/decision")
        print("Connected...")

mqttBroker = "broker.hivemq.com"
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="Smartphone", protocol=mqtt.MQTTv5)

client.on_message = on_message
client.on_connect = on_connect

client.connect(mqttBroker, 1883, 60)

print(client.is_connected())

client.loop_forever()