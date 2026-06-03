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

## Next Steps

- [x] Connect contact form to save submissions into `contact_submissions`
- [x] Convert blog page to fetch posts from Directus API
- [x] Convert services page to fetch from Directus API
- [x] Point real domain + set up HTTPS via Caddy (admin.doskonalo.render.ua)
