"""Kundalik o‘zbekcha vaziyatlarga moslangan 24 ta MBTI uslubidagi savol.

Tahrir: 2026-09-19. Bu savollar sinov uchun yozilgan; mahalliy auditoriyada
psixometrik tekshiruvdan o‘tgan so‘rovnoma sifatida taqdim etilmaydi.

Mavjud import, ro‘yxat nomi, tuple tuzilishi va o‘lchovlar tartibi saqlangan.
Har o‘lchovga 6 savol, har savolga 4 javob berilgan. Javoblarning mazmuniy
yo‘nalishi E -> I, S -> N, T -> F, J -> P tartibida: avval birinchi tomonga
kuchliroq, keyin yumshoqroq; so‘ng ikkinchi tomonga yumshoqroq va kuchliroq.
Haqiqiy ball og‘irliklari bu faylda emas; integratsiyada ularni tekshirish kerak.

Eski izohga ko‘ra, `app/seed/personality_placeholders.py` bankni qarama-qarshi
juftlar bilan 48 taga kengaytiradi. U fayl bu tahrirda ko‘rilmagan. Asl savol va
uning mazmunan takror juftini bitta sessiyaga tushirmaslik tanlash kodida
tekshiriladi; bu faylning o‘zi tanlash tartibini o‘zgartirmaydi.
"""

from app.models.enums import PersonalityDimension

# (savol matni, dimension, 4 ta javob matni)
PERSONALITY_QUESTIONS_UZ: list[tuple[str, PersonalityDimension, list[str]]] = [
    (
        "Majburiy ishlaringiz tugadi, bir soat bo‘sh vaqtingiz bor. Uni qanday o‘tkazishni xohlaysiz?",
        PersonalityDimension.EI,
        [
            "Butun vaqtni do‘stlar bilan suhbatlashib",
            "Ko‘proq suhbatlashib, ozgina yolg‘iz dam olib",
            "Ko‘proq yolg‘iz dam olib, ozgina suhbatlashib",
            "Butun vaqtni yolg‘iz, yoqtirgan mashg‘ulotim bilan",
        ],
    ),
    (
        "Do‘stingizning davrasida notanish tengdoshlaringiz bor. Suhbatga odatda qanday qo‘shilasiz?",
        PersonalityDimension.EI,
        [
            "Odatda birinchi bo‘lib gap boshlayman",
            "Ko‘proq o‘zim gap boshlayman, ba’zan kutaman",
            "Ko‘proq boshqalar boshlashini kutaman, ba’zan o‘zim boshlayman",
            "Odatda boshqalar gap boshlagach qo‘shilaman",
        ],
    ),
    (
        "Xayolingizga yangi g‘oya keldi. Uni o‘zingiz uchun aniqlashtirishga nima yordam beradi?",
        PersonalityDimension.EI,
        [
            "Birov bilan gaplashish davomida fikrimni shakllantirish",
            "Ko‘proq muhokama qilish, keyin o‘zim o‘ylash",
            "Ko‘proq o‘zim o‘ylash, keyin muhokama qilish",
            "Avval yolg‘iz o‘ylab, fikrimni shakllantirish",
        ],
    ),
    (
        "Siz kutgan yaxshi xabar keldi. Uni yaqinlaringizga qachon aytgingiz keladi?",
        PersonalityDimension.EI,
        [
            "Darhol aytib, quvonchimni bo‘lishgim keladi",
            "Odatda tezroq aytaman, ba’zan o‘zim uchun vaqt ajrataman",
            "Odatda avval o‘zim quvonaman, keyin aytaman",
            "Avval ancha vaqt o‘zim his qilib, keyin bo‘lishgim keladi",
        ],
    ),
    (
        "Yoqtirgan mavzuingizni o‘rganishda guruh bilan ham, mustaqil ham ishlash mumkin. Qaysi muhit sizga qulayroq?",
        PersonalityDimension.EI,
        [
            "Asosan guruh bilan birga o‘rganish",
            "Ko‘proq guruh bilan, ayrim qismlarini mustaqil o‘rganish",
            "Ko‘proq mustaqil, ayrim qismlarini guruh bilan o‘rganish",
            "Asosan mustaqil o‘rganish",
        ],
    ),
    (
        "Uchrashuvga kimlarni chaqirishni o‘zingiz tanlaysiz. Sizga qanday davra yoqimliroq?",
        PersonalityDimension.EI,
        [
            "Turli tanishlarim qatnashadigan katta davra",
            "Kichik davradan ko‘ra kattaroq davra",
            "Katta davradan ko‘ra bir necha yaqin do‘st",
            "Faqat bir yaqin do‘st bilan suhbat",
        ],
    ),
    (
        "Yangi ilovadan foydalanishni o‘rganmoqchisiz. Qanday tushuntirish sizga qulayroq?",
        PersonalityDimension.SN,
        [
            "Avval aniq misolda qadam-baqadam ko‘rsatish",
            "Ko‘proq aniq misollar, ozroq umumiy tushuntirish",
            "Ko‘proq umumiy tushuntirish, keyin aniq misollar",
            "Avval ishlash tamoyili va qismlarning bog‘liqligini tushuntirish",
        ],
    ),
    (
        "Yaqiningiz yangi xonasini ko‘rsatyapti. E’tiboringiz avval nimaga tushadi?",
        PersonalityDimension.SN,
        [
            "Hozirgi jihozlar va ularning aniq joylashuviga",
            "Ko‘proq hozirgi holatiga, keyin boshqa imkoniyatlariga",
            "Ko‘proq boshqa imkoniyatlariga, keyin hozirgi holatiga",
            "Bu joydan yana qanday foydalanish mumkinligiga",
        ],
    ),
    (
        "Ko‘rgan voqeangizni do‘stingizga aytyapsiz. Odatda nimaga ko‘proq urg‘u berasiz?",
        PersonalityDimension.SN,
        [
            "Kim nima qilgani va aniq tafsilotlariga",
            "Ko‘proq tafsilotlariga, keyin umumiy mazmuniga",
            "Ko‘proq umumiy mazmuniga, ayrim tafsilotlari bilan",
            "Voqeaning umumiy ma’nosi va boshqa holatlar bilan bog‘liqligiga",
        ],
    ),
    (
        "Ishda yoki o‘qishda bir holat qayta-qayta uchrayapti. Uni tushunish uchun nimadan boshlaysiz?",
        PersonalityDimension.SN,
        [
            "Har safar aynan nima bo‘lganini alohida ko‘rib chiqaman",
            "Avval aniq holatlarni, keyin ular orasidagi bog‘liqlikni ko‘raman",
            "Avval umumiy bog‘liqlikni, keyin alohida holatlarni ko‘raman",
            "Holatlarni birlashtiradigan umumiy sababni izlashdan boshlayman",
        ],
    ),
    (
        "Tanish ishni yana bajarishingiz kerak. Usulni o‘zingiz tanlasangiz, nimaga ko‘proq moyilsiz?",
        PersonalityDimension.SN,
        [
            "Tajribamda ishlagan usulni yana qo‘llashga",
            "Asosan tanish usulga, ayrim yangi yo‘llarni sinashga",
            "Asosan yangi yo‘llarni sinashga, tanish usuldan ham foydalanishga",
            "Ishni bajarishning yangicha yo‘lini izlashga",
        ],
    ),
    (
        "Yaqiningiz bir g‘oyasini aytyapti. Qaysi tomonini ko‘proq bilgingiz keladi?",
        PersonalityDimension.SN,
        [
            "Hozir uni amalda qanday bajarish mumkinligini",
            "Ko‘proq amaliy tomonini, keyin kelajak imkoniyatlarini",
            "Ko‘proq kelajak imkoniyatlarini, keyin amaliy tomonini",
            "Bu g‘oya kelajakda yana qanday imkoniyatlar ochishini",
        ],
    ),
    (
        "Do‘stingiz ikki o‘quv kursidan birini tanlamoqchi. Maslahat berishda nimani ustun qo‘yasiz?",
        PersonalityDimension.TF,
        [
            "Kurslarning solishtiriladigan sharoiti va natijalarini",
            "Do‘stimning qadriyatlarini ham o‘ylab, amaliy natijalarni",
            "Amaliy natijalarni ham o‘ylab, do‘stimning shaxsiy qadriyatlarini",
            "Do‘stim uchun nimaning shaxsan muhim va mazmunli ekanini",
        ],
    ),
    (
        "Tengdoshingiz bilan kelishmovchilikni hal qilyapsiz. Siz uchun qaysi mezon ustunroq?",
        PersonalityDimension.TF,
        [
            "Yechimning dalillar va izchil mezonlarga mosligi",
            "Ehtiyojlarni ham o‘ylab, dalillar va izchil mezonlarga ko‘proq tayanaman",
            "Dalillarni ham o‘ylab, tomonlarning ehtiyojlariga ko‘proq tayanaman",
            "Yechimda tomonlarning shaxsiy ehtiyojlari hisobga olinishi",
        ],
    ),
    (
        "Do‘stingiz qilgan ishiga fikringizni so‘radi. Rostini hurmat bilan aytishda nimaga ko‘proq e’tibor berasiz?",
        PersonalityDimension.TF,
        [
            "Fikrimning aniq va asosli tushuntirilishiga",
            "Gapimning ta’sirini ham o‘ylab, ko‘proq tahlilning aniqligiga",
            "Aniq tahlilga ham, ko‘proq gapim unga qanday yetib borishiga",
            "Fikrimni uning holati va hislarini hisobga olib yetkazishga",
        ],
    ),
    (
        "Bir xil vazifadagi ikki kishining sharoiti har xil. Ishni taqsimlashda nimaga ko‘proq tayanasiz?",
        PersonalityDimension.TF,
        [
            "Ikkalasiga bir xil mezon qo‘llashga",
            "Asosan umumiy mezonga, zarur joyda shaxsiy sharoitga",
            "Asosan shaxsiy sharoitga, umumiy mezonni ham hisobga olishga",
            "Har birining shaxsiy sharoitiga mos taqsimlashga",
        ],
    ),
    (
        "Oilangiz bilan umumiy ishning ikki yo‘lini muhokama qilyapsiz. Tanlovda nimani ustun qo‘yasiz?",
        PersonalityDimension.TF,
        [
            "Qaysi yo‘lning amaliy natijasi yaxshiroq ekanini",
            "Yaqinlarimning ehtiyojlarini ham hisobga olib, amaliy natijani",
            "Amaliy natijani ham hisobga olib, yaqinlarimning ehtiyojlarini",
            "Qaysi yo‘l yaqinlarimning qadriyat va ehtiyojlariga mosligini",
        ],
    ),
    (
        "Jamoaviy ish tugadi. Qaysi tomoni sizga ko‘proq qoniqish beradi?",
        PersonalityDimension.TF,
        [
            "Vazifa belgilangan mezon bo‘yicha yaxshi bajarilgani",
            "Odamlarning mamnunligi ham, lekin ko‘proq ishning aniq natijasi",
            "Ishning natijasi ham, lekin ko‘proq odamlarning o‘zini qadrlangan his qilishi",
            "Qatnashgan odamlarning o‘zini eshitilgan va qadrlangan his qilishi",
        ],
    ),
    (
        "Yangi ish yoki shaxsiy mashg‘ulot boshlayapsiz. Qaysi yondashuv sizga qulayroq?",
        PersonalityDimension.JP,
        [
            "Avval bosqichlarni belgilab, keyin ishga kirishish",
            "Asosiy bosqichlarni belgilab, ayrimlarini jarayonda tanlash",
            "Bir-ikki qadamni bilib, ko‘pini jarayonda tanlash",
            "Ishga kirishib, keyingi qadamlarni jarayonda belgilash",
        ],
    ),
    (
        "Dam olish kungi uchrashuv vaqti o‘zgardi. Keyingi ishlaringizni o‘zingiz tanlay olasiz. Nima qulayroq?",
        PersonalityDimension.JP,
        [
            "Darhol yangi tartibni aniq belgilab olish",
            "Asosiy tartibni belgilab, ozgina erkin joy qoldirish",
            "Faqat zarurini belgilab, ko‘pini ochiq qoldirish",
            "Qolgan vaqtni vaziyatga qarab o‘tkazish",
        ],
    ),
    (
        "Ikki mos variant bor, tanlash uchun ma’lumot yetarli. Sizga qaysi holat qulayroq?",
        PersonalityDimension.JP,
        [
            "Tanlovni yakunlab, bitta variant bilan davom etish",
            "Ko‘proq yakuniy tanlov qilishga moyilman",
            "Ko‘proq ikkala variantni hozircha ochiq qoldirishga moyilman",
            "Tanlash zarur bo‘lguncha ikkala variantni ochiq saqlash",
        ],
    ),
    (
        "Bir haftada bajariladigan ish bor. Uni vaqtida tugatish uchun qaysi usul sizga qulay?",
        PersonalityDimension.JP,
        [
            "Qaysi kuni qaysi qismini bajarishimni oldindan belgilash",
            "Asosiy ish vaqtlarini belgilab, qolganini moslashtirish",
            "Ayrim ish vaqtlarini belgilab, ko‘pini vaziyatga qarab tanlash",
            "Muddatni hisobga olib, ish vaqtlarini jarayon davomida tanlash",
        ],
    ),
    (
        "Bir nechta kichik shaxsiy ishlaringiz bor, tartibini o‘zingiz tanlaysiz. Qanday ishlash sizga qulayroq?",
        PersonalityDimension.JP,
        [
            "Har birini tugatib, keyingisiga o‘tish",
            "Ko‘proq bittadan tugatish, ba’zan ishlarni almashtirish",
            "Ko‘proq ishlarni navbatlab bajarish, ba’zan bittasini tugatish",
            "Ishlar orasida almashib, ularni parallel olib borish",
        ],
    ),
    (
        "Bo‘sh kecha uchun rejangiz bor. Boshqa qiziq mashg‘ulot chiqdi. Hech kim oldida majburiyatingiz yo‘q. Qaysi birini tanlaysiz?",
        PersonalityDimension.JP,
        [
            "Odatda avvalgi rejam bilan davom etaman",
            "Ko‘proq avvalgi rejani tanlayman, ba’zan yangi mashg‘ulotni",
            "Ko‘proq yangi mashg‘ulotni tanlayman, ba’zan avvalgi rejani",
            "Odatda yangi mashg‘ulotga qarab rejamni o‘zgartiraman",
        ],
    ),
]
