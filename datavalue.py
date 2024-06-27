from typing import Any, List, Optional
from time import time
class DataValue:
    """A class to represent a data field (eg. Power, Cadence).

    Attributes:
        value: Any type that represents the current data value of the field
        data_type: Type that represents the attribute of the data
                   (eg. int, str)
        time_updated: Integer that represents the time when value was updated
        DATA_EXPIRY: Constant integer of how long a data value is considered
                     valid for until expired
    """

    def __init__(self, data_type: type, time_to_expire: int = 5) -> None:
        self.value = None
        self.data_type = data_type
        # Time on update is initially set to expire by default
        self.time_updated = 0
        self.time_to_expire = time_to_expire

    def get(self) -> Any:
        """Return the data value if the expiry hasn't exceeded. Otherwise,
        it will return None."""
        if self.is_valid():
            return self.value
        return None

    def get_string(self, decimals: int = 0, scalar: int = 1) -> str:
        """Return the data value in string format, if the expiry hasn't exceeded.
        Otherwise it will return None.

        Args:
            decimals: Integer representing decimal places of the data point
            scalar: Integer used to multiply the data value
        """
        if self.data_type is str:
            return self.get()

        if self.data_type is bool:
            return str(self.get())

        if self.is_valid():
            format_str = f"{{:.{decimals}f}}"
            return format_str.format(self.value * scalar)
        return None

    def update(self, value: Any) -> None:
        """Update the data value and time it was updated.

        Args:
            value: Any type representing the data point of the field
        """
        if type(value) != self.data_type:
            # Casts value when the type is different to the assigned data_type
            value = self.data_type(value)
        self.value = value
        self.time_updated = time()

    def invalidate(self) -> None:
        """Invalidate the data value by making it received a long time ago."""
        self.time_updated = 0

    def is_valid(self) -> bool:
        """Assess whether data is valid by checking if the valid duration
        has exceeded. Return True if current time is less than the time
        when data expires."""
        return time() < self.time_updated + self.time_to_expire
