# #
# # mqtt_clientID = mqtt_.connect_mqtt()
# # print("Handle connect!")
# # client.loop_start()
# # mqtt_.publish(mqtt_clientID, string_JSON)
# # print("Sent the Data!")
#
# from paho.mqtt import client as mqtt_client, client
#
#
# class MQTTHandle:
#     """The class helps to get the mqtt connected and working"""
#
#     def __init__(self, json):
#         self.string_JSON_ = json
#
#     broker = 'broker.emqx.io'
#     port = 1883
#     topic = "/python/mqtt"
#     client_id = f'python-mqtt-RADAR'
#     username = 'emqx'
#     password = 'public'
#
#     def connect_mqtt(self):
#         # Set Connecting Client ID
#         print("self.clientID", self.client_id)
#         client_ = mqtt_client.Client(self.client_id)
#         client_.username_pw_set(self.username, self.password)
#         self.on_connect()
#         client_.connect(self.broker, self.port)
#         return client_
#
#     def on_connect(self, client, userdata, flags, rc):
#         if rc == 0:
#             print("Connected to MQTT Broker!")
#         else:
#             print("Failed to connect, return code %d\n", rc)
#
#     def publish(self, client_, message_JSON):
#         result = client_.publish(self.topic, message_JSON)
#         # result: [0, 1]
#         status = result[0]
#         if status == 0:
#             print(f"Send `{message_JSON}` to topic `{self.topic}`")
#         else:
#             print(f"Failed to send message to topic {self.topic}")
#
#     def run(self):
#         print("in run")
#         mqtt_clientID = self.connect_mqtt()
#         mqtt_clientID.loop_start()
#         self.publish(mqtt_clientID, self.string_JSON_)
#         mqtt_clientID.loop_stop()
