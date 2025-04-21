from data import Data
from typing import Any, List, Optional
import can
from json import loads

class DataCANbus(Data):
    def __init__(self):
        super().__init__()
        # CANbus instantiation
        self.bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=50000)

        # Create a Notifier with the bus and the function listeners
        self.notifier = can.Notifier(self.bus, [self.load_data])

        self.load_voltage_data("{ \"voltage\" : 4 }")

    
    def connect(self, arg1, arg2):
        pass


    def load_data(self,msg):
        byte_array = bytearray(msg.data)
        if msg.arbitration_id == 0x124: # Camera overlay data
            self.load_message_json(msg.data)
        elif msg.arbitration_id == 0x124: # Wired Module data
            self.load_sensor_data(msg.data)
        elif msg.arbitration_id == 0x124: # Start logging
            self.set_logging(True)
        elif msg.arbitration_id == 0x124: # Stop logging
            self.set_logging(False)
        elif msg.arbitration_id == 0x124: # Boost recommended speed
            self.load_recommended_sp(msg.data)
        elif msg.arbitration_id == 0x124: # Boost predicted max speed
            self.load_predicted_max_speed(msg.data)
        elif msg.arbitration_id == 0x124: # Boost max speed achieved
            self.load_max_speed_achieved(msg.data)
            # Test
        elif msg.arbitration_id == 0x1: # Voltage 
            self.data["voltage"].update(byte_array[0])
        elif msg.arbitration_id == 0x2: # RPM
            self.data["cadence"].update(byte_array[0])
        elif msg.arbitration_id == 0x3: # KPH
            self.data["gps_speed"].update(byte_array[0])
        elif msg.arbitration_id == 0x4: # BPM
            self.data["heartRate"].update(byte_array[0])
        elif msg.arbitration_id == 0x5: # REC KPH
            self.data["rec_speed"].update(byte_array[0])
        elif msg.arbitration_id == 0x6: # ZONE KM
            self.data["zdist"].update(byte_array[0])
        elif msg.arbitration_id == 0x7: # MAX KPH
            self.data["max_speed_achieved"].update(byte_array[0])
        elif msg.arbitration_id == 0x8: # DIST KM
            self.data["ant_distance"].update(byte_array[0])
    
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