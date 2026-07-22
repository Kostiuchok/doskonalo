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

## Migration plan: doskonalo.clinic

Target: move to client domain `doskonalo.clinic`. Decisions locked in:

- Static HTML → client's shared hosting (cPanel/FTP, provider adm.tools). Domain already resolves there (185.68.16.52), currently showing the hosting's default placeholder page — no site files uploaded yet.
- Directus + PostgreSQL → **stay on current VPS** (`178.105.208.56`), reachable via new subdomain `admin.doskonalo.clinic`.

**Security note:** on a third-party shared host we don't control tenant isolation (hypervisor/container escape, backup/snapshot access, hosting staff) — a compromise there can't be prevented by us, only bounded by what's exposed. The only thing that must never reach that host is the repo's `.env` (`DB_PASSWORD`, `SECRET` — Directus's JWT signing key — and `ADMIN_EMAIL`/`ADMIN_PASSWORD`): it's already `.gitignore`d and lives with `docker-compose.yml` for the VPS side, but nothing stops someone from FTP/zipping the whole project folder instead of just `www/` during deploy. Only `www/` (static HTML/JS, no secrets — the pages call Directus anonymously via its Public role, no token embedded) is meant to leave the VPS.

### Checklist

- [x] **DNS**: client added A record `admin.doskonalo.clinic` → `178.105.208.56` (2026-07-22)
- [x] Confirm DNS propagated (`nslookup admin.doskonalo.clinic` → `178.105.208.56`)
- [x] Add Caddy site block on VPS for `admin.doskonalo.clinic` (auto HTTPS) — added to `/root/dddcore/Caddyfile` on the VPS (shared Caddy instance, also serves `ddd.render.ua`, `doskonalo.render.ua`, `ulit.render.ua`, `ue-commerce.render.ua`, `finlover.render.ua`). Note: the bind-mounted Caddyfile inside the running container was stale (predated this edit), so a straight `reload` reported "config unchanged" — required `docker compose restart caddy` to actually pick up the new file. Cert issued, verified HTTP 200; other 5 sites re-checked healthy after restart.
- [x] Update `docker-compose.yml`: `PUBLIC_URL` → `https://admin.doskonalo.clinic` (updated on VPS `/root/doskonalo/docker-compose.yml` and mirrored in this repo)
- [x] Update `DIRECTUS` var in the 9 HTML files that call the API → `https://admin.doskonalo.clinic` (`price.html`, `blog.html`, `post.html`, `contact-form.html`, `service-skincare.html`, `service-longlife.html`, `service-injection.html`, `service-hardware.html`, `service-body.html`)
- [x] Restart `directus` container to pick up new `PUBLIC_URL` — done, verified `/server/info` responds on new domain
- [x] **Security: audited the Directus Public policy** — found far worse than expected: `contact_submissions` had full `create`/`read`/`update`/`delete`/`share` open to anonymous, all fields. Removed everything except `create`. Verified: anonymous `GET /items/contact_submissions` now returns `FORBIDDEN`; anonymous `POST` still succeeds (now returns `204` instead of the created object, since the policy can no longer read back what it created).
- [x] **Fixed a regression this caused**: `contact-form.html`'s success handler called `r.json()` on the POST response, which would throw on the new empty `204` body and route real successful submissions into the error-message branch. Removed the `.json()` call (its result was unused anyway). Re-deployed and confirmed live.
- [x] **Security: only uploaded the `www/` directory** to the shared host via FTP — repo root, `.env`, `docker-compose.yml`, `scripts/` were never touched on that host.
- [ ] **Security: rotate `SECRET`/`ADMIN_PASSWORD`/`DB_PASSWORD` in `.env`** once, as a precaution — still pending, do this in a calm moment, not urgent since `.env` never left the VPS.
- [x] Upload `www/` files to client's shared hosting via FTP (174 files, all succeeded; placeholder `index.html` replaced)
- [x] Smoke test on `doskonalo.clinic`: pages load (price/blog/contact-form/service-body all HTTP 200), price/services/blog fetch from `admin.doskonalo.clinic` correctly, contact form submits and is confirmed end-to-end (test row created then deleted)
- [ ] Once confirmed working, treat `doskonalo.clinic` as primary; decide whether to keep or retire `doskonalo.render.ua` / `admin.doskonalo.render.ua`
- [ ] **Cleanup:** the shared-host upload carried over unused legacy files as-is (`contact.php` — dead code, the real form posts to Directus via `fetch()`; `clapaert portfolio block.html`) — fine functionally, but worth pruning next time `www/` gets re-synced

## Changelog

### 2026-07-22
- Migrated live site from `doskonalo.render.ua` to `doskonalo.clinic`: DNS, Caddy site block on VPS, `PUBLIC_URL`, `DIRECTUS` var in 9 HTML files, `www/` uploaded to client's shared hosting
- Security: locked down Directus Public policy on `contact_submissions` from full `create/read/update/delete/share` (anonymous) down to `create`-only
- Fixed `contact-form.html` success handler to not call `r.json()` on the now-empty `204` POST response

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
