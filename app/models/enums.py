"""Enumerations for database models."""
import enum


class PlayerRole(str, enum.Enum):
    """Player position roles."""
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class DominantFoot(str, enum.Enum):
    """Player's dominant foot."""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"


class SessionType(str, enum.Enum):
    """Type of training session."""
    TRAINING = "TRAINING"
    MATCH = "MATCH"
    TEST = "TEST"


class PitchType(str, enum.Enum):
    """Type of playing surface."""
    NATURAL = "NATURAL"
    SYNTHETIC = "SYNTHETIC"
    INDOOR = "INDOOR"


class TimeOfDay(str, enum.Enum):
    """Time when session occurred."""
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"


class PlayerStatus(str, enum.Enum):
    """Player's physical status."""
    OK = "OK"
    INJURED = "INJURED"
    FATIGUED = "FATIGUED"
