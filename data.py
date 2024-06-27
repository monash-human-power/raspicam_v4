from abc import ABC, abstractmethod
from typing import Any, List, Optional
import config
from datavalue import DataValue
from mhp import topics





class Data(ABC):
    """A class to keep track of the most recent bike data for the overlays.

    Data comes into the class in the V3 MQTT format and may be accessed
    by using this class as a dictionary. This class is implemented by
    versions for specific bikes (i.e. DataV3)."""

    def __init__(self):
        # This is by no means a complete list of data fields we could track -
        # just the ones we currently think we might use on the overlays.
        self.data = {
            # DAS data
            "power": DataValue(int),
            "cadence": DataValue(int),
            "heartRate": DataValue(int),
            "gps": DataValue(int),
            "gps_speed": DataValue(float),
            "ant_speed": DataValue(float),
            "ant_distance": DataValue(float),
            "reed_velocity": DataValue(float),
            "reed_distance": DataValue(float),
            # Power model data
            "rec_power": DataValue(float),
            "rec_speed": DataValue(float),
            "predicted_max_speed": DataValue(float),
            "max_speed_achieved": DataValue(float, time_to_expire=3600),
            "zdist": DataValue(float),
            "plan_name": DataValue(str),
            # Voltage
            "voltage": DataValue(float, config.BATTERY_PUBLISH_INTERVAL),
        }
        self.logging = DataValue(bool, time_to_expire=3600)
        self.message = DataValue(str, 20)

    def set_logging(self, logging: bool) -> None:
        """Set the logging status of the DAS."""
        self.logging.update(logging)

    def is_logging(self) -> bool:
        """Return whether the DAS is logging."""
        return self.logging.get()

    def load_message(self, message: str) -> None:
        """Store a message which is made available by self.get_message."""
        self.message.update(message)

    def has_message(self) -> bool:
        """Check if a message is available for display on the overlay.

        Return True if a message is available for display. Otherwise, return
        false if the message has already been sent of the most recent message
        has expired.
        """
        return self.message.is_valid()

    def get_message(self) -> Optional[str]:
        """Return the most recent message from the DAShboard.

        This should only be called if self.has_message returns true.
        """
        return self.message.get()

    def __getitem__(self, field: str) -> Any:
        """Get the most recent value of a data field.

        This overloads the [] operator e.g. call with data_instance["power"].
        This only allows fetching the data, not assignment.
        """
        if field in self.data:
            return self.data[field]
        else:
            print(f"WARNING: invalid data field `{field}` used")
            return None

    @abstractmethod
    def load_data(self, topic: str, data: str) -> None:
        """Update stored fields with data stored in an MQTT data packet.

        Only the supplied data fields should be updated, the rest remain as
        they were. This should be implemented by all Data subclasses
        """
        pass

    @staticmethod
    @abstractmethod
    def get_topics() -> List[topics.Topic]:
        """Return a list of the topics the data for the bike comes from.

        Should be implemented by Data subclasses."""
        pass
