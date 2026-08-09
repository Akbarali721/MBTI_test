"""24 ta MBTI uslubidagi savollar (o‘lchov nomlari foydalanuvchiga ko‘rinmaydi).

Master bank 48 ta: har biri qarama-qarshi yo‘nalishdagi juft bilan kengaytiriladi
(`app/seed/personality_placeholders.py`).
"""

from app.models.enums import PersonalityDimension

# (savol matni, dimension, 4 ta javob matni)
PERSONALITY_QUESTIONS_UZ: list[tuple[str, PersonalityDimension, list[str]]] = [
    (
        "Bo‘sh vaqtingizda siz ko‘proq odamlar bilan uchrashishni yoki yolg‘iz dam olishni tanlaysiz?",
        PersonalityDimension.EI,
        [
            "Do‘stlaringiz bilan vaqt o‘tkazish",
            "Yaqinlar bilan uchrashish",
            "Yolg‘iz yurish yoki kitob o‘qish",
            "Hech kim bezovta qilmasin, tinch joyda bo‘lish",
        ],
    ),
    (
        "Yangi odamlar bilan tanishish sizga odatda qanday ta’sir qiladi?",
        PersonalityDimension.EI,
        [
            "Qiziqarli va ruhlantiradi",
            "Ko‘pincha yoqadi",
            "Ba’zan charchatadi",
            "Ko‘proq xavotir yoki charchoq beradi",
        ],
    ),
    (
        "Muhim qaror qabul qilishda siz odatda qandaysiz?",
        PersonalityDimension.EI,
        [
            "Boshqalar bilan maslahatlashib hal qilaman",
            "Fikr yig‘ib, keyin qaror qilaman",
            "Avval o‘zim o‘ylab, keyin boshqalar bilan gaplashaman",
            "Asosan yolg‘iz o‘ylab hal qilaman",
        ],
    ),
    (
        "Uzoq kun oxirida energiyangiz odatda qanday bo‘ladi?",
        PersonalityDimension.EI,
        [
            "Odamlar bilan muloqot meni tiklaydi",
            "Yengil suhbat yaxshi keladi",
            "Tinch joy kerak bo‘ladi",
            "Mutlaqo yolg‘iz qolishni xohlayman",
        ],
    ),
    (
        "Tadbir yoki uchrashuvdan keyin siz odatda nima qilasiz?",
        PersonalityDimension.EI,
        [
            "Yana odamlar bilan vaqt o‘tkazaman",
            "Birovlarni chaqirib davom etaman",
            "Uyga qaytib tinchlanaman",
            "Telefonni o‘chirib, yolg‘iz bo‘laman",
        ],
    ),
    (
        "Siz o‘zingizni ko‘proq qanday odam deb his qilasiz?",
        PersonalityDimension.EI,
        [
            "Oson ochiladigan va gapiradigan",
            "Yaqinlarga tez yaqinlashadigan",
            "Tanishguncha biroz ehtiyot",
            "Ichki dunyosi kuchli va kamgap",
        ],
    ),
    (
        "Yangi vazifa boshlaganingizda siz birinchi navbatda nima qilasiz?",
        PersonalityDimension.SN,
        [
            "Aniq qadamlar va tajribani qo‘llayman",
            "Avval mavjud usullarni ko‘rib chiqaman",
            "Umumiy g‘oya va imkoniyatlarni o‘ylayman",
            "Turli variantlarni tasavvur qilib ko‘raman",
        ],
    ),
    (
        "Sizga qaysi tavsif yaqinroq?",
        PersonalityDimension.SN,
        [
            "Amaliy va aniq ishlayman",
            "Fakt va tafsilotlarga e’tibor beraman",
            "Kelajakdagi imkoniyatlarni ko‘raman",
            "Yangi g‘oyalar bilan ishlayman",
        ],
    ),
    (
        "Gapirishda siz ko‘proq qaysi tarafdasiz?",
        PersonalityDimension.SN,
        [
            "Aniq misollar va voqealardan foydalanaman",
            "Real hayotdagi tajribani aytaman",
            "Umumiy ma’no va bog‘liqlikni tushuntiraman",
            "Metafora va tasavvur orqali tushuntiraman",
        ],
    ),
    (
        "Reja tuzayotganda siz nima muhim deb bilasiz?",
        PersonalityDimension.SN,
        [
            "Aniq vaqt va resurslar",
            "Ishonchli va sinovdan o‘tgan yo‘l",
            "Maqsad va umumiy yo‘nalish",
            "Moslashuvchan va yangi yechimlar",
        ],
    ),
    (
        "Siz yangiliklarni qanday qabul qilasiz?",
        PersonalityDimension.SN,
        [
            "Faqat isbotlangan bo‘lsa ishonaman",
            "Amalda sinab ko‘raman",
            "Umumiy mantiqini tushunsam yetarli",
            "Yangi g‘oya bo‘lsa qiziqaman",
        ],
    ),
    (
        "Ish yoki o‘qishda sizni nima ko‘proq qiziqtiradi?",
        PersonalityDimension.SN,
        [
            "Aniq natija va amaliy foyda",
            "Tafsilotlarni to‘g‘ri bajarish",
            "Katta maqsad va ma’no",
            "Yangi usul va ijodiy yondashuv",
        ],
    ),
    (
        "Do‘stingiz muammosi haqida gapirganda siz birinchi navbatda nima qilasiz?",
        PersonalityDimension.TF,
        [
            "Muammoni tahlil qilib yechim taklif qilaman",
            "Nima qilish kerakligini aniq aytaman",
            "His-tuyg‘ularini tushunishga harakat qilaman",
            "Qo‘llab-quvvatlab, yonida bo‘laman",
        ],
    ),
    (
        "Jamoada bahs bo‘lganda siz odatda qanday bo‘lasiz?",
        PersonalityDimension.TF,
        [
            "Mantiq va adolat muhim deb o‘ylayman",
            "Eng to‘g‘ri qarorni izlayman",
            "Har kimning fikri eshitilsin deb harakat qilaman",
            "Munosabatlar buzilmasin deb ehtiyot bo‘laman",
        ],
    ),
    (
        "Sizni ko‘proq qaysi xususiyat tavsiflaydi?",
        PersonalityDimension.TF,
        [
            "Xotirjam va tahliliy",
            "Qaror qabul qilishda qat’iy",
            "Mehribon va tushunuvchan",
            "Yurak bilan qaror qiladigan",
        ],
    ),
    (
        "Boshqalar sizdan maslahat so‘rasa, javobingiz ko‘pincha qanday bo‘ladi?",
        PersonalityDimension.TF,
        [
            "Nima qilish kerakligini aniq aytaman",
            "Afzallik va kamchilikni solishtiraman",
            "Ular qanday his qilishini so‘rayman",
            "Qo‘llab-quvvatlovchi so‘zlar aytaman",
        ],
    ),
    (
        "Tanqid eshitganingizda birinchi reaksiyangiz qanday?",
        PersonalityDimension.TF,
        [
            "Bu to‘g‘rimi, tekshiraman",
            "Mantiqiy bo‘lsa qabul qilaman",
            "Ko‘nglim og‘rishi mumkin",
            "O‘zimni yomon his qilishim mumkin",
        ],
    ),
    (
        "G‘alaba yoki muvaffaqiyat haqida gapirganda siz nima muhim deb bilasiz?",
        PersonalityDimension.TF,
        [
            "Natija va samaradorlik",
            "To‘g‘ri va adolatli yechim",
            "Jamoa ruhiyati va hamjihatlik",
            "Insonlar o‘rtasidagi ishonch",
        ],
    ),
    (
        "Yangi loyiha boshlanganda siz odatda qanday harakat qilasiz?",
        PersonalityDimension.JP,
        [
            "Reja tuzib, tartib bilan boshlayman",
            "Muddat va bosqichlarni belgilayman",
            "Umumiy yo‘nalishni bilaman, batafsil keyin",
            "Jarayon davomida moslashib boraman",
        ],
    ),
    (
        "Sayohat yoki tadbir oldidan siz qandaysiz?",
        PersonalityDimension.JP,
        [
            "Hammasini oldindan rejalashtiraman",
            "Asosiy narsalarni band qilaman",
            "Taxminan reja qilaman, qolganini joyida",
            "Ko‘pincha impulsiv va erkin harakat qilaman",
        ],
    ),
    (
        "Ish stolidagi yoki xonadagi tartib sizga qanchalik muhim?",
        PersonalityDimension.JP,
        [
            "Juda muhim, doim tartibli bo‘laman",
            "Ko‘pincha tartibli bo‘lishga harakat qilaman",
            "Muhim, lekin ba’zan chalkash bo‘lib qoladi",
            "Tartib kamroq, moslashuvchan bo‘lishni xohlayman",
        ],
    ),
    (
        "Muddati yaqin vazifa paydo bo‘lsa, siz qanday reaksiya bildirasiz?",
        PersonalityDimension.JP,
        [
            "Darhol reja tuzib boshlayman",
            "Vaqt bo‘yicha bosqichlab bajaraman",
            "Bosim ostida ham ishlay olaman",
            "Oxirgi daqiqagacha kutishim mumkin",
        ],
    ),
    (
        "Kun rejangiz odatda qanday bo‘ladi?",
        PersonalityDimension.JP,
        [
            "Aniq va oldindan belgilangan",
            "Asosiy ishlar rejalashtirilgan",
            "Elastik, vaziyatga qarab o‘zgaradi",
            "Ko‘pincha birdaniga qaror qilaman",
        ],
    ),
    (
        "Yakuniy qaror qabul qilish sizga qanday oson?",
        PersonalityDimension.JP,
        [
            "Tez va aniq qaror qilaman",
            "Ma’lum bir nuqtada yopaman",
            "Bir oz o‘ylab, keyin yopaman",
            "Variantlarni ochiq qoldirishni xohlayman",
        ],
    ),
]
