from data import Data
from data_mqtt import DataMQTT
from data_canbus import DataCANbus

class DataFactory:
    @staticmethod
    def create(bike_version: str) -> Data:
        """Return an instance of Data corresponding to a given bike name."""
        if isinstance(bike_version, str):
            bike_version = bike_version.lower()

        # V2 data is deprecated. Use V3 data format everywhere.
        if bike_version in ["v2", "v3"]:
            return DataMQTT()
        if bike_version == "v4":
            return DataCANbus()
        raise NotImplementedError(f"Unknown bike: {bike_version}")