# MBTI Shaxsiyat Testi Platformasi

Oʻzbek tilidagi MBTI (16 tip) shaxsiyat testi platformasi: veb-test, natija sahifasi,
premium natijani qoʻlda (karta orqali) toʻlash oqimi, Telegram bot orqali chek qabul qilish
va admin panelda moderatsiya.

Loyiha ikki jarayondan iborat:

- **web** — FastAPI ilovasi (`uvicorn app.main:app`): test, natija, admin panel;
- **bot** — aiogram 3 boti (`python -m app.bot`): premium deep-link, chek (kvitansiya) qabul qilish,
  adminga tasdiqlash/rad etish tugmalari.

---

## 1. Asosiy imkoniyatlar

- 16 tipli MBTI testi (savollar va natija matnlari bazadan oʻqiladi, oʻzbek tilida).
- Sessiyaga bogʻlangan token: natija `/personality/result/{token}` manzilida ochiladi.
- Bepul qisqa natija va **premium** toʻliq natija.
- Premium toʻlov oqimi: natija sahifasidan → Telegram deep-link (`?start=premium_<token>`) →
  bot chekni qabul qiladi → admin (bot tugmasi yoki admin panel) tasdiqlaydi → sessiya
  `is_premium = true` boʻladi.
- Admin panel: sessiyalar, analitika, premium soʻrovlar moderatsiyasi.
- Oʻsish kanallari:
  - **Ommaviy ulashish sahifasi** `/r/{share_code}` — cookie talab qilmaydi, faqat xarakter
    tipi va oʻlchovlarni koʻrsatadi (premium tahlil, toʻlov maʼlumotlari va sessiya tokeni
    unga chiqmaydi). Har tip uchun Open Graph rasmi bilan Telegram/ijtimoiy tarmoqlarda
    oldindan koʻrinadi.
  - **Test tarixi** `/personality/history` — shu brauzerda tugallangan testlar va birinchi
    hamda oxirgi urinish orasidagi oʻlchov siljishi.
  - **Ikki til** (oʻzbek/rus): interfeys, oʻlchov nomlari va 16 tipning natija kontenti.

### Open Graph rasmlari

`app/static/images/og/{TIP}.png` — 16 ta tayyor rasm repoda saqlanadi, shuning uchun ish
vaqtida generatsiya ham, shrift fayli ham kerak emas. Dizayn oʻzgarsa qayta yarating:

```bash
python scripts/generate_og_images.py
```

Skript Inter shriftini (OFL) `.fontcache/` ga yuklab oladi — u repoga qoʻshilmaydi.

---

## 2. Arxitektura

Qatlamlar aniq ajratilgan: **router → service → repository → model**.

```
                          ┌───────────────────┐
   Foydalanuvchi ────────►│  Browser (Jinja2) │
                          └─────────┬─────────┘
                                    │ HTTP
                     ┌──────────────▼───────────────────────────┐
                     │ app/main.py — FastAPI                    │
                     │ app/routers/  personality | admin |      │
                     │               relationship               │
                     │   HTTP, form, session cookie, template   │
                     └──────────────┬───────────────────────────┘
                                    │
                     ┌──────────────▼───────────────────────────┐
                     │ app/services/                            │
                     │   personality_service, personality_scoring│
                     │   premium_payment_service                │
                     │   admin_analytics_service                │
                     │   biznes-mantiq, HTTP dan xabarsiz       │
                     └──────────────┬───────────────────────────┘
                                    │
                     ┌──────────────▼───────────────────────────┐
                     │ app/repositories/                        │
                     │   personality_repository, payment_...    │
                     │   faqat SQLAlchemy soʻrovlari            │
                     └──────────────┬───────────────────────────┘
                                    │
                     ┌──────────────▼───────────────────────────┐
                     │ app/models/ — SQLAlchemy 2.0 ORM         │
                     └──────────────┬───────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │ PostgreSQL/SQLite │
                          └─────────▲─────────┘
                                    │ bir xil service qatlami
                     ┌──────────────┴───────────────────────────┐
                     │ app/bot/ — aiogram 3 (alohida jarayon)   │
                     │   handlers.py: deep-link, chek, moderatsiya│
                     └──────────────────────────────────────────┘
```

Papkalar:

| Yoʻl | Vazifasi |
| --- | --- |
| `app/main.py` | FastAPI ilovasi, middleware, router registratsiyasi |
| `app/config.py` | `Settings` (pydantic-settings), `.env` dan oʻqiydi |
| `app/database.py` | engine, `SessionLocal`, `Base`, `get_db` dependency |
| `app/routers/` | HTTP qatlami (`/personality`, `/admin`, `/relationship`) |
| `app/services/` | biznes-mantiq (scoring, premium toʻlov, analitika) |
| `app/repositories/` | baza soʻrovlari |
| `app/models/` | ORM modellar va enumlar |
| `app/personality/` | domen yordamchilari (theme, payment code, session binding) |
| `app/seed/` | savollar va natija matnlarining boshlangʻich maʼlumotlari |
| `app/bot/` | aiogram bot (`python -m app.bot`) |
| `app/templates/`, `app/static/` | Jinja2 shablonlar va statik fayllar |
| `alembic/` | migratsiyalar |
| `tests/` | pytest testlari |

---

## 3. Talablar

- **Python 3.10+** (CI 3.10 va 3.12 da tekshiradi)
- **PostgreSQL 14+** (production) yoki **SQLite** (lokal ishlanma uchun yetarli)
- Telegram bot tokeni (premium oqimi uchun; testlarni ishga tushirishga shart emas)

---

## 4. Oʻrnatish

```bash
git clone <repo-url> akbar_mbti
cd akbar_mbti

# virtual muhit
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

`requirements.txt` — ishlab turgan ilova uchun; `requirements-dev.txt` — testlar va lint
(pytest, pytest-cov, httpx, ruff, mypy). `requirements-dev.txt` oʻzi `requirements.txt` ni
ham tortadi, shuning uchun lokal ishlanmada `pip install -r requirements-dev.txt` yetarli.

> **PostgreSQL uchun driver.** `psycopg2-binary` `requirements.txt` da izohga olingan, chunki
> lokal ishlanma SQLite da ketadi. Postgres ga ulanadigan boʻlsangiz uni qoʻlda oʻrnating:
> `pip install psycopg2-binary==2.9.11`. Docker image buni allaqachon oʻz ichiga oladi.

---

## 5. `.env` sozlash

`.env.example` dan nusxa oling va qiymatlarni oʻzingiznikiga almashtiring:

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

### Asosiy

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `DATABASE_URL` | Baza ulanish satri | Prod: `postgresql+psycopg2://user:pass@host:5432/mbti`. Lokal: `sqlite:///./mbti_dev.db` |
| `SECRET_KEY` | Session cookie'ni imzolaydi (`SessionMiddleware`). Oʻzgarsa — barcha admin sessiyalari bekor boʻladi | **Majburiy.** `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DEBUG` | Xavfsizlik tekshiruvlari rejimi: `true` — faqat ogohlantirish, `false` — xato boʻlsa ilova **ishga tushmaydi** | Productionda `false` |
| `PUBLIC_BASE_URL` | Ilovaning tashqi manzili; bot yuboradigan natija havolalari shundan quriladi | Prod: `https://example.uz`. `DEBUG=false` da `localhost`/`127.0.0.1` qabul qilinmaydi |

### Admin panel

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `ADMIN_USERNAME` | `/admin/login` uchun login | `DEBUG=false` da `admin` boʻlishi mumkin emas |
| `ADMIN_PASSWORD_HASH` | Admin parolining **bcrypt hash'i** — ochiq parol hech qayerda saqlanmaydi | Productionda majburiy; quyidagi buyruq bilan hosil qilinadi |
| `ADMIN_PASSWORD` | Faqat lokal qulaylik uchun ochiq parol: `DEBUG=true` da ishga tushishda hashlanadi | `DEBUG=false` da **qabul qilinmaydi**; `admin` qiymati taqiqlangan |

### Telegram

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `BOT_TOKEN` | @BotFather bergan token; bot shu token bilan ishga tushadi | Boʻsh boʻlsa `python -m app.bot` ishlamaydi |
| `BOT_USERNAME` | Chekni **haqiqatda qabul qiladigan** bot username'i (`@` siz). Deep-link shundan quriladi: `https://t.me/<BOT_USERNAME>?start=premium_<token>` | `BOT_TOKEN` egasi bilan **bitta va oʻsha** bot boʻlishi shart |
| `PAYMENT_SUPPORT_BOT_USERNAME` | Koʻrsatiladigan qoʻllab-quvvatlash boti | `BOT_USERNAME` boʻsh boʻlsa zaxira sifatida ishlatiladi |
| `ADMIN_TELEGRAM_ID` | Botda "Tasdiqlash / Rad etish" tugmalarini bosishga ruxsat etilgan Telegram user ID (raqam) | ID ni @userinfobot dan oling |

### Premium toʻlov

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `PREMIUM_PRICE` | Premium narxi (soʻm, butun son) | Standart: `9990` |
| `PAYMENT_CARD_NUMBER` | Toʻlov qabul qilinadigan karta raqami | **Hech qachon repoga commit qilmang** — 9-boʻlimga qarang |
| `PAYMENT_CARD_HOLDER` | Karta egasining ismi (natija sahifasida koʻrsatiladi) | |

### Monitoring va rate limit

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `SENTRY_DSN` | Xatoliklarni Sentry ga yuboradi | Boʻsh boʻlsa Sentry oʻchiq |
| `SENTRY_TRACES_SAMPLE_RATE` | Tracing namunasi ulushi (`0.0`–`1.0`) | Prod uchun `0.05` atrofida yetarli |
| `LOG_LEVEL` | Root logger darajasi | `INFO` (standart), `DEBUG`, `WARNING`… |
| `ACCESS_LOG` | uvicorn access log'ini yoqadi | Standart `false`: aks holda yoʻlda natija tokeni log'ga tushadi |
| `RATE_LIMIT_ENABLED` | Soʻrov cheklovlarini yoqadi/oʻchiradi | Productionda `true` |
| `RATE_LIMIT_DEFAULT` | Barcha yoʻnalishlar uchun standart cheklov | `120/minute` |
| `RATE_LIMIT_LOGIN` | Admin login uchun qatʼiyroq cheklov (brute-force'ga qarshi) | `5/minute` |
| `RATE_LIMIT_STORAGE_URI` | slowapi saqlagichi | `memory://` yoki `redis://host:6379`. Bir nechta worker boʻlsa Redis kerak |

### Xavfsizlik va sessiya

| Kalit | Nima qiladi | Eslatma |
| --- | --- | --- |
| `SECURE_COOKIES` | Cookie'ni faqat HTTPS'ga bogʻlaydi va HSTS sarlavhasini qoʻshadi | Koʻrsatilmasa `DEBUG` boʻyicha aniqlanadi (prod: yoqiq) |
| `SESSION_MAX_AGE` | Admin sessiya cookie'sining amal qilish muddati (sekund) | Standart `28800` (8 soat) |
| `TRUSTED_PROXIES` | `X-Forwarded-*` sarlavhalariga ishoniladigan proxy manzillari (vergul bilan) | Standart `127.0.0.1`; hammasi uchun `*` |
| `CONTENT_SECURITY_POLICY` | CSP sarlavhasini toʻliq almashtiradi | Koʻrsatilmasa qatʼiy standart (`default-src 'self'`, faqat `/static`) |

### Admin parol hash'ini hosil qilish

```bash
python -c "from app.config import hash_password; print(hash_password('YANGI-PAROL'))"
```

Chiqqan `$2b$...` satrni `.env` dagi `ADMIN_PASSWORD_HASH=` ga qoʻying va `ADMIN_PASSWORD` ni
boʻsh qoldiring. Ochiq parolni hech qayerda saqlamang va shell tarixidan oʻchiring
(`history -d`; PowerShell'da `Clear-History`).

> `DEBUG=false` boʻlganda `app/config.py` sozlamalarni tekshiradi va yuqoridagi qoidalar
> buzilsa `RuntimeError` bilan **ishga tushishdan bosh tortadi**. Bu ataylab shunday: notoʻgʻri
> sozlangan ilova jimgina productionga chiqib ketmasligi kerak.

---

## 6. Baza: migratsiya va seed

Sxema **faqat Alembic** orqali yaratiladi — `Base.metadata.create_all()` ishlatilmaydi.
Shuning uchun ilovani ishga tushirishdan oldin migratsiyalarni qoʻllash shart:

```bash
alembic upgrade head
```

Foydali buyruqlar:

```bash
alembic current              # hozirgi revision
alembic history --verbose    # migratsiya zanjiri
alembic revision -m "izoh"   # yangi boʻsh migratsiya
alembic downgrade -1         # bitta orqaga
```

Boshlangʻich maʼlumotlar (savollar va natija matnlari) alohida CLI orqali yuklanadi.
Standart chaqiruv **ikkala til** natija kontentini ham yuklaydi (`uz` va `ru`):

```bash
python -m app.seed                  # savollar + natija matnlari (uz, ru)
python -m app.seed --language ru    # faqat bitta til
python -m app.seed --force --yes    # mavjud matnlarni joyida almashtiradi
python -m app.seed --help
```

Foydalanuvchi tilni `?lang=ru` bilan yoki brauzer sozlamasi orqali tanlaydi; tanlangan
til uchun natija yozuvi topilmasa sahifa `uz` kontentiga qaytadi.

---

## 7. Ishga tushirish (IKKI jarayon)

Web va bot — **alohida** jarayonlar, ikkalasini ham ishga tushirish kerak.

Terminal 1 — web:

```bash
alembic upgrade head
uvicorn app.main:app --reload            # http://127.0.0.1:8000
```

Terminal 2 — bot:

```bash
python -m app.bot
```

Manzillar:

- `/` → `/personality` ga redirect
- `/personality` — test boshlanishi
- `/personality/result/{token}` — natija
- `/admin/login` — admin panel
- `/health` — health check (Docker HEALTHCHECK shu manzilni soʻraydi)

### Docker orqali

```bash
cp .env.example .env      # qiymatlarni toʻldiring
docker compose up --build
```

`docker compose` uchta servisni koʻtaradi: `db` (postgres:16-alpine), `web` (migratsiya +
uvicorn) va `bot` (`python -m app.bot`). Batafsil: [DEPLOY.md](DEPLOY.md).

---

## 8. Testlar va sifat nazorati

```bash
pytest -q                    # testlar
pytest -q --cov=app          # coverage bilan
ruff check .                 # lint
ruff format --check .        # formatlash tekshiruvi (tuzatish uchun: ruff format .)
mypy app                     # type check
```

Testlar xotiradagi SQLite (`sqlite://`) da ishlaydi va tashqi baza yoki `.env` talab qilmaydi.

Xohlasangiz, oʻsha tekshiruvlarni commit oldidan avtomatlashtiring:

```bash
pip install pre-commit
pre-commit install           # .pre-commit-config.yaml: ruff, ruff-format, mypy, fayl tekshiruvlari
```

CI (`.github/workflows/ci.yml`) har `push` va `pull_request` da ishlaydi:

- `quality` job — Python 3.10 va 3.12 matritsasi: ruff check, ruff format --check,
  `mypy app` va `pytest -q --cov=app`. Hammasi qatʼiy: birortasi yiqilsa CI qizil boʻladi;
- `migrations` job — boʻsh SQLite bazada `alembic upgrade head`, soʻng `alembic downgrade base`:
  migratsiya zanjiri ikkala yoʻnalishda ham uzilmaganini tekshiradi.

---

## 9. Xavfsizlik: git tarixidagi karta raqami

**Muammo.** Boshlangʻich commit'da (`67b9db9`, `.env.example`) haqiqiy toʻlov kartasi raqami
qolgan. Ish daraxtidagi fayl allaqachon tozalangan (`PAYMENT_CARD_NUMBER=0000000000000000`),
ammo bu yetarli emas: raqam **git tarixida** saqlanib qoladi va repoga kirish huquqi bor har
kim uni `git log -p -- .env.example` bilan oʻqiy oladi.

**Birinchi navbatda:** raqamni allaqachon oshkor boʻlgan deb hisoblang. Agar mumkin boʻlsa,
kartani almashtiring/bloklang — tarixni tozalash uni oldin klon qilganlarda oʻchirmaydi.

**Tarixni tozalash.** [`git-filter-repo`](https://github.com/newren/git-filter-repo)
kerak (`pip install git-filter-repo`):

```bash
# 0) ZAXIRA — majburiy
git clone --mirror <repo-url> akbar_mbti-backup.git

# 1) toza mirror ustida ishlang
git clone --mirror <repo-url> akbar_mbti-clean.git
cd akbar_mbti-clean.git

# 2) almashtirish qoidasi
#    <KARTA-RAQAMI> o'rniga tarixdagi haqiqiy raqamni qo'ying.
#    Bu faylni repoga QO'SHMANG — ish tugagach o'chiring.
printf '<KARTA-RAQAMI>==>REDACTED-CARD-NUMBER\n' > ../replacements.txt

# 3) tarixni qayta yozish
git filter-repo --replace-text ../replacements.txt

# 4) natijani tekshiring — hech narsa topilmasligi kerak
git log -p --all | grep -c '<KARTA-RAQAMI>'

# 5) force-push
git push --force --all
git push --force --tags
```

> ⚠️ **DIQQAT.** `git filter-repo` **butun tarixni qayta yozadi**: barcha commit SHA lari
> oʻzgaradi va `--force` push talab qilinadi. Ochiq PR lar, forklar va jamoadagi lokal
> klonlar buziladi (har bir ishtirokchi qayta klon qilishi kerak).
> Shuning uchun bu buyruqni **repo egasi oʻzi**, jamoani ogohlantirgan holda bajarishi kerak.
> **Biz uni bajarmadik** — yuqoridagilar faqat koʻrsatma.

**Bundan keyin:**

- `.env` hech qachon commit qilinmaydi (`.gitignore` da bor);
- `.env.example` da faqat **soxta** qiymatlar boʻlsin
  (masalan `PAYMENT_CARD_NUMBER=0000000000000000`);
- `SECRET_KEY`, `BOT_TOKEN`, `ADMIN_PASSWORD_HASH` ham faqat `.env` da yoki deploy
  muhitining secret'larida saqlanadi.

---

## 10. Litsenziya

Loyiha egasi belgilaydi.
