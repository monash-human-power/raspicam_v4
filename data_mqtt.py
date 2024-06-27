import paho.mqtt.client as mqtt
from data import Data
from mhp import topics
from mhp.topics import Topic
from typing import Any, List, Optional
import config
from json import loads

class DataMQTT(Data):
    @staticmethod
    def get_topics() -> List[topics.Topic]:
        # TODO: Not have to read configs everytime
        return [
            topics.WirelessModule.all().start,
            topics.WirelessModule.all().data,
            topics.WirelessModule.all().stop,
            topics.Camera.overlay_message,
            DataMQTT.create_voltage_topic(),
            topics.BOOST.recommended_sp,
            topics.BOOST.predicted_max_speed,
            topics.BOOST.max_speed_achieved,
            # TODO: Implement handling topics.BOOST.generate_complete
        ]

    @staticmethod
    def create_voltage_topic() -> topics.Topic:
        device = config.read_configs()["device"]
        battery_topic = topics.Camera.status_camera / device / "battery"
        return battery_topic

    def __init__(self):
        super().__init__()
        # MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.reconnect_delay_set(max_delay=10)
        self.set_callback_for_topic_list(
            self.get_topics(), self.on_data_message)

        # Used to detect missed start messages
        self.data_messages_received = 0

    def load_data(self, topic: str, data: str) -> None:
        """Update stored fields with data from a V3 WM data packet."""
        if topic == topics.Camera.overlay_message:
            self.load_message_json(data)
        elif topics.WirelessModule.all().data.matches(topic):
            self.load_sensor_data(data)
            # We have 3 WMs, so in the worst case we shouldn't receive more
            # than four messages due to delay after logging stops. If we do,
            # we know we missed the start message.
            self.data_messages_received += 1
            if not self.logging.get() and self.data_messages_received > 3:
                self.set_logging(True)
        elif topics.WirelessModule.all().start.matches(topic):
            self.data_messages_received = 0
            self.set_logging(True)
        elif topics.WirelessModule.all().stop.matches(topic):
            self.set_logging(False)
        elif self.create_voltage_topic().matches(topic):
            self.load_voltage_data(data)
        elif topic == topics.BOOST.recommended_sp:
            self.load_recommended_sp(data)
        elif topic == topics.BOOST.predicted_max_speed:
            self.load_predicted_max_speed(data)
        elif topic == topics.BOOST.max_speed_achieved:
            self.load_max_speed_achieved(data)

    def load_message_json(self, data: str) -> None:
        """Load a message in the V3 JSON format."""
        message_data = loads(data)
        self.load_message(message_data["message"])

    def load_sensor_data(self, data: str) -> None:
        """Load data in the json V3 wireless sensor module format."""
        module_data = loads(data)
        sensor_data = module_data["sensors"]
        for sensor in sensor_data:
            sensor_name = sensor["type"]
            sensor_value = sensor["value"]

            if sensor_name == "gps":
                self.data["gps"].update(1)
                self.data["gps_speed"].update(sensor_value["speed"] * 3.6)
            elif sensor_name == "antSpeed":
                self.data["ant_speed"].update(sensor_value * 3.6)
            elif sensor_name == "antDistance":
                self.data["ant_distance"].update(sensor_value)
            elif sensor_name == "reedVelocity":
                self.data["reed_velocity"].update(sensor_value * 3.6)
            elif sensor_name == "reedDistance":
                self.data["reed_distance"].update(sensor_value)
            elif sensor_name in self.data.keys():
                self.data[sensor_name].update(sensor_value)

    def load_voltage_data(self, data: str) -> None:
        voltage_data = loads(data)
        self.data["voltage"].update(voltage_data["voltage"])

    def load_recommended_sp(self, data: str) -> None:
        python_data = loads(data)
        self.data["rec_power"].update(python_data["power"])
        self.data["rec_speed"].update(python_data["speed"] * 3.6)
        self.data["zdist"].update(python_data["zoneDistance"])

    def load_predicted_max_speed(self, data: str) -> None:
        if data == "":
            self.data["predicted_max_speed"].invalidate()
        else:
            python_data = loads(data)
            self.data["predicted_max_speed"].update(python_data["speed"] * 3.6)

    def load_max_speed_achieved(self, data: str) -> None:
        if data == "":
            self.data["max_speed_achieved"].invalidate()
        else:
            python_data = loads(data)
            self.data["max_speed_achieved"].update(python_data["speed"] * 3.6)

    # MQTT Methods
    def set_callback_for_topic_list(self, topics: List[Topic], callback):
        """ Set the on_message callback for every topic in topics to the
            provided callback """
        for topic in map(str, topics):
            self.client.message_callback_add(topic, callback)

    def subscribe_to_topic_list(self, topics: List[Topic]):
        """ Construct a list in the format [("topic1", qos1), ("topic2", qos2), ...]
            see https://pypi.org/project/paho-mqtt/#subscribe-unsubscribe """
        topic_values = map(str, topics)
        at_most_once_qos = [0] * len(topics)

        topics_qos = list(zip(topic_values, at_most_once_qos))
        self.client.subscribe(topics_qos)
    
    def on_data_message(self, client, userdata, msg):
        with self.exception_handler:
            payload = msg.payload.decode("utf-8")
            self.load_data(msg.topic, payload)

    
    def _on_connect(self, client, userdata, flags, rc):
        self.subscribe_to_topic_list(self.get_topics())
        with self.exception_handler:
            self.on_connect(client, userdata, flags, rc)
        print("Connected with rc: {}".format(rc))
    
    def on_disconnect(self, client, userdata, msg):
        print("Disconnected from broker")