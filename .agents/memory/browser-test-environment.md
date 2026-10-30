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
