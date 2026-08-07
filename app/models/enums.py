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


class PaymentStatus(str, enum.Enum):
    """To'lov holatlari. Ustun turi String(32) bo'lib qoladi, DB darajasida CHECK cheklovi qo'yiladi."""

    PENDING = "pending"
    RECEIPT_SENT = "receipt_sent"
    APPROVED = "approved"
    REJECTED = "rejected"


PAYMENT_STATUS_VALUES: tuple[str, ...] = tuple(member.value for member in PaymentStatus)
