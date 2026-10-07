# Prijsgrenzen voor audits

Alle configuratie staat in `utils/pricing.py`. Een prijs exact op een grens
valt in het volgende niveau. Audits melden afwijkingen, maar wijzigen geen
productgegevens. Nieuwe grenzen gelden voor nieuwe runs, niet voor oude rapporten.

## Keramische koekenpannen

- `KERAMISCHE_KOEKENPANNEN_PRICE_RANGES`: losse pannen, sleutel = diameter in cm.
- `KERAMISCHE_KOEKENPANNENSETS_PRICE_RANGES`: sets, sleutel = tuple van diameters.
- `PAN_AUDIT_PRICE_RANGES`: koppelt deze tabellen aan de categorie `koekenpannen`.

De audit leest `diameter` voor een losse pan en `diameters` voor een set.
Een set met zowel `diameter: 28` als `diameters: [20, 28]` gebruikt de setgrenzen.
Setdiameters worden gesorteerd; `[28, 20]` gebruikt dus ook `(20, 28)`.
Ontbrekende, ongeldige of niet-geconfigureerde formaten geven een waarschuwing
en geen berekend niveau. Er is geen fallback naar de grenzen voor losse pannen.

## Andere pannengroepen toevoegen

1. Definieer in `utils/pricing.py` eigen tabellen met je gekozen grenzen:

```python
RVS_KOEKENPANNEN_PRICE_RANGES = {
    # Voeg je diameters toe met deze structuur:
    # 24: (
    #     (Decimal("jouw eerste grens"), "€"),
    #     (Decimal("jouw tweede grens"), "€€"),
    #     (Decimal("jouw derde grens"), "€€€"),
    #     (None, "€€€€"),
    # ),
}

RVS_KOEKENPANNENSETS_PRICE_RANGES = {
    # Zelfde structuur, maar met bijvoorbeeld (20, 28) als sleutel.
}
```

2. Voeg de koppeling toe **binnen** `PAN_AUDIT_PRICE_RANGES`:

```python
"rvs-koekenpannen": {
    "single": RVS_KOEKENPANNEN_PRICE_RANGES,
    "sets": RVS_KOEKENPANNENSETS_PRICE_RANGES,
},
```

Gebruik de exacte categoriekey van het auditdashboard, bijvoorbeeld
`hapjespannen`, `wokpannen`, `rvs-koekenpannen`,
`koolstofstalen-koekenpannen` of `gietijzeren-koekenpannen`.
Registreer alleen categorieën waarvoor je grenzen hebt ingevuld; een lege
formaatconfig schakelt de bestaande categoriebrede auditgrenzen uit.
Producten moeten numerieke `diameter` of `diameters` hebben.

3. Herstart de server en voer een nieuwe prijsaudit uit:

```bash
python manage.py audit_products --audit price_levels --category rvs-koekenpannen
```

Of kies in `/admin/product-audits/` de controle **Prijzen en prijsniveaus**,
selecteer de categorie en klik op **Audit uitvoeren**. Onderaan de run staat
de **Interne prijstabel (niet publiek)**.

Deze formaatconfig is uitsluitend voor audits. De openbare prijsweergave
blijft de bestaande categoriebrede regels in `PRICE_RANGE_THRESHOLDS` gebruiken.
