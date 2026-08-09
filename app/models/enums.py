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


class AdminRole(str, enum.Enum):
    """Admin rollari. 008 migratsiyasidagi og'riqdan keyin native ENUM ishlatilmaydi:
    ustun String(16) bo'lib qoladi, cheklov CHECK orqali qo'yiladi."""

    OWNER = "owner"
    MODERATOR = "moderator"
    VIEWER = "viewer"


ADMIN_ROLE_VALUES: tuple[str, ...] = tuple(member.value for member in AdminRole)


class NotificationStatus(str, enum.Enum):
    """Bildirishnoma navbati holatlari.

    Terminal holatlar ataylab ajratilgan, chunki ular boshqacha muomala talab qiladi:
    `SENT` va `CANCELLED` — normal yakun, `BLOCKED` — foydalanuvchi botni bloklagan,
    `FAILED` — urinishlar tugadi (diqqat talab qiladi), `INVALID` — kod nuqsoni.
    """

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    FAILED = "failed"
    INVALID = "invalid"


NOTIFICATION_STATUS_VALUES: tuple[str, ...] = tuple(member.value for member in NotificationStatus)

# Bu holatlardan keyin qator hech qachon qayta yuborilmaydi (retry tugmasidan tashqari).
NOTIFICATION_TERMINAL_STATUSES: frozenset[str] = frozenset(
    {
        NotificationStatus.SENT.value,
        NotificationStatus.CANCELLED.value,
        NotificationStatus.BLOCKED.value,
        NotificationStatus.FAILED.value,
        NotificationStatus.INVALID.value,
    }
)
