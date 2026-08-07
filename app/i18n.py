"""Oddiy dict asosidagi tarjima katalogi (babel'siz).

Faqat interfeys matnlari shu yerda. Natija KONTENTI (xarakter tavsiflari) bazadan
keladi va tarjima qilinmaydi.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from starlette.requests import Request

SUPPORTED: tuple[str, ...] = ("uz", "ru")
DEFAULT: str = "uz"

LANG_QUERY_KEY = "lang"
LANG_COOKIE_KEY = "lang"
LANG_COOKIE_MAX_AGE = 365 * 24 * 60 * 60

LANGUAGE_NAMES: dict[str, str] = {
    "uz": "O‘zbekcha",
    "ru": "Русский",
}
LANGUAGE_SHORT: dict[str, str] = {
    "uz": "UZ",
    "ru": "RU",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "uz": {
        # Umumiy
        "site.name": "Xarakter testi",
        "site.title_default": "Xarakter testi",
        "site.description": (
            "Xarakteringizning kuchli tomonlarini, motivatsiyangiz nega pasayishini va "
            "sizga mos ishlash hamda muloqot usulini 4 daqiqada aniqlang."
        ),
        "common.no_wrong_answer": "To‘g‘ri yoki noto‘g‘ri javob yo‘q.",
        "common.back_home": "Bosh sahifaga qaytish",
        "common.logo_alt": "Xarakterni anglash logosi",
        # Tillar nomi LANGUAGE_NAMES/LANGUAGE_SHORT da — bu yerda takrorlanmaydi.
        "lang.label": "Til",
        # Landing
        "landing.title": "Xarakter va hayot uslubi testi",
        "landing.eyebrow": "XARAKTER VA HAYOT USLUBI TESTI",
        "landing.headline": "Siz dangasa emassiz",
        "landing.lead": "Balki o‘zingizga mos bo‘lmagan usulda harakat qilayotgandirsiz.",
        "landing.copy": (
            "Xarakteringizning kuchli tomonlarini, motivatsiyangiz nega pasayishini va "
            "sizga mos ishlash hamda muloqot usulini aniqlang."
        ),
        "landing.meta_aria": "Test haqida",
        "landing.meta_questions": "24 ta savol",
        "landing.meta_minutes": "4 daqiqa",
        "landing.meta_personal": "Shaxsiy natija",
        "landing.cta": "Xarakterimni aniqlash",
        "landing.hero_alt": "Xarakterni anglash testi",
        # Ko‘rsatma
        "instructions.title": "Testdan oldin",
        "instructions.text": (
            "Javoblarni hozir qanday bo‘lishni xohlayotganingizga emas, "
            "odatda qanday harakat qilishingizga qarab belgilang."
        ),
        "instructions.gender_group": "Jinsni tanlang",
        "instructions.female": "Ayol",
        "instructions.male": "Erkak",
        "instructions.start": "Testni boshlash",
        # Savol
        "question.title": "Savol {current} / {total}",
        "question.back": "Orqaga",
        "question.next": "Keyingi",
        "question.see_result": "Natijani ko‘rish",
        "question.progress_aria": "Test bosqichi",
        # Yuklanish
        "loading.title": "Natija tayyorlanmoqda",
        "loading.spinner_aria": "Tahlil qilinmoqda",
        "loading.step_1": "Kuchli tomonlaringiz tahlil qilinmoqda",
        "loading.step_2": "Sizga mos ishlash usuli aniqlanmoqda",
        "loading.step_3": "Muloqot xususiyatlaringiz tayyorlanmoqda",
        "loading.open_result": "Natijani ochish",
        # Savollar xatosi
        "questions_error.title": "Savollar yuklanmadi",
        "questions_error.text": "Savollarni yuklab bo‘lmadi. Iltimos, qayta urinib ko‘ring.",
        "questions_error.retry": "Qayta urinish",
        # Natija
        # eyebrow_after <strong> tegidan keyin bevosita qo'shiladi, shuning uchun
        # bo'shliq matnning o'zida turadi.
        "result.eyebrow_before": "Sizning xarakter yo‘nalishingiz",
        "result.eyebrow_after": " tipiga eng yaqin.",
        "result.type_label": "Tip:",
        "result.disclaimer": (
            "Bu natija sizning eng yaqin xarakter yo‘nalishingizni ko‘rsatadi. "
            "Tibbiy yoki psixologik tashxis emas."
        ),
        "result.strengths": "Kuchli tomonlar",
        "result.challenges": "Qiyin tomonlar",
        "result.public_view": "Boshqalar sizni qanday ko‘rishi mumkin",
        "result.dimensions": "O‘lchovlar",
        "result.premium_headline": (
            "Xarakteringizni bildingiz. Endi undan qanday foydalanishni bilib oling."
        ),
        "result.premium_opened": "Premium profilingiz ochildi",
        "result.section.motivation": "Nega motivatsiyangiz pasayadi?",
        "result.section.work_style": "Sizga mos ishlash usuli",
        "result.section.career": "Sizga mos kasb va muhit",
        "result.section.friendship": "Do‘stlikda qanday odamsiz?",
        "result.section.relationship": "Munosabatda sizga qanday juft mos?",
        "result.section.compatible_people": "Sizga mos odamlar",
        "result.section.difficult": "Qaysi odamlar bilan muloqot qiyinroq?",
        "result.section.action_plan": "7 kunlik shaxsiy tavsiya",
        "result.locked_note": "Premium tahlil — ochish uchun to‘lov tasdiqlanishi kerak.",
        "result.status_pending_title": "To‘lov tekshirilmoqda",
        "result.status_pending_text": (
            "Chekingiz administratorga yuborildi. Tasdiqlangach premium natija ochiladi."
        ),
        "result.status_awaiting_title": "Chek kutilmoqda",
        "result.status_awaiting_text": (
            "To‘lovni amalga oshirib, chek rasmini Telegram bot orqali yuboring."
        ),
        "result.test_code_label": "Test kodi:",
        "result.refresh_status": "Holatni yangilash",
        "result.cta_title": "To‘liq xarakter profilingizni oching",
        "result.cta_desc": (
            "Kuchli va zaif tomonlaringiz, sizga mos kasblar, ish uslubingiz va "
            "shaxsiy rivojlanish yo‘nalishlarini ko‘ring."
        ),
        "result.cta_note": "To‘lov tasdiqlangach natija shu sahifada ochiladi.",
        "result.open_premium": "Premium natijani ochish",
        "result.restart": "Testni qayta ishlash",
        "result.currency": "so‘m",
        # To‘lov modali
        "payment.title": "To‘lovni amalga oshiring",
        "payment.close": "Yopish",
        "payment.card_number": "Karta raqami",
        "payment.card_holder": "Qabul qiluvchi",
        "payment.amount": "To‘lov summasi",
        "payment.test_code": "Test kodi",
        "payment.copy": "Nusxalash",
        "payment.copied": "Nusxalandi",
        "payment.copy_failed": "Nusxalanmadi — qo‘lda belgilang",
        "payment.step_1": "{price} so‘m to‘lov qiling.",
        "payment.step_2": (
            "«Chekni Telegram orqali yuborish» tugmasini bosing — havola botni shu test bilan bog‘laydi."
        ),
        "payment.step_3": "Botga chek rasmini yuboring.",
        "payment.step_4": "Bot testni topa olmasa, test kodini matn sifatida yuboring.",
        "payment.telegram_button": "Chekni Telegram orqali yuborish",
        "payment.unavailable": (
            "To‘lov xizmati vaqtincha mavjud emas. Keyinroq urinib ko‘ring yoki "
            "administrator bilan bog‘laning."
        ),
        # Munosabat testi (placeholder)
        "relationship.title": "Munosabat testi",
        "relationship.text": ("Bu bo‘lim tayyorlanmoqda. Xarakter testi alohida mahsulot sifatida ishlaydi."),
        "relationship.cta": "Xarakter testiga o‘tish",
        # Xato sahifalari
        "errors.retry": "Qayta urinish",
        "errors.help_404": "Manzilni tekshiring yoki bosh sahifadan qaytadan boshlang.",
        "errors.help_500": "Xatolik bizning tomonda. Bir necha daqiqadan so‘ng qayta urinib ko‘ring.",
        # Admin
        "admin.status.all": "Hammasi",
        "admin.status.pending": "Kutilmoqda",
        "admin.status.receipt_sent": "Chek yuborilgan",
        "admin.status.approved": "Tasdiqlangan",
        "admin.status.rejected": "Rad etilgan",
        "admin.reject_confirm": "Bu to‘lovni rad etasizmi? Foydalanuvchi premiumni ololmaydi.",
        "admin.pagination.aria": "Sahifalar",
        "admin.pagination.prev": "Oldingi",
        "admin.pagination.next": "Keyingi",
        "admin.pagination.summary": "{first}–{last} / {total} ta",
        "admin.receipt.view": "Chekni ochish",
        "admin.receipt.alt": "Yuborilgan chek",
        "admin.receipt.none": "Chek yo‘q",
    },
    "ru": {
        # Общее
        "site.name": "Тест характера",
        "site.title_default": "Тест характера",
        "site.description": (
            "За 4 минуты узнайте сильные стороны своего характера, причины падения "
            "мотивации и подходящий вам стиль работы и общения."
        ),
        "common.no_wrong_answer": "Правильных и неправильных ответов нет.",
        "common.back_home": "Вернуться на главную",
        "common.logo_alt": "Логотип теста характера",
        "lang.label": "Язык",
        # Лендинг
        "landing.title": "Тест характера и стиля жизни",
        "landing.eyebrow": "ТЕСТ ХАРАКТЕРА И СТИЛЯ ЖИЗНИ",
        "landing.headline": "Вы не ленивы",
        "landing.lead": "Возможно, вы просто действуете способом, который вам не подходит.",
        "landing.copy": (
            "Определите сильные стороны своего характера, причины падения мотивации "
            "и подходящий вам стиль работы и общения."
        ),
        "landing.meta_aria": "О тесте",
        "landing.meta_questions": "24 вопроса",
        "landing.meta_minutes": "4 минуты",
        "landing.meta_personal": "Личный результат",
        "landing.cta": "Узнать свой характер",
        "landing.hero_alt": "Тест на понимание характера",
        # Инструкция
        "instructions.title": "Перед тестом",
        "instructions.text": (
            "Отвечайте не так, как вам хотелось бы поступать, а так, как вы обычно поступаете на самом деле."
        ),
        "instructions.gender_group": "Выберите пол",
        "instructions.female": "Женщина",
        "instructions.male": "Мужчина",
        "instructions.start": "Начать тест",
        # Вопрос
        "question.title": "Вопрос {current} / {total}",
        "question.back": "Назад",
        "question.next": "Далее",
        "question.see_result": "Посмотреть результат",
        "question.progress_aria": "Этап теста",
        # Загрузка
        "loading.title": "Результат готовится",
        "loading.spinner_aria": "Идёт анализ",
        "loading.step_1": "Анализируем ваши сильные стороны",
        "loading.step_2": "Определяем подходящий вам стиль работы",
        "loading.step_3": "Готовим особенности вашего общения",
        "loading.open_result": "Открыть результат",
        # Ошибка загрузки вопросов
        "questions_error.title": "Вопросы не загрузились",
        "questions_error.text": "Не удалось загрузить вопросы. Пожалуйста, попробуйте ещё раз.",
        "questions_error.retry": "Попробовать снова",
        # Результат
        "result.eyebrow_before": "Ваш тип характера ближе всего к",
        "result.eyebrow_after": ".",
        "result.type_label": "Тип:",
        "result.disclaimer": (
            "Результат показывает наиболее близкое вам направление характера. "
            "Это не медицинский и не психологический диагноз."
        ),
        "result.strengths": "Сильные стороны",
        "result.challenges": "Сложные стороны",
        "result.public_view": "Каким вас могут видеть окружающие",
        "result.dimensions": "Шкалы",
        "result.premium_headline": ("Вы узнали свой характер. Теперь узнайте, как им пользоваться."),
        "result.premium_opened": "Премиум-профиль открыт",
        "result.section.motivation": "Почему падает ваша мотивация?",
        "result.section.work_style": "Подходящий вам стиль работы",
        "result.section.career": "Подходящая профессия и среда",
        "result.section.friendship": "Какой вы друг?",
        "result.section.relationship": "Какой партнёр вам подходит?",
        "result.section.compatible_people": "Люди, которые вам подходят",
        "result.section.difficult": "С кем общение даётся сложнее?",
        "result.section.action_plan": "Личный план на 7 дней",
        "result.locked_note": "Премиум-анализ — откроется после подтверждения оплаты.",
        "result.status_pending_title": "Оплата проверяется",
        "result.status_pending_text": (
            "Ваш чек отправлен администратору. После подтверждения откроется премиум-результат."
        ),
        "result.status_awaiting_title": "Ожидается чек",
        "result.status_awaiting_text": ("Оплатите и отправьте фото чека через Telegram-бот."),
        "result.test_code_label": "Код теста:",
        "result.refresh_status": "Обновить статус",
        "result.cta_title": "Откройте полный профиль характера",
        "result.cta_desc": (
            "Посмотрите свои сильные и слабые стороны, подходящие профессии, "
            "стиль работы и направления личного развития."
        ),
        "result.cta_note": "После подтверждения оплаты результат откроется на этой странице.",
        "result.open_premium": "Открыть премиум-результат",
        "result.restart": "Пройти тест заново",
        "result.currency": "сум",
        # Модальное окно оплаты
        "payment.title": "Выполните оплату",
        "payment.close": "Закрыть",
        "payment.card_number": "Номер карты",
        "payment.card_holder": "Получатель",
        "payment.amount": "Сумма оплаты",
        "payment.test_code": "Код теста",
        "payment.copy": "Копировать",
        "payment.copied": "Скопировано",
        "payment.copy_failed": "Не скопировалось — выделите вручную",
        "payment.step_1": "Оплатите {price} сум.",
        "payment.step_2": "Нажмите «Отправить чек через Telegram» — ссылка свяжет бота с этим тестом.",
        "payment.step_3": "Отправьте боту фото чека.",
        "payment.step_4": "Если бот не найдёт тест, отправьте код теста текстом.",
        "payment.telegram_button": "Отправить чек через Telegram",
        "payment.unavailable": (
            "Сервис оплаты временно недоступен. Попробуйте позже или свяжитесь с администратором."
        ),
        # Тест отношений (заглушка)
        "relationship.title": "Тест отношений",
        "relationship.text": ("Этот раздел готовится. Тест характера работает как отдельный продукт."),
        "relationship.cta": "Перейти к тесту характера",
        # Страницы ошибок
        "errors.retry": "Попробовать снова",
        "errors.help_404": "Проверьте адрес или начните заново с главной страницы.",
        "errors.help_500": "Ошибка на нашей стороне. Попробуйте снова через несколько минут.",
        # Админка
        "admin.status.all": "Все",
        "admin.status.pending": "Ожидает",
        "admin.status.receipt_sent": "Чек отправлен",
        "admin.status.approved": "Подтверждено",
        "admin.status.rejected": "Отклонено",
        "admin.reject_confirm": "Отклонить этот платёж? Пользователь не получит премиум.",
        "admin.pagination.aria": "Страницы",
        "admin.pagination.prev": "Назад",
        "admin.pagination.next": "Далее",
        "admin.pagination.summary": "{first}–{last} из {total}",
        "admin.receipt.view": "Открыть чек",
        "admin.receipt.alt": "Отправленный чек",
        "admin.receipt.none": "Чека нет",
    },
}


def normalize_lang(value: str | None) -> str | None:
    if not value:
        return None
    code = value.strip().lower().replace("_", "-").split("-", 1)[0]
    return code if code in SUPPORTED else None


def _from_accept_language(header: str | None) -> str | None:
    """Accept-Language: sifat ko'rsatkichi bo'yicha eng yuqori mos tilni tanlaydi."""
    if not header:
        return None
    best: tuple[float, str] | None = None
    for chunk in header.split(","):
        parts = chunk.split(";")
        code = normalize_lang(parts[0])
        if not code:
            continue
        quality = 1.0
        for param in parts[1:]:
            key, _, raw = param.partition("=")
            if key.strip() == "q":
                try:
                    quality = float(raw)
                except ValueError:
                    quality = 0.0
        if best is None or quality > best[0]:
            best = (quality, code)
    return best[1] if best else None


def resolve_lang(request: Request) -> str:
    """?lang= → cookie → Accept-Language → DEFAULT."""
    return (
        normalize_lang(request.query_params.get(LANG_QUERY_KEY))
        or normalize_lang(request.cookies.get(LANG_COOKIE_KEY))
        or _from_accept_language(request.headers.get("accept-language"))
        or DEFAULT
    )


def t(key: str, lang: str, **kwargs: Any) -> str:
    """Kalit bo'yicha matn; til yoki kalit topilmasa DEFAULT, so'ng kalitning o'zi."""
    catalog = TRANSLATIONS.get(lang) or TRANSLATIONS[DEFAULT]
    text = catalog.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT].get(key, key)
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        # Tarjimada noto'g'ri joker bo'lsa sahifa yiqilmasin.
        return text


def language_links(request: Request, current: str) -> list[dict[str, str | bool]]:
    """Til almashtirgich uchun: joriy manzilga ?lang=... qo'shilgan havolalar."""
    params = [(k, v) for k, v in request.query_params.multi_items() if k != LANG_QUERY_KEY]
    links: list[dict[str, str | bool]] = []
    for code in SUPPORTED:
        query = urlencode([*params, (LANG_QUERY_KEY, code)])
        links.append(
            {
                "code": code,
                "name": LANGUAGE_NAMES[code],
                "short": LANGUAGE_SHORT[code],
                "url": f"{request.url.path}?{query}",
                "active": code == current,
            }
        )
    return links
