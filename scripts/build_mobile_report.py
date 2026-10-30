"""Bundle measured browser results and screenshots as a self-contained report."""
import base64
import html
import json
import re
from pathlib import Path

OUT = Path("generated-artifacts/mobile-ux")
before = json.loads((OUT / "before.json").read_text())
after = json.loads((OUT / "after.json").read_text())
checks = json.loads((OUT / "checks.json").read_text())
hint = "Veeg horizontaal voor alle kolommen. Met het toetsenbord: gebruik de pijltjestoetsen."


def normalize(text):
    return re.sub(r"\s+", " ", text.replace(hint, "")).strip()


for key, original in before.items():
    changed = after[key]
    for field in ("links", "seo", "productCount", "tableCells"):
        assert original[field] == changed[field], (key, field)
    assert normalize(original["text"]) == normalize(changed["text"]), (key, "text")
    if key.startswith("1440"):
        for field in ("bodyFont", "heroHeight", "productMediaFloat", "sidebarWidth"):
            assert original[field] == changed[field], (key, field)
assert not checks["errors"]
assert all(not result["overflow"] for result in after.values())


def image(filename, label):
    data = base64.b64encode((OUT / filename).read_bytes()).decode()
    return f'<figure><img src="data:image/jpeg;base64,{data}" alt="{html.escape(label)}"><figcaption>{html.escape(label)}</figcaption></figure>'


sections = []
for title, stem in (
    ("Homepage — telefoon", "390-0"),
    ("Keramische vergelijking — telefoon", "390-1"),
    ("Productkaart — telefoon", "390-1-card"),
    ("Vershoudkaart — telefoon", "390-2-card"),
    ("Homepage — desktop", "1440-0"),
    ("Productkaart — desktop", "1440-1-card"),
):
    sections.append(f'<section><h2>{title}</h2><div class="pair">' +
                    image(f"before-{stem}.jpg", "Voor") +
                    image(f"after-{stem}.jpg", "Na") + '</div></section>')
sections.append('<section><h2>Menu — telefoon</h2><div class="pair">' +
                image("before-menu.jpg", "Voor") + image("after-menu.jpg", "Na") + '</div></section>')
sections.append('<section><h2>Horizontaal vergelijken</h2>' +
                image("after-table.jpg", "Na scrollen: productkolom blijft zichtbaar") + '</section>')
metrics = f"""
<h1>Mobiele gebruikerservaring: voor en na</h1>
<p>Gerichte verbetering van de bestaande website. Geen gewijzigde productgegevens,
geen nieuw ontwerp, geen publicatie.</p>
<h2>Gemeten weergave</h2>
<ul><li>Basistekst bij 390 px: {before['390-0']['bodyFont']} → {after['390-0']['bodyFont']}.</li>
<li>Homepagefoto bij 390 px: {before['390-0']['heroHeight']:.0f} → {after['390-0']['heroHeight']:.0f} px.</li>
<li>{len(checks['matrix'])} geslaagde pagina-/breedtecontroles; geen pagina-overloop of JavaScript-fouten.</li>
<li>Voor/na identiek: hoofdinhoud, productaantallen, links, tabelcellen, metadata en structured data.</li>
<li>Desktop: basisletter, fotohoogte, product-float en zijbalkbreedte behouden.</li></ul>
<h2>Uitgevoerde interactietests</h2><ul>""" + "".join(
    "<li>" + html.escape(test) + "</li>" for test in checks["interactions"]) + """</ul>
<h2>Django-controle</h2><p>Systeemcontrole geslaagd. 472 van 473 tests geslaagd.
Dezelfde bestaande Ninja-prijsafwijking faalde ook vóór deze wijzigingen (toen 469 van 470 geslaagd);
die productdata is volgens de opdracht niet aangepast.</p>
<h2>Beperkingen</h2><p>Headless Chromium/Linux, responsive en touch-emulatie.
Geen echte iOS/Android-, Safari/Firefox- of schermlezertest. 200% tekst en equivalente
zoom-reflow gecontroleerd; geen volledige test van native OS-/browservergroting.
Geen conversie-, snelheids-, Core Web Vitals- of SEO-effecten gemeten.</p>
<p>Voorbeelden hieronder: 390×844 en 1440×1000. Screenshots van de uitgangssituatie gebruiken
de oorspronkelijke stijlen en menubediening uit Git op dezelfde routes en gegevens.
Het volledige technische verslag staat in reports/mobile-ux.md.</p>
"""
document = """<!doctype html><html lang="nl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mobiele gebruikerservaring — voor/na</title><style>
*{box-sizing:border-box}body{font:16px/1.6 system-ui,sans-serif;color:#26363c;background:#f4f7f7;max-width:1150px;margin:auto;padding:24px}
h1,h2{line-height:1.25}h1{font-size:2rem}section{background:white;padding:20px;border:1px solid #ccd8da;border-radius:8px;margin:24px 0}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0;min-width:0}img{display:block;max-width:100%;max-height:900px;width:auto;margin:auto}
figcaption{font-weight:700;text-align:center;padding:12px}li{margin-bottom:8px}
@media(max-width:640px){body{padding:16px}.pair{grid-template-columns:1fr}}
</style>""" + metrics + "".join(sections) + "</html>"
(OUT / "rapport.html").write_text(document)
print(f"Content/link/SEO/table/desktop invariance passed for {len(before)} snapshots.")
print(OUT / "rapport.html")
