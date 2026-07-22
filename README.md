# Doskonalo — Aesthetic Medicine Clinic Website

Website for DOSKONALO clinic (cosmetology & dermatology, Kyiv). Live at **https://doskonalo.clinic**.

**Status:** migration to `doskonalo.clinic` is done and this is production. The old `doskonalo.render.ua` / `admin.doskonalo.render.ua` (Caddy still proxies it to the `doskonalo-www-1` container on the VPS, port 8080) is stale, unmaintained, and no longer gets frontend updates — **what to do with it is an open decision for a future session** (retire it / redirect it / leave it as-is), see "Next Steps".

## Architecture (since the 2026-07-22 migration)

Two separate hosts, on purpose — see "Migration plan" below for why:

- **Static frontend** (`www/` — all the `.html`/`css`/`js`/images in this repo) is served from the client's **shared hosting** (provider: adm.tools). It has no server-side code and no secrets; it calls Directus over HTTPS from the browser.
- **Directus + PostgreSQL** run in Docker on a **VPS**, shared with a few unrelated other projects behind one Caddy reverse proxy. This is where all the actual data (services, prices, blog, contact submissions) and admin access live.

```
/root/doskonalo/            (on the VPS — NOT this git repo's root)
├── docker-compose.yml      db + directus services (this repo's docker-compose.yml should match it)
├── .env                    Real secrets: DB_PASSWORD, SECRET, ADMIN_EMAIL, ADMIN_PASSWORD, EMAIL_SMTP_PASSWORD
├── uploads/                Directus file uploads (images, documents)
└── www/                    Old nginx-served copy from the pre-migration setup — no longer the live site, kept as-is for now
```

This repo's own `www/` is what actually goes to the shared host (via FTP) — the `/root/doskonalo/www/` on the VPS is a leftover from before the migration and is not what visitors see anymore.

## Access

| What | Where | Credential |
|---|---|---|
| **VPS SSH** | `178.105.208.56` | Key-based, alias `ssh doskonalo` if you have the SSH config entry (`~/.ssh/doskonalo_deploy`) set up; otherwise ask Tolik for VPS root access |
| **Directus admin panel** | https://admin.doskonalo.clinic | Email `tolik.kostyuchok@gmail.com`; password was changed via the Directus UI directly (not by editing `.env`) on 2026-07-22 — if login fails, the `.env` copy on the VPS may be stale; ask Tolik for the current password and update `/root/doskonalo/.env` → `ADMIN_PASSWORD` to match (see "Gotchas" below) |
| **Shared hosting FTP** (for uploading `www/`) | `ftp://dsknlo.ftp.tools:21/`, doc-root is `/doskonalo.clinic/www/` (not FTP root — that directory holds one folder per domain) | Login `dsknlo_ftp`; password held by Tolik, not stored in this repo or on the VPS |
| **Outgoing email** (Directus → client, contact form notifications) | SMTP host `mail.adm.tools`, port `587` (STARTTLS), user `info@doskonalo.clinic` | Password stored only in `/root/doskonalo/.env` → `EMAIL_SMTP_PASSWORD` on the VPS — not in git |
| **GitHub repo** | https://github.com/Kostiuchok/doskonalo | — |

None of the real secrets above are (or should ever be) committed to this repo — `.env` is `.gitignore`d and lives only on the VPS.

## How to deploy a change

1. Edit files locally in this repo, commit, push to GitHub as usual.
2. **Frontend (`www/`)**: upload the changed files to the shared host via FTP (see Access table) — only `www/`, never the repo root or `.env`. There's no automated deploy step; it's a manual `curl -T`/FTP-client upload to `dsknlo.ftp.tools:21/doskonalo.clinic/www/...`.
3. **Directus/backend** (`docker-compose.yml`, schema, permissions, flows): SSH into the VPS (`/root/doskonalo/`), make the equivalent change there (this repo's `docker-compose.yml` is a mirror for reference — the VPS copy is what actually runs), then `docker compose up -d directus` to apply env/config changes, or use the Directus admin UI / REST API directly for schema/permissions/flow changes.

## Gotchas learned the hard way

- **Always `git fetch`/`git pull` before starting work.** This repo gets edited from more than one place — a past session shipped a regression by building on a local branch that was 6 commits behind `origin/main`.
- **The VPS's shared Caddy container can silently run on a stale bind-mounted `Caddyfile`.** If you edit `/root/dddcore/Caddyfile` and `caddy reload` reports "config unchanged" when it shouldn't, the fix is `docker compose restart caddy` (in `/root/dddcore/`) — this briefly affects a few *other* unrelated sites on the same VPS (`ddd.render.ua`, `ulit.render.ua`, `ue-commerce.render.ua`, `finlover.render.ua`), so don't do it lightly.
- **Directus's admin password can be changed directly in the UI**, independently of `.env` — if scripted admin API login starts failing with `401 Invalid user credentials`, this is the first thing to check (ask Tolik, then update `.env` on the VPS).
- **The Directus "Public" policy is what the entire public website runs on** (anonymous reads for prices/blog/services, anonymous create for contact form) — there is no API token anywhere in the frontend. Before granting the Public policy any new permission, check it isn't broader than it needs to be; it was found wide open (`create`/`read`/`update`/`delete`/`share`, all fields) on `contact_submissions` once already.
- **The VPS blocks outbound SMTP on ports 465 and 25** (common cloud-provider anti-spam default) — only `587` and `2525` are open outbound. If Directus emails silently never arrive and there are no errors at all in `docker logs doskonalo-directus-1` (not even a connection failure), suspect the outbound port before anything else; test with a raw `smtplib`/`swaks` connection from the VPS itself to confirm.

## Running Services (VPS)

| Container | Role | Port |
|---|---|---|
| `doskonalo-db-1` | PostgreSQL 16 (Directus database) | internal |
| `doskonalo-directus-1` | Directus CMS + admin panel | 8055 (proxied via Caddy at `admin.doskonalo.clinic`) |
| `doskonalo-www-1` | Nginx serving the old pre-migration static copy — not the live site anymore | 8080 |

## Directus Collections

| Collection | Purpose |
|---|---|
| `blog_posts` | Blog articles — title, slug, cover image, summary, content, publish date, status |
| `service_groups` | Top-level service categories (Ін'єкційна косметологія, Апаратна косметологія, etc.) |
| `service_procedures` | Procedures within a group |
| `service_subprocedures` | Individual priced line items within a procedure — see field notes below |
| `contact_submissions` | Messages from the contact form — name, phone, email, message. Public policy is **create-only**, no read/update/delete — don't widen this without a good reason |

### Email notifications

A Directus **Flow** ("Contact form email notification", trigger: `items.create` on `contact_submissions`) emails `info@doskonalo.clinic` on every new submission, via the SMTP config in "Access" above. Manage/edit it in the Directus admin UI under Settings → Flows.

## Useful Commands

```bash
cd /root/doskonalo

docker compose ps                          # check running containers
docker compose logs directus --tail 50    # Directus logs
docker compose restart directus           # restart Directus
docker compose down                        # stop everything
docker compose up -d                       # start everything
```

## GitHub Repo

HTML source files: https://github.com/Kostiuchok/doskonalo

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

## Migration plan: doskonalo.clinic (completed 2026-07-22 — kept here for history/context)

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
- Fixed a duplicated/un-patched accordion click handler in `price.html` + 5 `service-*.html` pages that still auto-closed sibling sections (missed by an earlier fix that only touched `common.js`)
- Fixed contact form silently failing to submit when reached via the site's AJAX page-transition nav (the Directus submit handler lived in an inline `<script>` that never re-executes on that path) — moved the logic into `js/contact.js`'s `ContactForm()`, which the transition system does re-invoke
- Replaced the decorative "magnetic button" contact-form submit control (which stopped registering real clicks for at least one user, cause not fully root-caused) with a plain styled button
- Added phone/email format validation and a honeypot field to the contact form
- Added a Directus Flow emailing `info@doskonalo.clinic` (via `mail.adm.tools` SMTP) on every new `contact_submissions` row — initially configured on port 465, silently never delivered (VPS blocks that port outbound with no logged error); switched to port 587/STARTTLS, confirmed delivered

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
- [x] Point real domain + set up HTTPS via Caddy
- [x] Migrate to doskonalo.clinic domain (client hosting for frontend, VPS stays for Directus)
- [x] Email notification on new contact form submissions
- [ ] Use `currency` field from Directus instead of hardcoded " грн"
- [ ] Rotate `SECRET`/`ADMIN_PASSWORD`/`DB_PASSWORD` in `.env` as a precaution (see migration checklist below)
- [ ] Decide whether to retire `doskonalo.render.ua` / `admin.doskonalo.render.ua` now that `doskonalo.clinic` is primary
- [ ] Prune unused legacy files from `www/` (`contact.php`, `clapaert portfolio block.html`, leftover template demo pages) next time it's touched
- [ ] Root-cause why the original decorative contact-form button stopped receiving real clicks for at least one user (worked around, not fixed)
