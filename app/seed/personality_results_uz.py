"""16 MBTI turi uchun o‘zbekcha natija matnlari.

Asosiy auditoriya 18–25 yosh. Matn javoblarga qarab berilgan taxmin, ilmiy tashxis emas.
Kalitlar va tuzilma saqlangan. Har bir tur alohida yozilgan.
Bepul qism: sarlavha, kimligingiz, hayotiy misol, 3 kuch, 2 qiyinchilik.
Premium qism shu matnni takrorlamaydi: kundalik vaziyat, kuchni qayerda ishlatish,
charchatadigan holat va yechim, ish muhiti, munosabat.
`get_result_copy` 3 ta amaliy tavsiya va 7 kunlik rejani `personality_guidance_uz` dan qo‘shadi.
"""

from typing import TypedDict


class ResultCopy(TypedDict):
    title: str
    short_description: str
    strengths: list[str]
    challenges: list[str]
    daily_tips: list[str]
    public_view: str
    advice: str
    motivation_analysis: str
    work_style: str
    career_environment: str
    friendship_style: str
    relationship_needs: str
    compatible_people: str
    difficult_communication: str
    action_plan: str


GENERIC_FALLBACK: ResultCopy = {
    "title": "Sizning xarakter yo‘nalishingiz",
    "short_description": (
        "Bu javoblaringizga asoslangan taxminiy tavsif. Aniq tipni aniqlab bo‘lmadi — "
        "qayta urinib ko‘rishingiz yoki natijani do‘stingiz bilan muhokama qilishingiz mumkin."
    ),
    "strengths": [
        "Moslashish. Yangi vaziyatda ham o‘rganishga tayyor turishingiz mumkin.",
        "Sinash. Kuchli tomoningizni avval kichik ishda ko‘rib chiqishingiz mumkin.",
        "Ochiqlik. Muloqotda sodda va samimiy gapirish sizga yengilroq kelishi mumkin.",
    ],
    "challenges": [
        "Juda ko‘p yo‘nalishni bir vaqtda ochib yuborish",
        "O‘z chegarangizni aniq aytmaslik",
    ],
    "daily_tips": [
        "Bugun bitta kuchli tomoningizni aniq bir vazifada sinab ko‘ring.",
        "Charchagan paytingizda 10 daqiqa tanaffus qiling, keyin davom eting.",
        "Kechqurun «nima yaxshi ketdi?» deb bitta jumla yozing.",
    ],
    "public_view": (
        "Bu uslubda odam atrofda xotirjam, muloqotga ochiq va o‘z yo‘lini qidirayotgan inson "
        "deb qabul qilinishi mumkin — bu haqiqiy fikr emas, ehtimoliy tasvir."
    ),
    "advice": "Kuchli tomoningizni bugun bitta kichik ishda sinab ko‘ring.",
    "motivation_analysis": (
        "Motivatsiya sizda ma’noli maqsad va ko‘zga ko‘rinadigan kichik yutuqlar bo‘lganda barqarorroq bo‘ladi."
    ),
    "work_style": "Reja va moslashuv muvozanatda bo‘lgan ish sizga yaxshi kelishi mumkin.",
    "career_environment": "Hurmat, aniq vazifalar va o‘sish imkoniyati bor muhit sizga qulay kelishi mumkin.",
    "friendship_style": "Siz uchun sodda, to‘g‘ridan-to‘g‘ri muloqot va o‘zaro ishonch muhim bo‘lishi mumkin.",
    "relationship_needs": "Tushunish, hurmat va bir-biringizga ataylab ajratilgan vaqt kerak bo‘lishi mumkin.",
    "compatible_people": (
        "Murakkab mavzuni tinch muhokama qila oladigan va baho bermay qo‘llab-quvvatlaydigan odamlar."
    ),
    "difficult_communication": "Bosim va hurmatsiz ohang sizni tez charchatishi mumkin.",
    "action_plan": (
        "1-kun: bitta kuchli tomoningizni aniq bir vazifada qo‘llang. "
        "7-kungacha har kuni bitta kichik qadam qo‘shib boring."
    ),
}


def _entry(
    *,
    title: str,
    summary: str,
    strengths: list[str],
    challenges: list[str],
    others: str,
    advice: str,
    motivation: str,
    work: str,
    career: str,
    friendship: str,
    relationship: str,
    compatible: str,
    difficult: str,
    plan: str,
) -> ResultCopy:
    return {
        "title": title,
        "short_description": summary,
        "strengths": strengths,
        "challenges": challenges,
        "daily_tips": [],
        "public_view": others,
        "advice": advice,
        "motivation_analysis": motivation,
        "work_style": work,
        "career_environment": career,
        "friendship_style": friendship,
        "relationship_needs": relationship,
        "compatible_people": compatible,
        "difficult_communication": difficult,
        "action_plan": plan,
    }


def _use(*lines: str) -> str:
    return "\n".join(lines)


PERSONALITY_RESULTS_UZ: dict[str, ResultCopy] = {
    "INFP": _entry(
        title="Siz — ichki mezoniga qarab qaror qiladigan odamsiz.",
        summary=(
            "Sizda ishni avval o‘zingizga muhim yoki muhim emasligiga qarab tekshirish odat bo‘lishi mumkin. "
            "Tashqaridan ko‘p gapirmasangiz ham, ichingizda javob allaqachon shakllanayotgan bo‘lishi mumkin. "
            "Yaqin odamning holatini sezasiz, lekin o‘z noqulayligingizni keyinroq aytishingiz mumkin. "
            "Shuning uchun «mayli» degan javob ba’zan sizni emas, boshqani tinchlantiradi.\n\n"
            "Masalan, do‘stlar kechqurun chiqishni reja qiladi. Siz uyda qolishni xohlaysiz, lekin «mayli» deb qo‘yasiz. "
            "Kechasi charchab qaytasiz va ertasiga topshiriqqa kuchingiz yetmaydi."
        ),
        strengths=[
            "Tinglash. Yaqin odam gapirganda shoshilmay oxirigacha eshitishingiz mumkin.",
            "Ma’no. Sizga muhim ishni chala tashlab yuborish qiyinroq kelishi mumkin.",
            "Ohang. Yozma yoki ijodiy ishda o‘z ovozingizni topishingiz mumkin.",
        ],
        challenges=[
            "«Mayli» deb qo‘yib, keyin ichingizda qolish",
            "Noqulay gapni keyinga surib, jim yurish",
        ],
        others=_use(
            "Guruh suhbatida oxirida bir jumla bilan xulosa qiling: eshitganingiz qarorga aylanadi.",
            "Yozma topshiriqda o‘z ohangingizni saqlang va oxiriga bitta aniq xulosa qo‘ying.",
            "Muhim ishni bitta odam bilan yakunlang, har paragrafni umumiy chatda kelishtirmang.",
        ),
        advice="Bugun bitta kichik iltimosga «hozir qiyin, keyinroq yozaman» deb javob bering.",
        motivation=(
            "Kurs ishi faqat baho uchun bo‘lsa, qo‘lingiz sekinlashishi mumkin. "
            "Daftar chetiga «buni kim uchun qilyapman» deb bir qator yozsangiz, davom ettirish osonlashadi. "
            "Do‘stning xabari kechqurun kelib, o‘qish vaqtingizni olsa, avval 20 daqiqa o‘qib, keyin javob yozish sizni yengilroq tutishi mumkin."
        ),
        work=(
            "Avval yolg‘iz qoralama yozib, keyin odamga ko‘rsatish sizga qulayroq kelishi mumkin. "
            "Vazifa aniq bo‘lsa va muddat siqib turmasa, matn yaxshiroq chiqishi mumkin. "
            "Har qadamni guruhda ovozga qo‘yish sizni to‘xtatib qo‘yishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "yozma ish, kichik guruh, o‘z sur’ati, odamga foydasi ko‘rinadigan topshiriq."
        ),
        friendship=(
            "Sizga shovqinli davradan ko‘ra bitta odam bilan uzoqroq suhbat yaqinroq kelishi mumkin. "
            "Ko‘p chaqiruvdan keyin ertasiga yozma xabar orqali ochilishingiz ham mumkin. Shu xabarni oldindan ayting."
        ),
        relationship=(
            "Har kecha uzun hisobot shart emas. «Bugun shu narsa og‘ir bo‘ldi» degan bir jumla ham sizni ochishi mumkin. "
            "Yolg‘iz qolishni so‘rasangiz, buni uzoqlashish deb o‘qimaslikni oldindan ayting."
        ),
        compatible=(
            "Kelishmovchilik chiqsa, avval nima bo‘lganini bir jumlada yozing, keyin hisni qo‘shing. "
            "«Hozir gaplasha olmayman, ertaga 15 daqiqa bor» desangiz, jimlik adashishga aylanmasligi mumkin."
        ),
        difficult=_use(
            "Chiqishga ichingiz yo‘q bo‘lsa ham «mayli» deb qo‘yasiz. Yechim: «bugun kela olmayman, ertaga yozaman» deb bir jumla yuboring.",
            "Noqulay gapni bir necha kun ichingizda yurasiz. Yechim: xabarni qoralab, 10 daqiqadan keyin yuboring.",
            "Bitta tanqidni uzoq o‘ylab, ishni to‘xtatasiz. Yechim: tanqidning bitta aniq joyini belgilab, faqat shu joyni tuzating.",
        ),
        plan="1-kun: bitta iltimosga aniq chegara yozing. 7-kun: qaysi chegara oson bo‘lganini ikki qator qilib yozing.",
    ),
    "INFJ": _entry(
        title="Siz — oldindan o‘ylab, odamni eshitadigan odamsiz.",
        summary=(
            "Sizda gapni aytishdan oldin uning oqibatini ko‘rib chiqish odat bo‘lishi mumkin. "
            "Yaqin odamning holatini sezasiz va yordamni o‘zingiz taklif qilishingiz mumkin. "
            "Reja ichingizda tayyor bo‘lsa ham, uni hammaga darrov ochmasligingiz mumkin. "
            "Boshqalar tinchigida siz charchab qolishingiz ham mumkin.\n\n"
            "Masalan, guruh loyihasida hamma chalg‘igan. Siz muddatni, kim nima qilishini va kim noqulay bo‘lishini oldindan o‘ylaysiz. "
            "Kechasi esa o‘zingiz dam olmasdan ro‘yxat tuzasiz."
        ),
        strengths=[
            "Oldindan ko‘rish. Muhim ishning keyingi qadamini erta sezishingiz mumkin.",
            "Eshitish. Odamning so‘zini tuzatishdan oldin tinglashingiz mumkin.",
            "Tartib. Chalg‘igan ishni bitta ro‘yxatga yig‘ishingiz mumkin.",
        ],
        challenges=[
            "Boshqaning kayfini o‘z damingizdan oldinga qo‘yish",
            "Ichki rejangizni aytmasdan, odam sizni tushunmayapti deb qolish",
        ],
        others=_use(
            "Guruhda keyingi qadamni bitta xabarda yozing, hammasini o‘zingiz qilmang.",
            "Maslahatdan oldin «hozir eshitaymi yoki yo‘l aytaymi?» deb so‘rang.",
            "Kechki damni kalendarga qo‘ying va uni boshqa ish bilan almashtirmang.",
        ),
        advice="Bugun kechki 20 daqiqani o‘zingiz uchun band qiling va bu vaqtni boshqaga bermang.",
        motivation=(
            "Do‘st kechqurun yordam so‘rasa, o‘qishni to‘xtatib, ertalab charchab turishingiz mumkin. "
            "Oila yig‘inida hamma kayfini siz ushlab, o‘z rejangiz qolib ketishi mumkin. "
            "Bitta aniq «men shu soatdan keyin javob yozaman» qoidasi sizni yengilroq tutishi mumkin."
        ),
        work=(
            "Oldindan tuzilgan, odamga foydasi ko‘rinadigan ish sizga qulayroq kelishi mumkin. "
            "Jamoa kichik bo‘lsa va rol aniq bo‘lsa, ortiqcha yuk kamayishi mumkin. "
            "Har kuni reja o‘zgarib tursa, kuch tez ketishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "aniq rol, kichik jamoa, oldindan ko‘rinadigan muddat, odamga yordami bor ish."
        ),
        friendship=(
            "Do‘stga yordam berishni yaxshi ko‘rasiz, lekin har safar o‘zingiz yetib borishingiz shart emas. "
            "«Bugun eshitaman, yechimni ertaga birga qaraymiz» desangiz, do‘stlik ham, damingiz ham saqlanishi mumkin."
        ),
        relationship=(
            "Yaqin odam nima o‘ylayotganingizni taxmin qilavermasin. Bitta rejangizni o‘zingiz ayting. "
            "Tinch vaqtni oldindan belgilasangiz, yaqinlik faqat muammo chiqqanda gaplashishga aylanmasligi mumkin."
        ),
        compatible=(
            "Kelishmovchilikda avval eshitganingizni bir jumlada qaytaring, keyin o‘z xavotiringizni ayting. "
            "«Men shuni nazarda tutgan edim» deb rejangizni ochsangiz, jimlik adashishga aylanmasligi mumkin."
        ),
        difficult=_use(
            "Hamma sizdan maslahat kutadi, siz esa charchagansiz. Yechim: «hozir eshitaman, yechimni ertaga aytaman» deng.",
            "Ichki rejangizni aytmaysiz, keyin xafa bo‘lasiz. Yechim: rejaning bitta qadamini xabarda yozing.",
            "Boshqaning kayfini tuzatishga kechasi ketadi. Yechim: kechki 20 daqiqani oldindan band qiling.",
        ),
        plan="1-kun: kechki 20 daqiqani o‘zingizga qo‘ying. 7-kun: qaysi yordamni kechiktirganingizni yozing.",
    ),
    "INTJ": _entry(
        title="Siz — uzoq reja tuzib, o‘zingiz yuradigan odamsiz.",
        summary=(
            "Sizda maqsadni oldindan qo‘yib, keraksiz qadamni tashlab yuborish odat bo‘lishi mumkin. "
            "Yolg‘iz ishlaganda tezroq natija chiqishi mumkin. "
            "Gapni qisqa aytasiz, shuning uchun odam sizni sovuq deb o‘qishi mumkin. "
            "Reja buzilsa, avval jahlingiz chiqib, keyin yangi yo‘l qidirishingiz mumkin.\n\n"
            "Masalan, semestr boshida fanlarni haftalarga bo‘lib qo‘yasiz. "
            "Guruh esa har kuni rejani o‘zgartiradi. Siz jim ishlaysiz, oxirida esa «nega oldin aytmadingiz» deysiz."
        ),
        strengths=[
            "Reja. Uzoq ishni bosqichlarga bo‘lib, muddatni ushlashingiz mumkin.",
            "Tanlash. Keraksiz ishni erta tashlab, asosiy narsaga kuch sarflashingiz mumkin.",
            "Mustaqil yurish. Yo‘l aniq bo‘lsa, nazoratsiz ham oxiriga yetishingiz mumkin.",
        ],
        challenges=[
            "Qarorni ichingizda qilib, boshqaga kech ayting",
            "Reja buzilganda butun ish yiqildi deb his qilish",
        ],
        others=_use(
            "Rejaning sababini bitta jumlada yozing, odam nima uchun shunday qilayotganingizni ko‘radi.",
            "Mustaqil qismni o‘zingiz yoping, umumiy qarorni esa bir marta guruhga ko‘rsating.",
            "Buzilgan kunga bitta zaxira soat qo‘ying, butun rejani o‘chirmang.",
        ),
        advice="Bugun bitta qaroringizning sababini guruhga bir jumla qilib yozing.",
        motivation=(
            "Guruh har kuni yo‘nalishni o‘zgartirsa, siz ishni to‘xtatib, yolg‘iz qismni qilishingiz mumkin. "
            "Imtihon oldidan boshqalar kechasi o‘qisa, siz eski rejangizni ushlab, moslasha olmasligingiz mumkin. "
            "Bitta zaxira soat rejani butunlay tashlashdan saqlashi mumkin."
        ),
        work=(
            "Uzoq muddatli, aniq natijali va ortiqcha yig‘ilishi kam ish sizga qulayroq kelishi mumkin. "
            "Jamoa qarorni qisqa yozsa, siz ham o‘z qismingizni o‘z vaqtida yopishingiz mumkin. "
            "Har soatda yo‘nalish o‘zgarsa, sifat tushishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "uzoq loyiha, aniq natija, kam yig‘ilish, mustaqil qism."
        ),
        friendship=(
            "Do‘stga har kuni uzun suhbat shart emas. Haftada bitta aniq uchrashuv yaqinlikni ushlab turishi mumkin. "
            "Javobingiz qisqa bo‘lsa, «hozir bandman, kechqurun yozaman» deb vaqtni ayting."
        ),
        relationship=(
            "Yaqin odam hisni eshitishni xohlasa, yechimdan oldin bir jumla qo‘shing: «bu og‘ir ekan». "
            "Rejangizni yashirsangiz, u nazorat deb o‘qilishi mumkin. Bitta sababni oching."
        ),
        compatible=(
            "Bahsda avval raqibning bitta kuchli jihatini ayting, keyin o‘z rejangizni qo‘ying. "
            "«Men shu muddatni nazarda tutgan edim» desangiz, qisqa ohang adashishga aylanmasligi mumkin."
        ),
        difficult=_use(
            "Qaror ichingizda qoladi, guruh kech biladi. Yechim: qaror va sababini bugun bitta xabarda yozing.",
            "Reja buzilsa, butun kun to‘xtaydi. Yechim: buzilgan qismga 30 daqiqalik zaxira qo‘ying.",
            "Qisqa javobingizni sovuqlik deb olishadi. Yechim: javob oxiriga «kechqurun davom ettiramiz» qo‘shing.",
        ),
        plan="1-kun: bitta qarorning sababini yozing. 7-kun: qaysi reja zaxira soat bilan omon qolganini belgilang.",
    ),
    "INTP": _entry(
        title="Siz — avval sababini tushunib oladigan odamsiz.",
        summary=(
            "Sizda yangi narsani qilishdan oldin «nima uchun» deb so‘rash odat bo‘lishi mumkin. "
            "Tushunarsiz qoidani ko‘r-ko‘rona bajarish qiyin kelishi mumkin. "
            "G‘oya ko‘p chiqadi, lekin oxirgi rasmiylashtirish cho‘zilishi mumkin. "
            "Hisni ichingizda tahlil qilib, kech aytishingiz mumkin.\n\n"
            "Masalan, guruh topshirig‘ida hamma dizayn tanlaydi. Siz esa «bu talab nima demoqchi?» deb savol berasiz. "
            "Savol to‘g‘ri, lekin muddat yaqinlashganda hujjat hali ochiq qoladi."
        ),
        strengths=[
            "Savol. Chalkash topshiriqning zaif joyini erta topishingiz mumkin.",
            "Tahlil. Bir nechta yo‘lni solishtirib, sababini ayta olasiz.",
            "O‘rganish. Qiziq mavzuga chuqur kirib, boshqaga tushuntira olasiz.",
        ],
        challenges=[
            "Tushunishni tugatmay, ishni rasmiylashtirmaslik",
            "Hisni tahlil qilib, odamga kech yoki quruq aytish",
        ],
        others=_use(
            "Savolni bering, lekin javobdan keyin bugungi bitta qadamni ham yozing.",
            "Tushuntirishni do‘stga 5 daqiqada aytib, keyin yozuvni yakunlang.",
            "Hisni tahlildan ajrating: avval «og‘ir», keyin sabab.",
        ),
        advice="Bugun ochiq ishning «tugadi» degan holatini bir jumla qilib yozing.",
        motivation=(
            "Ma’ruza qiziq bo‘lsa, kechgacha o‘qishingiz mumkin. "
            "Oddiy hisobot esa bir necha kun ochiq yotishi mumkin, chunki u savol bermaydi. "
            "Hisobotga ham bitta «nima uchun kerak» jumlasini qo‘ssangiz, yakunlash osonlashishi mumkin."
        ),
        work=(
            "Murakkab savolni yechadigan, lekin oxirida qisqa xulosa so‘raladigan ish sizga qulayroq kelishi mumkin. "
            "Jamoa sizdan faqat g‘oya emas, bitta yozma xulosa ham kutsa, ish yopilishi mumkin. "
            "Cheksiz muhokama muddatni yeb qo‘yishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "murakkab savol, tinch o‘qish, qisqa xulosa, aniq muddat."
        ),
        friendship=(
            "Do‘st bilan mavzuni chuqur so‘rash sizni yaqinlashtirishi mumkin. "
            "Lekin har suhbat tahlil bo‘lmasin: haftada bir marta oddiy «qalaysan» xabari ham yetadi."
        ),
        relationship=(
            "Yaqin odam yechim emas, yonida turishni so‘rasa, avval 10 daqiqa tinglang. "
            "Sababni keyin so‘rang. Aks holda g‘amxo‘rlik imtihondek tuyulishi mumkin."
        ),
        compatible=(
            "Bahsda o‘z fikringizni aytishdan oldin suhbatdoshning jumlasini qaytaring. "
            "«Tushundim, siz shuni deyapsiz» desangiz, savol hujumdek eshitilmasligi mumkin."
        ),
        difficult=_use(
            "Savol ko‘p, hujjat ochiq qoladi. Yechim: savoldan keyin bugungi 15 daqiqalik qadamni yozing.",
            "Hisobot zerikarli bo‘lib, suriladi. Yechim: unga «kim o‘qiydi» deb bir qator yozing.",
            "Do‘st xafa bo‘lsa, siz sabab so‘raysiz. Yechim: avval «og‘ir ekan» deng, 10 daqiqadan keyin savol bering.",
        ),
        plan="1-kun: ochiq ishning tugash jumlasini yozing. 7-kun: qaysi savol ishni surganini belgilang.",
    ),
    "ISFP": _entry(
        title="Siz — o‘z ritmingizda ish qiladigan odamsiz.",
        summary=(
            "Sizda ishni o‘z uslubingiz va o‘z vaqtingiz bilan qilish odat bo‘lishi mumkin. "
            "Majburan tezlashtirish sifatni tushirishi mumkin. "
            "E’tirozni ichingizda saqlab, jim davom etishingiz mumkin. "
            "Qo‘l bilan yoki ko‘z bilan ko‘rinadigan ishda ochilishingiz osonroq bo‘lishi mumkin.\n\n"
            "Masalan, guruh slaydni kechasi qayta yasashni so‘raydi. Siz charchagansiz, lekin rad eta olmaysiz. "
            "Slayd chiqadi, ertalab esa darsda jim o‘tirasiz."
        ),
        strengths=[
            "Did. Ko‘rinadigan ishda ortiqcha narsani olib tashlashingiz mumkin.",
            "Sabr. O‘z ritmingizda sifatli yakun topishingiz mumkin.",
            "Sezuv. Yaqin odamning holatini so‘zdan oldin payqashingiz mumkin.",
        ],
        challenges=[
            "Noqulay ishga jim rozi bo‘lib, keyin charchash",
            "Fikringizni baland aytmaslik",
        ],
        others=_use(
            "Ko‘rinadigan ishda bitta namunani erta ko‘rsating, oxirida katta o‘zgarish kamayadi.",
            "Ritmni himoya qiling: «bu qismga 30 daqiqa kerak» deb yozing.",
            "Fikringizni avval bitta odamga ayting, keyin guruhga chiqing.",
        ),
        advice="Bugun noqulay iltimosga «bugun sig‘maydi, ertaga 30 daqiqa bor» deb yozing.",
        motivation=(
            "Slayd yoki rasm o‘z qo‘lingizdan chiqsa, vaqt tez o‘tishi mumkin. "
            "Lekin kimdir har besh daqiqada tuzatish yuborsa, ishni yopib qo‘yishingiz mumkin. "
            "Bitta ko‘rsatish vaqti belgilansa, ritm saqlanishi mumkin."
        ),
        work=(
            "Qo‘l yoki ko‘z bilan ko‘rinadigan, o‘z sur’atida bajariladigan ish sizga qulayroq kelishi mumkin. "
            "Jamoa namuna ko‘rsatish vaqtini oldindan qo‘ysa, siz ham muddatga ulgurishingiz mumkin. "
            "Doimiy nazorat ostida sifat tushishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "ko‘rinadigan natija, o‘z sur’ati, kam nazorat, aniq namunaviy ko‘rsatish."
        ),
        friendship=(
            "Do‘st bilan yonma-yon ish qilish sizga uzun maslahatdan yaqinroq kelishi mumkin. "
            "Chaqiruv ko‘p bo‘lsa, bittasini tanlab, qolganiga aniq vaqt ayting."
        ),
        relationship=(
            "Yaqin odam sizdan tez javob kutsa, jimlikni tushuntiring: «o‘ylayapman, kechqurun aytaman». "
            "Hisni she’rdek yashirish shart emas. Bitta oddiy jumla ham yetadi."
        ),
        compatible=(
            "Norozi bo‘lsangiz, avval nima og‘irligini ayting, keyin nima xohlayotganingizni qo‘shing. "
            "«Bu usul menga siqiladi, shu variantni sinaylik» desangiz, jimlik rad etishdek o‘qilmasligi mumkin."
        ),
        difficult=_use(
            "Kechasi qayta ishlashni so‘rashadi, siz jim rozi bo‘lasiz. Yechim: «ertaga 30 daqiqa» deb yozing.",
            "Fikringiz bor, lekin guruhda demaysiz. Yechim: avval bitta odamga ovozli xabar yuboring.",
            "Har besh daqiqada tuzatish kelsa, ishni yopasiz. Yechim: ko‘rsatish vaqtini oldindan belgilang.",
        ),
        plan="1-kun: bitta iltimosga aniq vaqt yozing. 7-kun: qaysi ish o‘z ritmingizda yaxshi chiqqanini belgilang.",
    ),
    "ISFJ": _entry(
        title="Siz — yaqinlaringizni eslab, yonida turadigan odamsiz.",
        summary=(
            "Sizda yaqin odamning mayda ehtiyojini eslab qolish odat bo‘lishi mumkin. "
            "Vazifa aniq bo‘lsa, uni oxirigacha olib borishingiz mumkin. "
            "O‘zingizga vaqt ajratishni unutib, boshqaning ishini olishingiz mumkin. "
            "O‘zgarish birdan kelsa, avval xavotir, keyin moslashish kelishi mumkin.\n\n"
            "Masalan, kursdosh kasal bo‘lib, konspekt so‘raydi. Siz yuborasiz, keyin uning topshirig‘iga ham yordamlashasiz. "
            "O‘z muddatingiz esa tungi soatga qoladi."
        ),
        strengths=[
            "Eslab qolish. Yaqin odam aytgan mayda narsani yodda tutishingiz mumkin.",
            "Mas’uliyat. Aniq vazifani oxirigacha yetkazishingiz mumkin.",
            "Tinch yordam. Shovqinsiz, o‘z vaqtida yonida turishingiz mumkin.",
        ],
        challenges=[
            "O‘z ishingizdan oldin boshqaning ishini olish",
            "O‘zgarishni oldindan bilmasangiz, qotib qolish",
        ],
        others=_use(
            "Yordamni cheklang: bugun bitta aniq narsa, qolgani ertaga.",
            "O‘z muddatingizni kalendarda yordamdan oldin turadigan qilib qo‘ying.",
            "O‘zgarish chiqsa, avval nima o‘zgarmaganini yozing, keyin yangi qadamni qo‘ying.",
        ),
        advice="Bugun yordam so‘rovidan bittasini qoldiring, o‘z ishingizga 25 daqiqa qo‘ying.",
        motivation=(
            "Uydagilar yoki kursdosh kechqurun yordam so‘rasa, o‘z rejangiz surilishi mumkin. "
            "Eslab qolgan mayda ishlar kun bo‘yi sizda yurishi mumkin. "
            "Ularni bitta ro‘yxatga yozib, bugungi bittasini tanlasangiz, boshingiz yengillashishi mumkin."
        ),
        work=(
            "Aniq topshiriq, tushunarli muddat va odamga aniq foydasi bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa kim nima qilishini yozsa, siz ortiqcha yuk olmasligingiz mumkin. "
            "Har kuni qoida o‘zgarsa, xavotir oshishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "aniq topshiriq, barqaror muddat, kichik guruh, ko‘rinadigan yordam."
        ),
        friendship=(
            "Do‘stning tug‘ilgan kunini yoki imtihonini eslash sizni ishonchli qiladi. "
            "Lekin har safar yetib borish shart emas. «Bugun konspekt yuboraman, qolganini ertaga» deng."
        ),
        relationship=(
            "Yaqin odam sizning yordamingizni odat deb qabul qilmasin. O‘z charchoqlingizni ham ayting. "
            "«Bugun men ham dam olaman» degan jumla munosabatni buzmasligi, aniqlashtirishi mumkin."
        ),
        compatible=(
            "Xafa bo‘lsangiz, yordamni to‘xtatib jim yurmang. Bitta jumla ayting: «bu safar og‘ir bo‘ldi». "
            "Keyin nima o‘zgarsin deb xohlayotganingizni qo‘shing."
        ),
        difficult=_use(
            "O‘z muddatingiz qolib, boshqaning ishini olasiz. Yechim: bugun faqat bitta yordamni qoldiring.",
            "Mayda va’dalar boshda yuradi. Yechim: ularni ro‘yxatga yozib, bittasini tanlang.",
            "Reja birdan o‘zgarsa, qotib qolasiz. Yechim: nima o‘zgarmaganini yozib, bitta yangi qadam qo‘ying.",
        ),
        plan="1-kun: yordamni bitta narsa bilan cheklang. 7-kun: o‘z muddatingiz saqlangan kunni belgilang.",
    ),
    "ISTJ": _entry(
        title="Siz — so‘zida turib, tartib bilan ishlaydigan odamsiz.",
        summary=(
            "Sizda aytgan vaqtda ishni topshirish va qoidani aniq saqlash odat bo‘lishi mumkin. "
            "Tafsilotni ko‘rasiz va xatoni erta ushlashingiz mumkin. "
            "Reja buzilsa, avval nima noto‘g‘ri ketganini tuzatmoqchi bo‘lasiz. "
            "Boshqalar erkinroq yursa, siz shoshilishingiz mumkin.\n\n"
            "Masalan, laboratoriya hisobotida jadvalni o‘zingiz to‘ldirasiz, chunki guruh kechikadi. "
            "Hisobot toza chiqadi, lekin siz guruhga ishonish qiyinlashadi."
        ),
        strengths=[
            "So‘z. Belgilangan muddatni ushlashga intilishingiz mumkin.",
            "Tafsilot. Xatoni hisobot yoki ro‘yxatda erta ko‘rishingiz mumkin.",
            "Tartib. Chalkash ishni qadam-baqadam yopishingiz mumkin.",
        ],
        challenges=[
            "Reja buzilganda butun ish to‘xtadi deb his qilish",
            "Boshqaning erkin usulini xato deb o‘qish",
        ],
        others=_use(
            "Muddatni ushlaganingizni guruhga namuna qiling, hammasini o‘zingiz yopmang.",
            "Xatoni topganingizda bitta joyini yozing, butun ishni qayta boshlamang.",
            "Buzilgan kunga sodda yechim qo‘ying: asosiy qism bugun, qolgani ertaga.",
        ),
        advice="Bugun buzilgan bitta qismga sodda yechim tanlang va qolganini ertaga yozing.",
        motivation=(
            "Jadval o‘z joyida bo‘lsa, imtihon oldi tinchroq o‘tishi mumkin. "
            "Guruh kechki payt yangi talab yuborsa, siz butun kuni qayta boshlamoqchi bo‘lishingiz mumkin. "
            "Asosiy qismni saqlab, yangi talabni ertangi ro‘yxatga qo‘yish kifoya qilishi mumkin."
        ),
        work=(
            "Aniq qoida, tekshiriladigan natija va barqaror muddat bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa o‘zgarishni oldindan yozsa, siz moslasha olasiz. "
            "Har soatda yangi buyruq kelsa, tartib foyda o‘rniga to‘siq bo‘lishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "aniq qoida, tekshiriladigan natija, barqaror muddat, yozma topshiriq."
        ),
        friendship=(
            "Va’dada turish sizni ishonchli do‘st qiladi. "
            "Do‘st rejani o‘zgartirsa, avval nima uchun o‘zgarganini so‘rang, keyin yangi vaqtni yozing."
        ),
        relationship=(
            "Yaqin odam erkinroq yashasa, buni hurmatsizlik deb o‘qimang. Bitta muhim qoidani ayting, qolganini qo‘yib bering. "
            "«Menga muddat muhim, qolgan joyda sen tanla» desangiz, nazorat kamayishi mumkin."
        ),
        compatible=(
            "Tuzatishdan oldin bitta to‘g‘ri qilingan joyini ayting. "
            "Keyin xatoni ko‘rsating. Shunda gap hujum emas, yordam bo‘lib eshitilishi mumkin."
        ),
        difficult=_use(
            "Guruh kechikadi, siz hammasini o‘zingiz yopasiz. Yechim: o‘z qismingizni yoping, qolganiga muddat yozing.",
            "Reja buzilsa, kun to‘xtaydi. Yechim: asosiy qismni bugun, qolganini ertangi ro‘yxatga qo‘ying.",
            "Xatoni ko‘rib, odamni tuzatasiz. Yechim: avval bitta yaxshi joyini ayting.",
        ),
        plan="1-kun: buzilgan qismga sodda yechim qo‘ying. 7-kun: qaysi ishni boshqaga qoldirganingizni yozing.",
    ),
    "ISTP": _entry(
        title="Siz — muammoni joyida yechadigan odamsiz.",
        summary=(
            "Sizda uzoq muhokamadan ko‘ra buzilgan narsani joyida tuzatish odat bo‘lishi mumkin. "
            "Qo‘lingiz tegadigan ishda tez yo‘l topishingiz mumkin. "
            "Nima qilganingizni tushuntirishni keyinga qoldirishingiz mumkin. "
            "Tez qaror to‘g‘ri chiqsa ham, katta xaridda shoshilish xavfli bo‘lishi mumkin.\n\n"
            "Masalan, guruh chatida printer buzilgani haqida bahs ketadi. "
            "Siz borib qog‘ozni to‘g‘rilaysiz. Muammo yopiladi, lekin hisobotda nima bo‘lgani yozilmaydi."
        ),
        strengths=[
            "Joyida yechish. Buzilgan narsani gapirishdan oldin tuzatishingiz mumkin.",
            "Tinch qo‘l. Shoshilinch vaziyatda ortiqcha shovqinsiz ishlashingiz mumkin.",
            "Sinash. Nazariyani emas, ishlaydigan usulni tekshirishingiz mumkin.",
        ],
        challenges=[
            "Qilgan ishni tushuntirmasdan keyingi odamga qoldirish",
            "Katta qarorni sinab ko‘rmasdan tez qabul qilish",
        ],
        others=_use(
            "Yechimdan keyin uchta qator yozing: nima buzilgan, nima qildingiz, nima qoldi.",
            "Guruh bahsida avval muammoni yoping, keyin bir jumla xulosa tashlang.",
            "Katta xariddan oldin bir kecha kutib, ertalab narxni qayta o‘qing.",
        ),
        advice="Bugun yechgan bitta muammo haqida uchta qator yozuv qoldiring.",
        motivation=(
            "Laboratoriya yoki usta ishida qo‘l tekkanda vaqt sezilmasligi mumkin. "
            "Uzun yig‘ilishda esa telefonni ochib, ishdan chiqib ketishingiz mumkin. "
            "Yig‘ilishga «oxirida nima qaror bo‘ladi» deb bir savol qo‘ysangiz, o‘tirish foydaliroq bo‘lishi mumkin."
        ),
        work=(
            "Qo‘l tegadigan, natijasi darrov ko‘rinadigan va ortiqcha yig‘ilishi kam ish sizga qulayroq kelishi mumkin. "
            "Jamoa yechimni qisqa yozishni so‘rasa, keyingi odam ham tushunadi. "
            "Faqat gapiriladigan ish sizni tez charchatishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "qo‘l tegadigan ish, darrov ko‘rinadigan natija, kam yig‘ilish, qisqa yozuv."
        ),
        friendship=(
            "Do‘stga yordam ko‘pincha gap emas, ish bo‘lishi mumkin. "
            "Shundan keyin ham bitta xabar yozing, aks holda yaqinlik faqat muammo chiqqanda ko‘rinadi."
        ),
        relationship=(
            "Yaqin odam nima bo‘lganini eshitmoqchi bo‘lsa, yechim yetarli emas. Uchta qator unga ham kerak. "
            "Tez javob berib, keyin jimib ketmaslik uchun «hozir bandman» deb ayting."
        ),
        compatible=(
            "Bahs cho‘zilsa, muammoni bitta jumlada ayting va nima sinab ko‘rganingizni qo‘shing. "
            "«Keling, shuni tekshiramiz» desangiz, gap aylanib o‘tirmasligi mumkin."
        ),
        difficult=_use(
            "Muammo yopiladi, yozuv qolmaydi. Yechim: yechimdan keyin uchta qator yozing.",
            "Yig‘ilish cho‘zilsa, chiqib ketasiz. Yechim: oxiridagi qarorni so‘rab, shu qarorni yozing.",
            "Katta xaridni darrov qilasiz. Yechim: bir kecha kutib, ertalab narxni qayta o‘qing.",
        ),
        plan="1-kun: bitta yechimga uchta qator yozing. 7-kun: qaysi qarorni kechiktirganingiz foyda berganini belgilang.",
    ),
    "ENFP": _entry(
        title="Siz — yangi g‘oyaga tez isinadigan odamsiz.",
        summary=(
            "Sizda yangi imkoniyatni ko‘rib, odamlarni unga tortish odat bo‘lishi mumkin. "
            "Suhbatda kayfiyatni ko‘tarishingiz mumkin. "
            "Bir haftada bir nechta ish ochilsa, oxiri chala qolishi mumkin. "
            "Qiziqish tushsa, boshlagan narsani keyinga surishingiz mumkin.\n\n"
            "Masalan, dushanbada yangi to‘garak, chorshanbada loyiha, juma kuni esa do‘stingizga yordam va’da qilasiz. "
            "Yakshanba hech biri oxiriga yetmaganini ko‘rasiz."
        ),
        strengths=[
            "Boshlash. Yangi ishga odamni tez qo‘shib yuborishingiz mumkin.",
            "Aloqa. Turli odamlar orasida umumiy nuqta topishingiz mumkin.",
            "Kayf. Qiyin kunda ham bitta yo‘l ko‘rsatishingiz mumkin.",
        ],
        challenges=[
            "Bir nechta ishni birdan ochib, oxirini qoldirish",
            "Qiziqish tushganda boshlangan ishni surish",
        ],
        others=_use(
            "Yangi g‘oyani alohida ro‘yxatga yozing, bugungi ochiq ishni yopmaguncha boshlamang.",
            "Odam yig‘ganingizda bitta muddat va bitta mas’ulni ham yozing.",
            "Qiziqish tushsa, ishni tashlamang: 15 daqiqalik eng kichik qismni yoping.",
        ),
        advice="Bugun ochiq ishlardan bittasini tanlang, yangi g‘oyani alohida ro‘yxatga yozing.",
        motivation=(
            "Yangi to‘garak e’lonini ko‘rsangiz, darrov yozilishingiz mumkin. "
            "Eski topshiriq esa jildsiz qolib, kayf tushishi mumkin. "
            "Yangi narsani ro‘yxatga yozib, bugun eskisining bitta sahifasini yopsangiz, ikkalasi ham saqlanadi."
        ),
        work=(
            "Yangi odam, yangi mavzu va erkin taklif bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa yakun uchun bitta mas’ul va bitta muddat qo‘ysa, g‘oya chala qolmasligi mumkin. "
            "Har kuni yangi yo‘nalish ochilsa, hech biri tugamasligi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "yangi odam, yangi mavzu, erkin taklif, bitta aniq yakun."
        ),
        friendship=(
            "Ko‘p odam bilan tez chiqishasiz. Yaqinlik uchun haftada bitta odamga alohida vaqt qo‘ying. "
            "Va’dani kalendarga yozsangiz, kayf o‘tgach ham uchrashuv qoladi."
        ),
        relationship=(
            "Yaqin odam barqaror vaqt kutsa, har safar yangi reja taklif qilmang. "
            "Bitta kichik odat, masalan payshanba kechki qo‘ng‘iroq, ishonchni ushlashi mumkin."
        ),
        compatible=(
            "Bahsda yangi yo‘lni aytishdan oldin hozirgi ishning bitta ochiq joyini yoping. "
            "«Bu g‘oyani ro‘yxatga yozdim, bugun eskisini tugatamiz» desangiz, suhbat ham, ish ham yurishi mumkin."
        ),
        difficult=_use(
            "Bir haftada uchta ish ochiladi. Yechim: yangisini ro‘yxatga yozing, bugun bittasini yoping.",
            "Qiziqish tushsa, topshiriq yotadi. Yechim: 15 daqiqada eng kichik qismni bajaring.",
            "Va’da kayf bilan beriladi, keyin unutiladi. Yechim: va’dani darrov kalendarga qo‘ying.",
        ),
        plan="1-kun: ochiq ishlardan bittasini tanlang. 7-kun: yopilgan ish va ro‘yxatdagi g‘oyani ajrating.",
    ),
    "ENFJ": _entry(
        title="Siz — odamlarni bir joyga yig‘adigan odamsiz.",
        summary=(
            "Sizda guruhdagi odamni ko‘rib, ularni umumiy ishga chorlash odat bo‘lishi mumkin. "
            "Kimning kayfi tushganini sezishingiz mumkin. "
            "Maslahatni odam so‘ramasdan berib yuborishingiz mumkin. "
            "Hamma yaxshi bo‘lsin deb, o‘z damingizni unutishingiz mumkin.\n\n"
            "Masalan, kursdoshlar janjallashadi. Siz yarashtirasiz, keyin ikkalasining topshirig‘iga ham qaraysiz. "
            "Kechqurun o‘zingizga vaqt qolmaydi."
        ),
        strengths=[
            "Yig‘ish. Tarqalgan guruhni bitta ish atrofida tutishingiz mumkin.",
            "Sezish. Kim chetda qolganini payqab, uni gapga qo‘shishingiz mumkin.",
            "Mas’ul kayf. Qiyin kunda odamga aniq keyingi qadam aytishingiz mumkin.",
        ],
        challenges=[
            "So‘ralmagan maslahat berib, odamni siqish",
            "Hamma tinch bo‘lsin deb o‘z kuchingizni tugatish",
        ],
        others=_use(
            "Maslahatdan oldin «hozir eshitaymi yoki yo‘l aytaymi?» deb so‘rang.",
            "Guruh ishida o‘z qismingizni ham yozing, faqat boshqani boshlamang.",
            "Kechki damni bitta uchrashuv bilan to‘ldirmang.",
        ),
        advice="Bugun maslahat berishdan oldin «eshitaymi yoki yo‘l aytaymi?» deb so‘rang.",
        motivation=(
            "Guruh tarqalsa, siz yig‘ishga kuch sarflab, o‘z topshirig‘ingiz kechikishi mumkin. "
            "Do‘st xafa bo‘lsa, kechagacha yonida o‘tirib, ertalab darsga charchab borishingiz mumkin. "
            "Yordamga soat qo‘yish sizni ham, do‘stni ham saqlashi mumkin."
        ),
        work=(
            "Odamlar bilan, aniq maqsadli va rollari yozilgan ish sizga qulayroq kelishi mumkin. "
            "Jamoa sizdan ham yakun kutsa, faqat ruhlantirish emas, natija ham chiqadi. "
            "Cheksiz g‘amxo‘rlik muddatni yeyishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "odam bilan ish, aniq maqsad, yozilgan rol, o‘z damingiz saqlanadigan jadval."
        ),
        friendship=(
            "Do‘stlar sizni yig‘uvchi deb bilishi mumkin. Ba’zan o‘zingiz ham chaqirilishingiz kerak. "
            "Haftada bitta uchrashuvni boshqa odam tashkil qilsin, siz faqat boring."
        ),
        relationship=(
            "Yaqin odamning kayfini tuzatish sizning asosiy ishingiz emas. "
            "«Bugun men ham charchadim» desangiz, munosabat tengroq turishi mumkin."
        ),
        compatible=(
            "Nizo chiqsa, ikki tomonni emas, bitta keyingi qadamni ayting. "
            "«Hozir kim nima qiladi?» deb so‘rasangiz, yarashtirish sizda qolmasligi mumkin."
        ),
        difficult=_use(
            "So‘ralmagan maslahat odamni siqadi. Yechim: avval eshitish yoki yo‘l aytishni so‘rang.",
            "Hamma ishini o‘zingiz ushlaysiz. Yechim: o‘z qismingizni yozib, qolganiga mas’ul qo‘ying.",
            "Kechqurun ham yig‘asiz. Yechim: bitta kechki soatni bo‘sh qoldiring.",
        ),
        plan="1-kun: maslahatdan oldin savol bering. 7-kun: o‘zingiz dam olgan bitta kechqurunni belgilang.",
    ),
    "ENTJ": _entry(
        title="Siz — maqsad qo‘yib, ishni siljitadigan odamsiz.",
        summary=(
            "Sizda natijani ko‘rib, odamlarni shu natija tomon yurgizish odat bo‘lishi mumkin. "
            "Qaror tez chiqishi mumkin. "
            "Ohang qattiq bo‘lsa, to‘g‘ri gap ham og‘ir eshitilishi mumkin. "
            "Boshqaning sekin usulini vaqt yo‘qotish deb o‘qishingiz mumkin.\n\n"
            "Masalan, tadbirgacha ikki kun bor. Siz ro‘yxat yuborasiz va kechikkan kursdoshga qisqa yozasiz. "
            "Ish siljiydi, lekin u xabar sizni qo‘pol deb o‘qishi mumkin."
        ),
        strengths=[
            "Maqsad. Natijani oldindan qo‘yib, qadamni shunga bog‘lashingiz mumkin.",
            "Siljitish. To‘xtab qolgan ishni qayta yurgizishingiz mumkin.",
            "Qaror. Variant ko‘p bo‘lsa, bittasini tanlab olishingiz mumkin.",
        ],
        challenges=[
            "To‘g‘ri gapni qattiq ohangda aytish",
            "Sekinroq odamni susaygan deb o‘qish",
        ],
        others=_use(
            "Topshiriq yuborishdan oldin bitta yaxshi qadamni ham yozing.",
            "Qarorni aytgach, 10 daqiqa e’tiroz uchun qoldiring.",
            "Sekin odamga uning qismini va muddatini aniq bering, sur’atini o‘zingiznikiga tenglamang.",
        ),
        advice="Bugun bitta topshiriqdan oldin yaxshi qilingan joyini bir jumla qilib yozing.",
        motivation=(
            "Tadbir yoki musobaqa yaqin bo‘lsa, siz kechasi ham ro‘yxat yuborishingiz mumkin. "
            "Oddiy dars esa «natija yo‘q» bo‘lib, qo‘ldan kelmasligi mumkin. "
            "Oddiy darsga ham bitta ko‘rinadigan natija qo‘ysangiz, u ham siljishi mumkin."
        ),
        work=(
            "Aniq natija, qisqa qaror va mas’uliyati yozilgan ish sizga qulayroq kelishi mumkin. "
            "Jamoa e’tiroz uchun vaqt qoldirsa, odamlar siz bilan yurishi osonroq bo‘ladi. "
            "Faqat tezlik so‘raladigan joyda sifat va munosabat tushishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "aniq natija, qisqa qaror, yozilgan mas’uliyat, e’tiroz uchun vaqt."
        ),
        friendship=(
            "Do‘stni maqsadga tortish yaxshi, lekin har uchrashuv reja bo‘lmasin. "
            "Haftada bitta uchrashuvni natijasiz qoldiring: shunchaki yuring."
        ),
        relationship=(
            "Yaqin odam yechimdan oldin eshitilishni xohlashi mumkin. "
            "Avval «eshitdim» deng, keyin qadamni ayting. Aks holda g‘amxo‘rlik buyruqdek tuyuladi."
        ),
        compatible=(
            "Qattiq xabardan oldin bitta aniq yaxshi joyni yozing. "
            "«Ro‘yxat kerak, lekin kechagi qisming to‘g‘ri edi» desangiz, ish ham, ohang ham turadi."
        ),
        difficult=_use(
            "Qisqa xabar qo‘pol eshitiladi. Yechim: oldiga bitta yaxshi jumla qo‘ying.",
            "Qarorni darrov yopasiz. Yechim: 10 daqiqa e’tiroz uchun qoldiring.",
            "Sekin odamga jahlingiz chiqadi. Yechim: uning qismi va muddatini yozing, sur’atini tenglamang.",
        ),
        plan="1-kun: bitta xabarga yaxshi jumla qo‘shing. 7-kun: qaysi qarorga e’tiroz vaqti qolganini yozing.",
    ),
    "ENTP": _entry(
        title="Siz — savol berib, boshqa yo‘l qidiradigan odamsiz.",
        summary=(
            "Sizda tayyor javobga savol qo‘yib, boshqa yo‘l qidirish odat bo‘lishi mumkin. "
            "Bahsda tez javob topishingiz mumkin. "
            "Yangi g‘oya eski ishning mayda qismini surib qo‘yishi mumkin. "
            "Tafsilot zerikarli bo‘lsa, uni boshqaga qoldirishingiz mumkin.\n\n"
            "Masalan, referatning kirish qismi sizga qiziq. Manba ro‘yxati esa qoladi. "
            "Muhokamada g‘alaba qilasiz, lekin fayl kechasi ham ochiq turadi."
        ),
        strengths=[
            "Savol. Tayyor javobning teshigini tez ko‘rishingiz mumkin.",
            "Yo‘l. Tiqilib qolgan ishga boshqa variant taklif qilishingiz mumkin.",
            "Muhokama. Qiyin mavzuni jonli qilib tushuntirishingiz mumkin.",
        ],
        challenges=[
            "Yangi g‘oya uchun boshlangan ishning oxirini qoldirish",
            "Bahsda odamning gapini to‘liq olmaslik",
        ],
        others=_use(
            "Yangi g‘oyani alohida ro‘yxatga yozing, bugungi mayda qismni yoping.",
            "Bahsda javobdan oldin suhbatdoshning jumlasini bir marta qaytaring.",
            "Manba, muddat, ism kabi mayda qismga 10 daqiqa alohida qo‘ying.",
        ),
        advice="Bugun chala ishning bitta mayda qismini yoping, yangi g‘oyani ro‘yxatga yozing.",
        motivation=(
            "Munozara yoki yangi mavzu bo‘lsa, kechgacha o‘tirishingiz mumkin. "
            "Manba ro‘yxati va jild esa ochiq qolishi mumkin. "
            "Mayda qismga alohida 10 daqiqa qo‘ysangiz, qiziq qism ham, hujjat ham tugashi mumkin."
        ),
        work=(
            "Savol qo‘yish, variant qidirish va qisqa muhokama bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa yakun uchun mayda ro‘yxatni alohida qadam qilsa, g‘oya qog‘ozda qoladi. "
            "Cheksiz bahs muddatni yeyishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "ochiq savol, qisqa muhokama, yangi variant, alohida yoziladigan mayda qism."
        ),
        friendship=(
            "Do‘st bilan bahslashish sizga o‘yindek kelishi mumkin. "
            "U xafa bo‘lsa, avval uning jumlasini qaytaring, keyin hazil qiling."
        ),
        relationship=(
            "Yaqin odam har gapingizni sinov deb o‘qimasin. Muhim mavzuda «hozir jiddiy aytayapman» deb boshlang. "
            "Yangi reja taklif qilishdan oldin bugungi va’dani yoping."
        ),
        compatible=(
            "E’tirozni aytishdan oldin bitta kuchli joyni tan oling. "
            "«Bu joy ishlaydi, mana bu joy teshik» desangiz, bahs yopilishi mumkin."
        ),
        difficult=_use(
            "Yangi g‘oya eski ishni suradi. Yechim: g‘oyani ro‘yxatga yozing, bugun mayda qismni yoping.",
            "Bahsda odamni bo‘lib yuborasiz. Yechim: javobdan oldin uning jumlasini qaytaring.",
            "Manba ro‘yxati ochiq qoladi. Yechim: unga alohida 10 daqiqa qo‘ying.",
        ),
        plan="1-kun: mayda qismni yoping. 7-kun: ro‘yxatdagi g‘oya bilan yopilgan ishni ajrating.",
    ),
    "ESFP": _entry(
        title="Siz — hozirgi lahzani jonlantiradigan odamsiz.",
        summary=(
            "Sizda odamlar orasida kayfni ko‘tarish va hozirgi vaziyatga tez qo‘shilish odat bo‘lishi mumkin. "
            "Amaliy ishni darrov boshlashingiz mumkin. "
            "Keyingi kunning mayda ro‘yxati esa qolib ketishi mumkin. "
            "His kuchli bo‘lsa, xabar yoki qaror shoshilinch chiqishi mumkin.\n\n"
            "Masalan, do‘stlar to‘satdan choyxona taklif qiladi. Siz borasiz va hamma kayfini ko‘tarasiz. "
            "Ertasi kuni topshiriq ochilmaganini ko‘rasiz."
        ),
        strengths=[
            "Hozirgi lahza. Yangi joyda odamni tez erkin qilishingiz mumkin.",
            "Boshlash. Muhokama cho‘zilsa, ishni qo‘lga olishingiz mumkin.",
            "Kayf. Qiyin kunda ham bitta yengil qadam topishingiz mumkin.",
        ],
        challenges=[
            "Bugungi kayf ertangi mayda ishni surib qo‘yishi",
            "Kuchli his bilan shoshilinch xabar yozish",
        ],
        others=_use(
            "Chiqishdan oldin ertangi bitta ishni 15 daqiqaga qo‘ying.",
            "Kuchli hisda xabarni qoralab, 20 daqiqadan keyin yuboring.",
            "Kuniga uchta ishdan bittasini ertalab yozing.",
        ),
        advice="Bugun chiqishdan oldin ertangi bitta ishga 15 daqiqa qo‘ying.",
        motivation=(
            "Do‘stlar chaqirsa, siz darrov qo‘shilib, kechasi quvnoq qaytishingiz mumkin. "
            "Ertasi kuni esa jadval bo‘sh bo‘lib, ish og‘ir tuyulishi mumkin. "
            "Chiqish oldidan 15 daqiqa qo‘yish ertalabki og‘irlikni yumshatishi mumkin."
        ),
        work=(
            "Odam bor, harakat bor va natijasi ko‘rinadigan ish sizga qulayroq kelishi mumkin. "
            "Jamoa ertalabki uchta ishni yozsa, kayf ishni yeb qo‘ymasligi mumkin. "
            "Uzoq yolg‘iz hisobot sizni tez charchatishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "odam bor joy, ko‘rinadigan harakat, qisqa natija, ertalabki kichik ro‘yxat."
        ),
        friendship=(
            "Do‘stlar sizni chaqirishni yaxshi ko‘radi. Siz ham ba’zan rejani o‘zingiz yozing, aks holda kunlar tasodif bo‘lib qoladi. "
            "Bitta yaqin odamga alohida vaqt qo‘ying, hammasi katta davrada qolmasin."
        ),
        relationship=(
            "Yaqin odam tinch kechqurun kutsa, har safar yangi joy taklif qilmang. "
            "Haftada bitta oddiy uy kechasi ham yaqinlikni ushlashi mumkin."
        ),
        compatible=(
            "Xafa bo‘lganingizda xabarni darrov yubormang. 20 daqiqa kutib, bitta aniq jumla yozing. "
            "«Hozir og‘ir, kechroq gaplashamiz» desangiz, kayf gapni buzmasligi mumkin."
        ),
        difficult=_use(
            "Chiqish ertangi ishni yeydi. Yechim: chiqishdan oldin 15 daqiqa qo‘ying.",
            "His bilan xabar ketadi. Yechim: qoralang, 20 daqiqadan keyin yuboring.",
            "Kun bo‘sh qoladi. Yechim: ertalab uchta ishdan bittasini yozing.",
        ),
        plan="1-kun: chiqish oldidan 15 daqiqa qo‘ying. 7-kun: qaysi ish shu 15 daqiqada yopilganini belgilang.",
    ),
    "ESFJ": _entry(
        title="Siz — guruh kayfini ushlab turadigan odamsiz.",
        summary=(
            "Sizda odam o‘zini qulay sezishi uchun mayda narsani eslab, guruhni bir joyda tutish odat bo‘lishi mumkin. "
            "Mehmon, guruh ishi yoki oila yig‘inida tartib sizdan chiqishi mumkin. "
            "Hamma rozi bo‘lsin deb, o‘z charchog‘ingizni yashirishingiz mumkin. "
            "Minnatdorlik sezilmasa, kajingiz chiqishi mumkin.\n\n"
            "Masalan, tug‘ilgan kun dasturxoni uchun ro‘yxat, joy va kim nima olib kelishini siz yozasiz. "
            "Kechqurun hamma rahmat deydi, siz esa idish yuvib charchaysiz."
        ),
        strengths=[
            "Eslab qolish. Guruhga nima kerakligini oldindan yozib qo‘yishingiz mumkin.",
            "Mehmondo‘stlik. Yangi odamni davraga qo‘shishingiz mumkin.",
            "Tartib. Tarqalgan tayyorgarlikni bitta ro‘yxatga yig‘ishingiz mumkin.",
        ],
        challenges=[
            "Hamma rozi bo‘lsin deb o‘z yukingizni oshirish",
            "Rahmat eshitilmasa, ichingizda qolish",
        ],
        others=_use(
            "Ro‘yxat tuzganingizda o‘zingizdan boshqa ikki kishiga ham qator yozing.",
            "Charchaganingizni kechqurun ayting, idish ustida jim yurmang.",
            "Bitta iltimosni rad etish uchun oldindan tayyor jumla yozing.",
        ),
        advice="Bugun guruh ishidan bitta qatorni boshqa odamning yoniga yozing.",
        motivation=(
            "Yig‘in yaqin bo‘lsa, siz kechasi ham ro‘yxat yuborishingiz mumkin. "
            "Hech kim qo‘shilmasa, kajingiz chiqib, keyingi safar hammasini yana o‘zingiz olishingiz mumkin. "
            "Ikki kishiga aniq qator bersangiz, yuk bo‘linadi."
        ),
        work=(
            "Odam bilan, aniq mehmon yoki mijoz bor, tartibi yoziladigan ish sizga qulayroq kelishi mumkin. "
            "Jamoa rahmatni va mas’uliyatni ochiq aytsa, siz ortiqcha yuk olmasligingiz mumkin. "
            "Hamma sizdan kutadigan joyda charchoq tez yig‘iladi."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "odam bilan ish, yozilgan ro‘yxat, bo‘lingan vazifa, ochiq rahmat."
        ),
        friendship=(
            "Do‘stlar sizni yig‘uvchi deb biladi. Siz ham ba’zan mehmon bo‘ling. "
            "«Bu safar ro‘yxatni sen yoz» desangiz, do‘stlik tengroq turishi mumkin."
        ),
        relationship=(
            "Yaqin odam sizning mehnatingizni ko‘rmasligi mumkin, chunki siz jim qilasiz. "
            "Bitta ishni ayting: «bugun men shuni qildim, endi dam olaman»."
        ),
        compatible=(
            "Ichkarida qolgan kajni kechki xabarda ayting. "
            "«Yordam kerak edi, jim qoldim» desangiz, keyingi safar yuk bo‘linishi mumkin."
        ),
        difficult=_use(
            "Hammasini o‘zingiz qilasiz. Yechim: ro‘yxatda ikki kishiga qator yozing.",
            "Rahmat yo‘q, ichingizda qolasiz. Yechim: kechqurun bitta jumla ayting.",
            "Rad eta olmaysiz. Yechim: «bu safar sig‘maydi» degan jumlani oldindan yozib qo‘ying.",
        ),
        plan="1-kun: bitta qatorni boshqaga yozing. 7-kun: o‘zingiz dam olgan yig‘inni belgilang.",
    ),
    "ESTJ": _entry(
        title="Siz — mas’uliyatli va tartibli odamsiz.",
        summary=(
            "Sizda ish tarqasa, muddat va tartibni eslatish odat bo‘lishi mumkin. "
            "Kim nima qilishini yozib qo‘ysangiz, guruh yurishi mumkin. "
            "Tuzatishni maqtovdan oldin aytib yuborishingiz mumkin. "
            "O‘z sur’atingizni boshqadan ham kutishingiz mumkin.\n\n"
            "Masalan, umumiy hujjatda kursdosh o‘z qatorini to‘ldirmaydi. "
            "Siz eslatma yozasiz va kechqurun o‘zingiz to‘ldirasiz. Hujjat chiqadi, lekin ichingizda kaj qoladi."
        ),
        strengths=[
            "Muddat. Topshiriq qachon tugashini ushlab turishingiz mumkin.",
            "Tartib. Tarqalgan ishni qatorlarga bo‘lib berishingiz mumkin.",
            "Mas’uliyat. Aytgan ishni o‘z bo‘yningizga olishingiz mumkin.",
        ],
        challenges=[
            "Tuzatishni yaxshi tomondan oldin aytish",
            "O‘z sur’atingizni hammaniniki deb kutish",
        ],
        others=_use(
            "Eslatmadan oldin bitta to‘g‘ri qilingan joyini yozing.",
            "O‘zingiz yopmang: qatorni odamning yoniga yozib, muddat qo‘ying.",
            "Sur’ati boshqacha odamga uning qismini kichikroq bering.",
        ),
        advice="Bugun tuzatish yozishdan oldin bitta aniq yaxshi narsani ayting.",
        motivation=(
            "Muddat yaqin bo‘lsa, siz ro‘yxat yuborib, guruhni yurgizishingiz mumkin. "
            "Hech kim qatorini yozmasa, kechasi hammasini o‘zingiz yopishingiz mumkin. "
            "Bitta yaxshi jumla va aniq muddat eslatmani yumshatib, ishni baribir siljitishi mumkin."
        ),
        work=(
            "Aniq muddat, tekshiriladigan natija va bo‘lingan vazifa bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa sizning tartibingizni eshitsa, lekin ohangni ham ko‘rsa, odamlar yonida turadi. "
            "Faqat nazorat so‘raladigan joyda kaj tez yig‘iladi."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "aniq muddat, bo‘lingan vazifa, tekshiriladigan natija, qisqa yozma eslatma."
        ),
        friendship=(
            "Do‘stlar sizni ishonchli deb bilishi mumkin, chunki vaqtingizda kelasiz. "
            "Ular kechiksa, avval sababini so‘rang, keyin keyingi aniq vaqtni yozing."
        ),
        relationship=(
            "Yaqin odam tartibni nazorat deb o‘qishi mumkin. Bitta muhim qoidani ayting, mayda joyini qo‘yib bering. "
            "«Menga vaqt muhim, qolganini sen tanla» desangiz, ohang yumshashi mumkin."
        ),
        compatible=(
            "Tuzatish xabarida avval yaxshi joy, keyin o‘zgarish bo‘lsin. "
            "«Jadval to‘g‘ri, mana bu qator bo‘sh» desangiz, odam yopilib qolmasligi mumkin."
        ),
        difficult=_use(
            "Eslatma qattiq chiqadi. Yechim: oldiga bitta yaxshi jumla qo‘ying.",
            "Bo‘sh qatorni o‘zingiz yopasiz. Yechim: qatorni odamga yozib, muddat qo‘ying.",
            "Sekin odamga jahlingiz chiqadi. Yechim: uning qismini kichikroq qilib bering.",
        ),
        plan="1-kun: tuzatishdan oldin yaxshi jumla yozing. 7-kun: o‘zingiz yopmagan bitta qatorni belgilang.",
    ),
    "ESTP": _entry(
        title="Siz — vaziyatni kechiktirmay hal qiladigan odamsiz.",
        summary=(
            "Sizda muammo chiqsa, kutmasdan yo‘l qidirish odat bo‘lishi mumkin. "
            "Harakat bor joyda tez ochilishingiz mumkin. "
            "Zerikarli mayda qism sizni to‘xtatishi mumkin. "
            "Katta qarorda ham shu tezlikni ishlatsangiz, keyin tuzatish ko‘p bo‘lishi mumkin.\n\n"
            "Masalan, guruh kechikib, zalni bron qilolmaydi. Siz boshqa joyni darrov topasiz. "
            "Yig‘ilish bo‘ladi, lekin kim to‘laydi va qanday boriladi yozilmaydi."
        ),
        strengths=[
            "Tezlik. To‘xtab qolgan vaziyatda yo‘l topishingiz mumkin.",
            "Jasorat. Yangi joyda birinchi bo‘lib gapirish yoki sinash mumkin.",
            "Amaliyot. Nazariya cho‘zilsa, ishlaydigan variantni tekshirishingiz mumkin.",
        ],
        challenges=[
            "Mayda shartni yozmasdan keyingi ishga o‘tish",
            "Katta qarorni bir kecha kutmasdan yopish",
        ],
        others=_use(
            "Tez yechimdan keyin kim, qachon, qancha deb uchta qator yozing.",
            "Zerikarli qismga 20 daqiqa qo‘ying va shu vaqtni boshqa ish bilan almashtirmang.",
            "Katta xariddan oldin bir kecha kutib, ertalab raqamlarni qayta o‘qing.",
        ),
        advice="Bugun tez yechgan ishning uchta shartini yozing: kim, qachon, qancha.",
        motivation=(
            "Musobaqa yoki shoshilinch ish bo‘lsa, siz darrov joyidasiz. "
            "Oddiy forma va mayda shart esa ochiq qolishi mumkin. "
            "Ularga 20 daqiqa qo‘ysangiz, tez yechim ham tugagan hisoblanadi."
        ),
        work=(
            "Harakat, tez natija va ozgina musobaqa bor ish sizga qulayroq kelishi mumkin. "
            "Jamoa mayda shartni sizdan yozma so‘rasa, keyingi odam ham tushunadi. "
            "Uzoq tayyorgarlik va cheksiz hujjat sizni chiqarib yuborishi mumkin."
        ),
        career=(
            "Aniq kasb va’dasi emas. Sizga yengilroq kelishi mumkin bo‘lgan sharoit: "
            "tez natija, harakat, qisqa qaror, yozib qo‘yiladigan mayda shart."
        ),
        friendship=(
            "Do‘stlar shoshilinch paytda sizni chaqirishi mumkin. "
            "Oddiy kunda ham bitta xabar yozing, yaqinlik faqat muammoga bog‘lanib qolmasin."
        ),
        relationship=(
            "Yaqin odam reja va tinch vaqt kutsa, har safar yangi sarguzasht taklif qilmang. "
            "Bitta oldindan yozilgan kechqurun ishonchni ushlashi mumkin."
        ),
        compatible=(
            "Qattiq javobdan oldin bir nafas oling va nima kerakligini raqam bilan ayting. "
            "«Bugun shu summa, ertaga qolgani» desangiz, shoshilish adashishga aylanmasligi mumkin."
        ),
        difficult=_use(
            "Joy topiladi, shart yozilmaydi. Yechim: kim, qachon, qancha deb uchta qator yozing.",
            "Zerikarli forma ochiq qoladi. Yechim: unga 20 daqiqa qo‘ying.",
            "Katta xarid darrov bo‘ladi. Yechim: bir kecha kutib, ertalab raqamni qayta o‘qing.",
        ),
        plan="1-kun: uchta shartni yozing. 7-kun: kechiktirilgan katta qaror foyda berdimi, belgilang.",
    ),
}


def get_result_copy(personality_type: str) -> ResultCopy:
    from app.seed.growth_guidance_schema import format_action_plan
    from app.seed.personality_guidance_uz import PERSONALITY_GROWTH_UZ

    key = personality_type.upper()
    base = PERSONALITY_RESULTS_UZ.get(key, GENERIC_FALLBACK)
    if key not in PERSONALITY_GROWTH_UZ:
        return base
    areas = PERSONALITY_GROWTH_UZ[key]
    merged: ResultCopy = {
        **base,
        "action_plan": format_action_plan(areas[0]),
        "daily_tips": list(areas[0]["steps"][:3]),
    }
    return merged
