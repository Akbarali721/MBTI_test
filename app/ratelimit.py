"""So'rov chegaralagichi — butun ilova uchun BITTA nusxa.

`app.state.limiter` bitta obyektni ko'rsatadi va slowapi dekoratori aynan shundan
foydalanadi. Har router o'z `Limiter()` ini yaratsa, chegara faqat bittasida
ishlab, qolganlarida jimgina o'chib qolardi.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    storage_uri=settings.rate_limit_storage_uri,
)
