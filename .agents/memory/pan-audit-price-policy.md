---
name: Formaatgebonden panprijzen
description: Scope van prijsgrenzen per diameter en set voor keramische en andere pannen
---
De gebruiker wil aparte auditprijsgrenzen voor keramische koekenpannen van 20, 24, 26, 28, 30 en 32 cm en sets van 20+24, 20+28, 24+28 en 20+24+28 cm.

**Why:** Prijsniveaus moeten binnen hetzelfde formaat worden vergeleken, niet met één vaste indeling voor alle keramische pannen.

**How to apply:** Sets niet behandelen als een losse pan wanneer de productdata ook een diameter voor de grootste pan bevat. Ontbrekende formaatconfiguratie rapporteren zonder impliciete fallback.

Voor keramische koekenpannen vraagt de gebruiker inmiddels expliciet om één
bron voor de publieke prijsuitleg, de afgeleide niveaus en de bestaande audit.
De bovengrenzen zijn inclusief: precies €40 valt bij 28 cm nog in €;
€40,01 valt in €€. Dit verandert geen opgeslagen prijzen of productselecties.
De overige pannencategorieën behouden hun bestaande openbare indeling en
grensgedrag; hun formaatconfiguratie blijft audit-only.

**Why:** de gebruiker heeft bij de contentactualisering voor keramische
koekenpannen gekozen voor het voorbeeld met inclusieve bovengrenzen.

**How to apply:** houd berekening en zichtbare prijsintervallen gelijk.
Onderhoud geen tweede prijsmodel in algemene content en verander andere
categorieën niet mee.
