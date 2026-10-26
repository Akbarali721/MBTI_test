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
                (
                    "Bitta chala ishni tanlang va uni tugagan deb aytish uchun nima tayyor bo‘lishini bir jumlada yozing.",
                    "10 daqiqa",
                    "Yangi g‘oya chiqsa ham, bugun shu ish asosiy bo‘lib qoladi.",
                ),
                (
                    "Shu ishning eng kichik bo‘lagini bajaring. Yangi g‘oya kelsa, alohida qog‘ozga yozib, hozir ochmang.",
                    "15 daqiqa",
                    "G‘oya yo‘qolmaydi, faqat o‘z navbatini kutadi.",
                ),
                (
                    "Kecha yozgan jumlani qayta o‘qing va hali ham shu natija kerakligini o‘zingizga ayting.",
                    "5 daqiqa",
                    "Yo‘nalish o‘zgagan bo‘lsa, bugun bitta jumla bilan yangilaysiz.",
                ),
                (
                    "Ishning keyingi kichik bo‘lagini bajaring.",
                    "15 daqiqa",
                    "Bu qadam yangi loyiha emas, kechagi ishning davomi.",
                ),
                (
                    "Tayyor ishni boshqa odam ko‘rsa nima yetishmasligini bitta gap bilan ayting.",
                    "10 daqiqa",
                    "Bitta nuqta butun ishni qaytadan ochmaydi.",
                ),
                (
                    "Shu yetishmovchilikni yopadigan bitta qisqa qadamni bajaring.",
                    "15 daqiqa",
                    "Ish boshqaga ko‘rsatishga yaqinlashadi.",
                ),
                (
                    "Ertaga qilinadigan bitta qadamni tanlang va eslatmaga qo‘ying.",
                    "10 daqiqa",
                    "Ertaga qayerdan kirish oldindan aniq bo‘ladi.",
                ),
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
                (
                    "Bitta qisqa suhbatda javobdan oldin suhbatdoshning gapini bir jumla bilan qaytaring.",
                    "10 daqiqa",
                    "U o‘zini eshitilganini sezishi mumkin.",
                ),
                (
                    "Chatda javob yozishdan oldin xabarni oxirigacha o‘qing va «tushundim» deb boshlang.",
                    "5 daqiqa",
                    "Shoshilinch javob har safar ham kerak bo‘lmasligi mumkin.",
                ),
                (
                    "Muhim mavzuda o‘z fikringizdan oldin bitta aniqlashtiruvchi savol bering.",
                    "10 daqiqa",
                    "Savol bahsni yumshatishi mumkin.",
                ),
                (
                    "Bitta gapni «Men shunday tushundim» deb boshlang, keyin o‘z fikringizni qo‘shing.",
                    "10 daqiqa",
                    "Avval uning nuqtasi, keyin sizniki eshitiladi.",
                ),
                (
                    "Qattiqroq gapdan oldin suhbatdoshning bitta asosiy gapini eslab, shuni ayting.",
                    "10 daqiqa",
                    "Javobingiz uning gapiga tayanadi.",
                ),
                (
                    "E’tirozdan oldin ikkala tomonda ham bitta to‘g‘ri joy borligini ayting.",
                    "15 daqiqa",
                    "E’tiroz shu tan olishdan keyin yengilroq eshitilishi mumkin.",
                ),
                (
                    "Bugun yumshoqroq ketgan suhbatda nima yordam berganini eslang va ertaga yana shuni sinang.",
                    "10 daqiqa",
                    "Yaxshi chiqqan usul esdan chiqmaydi.",
                ),
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
                (
                    "Bitta kichik iltimosga «hozir qiyin, keyinroq gaplashamiz» deb yozing.",
                    "5 daqiqa",
                    "Qisqa javob ham hurmatli javob.",
                ),
                (
                    "Kun oxirida 15 daqiqani o‘zingizga qoldiring va shu vaqtda yangi ish olmang.",
                    "15 daqiqa",
                    "Bu oraliq boshqa odamning iltimosi uchun emas.",
                ),
                (
                    "Yordam so‘raganingizda nima kerakligini bitta aniq jumla bilan ayting.",
                    "10 daqiqa",
                    "Aniq so‘rov odamga yengilroq tushadi.",
                ),
                (
                    "Noqulay bir joyda «bu menga qiyin» deb bir jumla ayting yoki yozing.",
                    "10 daqiqa",
                    "Ichkarida qolgan gap biroz joy topadi.",
                ),
                (
                    "Reja o‘zgarsa, odamga oldindan bitta xabar yozing.",
                    "10 daqiqa",
                    "Kutgan odam yangi vaqtni oldindan biladi.",
                ),
                (
                    "Yaqin odamga bitta ehtiyojingizni ayting. Masalan: bugun tinch vaqt kerak.",
                    "10 daqiqa",
                    "Yaqin odam taxmin qilishi shart emas.",
                ),
                (
                    "Ertaga o‘zingizga qoldiradigan vaqtni oldindan belgilang.",
                    "10 daqiqa",
                    "Ertangi chegara bugundan tayyor turadi.",
                ),
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
                (
                    "Kichik noqulaylikni bitta jumlada yozing: nima bo‘ldi va sizga nima og‘ir.",
                    "10 daqiqa",
                    "Noma’lum og‘irlik bir gapga aylanadi.",
                ),
                (
                    "Shu jumlani yumshoq xabar qilib yuboring yoki ayting.",
                    "10 daqiqa",
                    "Kechiktirilgan gap biroz yengillashishi mumkin.",
                ),
                (
                    "Keyingi suhbatdan oldin nima kelishmoqchi ekaningizni bir gap qilib yozing.",
                    "5 daqiqa",
                    "Suhbatga kirish maqsadi aniq bo‘ladi.",
                ),
                (
                    "Suhbatda avval ikki daqiqa tinglang, keyin o‘z jumlangizni ayting.",
                    "15 daqiqa",
                    "Sizning gapingiz uning gapidan keyin keladi.",
                ),
                (
                    "Bitta gapni «Men shuni his qilyapman» deb boshlang.",
                    "10 daqiqa",
                    "Hisni aytish ayblash emas.",
                ),
                (
                    "Suhbat oxirida kelishuvni yoki keyingi qadamni bir jumla bilan ayting.",
                    "10 daqiqa",
                    "Ikkalangiz ham nima bo‘lishini bilasiz.",
                ),
                (
                    "Ertaga ochiq aytmoqchi bo‘lgan bitta mavzuni tanlang va qachon gaplashishingizni belgilang.",
                    "10 daqiqa",
                    "Mavzu yana ichkarida qolib ketmaydi.",
                ),
            ],
        ),
    ),
    "INFJ": (
        _area(
            id="infj-rest",
            name="O‘ziga vaqt ajratish",
            situation=(
                "Agar boshqalarning ehtiyoji dam olish vaqtingizni tez-tez egallab ketsa, quyidagi usulni sinab ko‘ring."
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
                (
                    "Telefonni boshqa xonaga qo‘yib, 15 daqiqa hech kimga javob yozmang.",
                    "15 daqiqa",
                    "Shu daqiqalar boshqa odamning xabari uchun emas.",
                ),
                (
                    "Ertaga kerak bo‘lishi mumkin bo‘lgan «bugun sig‘maydi» javobini oldindan yozib qo‘ying.",
                    "5 daqiqa",
                    "Kerak bo‘lganda tayyor jumla yoningizda turadi.",
                ),
                (
                    "Yordam taklif qilishdan oldin bugun kuchingiz yetadimi, o‘zingizga ayting.",
                    "5 daqiqa",
                    "Hozir yo‘q deyish odamni tashlab ketish emas.",
                ),
                (
                    "15 daqiqani boshqa odam uchun emas, o‘zingiz xohlagan bitta kichik ishga sarflang.",
                    "15 daqiqa",
                    "Bu vaqt sizniki.",
                ),
                (
                    "Uzoq suhbatdan oldin «menda 15 daqiqa bor» deb ayting.",
                    "5 daqiqa",
                    "Chegara oldindan aytilsa, suhbat yengilroq tugashi mumkin.",
                ),
                (
                    "Ertangi dam olishni reja qatoriga yozing va uni ish bilan almashtirmang.",
                    "10 daqiqa",
                    "Dam olish ham rejadagi ish kabi joy oladi.",
                ),
                (
                    "Ertaga yana qaysi vaqtda telefonni chetga qo‘yishingizni belgilang.",
                    "10 daqiqa",
                    "Tanaffus tasodifga qolmaydi.",
                ),
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
                (
                    "Bitta muhim fikrni uch jumladan oshirmay yozing.",
                    "10 daqiqa",
                    "Qisqa matnni aytish osonroq.",
                ),
                ("Shu fikrni guruhda yoki chatda ayting.", "10 daqiqa", "Ichki fikr bitta odamgacha yetadi."),
                (
                    "Keyingi gapni oldindan yozib oling va o‘sha matndan foydalaning.",
                    "10 daqiqa",
                    "Tayyor jumla o‘rtada yo‘qolmaydi.",
                ),
                (
                    "Bitta gapni «Men shunday ko‘ryapman» deb boshlang.",
                    "10 daqiqa",
                    "Bu sizning ko‘rishingiz, yakuniy hukm emas.",
                ),
                (
                    "Noto‘g‘ri tushunilgan bo‘lsangiz, bitta tuzatuvchi xabar yuboring.",
                    "10 daqiqa",
                    "Bitta xabar tushunmovchilikni cho‘zmasligi mumkin.",
                ),
                (
                    "Yaqin odamga bitta chuqurroq fikringizni 15 daqiqa ichida ayting.",
                    "15 daqiqa",
                    "Yaqin odam taxmin qilishi shart emas.",
                ),
                (
                    "Ertaga aytmoqchi bo‘lgan bitta fikrni tanlang va qachon aytishingizni belgilang.",
                    "10 daqiqa",
                    "Ertangi gap oldindan joy topadi.",
                ),
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
                (
                    "Bitta qaroringizning sababini va undan kimga foyda borligini ikki jumla qilib yozing.",
                    "10 daqiqa",
                    "Sabab aytilsa, odamlar rejangizni osonroq ko‘radi.",
                ),
                (
                    "Shu ikki jumlani guruhga yoki bitta odamga yuboring.",
                    "5 daqiqa",
                    "Qisqa xabar ham tushuntirish bo‘lishi mumkin.",
                ),
                (
                    "Suhbatda avval maqsadni, keyin usulni ayting.",
                    "15 daqiqa",
                    "Odamlar avval nima uchunligini eshitadi.",
                ),
                (
                    "O‘z rejangizni aytgach, 10 daqiqa boshqalarning savolini eshiting.",
                    "10 daqiqa",
                    "Savol rejangizni buzishi shart emas, aniqlashtirishi mumkin.",
                ),
                (
                    "Agar xato bo‘lsa, uni bitta jumla bilan ochiq ayting.",
                    "10 daqiqa",
                    "Qisqa tan olish ishonchni saqlashi mumkin.",
                ),
                (
                    "Murakkab ishni uch qatorlik ro‘yxat qilib ko‘rsating.",
                    "15 daqiqa",
                    "Uch qator uzun tushuntirishdan yengilroq.",
                ),
                (
                    "Ertaga tushuntirmoqchi bo‘lgan bitta qarorni tanlang va ikki jumlasini oldindan yozing.",
                    "10 daqiqa",
                    "Ertangi gap shoshilinch bo‘lmaydi.",
                ),
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
                (
                    "Bugungi reja yoniga 15 daqiqalik bo‘sh vaqt yozing.",
                    "5 daqiqa",
                    "Kutilmagan ish chiqsa, butun kun siljishi shart emas.",
                ),
                (
                    "Bitta vazifani qisqaroq usul bilan sinab ko‘ring. Asosiy natija o‘sha qolsin.",
                    "15 daqiqa",
                    "Qisqa yo‘l ham natijani saqlashi mumkin.",
                ),
                (
                    "«Hozir nima muhimroq?» savoliga bir jumla javob yozing.",
                    "5 daqiqa",
                    "Bitta tanlov qolgan ishlarni navbatga qo‘yadi.",
                ),
                (
                    "Kutilmagan ish chiqsa, uni shu bo‘sh vaqtda qiling yoki ertaga yozing.",
                    "15 daqiqa",
                    "Reja siljigani uchun kun bekor bo‘lmaydi.",
                ),
                (
                    "Boshqa odamning bitta taklifini kichik ishda sinab ko‘ring.",
                    "15 daqiqa",
                    "Sinov butun rejangizni almashtirmaydi.",
                ),
                (
                    "Kechikish bo‘lsa, keyingi bitta qadamni yozing. Butun rejani o‘chirmang.",
                    "10 daqiqa",
                    "Bir qadam rejani qayta tiklashga yetishi mumkin.",
                ),
                (
                    "Ertangi reja yoniga yana 15 daqiqa bo‘sh joy qoldiring.",
                    "5 daqiqa",
                    "Ertangi kun ham nafas oladigan joy bilan boshlanadi.",
                ),
            ],
        ),
    ),
    "INTP": (
        _area(
            id="intp-finish-one",
            name="Bitta g‘oyani yakunlash",
            situation=("Agar yangi savollar eski g‘oyani ochiq qoldirsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta ochiq g‘oyaning eng sodda ishlaydigan holatini bir jumla qilib yozing.",
                    "10 daqiqa",
                    "Mukammal variantni kutmasdan, kichik holat ham yetadi.",
                ),
                (
                    "Faqat shu holatni 15 daqiqada sinab ko‘ring. Yangi savol chiqsa, chetga yozing.",
                    "15 daqiqa",
                    "Savol yo‘qolmaydi, sinov esa bugun joyida qoladi.",
                ),
                (
                    "Yangi savollarni alohida ro‘yxatga yozing va bugungi ishni qayta ochmang.",
                    "5 daqiqa",
                    "Ro‘yxat g‘oyani saqlaydi, ish esa davom etadi.",
                ),
                (
                    "Sinovdan nima chiqqanini uch jumla bilan o‘zingizga yoki yaqin odamga ayting.",
                    "10 daqiqa",
                    "Qisqa xulosa ishni ochiq qoldirmaydi.",
                ),
                (
                    "Ishlamagan bitta bo‘lakni olib tashlang.",
                    "15 daqiqa",
                    "Ortig‘i ketganda, ishlaydigan qismi ko‘rinadi.",
                ),
                (
                    "Natijani bitta odamga uch jumla bilan tushuntiring.",
                    "10 daqiqa",
                    "Boshqa odam eshitsa, g‘oya faqat sizda qolmaydi.",
                ),
                (
                    "Ertaga qilinadigan bitta keyingi qadamni tanlang.",
                    "10 daqiqa",
                    "Ertaga qayerdan kirish aniq bo‘ladi.",
                ),
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
                (
                    "Bugungi eng sezilarli hisni bir jumla qilib yozing.",
                    "5 daqiqa",
                    "Nom qo‘yilgan his biroz tushunarli bo‘ladi.",
                ),
                (
                    "Shu jumlani yaqin odamga qisqa xabar qilib yuboring.",
                    "5 daqiqa",
                    "Yaqin odam taxmin qilishi shart emas.",
                ),
                (
                    "Bitta suhbatda hisni ham qo‘shing. Tushuntirish shart emas.",
                    "10 daqiqa",
                    "Hisni aytish sabab izlash emas.",
                ),
                (
                    "Charchoq yoki quvonchni bir so‘z bilan nomlang va shu so‘zni eslab qoling.",
                    "5 daqiqa",
                    "Bir so‘z keyingi gapga eshik ochadi.",
                ),
                (
                    "Bitta gapni «Bu menga muhim, chunki» deb boshlang.",
                    "10 daqiqa",
                    "Muhimlik sabab bilan birga eshitiladi.",
                ),
                (
                    "10 daqiqa faqat tinglang va yechim aytmang.",
                    "10 daqiqa",
                    "Tinglash ham yordam bo‘lishi mumkin.",
                ),
                (
                    "Ertaga aytmoqchi bo‘lgan bitta hisni tanlang va kimga aytishingizni belgilang.",
                    "10 daqiqa",
                    "Ertangi gap oldindan joy topadi.",
                ),
            ],
        ),
    ),
    "ISFP": (
        _area(
            id="isfp-speak-up",
            name="Ovoz chiqarib fikr aytish",
            situation=("Agar guruhda fikringiz ichingizda qolsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta fikringizni oldindan bir jumla qilib yozing.",
                    "5 daqiqa",
                    "Tayyor jumla o‘rtada yo‘qolmaydi.",
                ),
                ("Shu jumlani guruhda yoki chatda ayting. Bahslashmang.", "10 daqiqa", "Bitta gap ham ovoz."),
                (
                    "Do‘st bilan kichik mavzuda o‘z fikringizni ayting.",
                    "10 daqiqa",
                    "Kichik mavzuda ham fikr aytish mumkin.",
                ),
                (
                    "Bitta gapni «Men shunday ko‘ryapman» deb boshlang.",
                    "10 daqiqa",
                    "Bu sizning ko‘rishingiz.",
                ),
                (
                    "Noqulay bitta iltimosga «yo‘q» yoki «keyinroq» deb yozing.",
                    "5 daqiqa",
                    "Qisqa rad ham muloyim javob.",
                ),
                (
                    "Bitta odamga aniq minnat yoki yaxshi so‘z ayting.",
                    "10 daqiqa",
                    "Aniq so‘z odamga yetib boradi.",
                ),
                (
                    "Ertaga aytmoqchi bo‘lgan bitta fikrni tanlang.",
                    "5 daqiqa",
                    "Ertangi gap oldindan tayyor turadi.",
                ),
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
                (
                    "Bitta ishni uch qadamga bo‘lib yozing.",
                    "10 daqiqa",
                    "Uch qadam katta ishni kichik qiladi.",
                ),
                (
                    "Bugun faqat birinchi qadamni bajaring.",
                    "15 daqiqa",
                    "Birinchi qadam keyingilariga yo‘l ochadi.",
                ),
                (
                    "Ikkinchi qadamni bajaring. Uchinchi qadamga o‘tmang.",
                    "15 daqiqa",
                    "Bitta qadam bugun uchun yetarli sur’at.",
                ),
                (
                    "Uchinchi qadam uchun ertangi eslatmani qo‘ying.",
                    "5 daqiqa",
                    "Ertaga nima qilish esdan chiqmaydi.",
                ),
                ("Uchinchi qadamni bajaring.", "15 daqiqa", "Ish shu uch qadam bilan yig‘iladi."),
                (
                    "Ishga bir marta qarab chiqing. Qolgan joy bo‘lsa, ertaga bitta qadam qilib yozing.",
                    "10 daqiqa",
                    "Qolgan joy ham kichik qadamga aylanadi.",
                ),
                (
                    "Keyingi ish uchun faqat birinchi qadamni tanlab yozing.",
                    "10 daqiqa",
                    "Yangi ish ham bitta qadamdan boshlanadi.",
                ),
            ],
        ),
    ),
    "ISFJ": (
        _area(
            id="isfj-self",
            name="O‘z ehtiyojini rejalash",
            situation=(
                "Agar boshqalarga vaqt ajratib, o‘zingiz tez-tez charchab qolsangiz, quyidagi usulni sinab ko‘ring."
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
                (
                    "Telefonni qo‘yib, 15 daqiqa hech kimga javob yozmang.",
                    "15 daqiqa",
                    "Shu daqiqalarda javob kutishingiz shart emas.",
                ),
                (
                    "Bitta iltimosga «bugun sig‘maydi» yoki «ertaga qarayman» deb yozing.",
                    "5 daqiqa",
                    "Qisqa rad ham munosabatni buzishi shart emas.",
                ),
                (
                    "O‘z ishingizdan bitta bo‘lakni boshqa odamdan so‘rang.",
                    "10 daqiqa",
                    "Hammasini o‘zingiz ko‘tarishingiz shart emas.",
                ),
                (
                    "Kechki uyqu vaqtingizni ayting va shu soatdan keyin yangi ish olmang.",
                    "10 daqiqa",
                    "Shu soatdan keyin kun sizniki.",
                ),
                (
                    "15 daqiqa o‘zingiz xohlagan bitta ish qiling: sayr, musiqa yoki choy.",
                    "15 daqiqa",
                    "Bu vaqt boshqa odamning ishi uchun emas.",
                ),
                (
                    "Ertangi ishlardan bittasini do‘st yoki oilaga ayting.",
                    "10 daqiqa",
                    "Ertangi yuk biroz yengilroq bo‘lishi mumkin.",
                ),
                (
                    "Qaysi payt o‘zingizga vaqt qolganini eslang va ertaga shunday vaqtni yana belgilang.",
                    "10 daqiqa",
                    "O‘z vaqtingiz tasodifga qolmaydi.",
                ),
            ],
        ),
        _area(
            id="isfj-change",
            name="O‘zgarishga asta kirish",
            situation=("Agar kutilmagan o‘zgarish sizni asabiylashtirsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Nima o‘zgarganini va nimani tushunmayotganingizni ikki qator qilib yozing.",
                    "10 daqiqa",
                    "Noaniqlik bir varaqda ko‘rinadi.",
                ),
                (
                    "Shu savolni do‘st, oila yoki o‘qituvchiga bering.",
                    "10 daqiqa",
                    "Savolni boshqa odam ham eshitsa, yolg‘iz qolmaydi.",
                ),
                (
                    "Eski tartibda nima qolgani va yangisida nima boshqaligini ikki qator qilib yozing.",
                    "10 daqiqa",
                    "O‘zgarmagan joy ham borligini ko‘rasiz.",
                ),
                (
                    "Yangi usulni faqat bitta kichik ishda sinab ko‘ring.",
                    "15 daqiqa",
                    "Sinov butun tartibingizni almashtirmaydi.",
                ),
                (
                    "Yordam so‘rash mumkin bo‘lgan ikki kishining ismini yozing.",
                    "5 daqiqa",
                    "Kerak bo‘lsa, kimga murojaat qilish oldindan aniq.",
                ),
                (
                    "Do‘st yoki oila a’zosi bilan 15 daqiqa gaplashing.",
                    "15 daqiqa",
                    "Oddiy suhbat yangi holatni yengilroq qilishi mumkin.",
                ),
                (
                    "Bitta oddiy qoida yozing. Masalan: 22:00 dan keyin yangi ish olmaslik.",
                    "10 daqiqa",
                    "Bitta qoida yangi haftaga tayanch bo‘ladi.",
                ),
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
                "Buzilgan qism uchun hozir yetadigan sodda yechimni tanlang.",
                "Qolganini keyingi kunga yozing.",
            ],
            today_task="Bitta vazifani qisqaroq usul bilan yopish.",
            success_criteria="Maqsadning asosiy qismi bajarildi.",
            lighter_variant="Faqat keyingi qadamni yozish.",
            check_question="Kun baribir foydali o‘tdimi?",
            week=[
                (
                    "Buzilgan bitta vazifaning asosiy qismini sodda usul bilan yoping.",
                    "15 daqiqa",
                    "Sodda usul ham kunni saqlab qolishi mumkin.",
                ),
                (
                    "Qolgan qismini ertangi kunga bir qator qilib yozing.",
                    "5 daqiqa",
                    "Qolgani yo‘qolmaydi, ertaga o‘z joyida turadi.",
                ),
                (
                    "Kutilmagan ish chiqsa, 10 daqiqada hal qiling yoki ertaga qo‘ying.",
                    "10 daqiqa",
                    "Har bir yangi ish butun rejani to‘xtatishi shart emas.",
                ),
                (
                    "Boshqa odamning usulini bitta kichik ishda sinab ko‘ring.",
                    "15 daqiqa",
                    "Sinov odatdagi tartibingizni bekor qilmaydi.",
                ),
                (
                    "Bugungi rejani yangilang: tugagan ishni belgilang, qolganini ajrating.",
                    "10 daqiqa",
                    "Yangilangan reja kunni qayta ko‘rsatadi.",
                ),
                (
                    "Bugun nima muhimligini va nima ertaga qolishini o‘zingizga ayting.",
                    "10 daqiqa",
                    "Muhim narsa qolgan ishdan ajralib qoladi.",
                ),
                (
                    "Ertangi reja yoniga bitta sodda zaxira usul yozing.",
                    "10 daqiqa",
                    "Ertaga reja siljisa, tayyor yo‘l bor.",
                ),
            ],
        ),
        _area(
            id="istj-praise",
            name="Ijobiy fikrni aytish",
            situation=("Agar ko‘p tanqid va tuzatish, kam maqtov bo‘lsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta odamning aniq yaxshi ishini topib, shuni ayting.",
                    "5 daqiqa",
                    "Aniq so‘z umumiy maqtovdan issiqroq eshitiladi.",
                ),
                (
                    "Tuzatish yozishdan oldin bitta yaxshi joyni yozing.",
                    "10 daqiqa",
                    "Yaxshi joy eshitilsa, tuzatish yengilroq tushishi mumkin.",
                ),
                (
                    "Oila yoki do‘stga bitta aniq minnat ayting.",
                    "10 daqiqa",
                    "Kichik minnat ham odamga yetadi.",
                ),
                (
                    "O‘zingizning bugungi bitta kichik ishingizni eslang va o‘zingizga ayting.",
                    "5 daqiqa",
                    "O‘z ishingiz ham e’tiborga loyiq.",
                ),
                (
                    "Guruhda yoki chatda bitta yaxshi xulosa ayting.",
                    "10 daqiqa",
                    "Yaxshi xulosa faqat sizda qolmaydi.",
                ),
                (
                    "Yordam bergan odamga nima uchun rahmat ekanini bir jumla qilib yozing.",
                    "5 daqiqa",
                    "Sababli rahmat aniqroq eshitiladi.",
                ),
                (
                    "Ertaga kimga yaxshi so‘z aytishingizni oldindan tanlang.",
                    "5 daqiqa",
                    "Ertangi so‘z tasodifga qolmaydi.",
                ),
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
                (
                    "Tugatgan bitta ishingizni uch jumla qilib yozing: nima qildingiz, nima uchun, keyin nima.",
                    "10 daqiqa",
                    "Uch jumla ishni boshqaga ko‘rsatadi.",
                ),
                (
                    "Shu ishdan bitta qadamni odamga ko‘rsating yoki rasm bilan yuboring.",
                    "10 daqiqa",
                    "Ko‘rsatish uzun tushuntirishdan osonroq.",
                ),
                (
                    "Bitta savolga qisqa va aniq javob yozing. Ortiqcha izoh qo‘shmang.",
                    "10 daqiqa",
                    "Qisqa javob ham to‘liq bo‘lishi mumkin.",
                ),
                (
                    "Reja yoki ro‘yxatingizni bitta odamga yuboring.",
                    "10 daqiqa",
                    "Ro‘yxatni ko‘rgan odam keyingi qadamni biladi.",
                ),
                (
                    "Hamkor bilan keyingi bitta qadamni kelishib oling.",
                    "15 daqiqa",
                    "Ikkalangiz ham nima bo‘lishini bilasiz.",
                ),
                (
                    "Xato bo‘lgan bo‘lsa, uni qanday tuzatganingizni bir jumla qilib ayting.",
                    "10 daqiqa",
                    "Tuzatishni aytish uzun uzrdan aniqroq.",
                ),
                (
                    "Keyingi safar qanday qisqa xabar berishingizni bir jumla qilib belgilang.",
                    "10 daqiqa",
                    "Keyingi xabar oldindan osonroq bo‘ladi.",
                ),
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
                (
                    "Katta qarordan oldin 10 daqiqa kuting va hozir hech narsa qilmang.",
                    "10 daqiqa",
                    "O‘n daqiqa qarorni buzmaydi, faqat biroz sovitadi.",
                ),
                (
                    "«Agar noto‘g‘ri bo‘lsa, nima bo‘ladi?» savoliga bir jumla yozing.",
                    "5 daqiqa",
                    "Xavf bir gapda ko‘rinadi.",
                ),
                (
                    "Shu qaror haqida do‘stdan bitta fikr so‘rang.",
                    "10 daqiqa",
                    "Boshqa ko‘z bitta nuqtani ko‘rsatishi mumkin.",
                ),
                (
                    "Katta o‘zgarish o‘rniga bitta kichik sinov tanlang va uni bajaring.",
                    "15 daqiqa",
                    "Kichik sinov katta qarorni shoshiltirmaydi.",
                ),
                (
                    "Sinovdan nima chiqqanini o‘zingizga uch jumla bilan ayting.",
                    "10 daqiqa",
                    "Qisqa xulosa keyingi qadamni ochadi.",
                ),
                (
                    "Shoshilinch bitta xarid yoki qattiq javobni hozir yubormang. Ertaga qayta o‘qing.",
                    "5 daqiqa",
                    "Ertangi siz bugungi shoshqaloqdan boshqacha ko‘rishingiz mumkin.",
                ),
                (
                    "Ertaga kutmoqchi bo‘lgan bitta qarorni yozing va vaqtini belgilang.",
                    "10 daqiqa",
                    "Kutish tasodifga qolmaydi.",
                ),
            ],
        ),
    ),
    "ENFP": (
        _area(
            id="enfp-focus",
            name="Bitta ishni oxirigacha yetkazish",
            situation=("Agar bir vaqtning o‘zida ko‘p g‘oya ochiq qolsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Ochiq ishlardan bittasini tanlang. Qolganini «keyinroq» ro‘yxatiga yozing.",
                    "10 daqiqa",
                    "Bitta ish tanlansa, qolgani yo‘qolmaydi.",
                ),
                (
                    "Tanlangan ishning 15 daqiqalik bo‘lagini bajaring. Yangi ish ochmang.",
                    "15 daqiqa",
                    "Yangi ish navbatini kutadi.",
                ),
                (
                    "Tanlangan ishda keyingi kichik qadamni belgilang va shu bilan cheklaning.",
                    "5 daqiqa",
                    "Bugun bitta yo‘nalish yetadi.",
                ),
                ("Ikkinchi bo‘lakni bajaring.", "15 daqiqa", "Kechagi ish davom etadi."),
                (
                    "Bu ish tugagan deb aytish uchun nima tayyor bo‘lishini bir jumla qilib yozing.",
                    "10 daqiqa",
                    "Tugash nuqtasi o‘zingizga tushunarli bo‘ladi.",
                ),
                (
                    "Shu jumlaga yetkazadigan oxirgi kichik qadamni bajaring.",
                    "15 daqiqa",
                    "Ish ko‘rsatishga yaqinlashadi.",
                ),
                (
                    "Keyingi hafta uchun faqat bitta asosiy ishni tanlab yozing.",
                    "10 daqiqa",
                    "Yangi hafta ham bitta ishdan boshlanadi.",
                ),
            ],
        ),
        _area(
            id="enfp-routine",
            name="Kichik kundalik tartib",
            situation=("Agar yorqin boshlanishlar keyin sustlashsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Har kuni takrorlamoqchi bo‘lgan bitta oddiy ish tanlang. Masalan: ertalab uchta ish yozish.",
                    "5 daqiqa",
                    "Bitta kichik ish katta qoidadan yengilroq.",
                ),
                (
                    "Shu ishni bugun 10 daqiqada bajaring. Yangi qoida qo‘shmang.",
                    "10 daqiqa",
                    "Bugun bitta takror yetadi.",
                ),
                (
                    "Ertangi shu ish uchun o‘zingizga eslatma qo‘ying.",
                    "5 daqiqa",
                    "Eslatma ertangi takrorni esdan chiqarmaydi.",
                ),
                (
                    "Shu ishni yana bajaring. O‘tkazib yuborgan bo‘lsangiz, kechqurun 10 daqiqa ichida yoping.",
                    "10 daqiqa",
                    "Kechikkan takror ham kunni saqlab qolishi mumkin.",
                ),
                (
                    "Shu ishni o‘sha vaqtda yana qiling.",
                    "10 daqiqa",
                    "Bir xil vaqt ishni odatga yaqinlashtiradi.",
                ),
                (
                    "Nima oson bo‘lganini va nima xalaqit berganini eslang.",
                    "10 daqiqa",
                    "Xalaqitni ko‘rsangiz, ertaga undan chetlanish osonroq.",
                ),
                (
                    "Keyingi hafta shu ishni saqlaysizmi, bir jumla bilan belgilang.",
                    "5 daqiqa",
                    "Saqlash yoki almashtirish sizning tanlovingiz.",
                ),
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
                (
                    "Maslahat berishdan oldin «Senga nima kerak?» deb so‘rang.",
                    "10 daqiqa",
                    "Savol maslahatdan oldin keladi.",
                ),
                (
                    "Javobni o‘z so‘zingiz bilan bir jumla qilib qaytaring.",
                    "10 daqiqa",
                    "U o‘z gapini sizdan eshitishi mumkin.",
                ),
                (
                    "Shundan keyin faqat bitta taklif qiling.",
                    "10 daqiqa",
                    "Bitta taklif tanlovni yengil qoldiradi.",
                ),
                (
                    "Suhbatda gapni o‘zingizga emas, suhbatdoshga qaytaring: «Sen nima xohlaysan?»",
                    "15 daqiqa",
                    "Diqqat biroz unga qaytadi.",
                ),
                (
                    "Yordamga chegara qo‘ying: «Bugun shu qismda yordam bera olaman».",
                    "10 daqiqa",
                    "Chegara ham yordamning bir turi.",
                ),
                (
                    "Yordamdan keyin «Bu foydali bo‘ldimi?» deb so‘rang.",
                    "10 daqiqa",
                    "Uning javobi keyingi yordamni yo‘naltiradi.",
                ),
                (
                    "Ertangi suhbatda maslahatdan oldin qanday savol berishingizni oldindan yozing.",
                    "10 daqiqa",
                    "Ertangi savol tayyor turadi.",
                ),
            ],
        ),
        _area(
            id="enfj-rest",
            name="O‘z energiyasini asrash",
            situation=("Agar boshqalarning kayfiyati sizni ham charchatsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "15 daqiqani faqat o‘zingizga qoldiring. Telefonni chetga qo‘ying va yangi ish olmang.",
                    "15 daqiqa",
                    "Shu vaqt boshqa odamning ishi uchun emas.",
                ),
                (
                    "Bugungi charchoqni 1 dan 5 gacha yozing va bir so‘z bilan sababini qo‘shing.",
                    "5 daqiqa",
                    "Raqam charchoqni ko‘rishga yordam beradi.",
                ),
                (
                    "Bitta odamga «bugun shu yerda to‘xtayman» deb yozing.",
                    "5 daqiqa",
                    "To‘xtashni aytish ham g‘amxo‘rlik.",
                ),
                (
                    "Yangi yordam so‘rovi kelsa, iloji bo‘lsa ertaga deb yozing.",
                    "10 daqiqa",
                    "Ertaga ham yordam berish mumkin.",
                ),
                (
                    "O‘zingiz xohlagan bitta kichik ishni 15 daqiqa qiling.",
                    "15 daqiqa",
                    "Bu daqiqalar sizniki.",
                ),
                (
                    "Uyqu vaqtingizni ayting va shu soatdan keyin yangi suhbat ochmang.",
                    "5 daqiqa",
                    "Shu soatdan keyin kun yopiladi.",
                ),
                (
                    "Ertaga o‘zingizga qoldiradigan 15 daqiqani oldindan belgilang.",
                    "10 daqiqa",
                    "Ertangi dam olish tasodifga qolmaydi.",
                ),
            ],
        ),
    ),
    "ENTJ": (
        _area(
            id="entj-pause",
            name="Tez qarordan oldin pauza",
            situation=("Agar jamoa sizning sur’atingizdan charchasa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bugun qilinmaydigan bitta qarorni yozing va ertaga qayta ko‘rish vaqtini qo‘ying.",
                    "10 daqiqa",
                    "Ertaga ham shu qaror sizniki bo‘ladi.",
                ),
                (
                    "Shu qaror uchun sizda bor ma’lumotni uch qator qilib yozing.",
                    "15 daqiqa",
                    "Ma’lumot yig‘ilsa, shoshilish kamayishi mumkin.",
                ),
                (
                    "Bitta odamdan shu qaror haqida fikr so‘rang.",
                    "15 daqiqa",
                    "Boshqa fikr siznikini bekor qilmaydi.",
                ),
                (
                    "Kecha qo‘yib qo‘ygan qarorni qayta o‘qing va tasdiqlang yoki o‘zgartiring.",
                    "15 daqiqa",
                    "Bir kecha qarorni boshqacha ko‘rsatishi mumkin.",
                ),
                (
                    "Xabar yuborishdan oldin bitta yaxshi qilingan joyni yozing.",
                    "10 daqiqa",
                    "Yaxshi jumla keyingi gapni yumshatadi.",
                ),
                (
                    "Bitta ishning muddati va kim qilishini aniq qilib yozing.",
                    "15 daqiqa",
                    "Aniq muddat shoshilinch qarorni bosadi.",
                ),
                (
                    "Ertaga pauza qilmoqchi bo‘lgan bitta qarorni oldindan belgilang.",
                    "10 daqiqa",
                    "Pauza ertaga ham joy topadi.",
                ),
            ],
        ),
        _area(
            id="entj-soft",
            name="Ohangni yumshatish",
            situation=("Agar to‘g‘ri gapingiz qattiq eshitilsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta xabarni yaxshi jumla bilan boshlang, keyin asosiy gapni yozing.",
                    "10 daqiqa",
                    "Birinchi jumla xabarning ohangini beradi.",
                ),
                (
                    "Yana bitta xabarni xuddi shu tartibda yuboring.",
                    "10 daqiqa",
                    "Ikkinchi marta ohang tanishroq bo‘ladi.",
                ),
                (
                    "Tanqid o‘rniga bitta savol bering: «Shu joyni qanday yopamiz?»",
                    "10 daqiqa",
                    "Savol birga yechim izlaydi.",
                ),
                (
                    "Bitta gapni «Men shunday o‘ylayapman» deb boshlang.",
                    "10 daqiqa",
                    "Bu sizning fikringiz, buyruq emas.",
                ),
                (
                    "Guruh suhbatida boshqalarga kamida 10 daqiqa gapirish vaqti qoldiring.",
                    "15 daqiqa",
                    "Siz kutganingizda boshqalar ham eshitiladi.",
                ),
                (
                    "Xato bo‘lsa, bitta qisqa uzr ayting.",
                    "5 daqiqa",
                    "Qisqa uzr ham munosabatni yumshatishi mumkin.",
                ),
                (
                    "Ertangi bitta xabarni yaxshi jumla bilan oldindan boshlang.",
                    "10 daqiqa",
                    "Ertangi ohang bugundan tayyor.",
                ),
            ],
        ),
    ),
    "ESFP": (
        _area(
            id="esfp-list",
            name="Kun uchun uch vazifa",
            situation=("Agar kun tartibsiz o‘tsa va muhim ish qolsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Ertalab bugungi uchta ishni yozing. Eng muhimini birinchi qo‘ying.",
                    "5 daqiqa",
                    "Uchta ish kunni ko‘rinadigan qiladi.",
                ),
                (
                    "Birinchi ishning 15 daqiqalik bo‘lagini bajaring.",
                    "15 daqiqa",
                    "Eng muhim ish kundan oldinroq joy oladi.",
                ),
                (
                    "Ikkinchi ishning 15 daqiqalik bo‘lagini bajaring.",
                    "15 daqiqa",
                    "Ikkinchi ish ham o‘z navbatini oladi.",
                ),
                (
                    "Kechqurun qaysi ish joyida ekanini belgilang.",
                    "5 daqiqa",
                    "Kechki qarash ertangi ro‘yxatni yengil qiladi.",
                ),
                (
                    "Uchinchi ishning 15 daqiqalik bo‘lagini bajaring.",
                    "15 daqiqa",
                    "Uchinchi ish ham e’tiborsiz qolmaydi.",
                ),
                (
                    "Ertaga uchun bitta ishni oldindan yozing.",
                    "5 daqiqa",
                    "Ertangi kun bo‘sh ro‘yxat bilan boshlanmaydi.",
                ),
                (
                    "Keyingi ertalab yana uchta ish yozish vaqtini belgilang.",
                    "10 daqiqa",
                    "Ro‘yxat ertaga ham o‘z vaqtida chiqadi.",
                ),
            ],
        ),
        _area(
            id="esfp-pause",
            name="His-tuyg‘udan oldin tanaffus",
            situation=("Agar xafa bo‘lib tez javob yuborsangiz, quyidagi usulni sinab ko‘ring."),
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
                ("Xabarni yozing, lekin 10 daqiqa yubormang.", "10 daqiqa", "O‘n daqiqa xabarni buzmaydi."),
                (
                    "Qayta o‘qib, qattiq bitta so‘zni yumshating va shundan keyin yuboring.",
                    "10 daqiqa",
                    "Yumshoq so‘z ham ma’noni saqlashi mumkin.",
                ),
                (
                    "Telefonni qo‘yib, 15 daqiqa boshqa joyga chiqing yoki jim o‘tiring.",
                    "15 daqiqa",
                    "Tanaffus keyingi javobni sovitadi.",
                ),
                (
                    "Suhbat qizisa, «hozir gaplashmayman, keyinroq yozaman» deb ayting.",
                    "5 daqiqa",
                    "Vaqt so‘rash ham javob.",
                ),
                (
                    "Kerak bo‘lsa, keyin qisqa tushuntirish yuboring. Uzun bahs ochmang.",
                    "10 daqiqa",
                    "Qisqa xabar bahsni cho‘zmasligi mumkin.",
                ),
                (
                    "Muhim gapni yozish o‘rniga yuzma-yuz yoki qo‘ng‘iroq vaqtini belgilang.",
                    "10 daqiqa",
                    "Ovoz yozma gapdan yumshoqroq yetishi mumkin.",
                ),
                (
                    "Ertaga shoshilinch xabar bo‘lsa, avval qancha kutishingizni belgilang.",
                    "10 daqiqa",
                    "Kutish vaqti oldindan tayyor turadi.",
                ),
            ],
        ),
    ),
    "ESFJ": (
        _area(
            id="esfj-ask",
            name="Yordam so‘rash",
            situation=("Agar ko‘p ishni o‘zingiz olib, charchab qolsangiz, quyidagi usulni sinab ko‘ring."),
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
                (
                    "O‘zingiz olgan bitta ishni tanlang va kimga berish mumkinligini yozing.",
                    "10 daqiqa",
                    "Ish va odam oldindan juftlashadi.",
                ),
                (
                    "Shu odamdan bitta aniq yordam so‘rang.",
                    "10 daqiqa",
                    "Aniq so‘rov odamga yengilroq tushadi.",
                ),
                (
                    "Rad javob kelsa nima deysiz, bir jumla qilib oldindan yozing.",
                    "5 daqiqa",
                    "Rad javobi ham suhbatni uzmaydi.",
                ),
                (
                    "15 daqiqa o‘z ishingizni qiling va bu vaqtda boshqaning ishini olmang.",
                    "15 daqiqa",
                    "Bu vaqt sizning ishingizniki.",
                ),
                (
                    "Yordam bergan odamga nima uchun rahmat ekanini aniq ayting.",
                    "10 daqiqa",
                    "Aniq rahmat yordamni ko‘rinadigan qiladi.",
                ),
                (
                    "Katta ishni ikki qismga bo‘ling va bittasini boshqa odamga ayting.",
                    "15 daqiqa",
                    "Ikki qism bir odamga og‘irroq tushmaydi.",
                ),
                (
                    "Ertaga so‘ramoqchi bo‘lgan bitta yordamni oldindan yozing.",
                    "10 daqiqa",
                    "Ertangi so‘rov tayyor turadi.",
                ),
            ],
        ),
        _area(
            id="esfj-no",
            name="Muloyim rad etish",
            situation=("Agar hamma narsaga «ha» deb, keyin asabiylashsangiz, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta iltimosga «hozir qila olmayman, keyinroq gaplashamiz» deb yozing.",
                    "5 daqiqa",
                    "Qisqa rad ham muloyim javob.",
                ),
                (
                    "Yana bitta iltimosga shu jumlani yoki aniq vaqtni yozing.",
                    "5 daqiqa",
                    "Ikkinchi marta aytish osonroq bo‘lishi mumkin.",
                ),
                (
                    "O‘z ehtiyojingizni bir jumla qilib ayting.",
                    "10 daqiqa",
                    "Ehtiyojingiz ham suhbatning bir qismi.",
                ),
                (
                    "Rejaga o‘zingiz uchun 15 daqiqa yozing va shu vaqtni boshqaga bermang.",
                    "15 daqiqa",
                    "Bu vaqt sizniki.",
                ),
                (
                    "Og‘ir gapni shaxsingiz haqida emas, bitta ish haqida qilib qayta yozing.",
                    "10 daqiqa",
                    "Ish haqidagi gap odamga yengilroq yetadi.",
                ),
                (
                    "Yaqin odamga 15 daqiqa ichida bitta ochiq gap ayting.",
                    "15 daqiqa",
                    "Ochiq gap yaqinlikni saqlashi mumkin.",
                ),
                (
                    "Ertaga qo‘yib yubormoqchi bo‘lgan bitta chegarani oldindan yozing.",
                    "10 daqiqa",
                    "Ertangi javob tayyor turadi.",
                ),
            ],
        ),
    ),
    "ESTJ": (
        _area(
            id="estj-praise-first",
            name="Avval yaxshi tomonni aytish",
            situation=("Agar tez tuzatish boshqalarni ranjitsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Bitta odamga avval aniq yaxshi ishini ayting, keyin bitta taklif bering.",
                    "10 daqiqa",
                    "Avval yaxshi joy, keyin taklif eshitiladi.",
                ),
                (
                    "Bugun faqat bitta aniq yaxshi so‘z ayting. Tuzatish qo‘shmang.",
                    "5 daqiqa",
                    "Yaxshi so‘z o‘zi ham yetarli bo‘lishi mumkin.",
                ),
                ("Taklifni buyruq emas, savol qilib yozing.", "10 daqiqa", "Savol odamga tanlov qoldiradi."),
                (
                    "Bitta ishni boshqa odamga ayting: nima va qachon.",
                    "15 daqiqa",
                    "Aniq ish va muddat ikkalangizga ham yengil.",
                ),
                (
                    "O‘z xatongizni bitta jumla bilan ayting.",
                    "10 daqiqa",
                    "Qisqa tan olish ham ishonch berishi mumkin.",
                ),
                (
                    "Guruhdan keyingi qadam haqida fikr so‘rang va javobni eshiting.",
                    "15 daqiqa",
                    "Javob keyingi qadamni birga ochadi.",
                ),
                (
                    "Ertaga avval yaxshi so‘z aytmoqchi bo‘lgan odamni tanlang.",
                    "10 daqiqa",
                    "Ertangi gap oldindan joy topadi.",
                ),
            ],
        ),
        _area(
            id="estj-flex",
            name="Rejada istisno qo‘shish",
            situation=("Agar kutilmagan holat hammani stress qilsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Asosiy reja yoniga «agar o‘zgarsa» deb bitta muqobil qator yozing.",
                    "10 daqiqa",
                    "Muqobil qator reja siljisa tayyor turadi.",
                ),
                (
                    "Shu muqobilni bitta kichik ishda sinab ko‘ring.",
                    "15 daqiqa",
                    "Sinov asosiy rejani bekor qilmaydi.",
                ),
                ("Kim nima qilishini ikki qator qilib yozing.", "10 daqiqa", "Har kim o‘z qismini ko‘radi."),
                (
                    "15 daqiqa ichida shu reja haqida qisqa gaplashing.",
                    "15 daqiqa",
                    "Qisqa gap reja haqidagi taxminni kamaytiradi.",
                ),
                (
                    "Moslashgan odamga bitta aniq yaxshi so‘z ayting.",
                    "5 daqiqa",
                    "Yaxshi so‘z moslashuvni ko‘radi.",
                ),
                (
                    "Hozir kerak bo‘lmagan bitta qoidani shu haftaga chetga oling.",
                    "10 daqiqa",
                    "Vaqtincha chetga olingan qoida keyin qaytishi mumkin.",
                ),
                (
                    "Keyingi hafta uchun bitta zaxira rejasini yozing.",
                    "10 daqiqa",
                    "Yangi haftada ham nafas oladigan joy bor.",
                ),
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
                (
                    "Qolgan zerikarli bo‘lakni tanlang va 15 daqiqa faqat shuni qiling.",
                    "15 daqiqa",
                    "Qisqa vaqt zerikarli ishni cheklab turadi.",
                ),
                (
                    "Shu bo‘lakning keyingi qismini yana 15 daqiqa qiling.",
                    "15 daqiqa",
                    "Ikkinchi parcha kechagini davom ettiradi.",
                ),
                (
                    "Ish tugagan deb aytish uchun nima tayyor bo‘lishini bir jumla qilib yozing.",
                    "10 daqiqa",
                    "Tugash nuqtasi o‘zingizga tushunarli bo‘ladi.",
                ),
                (
                    "Yana 15 daqiqa shu ishda qoling. Boshqa ish ochmang.",
                    "15 daqiqa",
                    "Boshqa ish shu vaqt tugagach ham o‘z joyida turadi.",
                ),
                (
                    "Tugash jumlasiga qarab nima qolganini ayting va yozing.",
                    "10 daqiqa",
                    "Qolgan joy keyingi qisqa qadamga aylanadi.",
                ),
                ("Oxirgi kichik bo‘lakni yoping.", "15 daqiqa", "Ish ko‘rsatishga yaqinlashadi."),
                (
                    "Keyingi ish uchun tugash kunini yozing.",
                    "10 daqiqa",
                    "Yangi ish ham tugash kuni bilan boshlanadi.",
                ),
            ],
        ),
        _area(
            id="estp-wait-big",
            name="Yirik qarordan oldin kutish",
            situation=("Agar darhol harakat qilish keyin afsus keltirsa, quyidagi usulni sinab ko‘ring."),
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
                (
                    "Katta qarorni yozing va bugun amalga oshirmang.",
                    "10 daqiqa",
                    "Yozilgan qaror bugun ham sizniki, faqat kutadi.",
                ),
                (
                    "Nima foyda va nima xavf borligini ikki qator qilib yozing.",
                    "15 daqiqa",
                    "Foyda va xavf yonma-yon ko‘rinadi.",
                ),
                (
                    "Ishonchli bitta odamdan fikr so‘rang.",
                    "15 daqiqa",
                    "Boshqa fikr siznikini almashtirishi shart emas.",
                ),
                (
                    "Kecha yozganingizni qayta o‘qing va qarorni tasdiqlang yoki kechiktirib qo‘ying.",
                    "15 daqiqa",
                    "Qayta o‘qish shoshilishni pasaytirishi mumkin.",
                ),
                (
                    "To‘liq qaror o‘rniga bitta kichik sinov tanlang.",
                    "15 daqiqa",
                    "Kichik sinov katta qadamning o‘rnini bosadi.",
                ),
                (
                    "Shoshilinch bitta xarajatni bugun qilmang. Ertaga qayta qaraysiz deb yozing.",
                    "5 daqiqa",
                    "Ertangi qarash bugungi xarajatni sovitadi.",
                ),
                (
                    "Ertaga kutmoqchi bo‘lgan bitta qarorni va vaqtini yozing.",
                    "10 daqiqa",
                    "Kutish ertaga ham joy topadi.",
                ),
            ],
        ),
    ),
}
