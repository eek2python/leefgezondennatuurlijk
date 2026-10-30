# Mobiele gebruikerservaring — voor/na

## Afbakening

Gerichte verbeteringen aan de bestaande Django-site; geen nieuw ontwerp, aparte
app, nieuwe afbeeldingen of gewijzigde productgegevens. De broncode van
productkeuzes, prijsberekening, centrale linkresolutie en variantprojectie is
ongewijzigd. Er is niets gepubliceerd.

## Verbeteringen

- Op telefoons is de basisletter 16 px in plaats van circa 13,3 px
  (en 12 px op de smalste schermen). Secundaire tekst heeft een ondergrens van
  14 px. Relatieve tekstmaten ondersteunen vergroting.
- Browserzoom is toegestaan. Donkerdere tekst, links en knoppen behouden
  turquoise als merkkleur. Gecontroleerde contrastverhoudingen op wit:
  gewone tekst `#59636a` **6,14:1**, links en primaire knoppen `#087586`
  **5,39:1**. Badgekleuren hebben leesbare tekst. Dit is geen volledige
  toegankelijkheidsaudit.
- Mobiele knoppen, filters en variantkeuzes hebben minimaal circa 44 px
  aanraakhoogte. Kleurswatches krijgen 44×44 px klikruimte zonder grotere
  productfoto; een vinkje markeert de selectie. Formaat- en uitvoeringskeuzes
  gebruiken naast kleur ook onderstreping/lettergewicht.
- Productbeelden staan op telefoons boven de volledige tekstbreedte.
  Productinformatie, beoordelingen, beschikbaarheidsmeldingen en acties blijven
  aanwezig. De decoratieve homepagefoto blijft dezelfde maar is compacter;
  de tekst kan bij vergroting de hoogte laten meegroeien.
- De reeds aanwezige uitvoeringsknoppen op productdetailpagina’s waren nog
  niet aangesloten op de bestaande variantbediening. Detail en overzicht
  gebruiken nu dezelfde selectorpartial en dezelfde serverpayload; de
  product- en linklogica is niet gewijzigd.
- Vergelijkingstabellen houden alle cellen. Een eigen horizontaal scrollgebied,
  zichtbare instructie en vaststaande productkolom op telefoon maken vergelijken
  bruikbaar. Het gebied is met het toetsenbord bereikbaar en bedienbaar.
- Het menu heeft een Nederlandse naam en open/dicht-status. Enter/Spatie,
  Tab/Shift+Tab en Escape werken. Gesloten menu-inhoud is niet focusbaar;
  bedekte pagina-inhoud evenmin. Sluiten brengt focus terug naar de menuknop.
- Vaste filters beginnen onder de menuknop. Ankerafstand volgt de werkelijke
  filterhoogte. Een filter dat op korte of vergrote schermen te veel ruimte
  inneemt, scrollt normaal weg. Desktop behoudt de brede productpresentatie.

## Bewijs en tests

De afzonderlijk geleverde HTML-versie bevat de voor/na-afbeeldingen en de
uitkomsten van de browsercontroles. Ruwe resultaten en afbeeldingen staan
lokaal in `generated-artifacts/mobile-ux/` (bewust niet in Git of deployment).

Uitgangssituatie en resultaat zijn vastgelegd op **390×844** en
**1440×1000**, voor homepage, keramische vergelijking, vershoudbakjes,
airfryers en blogs. De uitgangssituatie gebruikt de oorspronkelijke CSS,
menuscript en menumarkup uit de Git-basis, zonder de nieuwe hulpscriptcode.
De routes, huidige productinhoud en database zijn in beide opnamen gelijk.

Herhaalbare browsercontrole: `scripts/check_mobile_ux.py`.

- **104** pagina-/breedtecombinaties zonder pagina-overloop; geen
  JavaScript-fouten. Negen kleurkeuzes, 23 uitvoeringskeuzes op
  overzichtspagina’s en drie op productdetail zijn gecontroleerd.
- Bij 390 px nam de hoogte van de homepagefoto af van circa **464 naar
  220 px**, met behoud van afbeelding en tekst.
- Schermbreedtes **320, 360, 390, 430, 768, 1024, 1440 en 1920 px**.
- Homepage, categorieën, panmaat, pannenset, compact/XL/dual-airfryers,
  losse/3-delige/5-delige bakjes, productdetail en blogartikel.
- Menu, toetsenbordfocus, submenu, navigatie, touch-emulatie, variantknoppen,
  resolutie van bestaande bestemmingen, formaatfilters en beschikbaarheid.
- De geteste echte variantkeuzes hadden allemaal een bestemming. De toestand
  zonder link is daarom aanvullend met een geïsoleerde browsertestfixture
  gecontroleerd: melding zichtbaar, oude `href`/`rel` verwijderd en herstel na
  terugkiezen. De catalogus en database zijn daarvoor niet aangepast.
- Horizontaal scrollen met pijltjestoetsen en productnaam in beeld.
- Springdoelen in portret/landschap en bij 200% tekstvergroting, inclusief een
  kort scherm; 200%-equivalente reflow met een halve CSS-viewport en dubbele
  pixelschaal.
- Echte 404-status voor onbekend product en onbekend airfryerformaat.
- Voor/na-vergelijking van hoofdinhoud, links, tabelcellen, metadata,
  structured data, productaantallen en desktop-layoutkenmerken.

`python manage.py check` slaagt. De volledige Django-testreeks bevat
**473 tests: 472 slagen, één bestaande fout blijft staan**:
`products.tests.VariantAuditCommandTests.test_airfryer_variant_data_has_no_known_swatch_warnings`.
De fout stond ook vóór de wijzigingen in de reeks van 470 tests:
Ninja Crispi heeft een productniveauprijs van 109 tegenover 135 voor de
defaultswatch Marineblauw. Deze productdatafout valt expliciet buiten de opdracht.
De foutmelding bij de opzettelijk kapotte audit is een bestaande geslaagde
foutafhandelingstest, geen extra mislukte test.

## Beperkingen

Automatisch getest met headless Chromium op Linux en telefoon-/touch-emulatie.
Er zijn **geen echte iPhone-/Android-, Safari-, Firefox-, VoiceOver- of
TalkBack-tests** uitgevoerd. De reflow- en tekstvergrotingschecks zijn geen
claim dat alle native browserzoom- en OS-tekstinstellingen op echte apparaten
zijn getest. Er zijn geen Core Web Vitals, conversie-effecten, snelheidseffecten,
SEO-effecten of echte bezoekersresultaten gemeten.

## Aanvullende controle na previewfeedback

De sterren van beoordelingen blijven nu op één regel, ook binnen de gedeeltelijk
gevulde laag; de oorspronkelijke scores en vulpercentages zijn behouden.
De drie uitvoeringskeuzes staan onder “Kies uitvoering:” in plaats van naast
het label. Andere formaatselectors zijn niet gewijzigd.

`scripts/check_rating_filters.py` controleert dit op 320, 390, 768 en 1440 px
op drie categoriepagina’s (12 combinaties), plus 200% tekstvergroting en het
kiezen van een 3-delige uitvoering. Deze controles en de drie gerichte
Django-toegankelijkheidstests slagen. De bijgewerkte weergave is visueel
gecontroleerd in Chromium.

## Opnieuw uitvoeren

De toepassing gebruikt de bestaande workflow. Browserhulpmiddelen staan
afzonderlijk in `requirements-browser.txt`, niet in de productieafhankelijkheden.
Installeer die met de pakketvoorziening van de werkruimte. Het capturescript
zoekt de aanwezige Nix Chromium-binary; elders kan die locatie verschillen.
Als `greenlet` in Nix `libstdc++.so.6` niet vindt, voeg de `lib`-map van de
aanwezige GCC-runtime toe aan `LD_LIBRARY_PATH` voor de testopdracht.

```sh
python manage.py check
python manage.py test --noinput
python scripts/check_mobile_ux.py
MOBILE_CAPTURE_STAGE=before python scripts/mobile_capture.py
MOBILE_CAPTURE_STAGE=after python scripts/mobile_capture.py
python scripts/build_mobile_report.py
```
