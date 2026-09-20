"""16 tip uchun ikkita rivojlanish yo‘nalishi va 7 kunlik reja (o‘zbekcha)."""

from app.seed.growth_guidance_schema import GrowthArea, week_from_rows


def _area(
    *,
    id: str,
    name: str,
    situation: str,
    method: str,
    steps: list[str],
    today_task: str,
    success_criteria: str,
    lighter_variant: str,
    check_question: str,
    week: list[tuple[str, str, str]],
) -> GrowthArea:
    return GrowthArea(
        id=id,
        name=name,
        situation=situation,
        method=method,
        steps=steps[:3],
        today_task=today_task,
        success_criteria=success_criteria,
        lighter_variant=lighter_variant,
        check_question=check_question,
        week_plan=week_from_rows(week),
    )


PERSONALITY_GROWTH_UZ: dict[str, tuple[GrowthArea, GrowthArea]] = {
    "ENTP": (
        _area(
            id="entp-finish",
            name="Boshlagan ishni yakunlash",
            situation=(
                "Agar yangi g‘oya paydo bo‘lganda oldingi ishning mayda qismlarini keyinga "
                "surib qo‘ysangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Ishning tugagan holatini aniq belgilash va navbatdagi kichik qadamni tanlash.",
            steps=[
                "Bitta chala ishni tanlang.",
                "«Bu ish tugadi deyishim uchun nima tayyor bo‘lishi kerak?» savoliga bir jumla yozing.",
                "Shu natijaga olib boradigan 10 daqiqalik bitta qismni bajaring; yangi g‘oya chiqsa, alohida ro‘yxatga yozib qo‘ying.",
            ],
            today_task="Tanlangan ishning bitta kichik qismini bajarish.",
            success_criteria="Oldindan belgilangan kichik qism tayyor.",
            lighter_variant="Ish materialini ochib, keyingi qadamni yozish.",
            check_question="Boshlash osonlashdimi? Qaysi joyda to‘xtadingiz?",
            week=[
                ("Bugungi kichik qismni belgilab bajaring", "10–15 daqiqa", "Belgilangan qism bajarilgan"),
                ("Kecha qoldirilgan ishning «tugagan» jumlasini tekshiring", "5 daqiqa", "Jumla hali ham aniq"),
                ("Yangi g‘oyalar ro‘yxatiga faqat bitta qator qo‘shing, eskisini ochmang", "10 daqiqa", "Ro‘yxat alohida saqlangan"),
                ("Chala ishning ikkinchi kichik qismini bajaring", "10–15 daqiqa", "Ikkinchi qism tayyor"),
                ("Ishni kimdir ko‘rsa nima ko‘rishini tasavvur qilib, yetishmayotgan qismni yozing", "10 daqiqa", "Bitta yetishmovchilik aniq"),
                ("Yetishmovchilikni yopadigan qisqacha qadam bajaring", "15 daqiqa", "Kamida bitta nuqta yopilgan"),
                ("Hafta oxirida: nima tugadi, keyingi qadam nima — ikkalasini yozing", "10 daqiqa", "Keyingi qadam tanlangan"),
            ],
        ),
        _area(
            id="entp-listen",
            name="Bahsdan oldin eshitish",
            situation=(
                "Agar muhokamada tez javob berib, suhbatdoshning fikrini to‘liq olmay qo‘ysangiz, "
                "quyidagi usulni sinab ko‘ring."
            ),
            method="Avval gapirib bergan fikrni o‘z so‘zingiz bilan qisqa qayta aytish.",
            steps=[
                "Keyingi munozarada javob berishdan oldin nafas oling.",
                "Suhbatdosh aytganini bir jumla bilan qayta ifodalang.",
                "Keyin o‘z fikringizni qo‘shing.",
            ],
            today_task="Bitta qisqa suhbatda avval tinglab, keyin javob berish.",
            success_criteria="Kamida bir marta suhbatdoshning fikrini qayta aytib oldingiz.",
            lighter_variant="Chatda javob yozishdan oldin o‘qib chiqing va «tushundim» deb qisqa yozing.",
            check_question="Suhbat yumshoqroq ketdimi yoki baribir shoshildingiz?",
            week=[
                ("Bitta suhbatda qayta ifoda qilishni sinab ko‘ring", "5–10 daqiqa", "Kamida bir marta qayta aytildi"),
                ("Telefon/chatda javobdan oldin 1 daqiqa kutish", "1 daqiqa", "Kutish amalga oshirildi"),
                ("Muhim mavzuda savol berishdan oldin eshitish", "10 daqiqa", "Kamida 2 ta savol tinglangandan keyin"),
                ("«Men shunday tushundim…» bilan boshlanadigan jumlani sinab ko‘ring", "5 daqiqa", "Bitta jumla ishlatildi"),
                ("Bahs paytida qog‘ozga suhbatdosh nuqtasini yozing", "10 daqiqa", "Yozuv bor"),
                ("E’tirozdan oldin ikkala tomondan ham nima to‘g‘ri ekanini ayting", "15 daqiqa", "Ijobiy jumla aytilgan"),
                ("Hafta oxirida: qaysi suhbat yaxshi ketdi, nima yordam berdi — qisqa yozuv", "10 daqiqa", "Bitta xulosa yozilgan"),
            ],
        ),
    ),
    "INFP": (
        _area(
            id="infp-boundary",
            name="O‘z ehtiyojini aytish",
            situation=(
                "Agar o‘zingizni qulay ko‘rsatish uchun «mayli» deb qo‘ysangiz, keyin ichingiz og‘ir bo‘lsa, "
                "quyidagi usulni sinab ko‘ring."
            ),
            method="Kichik, aniq va hurmatli rad etish yoki so‘rov.",
            steps=[
                "Bugun bitta kichik narsada o‘z fikringizni ayting.",
                "«Men hozir … qila olmayman, chunki …» kabi sodda jumla ishlating.",
                "Uzr so‘rab, keyingi vaqtni taklif qiling.",
            ],
            today_task="Bitta kichik iltimonga muloyim chegara qo‘yish.",
            success_criteria="Bir jumlada o‘z holatingizni aytdingiz.",
            lighter_variant="Faqat «hozir qiyin, keyinroq gaplashamiz» deb yozing.",
            check_question="Keyin pushaymon bo‘ldingizmi yoki yengillik sezildimi?",
            week=[
                ("Bitta kichik chegara — og‘zaki yoki yozma", "5 daqiqa", "Javob berildi"),
                ("Kun oxirida o‘zingiz uchun 15 daqiqa ajrating", "15 daqiqa", "Vaqt ajratildi"),
                ("Yordam so‘raganda aniq nima kerakligini ayting", "10 daqiqa", "So‘rov aniq"),
                ("«Men uchun qiyin» degan bir jumlani ishlating", "5 daqiqa", "Jumla aytilgan"),
                ("Rejani o‘zgartirish kerak bo‘lsa, oldindan xabar bering", "10 daqiqa", "Xabar berildi"),
                ("Tanish yoki oila a’zosiga bitta ehtiyojingizni ayting", "10 daqiqa", "Suhbat bo‘ldi"),
                ("Hafta oxirida: qaysi chegara oson, qaysi biri qiyin — yozing", "10 daqiqa", "Ikki qator yozuv"),
            ],
        ),
        _area(
            id="infp-conflict",
            name="Ziddiyatni kechiktirmaslik",
            situation=(
                "Agar noqulay mavzuni uzoq vaqt jimlik bilan o‘tkazib yuborsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Kichik, xavfsiz mavzuda vaqt belgilab ochiq gapirish.",
            steps=[
                "Muhim bo‘lmagan kichik nizo tanlang.",
                "«Men … haqida gapirmoqchiman» deb boshlang.",
                "Bitta fakt va bitta his-tuyg‘uni ayting.",
            ],
            today_task="Kichik bir noqulaylikni muloyim jumla bilan nomlash.",
            success_criteria="Kamida bitta aniq jumla aytilgan yoki yozilgan.",
            lighter_variant="Avval qog‘ozga nima aytmoqchi ekanligingizni yozing.",
            check_question="Suhbat qanchalik og‘ir tuyuldi — 1 dan 5 gacha?",
            week=[
                ("Kichik mavzuda bitta aniq jumla", "10 daqiqa", "Jumla aytilgan"),
                ("Yozma xabar orqali noqulaylikni yumshoq ifoda etish", "10 daqiqa", "Xabar yuborildi"),
                ("Suhbatdan oldin maqsadni bir qatorga yozish", "5 daqiqa", "Maqsad yozilgan"),
                ("Tinglash va javob berish vaqtini teng bo‘lish", "15 daqiqa", "Avval tinglab keyin javob"),
                ("«Men … his qilyapman» bilan boshlanadigan gap", "10 daqiqa", "Gap ishlatildi"),
                ("Kelishuv yoki keyingi qadamni bir jumla bilan ayting", "10 daqiqa", "Keyingi qadam aniq"),
                ("Hafta oxirida: qaysi suhbat yengilroq bo‘ldi — qisqa xulosa", "10 daqiqa", "Xulosa yozilgan"),
            ],
        ),
    ),
    "INFJ": (
        _area(
            id="infj-rest",
            name="O‘ziga vaqt ajratish",
            situation=(
                "Agar boshqalarning ehtiyoji sizning dam olish vaqtini doim bosib ketsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Kuniga qisqa, telefonsiz tanaffusni reja qilish.",
            steps=[
                "15 daqiqalik vaqt tanlang.",
                "Telefonni boshqa xonaga qo‘ying.",
                "Faqat nafas olish, yurish yoki jim o‘tirish — vazifa emas.",
            ],
            today_task="15 daqiqa hech kimga javob bermasdan o‘tish.",
            success_criteria="Vaqt tugaguncha yangi vazifa olmadingiz.",
            lighter_variant="5 daqiqa derazada tikilib turish.",
            check_question="Keyin boshqalar bilan muloqot osonroq bo‘ldimi?",
            week=[
                ("15 daqiqa telefonsiz tanaffus", "15 daqiqa", "Tanaffus bo‘ldi"),
                ("Kechqurun ertaga uchun bitta «yo‘q» javobini oldindan o‘ylab qo‘yish", "5 daqiqa", "Javob rejada"),
                ("Yordam taklif qilishdan oldin o‘zingizning kuchingizni baholash", "5 daqiqa", "Baholash yozildi"),
                ("Bir kishi uchun emas, o‘zingiz uchun kichik ish qiling", "15 daqiqa", "Ish bajarildi"),
                ("Uzoq suhbatdan oldin «muddati» ayting", "5 daqiqa", "Vaqt chegarasi aytilgan"),
                ("Dam olishni «ish emas» deb rejalashtirish", "15 daqiqa", "Rejada turadi"),
                ("Hafta oxirida: qachon charchaganingizni va nima yordam berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="infj-share",
            name="Fikrni ochiqroq aytish",
            situation=(
                "Agar muhim fikringizni ichingizda uzoq ushlab, boshqalar noto‘g‘ri taxmin qilsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta fikrni aniq va qisqa jumla bilan baham ko‘rish.",
            steps=[
                "Bitta muhim fikrni tanlang.",
                "Uch jumladan oshirmay yozing yoki ayting.",
                "Savol bo‘lsa, javob bering; bahslash shart emas.",
            ],
            today_task="Bitta fikrni yozma yoki og‘zaki ulashish.",
            success_criteria="Fikr to‘liq yetkazildi.",
            lighter_variant="Faqat bitta jumlalik xulosa yuborish.",
            check_question="Reaksiya siz kutgandek bo‘ldimi?",
            week=[
                ("Bitta fikrni uch jumla bilan ulashish", "10 daqiqa", "Ulashildi"),
                ("Yig‘ilishda kamida bitta savol yoki fikr", "10 daqiqa", "Gapirildi"),
                ("Oldindan yozib olib, keyin o‘qish", "10 daqiqa", "Matn ishlatildi"),
                ("«Men shunday ko‘ryapman» bilan boshlash", "10 daqiqa", "Jumla ishlatildi"),
                ("Noto‘g‘ri tushunilgan bo‘lsa, tuzatish xabari", "10 daqiqa", "Tuzatish yuborildi"),
                ("Yaqin odam bilan chuqurroq mavzu", "20 daqiqa", "Suhbat bo‘ldi"),
                ("Hafta oxirida: qaysi ulashish osonroq edi — qisqa yozuv", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "INTJ": (
        _area(
            id="intj-explain",
            name="Qarorni tushuntirish",
            situation=(
                "Agar jamoa sizning rejangizni «sovuq» deb qabul qilsa, lekin siz faqat samaradorlik haqida o‘ylagan bo‘lsangiz, "
                "quyidagi usulni sinab ko‘ring."
            ),
            method="Qarordan oldin qisqa «nega» va kutilayotgan natija.",
            steps=[
                "Bitta qaror tanlang.",
                "Ikki jumlada sabab va foyda.",
                "Savollar uchun 5 daqiqa qoldiring.",
            ],
            today_task="Bitta qaroringizni ikki jumla bilan tushuntirish.",
            success_criteria="Kamida bitta odam sababni eshitdi.",
            lighter_variant="Chatda qisqa xabar yuborish.",
            check_question="Kamroq noto‘g‘ri tushunish bo‘ldimi?",
            week=[
                ("Bitta qaror uchun qisqa tushuntirish", "10 daqiqa", "Tushuntirish berildi"),
                ("Rejada «nega» qatorini qo‘shish", "5 daqiqa", "Qator bor"),
                ("Suhbatda avval maqsad, keyin usul", "15 daqiqa", "Tartib saqlandi"),
                ("Boshqalar fikrini eshitish vaqti", "10 daqiqa", "Tinglash bo‘ldi"),
                ("Xatolik bo‘lsa, ochiq tan olish", "10 daqiqa", "Tan olish aytilgan"),
                ("Murakkab mavzuni diagramma yoki ro‘yxat bilan ko‘rsatish", "15 daqiqa", "Vizual tayyor"),
                ("Hafta oxirida: qaysi tushuntirish yaxshi ishladi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="intj-flex",
            name="Rejada moslashuv joyi",
            situation=(
                "Agar kutilmagan o‘zgarish rejangizni buzsa va asabiylashsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Rejada «B» varianti uchun 20 daqiqalik zaxira vaqt.",
            steps=[
                "Kun rejasiga bo‘sh 20 daqiqa qo‘shing.",
                "O‘zgarish bo‘lsa, shu vaqtda hal qiling.",
                "Asosiy maqsaddan voz kechmasdan, usulni o‘zgartiring.",
            ],
            today_task="Rejaga 20 daqiqalik zaxira qo‘shish.",
            success_criteria="Zaxira vaqt rejada ko‘rinadi.",
            lighter_variant="Faqat bitta vazifani keyinga surish va o‘rniga nima qo‘yilganini yozish.",
            check_question="Kun oxirida asabiylik kamaydimi?",
            week=[
                ("Kun rejasiga zaxira vaqt", "5 daqiqa", "Zaxira belgilandi"),
                ("Bitta vazifani qisqaroq usul bilan sinash", "15 daqiqa", "Alternativ sinab ko‘rildi"),
                ("«Hozir nima muhimroq?» savoliga javob", "5 daqiqa", "Javob yozilgan"),
                ("Kutilmagan ishni zaxira vaqtda qilish", "20 daqiqa", "Ish qilindi yoki reja o‘zgardi"),
                ("Boshqalar taklifini bitta sinab ko‘rish", "15 daqiqa", "Sinov bo‘ldi"),
                ("Kechikish bo‘lsa, keyingi qadamni yozish", "10 daqiqa", "Keyingi qadam aniq"),
                ("Hafta oxirida: qaysi moslashuv yordam berdi — qisqa yozuv", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "INTP": (
        _area(
            id="intp-finish-one",
            name="Bitta g‘oyani yakunlash",
            situation=(
                "Agar yangi savollar eski g‘oyani ochiq qoldirsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta g‘oya uchun «ishlaydigan minimum» belgilash.",
            steps=[
                "Bitta ochiq g‘oyani tanlang.",
                "Eng sodda ishlaydigan holatni bir jumlada yozing.",
                "Faqat shu qismni 15 daqiqada sinab ko‘ring.",
            ],
            today_task="Tanlangan g‘oyaning eng kichik sinovini bajarish.",
            success_criteria="Sinov natijasi yozilgan yoki ko‘rinadi.",
            lighter_variant="Faqat sinov rejasini ro‘yxatga yozish.",
            check_question="G‘oya aniqroq bo‘ldimi yoki yangi savollar paydo bo‘ldimi?",
            week=[
                ("Minimum holat jumlasini yozish", "10 daqiqa", "Jumla tayyor"),
                ("15 daqiqalik sinov", "15 daqiqa", "Sinov bajarildi"),
                ("Yangi savollarni alohida ro‘yxatga yozish", "5 daqiqa", "Ro‘yxat alohida"),
                ("Sinov natijasini uch jumla bilan yozish", "10 daqiqa", "Natija yozilgan"),
                ("Keraksiz qismni olib tashlash", "15 daqiqa", "Kamida bitta qism olib tashlandi"),
                ("Boshqaga qisqa tushuntirish", "10 daqiqa", "Tushuntirish berildi"),
                ("Keyingi qadamni tanlash", "10 daqiqa", "Keyingi qadam yozilgan"),
            ],
        ),
        _area(
            id="intp-feelings",
            name="His-tuyg‘uni so‘z bilan aytish",
            situation=(
                "Agar muhim his-tuyg‘u ichingizda qolib, boshqalar sizni sovuq deb o‘ylasa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta his uchun sodda «men … his qilyapman» jumlasi.",
            steps=[
                "Bugungi eng kuchli hisni tanlang.",
                "Bir jumlada ayting yoki yozing.",
                "Tushuntirish shart emas.",
            ],
            today_task="Bitta his-tuyg‘uni bir jumla bilan ulashish.",
            success_criteria="Jumla aytilgan yoki yuborilgan.",
            lighter_variant="Kundalikda bir qator yozish.",
            check_question="Yengillik sezildimi?",
            week=[
                ("Bitta his jumlasi", "5 daqiqa", "Jumla bor"),
                ("Yaqin odamga qisqa xabar", "5 daqiqa", "Xabar yuborildi"),
                ("Suhbatda his qo‘shish", "10 daqiqa", "His aytilgan"),
                ("Jismoniy belgi (charchoq, quvonch) ni nomlash", "5 daqiqa", "Nom berildi"),
                ("«Men uchun bu muhim, chunki…» jumlasi", "10 daqiqa", "Jumla ishlatildi"),
                ("Tinglash va javob bermaslik mashqi", "10 daqiqa", "Faqat tinglab qoldingiz"),
                ("Hafta oxirida qaysi ulashish osonroq — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ISFP": (
        _area(
            id="isfp-speak-up",
            name="Ovoz chiqarib fikr aytish",
            situation=(
                "Agar guruhda fikringiz ichingizda qolsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Kichik, aniq va qisqa fikr — bitta jumla.",
            steps=[
                "Yig‘ilish yoki suhbat oldidan bitta fikrni yozing.",
                "Mos paytda o‘sha jumlani ayting.",
                "Bahslash shart emas.",
            ],
            today_task="Bitta qisqa fikrni ovoz chiqarib aytish.",
            success_criteria="Kamida bitta jumla aytilgan.",
            lighter_variant="Chatda emoji bilan qo‘llab-quvvatlash va bitta qator izoh.",
            check_question="Keyin pushaymon bo‘ldingizmi?",
            week=[
                ("Bitta jumlalik fikr", "5 daqiqa", "Fikr aytilgan"),
                ("Oldindan yozib olish", "5 daqiqa", "Matn tayyor"),
                ("Do‘st bilan kichik mavzuda fikr", "10 daqiqa", "Suhbat bo‘ldi"),
                ("«Men shunday ko‘ryapman» jumlasi", "10 daqiqa", "Jumla ishlatildi"),
                ("Rad etish yoki «yo‘q» deyish", "5 daqiqa", "Rad javob berildi"),
                ("Ijobiy fikrni aniq aytish", "10 daqiqa", "Maqtov yoki minnat aytilgan"),
                ("Hafta oxirida qaysi holat osonroq — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="isfp-plan",
            name="Kichik reja bilan harakat",
            situation=(
                "Agar «hozir qanday bo‘lsa shunday» yondashuv muhim ishni cho‘zsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta ish uchun uch qadam va bugungi bittasi.",
            steps=[
                "Ishni uch qadamga bo‘ling.",
                "Bugun faqat birinchi qadam.",
                "Qolganini ertaga rejalashtiring.",
            ],
            today_task="Rejadagi birinchi qadamni bajarish.",
            success_criteria="Birinchi qadam tugadi.",
            lighter_variant="Faqat birinchi qadamni yozish.",
            check_question="Ish oldinga siljdimi?",
            week=[
                ("Uch qadam ro‘yxati", "10 daqiqa", "Ro‘yxat bor"),
                ("Birinchi qadam", "15 daqiqa", "Qadam bajarildi"),
                ("Ikkinchi qadam", "15 daqiqa", "Qadam bajarildi"),
                ("Eslatma yoki budilnik qo‘yish", "5 daqiqa", "Eslatma bor"),
                ("Uchinchi qadam", "15 daqiqa", "Qadam bajarildi"),
                ("Ishni yopish — oxirgi tekshiruv", "10 daqiqa", "Ish yopildi yoki aniq holat"),
                ("Keyingi ish uchun bitta qadam tanlash", "10 daqiqa", "Tanlov bor"),
            ],
        ),
    ),
    "ISFJ": (
        _area(
            id="isfj-self",
            name="O‘z ehtiyojini rejalash",
            situation=(
                "Agar doim boshqalarga vaqt ajratib, o‘zingiz charchagan bo‘lsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Kun rejasiga o‘zingiz uchun bitta aniq band.",
            steps=[
                "15 daqiqalik «men uchun» band qo‘shing.",
                "Boshqa vazifalar bilan almashtirmang.",
                "Kerak bo‘lsa, oldindan «bu vaqt band» deb ayting.",
            ],
            today_task="Rejada o‘zingiz uchun 15 daqiqa qoldirish.",
            success_criteria="Vaqt ajratildi va ishlatildi.",
            lighter_variant="5 daqiqa choy/ suv ichish va hech narsa qilmaslik.",
            check_question="Kechqurun energiya qoldimi?",
            week=[
                ("15 daqiqa o‘z vaqt", "15 daqiqa", "Vaqt o‘tdi"),
                ("«Yo‘q» yoki «keyinroq» javobi", "5 daqiqa", "Javob berildi"),
                ("Yordam so‘rash", "10 daqiqa", "So‘rov yuborildi"),
                ("Uxlash vaqti yoki dam olishni himoya qilish", "5 daqiqa", "Chegara aytilgan"),
                ("O‘zingiz yoqtirgan kichik ish", "15 daqiqa", "Ish qilindi"),
                ("Rejani boshqalar bilan kelishish", "10 daqiqa", "Kelishuv bor"),
                ("Hafta oxirida nima yordam berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="isfj-change",
            name="O‘zgarishga asta kirish",
            situation=(
                "Agar kutilmagan o‘zgarish sizni asabiylashtirsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Kichik qadam va aniq savollar bilan yangi holatni tushunish.",
            steps=[
                "Nima o‘zgarganini yozing.",
                "Sizga nima noaniq — bitta savol tuzing.",
                "Javob olguncha katta qaror qilmang.",
            ],
            today_task="Bitta noaniqlik uchun savol berish.",
            success_criteria="Savol berildi yoki javob olindi.",
            lighter_variant="Savolni oldindan yozib qo‘yish.",
            check_question="Xavotir kamaydimi?",
            week=[
                ("O‘zgarish va savol yozuvi", "10 daqiqa", "Yozuv bor"),
                ("Savol berish", "10 daqiqa", "Savol berildi"),
                ("Eski va yangi tartibni solishtirish", "10 daqiqa", "Solishtirish qilindi"),
                ("Bitta kichik sinov (yangi usul)", "15 daqiqa", "Sinov bo‘ldi"),
                ("Kimdan yordam so‘rash mumkin — ro‘yxat", "5 daqiqa", "Ro‘yxat bor"),
                ("Rahbar yoki do‘st bilan qisqa suhbat", "15 daqiqa", "Suhbat bo‘ldi"),
                ("Keyingi hafta uchun bitta qoidani tanlash", "10 daqiqa", "Qoida tanlandi"),
            ],
        ),
    ),
    "ISTJ": (
        _area(
            id="istj-flex-small",
            name="Kichik moslashuv",
            situation=(
                "Agar reja buzilganda hamma narsa to‘xtab qolgandek tuyulsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Asosiy maqsadni saqlab, bitta vazifani qisqaroq usulda bajarish.",
            steps=[
                "Bugungi eng muhim bitta maqsadni tanlang.",
                "Buzilgan qism uchun «80% yechim» toping.",
                "Qolganini keyingi kunga yozing.",
            ],
            today_task="Bitta vazifani qisqaroq usul bilan yopish.",
            success_criteria="Maqsadning asosiy qismi bajarildi.",
            lighter_variant="Faqat keyingi qadamni yozish.",
            check_question="Kun baribir foydali o‘tdimi?",
            week=[
                ("80% yechim bitta vazifada", "15 daqiqa", "Vazifa yopildi"),
                ("Keyingi kun bandi", "5 daqiqa", "Band qo‘yildi"),
                ("Kutilmagan ish — 10 daqiqada hal qilish", "10 daqiqa", "Hal qilindi yoki rejalashtirildi"),
                ("Boshqalar usulini bir marta sinash", "15 daqiqa", "Sinov bo‘ldi"),
                ("Rejani yangilash", "10 daqiqa", "Reja yangilandi"),
                ("«Nima muhim, nima emas» ro‘yxati", "10 daqiqa", "Ro‘yxat bor"),
                ("Hafta oxirida qaysi moslashuv ishladi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="istj-praise",
            name="Ijobiy fikrni aytish",
            situation=(
                "Agar ko‘p tanqid va tuzatish, kam maqtov bo‘lsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Tanqiddan oldin bitta aniq ijobiy kuzatuv.",
            steps=[
                "Bugun bitta odamning yaxshi ishini toping.",
                "Aniq va qisqa ayting.",
                "Keyin kerak bo‘lsa taklif bering.",
            ],
            today_task="Bitta odamga aniq maqtov yoki minnat.",
            success_criteria="Ijobiy fikr aytilgan.",
            lighter_variant="Chatda qisqa «rahmat, … yaxshi bo‘ldi» xabari.",
            check_question="Munosabat yumshoqroq bo‘ldimi?",
            week=[
                ("Bitta maqtov", "5 daqiqa", "Maqtov aytilgan"),
                ("Tanqiddan oldin ijobiy jumla", "10 daqiqa", "Tartib saqlandi"),
                ("Oilada yoki do‘stlar bilan minnat", "10 daqiqa", "Minnat aytilgan"),
                ("O‘zingizning kichik yutug‘ingizni yozish", "5 daqiqa", "Yozuv bor"),
                ("Yig‘ilishda ijobiy xulosa", "10 daqiqa", "Xulosa aytilgan"),
                ("Yordam bergan odamga rahmat", "5 daqiqa", "Rahmat aytilgan"),
                ("Hafta oxirida qaysi odamga oson maqtov berildi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ISTP": (
        _area(
            id="istp-explain",
            name="Qilgan ishni tushuntirish",
            situation=(
                "Agar siz ishni qilib bo‘lgach, boshqalar «nima qildingiz?» deb so‘rasa, quyidagi usulni sinab ko‘ring."
            ),
            method="Uch jumlada: nima qildim, nima uchun, keyingi qadam.",
            steps=[
                "Bitta tugatilgan ishni tanlang.",
                "Uch jumlada yozing.",
                "Kerak bo‘lsa, qisqa ko‘rsatib bering.",
            ],
            today_task="Bitta ish haqida uch jumlalik tushuntirish.",
            success_criteria="Tushuntirish berildi.",
            lighter_variant="Foto yoki qisqa video yuborish.",
            check_question="Savollar kamaydimi?",
            week=[
                ("Uch jumlalik tushuntirish", "10 daqiqa", "Tushuntirish bor"),
                ("Ish jarayonidan bitta qadamni ko‘rsatish", "10 daqiqa", "Ko‘rsatildi"),
                ("Savolga javob — qisqa va aniq", "10 daqiqa", "Javob berildi"),
                ("Reja yoki ro‘yxatni ulashish", "10 daqiqa", "Ulashildi"),
                ("Hamkor bilan bitta qadamni kelishish", "15 daqiqa", "Kelishuv bor"),
                ("Xatolik bo‘lsa, qanday tuzatganingizni aytish", "10 daqiqa", "Aytildi"),
                ("Keyingi hafta uchun aloqa usulini tanlash", "10 daqiqa", "Tanlov bor"),
            ],
        ),
        _area(
            id="istp-wait",
            name="Tez qarordan oldin to‘xtash",
            situation=(
                "Agar muammoni darhol «qo‘lingiz bilan» hal qilmoqchi bo‘lib, keyin afsuslanishingiz mumkin bo‘lsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Harakatdan oldin 10 daqiqa va bitta xavf savoli.",
            steps=[
                "10 daqiqa taymer qo‘ying.",
                "«Agar noto‘g‘ri bo‘lsa, nima bo‘ladi?» deb yozing.",
                "Keyin qaror qiling.",
            ],
            today_task="Bitta muhim qarordan oldin 10 daqiqa kutish.",
            success_criteria="Kutish va qisqa yozuv bor.",
            lighter_variant="Faqat xavf savolini yozish.",
            check_question="Qaror aniqroq bo‘ldimi?",
            week=[
                ("10 daqiqa kutish", "10 daqiqa", "Kutildi"),
                ("Xavf savoli yozuvi", "5 daqiqa", "Yozuv bor"),
                ("Ikkinchi fikr — do‘st yoki hamkordan so‘rash", "10 daqiqa", "So‘rov yuborildi"),
                ("Kichik sinov o‘rniga katta o‘zgarish", "15 daqiqa", "Sinov tanlandi"),
                ("Qilgan ishingizni qisqa qayd etish", "5 daqiqa", "Qayd bor"),
                ("Impulsiv xarid yoki javobdan voz kechish mashqi", "5 daqiqa", "Bir marta to‘xtatildi"),
                ("Hafta oxirida qaysi kutish yordam berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ENFP": (
        _area(
            id="enfp-focus",
            name="Bitta ishni oxirigacha yetkazish",
            situation=(
                "Agar bir vaqtning o‘zida ko‘p g‘oya ochiq qolsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta ishni tanlab, qolganlarini «keyinroq» ro‘yxatiga yozish.",
            steps=[
                "Eng muhim bitta ishni tanlang.",
                "Boshqa g‘oyalarni alohida ro‘yxatga o‘tkazing.",
                "Bugun faqat tanlangan ishning kichik qismi.",
            ],
            today_task="Tanlangan ishning 15 daqiqalik qismini bajarish.",
            success_criteria="Qism bajarildi, yangi ish boshlanmadi.",
            lighter_variant="Faqat «keyinroq» ro‘yxatini tozalash.",
            check_question="Boshqa g‘oya sizni chalg‘itdimi?",
            week=[
                ("Bitta ish tanlash", "5 daqiqa", "Ish tanlandi"),
                ("Keyinroq ro‘yxati", "10 daqiqa", "Ro‘yxat alohida"),
                ("15 daqiqalik qism", "15 daqiqa", "Qism bajarildi"),
                ("Ikkinchi qism", "15 daqiqa", "Qism bajarildi"),
                ("Ishning «tugadi» mezonini yozish", "10 daqiqa", "Mezon bor"),
                ("Yakuniy kichik qadam", "15 daqiqa", "Qadam bajarildi"),
                ("Keyingi hafta uchun bitta ustuvor tanlash", "10 daqiqa", "Tanlov bor"),
            ],
        ),
        _area(
            id="enfp-routine",
            name="Kichik kundalik tartib",
            situation=(
                "Agar yorqin boshlanishlar keyin sustlashsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Har kuni takrorlanadigan bitta kichik odat (5–10 daqiqa).",
            steps=[
                "Bitta oddiy odat tanlang (masalan, ertalab reja).",
                "Xuddi shu vaqtda 5 daqiqa.",
                "Murakkablashtirmang.",
            ],
            today_task="Tanlangan odatni bir marta bajarish.",
            success_criteria="Odat bugun bajarildi.",
            lighter_variant="Eslatma qo‘yish va ertaga boshlash.",
            check_question="Odat qanchalik tabiiy tuyuldi?",
            week=[
                ("Odat tanlash", "5 daqiqa", "Odat tanlandi"),
                ("1-kun odat", "5–10 daqiqa", "Bajarildi"),
                ("2-kun odat", "5–10 daqiqa", "Bajarildi"),
                ("3-kun odat", "5–10 daqiqa", "Bajarildi"),
                ("4-kun odat", "5–10 daqiqa", "Bajarildi"),
                ("5-kun odat", "5–10 daqiqa", "Bajarildi"),
                ("6–7-kun: nima ishladi, nima o‘zgartirish — yozing", "10 daqiqa", "Xulosa yozilgan"),
            ],
        ),
    ),
    "ENFJ": (
        _area(
            id="enfj-listen",
            name="Maslahatdan oldin eshitish",
            situation=(
                "Agar yordam bermoqchi bo‘lib, tez yechim taklif qilsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Avval savol berish, keyin taklif.",
            steps=[
                "«Senga nima kerak?» deb so‘rang.",
                "Kamida ikki javob tinglang.",
                "Keyin bitta taklif qiling.",
            ],
            today_task="Bir suhbatda maslahatdan oldin savol berish.",
            success_criteria="Kamida ikki savol berildi.",
            lighter_variant="Chatda «Qanday yordam kerak?» deb yozish.",
            check_question="Odamlar o‘zlarini eshitilgan deb his qildimi?",
            week=[
                ("Savoldan boshlash", "10 daqiqa", "Savollar berildi"),
                ("Javobni qayta aytish", "10 daqiqa", "Qayta aytildi"),
                ("Taklifni bitta qilish", "10 daqiqa", "Bitta taklif"),
                ("«Men emas, sen» — suhbatda diqqatni qaytarish", "15 daqiqa", "Kuzatildi"),
                ("O‘zingiz uchun chegara", "10 daqiqa", "Chegara aytilgan"),
                ("Yordamdan keyin qisqa fikr so‘rash", "10 daqiqa", "Fikr olindi"),
                ("Hafta oxirida qaysi suhbat yaxshi ketdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="enfj-rest",
            name="O‘z energiyasini asrash",
            situation=(
                "Agar boshqalarning kayfiyati sizni ham charchatsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Kun oxirida 15 daqiqa «hech kim uchun emas» vaqt.",
            steps=[
                "Vaqt belgilang.",
                "Yangi vazifa olmang.",
                "Telefonni chetga qo‘ying.",
            ],
            today_task="15 daqiqa faqat o‘zingiz uchun.",
            success_criteria="Vaqt o‘tdi.",
            lighter_variant="5 daqiqa tinch nafas.",
            check_question="Ertasi kuni yordam berish osonroq bo‘ldimi?",
            week=[
                ("15 daqiqa o‘z vaqt", "15 daqiqa", "Vaqt o‘tdi"),
                ("Kayfiyatni yozish — 1 dan 5", "5 daqiqa", "Baholash bor"),
                ("«Bugun yetarli» degan jumla", "5 daqiqa", "Jumla aytilgan"),
                ("Yordamni keyinga surish (mumkin bo‘lsa)", "10 daqiqa", "Surildi"),
                ("Sevimli kichik ish", "15 daqiqa", "Ish qilindi"),
                ("Uxlash vaqtini himoya qilish", "5 daqiqa", "Vaqt saqlandi"),
                ("Hafta oxirida energiya grafigi — qisqa", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ENTJ": (
        _area(
            id="entj-pause",
            name="Tez qarordan oldin pauza",
            situation=(
                "Agar jamoa sizning sur’atingizdan charchasa, quyidagi usulni sinab ko‘ring."
            ),
            method="Muhim qarordan oldin «bitta tun» yoki qisqa tanaffus qoidasi.",
            steps=[
                "Bugun kechiktiriladigan bitta qarorni tanlang.",
                "Ertaga qayta ko‘rib chiqish vaqtini belgilang.",
                "Hozir faqat ma’lumot to‘plash.",
            ],
            today_task="Bitta qarorni 24 soatga kechiktirish.",
            success_criteria="Qaror yozma qayd etildi va kechiktirildi.",
            lighter_variant="1 soatlik tanaffus.",
            check_question="Keyingi kun qaror aniqroq bo‘ldimi?",
            week=[
                ("Qarorni kechiktirish", "10 daqiqa", "Kechiktirildi"),
                ("Ma’lumot ro‘yxati", "15 daqiqa", "Ro‘yxat bor"),
                ("Boshqalar fikrini so‘rash", "15 daqiqa", "Fikr olindi"),
                ("Qarorni qayta ko‘rib chiqish", "15 daqiqa", "Ko‘rib chiqildi"),
                ("Ijobiy fikr oldin", "10 daqiqa", "Ijobiy jumla aytilgan"),
                ("Vakolatni aniq topshirish", "15 daqiqa", "Topshirildi"),
                ("Hafta oxirida qaysi kechiktirish foyda berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="entj-soft",
            name="Ohangni yumshatish",
            situation=(
                "Agar to‘g‘ri gapingiz qattiq eshitilsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Xabar oldidan bitta ijobiy yoki minnat jumlasi.",
            steps=[
                "Xabar yoki fikrni yozing.",
                "Boshiga bitta ijobiy jumla qo‘shing.",
                "Keyin asosiy fikr.",
            ],
            today_task="Bitta xabarni ijobiy jumla bilan boshlash.",
            success_criteria="Xabar yuborildi yoki aytilgan.",
            lighter_variant="Ovoz ohangini pasaytirish.",
            check_question="Javob yumshoqroq keldi mi?",
            week=[
                ("Ijobiy boshlanish", "10 daqiqa", "Xabar yuborildi"),
                ("Yana bitta ijobiy boshlanish", "10 daqiqa", "Xabar yuborildi"),
                ("Tanqid o‘rniga savol", "10 daqiqa", "Savol ishlatildi"),
                ("«Men … deb o‘ylayapman» jumlasi", "10 daqiqa", "Jumla ishlatildi"),
                ("Yig‘ilishda vaqt berish", "15 daqiqa", "Vaqt berildi"),
                ("Xato bo‘lsa uzr", "5 daqiqa", "Uzr aytilgan"),
                ("Hafta oxirida qaysi usul ishladi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ESFP": (
        _area(
            id="esfp-list",
            name="Kun uchun uch vazifa",
            situation=(
                "Agar kun tartibsiz o‘tsa va muhim ish qolsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Ertalab uchta vazifa, kechqurun belgilash.",
            steps=[
                "Uchta vazifa yozing.",
                "Eng muhimini birinchi qiling.",
                "Kechqurun bajarilganini belgilang.",
            ],
            today_task="Uchta vazifadan bittasini tugatish.",
            success_criteria="Bitta vazifa yopildi.",
            lighter_variant="Faqat bitta vazifa yozish.",
            check_question="Kechqurun rozi bo‘ldingizmi?",
            week=[
                ("Uch vazifa ro‘yxati", "5 daqiqa", "Ro‘yxat bor"),
                ("Birinchi vazifa", "15–30 daqiqa", "Vazifa yopildi"),
                ("Ikkinchi vazifa", "15–30 daqiqa", "Vazifa yopildi"),
                ("Kechki belgilash", "5 daqiqa", "Belgilash qilindi"),
                ("Uchinchi vazifa", "15–30 daqiqa", "Vazifa yopildi"),
                ("Ertaga uchun bitta vazifa oldindan", "5 daqiqa", "Vazifa yozilgan"),
                ("Hafta oxirida qaysi usul yordam berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="esfp-pause",
            name="His-tuyg‘udan oldin tanaffus",
            situation=(
                "Agar xafa bo‘lib tez javob yuborsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Xabar yuborishdan oldin 10 daqiqa kutish.",
            steps=[
                "Xabarni yozing, yubormang.",
                "10 daqiqa boshqa ish.",
                "Qayta o‘qib, yuboring yoki yumshating.",
            ],
            today_task="Bitta xabarni kechiktirilgan yuborish.",
            success_criteria="Kamida 10 daqiqa kutildi.",
            lighter_variant="Faqat xabarni o‘qib, bitta so‘zni yumshatish.",
            check_question="Keyin pushaymon bo‘ldingizmi?",
            week=[
                ("10 daqiqa kutish", "10 daqiqa", "Kutildi"),
                ("Xabarni yumshatish", "10 daqiqa", "Matn o‘zgartirildi"),
                ("Telefonni qo‘yib chiqish", "15 daqiqa", "Tanaffus bo‘ldi"),
                ("Suhbatda «hozir gaplashmayman» degan vaqt", "5 daqiqa", "Vaqt aytilgan"),
                ("Keyin qisqa uzr yoki tushuntirish", "10 daqiqa", "Xabar yuborildi"),
                ("Muhim mavzuni yuzma-yuz rejalash", "15 daqiqa", "Reja bor"),
                ("Hafta oxirida qaysi holat qiyin — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ESFJ": (
        _area(
            id="esfj-ask",
            name="Yordam so‘rash",
            situation=(
                "Agar doim o‘zingiz barcha ishni olib, charchagan bo‘lsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="Aniq, kichik yordam so‘rovi — bir vazifa.",
            steps=[
                "Bitta vazifani tanlang.",
                "Kimga va nima kerakligini yozing.",
                "So‘rov yuboring yoki ayting.",
            ],
            today_task="Bitta aniq yordam so‘rovi.",
            success_criteria="So‘rov aytilgan yoki yuborilgan.",
            lighter_variant="«Bugun … qila olasizmi?» bitta jumla.",
            check_question="Rad javob bo‘lsa ham yengillik sezildimi?",
            week=[
                ("Bitta yordam so‘rovi", "10 daqiqa", "So‘rov bor"),
                ("Yana bitta so‘rov", "10 daqiqa", "So‘rov bor"),
                ("Rad javobga tayyor javob", "5 daqiqa", "Reja bor"),
                ("O‘z vaqtini himoya qilish", "15 daqiqa", "Vaqt o‘tdi"),
                ("Minnat va aniq maqtov", "10 daqiqa", "Aytilgan"),
                ("Vazifani bo‘lishish", "15 daqiqa", "Bo‘lishildi"),
                ("Hafta oxirida qaysi so‘rov osonroq — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="esfj-no",
            name="Muloyim rad etish",
            situation=(
                "Agar hamma narsaga «ha» deb, keyin asabiylashsangiz, quyidagi usulni sinab ko‘ring."
            ),
            method="«Hozir qila olmayman, … vaqtida gaplashamiz» jumlasi.",
            steps=[
                "Bitta iltimoni rad etish yoki kechiktirish.",
                "Sababni qisqa ayting.",
                "Muqobil vaqt taklif qiling.",
            ],
            today_task="Bitta iltimonga muloyim «yo‘q» yoki «keyinroq».",
            success_criteria="Javob berildi.",
            lighter_variant="Faqat keyinroq vaqt taklif qilish.",
            check_question="Pushaymonlik kamaydimi?",
            week=[
                ("Bitta rad yoki kechiktirish", "5 daqiqa", "Javob berildi"),
                ("Yana bitta", "5 daqiqa", "Javob berildi"),
                ("O‘z ehtiyojini bir jumla bilan aytish", "10 daqiqa", "Jumla aytilgan"),
                ("Rejada o‘z bandi", "15 daqiqa", "Band bajarildi"),
                ("Tanqidni shaxsiy emas deb qabul qilish mashqi", "10 daqiqa", "Yozuv bor"),
                ("Yaqin odam bilan ochiq suhbat", "20 daqiqa", "Suhbat bo‘ldi"),
                ("Hafta oxirida qaysi chegara muhim — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
    "ESTJ": (
        _area(
            id="estj-praise-first",
            name="Avval yaxshi tomonni aytish",
            situation=(
                "Agar tez tuzatish boshqalarni ranjitsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Bitta aniq yaxshi ish, keyin taklif.",
            steps=[
                "Nima yaxshi qilinganini toping.",
                "Aniq ayting.",
                "Keyin bitta yaxshilash taklifi.",
            ],
            today_task="Bitta odamga avval maqtov, keyin taklif.",
            success_criteria="Ijobiy jumla aytilgan.",
            lighter_variant="Faqat maqtov.",
            check_question="Reaksiya yumshoqroq bo‘ldimi?",
            week=[
                ("Maqtov + taklif", "10 daqiqa", "Ikkalasi aytilgan"),
                ("Faqat maqtov kuni", "5 daqiqa", "Maqtov aytilgan"),
                ("Savol bilan taklif", "10 daqiqa", "Savol ishlatildi"),
                ("Vakolatni topshirish", "15 daqiqa", "Topshirildi"),
                ("O‘z xatosini tan olish", "10 daqiqa", "Tan olish aytilgan"),
                ("Jamoa fikrini so‘rash", "15 daqiqa", "Fikr olindi"),
                ("Hafta oxirida qaysi usul ishladi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
        _area(
            id="estj-flex",
            name="Rejada istisno qo‘shish",
            situation=(
                "Agar kutilmagan holat hammani stress qilsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Rejada «agar … bo‘lsa» qatorini qo‘shish.",
            steps=[
                "Asosiy reja.",
                "Bitta muqobil senariy.",
                "Kim nima qiladi — qisqa.",
            ],
            today_task="Rejaga bitta muqobil qator qo‘shish.",
            success_criteria="Muqobil rejada ko‘rinadi.",
            lighter_variant="Faqat «B plan» sarlavhasi va bitta qadam.",
            check_question="O‘zgarish bo‘lganda kamroq asabiylashdingizmi?",
            week=[
                ("Muqobil qator", "10 daqiqa", "Qator bor"),
                ("B plan sinovi (mavjud emas bo‘lsa, o‘yin)", "15 daqiqa", "Sinov qilindi"),
                ("Rollar aniq", "10 daqiqa", "Rollar yozilgan"),
                ("Qisqa yig‘ilish", "15 daqiqa", "Yig‘ilish bo‘ldi"),
                ("Moslashuvni maqtash", "5 daqiqa", "Maqtov aytilgan"),
                ("Keraksiz qoidani vaqtincha olib tashlash", "10 daqiqa", "Qoida moslashtirildi"),
                ("Keyingi hafta uchun bitta B plan — yozing", "10 daqiqa", "Reja bor"),
            ],
        ),
    ),
    "ESTP": (
        _area(
            id="estp-finish-boring",
            name="Zerikarli qismni yakunlash",
            situation=(
                "Agar qiziqarli ish tugasa, mayda qismlar ochiq qolsa, quyidagi usulni sinab ko‘ring."
            ),
            method="15 daqiqalik «zerikarli» taymer va bitta qism.",
            steps=[
                "Qolgan zerikarli qismni tanlang.",
                "15 daqiqa taymer.",
                "Faqat shu qism.",
            ],
            today_task="15 daqiqada bitta zerikarli qism.",
            success_criteria="Taymer tugadi, qism bajarildi yoki aniq progress.",
            lighter_variant="Faqat qismni yozib, ertaga boshlash.",
            check_question="Ish yopilishiga yaqinlashdimi?",
            week=[
                ("15 daqiqa zerikarli qism", "15 daqiqa", "Sessiya bo‘ldi"),
                ("Ikkinchi sessiya", "15 daqiqa", "Sessiya bo‘ldi"),
                ("Ishning «tugadi» mezoni", "10 daqiqa", "Mezon yozilgan"),
                ("Uchinchi sessiya", "15 daqiqa", "Sessiya bo‘ldi"),
                ("Natijani tekshirish", "10 daqiqa", "Tekshirildi"),
                ("Yakuniy qism", "15 daqiqa", "Qism yopildi"),
                ("Keyingi loyiha uchun deadline qo‘yish", "10 daqiqa", "Deadline bor"),
            ],
        ),
        _area(
            id="estp-wait-big",
            name="Yirik qarordan oldin kutish",
            situation=(
                "Agar darhol harakat qilish keyin afsus keltirsa, quyidagi usulni sinab ko‘ring."
            ),
            method="Yirik qaror uchun bir tun kutish qoidasi.",
            steps=[
                "Yirik qarorni yozing.",
                "24 soat o‘tkazmasdan amalga oshmaysiz.",
                "Ertaga qayta o‘qing.",
            ],
            today_task="Bitta yirik qarorni kechiktirish.",
            success_criteria="Qaror yozilgan, bugun amalga oshmagan.",
            lighter_variant="1 soat kutish.",
            check_question="Ertaga qaror o‘zgardimi?",
            week=[
                ("Qarorni yozish va kechiktirish", "10 daqiqa", "Kechiktirildi"),
                ("Xavf va foyda ro‘yxati", "15 daqiqa", "Ro‘yxat bor"),
                ("Ishonchli odamdan fikr", "15 daqiqa", "Fikr olindi"),
                ("Qayta o‘qish va qaror", "15 daqiqa", "Qaror qilindi"),
                ("Kichik sinov o‘rniga to‘liq qaror", "15 daqiqa", "Sinov tanlandi"),
                ("Impulsiv xarajatni kechiktirish", "5 daqiqa", "Kechiktirildi"),
                ("Hafta oxirida qaysi kutish foyda berdi — yozing", "10 daqiqa", "Yozuv bor"),
            ],
        ),
    ),
}
