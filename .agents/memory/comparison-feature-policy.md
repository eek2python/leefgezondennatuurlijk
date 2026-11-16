---
name: Kenmerken in vergelijkingstabellen
description: Scheid features van material in de algemene vergelijkingskolom; rapporteer verlies van materiaalinformatie.
---

De gebruiker kiest voor `comparison_features` in de kolom Kenmerken van de
vergelijkingstabellen, met terugval op `features` wanneer het veld ontbreekt
of leeg is. Combineer dit niet automatisch met `material`.
Dit geldt ook voor de mobiele kenmerkenkolom. De aparte onderdelenvergelijking
voor Gourmetsets hoeft hiervoor niet te veranderen.

**Why:** de gecombineerde tekst herhaalt geregeld constructie- en coatinginformatie.
De gebruiker stemde in met scheiding en met een controle op informatieverlies.
De gebruiker voert `comparison_features` stapsgewijs in om de belangrijkste
kenmerken te tonen zonder lange, onoverzichtelijke lijsten.

**How to apply:** behoud `material` als afzonderlijk brongegeven. Controleer
bij wijzigingen welke relevante materiaal- of coatinginformatie niet in
`features` voorkomt en meld dat expliciet. Voeg niet stilzwijgend materiaal
weer toe aan features; dat zou de gekozen scheiding ongedaan maken.

Op mobiel worden maximaal vier ingevulde `comparison_features` onder elkaar
getoond. Verberg deze niet wanneer ze bij meerdere producten gelijk zijn.
Zonder ingevulde vergelijkingskenmerken blijft de bestaande compacte terugval
op één eigenschap uit `features` gelden. De desktopweergave blijft behouden.

**Why:** de gebruiker heeft ingestemd met maximaal vier bewust gekozen
kenmerken om de telefoonvergelijking nuttiger te maken zonder lange lijsten.

**How to apply:** houd de productnaam vast bij horizontaal schuiven en zorg
dat vergelijken ook rechtop werkt; kantelen mag geen vereiste zijn.
