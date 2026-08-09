# MBTI_test — to'liq SWOT tahlili va rivojlantirish takliflari

**Repozitoriy:** `github.com/Akbarali721/MBTI_test` · **Tahlil sanasi:** 2026-yil 6-avgust
**Hajmi:** 88 fayl, 3 ta commit · **Testlar:** 42 ta test, 7.8 soniyada muvaffaqiyatli o'tadi

---

## 0. Qisqacha xulosa

Bu — FastAPI asosidagi o'zbek tilidagi MBTI shaxsiyat testi. Veb-ilova, Telegram bot,
admin panel va premium to'lov oqimidan iborat. **Arxitektura kutilganidan ancha yaxshi:**
router → service → repository qatlamlari toza ajratilgan, SQLAlchemy 2.0 tipli modellar,
migratsiyalar dialektga moslashgan, 42 ta real test bor.

Ammo **mahsulot hozirgi holatida pul ishlab bera olmaydi va natijalari noto'g'ri**.
Uchta kritik nuqson bor va ularning har biri men tomonidan shaxsan kod ustida tekshirilgan:

| # | Muammo | Ta'siri |
|---|--------|---------|
| 1 | Javob ballari **teskari qo'yilgan** — har savolning 4 ta variantidan 2 tasi noto'g'ri o'lchovga hisoblanadi | Foydalanuvchilar **noto'g'ri MBTI tipini** oladi va o'sha noto'g'ri tip uchun pul to'laydi |
| 2 | Veb-to'lov oqimi bot bilan **umuman ulanmagan** | Pul to'lagan foydalanuvchi chekni yubora olmaydi — bot "so'rov topilmadi" deb javob beradi |
| 3 | Admin paroli **ochiq matnda**, standart qiymati `admin`/`admin`, `SECRET_KEY` esa `dev-secret-key` | To'lovlarni tasdiqlaydigan panelga istalgan odam kira oladi |

Bularga qo'shimcha: repozitoriyga **~32 MB begona hujjat** (eshik chizmalari PDF, xlsx,
Office lock fayli) kommit qilingan va ular `/static` orqali **internetdan ochiq yuklab olinadi**.

Yaxshi xabar: sanab o'tilgan muammolarning aksariyati kichik va aniq tuzatishlar.
Deep-link oqimi allaqachon yozilgan va testdan o'tgan — shunchaki UI'ga ulanmagan.

---

## 1. Loyiha tuzilishi

```
app/
├── main.py              FastAPI ilova, lifespan (create_all + seeding)
├── config.py            pydantic-settings, 14 ta sozlama
├── routers/             personality (test oqimi), admin (panel), relationship (bo'sh)
├── services/            personality_service, personality_scoring, premium_payment_service,
│                        admin_analytics_service
├── repositories/        personality_repository, payment_repository
├── personality/         session_binding, themes, payment_code
├── models/              PersonalityTestSession, Question, Option, Answer, ResultContent,
│                        PaymentRequest
├── seed/                24 ta o'zbekcha savol + 16 ta tip uchun natija matnlari
├── bot/                 aiogram 3 — deep-link, chek qabul qilish, admin tasdiqlash
├── templates/           Jinja2 — landing → instructions → question → loading → result
└── static/              CSS, JS, rasmlar (+ 32 MB begona fayl)
alembic/versions/        4 ta migratsiya
tests/                   42 ta test, 8 ta faylda
```

**Foydalanuvchi yo'li:** landing → jins tanlash → 24 ta savol (har biri alohida sahifa) →
loading → natija (bepul qism ochiq, 7 ta premium bo'lim yopiq) → to'lov modali →
Telegram bot orqali chek → admin tasdiqlaydi → premium ochiladi.

---

## 2. SWOT matritsasi

| | **Ijobiy** | **Salbiy** |
|---|---|---|
| **Ichki** | **S — Kuchli tomonlar**<br>· Toza 3 qatlamli arxitektura<br>· SQLAlchemy 2.0 + to'liq tiplashtirish<br>· 42 ta real test (smoke emas)<br>· Idempotent, dialektga moslashgan migratsiyalar<br>· Bot va veb bir xil service qatlamini ishlatadi<br>· Mobile-first CSS, a11y asoslari mavjud<br>· Sifatli o'zbekcha kontent + etik disclaimer | **W — Zaif tomonlar**<br>· Ball hisoblash teskari (kritik)<br>· Veb→bot to'lov oqimi uzilgan (kritik)<br>· Ochiq matnli parol, admin/admin standart (kritik)<br>· 32 MB begona fayl ommaviy ochiq<br>· 8.5 MB rasm mobil sahifalarda<br>· Startupda ma'lumot o'chiruvchi seeding<br>· N+1 so'rovlar (>10 000 so'rov/sahifa)<br>· Bot uchun 0% test qamrovi |
| **Tashqi** | **O — Imkoniyatlar**<br>· Payme/Click/Uzum integratsiyasi<br>· Rus tili — katta ikkilamchi bozor<br>· Ulashiladigan natijalar = viral o'sish<br>· Deep-link allaqachon tayyor, ulash kifoya<br>· CI ~7 soniya, deyarli bepul<br>· Postgres bir sozlama uzoqlikda | **T — Tahdidlar**<br>· Qo'lda chek tekshirish — firibgarlikka ochiq<br>· Bitta admin — bus factor 1<br>· Bot to'xtasa mijozlar pulini yo'qotadi<br>· Karta raqami git tarixida qolgan<br>· Pinlanmagan bog'liqliklar<br>· Birinchi Postgres deploy ishlamaydi (enum) |

---

## 3. S — Kuchli tomonlar

### Arxitektura
- **Toza qatlamlar.** Routerlar yupqa, biznes mantiq service'larda, SQL repository'larda.
  Domen yordamchilari `app/personality/` da ajratilgan. (Bitta istisno: `app/routers/admin.py:158`
  service'ni chetlab o'tib repository'ga to'g'ridan-to'g'ri murojaat qiladi.)
- **Bot va veb bitta service qatlamini bo'lishadi.** `app/bot/handlers.py` da biznes mantiq yo'q —
  hammasi `PremiumPaymentService` orqali. To'lov holati uchun yagona haqiqat manbai.
- **SQLAlchemy 2.0 zamonaviy uslubi.** `Mapped[]` / `mapped_column`, `DeclarativeBase`,
  eski `Query` API umuman ishlatilmagan. `X | None` uslubidagi tiplar deyarli hamma joyda.
- **Sof, freymvorksiz ball hisoblash.** `app/services/personality_scoring.py` faqat `dataclasses`
  import qiladi — DB ham, FastAPI ham yo'q. Shuning uchun uni sinash juda oson.
- **O'zgarmas natija obyektlari.** To'lov oqimi `frozen=True` dataclass'lar qaytaradi
  (`PremiumStartOutcome`, `ReceiptOutcome`, `ModerationOutcome`).

### Ma'lumotlar qatlami
- **Yaxshi cheklovlar.** Token unique+indeksli; javoblarda `(session_id, question_id)` bo'yicha
  kompozit UNIQUE; FK'larda `ondelete=CASCADE`; ORM tomonda `cascade="all, delete-orphan"`.
- **Indekslar to'g'ri joyda.** Aynan `WHERE` da ishlatiladigan ustunlarda: token, session_id,
  telegram_user_id, status.
- **Vaqt zonasi intizomi.** Barcha `DateTime(timezone=True)`, barcha vaqt belgilari
  `datetime.now(timezone.utc)` bilan.
- **Migratsiyalar himoyalangan.** 002–004 har o'zgarishni `_has_column`/`_has_table` bilan
  tekshiradi va SQLite/PostgreSQL uchun alohida tarmoqlanadi (`ALTER TYPE ... ADD VALUE IF NOT EXISTS`,
  `batch_alter_table`). Kichik loyiha uchun g'ayrioddiy puxta yozilgan.
- **BigInteger Telegram ID'lari** — Telegram ID'lari int32 dan katta, bu to'g'ri hisobga olingan.

### Xavfsizlik (ijobiy tomonlari)
- **Jinja2 avtoescaping to'liq saqlangan** — butun repoda bironta `|safe`, `Markup()` yoki
  `autoescape` override yo'q.
- **Barcha SQL parametrlashtirilgan** — `text()` import umuman yo'q, hamma joyda `select()`.
- **UUID4 tokenlar** (122 bit entropiya) + natija sahifalarida egalik tekshiruvi.
- **Bot admin avtorizatsiyasi fail-closed** — `ADMIN_TELEGRAM_ID` sozlanmagan bo'lsa,
  moderatsiya **rad etiladi** (ochilib ketmaydi).
- **Deep-link payload qat'iy validatsiya qilinadi** — prefiks, uzunlik ≤64, `isalnum()`.
- **Javob variantining savolga tegishliligi tekshiriladi** (`personality_service.py:77-85`) —
  aks holda foydalanuvchi begona `option_id` yuborib, o'ziga kerakli tipni "tanlab" olishi mumkin edi.

### Frontend va kontent
- **Haqiqiy mobile-first CSS.** 360–430px uchun mo'ljallangan, `clamp()` bilan suyuq tipografika,
  `env(safe-area-inset-bottom)`, 6 ta breakpoint.
- **A11y asoslari bor.** `lang="uz"`, `role="radiogroup"`, `role="progressbar"` + `aria-valuenow`,
  `role="alert"`, `role="status"`, dekorativ SVG'larda `aria-hidden`.
- **Server tomonda boshqariladigan oqim.** POST-redirect-GET, "Orqaga" tugmasi oldingi javobni
  belgilangan holda qaytaradi, tashlab ketilgan sessiya to'g'ri savoldan davom etadi.
- **Jinsga qarab mavzulash** server tomonda `<body>` klassiga yoziladi — JS'siz ham saqlanadi.
- **Sifatli o'zbekcha matn.** To'g'ri tipografik apostroflar (o', to'g'ri), landing'dagi
  "24 ta savol" da'vosi haqiqatga mos, natija sahifasida halol disclaimer bor.

### Testlar
- **42 ta test, haqiqiy assertion'lar bilan.** To'liq 24 savollik oqim HTTP orqali o'tkaziladi,
  yashirin form maydonlari HTML'dan parse qilinadi, redirect manzillari aniq tekshiriladi.
- **Regressiya testlari haqiqiy baglar uchun yozilgan** — `test_static_urls_https_safe.py`
  aynan `2e5b1fb` va `ea0df58` commit'laridagi mixed-content bagiga mos.
- **Algoritm testlari** — 16 ta tipning hammasi erishiluvchan ekani isbotlangan, teng ball
  holatidagi tie-break tekshirilgan.
- **Test izolyatsiyasi toza** — har test uchun yangi in-memory SQLite + `dependency_overrides`.

---

## 4. W — Zaif tomonlar

### 🔴 KRITIK

#### W1. Javob ballari teskari qo'yilgan — natijalar noto'g'ri
`app/seed/personality_placeholders.py:31-36`

Har savolning 4 ta varianti **semantik gradient** bo'yicha yozilgan: birinchi ikkitasi bir qutb,
keyingi ikkitasi ikkinchi qutb. Masalan 1-savol (EI):

| # | Variant matni | Bo'lishi kerak | Kod nima beradi |
|---|---|---|---|
| 1 | "Do'stlaringiz bilan vaqt o'tkazish" | E | E ✅ |
| 2 | "Yaqinlar bilan uchrashish" | E | **I** ❌ |
| 3 | "Yolg'iz yurish yoki kitob o'qish" | I | **E** ❌ |
| 4 | "Hech kim bezovta qilmasin, tinch joyda bo'lish" | I | I ✅ |

Kodda mapping almashib ketgan: `[("e","i"), ("i","e"), ("e","i"), ("i","e")]` —
ya'ni `[E, I, E, I]`. To'g'risi `[("e","i"), ("e","i"), ("i","e"), ("i","e")]` — ya'ni `[E, E, I, I]`.

**Bu barcha 24 ta savolga, barcha 4 ta o'lchovga taalluqli.** O'rtadagi (2- va 3-) variantlarni
tanlagan har bir foydalanuvchi teskari ball oladi. Mahsulot pullik bo'lgani uchun bu shunchaki
bag emas — mijoz o'ziga tegishli bo'lmagan tip uchun pul to'laydi.

**Tuzatish:** mapping'ni gradient tartibiga keltirish (3 qator), so'ng mavjud sessiyalar uchun
ballarni qayta hisoblash.

#### W2. Veb-to'lov oqimi bot bilan ulanmagan — chek hech qachon topilmaydi
`app/services/premium_payment_service.py:59-63, 291-298` · `app/routers/personality.py:331-344`

Natija sahifasidagi "Chekni Telegram orqali yuborish" tugmasi:
1. `GET /result/{token}/support-bot` ga boradi;
2. `begin_web_manual_payment()` **`telegram_user_id=0`** bilan `PaymentRequest` yaratadi
   (veb sessiyasida Telegram identifikatori yo'q);
3. foydalanuvchi **bo'sh** `https://t.me/<bot>` havolasiga yo'naltiriladi — `?start=premium_<token>`
   payload'i **yo'q** (butun repoda `start=premium_` qatori topilmadi).

Natijada:
- Bot faqat `CommandStart(deep_link=True)` ni tinglaydi → oddiy "Start" bosilganda **bot jim turadi**;
- Foydalanuvchi chek rasmini yuborsa, `attach_receipt()` uni haqiqiy `telegram_user_id` bo'yicha
  qidiradi, lekin bazadagi yozuvda `0` turibdi → **"Faol premium so'rov topilmadi"**;
- To'lov modalidagi "Botga chek rasmi va **test kodini** yuboring" ko'rsatmasi ham ishlamaydi —
  botda **matnli xabar handleri umuman yo'q**.

Eng achinarlisi: deep-link oqimi (FSM, avtomatik moslashtirish, adminga inline tugmalar bilan
xabar) **to'liq yozilgan va testdan o'tgan** — shunchaki UI'ga ulanmagan. `bot_username` sozlamasi
`app/config.py:13` da bor, lekin hech qayerda ishlatilmaydi.

**Tuzatish:** tugmani `https://t.me/{bot_username}?start=premium_{token}` qilib render qilish.

#### W3. Admin autentifikatsiyasi — ochiq matnli parol va standart qiymatlar
`app/dependencies.py:20-21` · `app/config.py:8-10` · `.env.example:2-4`

```python
return username == settings.admin_username and password == settings.admin_password
```

- Parol **hashlanmagan**, `secrets.compare_digest` ishlatilmagan (timing hujumiga ochiq);
- Kod standartlari: `admin` / `admin`, `secret_key = "dev-secret-key"`;
- `.env.example` ham xuddi shu `ADMIN_PASSWORD=admin` ni tarqatadi;
- **Hech narsa** standart qiymatlar bilan ishga tushishga to'sqinlik qilmaydi.

`SECRET_KEY` standart qolsa, sessiya cookie'si **imzolanadigan, lekin shifrlanmaydigan**
bo'lgani uchun tajovuzkor `admin_authenticated=True` cookie'sini **oflayn yasab olishi** mumkin —
parolni bilmasdan. Bu panel esa to'lovlarni tasdiqlaydi.

Qo'shimcha: login uchun **rate limiting yo'q** (butun repoda `slowapi`/`limiter` topilmadi).

#### W4. `/static` orqali begona hujjatlar ommaviy ochiq
`app/static/images/personality/gender/`

| Fayl | Hajmi |
|---|---|
| `click_telegram_uz.doc` | 13.9 MB |
| `Door-rolling shutter shop drawings 18052026.pdf` | 12.1 MB |
| `Door Details Sheet.xlsx` | 28 KB |
| `~$Door Details Sheet.xlsx` (Office lock fayli) | 165 B |

To'rttalasi ham git'da kuzatilmoqda va `app/main.py:34` dagi `StaticFiles` mount orqali
**autentifikatsiyasiz yuklab olinadi**. Lock fayli oxirgi tahrirlovchining Windows foydalanuvchi
nomini (`admin`) ichida saqlaydi. Bu eshik-jalyuzi biznesiga oid hujjatlar — MBTI testiga
hech qanday aloqasi yo'q. Bundan tashqari `app/static/images/personalty/` (imlo xatosi bilan)
4.7 MB va static ildizida 1.4 MB `ChatGPT Image ... .png` — ikkalasi ham hech qayerda ishlatilmaydi.

### 🟠 YUQORI

#### W5. Startupda ma'lumot o'chiruvchi seeding
`app/main.py:15-24` · `app/seed/personality_placeholders.py:42-59`

Har ishga tushishda `Base.metadata.create_all` + seeding ishlaydi. `_is_placeholder_data()`
faqat **birinchi** aktiv savolning matnida `"[Placeholder]"` yoki `"placeholder javob"` bor-yo'qligini
tekshiradi. Topilsa, `_clear_questions()` **barcha `PersonalityAnswer`, `PersonalityOption` va
`PersonalityQuestion` yozuvlarini o'chiradi**. Natija matnlari uchun tekshiruv yanada kengroq:
birinchi qatorda `"placeholder"` so'zi uchrasa, 16 ta tipning hammasi qayta yoziladi.

Ya'ni kontentga qilingan **bitta tahrir** keyingi restartda barcha javoblar tarixini
qaytarib bo'lmaydigan tarzda o'chirishi mumkin.

#### W6. N+1 so'rovlar bo'roni
`app/personality/payment_code.py:9-20`

`payment_code_for_session()` tokenning noyob prefiksini topish uchun **har uzunlik uchun bitta
`COUNT ... LIKE` so'rovi** yuboradi — token 32 belgi, sikl 8 dan boshlanadi, ya'ni sessiyaga
**25 tagacha so'rov**. Bu funksiya:
- admin sessiyalar sahifasida **har qator uchun** chaqiriladi (limit 500) → **>10 000 so'rov/sahifa**;
- **har bir foydalanuvchining natija sahifasida** ham chaqiriladi (`app/routers/personality.py:304`).

Boshqa N+1 nuqtalari: `recalculate_and_complete_session` har javob uchun alohida `db.get(Option)`
(24 ta ortiqcha so'rov), `count_active_questions` `SELECT COUNT(*)` o'rniga hamma qatorni yuklab
`len()` oladi — va u **har sessiya yaratilganda** ishlaydi.

#### W7. Mobil sahifalarda 8.5 MB rasm
Barcha 4 ta ishlatiladigan PNG **1536×1024** o'lchamda:

| Fayl | Hajmi | Ko'rsatiladigan o'lcham |
|---|---|---|
| `personality-logo.png` | 2.19 MB | 40–52 px |
| `personality-hero.png` | 2.08 MB | 110–150 px |
| `gender/female.png` | 2.14 MB | 76–96 px |
| `gender/male.png` | 2.10 MB | 76–96 px |

Logo **har sahifada** yuklanadi (bitta test seansida ~27 marta). Instructions sahifasi
~6.4 MB rasm tortadi. O'zbekistonning mobil internet sharoitida bu to'g'ridan-to'g'ri
konversiyani yo'qotadi. Rasmlar ichida C2PA/JUMBF metama'lumotlari ham bor (AI generatsiya izlari).

#### W8. Admin himoyasi 8 marta nusxalangan, `require_admin` esa o'lik kod
`app/routers/admin.py:13-16` · `app/dependencies.py:12-17`

Har admin handler o'zining birinchi qatorida `_admin_redirect(request)` chaqiradi — 8 marta
takrorlangan. Ayni paytda `app/dependencies.py` da **to'g'ri yozilgan `require_admin` dependency
mavjud, lekin hech qayerda ishlatilmaydi**. Yangi endpoint qo'shgan dasturchi ikki qatorni
unutса, u **jimgina himoyasiz** qoladi va buni **hech qanday test tutmaydi**
(autentifikatsiyasiz murojaat uchun negativ test yo'q).

#### W9. JavaScript'siz oqim to'liq to'xtaydi
Yuborish tugmalari HTML'da `disabled` bilan render qilinadi va faqat JS ularni yoqadi
(`instructions.html:55`, `question.html:44-49`). Radio'larda `required` yo'q. Loading sahifasi
natijaga **faqat** `setTimeout` orqali o'tadi — `<noscript>` ham, `meta refresh` ham yo'q.

#### W10. Klaviatura fokusi ko'rinmaydi
Jins va savol variantlari `clip` usuli bilan yashirilgan radio'lar, ammo ular uchun
`:focus-visible` qoidasi **yozilmagan** (faqat o'lik `appearance` sahifasi uchun bor).
Klaviatura yoki skrinrider bilan ishlaydigan foydalanuvchi qayerdaligini ko'rmaydi.

#### W11. Bot qatlami uchun 0% test qamrovi
`app/bot/handlers.py` — 265 qator pul bilan bog'liq mantiq (deep-link, chek qabul qilish,
admin tasdiqlash, avtorizatsiya) — va `tests/` da `aiogram` so'zi umuman uchramaydi.
`/admin/premium-requests/{id}/approve` va `/reject` endpoint'lari ham HTTP darajasida sinalmagan.

### 🟡 O'RTA

- **Tranzaksiya chegaralari tarqoq.** Repository'lar deyarli har metodda `commit()` qiladi;
  bitta javob yuborish **3 ta alohida commit** hosil qiladi. `get_db` xatolikda `rollback` qilmaydi.
- **Enum nomlari migratsiyalarga mos emas.** SQLAlchemy `values_callable`siz enum **nomlarini**
  (`"VISITED"`) yozadi, migratsiya esa PG tipini **qiymatlar** (`"visited"`) bilan yaratadi —
  ustiga 001 da `visited` umuman yo'q. **Alembic bilan qurilgan PostgreSQL bazasiga birinchi
  sessiya yozuvi xato beradi.** SQLite'da enum VARCHAR'ga aylangani uchun testlar buni tutmaydi.
- **001 va 004 migratsiyalari SQLite'da umuman ishlamaydi** — `sa.text('now()')` SQLite'da yo'q,
  holbuki standart `DATABASE_URL` aynan SQLite.
- **`create_all` va Alembic bir-biriga zid.** `create_all` bilan qurilgan bazada `alembic_version`
  yo'q, 001 esa himoyasiz `create_table` qiladi → `alembic upgrade head` **xato beradi**.
- **SQLite'da FK'lar umuman tekshirilmaydi** — `PRAGMA foreign_keys=ON` hech qayerda yo'q.
- **Sessiya tokenlari INFO logga yoziladi** (`app/routers/personality.py:221-227`) — token bu
  bearer-imkoniyat, log fayliga kirgan kishi uni qayta ishlatishi mumkin.
- **`GET /test/{token}` va `POST .../answer` da egalik tekshiruvi yo'q** — natija sahifalarida bor,
  bu ikkitasida yo'q. Tokenni bilgan kishi begona testni ko'rishi va javoblarini **o'zgartirishi** mumkin.
- **Poyga holatlari.** `with_for_update()` hech qayerda ishlatilmaydi; veb-admin va bot bir vaqtda
  tasdiqlash/rad etishni bajarsa, oxirgi yozuvchi g'olib bo'ladi va `payment=rejected` +
  `is_premium=True` kabi nomuvofiq holat yuzaga kelishi mumkin.
- **Veb-admin chekni ko'rmasdan tasdiqlaydi.** Panelda faqat "Telegram'da" yozuvi chiqadi,
  rasmni ko'rish imkoni yo'q; ustiga tasdiqlash tugmasi `pending` (chek umuman yuborilmagan)
  holatida ham ko'rinadi.
- **`_handle_receipt` FSM holatini e'tiborsiz qoldiradi.** Handler'lar `F.photo`/`F.document`
  ga bog'langan, `StateFilter` yo'q — **botga yuborilgan istalgan rasm** chek deb qabul qilinadi.
  `state.clear()` hech qachon chaqirilmaydi.
- **Deep-link egalikni qayta biriktiradi.** Havola tarqalsa, uni ochgan istalgan kishi to'lovni
  o'z Telegram ID'siga o'tkazib yuboradi va asl foydalanuvchining cheki mos kelmay qoladi.
- **Bot javobi `send_message` dan keyin beriladi.** Foydalanuvchi botni bloklagan bo'lsa,
  exception chiqadi, `query.answer()` bajarilmaydi — admin tugmasi "aylanaveradi", klaviatura tozalanmaydi.
- **CSRF himoyasi umuman yo'q.** (SameSite=Lax klassik POST hujumini to'sadi, lekin
  `GET /admin/logout` va `GET /result/{token}/support-bot` — ikkalasi ham **holatni o'zgartiradi** —
  Lax bilan ham cross-site navigatsiyada ishlaydi.)
- **`ProxyHeadersMiddleware(trusted_hosts="*")`** — istalgan mijoz `X-Forwarded-*` sarlavhalarini
  soxtalashtira oladi.
- **Xavfsizlik sarlavhalari yo'q** (CSP, X-Frame-Options, HSTS, nosniff), Bootstrap va shriftlar
  CDN'dan SRI'siz yuklanadi.
- **Anonim sessiya qatorlari cheksiz o'sadi.** Cookie'siz har `GET /personality` yangi qator
  yaratadi — kraulerlar, health-check'lar, prefetch. Tozalash mexanizmi yo'q.
- **Chek faqat Telegram `file_id` sifatida saqlanadi** — bot tokeni almashtirilsa, butun
  to'lov tarixi kirish imkonsiz bo'lib qoladi.
- **Rad etilgan to'lovni qayta faollashtirish audit izini o'chiradi** — eski chek maydonlari
  `NULL` ga tushiriladi, nizoli holatda dalil qolmaydi.
- **Natija sahifasi noto'g'ri xabar beradi** — chek yuborilmagan bo'lsa ham
  "Chekingiz administratorga yuborildi" deb yozadi.
- **`.env.example` da haqiqiy karta raqami** (Luhn bo'yicha to'g'ri, Uzcard `9860` BIN)
  va karta egasi nomi — **uchala commit'da ham** bor, ya'ni git tarixida qolgan.

### 🟢 PAST

- **Katta hajmdagi o'lik kod:** `require_admin`, `APPEARANCE_OPTIONS` + `_appearance_page_context`
  (`appearance.html` hech qachon render qilinmaydi), `touch_session_activity`, `get_question_by_order`,
  `PersonalityRepository.list_sessions`, `build_admin_telegram_receipt_url`, `PAYMENT_STATUS_CANCELLED`,
  `settings.debug` (o'qilmaydi), `settings.bot_username`, `partials/theme_illustration.html`,
  `admin/personality_sessions.html`, `personality.css` ning katta qismi, `appearance.js`.
- **Uchta mavjud bo'lmagan SVG'ga havola** — `THEME_CONFIG` va `APPEARANCE_OPTIONS`
  `personality_male.svg`, `personality_female.svg`, `personality_landing_discovery.svg` ga
  ishora qiladi; diskda faqat `logo_mark.svg` bor.
- **Natija sahifasi bitta CSS'ni ikki marta yuklaydi** — `base.html` da `?v=20`, `result.html` da `?v=22`.
- **Kesh-versiyalar testlarga qattiq yozilgan** (`?v=12`, `?v=20`) — har CSS o'zgarishi testni buzadi.
- **Production kodida `assert`** — `python -O` bilan ular olib tashlanadi
  (`personality.py:120`, `session_binding.py:63`, `bot/handlers.py:88`).
- **`filter` built-in nomi parametr sifatida** (`admin.py:81, 153`), funksiya ichida import'lar.
- **`telegram_user_id` query parametri validatsiyasiz** — `str | None` deb tiplangan, lekin
  `BigInteger` ustunga yoziladi; istalgan tashrifchi begona Telegram ID'ni "da'vo qilishi" mumkin.
- **`begin_web_manual_payment` `telegram_user_id=0` sentinel qiymatini yozadi** NOT NULL ustunga.
- **`amount` standart qiymati 9999**, `settings.premium_price` esa 9990.
- **Kod takrorlanishi:** `_format_price` ≡ `format_price_uzs`, UTC yarim tunini hisoblash
  3 marta, `_admin_redirect` ≡ `require_admin`, 3 ta JS fayl bir xil "radio tanlansa tugmani yoq"
  mantiqini takrorlaydi, test helper'lari 4 ta faylda nusxalangan.
- **Kontrast WCAG AA dan past** — oltin rang `#c98a22` krem fonda ~2.9:1 (kerak: 4.5:1),
  ayol mavzusidagi pushti `#d48498` ~2.7:1.
- **SEO/meta umuman yo'q** — description, Open Graph, canonical, favicon, theme-color, robots.
- **i18n qatlami yo'q** — matnlar template, inline JS, tashqi JS va Python kodida tarqoq;
  admin panelida esa inglizcha status yorliqlari (`Pending`, `Approved`) o'zbekcha UI ichida.
- **`conftest.py:3` `os.environ.setdefault("DATABASE_URL", ...)`** ishlatadi — serverda
  `DATABASE_URL` allaqachon o'rnatilgan bo'lsa, testlar **haqiqiy bazaga** ulanishi mumkin.
- **README, CI, Dockerfile, LICENSE, linter konfiguratsiyasi — hech biri yo'q.**
  Butun repoda yagona ishga tushirish ko'rsatmasi — `main.py` dagi bir qatorlik docstring.
- **Bog'liqliklar pinlanmagan** — 13 ta paket faqat `>=` bilan, lock fayl yo'q,
  `pytest` va `httpx` production ro'yxatida.
- **Health-check endpoint yo'q**, butun veb-ilovada **bitta** `logger.info` chaqiruvi bor.
- **`compatible_people` kontenti 16 ta tip uchun yozilgan, lekin natija sahifasida
  ko'rsatilmaydi** — pullik kontent bazada yotibdi, mijoz uni ko'rmaydi.
- **`/relationship` routeri — bo'sh placeholder** (13 qator HTML).

---

## 5. O — Imkoniyatlar

1. **Deep-link'ni ulash — bir qatorlik o'zgarish, butun to'lov oqimini tiklaydi.**
   Bot tomondagi mantiq allaqachon yozilgan va testdan o'tgan.
2. **O'zbek to'lov agregatorlari (Payme, Click, Uzum).** Merchant API + server callback
   qo'lda tekshirishni, admin darvozasini va firibgarlik yuzasini bir yo'la olib tashlaydi.
   `PaymentRequest` jadvali va status lifecycle allaqachon shu uchun mos.
3. **Rus tili** — O'zbekistondagi juda katta ikkilamchi auditoriya, dizaynni o'zgartirmasdan qo'shiladi.
4. **Ulashiladigan natijalar = viral o'sish kanali.** MBTI natijalari tabiatan ulashiladi.
   Har tip uchun Open Graph rasmi + anonim ommaviy havola har tugatilgan testni
   yangi mijoz manbaiga aylantiradi.
5. **CI deyarli bepul** — 42 test 7 soniyada, tashqi servis kerak emas. ~20 qatorlik
   GitHub Actions fayli barcha keyingi regressiyalarni to'sadi.
6. **PostgreSQL bir sozlama uzoqlikda** — `psycopg2-binary` allaqachon bog'liqliklarda,
   `alembic/env.py` `settings.database_url` ni to'g'ri o'qiydi. Enum muammosi hal bo'lsa, tayyor.
7. **Imzolangan natija havolalari** — `itsdangerous` allaqachon bog'liqliklarda; qisqa muddatli
   imzolangan token pullik mijozga **istalgan qurilmadan** natijasini ochish imkonini beradi.
8. **Bot'ni webhook sifatida FastAPI ichiga ko'chirish** — alohida polling jarayoni,
   uning jimgina o'lib qolishi va `getUpdates` konflikti muammolarini yo'q qiladi.
9. **Konversiya analitikasi allaqachon yig'ilayotgan ma'lumotlardan** —
   `premium_requested_at` / `premium_approved_at` + to'lov statuslari bilan
   to'liq voronka metrikasi sxemani o'zgartirmasdan quriladi.
10. **Rasm optimizatsiyasi** — 8.5 MB → <300 KB, faqat o'lchamni to'g'rilash va WebP'ga o'tkazish bilan.

---

## 6. T — Tahdidlar

| Tahdid | Izoh |
|---|---|
| **Qo'lda chek tekshirish firibgarlikka ochiq** | Tasdiqlash odamning rasmga qarashiga asoslangan; summa tekshirilmaydi, bank bilan solishtirilmaydi, soxta skrinshot arzon |
| **Bitta admin — bus factor 1** | `ADMIN_TELEGRAM_ID` bitta ixtiyoriy son; sozlanmagan bo'lsa xabarlar **jimgina** yuborilmaydi. O'sha odam yo'q bo'lsa, Telegram moderatsiyasi to'liq to'xtaydi |
| **Bot to'xtasa mijozlar strand bo'ladi** | Bot alohida polling jarayoni; supervisor, healthcheck, deploy konfiguratsiyasi yo'q. U o'chganda pul to'lagan mijoz chekni yubora olmaydi va **hech qanday xabar olmaydi** |
| **Karta raqami git tarixida** | Uchala commit'da; repo ommaviy bo'lsa yoki ulashilsa, fayl keyin tahrirlansa ham tiklanadi |
| **Standart parollar pul yo'lini qo'riqlaydi** | `admin`/`admin` + `dev-secret-key` + rate limiting yo'q + negativ test yo'q |
| **Birinchi Postgres deploy ishlamaydi** | Enum nomlari/qiymatlari mos emas; SQLite'da testlar buni **hech qachon** tutmaydi |
| **Pinlanmagan bog'liqliklar + CI yo'q** | Keyingi `pip install` buzuvchi major versiyani tortishi mumkin va buni hech kim sezmaydi. Test chiqishida allaqachon `StarletteDeprecationWarning` ko'rinmoqda |
| **SQLite + ikkita yozuvchi jarayon** | Standart `DATABASE_URL` SQLite, veb va bot alohida jarayonlar — `database is locked` xatolari, WAL/busy_timeout sozlanmagan |
| **Ikki marta polling** | Deploy paytida ikkita nusxa ishlasa, Telegram `getUpdates` konflikti — o'sha oynadagi cheklar **yo'qoladi** |
| **Sahifa og'irligidan voronka yo'qotishi** | Landing'da ~2 MB LCP, instructions'da ~6.4 MB — 3G'da 10+ soniya. Monitoring yo'q, ya'ni buni hech kim ko'rmaydi |
| **Ma'lumot sizishi hozir faol** | Eshik chizmalari va .doc fayli **ayni damda** production'dan yuklab olinadi |

---

## 7. Ustuvorlik bo'yicha yo'l xaritasi

### P0 — Darhol (mahsulot hozir buzuq)

| # | Vazifa | Hajmi | Fayl |
|---|---|---|---|
| 1 | Ball mapping'ini gradient tartibiga keltirish + mavjud natijalarni qayta hisoblash | 3 qator | `seed/personality_placeholders.py:31-36` |
| 2 | To'lov tugmasini `?start=premium_{token}` deep-link'iga o'tkazish | kichik | `templates/personality/result.html`, `routers/personality.py:331` |
| 3 | Botga oddiy `/start`, matn handleri (test kodi bo'yicha) va fallback javob qo'shish | o'rta | `bot/handlers.py` |
| 4 | Parolni hashlash (bcrypt/argon2), standart `admin`/`admin` ni olib tashlash | kichik | `dependencies.py:20`, `config.py:9-10` |
| 5 | `SECRET_KEY` ni majburiy qilish + placeholder qiymatlarda ishga tushmaslik | kichik | `config.py:8` |
| 6 | `require_admin` ni router darajasidagi dependency sifatida ulash | kichik | `routers/admin.py:19` |
| 7 | Begona hujjatlarni o'chirish + git tarixini qayta yozish (`git filter-repo`) | o'rta | `static/images/personality/gender/` |
| 8 | `.env.example` dagi karta raqamini placeholder bilan almashtirish | kichik | `.env.example:10-11` |
| 9 | `create_all` + startup seeding'ni olib tashlash, Alembic'ni yagona manba qilish | o'rta | `main.py:15-24` |
| 10 | Bog'liqliklarni pinlash, dev bog'liqliklarini ajratish | kichik | `requirements.txt` |

### P1 — Yaqin muddatda

- Rasm optimizatsiyasi (8.5 MB → <300 KB) + `width`/`height` atributlari
- `GET /test/{token}` va `POST .../answer` ga egalik tekshiruvini qo'shish
- Loglardan sessiya tokenini olib tashlash
- N+1 ni yo'q qilish: sessiyaga doimiy `payment_code` ustuni + ball hisoblashni bitta SQL'ga
- Klaviatura fokusini tiklash (`:focus-visible`)
- JS'siz oqimni ishlashga keltirish (`disabled` ni olib tashlash, `required`, `<noscript>`)
- Enum'larga `values_callable` qo'shish (Postgres uchun) + tuzatuvchi migratsiya
- Bot handler'lariga xato ishlovi + `dp.errors` dispatcher handleri
- Bot testlari + admin auth uchun negativ testlar
- GitHub Actions CI + README
- HTML xato sahifalari (404/500) + production `assert` larni olib tashlash
- To'lov mutatsiyalarini `with_for_update()` bilan seriyalash + partial unique indeks

### P2 — Keyinroq

- Tranzaksiyalarni bitta unit-of-work ga yig'ish
- O'lik kodni tozalash (~500+ qator)
- Xavfsizlik sarlavhalari middleware + CDN'ni self-host qilish
- Dockerfile + docker-compose (web + bot + postgres)
- `/health` endpoint + Sentry + so'rov loglash
- i18n qatlami (jinja2 i18n + babel), keyin rus tili
- Ruff + mypy + pre-commit
- SQLite uchun `PRAGMA foreign_keys=ON`, WAL, busy_timeout
- Chek tarixini saqlash (rad etilganda o'chirmaslik)
- Admin panelida chek rasmini ko'rsatish (Telegram `getFile` proxy)

---

## 8. Kiritish mumkin bo'lgan qo'shimchalar

Bu bo'lim — kod tuzatishlari emas, **mahsulotga qo'shsa bo'ladigan yangi imkoniyatlar**.

### 8.1 Daromadni oshiradiganlar

**Avtomatik to'lov (Payme / Click / Uzum).** Hozirgi qo'lda oqim: mijoz karta raqamiga
pul o'tkazadi → chek rasmini botga yuboradi → admin qaraydi → tasdiqlaydi. Bu sekin (mijoz
kutadi), firibgarlikka ochiq (soxta skrinshot) va masshtablanmaydi (bitta odam darvoza).
Merchant API server callback'i bilan bularning hammasi yo'qoladi va `PaymentRequest` jadvaliga
shunchaki `provider_transaction_id` ustuni qo'shiladi.

**Premium teaser'lar.** Hozir 7 ta yopiq bo'lim **bir xil** placeholder jumlani ko'rsatadi.
Har bo'limning birinchi jumlasini ko'rsatib, qolganini blur qilish — konversiyani sezilarli
oshiradigan klassik usul.

**Ko'rsatilmayotgan kontentni ochish.** `compatible_people` maydoni 16 ta tip uchun to'liq
yozilgan, bazada saqlanadi, lekin natija sahifasida **umuman render qilinmaydi** —
tayyor pullik kontent behuda yotibdi.

**Narx darajalari.** Hozir yagona narx (9 990 so'm). Masalan: bazaviy premium /
"premium + PDF hisobot" / "premium + juftlik tahlili" kabi 2-3 daraja.

**Referal tizimi.** Sessiyada `source` ustuni allaqachon bor va indekslangan — referal
kodlarini o'sha maydonga yozib, "3 ta do'stingiz test topshirsa, premium bepul" mexanikasini
sxemani o'zgartirmasdan qurish mumkin.

### 8.2 O'sish kanallari

**Ulashiladigan natija.** Hozir natija havolasi cookie'ga bog'langan — begona odam uni ochsa,
landing'ga uloqtiriladi va **hech qanday preview ham ko'rmaydi**. Har MBTI tipi uchun
Open Graph rasmi + anonim ommaviy sahifa (`/r/<qisqa-kod>`) har tugatilgan testni
Telegram/Instagram'da tarqaladigan reklamaga aylantiradi.

**Rus tili.** O'zbekistondagi katta auditoriya. i18n qatlami qo'yilgach — bu kontent
tarjimasi masalasi, kod masalasi emas.

**Natijani qayta olish.** Mijoz cookie'sini yo'qotsa (boshqa brauzer, telefon almashtirish),
**pullik natijasiga kirish imkonini butunlay yo'qotadi**. Yomoni: natija sahifasidagi
"Bosh sahifaga qaytish" tugmasining o'zi cookie'ni almashtirib yuboradi. Telegram orqali
imzolangan havola yuborish (`itsdangerous` allaqachon bor) buni hal qiladi.

**Test tarixi va dinamika.** Foydalanuvchi bir necha marta test topshirsa, natijalarning
vaqt bo'yicha o'zgarishini ko'rsatish — qaytib kelish sababi.

### 8.3 Mahsulot imkoniyatlari

**Juftlik / munosabat testi.** `/relationship` routeri allaqachon mavjud, lekin bo'sh
placeholder. Ikki kishining MBTI tipini solishtirish — bu mahsulotning tabiiy davomi va
alohida pullik xizmat bo'lishi mumkin.

**PDF hisobot.** Premium natijani chiroyli PDF sifatida yuklab olish yoki Telegram orqali
yuborish — idrok etilgan qiymatni oshiradi va ulashiladi.

**Jamoa / HR rejimi.** Bir nechta xodimning tipini bitta panelda ko'rish, jamoa tarkibi
tahlili — B2B yo'nalishi. Mavjud admin panel buning uchun asos bo'la oladi.

**Savol banki va A/B test.** Savollar bazada saqlanadi (`is_active`, `order_number`) —
turli savol to'plamlarini sinash uchun infratuzilma allaqachon tayyor.

**Botda to'liq test.** Hozir bot faqat to'lov uchun. Testning o'zini bot ichida o'tkazish
O'zbekiston bozorida sezilarli qulaylik bo'lardi.

### 8.4 Operatsion qo'shimchalar

**Admin panelida chek rasmini ko'rsatish.** Telegram `getFile` ni proxy qiluvchi
autentifikatsiyalangan endpoint — veb-admin chekni ko'rmasdan tasdiqlashdan xalos bo'ladi.

**Bir nechta admin + rollar.** Hozir bitta `ADMIN_TELEGRAM_ID`. Ro'yxat + "kim tasdiqladi"
auditi (`approved_by` ustuni allaqachon bor).

**Voronka dashboard'i.** Landing → test boshlandi → tugatildi → to'lov boshlandi →
chek yuborildi → tasdiqlandi. Barcha kerakli vaqt belgilari **allaqachon bazada saqlanmoqda**,
`AdminAnalyticsService` esa tayyor uy.

**Eksport (CSV/Excel).** Sessiyalar va to'lovlarni yuklab olish — buxgalteriya va tahlil uchun.

**Bildirishnoma navbati (outbox).** Hozir adminga xabar yuborilmasa yoki mijoz botni bloklagan
bo'lsa, xabar **izsiz yo'qoladi**. Jadvalga yozib, qayta urinish — pul yo'lida zarur.

**Ma'lumotlarni saqlash siyosati.** Tashlab ketilgan `VISITED` sessiyalarini N kundan keyin
tozalash — ham jadval o'sishini, ham saqlanayotgan shaxsiy ma'lumot hajmini cheklaydi.

---

## 9. Yakuniy baho

| Yo'nalish | Baho | Izoh |
|---|---|---|
| Arxitektura | 8/10 | Toza qatlamlar, tipli modellar, service qayta ishlatiladi |
| Ma'lumotlar qatlami | 6/10 | Yaxshi sxema, ammo `create_all`/Alembic ziddiyati va enum nomuvofiqligi |
| Xavfsizlik | 3/10 | Ochiq matnli parol, standart kalitlar, ommaviy hujjatlar |
| To'lov oqimi | 2/10 | Kod yaxshi yozilgan, lekin **uchi-uchiga ulanmagan** |
| Frontend / UX | 6/10 | Chiroyli va mobil-birinchi, ammo 8.5 MB rasm va JS'siz ishlamaydi |
| Testlar | 6/10 | 42 ta sifatli test, lekin bot va admin auth qamrab olinmagan |
| DevOps | 2/10 | README, CI, Docker, linter, health-check — hech biri yo'q |
| Kontent | 8/10 | Sifatli o'zbekcha matn, etik disclaimer, 16 ta tip to'liq |

**Umumiy:** poydevor mustahkam, ijro yarim yo'lda to'xtagan. P0 ro'yxatidagi 10 ta ish —
ularning aksariyati bir necha qatorlik — mahsulotni "ishlamaydi" holatidan "sotuvga tayyor"
holatiga o'tkazadi. Eng muhimi: **ball hisoblash xatosi** va **to'lov oqimi uzilishi** —
qolgan hamma narsa shulardan keyin keladi.
