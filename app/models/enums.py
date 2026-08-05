import enum


class PersonalitySessionStatus(str, enum.Enum):
    VISITED = "visited"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PersonalityDimension(str, enum.Enum):
    EI = "EI"
    SN = "SN"
    TF = "TF"
    JP = "JP"


class AppearanceTheme(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

