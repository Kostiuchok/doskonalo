# Doskonalo — Aesthetic Medicine Clinic Website

Website for DOSKONALO clinic (cosmetology & dermatology, Kyiv).

## Structure

```
/root/doskonalo/
├── docker-compose.yml   All services
├── .env                 Secrets (DB password, Directus secret, admin credentials)
├── uploads/             Directus file uploads (images, documents)
└── www/                 Static HTML website (cloned from GitHub)
```

## Running Services

| Container | Role | Port |
|---|---|---|
| `doskonalo-db-1` | PostgreSQL 16 (Directus database) | internal |
| `doskonalo-directus-1` | Directus CMS + admin panel | 8055 |
| `doskonalo-www-1` | Nginx serving static HTML | 8080 |

## Access

| | |
|---|---|
| **Admin panel** | https://admin.doskonalo.render.ua |
| **Website** | https://doskonalo.render.ua |
| **Admin email** | tolik.kostyuchok@gmail.com |
| **Admin password** | see `.env` → `ADMIN_PASSWORD` |

## Directus Collections

| Collection | Purpose |
|---|---|
| `blog_posts` | Blog articles — title, slug, cover image, summary, content, publish date, status |
| `services` | Clinic services — name, description, photo, price, category, status |
| `contact_submissions` | Messages from the contact form — name, phone, email, message, status |

## GitHub Repo

HTML source files: https://github.com/Kostiuchok/doskonalo

To pull latest HTML changes on the server:
```bash
cd /root/doskonalo/www && git pull
```

## Useful Commands

```bash
cd /root/doskonalo

docker compose ps                          # check running containers
docker compose logs directus --tail 50    # Directus logs
docker compose restart directus           # restart Directus
docker compose down                        # stop everything
docker compose up -d                       # start everything
```

## Connect to the server

ssh root@178.105.208.56

## Directus: service_subprocedures fields

| Field | Type | Notes |
|---|---|---|
| `price` | decimal | Numeric price (kopecks not used — full UAH) |
| `price_text` | string | Free-text price override, e.g. `від 500 / 700`. Currency suffix " грн" added automatically on frontend. Takes priority over `price`. |
| `price_women` / `price_men` | decimal | Gender-based pricing |
| `old_price` / `old_price_women` / `old_price_men` | decimal | Crossed-out old price |
| `currency` | string | Currency label (not yet used on frontend — грн hardcoded) |

### Price table logic (service-*.html, price.html)

Per section (group of subprocedures):
- Only `price`/`price_text` rows → 2 columns: **Назва \| Ціна**
- Only gender rows → 2 columns: **Назва \| Жінки \| Чоловіки**
- Mixed → 4 columns: **Назва \| Ціна \| Жінки \| Чоловіки**

## План міграції (майбутнє)

Мета: перенос на клієнтський домен `doskonalo.clinic`. Рішення: Directus + PostgreSQL **лишаються на поточному VPS** (`178.105.208.56`, `admin.doskonalo.render.ua`) — на shared hosting клієнта переїжджає тільки статичний фронтенд `www/`. Всі внутрішні посилання між сторінками в HTML — відносні (`about.html`, `price.html` тощо), тож переписувати їх не потрібно, якщо `www/` заливається в корінь хостингу як є.

### Чекліст

**Підготовка**
- [ ] Отримати доступ до shared hosting (FTP/SFTP або панель керування — cPanel/Plesk/ISPmanager)
- [ ] Підтвердити, хто керує DNS для `doskonalo.clinic` (ми або клієнт)
- [ ] Підтвердити, що хостинг підтримує HTTPS (AutoSSL/Let's Encrypt через панель)
- [ ] Синхронізувати `www/` з VPS (`root@178.105.208.56:/root/doskonalo/www/`) з GitHub-репо (`Kostiuchok/doskonalo`) перед переносом

**Заливка файлів**
- [ ] Завантажити вміст `www/` у кореневу директорію хостингу (`public_html/` або еквівалент), зберігаючи структуру папок (`css/`, `js/`, `images/`, `webfonts/`, `data/`, `admin/`)
- [ ] Не переносити невикористовувані застарілі файли (`contact.php` — мертвий код, форма насправді відправляється в Directus через `fetch()`; `clapaert portfolio block.html`)
- [ ] Не чіпати змінну `DIRECTUS` (`https://admin.doskonalo.render.ua`) у 9 файлах, де вона є (`service-*.html`, `blog.html`, `post.html`, `price.html`, `contact-form.html`)

**DNS + HTTPS**
- [ ] Прописати A-запис (або CNAME) `doskonalo.clinic` на IP нового хостингу
- [ ] Увімкнути SSL на новому хостингу
- [ ] Дочекатись пропагації DNS (до 24–48 год)

**Перевірка**
- [ ] Відкрити всі сторінки на новому домені: `index`, `about`, `price`, `blog`, `likari`, `service-*`
- [ ] Перевірити, що контент з Directus підтягується (ціни, блог, послуги) — cross-origin запити до `admin.doskonalo.render.ua` мають працювати, бо `CORS_ORIGIN: "true"`
- [ ] Відправити тестове звернення через контактну форму, перевірити появу в `contact_submissions`
- [ ] Перевірити мобільну версію
- [ ] Перевірити, що всі внутрішні навігаційні посилання (відносні шляхи) працюють на новому домені

**Фіналізація**
- [ ] Оновити цей README новими деталями хостингу/доступів
- [ ] Вирішити, чи зупиняти старий `www` nginx-контейнер (порт 8080) на VPS, чи лишити як staging — контейнери `db`/`directus` не чіпати

## Changelog

### 2026-06-26
- Services section background: `#000` → `#E2DED5`
- slide-title + slide-subtitle: `display: inline` (one line)
- Price tables `thead` background: `rgba(0,0,0,1)` → `#826040`
- Added `price_text` field support on all price pages (free-text price with auto currency suffix)
- Mixed price table layout: Ціна + Жінки + Чоловіки columns when section has both types
- Added static Консультація table at top of price.html

## Next Steps

- [x] Connect contact form to save submissions into `contact_submissions`
- [x] Convert blog page to fetch posts from Directus API
- [x] Convert services page to fetch from Directus API
- [x] Point real domain + set up HTTPS via Caddy (admin.doskonalo.render.ua)
- [ ] Migrate to doskonalo.clinic domain (client hosting for frontend, VPS stays for Directus)
- [ ] Use `currency` field from Directus instead of hardcoded " грн"
