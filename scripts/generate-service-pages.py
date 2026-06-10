#!/usr/bin/env python3
"""
Generates service-injection.html, service-hardware.html, etc.
Also patches the nav submenu in all pages that reference service01.html.
Run from /home/user/doskonalo:
  python3 scripts/generate-service-pages.py
"""
import os, re

WWW = os.path.join(os.path.dirname(__file__), "../www")

GROUPS = [
    ("injection",   "Ін'єкційна косметологія",  "Ін'єкційні процедури"),
    ("hardware",    "Апаратна косметологія",      "Апаратні процедури"),
    ("skincare",    "Догляд за шкірою",           "Догляд за шкірою"),
    ("dermatology", "Дерматологія",               "Дерматологія"),
    ("body",        "Тіло",                       "Тіло"),
]

NEW_SUBMENU_ITEMS = "\n".join([
    f'                                        <li><a class="ajax-link" href="service-{slug}.html" data-type="page-transition">{nav_title}</a></li>'
    for slug, _, nav_title in GROUPS
])

OLD_SUBMENU_RE = re.compile(
    r'(<li><a class="ajax-link[^"]*" href="service01\.html".*?</li>\s*){2,}',
    re.DOTALL
)

# ── Dynamic JS inserted at bottom of each service page ──────────────────────
JS_TEMPLATE = """    <script>
    (function() {
        var GROUP_SLUG = '__GROUP_SLUG__';
        var DIRECTUS = 'https://admin.doskonalo.render.ua';

        function formatPrice(value) {
            if (!value && value !== 0) return '';
            return Math.round(Number(value)).toLocaleString('uk-UA') + ' грн';
        }

        function renderProcedures(procedures, subprocedures) {
            var container = document.getElementById('services-container');
            if (!container) return;

            var subsByProc = {};
            subprocedures.forEach(function(s) {
                var pid = s.procedure_id;
                if (!subsByProc[pid]) subsByProc[pid] = [];
                subsByProc[pid].push(s);
            });

            if (!procedures.length) { container.innerHTML = '<p>Незабаром з\\'явиться прайс-лист.</p>'; return; }

            var html = '<dl class="accordion">';
            procedures.forEach(function(proc) {
                var subs = subsByProc[proc.id] || [];
                var priceHtml = '';
                if (subs.length) {
                    var hasGender = subs.some(function(s) { return s.price_women || s.price_men; });
                    priceHtml = '<div style="margin-top:16px;"><h5>Вартість процедури:</h5>'
                        + (hasGender
                            ? '<table><thead><tr><th>Назва</th><th>Жінки</th><th>Чоловіки</th></tr></thead><tbody>'
                            : '<table><thead><tr><th>Назва</th><th>Ціна</th></tr></thead><tbody>');
                    subs.forEach(function(sub) {
                        var nameCell = sub.title;
                        if (sub.description) nameCell += '<br><small style="color:#888;">' + sub.description + '</small>';
                        var unit = sub.unit ? ' / ' + sub.unit : '';
                        var promo = sub.is_promo ? ' <span style="color:#c0a060;font-size:.8em;">(акція)</span>' : '';
                        function cell(val, oldVal) {
                            if (!val && val !== 0) return '—';
                            var s = formatPrice(val) + unit;
                            if (oldVal) s += '<br><del style="color:#999;font-size:.85em;">' + formatPrice(oldVal) + '</del>';
                            return s + promo;
                        }
                        var row;
                        if (hasGender) {
                            row = '<td>' + nameCell + '</td>'
                                + '<td>' + cell(sub.price_women || sub.price, sub.old_price_women || sub.old_price) + '</td>'
                                + '<td>' + cell(sub.price_men   || sub.price, sub.old_price_men   || sub.old_price) + '</td>';
                        } else {
                            row = '<td>' + nameCell + '</td><td>' + cell(sub.price, sub.old_price) + '</td>';
                        }
                        priceHtml += '<tr>' + row + '</tr>';
                    });
                    priceHtml += '</tbody></table></div>';
                }

                var meta = '';
                if (proc.duration) meta += '<p><strong>Тривалість:</strong> ' + proc.duration + '</p>';
                if (proc.recovery) meta += '<p><strong>Реабілітація:</strong> ' + proc.recovery + '</p>';
                var label = proc.title + (proc.is_featured ? ' <span style="color:#c0a060;font-size:.85em;">★</span>' : '');

                html += '<dt>'
                    + '<span class="link"><div>' + label + '</div></span>'
                    + '<div class="acc-icon-wrap parallax-wrap"><div class="acc-button-icon parallax-element"><i class="fa fa-arrow-right"></i></div></div>'
                    + '</dt>'
                    + '<dd class="accordion-content">'
                    + (proc.description || proc.short_description || '')
                    + meta + priceHtml
                    + '</dd>';
            });
            html += '</dl>';

            container.innerHTML = html;
            var $acc = $(container).find('dl.accordion');
            $acc.find('dd.accordion-content').slideUp(1).addClass('hide');
            $acc.on('click', 'dt', function() {
                $(this).addClass('accordion-active').next().slideDown(350).siblings('dd.accordion-content').slideUp(350).prev().removeClass('accordion-active');
                $(this).delay(500).queue(function() { ScrollTrigger.refresh(); $(this).dequeue(); });
            });
            $acc.on('click', 'dt.accordion-active', function() {
                $(this).removeClass('accordion-active').siblings('dd.accordion-content').slideUp(350);
                $(this).delay(500).queue(function() { ScrollTrigger.refresh(); $(this).dequeue(); });
            });
        }

        var base = DIRECTUS + '/items/';
        var pf = 'filter[status][_eq]=published&sort=order&limit=500';

        fetch(base + 'service_groups?fields=id,title,subtitle,description&filter[slug][_eq]=' + GROUP_SLUG + '&filter[status][_eq]=published')
            .then(function(r) { return r.json(); })
            .then(function(d) {
                var group = d.data && d.data[0];
                if (!group) return null;
                var titleEl = document.getElementById('group-title');
                var subtitleEl = document.getElementById('group-subtitle');
                if (titleEl) titleEl.textContent = group.title;
                if (subtitleEl && (group.subtitle || group.description)) subtitleEl.innerHTML = group.subtitle || group.description;
                return Promise.all([
                    fetch(base + 'service_procedures?fields=id,group_id,title,short_description,description,duration,recovery,is_featured&filter[group_id][_eq]=' + group.id + '&' + pf).then(function(r) { return r.json(); }),
                    fetch(base + 'service_subprocedures?fields=id,procedure_id,title,description,price,old_price,price_women,old_price_women,price_men,old_price_men,unit,is_promo&' + pf).then(function(r) { return r.json(); }),
                ]);
            })
            .then(function(results) {
                if (!results) return;
                renderProcedures(results[0].data || [], results[1].data || []);
            })
            .catch(function(e) { console.error('Service load error', e); });
    })();
    </script>"""

# ── Build new submenu for a given active slug ────────────────────────────────
def build_submenu(active_slug):
    lines = []
    for slug, _, nav_title in GROUPS:
        active = ' active' if slug == active_slug else ''
        lines.append(
            f'                                        <li><a class="ajax-link{active}" href="service-{slug}.html" data-type="page-transition">{nav_title}</a></li>'
        )
    return "\n".join(lines)

# ── Patch submenu in any HTML string ────────────────────────────────────────
OLD_SUB_PATTERN = re.compile(
    r'(?s)(<li><a class="ajax-link[^"]*" href="service[-\w]*\.html"[^>]*>.*?</li>\s*){2,}(?=\s*</ul>)',
)

def patch_submenu(html, active_slug):
    new_sub = build_submenu(active_slug)
    patched, count = OLD_SUB_PATTERN.subn(new_sub + "\n", html)
    return patched, count > 0

# ── Generate service pages ───────────────────────────────────────────────────
with open(os.path.join(WWW, "service01.html")) as f:
    base_html = f.read()

for slug, group_title, nav_title in GROUPS:
    html = base_html

    # Replace hero H1
    html = re.sub(r'<H1>[^<]*</H1>', f'<H1 id="group-title">{group_title}</H1>', html, count=1)

    # Replace hero description paragraph (first <p> in hero-caption inner div)
    html = re.sub(
        r'(<div class="text-align-center">\s*)<p>.*?</p>',
        r'\1<p id="group-subtitle"></p>',
        html, count=1, flags=re.DOTALL
    )

    # Replace the static accordion block with a dynamic container
    html = re.sub(
        r'<dl class="accordion has-animation">.*?</dl>',
        '<div id="services-container"></div>',
        html, count=1, flags=re.DOTALL
    )

    # Patch nav submenu with active on current slug
    html, _ = patch_submenu(html, slug)

    # Insert dynamic script before </body>
    js = JS_TEMPLATE.replace('__GROUP_SLUG__', slug)
    html = html.replace("</body>", f"\n{js}\n\n\n</body>")

    out_path = os.path.join(WWW, f"service-{slug}.html")
    with open(out_path, "w") as f:
        f.write(html)
    print(f"  ✓ service-{slug}.html")

# ── Patch nav in all other pages ─────────────────────────────────────────────
OTHER_PAGES = [
    "about.html", "blog.html", "contact-form.html", "contact.html",
    "index.html", "likari.html", "post.html", "post01.html",
    "price.html", "project01.html", "service01.html",
]

for fname in OTHER_PAGES:
    path = os.path.join(WWW, fname)
    if not os.path.exists(path):
        continue
    with open(path) as f:
        html = f.read()
    patched, changed = patch_submenu(html, None)
    if changed:
        with open(path, "w") as f:
            f.write(patched)
        print(f"  ✓ nav patched: {fname}")
    else:
        print(f"  – no change:   {fname}")

print("\nDone.")
