---
name: Optionele browsertests in Nix
description: Browserhulpmiddelen gescheiden houden van productie en de GCC-runtime voor greenlet.
---

De browser-testvereisten zijn optioneel en horen niet in de
productieafhankelijkheden. Controleer na installatie of de pakketvoorziening
ze daar onbedoeld heeft toegevoegd of onnodige Nix-pakketten heeft opgenomen.
Gebruik bij een ontbrekende libstdc++.so.6 voor greenlet de aanwezige
GCC-runtime alleen in het LD_LIBRARY_PATH van de testopdracht.

**Why:** de pakketinstallatie werkte, maar importeren van Playwright faalde
zonder GCC-runtime; de installatie wijzigde bovendien automatisch de
productievereisten en Nix-pakketlijst voor uitsluitend lokale browsertests.

**How to apply:** lees de testinstructies in het bestaande mobiele rapport
voordat je de browseromgeving opnieuw inricht. Zoek actuele Nix-paden in
plaats van een oude store-hash over te nemen. Browseremulatie bewijst geen
compatibiliteit met fysieke iOS-/Android-apparaten.

Laat de initiële menu-initialisatie en de zijpaneeltransitie uitlopen voordat
een browsertest toetsen naar een submenu stuurt. Alleen aanwezigheid van de
gegenereerde menuknop bewijst nog niet dat de focus stabiel is.

**Why:** te vroege toetsenbordinteractie gaf wisselende testfouten terwijl
dezelfde bediening na initialisatie wel werkte.

**How to apply:** synchroniseer menu-interactietests met de geïnitialiseerde
bediening en wacht op de paneeltransitie voordat de focus wordt verplaatst.

Een IntersectionObserver met drempel nul meldt niet noodzakelijk een sprong
van volledig onder naar volledig boven het viewport: beide standen zijn
niet-intersecterend.

**Why:** snelle programmatische navigatie sloeg de zichtbaarheidsupdate van
de vaste formaatbalk over, terwijl langzaam scrollen wel werkte.

**How to apply:** test ook directe scrollsprongen en herstel na navigatie.
Laat vaste bediening niet uitsluitend van een intersectieovergang afhangen.

Een filterbalk die bij vastzetten compacter wordt, moet zijn oorspronkelijke
ruimte in de documentstroom behouden als hij naar `position: fixed` gaat.

**Why:** zonder ruimtebehoud kan browser-scrollverankering de pagina terug
schuiven over de vastzetdrempel en de compacte weergave laten wisselen.

**How to apply:** controleer de overgang vlak rond de drempel, niet alleen
na ver doorscrollen. Laat updates van overlooppijlen bestaande schuifposities
intact; tijdelijk verbergen van pijlen kan de schuifpositie begrenzen.
