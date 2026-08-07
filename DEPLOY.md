# Deploy qoʻllanmasi

Bu hujjat MBTI platformasini productionga chiqarish tartibini tavsiflaydi.
Umumiy maʼlumot va `.env` kalitlari tavsifi uchun [README.md](README.md) ga qarang.

Ikkita variant bor:

- **A — Docker Compose** (tavsiya etiladi): `db` + `web` + `bot` bitta buyruq bilan;
- **B — systemd** (Docker'siz server): PostgreSQL alohida, ikki service unit.

---

## 0. Deploydan oldin

- [ ] `.env` tayyor va **repoga commit qilinmagan**
- [ ] `SECRET_KEY` tasodifiy: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- [ ] `ADMIN_PASSWORD_HASH` toʻldirilgan, `ADMIN_PASSWORD` **boʻsh**:
      `python -c "from app.config import hash_password; print(hash_password('YANGI-PAROL'))"`
- [ ] `ADMIN_USERNAME` `admin` emas
- [ ] `DEBUG=false`
- [ ] `PUBLIC_BASE_URL` haqiqiy `https://` domen (bot havolalari shundan quriladi)
- [ ] `BOT_TOKEN` va `BOT_USERNAME` **bitta va oʻsha** botga tegishli
- [ ] `ADMIN_TELEGRAM_ID` toʻgʻri (aks holda botdagi tasdiqlash tugmalari ishlamaydi)
- [ ] `RATE_LIMIT_ENABLED=true`; bir nechta uvicorn worker boʻlsa
      `RATE_LIMIT_STORAGE_URI=redis://...` (`memory://` har bir workerda alohida hisoblaydi)
- [ ] `SENTRY_DSN` toʻldirilgan (ixtiyoriy, ammo tavsiya etiladi)
- [ ] PostgreSQL uchun backup rejasi bor
- [ ] README ning 9-boʻlimi (git tarixidagi karta raqami) koʻrib chiqilgan

> `DEBUG=false` boʻlganda ilova sozlamalarni tekshiradi va yuqoridagilardan biri buzilsa
> **ishga tushmaydi** (`RuntimeError: Xavfsiz boʻlmagan sozlamalar: ...`). Deploydan keyin
> loglarni albatta koʻring.

---

## A. Docker Compose

### A.1. Birinchi ishga tushirish

```bash
git clone <repo-url> /opt/akbar_mbti
cd /opt/akbar_mbti

cp .env.example .env
# .env ni toʻldiring (README 5-boʻlim)

docker compose up -d --build
docker compose ps
```

Compose quyidagilarni bajaradi:

| Servis | Nima qiladi |
| --- | --- |
| `db` | `postgres:16-alpine`, maʼlumotlar `pgdata` named volume'da, `pg_isready` healthcheck |
| `web` | `db` sogʻlom boʻlgach → `alembic upgrade head` → `uvicorn app.main:app` (port 8000) |
| `bot` | `web` sogʻlom boʻlgach → `python -m app.bot` |

`web` va `bot` **bitta image** dan (`akbar-mbti:latest`) ishlaydi, migratsiyani esa faqat
`web` bajaradi — shuning uchun bir vaqtda ikkita alembic jarayoni yuzaga kelmaydi.

`.env` dagi `DATABASE_URL` compose ichida `db` xostiga override qilinadi
(`docker-compose.yml` dagi `environment` blokiga qarang), shuning uchun lokal
`localhost:5432` qiymati konteynerlarga xalaqit bermaydi.

Postgres foydalanuvchi/parol/baza nomini oʻzgartirmoqchi boʻlsangiz, `.env` ga qoʻshing:

```env
POSTGRES_USER=mbti
POSTGRES_PASSWORD=<kuchli-parol>
POSTGRES_DB=mbti
WEB_PORT=8000
```

### A.2. Seed (faqat birinchi marta)

```bash
docker compose exec web python -m app.seed --help
```

### A.2.1. Admin hisoblari (ixtiyoriy, lekin tavsiya etiladi)

`.env` dagi hisob — zaxira yoʻl. Kundalik ish uchun nomli hisoblar yarating:

```bash
docker compose exec web python -m app.admins create --username erkin --role owner
docker compose exec web python -m app.admins create --username dilnoza --role moderator \
    --telegram-id 123456789
docker compose exec web python -m app.admins list
```

Parol buyruq satrida emas, soʻrov orqali kiritiladi — shell tarixida qolmaydi.
Rollar: `owner` (hammasi), `moderator` (toʻlovlar, sessiyalar, eksport),
`viewer` (faqat umumiy koʻrsatkichlar — shaxsiy maʼlumot va cheklarni koʻrmaydi).

### A.3. Yangilash (deploy)

```bash
cd /opt/akbar_mbti
git pull
docker compose build
docker compose up -d          # web ishga tushishda alembic upgrade head ni oʻzi bajaradi
docker compose logs -f web bot
```

### A.4. Kundalik buyruqlar

```bash
docker compose ps                       # holat + health
docker compose logs -f --tail=100 web   # web loglari
docker compose logs -f --tail=100 bot   # bot loglari
docker compose restart bot
docker compose exec web alembic current
docker compose exec db psql -U mbti -d mbti
docker compose down                     # toʻxtatish (volume saqlanadi)

# Maʼlumotlarni saqlash siyosati: avval koʻring, keyin bajaring
docker compose exec web python -m app.retention
docker compose exec web python -m app.retention --apply

# Admin hisoblari
docker compose exec web python -m app.admins list
```

> `docker compose down -v` **bazani oʻchiradi** — `pgdata` volume yoʻqoladi.

### A.5. Backup / restore

```bash
# backup
docker compose exec -T db pg_dump -U mbti -d mbti | gzip > backup-$(date +%F).sql.gz

# restore
gunzip -c backup-2026-08-06.sql.gz | docker compose exec -T db psql -U mbti -d mbti
```

Backupni cron'ga qoʻying va nusxani boshqa serverda saqlang.

### A.6. Saqlash siyosatini rejalashtirish

Tozalash **avtomatik ishlamaydi** — uni siz rejalashtirasiz. Host crontab'iga:

```cron
# Har kuni 04:15 da (backupdan KEYIN)
15 4 * * * cd /opt/akbar_mbti && docker compose exec -T web python -m app.retention --apply \
    >> /var/log/mbti-retention.log 2>&1
```

Nima boʻlishini oldindan koʻrish uchun `--apply` siz ishlating yoki `/admin/retention`
sahifasini oching. Sahifa hech narsani oʻchirmaydi.

> Konteyner ichida cron yoʻq (image'da faqat `curl` bor va u root'siz ishlaydi),
> shuning uchun jadval hostdan boshqariladi.

---

## B. systemd (Docker'siz)

### B.1. Tayyorlash

```bash
sudo adduser --system --group --home /opt/akbar_mbti mbti
sudo -u mbti git clone <repo-url> /opt/akbar_mbti
cd /opt/akbar_mbti

sudo -u mbti python3 -m venv .venv
sudo -u mbti .venv/bin/pip install --upgrade pip
# psycopg2-binary requirements.txt da izohga olingan — PostgreSQL uchun alohida kerak
sudo -u mbti .venv/bin/pip install -r requirements.txt psycopg2-binary==2.9.11

sudo -u mbti cp .env.example .env
sudo -u mbti nano .env
sudo chmod 600 .env

sudo -u mbti .venv/bin/alembic upgrade head
sudo -u mbti .venv/bin/python -m app.seed --help
```

### B.2. `/etc/systemd/system/mbti-web.service`

```ini
[Unit]
Description=MBTI web (FastAPI)
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
Type=simple
User=mbti
Group=mbti
WorkingDirectory=/opt/akbar_mbti
EnvironmentFile=/opt/akbar_mbti/.env
ExecStartPre=/opt/akbar_mbti/.venv/bin/alembic upgrade head
ExecStart=/opt/akbar_mbti/.venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips='*'
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

### B.3. `/etc/systemd/system/mbti-bot.service`

```ini
[Unit]
Description=MBTI Telegram bot (aiogram)
After=network-online.target mbti-web.service
Wants=network-online.target

[Service]
Type=simple
User=mbti
Group=mbti
WorkingDirectory=/opt/akbar_mbti
EnvironmentFile=/opt/akbar_mbti/.env
ExecStart=/opt/akbar_mbti/.venv/bin/python -m app.bot
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mbti-web mbti-bot
sudo systemctl status mbti-web mbti-bot
sudo journalctl -u mbti-bot -f
```

### B.4. Yangilash

```bash
cd /opt/akbar_mbti
sudo -u mbti git pull
sudo -u mbti .venv/bin/pip install -r requirements.txt psycopg2-binary==2.9.11
sudo -u mbti .venv/bin/alembic upgrade head
sudo systemctl restart mbti-web mbti-bot
```

---

## C. Reverse proxy va HTTPS

Ilova `ProxyHeadersMiddleware` bilan ishlaydi, shuning uchun nginx `X-Forwarded-*`
sarlavhalarini uzatishi shart — aks holda natija havolalari `http://` boʻlib qoladi.

`/etc/nginx/sites-available/mbti`:

```nginx
server {
    listen 80;
    server_name example.uz;
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name example.uz;

    ssl_certificate     /etc/letsencrypt/live/example.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.uz/privkey.pem;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/mbti /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d example.uz
```

Domen ishga tushgach `.env` da `PUBLIC_BASE_URL=https://example.uz` ekanini tekshiring
va `web` bilan `bot` ni qayta ishga tushiring — bot havolalari faqat qayta ishga
tushgandan keyin yangilanadi.

---

## D. Monitoring

- Health: `curl -fsS https://example.uz/health`
- Docker: `docker compose ps` ustunida `healthy` boʻlishi kerak
  (HEALTHCHECK har 30 soniyada `/health` ni soʻraydi)
- Loglar: `docker compose logs -f` yoki `journalctl -u mbti-web -u mbti-bot -f`
- Uptime monitoring (UptimeRobot va h.k.) ni `/health` ga ulang
- **Bildirishnoma navbati**: `/admin/notifications`. U yerda ishchining oxirgi belgisi
  (heartbeat) va kechikkan xabarlar soni koʻrinadi. Ishchi **bot jarayonida** ishlaydi,
  shuning uchun bot toʻxsa hech bir xabar yetkazilmaydi va sahifa buni ogohlantirish
  sifatida koʻrsatadi.
- Navbat holati ataylab `/health` ga qoʻshilmagan: u Docker HEALTHCHECK va bot
  konteynerining start sharti hamdir, ya'ni navbat toʻlib qolsa web qayta ishga
  tushirilardi va bot umuman koʻtarilmasdi — navbat esa hech qachon boʻshamasdi.

---

## E. Tez-tez uchraydigan muammolar

| Belgi | Sabab | Yechim |
| --- | --- | --- |
| `RuntimeError: Xavfsiz boʻlmagan sozlamalar: ...` | `DEBUG=false` da sozlama tekshiruvi yiqildi | Xabardagi roʻyxatni oʻqing; 0-boʻlimdagi checklist boʻyicha `.env` ni tuzating |
| `ModuleNotFoundError: No module named 'psycopg2'` | `psycopg2-binary` `requirements.txt` da izohga olingan | `pip install psycopg2-binary==2.9.11` (Docker image'da allaqachon bor) |
| `web` konteyner qayta-qayta restart boʻladi | `db` hali tayyor emas yoki `DATABASE_URL` notoʻgʻri | `docker compose logs db`, `.env` dagi ulanish satrini tekshiring |
| `alembic upgrade head` xatolik beradi | Baza sxemasi qoʻlda oʻzgartirilgan yoki revision uzilgan | `alembic current` va `alembic history` ni solishtiring |
| Bot javob bermaydi | `BOT_TOKEN` boʻsh/notoʻgʻri, yoki bir vaqtda ikkinchi polling jarayoni ishlayapti | Loglarni koʻring; **bitta** bot jarayoni ishlashi shart |
| Deep-link `t.me/...?start=premium_...` ochilmaydi | `BOT_USERNAME` `BOT_TOKEN` egasi bilan mos emas | Ikkalasini bitta botdan oling |
| Botdagi "Tasdiqlash" tugmasi ishlamaydi | `ADMIN_TELEGRAM_ID`/`ADMIN_TELEGRAM_IDS` notoʻgʻri, yoki hisob roli `viewer` | Oʻz ID ingizni @userinfobot dan oling; rolni `python -m app.admins list` bilan tekshiring |
| Mijozga xabar/PDF bormayapti | Bot jarayoni toʻxtagan — navbat ishchisi oʻsha yerda | `/admin/notifications` da heartbeat'ni koʻring, `docker compose restart bot`. Xabarlar yoʻqolmaydi, navbatda kutadi |
| `/admin/notifications` da koʻp `failed` | Telegram xatosi qaytarilmagan (bloklangan foydalanuvchi, yaroqsiz chat) | Qatordagi xatoni oʻqing; tuzatilgach "Qayta urinish" tugmasi urinishlar hisobini nolga qaytaradi |
| Panelga hech kim kira olmayapti | Oxirgi ega oʻchirilgan yoki `ADMIN_ENV_LOGIN_ENABLED=false` | `python -m app.admins activate --username <login>` yoki `set-password` |
| Tozalashdan keyin voronka sonlari oʻzgardi | Bunday boʻlmasligi kerak — oʻchirilgan sessiyalar avval kunlik agregatga yigʻiladi | `session_daily_stats` jadvalini tekshiring va xatoni xabar qiling |
| Natija havolalari `http://` boʻlib chiqadi | Reverse proxy `X-Forwarded-Proto` yubormayapti yoki `PUBLIC_BASE_URL` `http://` | nginx konfigi va `.env` ni tuzating |
| Admin panelga kira olmayapman | `ADMIN_PASSWORD_HASH` formati mos emas (bcrypt `$2b$...` boʻlishi kerak) | `python -c "from app.config import hash_password; print(hash_password('parol'))"` bilan qayta hosil qiling |
| Kirgandan keyin darhol chiqib ketadi | `SECRET_KEY` deploylar orasida oʻzgargan | `SECRET_KEY` ni barqaror saqlang (secret store'da) |

---

## F. Rollback

```bash
# Docker
cd /opt/akbar_mbti
git checkout <oldingi-tag-yoki-sha>
docker compose build && docker compose up -d

# Agar migratsiya ham qaytarilishi kerak boʻlsa (avval backupni tekshiring!)
docker compose exec web alembic downgrade -1
```

Migratsiyani qaytarishdan **oldin** har doim `pg_dump` bilan backup oling: barcha
migratsiyalar ham toʻliq `downgrade()` yozilganiga kafolat yoʻq.
