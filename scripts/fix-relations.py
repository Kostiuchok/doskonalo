#!/usr/bin/env python3
"""
Patches the two M2O relations to set the reverse (O2M) one_field,
which enables nested queries like service_groups → procedures → subprocedures.
"""
import os, sys, json
import urllib.request, urllib.error

DIRECTUS = "https://admin.doskonalo.render.ua"

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
        return None, f"HTTP {e.code}: {e.read().decode()[:500]}"

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

patches = [
    ("/relations/service_procedures/group_id",
     {"meta": {"one_field": "procedures", "one_deselect_action": "nullify", "sort_field": "order"}},
     "service_procedures.group_id → one_field=procedures"),

    ("/relations/service_subprocedures/procedure_id",
     {"meta": {"one_field": "subprocedures", "one_deselect_action": "nullify", "sort_field": "order"}},
     "service_subprocedures.procedure_id → one_field=subprocedures"),
]

for path, data, label in patches:
    r, err = _req("PATCH", path, data, T)
    if err:
        print(f"  ✗ {label}: {err}")
    else:
        print(f"  ✓ {label}")

print()

# ── Fix public permissions ────────────────────────────────────────────────────
print("=== Fixing public permissions ===")

r, err = _req("GET", "/policies?filter[name][_eq]=Public&limit=1", token=T)
if err or not r or not r.get("data"):
    print(f"  ✗ Could not find Public policy: {err}")
else:
    pid = r["data"][0]["id"]
    print(f"  Policy ID: {pid}")

    # For each collection, find existing permission and patch fields to include
    # virtual relational fields (procedures, subprocedures) alongside *
    col_fields = {
        "service_groups":       ["*", "procedures"],
        "service_procedures":   ["*", "subprocedures"],
        "service_subprocedures": ["*"],
    }
    for col, fields in col_fields.items():
        # find existing permission
        r2, err2 = _req("GET",
            f"/permissions?filter[policy][_eq]={pid}&filter[collection][_eq]={col}&filter[action][_eq]=read&limit=1",
            token=T)
        if err2:
            print(f"  ✗ GET permissions for {col}: {err2}")
            continue
        if r2 and r2.get("data"):
            perm_id = r2["data"][0]["id"]
            r3, err3 = _req("PATCH", f"/permissions/{perm_id}", {"fields": fields}, T)
            if err3:
                print(f"  ✗ PATCH {col}: {err3}")
            else:
                print(f"  ✓ {col} → fields={fields}")
        else:
            # create
            r3, err3 = _req("POST", "/permissions", {
                "policy": pid, "collection": col, "action": "read",
                "fields": fields, "permissions": {}, "validation": {},
            }, T)
            if err3:
                print(f"  ✗ POST {col}: {err3}")
            else:
                print(f"  ✓ {col} → created with fields={fields}")

print("\nDone. Test:")
print('  curl -sg --globoff "https://admin.doskonalo.render.ua/items/service_groups?fields=id,title,procedures.id,procedures.title&filter[status][_eq]=published"')
