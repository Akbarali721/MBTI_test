"""16 MBTI turi uchun o‘zbekcha natija matnlari (placeholder yo‘q).

Premium bo‘limlar (motivatsiya, ish uslubi, kasb, do‘stlik, munosabat, mos odamlar,
qiyin muloqot, 7 kunlik reja) har tur uchun alohida yozilgan — ruscha modul bilan
bir xil tuzilma va bir xil ma’no.
"""

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
    "public_view": (
        "Atrofdagilar sizni xotirjam, muloqotga ochiq va o‘z yo‘lini qidirayotgan inson deb ko‘rishlari mumkin."
    ),
    "advice": (
        "Kuchli tomonlaringizni kundalik kichik qadamlarda ishlating; bir vaqtning o‘zida "
        "hamma narsani o‘zgartirmang."
    ),
    "motivation_analysis": (
        "Motivatsiya sizda ma’noli maqsad va ko‘zga ko‘rinadigan kichik yutuqlar bo‘lganda barqarorroq bo‘ladi."
    ),
    "work_style": "Reja va moslashuv muvozanatda bo‘lgan ish sizga yaxshi keladi.",
    "career_environment": "Hurmat, aniq vazifalar va o‘sish imkoniyati bor muhit sizga qulay.",
    "friendship_style": "Siz uchun sodda, to‘g‘ridan-to‘g‘ri muloqot va o‘zaro ishonch muhim.",
    "relationship_needs": "Tushunish, hurmat va bir-biringizga ataylab ajratilgan vaqt.",
    "compatible_people": (
        "Murakkab mavzuni tinch muhokama qila oladigan va baho bermay qo‘llab-quvvatlaydigan odamlar."
    ),
    "difficult_communication": "Bosim va hurmatsiz ohang sizni tez charchatadi.",
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


PERSONALITY_RESULTS_UZ: dict[str, ResultCopy] = {
    "INFP": _entry(
        title="Ma’no izlovchi va qadriyatiga sodiq inson",
        summary=(
            "Siz ichki qadriyatlar, ma’no va shaxsiy o‘sishga yo‘naltirilgansiz. "
            "G‘oyalarga ham, odamlarga ham chuqur va jiddiy munosabatda bo‘lasiz."
        ),
        strengths=[
            "Empatiya va chinakam tinglay olish",
            "Ijodiy, obrazli fikrlash",
            "Munosabatlarda sodiqlik va samimiylik",
        ],
        challenges=[
            "O‘z ehtiyojingiz haqidagi suhbatni keyinga surish",
            "Ziddiyatni oydinlashtirish o‘rniga undan chetlanish",
        ],
        others="Boshqalar sizni muloyim, xayolparast va ichki dunyosi boy inson deb ko‘rishadi.",
        advice="Qadriyatlaringizga mos keladigan kichik kundalik qadamlarni rejalashtiring.",
        motivation=(
            "Sizni bosim yoki raqobat emas, ishning ma’noli ekani harakatga keltiradi. "
            "Vazifa qadriyatingizga zid bo‘lsa, tashqi muvaffaqiyat bo‘lsa ham kuch ketadi. "
            "Kundalik ishni o‘zingiz uchun muhim narsaga bog‘laganingizda motivatsiya qaytadi."
        ),
        work=(
            "Vazifaga chuqur kirishish uchun sizga tinchlik va bo‘sh joy kerak. Siz to‘lqin bilan "
            "ishlaysiz: uzoq ichki o‘ylash, so‘ng jamlangan ijodiy siljish. "
            "Har qadamni nazorat qilib turish esa qaytimingizni so‘ndiradi."
        ),
        career=(
            "Sizga faqat ko‘rsatkich emas, insonning o‘zi qadrlanadigan muhit mos: odamlarga yordam, "
            "ta’lim, matn, dizayn, psixologiya, gumanitar loyihalar. O‘z sur’atingizda ishlash imkoni muhim."
        ),
        friendship=(
            "Do‘stlaringiz ko‘p emas, lekin aloqalar chuqur. Shovqinli davradan ko‘ra yakkama-yakka "
            "uzoq samimiy suhbat sizga yaqin, og‘ir damda yoningizda bo‘lganlarni esa uzoq eslab qolasiz."
        ),
        relationship=(
            "Sizga sezgirligingizni qabul qiladigan va uni arzimas narsaga aylantirmaydigan juft kerak. "
            "Halollik, hissiy xavfsizlik va ba’zan yolg‘iz qolish huquqi muhim."
        ),
        compatible=(
            "His-tuyg‘u haqida to‘g‘ridan-to‘g‘ri va xotirjam gapiradigan odamlar bilan oson — ko‘pincha "
            "ENFJ, INFJ, ENFP. Ishda esa g‘oyani oxiriga yetkazishga yordam beradigan uyushqoq odamlar foydali."
        ),
        difficult=(
            "Keskin tanqid, baland ohang va darhol javob berish talab qilinadigan vaziyatlar qiyin kechadi. "
            "Bunday paytda siz jim bo‘lib qolasiz, ichkarida esa reaksiya juda kuchli bo‘ladi."
        ),
        plan=(
            "1-hafta: har kuni bitta istagingizni yoki bitta chegarangizni ovoz chiqarib ayting. "
            "2-hafta: bitta kichik ijodiy g‘oyani tayyor natijagacha yetkazing. "
            "Har oqshom nima kuch berganini va nima kuch olganini belgilab boring."
        ),
    ),
    "INFJ": _entry(
        title="Ma’no izlaydigan strateg",
        summary=(
            "Siz uchun uzoq muddatli maqsad va odamlarga foyda muhim. Intuitsiya va tizimli fikrlash "
            "sizda birga ishlaydi."
        ),
        strengths=[
            "Manzarani yillar oldinga ko‘ra olish",
            "Bosimsiz, empatiya bilan maslahat berish",
            "Qilayotgan ishingizda ma’no izlash",
        ],
        challenges=[
            "O‘z ehtiyojini orqaga surish odati",
            "O‘ziga nisbatan haddan tashqari yuqori talab",
        ],
        others="Sizni dono, muloyim va maqsadli inson sifatida qabul qilishadi.",
        advice="Yolg‘iz o‘zingiz bilan qoladigan vaqt ajrating — bu erkalik emas, tiklanish usuli.",
        motivation=(
            "Sizni joriy vazifadan kattaroq narsaning bir qismi ekanligingiz hissi ko‘taradi. "
            "Maqsadsiz yugurish sizning ko‘zingizda tez qadrsizlanadi. Ma’no ko‘rinib, o‘z hissangiz "
            "aniq bo‘lganda esa uzoq va qat’iy ishlaysiz."
        ),
        work=(
            "Siz avval hammasini o‘ylab olib, keyin harakat qilishni afzal ko‘rasiz. Murakkab loyihani "
            "boshingizda butun holda ushlaysiz, ammo doimiy kutilmagan almashinuvlarni yomon ko‘tarasiz."
        ),
        career=(
            "Chuqurlik va odamlar bilan ishlash talab qiladigan rollar mos: maslahat berish, o‘qitish, "
            "tadqiqot, HR, ijtimoiy va madaniy loyihalar. Qattiq raqobatsiz muhit muhim."
        ),
        friendship=(
            "Do‘stni ehtiyotkorlik bilan tanlaysiz, lekin uzoq yillar yonida qolasiz. Ko‘pincha "
            "eng shaxsiy gaplarni aynan sizga aytishadi — shu yerda o‘z resursingizni ham unutmang."
        ),
        relationship=(
            "Sizga chuqurlik, halollik va uzoq tushuntirmasdan tushunilish hissi kerak. "
            "Keskin o‘zgarishlar va munosabatdagi noaniqlik sizni hammasidan ko‘proq holdan toydiradi."
        ),
        compatible=(
            "ENFP va ENTP bilan oson — ular yengillik va harakat qo‘shadi — hamda o‘z his-tuyg‘usi "
            "haqida xotirjam gapira oladigan, jiddiy mavzudan qo‘rqmaydigan odamlar bilan."
        ),
        difficult=(
            "Yuzaki janjal, manipulyatsiya va o‘zini boshqacha ko‘rsatish kerak bo‘lgan muloqot og‘ir. "
            "Siz munosabatni oydinlashtirgandan ko‘ra jimgina uzoqlashishni tanlaysiz."
        ),
        plan=(
            "1-hafta: har kuni 20 daqiqa faqat o‘zingizga — telefonsiz va begona vazifalarsiz. "
            "2-hafta: bitta katta maqsadni yettita aniq qadamga bo‘ling va bajarilganini belgilab boring."
        ),
    ),
    "INTJ": _entry(
        title="Mustaqil strateg va tizim quruvchi",
        summary="Siz samaradorlik, aniq maqsad va uzoq muddatda ishlaydigan yechimlarni qadrlaysiz.",
        strengths=[
            "Strategik rejalashtirish",
            "Qarorlarda mustaqillik",
            "Murakkab vazifani qismlarga ajratib tahlil qilish",
        ],
        challenges=[
            "Boshqalarning sekinligiga sabrsizlik",
            "His-tuyg‘uni ikkinchi o‘ringa surish odati",
        ],
        others="Atrofdagilar sizni jiddiy, aqlli va maqsadli deb bilishadi.",
        advice="Maqsadni jamoaga so‘z bilan aytib bering — shunda hammasini yolg‘iz tortmaysiz.",
        motivation=(
            "Sizni ishlaydigan biror narsani qurish va uni doimiy yaxshilash imkoni harakatga keltiradi. "
            "«Shunday qabul qilingan» ruhidagi marosimlar motivatsiyani bir zumda o‘ldiradi. Eng yaxshi "
            "turtki — mantiqingiz natijani qanday o‘zgartirayotgani ko‘rinib turadigan vazifa."
        ),
        work=(
            "Avval tizim, keyin harakat. Siz mustaqillikni va o‘z jadvalingizni yaxshi ko‘rasiz, tashqi "
            "nazoratni hamda qarorsiz tugaydigan yig‘ilishlarni og‘ir ko‘tarasiz."
        ),
        career=(
            "Analitika, IT, muhandislik, moliya, strategiya, ilm-fan, jarayonlarni loyihalash mos keladi. "
            "Kompetentlik rasmiy ierarxiyadan yuqori turishi muhim."
        ),
        friendship=(
            "Do‘st kam, lekin bu ortiqcha rasmiyatchiliksiz munosabat. G‘oyalarni muhokama qila oladigan "
            "va noqulaylik his qilmay birga jim o‘tira oladigan odamlarni qadrlaysiz."
        ),
        relationship=(
            "Sizga shaxsiy makon ehtiyojingizni qabul qiladigan va to‘g‘ridan-to‘g‘ri gapiradigan juft kerak. "
            "Ishora va hissiy taxminlar sizni ochiq suhbatdan ko‘ra ko‘proq charchatadi."
        ),
        compatible=(
            "ENFP va ENTP bilan yaxshi chiqishasiz — ular jonlantiradi va yumshatadi — hamda mantiqni "
            "hurmat qiladigan, aniqlashtiruvchi savolni hujum deb qabul qilmaydigan odamlar bilan."
        ),
        difficult=(
            "To‘g‘ri gapdan xafa bo‘ladigan odamlar va aylanma muhokamalar qiyin. "
            "Bunday holatda siz yopilib, hammasini o‘zingiz hal qilasiz."
        ),
        plan=(
            "1-hafta: har bir ish suhbatida avval maqsadni ayting, keyin dalillarni. "
            "2-hafta: kuniga bir marta bitta odamga uning ishida nimani qadrlashingizni ayting — bu "
            "munosabatni keyinroq tuzatishdan arzonroq."
        ),
    ),
    "INTP": _entry(
        title="Tahlilchi va g‘oyalar tadqiqotchisi",
        summary="Siz narsalar qanday ishlashini tushunishni va mantiqiy modellar qurishni yoqtirasiz.",
        strengths=[
            "Mantiqiy tahlil",
            "Yangi g‘oyalar ishlab chiqish",
            "Mustaqil o‘rganish",
        ],
        challenges=[
            "Amalga o‘tishni cho‘zib yuborish",
            "Hissiy mavzulardan chetlanish",
        ],
        others="Sizni o‘ychan, qiziquvchan va mustaqil inson deb ko‘rishadi.",
        advice="G‘oyani faqat o‘ylash emas, kichik tajribaga aylantiring.",
        motivation=(
            "Sizni intizom emas, qiziqish yoqadi. Vazifa yangi savol tug‘dirib turgan ekan, juda chuqur "
            "sho‘ng‘iy olasiz; u takrorlanadigan bo‘lib qolgach, qiziqish pasayadi. "
            "Kundalik ishga ataylab tadqiqot elementini qo‘shish yordam beradi."
        ),
        work=(
            "Siz to‘lqin bilan ishlaysiz, o‘ylash bosqichida esa yolg‘izlik va bosimsizlik eng yaxshisi. "
            "Boshlash sizga tugatishdan osonroq, shuning uchun tashqi topshirish nuqtalari foydali."
        ),
        career=(
            "Tadqiqot, dasturlash, ma’lumot tahlili, ilm-fan, texnik loyihalash — nostandart yechim "
            "qadrlanadigan hamma soha mos. Usulni tanlash erkinligi muhim."
        ),
        friendship=(
            "Do‘st kam, lekin ular bilan istalgan mavzuni soatlab tahlil qila olasiz. Rasmiyatchilik "
            "uchun aloqa saqlamaysiz va uzoq tanaffusdan keyin ham xotirjam qaytasiz."
        ),
        relationship=(
            "Sizga doimiy hissiy tasdiq talab qilmaydigan va o‘zingizga chekinish ehtiyojingizni tushunadigan "
            "juft kerak. Shu bilan birga his-tuyg‘uni so‘z bilan aytish kerak — tashqaridan ular umuman "
            "ko‘rinib turmaydi."
        ),
        compatible=(
            "G‘oyani amalga oshirishga yordam beradigan ENTJ va ENFJ bilan qulay, hamda tayyor javobdan "
            "ko‘ra savolni ko‘proq yaxshi ko‘radigan odamlar bilan."
        ),
        difficult=(
            "Hissiy bosim, darhol javob talab qilish va mantiqni sovuqlik deb qabul qiladigan "
            "suhbatlar og‘ir."
        ),
        plan=(
            "1-hafta: bitta g‘oyani tanlab, uni eng sodda ishlaydigan holatgacha yetkazing. "
            "2-hafta: kuniga bir marta bitta his-tuyg‘uingizni yoki fikringizni asoslamasdan ayting."
        ),
    ),
    "ISFP": _entry(
        title="Hissiyotli estet va o‘z qadriyatiga ega inson",
        summary="Siz hozirgi lahzani, chiroyli tafsilotlarni va shaxsiy erkinlikni qadrlaysiz.",
        strengths=[
            "Badiiy did va amaliylik",
            "Empatiya",
            "Moslashuvchanlik",
        ],
        challenges=[
            "Uzoq muddatli rejalashtirishdagi qiyinchilik",
            "Keskin tanqidga sezgirlik",
        ],
        others="Sizni yumshoq, samimiy va yonida bo‘lish xotirjam inson deb bilishadi.",
        advice="Jadvalingizda ijod yoki tabiat uchun vaqt qoldiring.",
        motivation=(
            "Ish sizni shaxsan to‘lqinlantirsa va o‘zingizcha qilish erkinligi bo‘lsa, siz to‘liq kirishasiz. "
            "Uzoqdagi mavhum maqsadlar kuchsiz, bugun ko‘rinadigan natija esa kuchli turtki beradi."
        ),
        work=(
            "Sizga uzoq muhokamalardan ko‘ra qo‘lga ilinadigan natijali aniq ish yaqin. O‘zgarishlarga "
            "moslashasiz, ammo qattiq nazorat va shovqinli raqobatni yomon ko‘tarasiz."
        ),
        career=(
            "Dizayn, hunarmandchilik, oshpazlik, parvarish va tibbiyot, bolalar hamda hayvonlar bilan ishlash — "
            "amaliy va estetikaga bog‘liq hamma soha mos. Tinch muhit muhim."
        ),
        friendship=(
            "Siz o‘zingizni zo‘rlab taqdim etmaysiz, ammo yaqinlaringizga juda e’tiborlisiz. Do‘stlikni "
            "baland so‘z bilan emas, ish bilan — yordam, sovg‘a, yonida bo‘lish bilan ifodalaysiz."
        ),
        relationship=(
            "Sizga muloyimlik, qabul qilinish va bosimsizlik kerak. Juftingiz faqat so‘zni eshitibgina "
            "qolmay, qilgan ishlaringizni ham sezishi siz uchun muhim."
        ),
        compatible=(
            "ESFJ va ENFJ bilan, umuman muammoni o‘z vaqtida va yumshoq aytadigan, xafagarchilikni "
            "yig‘ib yurmaydigan e’tiborli odamlar bilan yaxshi."
        ),
        difficult=(
            "Begonalar oldidagi tanqid sizni qattiq va uzoq yaralaydi. Bahsda himoyalanishdan ko‘ra "
            "chiqib ketishni afzal ko‘rasiz."
        ),
        plan=(
            "1-hafta: har kuni 30 daqiqa ko‘zga va qo‘lga quvonch beradigan ishga ajrating. "
            "2-hafta: yaqiningizga sizni nima ranjitganini bir marta xotirjam ayting — qisqa va ayblovsiz."
        ),
    ),
    "ISFJ": _entry(
        title="G‘amxo‘r va ishonchli suyanchiq",
        summary=(
            "Sizning qo‘llab-quvvatlashingiz yaqinlaringiz va jamoa hayotini sezilarli o‘zgartiradi; "
            "siz barqarorlik va sinovdan o‘tgan tartibni qadrlaysiz."
        ),
        strengths=[
            "E’tiborlilik va sodiqlik",
            "Muhim tafsilotlarni eslab qolish",
            "Amaliy yordam",
        ],
        challenges=[
            "O‘zini ikkinchi o‘ringa qo‘yish odati",
            "O‘zgarishlar oldidan xavotir",
        ],
        others="Sizni ishonchli, mehribon va mas’uliyatli inson deb bilishadi.",
        advice="Hammaga yordam berishdan oldin o‘zingizga vaqt qoldirishni odat qiling.",
        motivation=(
            "Sizga keraklilik hissi va g‘amxo‘rlik qilgan odamlaringizning minnatdorligi kuch beradi. "
            "Ammo qaytim faqat bir tomonga ketsa, charchoq va jim xafagarchilik to‘planadi. "
            "O‘z hissangizni boshqalar aytishini kutmay, o‘zingiz sezishingiz muhim."
        ),
        work=(
            "Siz ozodasiz, boshlagan ishni oxiriga yetkazasiz va boshqalar unutadigan tafsilotlarni "
            "yodda saqlaysiz. Qoidalarning keskin almashishi va tartibsizlik sizni ritmdan chiqaradi."
        ),
        career=(
            "Tibbiyot, ta’lim, ma’muriy ish, buxgalteriya, xizmat ko‘rsatish, HR — aniqlik va insoniy "
            "munosabat qadrlanadigan sohalar mos. Bashoratlilik va jamoadagi hurmat muhim."
        ),
        friendship=(
            "Siz tug‘ilgan kunlarni, kayfiyatlarni va yarim yil oldin aytilgan mayda gaplarni eslaysiz. "
            "Do‘stlik siz uchun tasodifiy uchrashuvlar emas, uzun umumiy tarix."
        ),
        relationship=(
            "Sizga barqarorlik, minnatdorlik va sizga ham g‘amxo‘rlik qilinishiga ishonch kerak. "
            "Ogohlantirishsiz o‘zgarish o‘zgarishning o‘zidan ko‘ra ko‘proq xavotir tug‘diradi."
        ),
        compatible=(
            "Yengillik va harakat qo‘shadigan ESTP hamda ESFP bilan, umuman rahmatni ovoz chiqarib "
            "ayta oladigan odamlar bilan yaxshi."
        ),
        difficult=(
            "Ziddiyat, sovuqlik va to‘g‘ridan-to‘g‘ri iltimos o‘rniga ishora qilish og‘ir kechadi. "
            "Siz «yo‘q» deyishdan ko‘ra ortiqcha ish qilishni tanlaysiz."
        ),
        plan=(
            "1-hafta: har kuni bitta ishni faqat o‘zingiz uchun qiling. "
            "2-hafta: bir marta uzoq oqlanmasdan rad eting va munosabat bundan buzilmaganini ko‘ring."
        ),
    ),
    "ISTJ": _entry(
        title="Tartibli va mas’uliyatli ijrochi",
        summary="Siz uchun qoidalar, aniq vazifalar va oldindan bilinadigan natija muhim.",
        strengths=[
            "Tartib va rejalashtirish",
            "Ishonchlilik",
            "Amaliy tajriba",
        ],
        challenges=[
            "Kutilmagan o‘zgarishga qarshilik",
            "Moslashuvchanlik yetishmasligi",
        ],
        others="Sizni jiddiy, ishonchli va so‘zining ustidan chiqadigan inson deb ko‘rishadi.",
        advice="Rejada kichik zaxira qoldiring — hammasi boshqacha ketgan holat uchun.",
        motivation=(
            "Sizni aniq majburiyatlar va qilingan ishga hurmat harakatga keltiradi. Sizni turtkilash "
            "kamdan-kam kerak bo‘ladi, ammo kelishuvlar har hafta o‘zgaradigan joyda qiziqish yo‘qoladi. "
            "Tayyorlik mezoni aniq bo‘lishi — sizning asosiy energiya manbangiz."
        ),
        work=(
            "Avval reja, keyin harakat, qadam-baqadam. Siz muddatni ham, sifatni ham ushlaysiz, "
            "lekin yangi talabni qabul qilishga vaqt kerak — bu rad etish emas, aynan vaqt."
        ),
        career=(
            "Moliya, huquq, logistika, ma’muriyat, muhandislik, sifat nazorati, davlat tuzilmalari mos. "
            "Tushunarli qoidalar va barqaror yuklama muhim."
        ),
        friendship=(
            "Siz tez tanishmaysiz, ammo sizga yillar davomida suyanish mumkin. Yordamingiz aniq: "
            "yetib borish, tushunib olish, qilib berish."
        ),
        relationship=(
            "Sizga bashoratlilik, bajarilgan va’dalar hamda tartibingizga hurmat kerak. "
            "So‘z siz uchun ishdan kamroq ma’no beradi — his-tuyg‘uni ham amal bilan ko‘rsatasiz."
        ),
        compatible=(
            "Qat’iy jadvalni yumshatadigan ESFP va ESTP bilan, hamda vaqtga rioya qiladigan va "
            "kelishuvni buzmaydigan odamlar bilan yaxshi."
        ),
        difficult=(
            "Kechikish, ogohlantirmay muddatni surish va «yurib turib» qabul qilingan qarorlar charchatadi. "
            "Yonidagi impulsivlik sizdan ishning o‘zidan ko‘ra ko‘proq kuch oladi."
        ),
        plan=(
            "1-hafta: kunning bitta bandini ataylab rejasiz qoldiring. "
            "2-hafta: odatiy vazifani yangi usulda bajaring va natijani eskisi bilan solishtiring."
        ),
    ),
    "ISTP": _entry(
        title="Amaliy muammolarni qo‘li bilan hal qiluvchi",
        summary="Siz qo‘l mehnatini, tez tahlilni va harakatdagi mustaqillikni yoqtirasiz.",
        strengths=[
            "Tez qaror va amal",
            "Texnik tafakkur",
            "Bosim ostida xotirjamlik",
        ],
        challenges=[
            "Uzoq munosabatda his-tuyg‘uni ifodalash qiyinligi",
            "Ortiqcha qoidalardan charchash",
        ],
        others="Sizni xotirjam, mustaqil va og‘ir vaziyatda ishonchli inson deb bilishadi.",
        advice="Muhim qarorlarni yozib qo‘ying va biroz keyinroq ularga qayting.",
        motivation=(
            "Sizni olib hal qilsa bo‘ladigan aniq vazifa yoqadi. Uzoq yig‘ilishlar va mavhum maqsadlar "
            "qiziqishni hammasidan tez so‘ndiradi. Usulni tanlash erkinligi siz uchun natija uchun "
            "beriladigan mukofotdan muhimroq."
        ),
        work=(
            "Siz yo‘riqnoma bo‘yicha emas, ish davomida tushunib olasiz va inqirozda ko‘pchilikdan "
            "xotirjamroq harakat qilasiz. Bir xillik va ortiqcha hisobot energiyani yuvib ketadi."
        ),
        career=(
            "Texnika va ta’mirlash, IT infratuzilma, muhandislik, sport, favqulodda xizmatlar, "
            "«dala»dagi har qanday ish mos. Mustaqillik va minimal rasmiyatchilik muhim."
        ),
        friendship=(
            "Siz kamgapsiz, lekin ortiqcha savolsiz yordamga kelasiz. "
            "Do‘stlar sizni uzun suhbat uchun emas, amal uchun qadrlashadi."
        ),
        relationship=(
            "Sizga shaxsiy makon va jimligingizni uzoqlashish deb o‘qimaydigan juft kerak. "
            "Hech bo‘lmaganda ba’zan his-tuyg‘uni so‘zga aylantirish foydali — aks holda yaqin odam "
            "o‘zi taxmin qiladi va ko‘pincha xato qiladi."
        ),
        compatible=(
            "Tashkilotchilikni o‘z zimmasiga oladigan ESFJ va ESTJ bilan qulay, hamda hissiy bosim "
            "o‘tkazmaydigan, doimiy hisobot talab qilmaydigan odamlar bilan."
        ),
        difficult=(
            "Nazorat, uzun nasihat va hissiyot ustida munosabat oydinlashtirishni og‘ir ko‘tarasiz. "
            "Javoban shunchaki suhbatdan chiqib ketasiz."
        ),
        plan=(
            "1-hafta: impulsiv qarordan oldin bir soat tanaffus qiling. "
            "2-hafta: kuniga bir marta yaqiningizga holatingiz haqida bitta jumla ayting."
        ),
    ),
    "ENFP": _entry(
        title="Ilhomlantiruvchi g‘oyalar odami",
        summary="Sizni yangilik, odamlar va ochiq imkoniyatlar quvvatlantiradi.",
        strengths=[
            "Ijodiy energiya",
            "Muloqotdagi iliqlik",
            "Yangi loyihani boshlashdagi yengillik",
        ],
        challenges=[
            "Yakunlash bosqichida diqqatni yo‘qotish",
            "Ishlar ko‘payib ketishidan zo‘riqish",
        ],
        others="Sizni quvnoq, ochiq va ilhomlantiruvchi inson deb bilishadi.",
        advice="Bir vaqtda kamroq loyiha oling — va ularni oxirigacha yetkazing.",
        motivation=(
            "Sizni yangilik va oldinda ko‘p variant borligi hissi ko‘taradi. Motivatsiya murakkablikdan "
            "emas, bir xillikdan pasayadi. Zerikarli yakuniy bosqichni mukofoti bor alohida kichik "
            "maqsadga aylantirish yordam beradi."
        ),
        work=(
            "Siz g‘oyani ajoyib ishlab chiqasiz va boshqalarni ham yondirasiz, ammo tafsilot va kundalik "
            "ish tashqi suyanchiqni talab qiladi. Tuzilmani yaxshi ko‘radigan odam bilan juft ishlash "
            "natijangizni ikki barobar oshiradi."
        ),
        career=(
            "Marketing, ijodiy sohalar, o‘qitish, psixologiya, startaplar, ommaviy kommunikatsiya mos. "
            "Vazifalar xilma-xilligi va jonli muloqot muhim."
        ),
        friendship=(
            "Do‘stlaringiz ko‘p va juda turlicha; oson yaqinlashasiz va so‘z bilan qo‘llab-quvvatlay olasiz. "
            "Ba’zan o‘zingizni begona hikoyalarda eritib yubormayotganingizni tekshirib turing."
        ),
        relationship=(
            "Sizga hissiy ochiqlik, birga olingan taassurotlar va qattiq ramkalardan erkinlik kerak. "
            "Zerikish va sovuqlik sizni ochiq ziddiyatdan ko‘ra qattiqroq yaralaydi."
        ),
        compatible=(
            "Chuqurlik va tuzilma beradigan INFJ hamda INTJ bilan yaxshi, va o‘z-o‘zidanligingizni "
            "so‘ndirmay, ishga muloyim qaytaradigan odamlar bilan."
        ),
        difficult=(
            "Befarqlik, mayda-chuydaga tirishish va qattiq nazorat og‘ir kechadi. "
            "Xafagarchilikni tez unutasiz, lekin o‘sha lahzada juda o‘tkir reaksiya berasiz."
        ),
        plan=(
            "1-hafta: bitta loyihani tanlab, qolganini chetga surib, uni to‘liq yoping. "
            "2-hafta: har oqshom nima kuch berganini va nima kuch olganini yozing, haftada bir marta "
            "ro‘yxatni qayta o‘qing."
        ),
    ),
    "ENFJ": _entry(
        title="Odamlarni birlashtiradigan yetakchi",
        summary="Siz uchun yoningizdagi odamlarning o‘sishi va umumiy ma’noli maqsadlar muhim.",
        strengths=[
            "Xarizmatik muloqot",
            "Guruhni ilhomlantira olish",
            "Empatiya",
        ],
        challenges=[
            "O‘z ehtiyojini unutish",
            "Hamma uchun haddan tashqari mas’uliyat hissi",
        ],
        others="Sizni g‘ayratli, g‘amxo‘r va ortidan ergashtiradigan inson deb ko‘rishadi.",
        advice="Faqat boshqalarga yordamni emas, tiklanish vaqtini ham rejalashtiring.",
        motivation=(
            "Sizga yoningizdagi odamlarning ko‘zga ko‘rinadigan o‘sishi va umumiy maqsad hissi kuch beradi. "
            "Sa’y-harakat tan olinmaganda yoki jamoa bo‘lingan bo‘lsa, ish hajmidan ko‘ra tezroq "
            "«kuyib» qolasiz. Muvaffaqiyatni faqat begona natijalar bilan o‘lchamaslik muhim."
        ),
        work=(
            "Siz muvofiqlashtirishni tabiiy ravishda o‘z zimmangizga olasiz va jamoadagi muhitni ushlaysiz. "
            "Xavf shundaki, hech kimni qiyin ahvolda qoldirmaslik uchun begona vazifalarni ham o‘zingizga olasiz."
        ),
        career=(
            "O‘qitish, HR, jamoa boshqaruvi, psixologiya, jamoat loyihalari, insoniy yuzli savdo mos. "
            "Tashkilot qadriyatlari sizniki bilan mos kelishi muhim."
        ),
        friendship=(
            "Og‘ir damda birinchi bo‘lib sizga qo‘ng‘iroq qilishadi. Do‘stligingiz saxiy va to‘liq "
            "kirishgan — aynan shuning uchun ba’zan resurssiz bo‘lishga ham o‘zingizga ruxsat bering."
        ),
        relationship=(
            "Sizga o‘zaro javob, iliq so‘z va sizni ham o‘ylashlariga ishonch kerak. "
            "Juftingizning jim masofasini siz rad etish sifatida boshdan kechirasiz."
        ),
        compatible=(
            "Sizning qo‘llab-quvvatlashingiz haqiqatan kerak bo‘lgan INFP va ISFP bilan yaxshi, hamda "
            "minnatdorlik bildira oladigan va g‘amxo‘rlikni qaytara oladigan odamlar bilan."
        ),
        difficult=(
            "Sovuqlik, qadrsizlantirish va yaqin doiradagi ziddiyat og‘ir. Siz hammani yarashtirishga "
            "urinasiz, hatto bu sizning mas’uliyatingiz bo‘lmaganda ham."
        ),
        plan=(
            "1-hafta: har kuni faqat o‘zingiz uchun, boshqalarga foydasiz biror ish qiling. "
            "2-hafta: bitta begona vazifani egasiga qaytaring va u o‘zi qanday uddalashini kuzating."
        ),
    ),
    "ENTJ": _entry(
        title="Qat’iyatli strateg va tashkilotchi",
        summary="Siz samaradorlik, aniq maqsad va natijaga yo‘naltirilgansiz.",
        strengths=[
            "Yetakchilik",
            "Uzoq muddatli rejalashtirish",
            "Tez qaror qabul qilish",
        ],
        challenges=[
            "Atrofdagilarning his-tuyg‘usini kam baholash",
            "Muloqotdagi haddan tashqari qat’iy ohang",
        ],
        others="Sizni kuchli, maqsadli va ishonchli inson deb bilishadi.",
        advice="Jamoani tinglash uchun alohida vaqt ajrating.",
        motivation=(
            "Sizni katta maqsad va yakuniy natijaga ta’sir qilish imkoni harakatga keltiradi. "
            "O‘sish yo‘qligi sizni ortiqcha yuklamadan ko‘ra kuchliroq so‘ndiradi. Eng yaxshi rejim — "
            "muddati aniq va mustaqil qaror qabul qilish huquqi bor yirik vazifa."
        ),
        work=(
            "Siz tez tuzilma qurasiz, rollarni taqsimlaysiz va natija talab qilasiz — avvalo o‘zingizdan. "
            "Zaif joyingiz: jamoa har doim ham ko‘tara olmaydigan sur’at."
        ),
        career=(
            "Rahbarlik, biznes, konsalting, huquqshunoslik, loyiha boshqaruvi, tadbirkorlik mos. "
            "Vazifalar ko‘lami va real vakolat muhim."
        ),
        friendship=(
            "Do‘stni qulaylik bo‘yicha emas, hurmat bo‘yicha tanlaysiz va ularga vaqt hamda aloqalaringizni "
            "sarflaysiz. To‘g‘ridan-to‘g‘ri gapirish — sizning g‘amxo‘rlik ko‘rsatish usulingiz."
        ),
        relationship=(
            "Sizga o‘z pozitsiyasi bor, bahslashishdan qo‘rqmaydigan juft kerak. Shu bilan birga yaqinlar "
            "sizdan faqat baho emas, e’tirof ham eshitishi kerak — buni ovoz chiqarib aytish arziydi."
        ),
        compatible=(
            "Sur’atingizni muvozanatlaydigan INTP va INFP bilan yaxshi, hamda to‘g‘ri gapiradigan va "
            "aniqlikdan xafa bo‘lmaydigan odamlar bilan."
        ),
        difficult=(
            "Noaniq javoblar, bajarilmagan va’dalar va qarorsiz muhokamalar asabiylashtiradi. "
            "Javoban siz o‘zingiz xohlaganingizdan keskinroq bo‘lib qolasiz."
        ),
        plan=(
            "1-hafta: har suhbatda avval oxirigacha eshiting, keyin javob bering. "
            "2-hafta: kuniga bir marta birovning hissasini aniq jumla bilan qayd eting — oxirida «lekin»siz."
        ),
    ),
    "ENTP": _entry(
        title="Bahschi va yangi yechimlar generatori",
        summary="Siz g‘oyalarni, aqliy o‘yinni va chegaralarni sinab ko‘rishni yaxshi ko‘rasiz.",
        strengths=[
            "Tez fikrlash",
            "Innovatsion yondashuv",
            "Muloqotdagi joziba",
        ],
        challenges=[
            "Bir xil kundalik ishdan charchash",
            "Tafsilotlarni keyinga surish",
        ],
        others="Sizni aqlli, hozirjavob va qiziqarli suhbatdosh deb bilishadi.",
        advice="Eng yaxshi bitta g‘oyani tanlab, uni amalga oshirish rejasini yozing.",
        motivation=(
            "Sizni chaqiriq va «boshqacha ham bo‘ladi» ekanini isbotlash imkoni yoqadi. Vazifa boshda "
            "hal bo‘lishi bilan qiziqish tushadi — ijro zerikarli tuyuladi. Musobaqa elementi va "
            "marrani ushlab turadigan hamkor yordam beradi."
        ),
        work=(
            "Siz noaniqlik sharoitida ajoyib ishlaysiz va boshqalar to‘xtab qolgan joyda aylanma yo‘l topasiz. "
            "Reglament va bir xillik qaytimingizni hammasidan tez pasaytiradi."
        ),
        career=(
            "Tadbirkorlik, mahsulot boshqaruvi, konsalting, reklama, huquqshunoslik, muzokaralar — "
            "tez va nostandart yechim kerak bo‘lgan hamma soha mos."
        ),
        friendship=(
            "Siz oson tanishasiz va xafa bo‘lmasdan bahslasha oladigan odamlarni qadrlaysiz. "
            "Do‘stlik siz uchun g‘oya va energiya almashinuvi."
        ),
        relationship=(
            "Sizga aqliy qiziqish, hazil va erkinlik kerak. Juftingiz bahs siz uchun hujum emas, "
            "qiziqish shakli ekanini tushunishi muhim; sizga esa ba’zan shunchaki rozi bo‘lish foydali."
        ),
        compatible=(
            "G‘oyalaringizni tizimga aylantiradigan INFJ va INTJ bilan yaxshi, hamda o‘ziga ishonchi "
            "mustahkam, hazilni tushunadigan odamlar bilan."
        ),
        difficult=(
            "Tushuntirishsiz taqiqlar, munozarada xafa bo‘lish va byurokratiya og‘ir. "
            "Siz mavzu o‘zingizga muhim bo‘lmaganda ham prinsip uchun bahslasha boshlaysiz."
        ),
        plan=(
            "1-hafta: uchta yangi g‘oyadan voz kechib, bittasini oxiriga yetkazing. "
            "2-hafta: bahsda kuniga bir marta avval suhbatdoshning fikrini o‘z so‘zingiz bilan "
            "qaytaring, keyingina e’tiroz bildiring."
        ),
    ),
    "ESFP": _entry(
        title="Hozirgi lahzaning jonli odami",
        summary="Sizga odamlar, taassurotlar va iliq, yengil muhit energiya beradi.",
        strengths=[
            "Ijtimoiy energiya",
            "Moslashuvchanlik",
            "Amaliy yordam",
        ],
        challenges=[
            "Uzoq muddatli rejalashtirish",
            "Tanqidga sezgirlik",
        ],
        others="Sizni ochiq, samimiy va yorqin inson deb ko‘rishadi.",
        advice="Yirik qarorlardan oldin qisqa yozma reja tuzing.",
        motivation=(
            "Sizni odamlarning javobi va darhol ko‘rinadigan natija quvvatlantiradi. Oraliq quvonchsiz "
            "uzoq maqsadlar ko‘zdan yo‘qoladi. Katta ishni har biri yoqimli yakuni bor qisqa bosqichlarga "
            "bo‘lish yaxshi ishlaydi."
        ),
        work=(
            "Siz tez kirishasiz, odamlar bilan oson ishlaysiz va atrofdagi kayfiyatni yaxshi his qilasiz. "
            "Eng qiyini — jimjitlikdagi uzoq qog‘oz ishi."
        ),
        career=(
            "Savdo, tadbirlar, xizmat ko‘rsatish, sahna va media, turizm, sport, bolalar bilan ishlash — "
            "jonli va harakatdagi hamma soha mos."
        ),
        friendship=(
            "Siz odamlarni atrofingizga yig‘asiz va kayfiyat ko‘tara olasiz. Do‘stlar sizning e’tibor va "
            "vaqtga saxiyligingizni qadrlashadi."
        ),
        relationship=(
            "Sizga iliqlik, e’tibor va birga olingan taassurotlar kerak. Uzoq sovuqlik yoki jim "
            "xafagarchilik sizga juda og‘ir botadi."
        ),
        compatible=(
            "Suyanchiq va tartib qo‘shadigan ISFJ hamda ISTJ bilan yaxshi, va muammoni yig‘ib yurmay "
            "darrov aytadigan odamlar bilan."
        ),
        difficult=(
            "Keskin tanqid, ayniqsa boshqalar oldida, sizni uzoq muvozanatdan chiqaradi. "
            "Qiyin suhbatda javobdan oldin qisqa tanaffus qilish yordam beradi."
        ),
        plan=(
            "1-hafta: har tong kunning uchta vazifasini yozing, oqshom bajarilganini belgilang. "
            "2-hafta: bitta muhim qarorni bir kunga qoldiring va birinchi hissiyotni yakuniy tanlov "
            "bilan solishtiring."
        ),
    ),
    "ESFJ": _entry(
        title="Jamoa ruhining posboni",
        summary="Siz uchun jamiyat, an’analar va yaqinlaringizning farovonligi muhim.",
        strengths=[
            "Xayrixohlik",
            "Tashkilotchilik qobiliyati",
            "Munosabatlarda sodiqlik",
        ],
        challenges=[
            "Tanqiddan qo‘rquv",
            "O‘z ehtiyojini unutish",
        ],
        others="Sizni g‘amxo‘r, ishonchli va doim yordamga tayyor inson deb ko‘rishadi.",
        advice="Yordam so‘rash ham sog‘lom munosabatning bir qismi.",
        motivation=(
            "Sizga minnatdorlik va foydali ekanlik hissi kuch beradi. Ammo ma’qullash yagona yoqilg‘iga "
            "aylansa, har qanday tanbeh juda qattiq uradi. Qilgan ishingizga o‘zingiz baho bera olish "
            "motivatsiyani barqarorroq qiladi."
        ),
        work=(
            "Siz jamoadagi muhitni ushlaysiz, kelishuvlarni eslab qolasiz va ishni yarim yo‘lda tashlamaysiz. "
            "Ziddiyatli yoki sovuq muhitda ishlash sizga og‘ir."
        ),
        career=(
            "Ta’lim, tibbiyot, HR, xizmat ko‘rsatish, ma’muriyat, tadbirlarni tashkil qilish, ijtimoiy ish mos. "
            "Iliq jamoa va hissaning e’tirof etilishi muhim."
        ),
        friendship=(
            "Siz aloqalarni yillab saqlaysiz va kimdir yo‘qolib qolsa birinchi bo‘lib o‘zingiz yozasiz. "
            "E’tiboringiz ham, uyingiz ham yaqinlar uchun deyarli doim ochiq."
        ),
        relationship=(
            "Sizga barqarorlik, iliq so‘z va umumiy kelajakka ishonch kerak. "
            "Munosabatdagi noaniqlik sizni ochiq ziddiyatdan ko‘ra ko‘proq xavotirga soladi."
        ),
        compatible=(
            "Siz muvozanatlab turadigan ISFP va ISTP bilan yaxshi, hamda g‘amxo‘rlikni o‘z-o‘zidan "
            "bo‘ladigan narsa deb qabul qilmaydigan odamlar bilan."
        ),
        difficult=(
            "Begonalar oldidagi tanqid, sovuqlik va ortiqcha vasiylikda ayblash og‘ir. "
            "Siz ko‘nglini olishga urinasiz, keyin esa o‘zingizni ishlatilgandek his qilasiz."
        ),
        plan=(
            "1-hafta: har kuni o‘zingiz uchun biror ish qiling va bu haqda hech kimga hisobot bermang. "
            "2-hafta: yaqiningizdan bir marta aniq yordam so‘rang — oqlanmasdan."
        ),
    ),
    "ESTJ": _entry(
        title="Tartib va natija odami",
        summary="Siz aniq qoidalar, mas’uliyat va samaradorlikni qadrlaysiz.",
        strengths=[
            "Jarayonlarni tashkil qilish",
            "Tez ijro",
            "Aniqlik",
        ],
        challenges=[
            "Moslashuvchanlik yetishmasligi",
            "Hissiy nozikliklarga e’tiborsizlik",
        ],
        others="Sizni ishonchli, jiddiy va uyushqoq inson deb bilishadi.",
        advice="O‘zgarishlarni jamoa bilan oldindan muhokama qiling.",
        motivation=(
            "Sizni aniq maqsad, o‘lchanadigan natija va tushunarli mas’uliyat doirasi harakatga keltiradi. "
            "Tartibsizlik va noaniq rollar sizni katta yuklamadan ko‘ra ko‘proq asabiylashtiradi."
        ),
        work=(
            "Siz istalgan jarayonda tartib o‘rnatasiz, vazifalarni taqsimlaysiz va muddatlarni kuzatasiz. "
            "Xavf — boshqalardan ham xuddi o‘zingizdek sur’at va aniqlikni talab qilish."
        ),
        career=(
            "Boshqaruv, ishlab chiqarish, logistika, moliya, huquq, davlat xizmati, operatsion rollar mos. "
            "Aniq tuzilma va real vakolat muhim."
        ),
        friendship=(
            "Siz aniq maslahat yoki yordam uchun murojaat qilinadigan ishonchli do‘stsiz. G‘amxo‘rlikni "
            "his-tuyg‘u haqida gapirish bilan emas, ish va tashkilotchilik bilan ko‘rsatasiz."
        ),
        relationship=(
            "Sizga bashoratlilik, bajarilgan kelishuvlar va tartibingizga hurmat kerak. "
            "Juftingiz sizdan faqat tanbeh emas, ma’qullash ham eshitishi muhim."
        ),
        compatible=(
            "Sur’atni yumshatadigan ISFP va INFP bilan yaxshi, hamda tartibni qadrlaydigan va "
            "to‘g‘ridan-to‘g‘ri gapiradigan odamlar bilan."
        ),
        difficult=(
            "Mas’uliyatsizlik, bahonalar va dalilsiz qarorlar asabiylashtiradi. "
            "Bunday paytda ohangingiz kerak bo‘lganidan qattiqroq bo‘lib ketadi."
        ),
        plan=(
            "1-hafta: odamni tuzatishdan oldin avval u nimani yaxshi qilganini ayting. "
            "2-hafta: bitta jarayonni boshqasiga to‘liq topshiring va natijagacha aralashmang."
        ),
    ),
    "ESTP": _entry(
        title="Harakat va imkoniyat odami",
        summary="Sizga tez qarorlar, harakat va yangi tajriba kuch beradi.",
        strengths=[
            "Tez reaksiya",
            "Amaliy yechimlar",
            "Ijtimoiy joziba",
        ],
        challenges=[
            "Uzoq muddatli rejalar",
            "Sabr talab qiladigan vazifalar",
        ],
        others="Sizni jasur, ochiq va energiyali inson deb ko‘rishadi.",
        advice="Muhim loyihalar uchun qisqa muddat va oraliq deadline qo‘ying.",
        motivation=(
            "Sizni qiziqish, musobaqa va ayni damdagi qo‘lga ilinadigan natija yoqadi. Harakatsiz uzoq "
            "tayyorgarlik qiziqishni so‘ndiradi. Hisobi ko‘rinib turadigan qisqa siljishlar yaxshi ishlaydi."
        ),
        work=(
            "Inqirozda siz ko‘pchilikdan samaraliroqsiz: tez hal qilasiz va o‘zingizni yo‘qotmaysiz. "
            "Zaif joyingiz — tafsilotlarni sabr bilan yetkazish kerak bo‘lgan bosqich."
        ),
        career=(
            "Savdo, muzokaralar, sport, favqulodda xizmatlar, tadbirkorlik, qurilish — "
            "dinamik va tez natijali hamma soha mos."
        ),
        friendship=(
            "Siz odamlar bilan oson chiqishasiz va atrofingizda harakat yaratasiz. Do‘stlar biladi: "
            "shoshilinch harakat kerak bo‘lsa, siz allaqachon ishdasiz."
        ),
        relationship=(
            "Sizga jonlilik, halollik va mayda nazoratning yo‘qligi kerak. Juftingiz uchun sizning "
            "e’tiboringiz faqat yorqin lahzalarda emas, oddiy kunlarda ham muhim."
        ),
        compatible=(
            "Ishonchli orqa fon yaratadigan ISFJ va ISTJ bilan yaxshi, hamda sur’atingizni yoqtiradigan "
            "va o‘z vaqtida sekinlata oladigan odamlar bilan."
        ),
        difficult=(
            "Uzun nasihatlar, tushuntirishsiz xafagarchilik va ma’nosiz qoidalar og‘ir. Siz keskin javob "
            "berasiz, so‘ng tez soviysiz — buni yaqinlaringizga oldindan aytib qo‘ygan ma’qul."
        ),
        plan=(
            "1-hafta: har bir yirik qarordan oldin bir kunlik tanaffus oling. "
            "2-hafta: bitta zerikarli ishni oxiriga yetkazing va u aslida qancha vaqt olganini belgilang."
        ),
    ),
}


def get_result_copy(personality_type: str) -> ResultCopy:
    key = personality_type.upper()
    return PERSONALITY_RESULTS_UZ.get(key, GENERIC_FALLBACK)
