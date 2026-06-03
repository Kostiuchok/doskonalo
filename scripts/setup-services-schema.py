#!/usr/bin/env python3
"""
Creates service_groups, service_procedures, service_subprocedures collections
in Directus with all fields, relations, public read permissions, and seeds
the 5 initial service groups.

Usage (run on the server):
  python3 /root/doskonalo/scripts/setup-services-schema.py
"""
import os, sys, json
import urllib.request, urllib.error

DIRECTUS = "https://admin.doskonalo.render.ua"

# ─── Load .env ────────────────────────────────────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), "../.env")
env = {}
try:
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
except FileNotFoundError:
    print(f"ERROR: .env not found at {env_path}")
    sys.exit(1)

# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def _req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(DIRECTUS + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:300]}"

def post(path, data, token, *, silent_if_exists=True):
    r, err = _req("POST", path, data, token)
    if err:
        low = err.lower()
        if silent_if_exists and ("already exists" in low or "duplicate" in low
                                  or "unique" in low or "23505" in err or "23000" in err):
            print("    (already exists, skipped)")
            return True
        print(f"  ✗ POST {path}: {err}")
        return False
    return True

def get(path, token):
    r, err = _req("GET", path, token=token)
    if err:
        print(f"  ✗ GET {path}: {err}")
        return None
    return r

# ─── Login ────────────────────────────────────────────────────────────────────
print("Logging in…")
r, err = _req("POST", "/auth/login", {
    "email": env.get("ADMIN_EMAIL", ""),
    "password": env.get("ADMIN_PASSWORD", ""),
})
if err:
    print(f"Login failed: {err}")
    sys.exit(1)
T = r["data"]["access_token"]
print("✓ Logged in\n")

# ─── Task 1 — service_groups ──────────────────────────────────────────────────
print("=== Task 1: service_groups ===")
post("/collections", {"collection": "service_groups",
    "meta": {"icon": "folder", "note": "Групи послуг — верхній рівень ієрархії"}}, T)

for f in [
    {"field": "status", "type": "string", "schema": {"default_value": "draft"},
     "meta": {"interface": "select-dropdown", "width": "half",
              "options": {"choices": [
                  {"text": "Опубліковано", "value": "published"},
                  {"text": "Чернетка",     "value": "draft"},
                  {"text": "Архів",        "value": "archived"},
              ]}}},
    {"field": "sort",  "type": "integer", "meta": {"interface": "input", "hidden": True}},
    {"field": "order", "type": "integer", "schema": {"default_value": 0},
     "meta": {"interface": "input", "width": "half"}},
    {"field": "title", "type": "string",
     "meta": {"interface": "input", "width": "half", "required": True}},
    {"field": "slug",  "type": "string", "schema": {"is_unique": True},
     "meta": {"interface": "input", "width": "half", "required": True,
              "note": "URL-ідентифікатор, лише латиниця та дефіс"}},
    {"field": "subtitle",    "type": "string", "meta": {"interface": "input", "width": "full"}},
    {"field": "description", "type": "text",
     "meta": {"interface": "input-rich-text-html", "width": "full"}},
    {"field": "icon",  "type": "string", "meta": {"interface": "input", "width": "half",
                                                    "note": "Назва іконки або inline SVG"}},
    {"field": "color", "type": "string", "meta": {"interface": "select-color", "width": "half"}},
    {"field": "cover_image", "type": "uuid", "schema": {"is_nullable": True},
     "meta": {"interface": "file-image", "width": "half", "special": ["file"]}},
    {"field": "cover_image_alt", "type": "string",
     "meta": {"interface": "input", "width": "half"}},
    {"field": "seo_title",       "type": "string",
     "meta": {"interface": "input", "width": "half"}},
    {"field": "seo_description", "type": "string",
     "meta": {"interface": "input-multiline", "width": "half"}},
]:
    ok = post(f"/fields/service_groups", f, T)
    print(f"  {'✓' if ok else '✗'} {f['field']}")

print()

# ─── Task 2 — service_procedures ─────────────────────────────────────────────
print("=== Task 2: service_procedures ===")
post("/collections", {"collection": "service_procedures",
    "meta": {"icon": "list", "note": "Процедури всередині груп послуг"}}, T)

for f in [
    {"field": "status", "type": "string", "schema": {"default_value": "draft"},
     "meta": {"interface": "select-dropdown", "width": "half",
              "options": {"choices": [
                  {"text": "Опубліковано", "value": "published"},
                  {"text": "Чернетка",     "value": "draft"},
                  {"text": "Архів",        "value": "archived"},
              ]}}},
    {"field": "sort",  "type": "integer", "meta": {"interface": "input", "hidden": True}},
    {"field": "order", "type": "integer", "schema": {"default_value": 0},
     "meta": {"interface": "input", "width": "half"}},
    {"field": "group_id", "type": "integer", "schema": {"is_nullable": False},
     "meta": {"interface": "select-dropdown-m2o", "special": ["m2o"], "width": "half",
              "required": True, "note": "Група, до якої належить процедура",
              "options": {"template": "{{title}}"}}},
    {"field": "title", "type": "string",
     "meta": {"interface": "input", "width": "half", "required": True}},
    {"field": "slug",  "type": "string", "schema": {"is_unique": True},
     "meta": {"interface": "input", "width": "half", "required": True}},
    {"field": "short_description", "type": "string",
     "meta": {"interface": "input", "width": "full"}},
    {"field": "description", "type": "text",
     "meta": {"interface": "input-rich-text-html", "width": "full"}},
    {"field": "duration", "type": "string",
     "meta": {"interface": "input", "width": "half", "note": "Напр: 30–60 хв"}},
    {"field": "recovery", "type": "string",
     "meta": {"interface": "input", "width": "half", "note": "Напр: немає / 1–3 дні"}},
    {"field": "is_featured", "type": "boolean", "schema": {"default_value": False},
     "meta": {"interface": "boolean", "width": "half",
              "note": "Показати як популярну процедуру"}},
    {"field": "image", "type": "uuid", "schema": {"is_nullable": True},
     "meta": {"interface": "file-image", "width": "half", "special": ["file"]}},
    {"field": "image_alt", "type": "string",
     "meta": {"interface": "input", "width": "half"}},
]:
    ok = post(f"/fields/service_procedures", f, T)
    print(f"  {'✓' if ok else '✗'} {f['field']}")

print()

# ─── Task 3 — service_subprocedures ──────────────────────────────────────────
print("=== Task 3: service_subprocedures ===")
post("/collections", {"collection": "service_subprocedures",
    "meta": {"icon": "attach_money", "note": "Підпроцедури з цінами — прайс-лист"}}, T)

for f in [
    {"field": "status", "type": "string", "schema": {"default_value": "draft"},
     "meta": {"interface": "select-dropdown", "width": "half",
              "options": {"choices": [
                  {"text": "Опубліковано", "value": "published"},
                  {"text": "Чернетка",     "value": "draft"},
              ]}}},
    {"field": "sort",  "type": "integer", "meta": {"interface": "input", "hidden": True}},
    {"field": "order", "type": "integer", "schema": {"default_value": 0},
     "meta": {"interface": "input", "width": "half"}},
    {"field": "procedure_id", "type": "integer", "schema": {"is_nullable": False},
     "meta": {"interface": "select-dropdown-m2o", "special": ["m2o"], "width": "half",
              "required": True, "options": {"template": "{{title}}"}}},
    {"field": "title", "type": "string",
     "meta": {"interface": "input", "width": "full", "required": True}},
    {"field": "description", "type": "string",
     "meta": {"interface": "input", "width": "full", "note": "Уточнення: зона, обсяг, деталі"}},
    {"field": "price", "type": "decimal",
     "schema": {"numeric_precision": 10, "numeric_scale": 2, "is_nullable": False},
     "meta": {"interface": "input", "width": "half", "required": True,
              "options": {"prefix": "₴"}}},
    {"field": "old_price", "type": "decimal",
     "schema": {"numeric_precision": 10, "numeric_scale": 2},
     "meta": {"interface": "input", "width": "half", "options": {"prefix": "₴"},
              "note": "Перекреслена стара ціна (якщо є акція)"}},
    {"field": "currency", "type": "string", "schema": {"default_value": "UAH"},
     "meta": {"interface": "input", "width": "half"}},
    {"field": "unit", "type": "string",
     "meta": {"interface": "input", "width": "half", "note": "Напр: зона, мл, од, сеанс"}},
    {"field": "is_promo", "type": "boolean", "schema": {"default_value": False},
     "meta": {"interface": "boolean", "width": "half",
              "note": "Позначити як акційну позицію"}},
]:
    ok = post(f"/fields/service_subprocedures", f, T)
    print(f"  {'✓' if ok else '✗'} {f['field']}")

print()

# ─── Task 4 — Relations ───────────────────────────────────────────────────────
print("=== Task 4: Relations ===")

ok = post("/relations", {
    "collection": "service_procedures", "field": "group_id",
    "related_collection": "service_groups",
    "meta": {"one_field": "procedures", "one_deselect_action": "nullify", "sort_field": "order"},
    "schema": {"on_delete": "SET NULL"},
}, T)
print(f"  {'✓' if ok else '✗'} service_procedures.group_id → service_groups")

ok = post("/relations", {
    "collection": "service_subprocedures", "field": "procedure_id",
    "related_collection": "service_procedures",
    "meta": {"one_field": "subprocedures", "one_deselect_action": "nullify", "sort_field": "order"},
    "schema": {"on_delete": "SET NULL"},
}, T)
print(f"  {'✓' if ok else '✗'} service_subprocedures.procedure_id → service_procedures")

print()

# ─── Public read permissions ──────────────────────────────────────────────────
print("=== Public read permissions ===")

policies = get("/policies?filter[name][_eq]=Public&limit=1", T)
if not policies or not policies.get("data"):
    print("  WARNING: Public policy not found — add read permissions manually in Directus UI")
else:
    pid = policies["data"][0]["id"]
    print(f"  Policy ID: {pid}")
    for col in ["service_groups", "service_procedures", "service_subprocedures"]:
        ok = post("/permissions", {
            "policy": pid, "collection": col, "action": "read",
            "fields": ["*"], "permissions": {}, "validation": {},
        }, T)
        print(f"  {'✓' if ok else '✗'} {col} → read")

print()

# ─── Task 5 — Seed service_groups ────────────────────────────────────────────
print("=== Task 5: Seed service_groups ===")

for g in [
    {"title": "Ін'єкційна косметологія", "slug": "injection",
     "subtitle": "Ботулін, філери, біоревіталізація",
     "color": "#C9A97A", "icon": "mdi:needle", "order": 1, "status": "published"},
    {"title": "Апаратна косметологія", "slug": "hardware",
     "subtitle": "Лазер, RF-ліфтинг, фотоомолодження",
     "color": "#8FA8B8", "icon": "mdi:devices", "order": 2, "status": "published"},
    {"title": "Догляд за шкірою", "slug": "skincare",
     "subtitle": "Пілінги, маски, мезотерапія",
     "color": "#A8C0A0", "icon": "mdi:face-woman-shimmer", "order": 3, "status": "published"},
    {"title": "Дерматологія", "slug": "dermatology",
     "subtitle": "Лікування шкірних захворювань",
     "color": "#C4A0A0", "icon": "mdi:stethoscope", "order": 4, "status": "published"},
    {"title": "Тіло", "slug": "body",
     "subtitle": "Корекція фігури, антицелюліт",
     "color": "#B0A8C4", "icon": "mdi:human", "order": 5, "status": "published"},
]:
    ok = post("/items/service_groups", g, T, silent_if_exists=False)
    print(f"  {'✓' if ok else '✗'} {g['title']}")

print()
print("=== Done! ===")
print()
print("Next: add procedures in Directus → Content → service_procedures")
print("Verify API:")
print(f"  {DIRECTUS}/items/service_groups?fields=id,title,procedures.title,procedures.subprocedures.title,procedures.subprocedures.price&filter[status][_eq]=published&sort=order")
