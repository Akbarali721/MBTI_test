"""Xarakterim: 24 ta o‘zbekcha savol (asosiy auditoriya 18–25 yosh).

Har yo‘nalishga 6 savol: EI, SN, TF, JP.
Javoblar tartibi: A/B — birinchi qutb, C/D — ikkinchi qutb.
Mavjud import, o‘zgaruvchi nomi va tuple tuzilishi saqlangan.
Bu savollar ilmiy validatsiyadan o‘tgan psixologik diagnostika emas.
"""

from app.models.enums import PersonalityDimension

PERSONALITY_QUESTIONS_UZ: list[tuple[str, PersonalityDimension, list[str]]] = [
    (
        "Dam olish kuni bo‘sh vaqtingiz bor. Nima qilishni xohlaysiz?",
        PersonalityDimension.EI,
        [
            "Do‘stlarimni yig‘ib, birga vaqt o‘tkazaman",
            "Bir-ikki do‘stim bilan uchrashaman",
            "Yolg‘iz sayrga chiqaman",
            "Uyda tinchgina o‘zim bilan bo‘laman",
        ],
    ),
    (
        "Notanish odamlar ko‘p bo‘lgan davraga tushdingiz. Nima qilasiz?",
        PersonalityDimension.EI,
        [
            "O‘zim birinchi bo‘lib suhbat boshlayman",
            "Yonimdagi bir-ikki odam bilan tanishaman",
            "Kimdir gap boshlasa, suhbatga qo‘shilaman",
            "Ko‘proq tinglab, kuzatib o‘tiraman",
        ],
    ),
    (
        "Xayolingizga yangi g‘oya keldi. Odatda nima qilasiz?",
        PersonalityDimension.EI,
        [
            "Darhol do‘stlarim bilan muhokama qilaman",
            "Bir yaqinimning fikrini so‘rayman",
            "Avval o‘zim o‘ylab, keyin maslahatlashaman",
            "Avval g‘oyani o‘zim ishlab chiqaman",
        ],
    ),
    (
        "Sizga juda yaxshi xabar aytishdi. Birinchi nima qilasiz?",
        PersonalityDimension.EI,
        [
            "Darhol bir nechta yaqinimga aytaman",
            "Eng yaqin odamimga aytaman",
            "Biroz vaqt o‘tib yaqinimga aytaman",
            "Avval xursandchiligimni o‘zim his qilaman",
        ],
    ),
    (
        "Yangi narsani o‘rganmoqchisiz. Qaysi usul sizga qulay?",
        PersonalityDimension.EI,
        [
            "Boshqalar bilan birga o‘rganish",
            "Guruhda o‘rganib, fikr almashish",
            "Asosan o‘zim o‘rganib, kerak bo‘lsa so‘rash",
            "Yolg‘iz o‘rganib, mustaqil mashq qilish",
        ],
    ),
    (
        "Bir haftalik charchoqdan keyin qanday dam olasiz?",
        PersonalityDimension.EI,
        [
            "Do‘stlar bilan ko‘ngil ochaman",
            "Yaqinlarim bilan suhbatlashaman",
            "Tinch joyda bir-ikki yaqinim bilan bo‘laman",
            "Hech kim bezovta qilmaydigan joyda dam olaman",
        ],
    ),
    (
        "Yangi telefon olmoqchisiz. Nimaga ko‘proq e’tibor berasiz?",
        PersonalityDimension.SN,
        [
            "Narxi, xotirasi va batareyasiga",
            "Uni ishlatganlarning tajribasiga",
            "Kelajakda menga qanday foyda berishiga",
            "Yangi imkoniyatlari va funksiyalariga",
        ],
    ),
    (
        "Yangi uyga kirdingiz. Birinchi nimaga e’tibor berasiz?",
        PersonalityDimension.SN,
        [
            "Xonalarning kattaligi va jihozlariga",
            "Uy qanchalik qulayligiga",
            "Xonalarni boshqacha bezash imkoniyatiga",
            "Bu uyni kelajakda qanday o‘zgartirish mumkinligiga",
        ],
    ),
    (
        "Biror voqeani do‘stingizga aytib beryapsiz. Odatda qanday gapirasiz?",
        PersonalityDimension.SN,
        [
            "Voqeani boshidan oxirigacha aytaman",
            "Eng muhim tafsilotlarini aytaman",
            "Avval asosiy mazmunini tushuntiraman",
            "Voqeadan qanday xulosa chiqarganimni aytaman",
        ],
    ),
    (
        "Yangi ish boshlamoqchisiz. Avval nimani bilishni xohlaysiz?",
        PersonalityDimension.SN,
        [
            "Aniq qanday vazifalarni bajarishimni",
            "Ish tartibi va sharoitlarini",
            "Bu ish menga qanday imkoniyatlar ochishini",
            "Kelajakda qayergacha rivojlana olishimni",
        ],
    ),
    (
        "Telefoningizga yangi ilova o‘rnatdingiz. Undan qanday foydalanishni boshlaysiz?",
        PersonalityDimension.SN,
        [
            "Avval ko‘rsatmalarini o‘qib chiqaman",
            "Asosiy funksiyalarini birma-bir sinab ko‘raman",
            "Turli bo‘limlarini ochib, qanday imkoniyatlari borligini o‘rganaman",
            "Ilovadan noodatiy usullarda qanday foydalanish mumkinligini izlayman",
        ],
    ),
    (
        "Do‘stingiz sizga kelajakdagi rejalari haqida gapiryapti. Sizni ko‘proq nima qiziqtiradi?",
        PersonalityDimension.SN,
        [
            "Hozir bu maqsad uchun nima qilayotgani",
            "Rejasini qanday amalga oshirmoqchiligi",
            "Bu reja unga qanday yangi imkoniyatlar ochishi",
            "Kelajakda bu g‘oya qanchalik katta narsaga aylanishi mumkinligi",
        ],
    ),
    (
        "Do‘stingiz ikki xil ish taklifini oldi. Sizdan maslahat so‘radi. Nimaga e’tibor berishini aytasiz?",
        PersonalityDimension.TF,
        [
            "Maosh va ish sharoitlarini solishtirishga",
            "Qaysi ishda o‘sish imkoniyati ko‘proqligiga",
            "Qaysi jamoada o‘zini qulay his qilishiga",
            "Qaysi ish uning qiziqishlari va orzulariga yaqinligiga",
        ],
    ),
    (
        "Yaqin do‘stingiz bilan fikringiz to‘g‘ri kelmay qoldi. Nima qilasiz?",
        PersonalityDimension.TF,
        [
            "Nega bunday o‘ylayotganimni dalillar bilan tushuntiraman",
            "Ikkalamizga ham ma’qul yechim izlayman",
            "Avval uning fikrini tushunishga harakat qilaman",
            "Suhbatda uning ko‘ngli og‘rimasligiga e’tibor beraman",
        ],
    ),
    (
        "Do‘stingiz sizdan kiyimi yarashganini so‘radi. Nima deysiz?",
        PersonalityDimension.TF,
        [
            "Yarashmagan bo‘lsa, ochiq aytaman",
            "Fikrimni aniq, lekin muloyim aytaman",
            "Avval o‘ziga yoqqan-yoqmaganini so‘rayman",
            "Uning kayfiyatini hisobga olib javob beraman",
        ],
    ),
    (
        "Do‘stingiz muhim ishda xato qildi va sizga aytdi. Qanday javob berasiz?",
        PersonalityDimension.TF,
        [
            "Xatoni qanday tuzatish mumkinligini aytaman",
            "Xato sababini birga aniqlashni taklif qilaman",
            "Avval nima bo‘lganini va o‘zini qanday his qilayotganini so‘rayman",
            "Avval uni tinchlantirib, keyin yechim haqida gaplashaman",
        ],
    ),
    (
        "Do‘stlaringiz bilan sayrga chiqmoqchisiz. Qayerga borishni qanday tanlaysiz?",
        PersonalityDimension.TF,
        [
            "Narx va masofani solishtiraman",
            "Hamma uchun qulay joyni tanlashni taklif qilaman",
            "Do‘stlarim nimani xohlashini so‘rayman",
            "Hamma xursand bo‘ladigan joyni topishga harakat qilaman",
        ],
    ),
    (
        "Do‘stingiz imtihondan yiqildi va xafa bo‘lib sizga keldi. Nima qilasiz?",
        PersonalityDimension.TF,
        [
            "Qayerda xato qilganini birga tahlil qilaman",
            "Keyingi imtihonga qanday tayyorlanishni aytaman",
            "Avval uni tinglab, nima bo‘lganini so‘rayman",
            "Ko‘nglini ko‘tarib, yonida bo‘laman",
        ],
    ),
    (
        "Ertaga bir nechta muhim ishingiz bor. Odatda nima qilasiz?",
        PersonalityDimension.JP,
        [
            "Hammasini oldindan rejalashtiraman",
            "Eng muhim ishlarni ro‘yxatga yozaman",
            "Faqat asosiy ishlarni belgilab qo‘yaman",
            "Ertangi vaziyatga qarab harakat qilaman",
        ],
    ),
    (
        "Dam olish kuniga reja qilgansiz, lekin u bekor bo‘ldi. Nima qilasiz?",
        PersonalityDimension.JP,
        [
            "Darhol yangi reja tuzaman",
            "Qolgan vaqtni boshqa foydali ishga ajrataman",
            "Kayfiyatimga qarab biror mashg‘ulot tanlayman",
            "Bo‘sh vaqtimda nima qilishni o‘sha payt hal qilaman",
        ],
    ),
    (
        "Qimmatbaho buyum sotib olmoqchisiz. Qanday tanlaysiz?",
        PersonalityDimension.JP,
        [
            "Oldindan talablarimni belgilab, mosini olaman",
            "Bir nechta variantni solishtirib tanlayman",
            "Yaxshi taklif chiqsa, tanlovimni o‘zgartiraman",
            "Shoshilmayman, boshqa imkoniyatlarni ham ko‘raman",
        ],
    ),
    (
        "Bir haftadan keyin muhim topshiriqni bajarishingiz kerak. Qanday boshlaysiz?",
        PersonalityDimension.JP,
        [
            "Birinchi kundan reja tuzib ishlayman",
            "Ishni qismlarga bo‘lib, asta-sekin bajaraman",
            "Vaziyatga qarab qaysi qismidan boshlashni tanlayman",
            "Ilhom kelgan paytda faolroq ishlayman",
        ],
    ),
    (
        "Bir kunda uchta joyga borishingiz kerak. Nima qilasiz?",
        PersonalityDimension.JP,
        [
            "Qayerga qachon borishni oldindan belgilayman",
            "Qaysi biri muhim bo‘lsa, o‘shandan boshlayman",
            "Yo‘lda qaysi biri qulay bo‘lsa, shunga boraman",
            "Vaziyatga qarab tartibni o‘zgartirib boraman",
        ],
    ),
    (
        "Kechqurun uyda dam olmoqchisiz. Do‘stingiz to‘satdan uchrashuvga chaqirdi. Nima qilasiz?",
        PersonalityDimension.JP,
        [
            "Oldingi rejamda qolaman",
            "Rejamga mos kelsa, uchrashaman",
            "Uchrashuv qiziq bo‘lsa, boraman",
            "Yangi taklifni qabul qilib, rejamni o‘zgartiraman",
        ],
    ),
]
