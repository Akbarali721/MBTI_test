"""16 MBTI turi uchun o‘zbekcha natija matnlari (placeholder yo‘q)."""

from typing import TypedDict


class ResultCopy(TypedDict):
    title: str
    short_description: str
    strengths: list[str]
    challenges: list[str]
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
        "Natija sizning javoblaringiz asosida shakllangan. Bu sizning qadriyatlar, "
        "energiya manbai va qaror qabul qilish uslubingiz haqida umumiy tasvir."
    ),
    "strengths": [
        "Vaziyatga moslashish va o‘rganishga tayyorlik",
        "O‘z kuchli tomonlaringizni amalda sinab ko‘rish",
        "Muloqotda ochiq va samimiy bo‘lish",
    ],
    "challenges": [
        "Juda ko‘p yo‘nalishda bir vaqtda harakat qilish",
        "O‘z chegaralaringizni aniq aytmaslik",
    ],
    "public_view": "Atrofdagilar sizni xotirjam, muloqotga ochiq va o‘z yo‘lingizni qidirayotgan inson deb ko‘rishlari mumkin.",
    "advice": "Kuchli tomonlaringizni kundalik kichik qadamlarda ishlating; bir vaqtning o‘zida hamma narsani o‘zgartirmang.",
    "motivation_analysis": "Motivatsiya sizga ma’noli maqsad va aniq kichik yutuqlar bo‘lganda barqarorroq bo‘ladi.",
    "work_style": "Reja va moslashuv muvozanatida ishlash sizga yaxshi keladi.",
    "career_environment": "Hurmat, aniq vazifalar va o‘sish imkoniyati bo‘lgan muhit qulay.",
    "friendship_style": "Sodda muloqot va o‘zaro ishonch siz uchun muhim.",
    "relationship_needs": "Tushunish, hurmat va bir-biringizga vaqt ajratish.",
    "compatible_people": "Vaziyatni tinch muhokama qiladigan va qo‘llab-quvvatlaydigan odamlar.",
    "difficult_communication": "Faol bosim va hurmatsiz muloqot sizni charchatishi mumkin.",
    "action_plan": "1-kun: kuchli tomoningizni bitta vazifada sinab ko‘ring. 7-kungacha har kuni bitta kichik qadam qo‘shing.",
}


def _entry(
    title: str,
    summary: str,
    strengths: list[str],
    challenges: list[str],
    others: str,
    advice: str,
    premium_base: str,
) -> ResultCopy:
    return {
        "title": title,
        "short_description": summary,
        "strengths": strengths,
        "challenges": challenges,
        "public_view": others,
        "advice": advice,
        "motivation_analysis": f"{premium_base} Motivatsiyangiz maqsad aniq va natija ko‘rinadigan bo‘lganda oshadi.",
        "work_style": f"{premium_base} Sizga tartib va moslashuv muvozanati mos keladi.",
        "career_environment": f"{premium_base} Aniq rollar va hurmatli jamoa muhiti qulay.",
        "friendship_style": f"{premium_base} Chuqur suhbat va ishonchli do‘stlik sizga yaqin.",
        "relationship_needs": f"{premium_base} O‘zaro tushunish va barqaror aloqa muhim.",
        "compatible_people": f"{premium_base} Vaznyu va samimiy odamlar bilan yaxshi hamkorlik qilasiz.",
        "difficult_communication": f"{premium_base} Keskin tanqid va noaniq kutishlar muloqotni qiyinlashtiradi.",
        "action_plan": f"{premium_base} Bir hafta davomida har kuni bitta kuchli tomoningizni ataylab ishlating va natijani yozib boring.",
    }


PERSONALITY_RESULTS_UZ: dict[str, ResultCopy] = {
    "INFP": _entry(
        "Tushkunlik izlovchi va qadriyatga sodiq",
        "Siz ichki qadriyatlar, ma’no va shaxsiy o‘sishga yo‘naltirilgansiz. G‘oya va odamlarga chuqur munosabatda bo‘lasiz.",
        ["Empatiya va chuqur tinglash", "Ijodkor fikrlash", "Sodiq va samimiy munosabatlar"],
        ["O‘z ehtiyojini ifoda etishda kechikish", "Konfliktdan qochish"],
        "Boshqalar sizni muloyim, orzu qiluvchi va ichki dunyosi boy inson deb bilishadi.",
        "Kundalik hayotda kichik, lekin qadriyatingizga mos qadamlar rejalashtiring.",
        "INFP tipi uchun",
    ),
    "INFJ": _entry(
        "Ma’noli yo‘l izlovchi strateg",
        "Uzoq muddatli maqsad va odamlarga yordam berish sizga muhim. Intuitsiya va tizimli fikrlash uyg‘unlashadi.",
        ["Uzoq muddatli reja tuzish", "Empatiya bilan maslahat berish", "Ma’no izlash"],
        ["O‘z ehtiyojini e’tiborsiz qoldirish", "Juda yuqori standart"],
        "Sizni dono, muloyim va maqsadli odam sifatida ko‘rishadi.",
        "Energiyangizni tiklash uchun yolg‘iz vaqt ajrating.",
        "INFJ tipi uchun",
    ),
    "INTJ": _entry(
        "Mustaqil strateg va tizim quruvchi",
        "Siz samaradorlik, aniq maqsad va uzoq muddatli yechimlarni qadrlaysiz.",
        ["Strategik rejalashtirish", "Mustaqil qaror", "Murakkab muammolarni tahlil qilish"],
        ["Boshqalarning sekinligiga sabrsizlik", "His-tuyg‘uni e’tiborsiz qoldirish"],
        "Atrofdagilar sizni jiddiy, aqlli va maqsadli deb bilishadi.",
        "Jamoa bilan maqsadni aniq ulashing — yolg‘iz qolmaslik uchun.",
        "INTJ tipi uchun",
    ),
    "INTP": _entry(
        "Tahlilchi va g‘oya izlovchi",
        "Siz narsalar qanday ishlashini tushunishni va mantiqiy tizimlar qurishni yaxshi ko‘rasiz.",
        ["Mantiqiy tahlil", "Yangi g‘oyalar", "Mustaqil o‘rganish"],
        ["Amalga oshirishda kechikish", "Emotsional mavzulardan qochish"],
        "Sizni o‘ylovchi, qiziquvchan va mustaqil deb ko‘rishadi.",
        "G‘oyani kichik sinov bosqichiga aylantiring — faqat o‘ylamasdan.",
        "INTP tipi uchun",
    ),
    "ISFP": _entry(
        "Hissiy va estetik qadriyatlarga ega",
        "Siz hozirgi lahzani, chiroyli tafsilotlarni va shaxsiy erkinlikni qadrlaysiz.",
        ["San’at va amaliy yondashuv", "Empatiya", "Moslashuvchanlik"],
        ["Uzoq muddatli reja tuzishda qiyinchilik", "Keskin tanqidga sezgirlik"],
        "Sizni yumshoq, samimiy va yaxshi kayfiyat tarqatuvchi deb bilishadi.",
        "Kundalik rejada ijod yoki tabiat bilan vaqt ajrating.",
        "ISFP tipi uchun",
    ),
    "ISFJ": _entry(
        "G‘amxo‘r va ishonchli qo‘llab-quvvatlovchi",
        "Siz yaqinlaringiz va jamoa farqini seziladi qilasiz, an’anaviy va barqarorlikni qadrlaysiz.",
        ["E’tiborli va sodiq", "Tafsilotlarni eslab qolish", "Amaliy yordam"],
        ["O‘z ehtiyojini ikkinchi reja qilish", "O‘zgarishdan xavotir"],
        "Sizni ishonchli, mehribon va mas’uliyatli deb bilishadi.",
        "Yordam berishdan oldin o‘zingizga ham vaqt ajratishni odat qiling.",
        "ISFJ tipi uchun",
    ),
    "ISTJ": _entry(
        "Tartibli va mas’uliyatli ijrochi",
        "Siz qoidalar, aniq vazifalar va ishonchli natija muhim deb bilasiz.",
        ["Tartib va reja", "Ishonchlilik", "Amaliy tajriba"],
        ["Kutilmagan o‘zgarishga qarshilik", "Moslashuvchanlik yetishmasligi"],
        "Sizni jiddiy, ishonchli va o‘z so‘zining odami deb ko‘rishadi.",
        "Rejada moslashuv uchun kichik bo‘sh joy qoldiring.",
        "ISTJ tipi uchun",
    ),
    "ISTP": _entry(
        "Amaliy muammolarni hal qiluvchi",
        "Siz qo‘l bilan ishlash, tez tahlil va mustaqil harakatni yaxshi ko‘rasiz.",
        ["Tez qaror va amal", "Texnik tafakkur", "Sokinlik ostida samaradorlik"],
        ["Uzoq munosabatda his-tuyg‘u ifodasi", "Qoidalar ortiqcha bo‘lsa charchash"],
        "Sizni xotirjam, mustaqil va ishonchli deb bilishadi.",
        "Muhim qarorlarni yozib, keyinroq qayta ko‘rib chiqing.",
        "ISTP tipi uchun",
    ),
    "ENFP": _entry(
        "Ilhomlantiruvchi va g‘oya bilan yashovchi",
        "Siz yangilik, odamlar va imkoniyatlar sizni rag‘batlantiradi.",
        ["Ijodkor energiya", "Muloqotda iliqlik", "Yangi loyihalarni boshlash"],
        ["Tugatish bosqichida diqqatni yo‘qotish", "Haddan tashqari band bo‘lish"],
        "Sizni quvnoq, ochiq va ilhomli odam deb bilishadi.",
        "Bir vaqtda kamroq loyiha tanlang va ularni yakunlang.",
        "ENFP tipi uchun",
    ),
    "ENFJ": _entry(
        "Odamlarni birlashtiruvchi yetakchi",
        "Siz boshqalarning o‘sishiga yordam berish va ma’nobaxsh maqsadlar muhim.",
        ["Xarizmatik muloqot", "Guruhda motivatsiya", "Empatiya"],
        ["O‘z ehtiyojini unutish", "Haddan tashqari mas’uliyat hissi"],
        "Sizni g‘ayratli, g‘amxo‘r va yo‘naltiruvchi deb ko‘rishadi.",
        "Yordam berish va dam olish vaqtini rejalashtiring.",
        "ENFJ tipi uchun",
    ),
    "ENTJ": _entry(
        "Qarorli strateg va tashkilotchi",
        "Siz samaradorlik, aniq maqsad va natijaga yo‘naltirilgansiz.",
        ["Yetakchilik", "Uzoq muddatli reja", "Tez qaror qabul qilish"],
        ["Boshqalarning his-tuyg‘usini e’tiborsiz qoldirish", "Juda keskin muloqot"],
        "Sizni kuchli, maqsadli va ishonchli deb bilishadi.",
        "Jamoa fikrini tinglash uchun aniq vaqt belgilang.",
        "ENTJ tipi uchun",
    ),
    "ENTP": _entry(
        "Munozarali va yangi yechim izlovchi",
        "Siz g‘oyalar, mantiqqiy o‘yin va chegaralarni sinashni yaxshi ko‘rasiz.",
        ["Tez fikrlash", "Innovatsiya", "Muloqotda joziba"],
        ["Rutinada charchash", "Tafsilotlarni kechiktirish"],
        "Sizni aqlli, quvnoq va qiziqarli suhbatdosh deb bilishadi.",
        "Eng yaxshi g‘oyani bittasini tanlab, amalga oshirish rejasini yozing.",
        "ENTP tipi uchun",
    ),
    "ESFP": _entry(
        "Jonli va hozirgi lahzani qadrlaydigan",
        "Siz odamlar, tajriba va quvnoq muhitdan energiya olasiz.",
        ["Ijtimoiy energiya", "Moslashuv", "Amaliy yordam"],
        ["Uzoq muddatli reja", "Tanqidga sezgirlik"],
        "Sizni ochiq, samimiy va yorqin deb ko‘rishadi.",
        "Katta qarorlardan oldin qisqa yozma reja tuzing.",
        "ESFP tipi uchun",
    ),
    "ESFJ": _entry(
        "Jamoa ruhini qo‘llab-quvvatlovchi",
        "Siz hamjamiyat, an’analar va yaqinlar farqi muhim deb bilasiz.",
        ["Mehribonlik", "Tashkilotchilik", "Sodiq munosabat"],
        ["Tanqiddan qo‘rquv", "O‘z ehtiyojini e’tiborsiz qoldirish"],
        "Sizni g‘amxo‘r, ishonchli va yordam beruvchi deb bilishadi.",
        "Yordam so‘rash — ham munosabatning bir qismi.",
        "ESFJ tipi uchun",
    ),
    "ESTJ": _entry(
        "Tartib va natijaga yo‘naltirilgan",
        "Siz aniq qoidalar, mas’uliyat va samaradorlikni qadrlaysiz.",
        ["Tashkilot", "Tez ijro", "Aniqlik"],
        ["Moslashuvchanlik yetishmasligi", "Emotsional nuanslarni e’tiborsiz qoldirish"],
        "Sizni ishonchli, jiddiy va tartibli deb ko‘rishadi.",
        "Jamoa bilan o‘zgarishlarni oldindan muhokama qiling.",
        "ESTJ tipi uchun",
    ),
    "ESTP": _entry(
        "Harakat va imkoniyat izlovchi",
        "Siz tez qaror, amal va yangi tajribadan quvvat olasiz.",
        ["Tez reaksiya", "Amaliy yechim", "Ijtimoiy joziba"],
        ["Uzoq reja", "Sabr talab qiladigan vazifalar"],
        "Sizni jasur, ochiq va energiyali deb bilishadi.",
        "Muhim loyihalar uchun qisqa muddatli reja va deadline qo‘ying.",
        "ESTP tipi uchun",
    ),
}


def get_result_copy(personality_type: str) -> ResultCopy:
    key = personality_type.upper()
    return PERSONALITY_RESULTS_UZ.get(key, GENERIC_FALLBACK)
