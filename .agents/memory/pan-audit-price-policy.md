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

**How to apply:** houd berekening en zichtbare prijsintervallen gelijk en
verander andere categorieën niet mee.

De gebruiker onderhoudt inmiddels de openbare prijsuitleg per formaat en
pannenset in de content voor zowel RVS als keramische koekenpannen. Toon die
teksten letterlijk voor de geselecteerde maatcombinatie; genereer geen
vervangende prijsuitleg uit de rekenconfiguratie.

**Why:** de gebruiker heeft voor beide categorieën zelf de prijsniveaus aan
de content toegevoegd en vraagt om dezelfde formaatgebonden weergave.

**How to apply:** deze keuze betreft de openbare uitleg. Wijzig daarmee niet
stilzwijgend de productprijsniveaus of hun berekening. Eventuele afwijkingen
tussen redactionele uitleg en berekening moeten apart worden beoordeeld.

Voor kleurvarianten van keramische koekenpannen geldt voor het prijsniveau:
eerst de eigen `reference_price`, anders de gedeelde productreferentieprijs,
en pas zonder beide referenties de eigen actuele prijs. De gebruiker bevestigt
dat de productreferentieprijs voor alle bijbehorende kleuren mag worden gebruikt.
Leen nooit een actuele prijs of een referentieprijs van een andere kleur.

**Why:** tijdelijke aanbiedingen mogen het prijsniveau niet bepalen en
referentieprijzen zijn niet altijd afzonderlijk per kleur ingevoerd.

**How to apply:** dit is alleen een uitzondering voor de afgeleide prijsindeling
van kleuren, niet voor actuele prijzen, links of vorm-/inhoudsvarianten.
