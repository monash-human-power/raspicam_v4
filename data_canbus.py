from data import Data
from typing import Any, List, Optional
import can
from json import loads

class DataCANbus(Data):
    def __init__(self):
        super().__init__()
        # CANbus instantiation
        self.bus = can.interface.Bus(interface='socketcand', host="10.0.16.15", port=29536, channel="can0")

        # Create a Notifier with the bus and the function listeners
        self.notifier = can.Notifier(self.bus, [self.on_data_message])


    def on_data_message(self,msg):
        if msg.arbitration_id == 0x123:
            pass
        elif msg.arbitration_id == 0x124:
            pass
        elif msg.arbitration_id == 0x124:
            self.load_recommended_sp(msg.data)
        elif msg.arbitration_id == 0x124:
            self.load_predicted_max_speed(msg.data)
        elif msg.arbitration_id == 0x124:
            self.load_max_speed_achieved(msg.data)

    
    # Load functions copied from DataV3, will need to be changed
    
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