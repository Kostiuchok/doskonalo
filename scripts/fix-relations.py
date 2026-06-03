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

print("\nDone. Test:")
print('  curl -sg --globoff "https://admin.doskonalo.render.ua/items/service_groups?fields=id,title,procedures.id,procedures.title&filter[status][_eq]=published"')
