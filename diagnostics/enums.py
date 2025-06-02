from enum import Enum

class MachineType(Enum):
    LIVE = "live"
    DEV = "dev"
    TEST = "test"

    @classmethod
    def from_string(cls, s: str):
        if not isinstance(s, str):
            raise TypeError(f"Input must be a string, got {type(s).__name__}")
        try:
            return cls(s.lower())
        except ValueError:
            valid_types = ", ".join([e.value for e in cls])
            raise ValueError(
                f"'{s}' is not a valid MachineType. "
                f"Valid types are: {valid_types}."
            )

    def __str__(self):
        return self.value