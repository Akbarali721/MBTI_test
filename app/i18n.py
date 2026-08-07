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
        # O'lchov qutblari (scoring moduli sof qoladi, nomlar shu yerda tarjima qilinadi)
        "dimension.i": "Introvert (I)",
        "dimension.e": "Ekstravert (E)",
        "dimension.s": "Sensor (S)",
        "dimension.n": "Intuitiv (N)",
        "dimension.t": "Mantiqiy (T)",
        "dimension.f": "Hisliy (F)",
        "dimension.j": "Rejalovchi (J)",
        "dimension.p": "Improvisatsiya (P)",
        # Ulashish
        "share.box_title": "Natijani ulashing",
        "share.box_desc": (
            "Quyidagi havola faqat xarakter tipingizni va o‘lchovlaringizni ko‘rsatadi — "
            "premium tahlil va shaxsiy ma’lumotlar unda bo‘lmaydi."
        ),
        "share.box_note": "Havolani istalgan vaqtda yuboring; u muddatsiz ishlaydi.",
        "share.via_telegram": "Telegramda ulashish",
        "share.eyebrow": "Xarakter testi natijasi",
        "share.page_title": "{type} — {title}",
        "share.og_title": "Mening xarakter tipim: {type} — {title}",
        "share.cta_title": "O‘zingiznikini bilib oling",
        "share.cta_desc": "24 ta savol, taxminan 4 daqiqa. Ro‘yxatdan o‘tish shart emas.",
        "share.cta_button": "Testni boshlash",
        # Tarix
        "history.link": "Oldingi natijalar ({count})",
        "history.page_title": "Test tarixi",
        "history.title": "Test tarixingiz",
        "history.intro": "Shu brauzerda {count} ta tugallangan test bor.",
        "history.empty": "Hozircha tugallangan test yo‘q.",
        "history.empty_cta": "Testni boshlash",
        "history.open_result": "Natijani ochish",
        "history.premium_badge": "Premium",
        "history.shift_title": "Nima o‘zgardi",
        "history.shift_desc": "Birinchi va oxirgi urinishingiz orasidagi farq.",
        "history.shift_stable": "o‘zgarmadi",
        "history.retake": "Testni qayta ishlash",
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
        # Juftlik mosligi
        "compat.page_title": "Juftlik mosligi",
        "compat.page_desc": (
            "Ikki xarakter tipini solishtiring: qayerda o‘xshaysiz, qayerda bir-biringizni to‘ldirasiz."
        ),
        "compat.eyebrow": "Juftlik mosligi",
        "compat.title": "Ikkingiz bir-biringizga qanchalik mos?",
        "compat.intro": (
            "O‘z tipingizni va sherigingiznikini tanlang. Natija to‘rt o‘lchov bo‘yicha "
            "o‘xshashlik va to‘ldiruvchanlikni ko‘rsatadi."
        ),
        "compat.your_type": "Sizning tipingiz",
        "compat.partner_type": "Sherigingiz tipi",
        "compat.choose": "Tanlang",
        "compat.submit": "Solishtirish",
        "compat.error_invalid": "Ikkala tipni ham ro‘yxatdan tanlang.",
        "compat.unknown_type": "Tipingizni bilmaysizmi?",
        "compat.take_test": "Testni topshirish",
        "compat.disclaimer": (
            "Bu tahlil qoidalarga asoslangan izoh, ilmiy o‘lchov emas. Hech bir juftlik "
            "«mos emas» degan xulosa chiqarilmaydi — faqat kuch va ishqalanish nuqtalari ko‘rsatiladi."
        ),
        "compat.result_title": "{left} va {right} — juftlik mosligi",
        "compat.og_title": "{left} + {right}: moslik {score}%",
        "compat.by_dimension": "O‘lchovlar bo‘yicha",
        "compat.same": "O‘xshash",
        "compat.different": "Farqli",
        "compat.strengths": "Nima ishlaydi",
        "compat.frictions": "Qayerda ishqalanish bo‘lishi mumkin",
        "compat.advice": "Nima qilish kerak",
        "compat.compare_another": "Boshqa juftlikni solishtirish",
        "compat.result_cta": "Juftlik mosligini tekshirish",
        # Jamoa / HR rejimi
        "team.eyebrow": "Jamoa rejimi",
        "team.page_title": "Jamoa tahlili",
        "team.page_desc": (
            "Xodimlaringiz xarakter tiplarini bitta panelda ko‘ring va jamoa tarkibidagi bo‘shliqlarni "
            "aniqlang."
        ),
        "team.title": "Jamoangiz qanday tuzilgan?",
        "team.intro": (
            "Jamoa yarating, taklif havolasini xodimlarga yuboring — natijalar bitta panelda yig‘iladi."
        ),
        "team.name_label": "Jamoa nomi",
        "team.name_placeholder": "Masalan: Marketing bo‘limi",
        "team.create": "Jamoa yaratish",
        "team.step_1": "Jamoa nomini kiriting va yarating.",
        "team.step_2": "Taklif havolasini xodimlarga yuboring — ular testni topshiradi.",
        "team.step_3": "Panelda tarkib, muvozanat va bo‘shliqlarni ko‘ring.",
        "team.privacy_note": (
            "Panelga faqat boshqaruv havolasi bilan kiriladi. Uni saqlab qo‘ying — tiklash imkoni yo‘q."
        ),
        "team.error_empty_name": "Jamoa nomini kiriting.",
        "team.error_full": "Jamoa to‘lgan — yangi a’zo qo‘shib bo‘lmaydi.",
        "team.dashboard_title": "{team} — jamoa paneli",
        "team.invite_title": "Taklif havolasi",
        "team.invite_desc": (
            "Shu havolani xodimlarga yuboring. U faqat jamoaga qo‘shilish uchun, panelni ochmaydi."
        ),
        "team.manage_note": "Brauzer manzilidagi boshqaruv havolasini hech kimga bermang.",
        "team.stat_members": "A’zo",
        "team.stat_types": "Turli tip",
        "team.empty": "Hozircha hech kim qo‘shilmagan. Taklif havolasini yuboring.",
        "team.balance_title": "O‘lchovlar muvozanati",
        "team.insight_title": "E’tibor bering",
        "team.insight_skew": (
            "Jamoa {pole} tomonga sezilarli qiyshaygan — qarama-qarshi yondashuv yetishmasligi mumkin."
        ),
        "team.insight_missing": "Jamoada {pole} umuman yo‘q — bu ko‘r nuqta bo‘lishi mumkin.",
        "team.types_title": "Tiplar taqsimoti",
        "team.members_title": "A’zolar",
        "team.disclaimer": (
            "Bu tahlil jamoa tarkibini tushunish uchun; kadrlar bo‘yicha qaror uchun yagona asos bo‘la "
            "olmaydi."
        ),
        "team.join_title": "{team} jamoasiga qo‘shilish",
        "team.join_ready": "Sizning tipingiz: {type}. Panelda ko‘rinadigan ismni kiriting.",
        "team.your_name": "Ismingiz",
        "team.your_name_placeholder": "Masalan: Dilnoza",
        "team.join_button": "Jamoaga qo‘shilish",
        "team.join_privacy": (
            "Jamoa egasi faqat ismingizni va xarakter tipingizni ko‘radi — javoblaringizni emas."
        ),
        "team.join_needs_test": "Jamoaga qo‘shilish uchun avval testni tugating.",
        "team.take_test": "Testni boshlash",
        "team.join_return_hint": "Test tugagach shu havolaga qayting.",
        "team.joined_title": "Qo‘shildingiz",
        "team.joined_text": "Natijangiz «{team}» jamoasi paneliga qo‘shildi.",
        # PDF hisobot
        "pdf.generated": "Hisobot tayyorlangan sana:",
        "pdf.download": "PDF hisobotni yuklab olish",
        "compat.band_high": "Yuqori moslik",
        "compat.band_high_short": "Moslik {score}% — tabiiy tushunish.",
        "compat.band_high_desc": (
            "Siz dunyoni o‘xshash ko‘rasiz va o‘xshash sur’atda yashaysiz. Bunday juftlikda "
            "asosiy xavf — bir xil ko‘r nuqtalar: ikkalangiz ham e’tibor bermaydigan narsalar bo‘ladi."
        ),
        "compat.band_medium": "Yaxshi moslik",
        "compat.band_medium_short": "Moslik {score}% — o‘xshashlik ham, to‘ldiruvchanlik ham bor.",
        "compat.band_medium_desc": (
            "Ba’zi o‘lchovlarda o‘xshaysiz, ba’zilarida bir-biringizni to‘ldirasiz. Bu ko‘pincha "
            "eng barqaror kombinatsiya: yetarlicha umumiylik ham, yetarlicha yangilik ham bor."
        ),
        "compat.band_growing": "Rivojlanadigan moslik",
        "compat.band_growing_short": "Moslik {score}% — farqlar ko‘p, lekin ular to‘siq emas.",
        "compat.band_growing_desc": (
            "Siz ko‘p narsani turlicha qilasiz. Bu juftlik ishlamaydi degani emas — shunchaki "
            "kelishuvni ochiq aytib qo‘yish kerak bo‘ladi, chunki u o‘z-o‘zidan yuzaga kelmaydi."
        ),
        # O'lchovlar bo'yicha izoh
        "compat.ei.same_e": "Ikkalangiz ham odamlar orasida quvvat olasiz — birga chiqish oson.",
        "compat.ei.same_i": (
            "Ikkalangiz ham tinchlikni qadrlaysiz — yolg‘iz vaqtni tushuntirish shart emas."
        ),
        "compat.ei.diff": (
            "Biringiz muloqotdan quvvat olasiz, ikkinchingiz tinchlikdan — bu bir-biringizni muvozanatlaydi."
        ),
        "compat.sn.same_s": "Ikkalangiz ham aniq faktlar va amaliy tafsilotlarga tayanasiz.",
        "compat.sn.same_n": "Ikkalangiz ham g‘oya va imkoniyatlar tilida gaplashasiz.",
        "compat.sn.diff": (
            "Biringiz aniqlikka, ikkinchingiz g‘oyaga qaraysiz — bu eng ko‘p tushunmovchilik "
            "tug‘diradigan farq."
        ),
        "compat.tf.same_t": ("Ikkalangiz ham qarorni mantiq bilan olasiz — bahs shaxsiy qabul qilinmaydi."),
        "compat.tf.same_f": "Ikkalangiz ham odamlarning hissiyotini hisobga olasiz.",
        "compat.tf.diff": (
            "Biringiz mantiqqa, ikkinchingiz hissiyotga tayanadi — qaror sifati oshadi, lekin nizoda "
            "uslub farq qiladi."
        ),
        "compat.jp.same_j": "Ikkalangiz ham reja va aniqlikni yoqtirasiz — kelishish oson.",
        "compat.jp.same_p": "Ikkalangiz ham moslashuvchansiz — qattiq jadval kerak emas.",
        "compat.jp.diff": (
            "Biri rejalashtiradi, ikkinchisi moslashadi — kundalik hayotda eng ko‘p seziladigan farq shu."
        ),
        # Kuchli tomonlar
        "compat.strength.ei_same": "Dam olish va muloqot sur’ati bir xil — kelishuv talab qilmaydi.",
        "compat.strength.sn_same": (
            "Bir-biringizni yarim so‘zdan tushunasiz: axborotni bir xil qayta ishlaysiz."
        ),
        "compat.strength.tf_same": "Qaror qabul qilish mezoni bir xil — muhim tanlovlarda tez kelishasiz.",
        "compat.strength.jp_same": "Vaqt va tartibga munosabat bir xil — kundalik ishqalanish kam.",
        "compat.strength.all_diff": (
            "Hamma o‘lchovda farq qilasiz — bu juftlikda o‘rganadigan narsa ko‘p, "
            "chunki har biringiz ikkinchisining ko‘r nuqtasini ko‘rasiz."
        ),
        # Ishqalanish
        "compat.friction.ei": "Dam olish usuli farq qiladi: biriga odam kerak, ikkinchisiga tinchlik.",
        "compat.friction.sn": "Suhbatda biriga tafsilot, ikkinchisiga umumiy manzara kerak bo‘ladi.",
        "compat.friction.tf": "Nizoda biri yechim izlaydi, ikkinchisi avval eshitilishni kutadi.",
        "compat.friction.jp": "Reja va o‘z-o‘zidan bo‘lish o‘rtasidagi tortishuv takrorlanib turadi.",
        # Maslahat
        "compat.advice.ei": (
            "Birgalikdagi vaqt bilan yolg‘iz vaqtni oldindan kelishib oling — ikkalasi ham normal."
        ),
        "compat.advice.sn": (
            "Muhim suhbatda avval umumiy manzarani, keyin tafsilotni ayting — ikkalangiz ham yetib boradi."
        ),
        "compat.advice.tf": "Nizo boshlanganda so‘rang: hozir yechim kerakmi yoki eshitilish kerakmi?",
        "compat.advice.jp": (
            "Reja kerak bo‘lgan joyni va erkin qoldiriladigan joyni oldindan ajratib qo‘ying."
        ),
        "compat.advice.identical": (
            "Barcha o‘lchovda bir xilsiz. Kuchli tomoni — tushunish oson; xavfi — ko‘r nuqtalar ham bir xil. "
            "Muhim qarorlarda ataylab tashqi fikr so‘rang."
        ),
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
        "admin.funnel.visited": "Tashrif",
        "admin.funnel.started": "Test boshlandi",
        "admin.funnel.completed": "Test tugatildi",
        "admin.funnel.payment_started": "To‘lov so‘rovi ochildi",
        "admin.funnel.receipt_sent": "Chek yuborildi",
        "admin.funnel.approved": "Tasdiqlandi",
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
        # Полюса шкал
        "dimension.i": "Интроверт (I)",
        "dimension.e": "Экстраверт (E)",
        "dimension.s": "Сенсорик (S)",
        "dimension.n": "Интуит (N)",
        "dimension.t": "Логик (T)",
        "dimension.f": "Этик (F)",
        "dimension.j": "Планирующий (J)",
        "dimension.p": "Импровизирующий (P)",
        # Поделиться
        "share.box_title": "Поделитесь результатом",
        "share.box_desc": (
            "Ссылка ниже показывает только ваш тип характера и шкалы — "
            "премиум-разбор и личные данные в неё не попадают."
        ),
        "share.box_note": "Отправляйте ссылку когда угодно — она работает бессрочно.",
        "share.via_telegram": "Поделиться в Telegram",
        "share.eyebrow": "Результат теста характера",
        "share.page_title": "{type} — {title}",
        "share.og_title": "Мой тип характера: {type} — {title}",
        "share.cta_title": "Узнайте свой",
        "share.cta_desc": "24 вопроса, около 4 минут. Регистрация не нужна.",
        "share.cta_button": "Начать тест",
        # История
        "history.link": "Прошлые результаты ({count})",
        "history.page_title": "История тестов",
        "history.title": "История ваших тестов",
        "history.intro": "В этом браузере {count} завершённых теста.",
        "history.empty": "Пока нет завершённых тестов.",
        "history.empty_cta": "Начать тест",
        "history.open_result": "Открыть результат",
        "history.premium_badge": "Премиум",
        "history.shift_title": "Что изменилось",
        "history.shift_desc": "Разница между первой и последней попыткой.",
        "history.shift_stable": "без изменений",
        "history.retake": "Пройти тест заново",
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
        # Совместимость пары
        "compat.page_title": "Совместимость пары",
        "compat.page_desc": "Сравните два типа характера: где вы похожи, а где дополняете друг друга.",
        "compat.eyebrow": "Совместимость пары",
        "compat.title": "Насколько вы подходите друг другу?",
        "compat.intro": (
            "Выберите свой тип и тип партнёра. Результат покажет сходство и "
            "взаимодополняемость по четырём шкалам."
        ),
        "compat.your_type": "Ваш тип",
        "compat.partner_type": "Тип партнёра",
        "compat.choose": "Выберите",
        "compat.submit": "Сравнить",
        "compat.error_invalid": "Выберите оба типа из списка.",
        "compat.unknown_type": "Не знаете свой тип?",
        "compat.take_test": "Пройти тест",
        "compat.disclaimer": (
            "Это разбор на основе правил, а не научное измерение. Ни одна пара не получает "
            "вывод «не подходите» — показываются только точки силы и трения."
        ),
        "compat.result_title": "{left} и {right} — совместимость пары",
        "compat.og_title": "{left} + {right}: совместимость {score}%",
        "compat.by_dimension": "По шкалам",
        "compat.same": "Схожи",
        "compat.different": "Различны",
        "compat.strengths": "Что работает",
        "compat.frictions": "Где возможно трение",
        "compat.advice": "Что делать",
        "compat.compare_another": "Сравнить другую пару",
        "compat.result_cta": "Проверить совместимость пары",
        # Командный / HR-режим
        "team.eyebrow": "Командный режим",
        "team.page_title": "Анализ команды",
        "team.page_desc": (
            "Посмотрите типы характера сотрудников в одной панели и найдите пробелы в составе команды."
        ),
        "team.title": "Как устроена ваша команда?",
        "team.intro": (
            "Создайте команду и отправьте сотрудникам ссылку-приглашение — результаты соберутся в одной "
            "панели."
        ),
        "team.name_label": "Название команды",
        "team.name_placeholder": "Например: Отдел маркетинга",
        "team.create": "Создать команду",
        "team.step_1": "Введите название команды и создайте её.",
        "team.step_2": "Отправьте ссылку-приглашение сотрудникам — они пройдут тест.",
        "team.step_3": "Смотрите состав, баланс и пробелы в панели.",
        "team.privacy_note": (
            "В панель можно войти только по ссылке управления. Сохраните её — восстановить нельзя."
        ),
        "team.error_empty_name": "Введите название команды.",
        "team.error_full": "Команда заполнена — добавить участника нельзя.",
        "team.dashboard_title": "{team} — панель команды",
        "team.invite_title": "Ссылка-приглашение",
        "team.invite_desc": (
            "Отправьте эту ссылку сотрудникам. Она только для вступления и не открывает панель."
        ),
        "team.manage_note": "Никому не передавайте ссылку управления из адресной строки.",
        "team.stat_members": "Участников",
        "team.stat_types": "Разных типов",
        "team.empty": "Пока никто не присоединился. Отправьте ссылку-приглашение.",
        "team.balance_title": "Баланс шкал",
        "team.insight_title": "Обратите внимание",
        "team.insight_skew": (
            "Команда заметно смещена в сторону «{pole}» — может не хватать противоположного подхода."
        ),
        "team.insight_missing": "В команде совсем нет «{pole}» — это возможная слепая зона.",
        "team.types_title": "Распределение типов",
        "team.members_title": "Участники",
        "team.disclaimer": (
            "Этот разбор помогает понять состав команды и не может быть единственным основанием для "
            "кадровых решений."
        ),
        "team.join_title": "Присоединиться к команде «{team}»",
        "team.join_ready": "Ваш тип: {type}. Введите имя, которое увидят в панели.",
        "team.your_name": "Ваше имя",
        "team.your_name_placeholder": "Например: Дильноза",
        "team.join_button": "Присоединиться",
        "team.join_privacy": "Владелец команды видит только ваше имя и тип характера — не ваши ответы.",
        "team.join_needs_test": "Чтобы присоединиться, сначала пройдите тест.",
        "team.take_test": "Начать тест",
        "team.join_return_hint": "После теста вернитесь по этой ссылке.",
        "team.joined_title": "Вы присоединились",
        "team.joined_text": "Ваш результат добавлен в панель команды «{team}».",
        # PDF-отчёт
        "pdf.generated": "Отчёт сформирован:",
        "pdf.download": "Скачать PDF-отчёт",
        "compat.band_high": "Высокая совместимость",
        "compat.band_high_short": "Совместимость {score}% — понимание даётся легко.",
        "compat.band_high_desc": (
            "Вы похоже смотрите на мир и живёте в похожем ритме. Главный риск такой пары — "
            "одинаковые слепые зоны: есть вещи, которых не заметит ни один из вас."
        ),
        "compat.band_medium": "Хорошая совместимость",
        "compat.band_medium_short": "Совместимость {score}% — есть и сходство, и взаимодополнение.",
        "compat.band_medium_desc": (
            "По одним шкалам вы похожи, по другим дополняете друг друга. Часто это самая "
            "устойчивая комбинация: достаточно общего и достаточно нового."
        ),
        "compat.band_growing": "Совместимость, требующая работы",
        "compat.band_growing_short": "Совместимость {score}% — различий много, но они не преграда.",
        "compat.band_growing_desc": (
            "Многое вы делаете по-разному. Это не значит, что пара не работает — просто "
            "договорённости придётся проговаривать вслух, сами собой они не возникнут."
        ),
        # Пояснения по шкалам
        "compat.ei.same_e": "Оба набираетесь энергии среди людей — выходить вместе легко.",
        "compat.ei.same_i": "Оба цените тишину — время наедине не нужно объяснять.",
        "compat.ei.diff": "Один заряжается общением, другой тишиной — это уравновешивает вас.",
        "compat.sn.same_s": "Оба опираетесь на факты и практические детали.",
        "compat.sn.same_n": "Оба говорите на языке идей и возможностей.",
        "compat.sn.diff": (
            "Один смотрит на конкретику, другой на идею — это различие чаще всего рождает недопонимание."
        ),
        "compat.tf.same_t": "Оба решаете логикой — спор не воспринимается как личное.",
        "compat.tf.same_f": "Оба учитываете чувства людей.",
        "compat.tf.diff": (
            "Один опирается на логику, другой на чувства — качество решений растёт, но стиль в конфликте "
            "разный."
        ),
        "compat.jp.same_j": "Оба любите план и определённость — договориться просто.",
        "compat.jp.same_p": "Оба гибкие — жёсткий график не нужен.",
        "compat.jp.diff": "Один планирует, другой подстраивается — в быту это заметно чаще всего.",
        # Сильные стороны
        "compat.strength.ei_same": "Ритм отдыха и общения совпадает — не требует переговоров.",
        "compat.strength.sn_same": "Понимаете друг друга с полуслова: одинаково обрабатываете информацию.",
        "compat.strength.tf_same": "Критерий принятия решений один — в важном выборе договариваетесь быстро.",
        "compat.strength.jp_same": "Отношение к времени и порядку совпадает — бытового трения мало.",
        "compat.strength.all_diff": (
            "Вы различаетесь по всем шкалам — в такой паре многому учатся, "
            "потому что каждый видит слепую зону другого."
        ),
        # Трение
        "compat.friction.ei": "Способ восстановиться разный: одному нужны люди, другому тишина.",
        "compat.friction.sn": "В разговоре одному нужны детали, другому общая картина.",
        "compat.friction.tf": "В конфликте один ищет решение, другой сначала ждёт, что его услышат.",
        "compat.friction.jp": "Спор между планом и спонтанностью будет возвращаться.",
        # Советы
        "compat.advice.ei": (
            "Заранее договоритесь о времени вместе и времени наедине — нормально и то, и другое."
        ),
        "compat.advice.sn": ("В важном разговоре сначала общая картина, потом детали — так дойдёт до обоих."),
        "compat.advice.tf": ("В начале конфликта спросите: сейчас нужно решение или нужно, чтобы выслушали?"),
        "compat.advice.jp": "Заранее разделите, где нужен план, а где остаётся свобода.",
        "compat.advice.identical": (
            "Вы совпадаете по всем шкалам. Сила — лёгкое понимание; риск — слепые зоны тоже общие. "
            "В важных решениях намеренно спрашивайте взгляд со стороны."
        ),
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
        "admin.funnel.visited": "Визит",
        "admin.funnel.started": "Тест начат",
        "admin.funnel.completed": "Тест завершён",
        "admin.funnel.payment_started": "Заявка на оплату",
        "admin.funnel.receipt_sent": "Чек отправлен",
        "admin.funnel.approved": "Подтверждено",
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
