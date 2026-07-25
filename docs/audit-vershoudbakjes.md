# Audit vershoudbakjes — productdata & productblokken

Datum: 25 juli 2026. Scope: `products/products_vershoudcontainers.py`,
rankings, templates en gebruiksinformatie ("Geschikt voor"). Binnen deze
audit zijn rankings, awards, prijzen, affiliate-links en de recent
bijgewerkte 3-delige afbeeldingen niet gewijzigd. (De werkkopie bevat ook
eerder goedgekeurd variantwerk uit dezelfde sessie — o.a. BergHOFF/LEO- en
Igluu-varianten met eigen prijzen/links; dat valt buiten deze audit.)

## 1. Nieuwe gebruiksinformatie-structuur

Producten (en optioneel varianten) hebben een `usage`-dict:

```python
"usage": {
    "oven":       {"container": True,  "lid": False, "note": "Alleen het glazen bakje"},
    "microwave":  {"container": True,  "lid": True,  "note": "Ventiel openen"},
    "freezer":    {"container": True,  "lid": None,  "note": None},
    "dishwasher": {"container": None,  "lid": None,  "note": None},
}
```

Regels (`utils/usage_helpers.py`):
- `None` = onbekend en wordt **nooit** als "Nee" getoond; de rij verdwijnt.
- `container=True, lid=False` → "Ja, alleen zonder deksel" (of de note).
- `container=True, lid=None` → "Bakje: ja" (dekselstatus onbekend).
- Varianten erven de productbasis en mogen per veld overschrijven
  (`merge_usage`); wissel van variant actualiseert de rijen client-side
  (`static/assets/js/variant-selector.js`).
- Weergave via `build_usage_display`; schema bewaakt door `validate_usage`
  en de importvalidator.

Usage toegekend op basis van bestaande productdata (verplaatst uit
pros/cons/description; niets bijverzonnen): Pyrex Cook & Store enkel,
IKEA 365+, Mepal EasyClip (enkel + 3-delig), Lock&Lock enkel, Luminarc
PureBox (enkel/3/5), Igluu (3/5), Pyrex Cook & Heat (3/5), Bormioli
Frigoverre (3/5). Geen usage voor de gekopieerde/onbetrouwbare records
(BergHOFF, Glasslock, KitchenBrothers, OXO) — zie §4.

## 2. Structurele migraties

- **IKEA 365+** en **Mepal EasyClip enkel**: legacy "vorm"-varianten die
  eigenlijk inhoudsmaten waren, gemigreerd naar
  `variant_selectors: [{"key": "capacity", "label": "Inhoud"}]` met
  `options`/`option_labels`. Geen inhoudsmaten meer in `shape`.
- Literlabels genormaliseerd naar Nederlandse komma's: "1,2 L", "1,5 L",
  "2,25 L", "1,22 L", "1,97 L", "1,1 L".
- `pyrex_cook_store_3delig` → **`pyrex_cook_store_enkel`** (het is één
  bakje van 800 ml); ranking "single" bijgewerkt.
- Luminarc enkel: variant-id `630-ml-rectangle` → `820-ml-rectangle`
  (capaciteit is 820 ml).

## 3. Veilig gecorrigeerde fouten

- Materiaal: "Borosilicaat glas" → "Borosilicaatglas" (9×), ook in pros.
- "silicone afdichting/ring" → "siliconen …"; feature "Klikdeksel +
  silicone" → "Klikdeksel met siliconen afdichting".
- `award: ""` → `award: None` (8×); `price: "65.00"` → `65.00`.
- Bormioli 5-delig: pro en verdict zeiden "3-delige" → "5-delige".
- Igluu 5-delig: pro "Drie verschillende formaten" verwijderd (set bevat
  5 gelijke bakjes van 950 ml); basisafbeelding verwees naar het niet
  bestaande `igluu-5delig.jpg` → nu `igluu-5delig-rond.webp` (bestaat, is
  de defaultvariant).
- BergHOFF: beschrijving noemde "de bekende vierzijdige
  Lock&Lock-sluiting" (verkeerd merk) → "een vierzijdige kliksluiting"
  (alleen merkverwijzing verwijderd, geen nieuwe claim).
- Pyrex Cook & Heat: feature "klikdeksel" → "Klikdeksel".
- Redactieregels toegepast: max 3 pluspunten / 2 minpunten; generieke
  gebruiksclaims verplaatst naar `usage`; verboden frasen verwijderd
  ("Nederlands kwaliteitsmerk", "Controleer per set of deksels volledig
  lekvrij zijn").

## 4. Nog handmatig verifiëren (NIET zelf aangepast)

- **oxo_good_grips_smart_seal_6delig** (bewust ongerankt): volledig
  gekopieerde Glasslock/Luminarc-data, inclusief niet-bestaande afbeelding
  `glasslock-3delig.jpg`, 3 capaciteiten bij een "6-delige" naam.
- **kitchenbrothers_5delig**: materiaal "Borosilicaatglas" botst met
  beschrijving "gehard glas" (gekopieerde Luminarc-tekst).
- **glasslock_3delig** en **berghoff_perfect_seal**: beschrijving/verdict/
  pluspunten identiek aan een ander merk.
- **ikea_365+_enkel**: affiliate-URL van de 600 ml-variant noemt "740-ml".
- **luminarc_purebox_5delig**: beschrijving identiek aan KitchenBrothers.
- **igluu_meal_prep_5delig**: rechthoek-variant mist capacities en echte
  data (bestaande TODO's); Igluu vierkant-variant idem (3-delig).
- Lock&Lock 630 ml / 1 L varianten: TODO's blijven wachten op echte data.

## 5. Validator

`products/validators_vershoudbakjes.py::validate_vershoudbakjes` draait
bij het importeren van `products/views.py`:
- **Raist** bij structurele fouten: onbekende rankingkeys, dubbele
  variant-ids/optiecombinaties, ≠1 defaultvariant, ongeldig award of
  usage-schema.
- **Logt waarschuwingen** (wijzigt nooit zelf feiten): afwijkende
  materiaalschrijfwijze, niet-numerieke prijs/capaciteit, capaciteitsaantal
  vs. "-delig", inhoudsmaat in `shape`, punt-literlabels, ontbrekende
  afbeeldingen, placeholders, identieke teksten tussen merken,
  merkconflicten, >3 pros / >2 cons.
- Huidige stand: 13 waarschuwingen, alle terug te voeren op §4 plus de
  bewust afwijkende IKEA-slug (`ikea-365-plus-enkel` bij key
  `ikea_365+_enkel`).

## 6. Tests

`products/test_usage_vershoudbakjes.py` (17 tests) dekt spec §13:
weergaveregels, verbergen van onbekende waarden, overerving en
variant-overrides, paginaweergave + variant-payload, redactieregels,
komma-labels, geen inhoud in `shape`, unieke ids/combos, één default,
behoud van de 3-delige afbeeldingen en werkende bestaande selectors.
Volledige suite: **187 tests, allemaal groen** (`python manage.py test products`).

N.B. Drie bestaande formaatfilter-tests verwachtten aantallen van vóór de
laatste catalogusuitbreiding (3 "kleine" enkele bakjes); die verwachtingen
zijn geactualiseerd naar de huidige catalogus (2). Dit stond los van deze
audit (faalde ook met de oude data).
