# Canonical- en indexeringsaudit — 7 oktober 2026

## Audit vóór wijzigingen

Gewenste primaire hostname: `https://leefnatuurlijkengezond.nl` (zonder www).

### Live bevindingen

- `https://leefnatuurlijkengezond.nl/wokpannen/` → 200.
- Dezelfde HTTPS-URL met www → 301 naar de equivalente non-www-URL.
- Canonical en `og:url` in de non-www-HTML gebruiken ten onrechte www.
- `/sitemap.xml` → 200, geldige XML, 274 URL's; alle 274 gebruiken www.
- RVS, koolstofstaal en gietijzer zijn al in de sitemap opgenomen.
- `/robots.txt` → 200, `Allow: /`, maar sitemapverwijzing gebruikt www.
- HTTPS-www behoudt pad en querystring bij de 301 naar HTTPS-non-www.
- HTTP-www → 301 HTTPS-www → 301 HTTPS-non-www: bestaande tweestapsketen.

De live redirect bevestigt non-www als eindhost. Er is geen aanwijzing dat
de productiehost bewust www als eindhost gebruikt; de oude projectdocumentatie
en applicatiecode beschrijven wel www en zijn dus inconsistent met productie.

### Vindplaatsen en besluit

| Bestanden | Bevinding | Veilige aanpassing |
|---|---|---|
| `templates/index.html`, `koekenpannen.html`, `rvs-koekenpannen.html`, `koolstofstaal-koekenpannen.html`, `gietijzeren-koekenpannen.html`, `hapjespannen.html`, `wokpannen.html`, `snijplanken.html`, `airfryers.html`, `vershoudcontainers.html`, `over_ons.html`, `hoe_wij_beoordelen.html`, `privacy.html`, `product_detail.html` | Hardcoded www in canonical/social metadata en eventuele eigen absolute URL's | Eigen origin vervangen door centrale templatevariabele; paden en teksten behouden |
| `blogs/templates/blogs/blogoverzicht.html`, `koken-zonder-schadelijke-stoffen.html`, `pfas-in-huis.html`, `koolstofstaal-vs-gietijzer-koekenpan.html`, `welke-maat-koekenpan.html`, `rvs-pan-bakken-zonder-aanbakken.html`, `greenpan-barcelona-vs-demeyere-industry-5.html`, `beste-koekenpan-inductie-pfas-vrij.html`, `is-keramische-coating-veilig.html`, `internal/keramische-vs-rvs-koekenpan.html` | Hardcoded www in canonical/OG/Twitter | Dezelfde centrale origin gebruiken |
| `products/views.py` | www-breadcrumbs en airfryer-origin; Product-afbeelding gebruikt requesthost | Centrale helper voor eigen absolute URL's |
| `blogs/views.py` | www in breadcrumbs, Article-image en mainEntityOfPage | Centrale helper |
| `LeefNatuurlijkenGezond/sitemap_views.py` | Hardcoded www-BASE_URL | Centrale helper; bestaande URL-selectie behouden en toetsen op redirects/duplicaten |
| `templates/robots.txt` | www-sitemap | Centrale templatevariabele |
| `LeefNatuurlijkenGezond/settings.py` | Beide hosts in CSRF-allowlist; nog geen centrale SITE_URL | SITE_URL toevoegen; CSRF-hosts behouden voor compatibiliteit |
| `LeefNatuurlijkenGezond/context_processors.py` | Alleen analytics-context | Centrale origin beschikbaar maken in templates |
| `blogs/tests.py`, `products/tests.py` | Oude www-verwachtingen | Verwachtingen afstemmen op nieuwe non-www-strategie |
| `replit.md` | Oude www-instructie | Vervangen door expliciete non-www-strategie |

### Overige controles

- Geen `django.contrib.sites`: het Sites-framework is niet actief.
- `django.contrib.sitemaps` is geïnstalleerd, maar de actieve route
  `/sitemap.xml` gebruikt de eigen `sitemap_xml`-view, geen Sitemap classes.
- Sitemapcategorieën omvatten alle gevraagde groepen plus airfryer XL/dual;
  blogs komen uit de actieve blogregistry, producten uit de unieke slugregistry.
- Geen query-/filtervarianten, admin- of technische pagina's in die selectie.
- Canonicals van filters blijven bewust de bestaande basispagina aanwijzen.
- Named routes gebruiken trailing slashes; APPEND_SLASH is Django's standaard
  True via CommonMiddleware. `/sitemap.xml` en `/robots.txt` zijn bewuste
  bestandachtige uitzonderingen.
- Geen hostname-redirectmiddleware of www-redirectroute gevonden in Django.
- `.replit` bevat geen hostname-redirect; geen Render Blueprint gevonden.
- Geen andere hostnamebron in custom template tags of context processors.
- Geen SITE_URL, BASE_URL, DOMAIN, CANONICAL_HOST of DJANGO_SITE_DOMAIN
  geconfigureerd in de gecontroleerde Replit-ontwikkelomgeving.
- Render-dashboard, productievariabelen en DNS/proxyregels zijn niet
  toegankelijk vanuit deze audit. De precieze externe redirectregel is
  daarom niet bewezen; responsheaders tonen Cloudflare/Render-infrastructuur.
- Externe fabrikant-, affiliate- en social URLs worden niet aangepast.

## Redirects en handmatige productieacties

Geen Django-redirect toevoegen: productie voert HTTPS-www → non-www al uit.
Controleer in Render **Settings → Custom Domains** dat beide hosts naar
de juiste service wijzen en de non-www-host de definitieve bestemming blijft.
Als een DNS/proxyprovider redirectregels beheert, controleer die daar ook.

Maak HTTP-www desgewenst rechtstreeks 301/308 naar HTTPS-non-www,
met behoud van volledig pad en querystring. Dit kan niet via Django worden
opgelost als de eerste HTTPS-redirect vóór Django plaatsvindt. DNS-records
alleen voeren geen HTTP-redirect uit.

Publiceer de gewijzigde applicatie op Render. Controleer daarna opnieuw
HTML, sitemap, robots en de vier HTTP/HTTPS-hostcombinaties. Deze lokale
wijzigingen passen productie niet automatisch aan.

In Google Search Console:

1. Dien `https://leefnatuurlijkengezond.nl/sitemap.xml` in bij de passende
   domeinproperty of non-www HTTPS-URL-prefixproperty.
2. Inspecteer de non-www categorie-URL's met de live-test en vraag zo nodig
   herindexering aan.
3. Een www-URL met status "Page with redirect" is verwacht: de non-www
   eindpagina moet worden geïndexeerd, niet de redirect-URL.
4. Canonicalkeuze en indexering kunnen pas na hercrawlen veranderen;
   technisch correcte signalen garanderen geen opname in Google's index.

## Uitgevoerde wijzigingen en verificatie

- `LeefNatuurlijkenGezond/settings.py`: centrale `SITE_URL` en nieuwe contextprocessor.
- `LeefNatuurlijkenGezond/context_processors.py`: origin beschikbaar in templates.
- `LeefNatuurlijkenGezond/site_urls.py` (nieuw): gedeelde absolute-URL-helper.
- `products/views.py`: breadcrumbs, airfryercanonical en Product-afbeeldingen
  gebruiken de publieke origin, niet de requesthost.
- `blogs/views.py`: breadcrumbs en Article-URLs gebruiken dezelfde helper.
- `LeefNatuurlijkenGezond/sitemap_views.py`: sitemaplocaties via dezelfde helper.
- De 25 hierboven genoemde HTML/robots-templates: alleen eigen origin aangepast;
  SEO titles, descriptions, content, links naar externe sites en styling behouden.
- `products/tests.py`, `blogs/tests.py`: non-www-verwachtingen.
- `LeefNatuurlijkenGezond/tests_canonical_urls.py` (nieuw): sitebrede regressietests.
- `replit.md`: huidige non-www-hostnamestrategie.
- `.local/url-structure-audit.md`: historische www-aanbeveling als achterhaald
  gemarkeerd; het oude auditrapport blijft als historische momentopname bewaard.
- Dit rapport: inventaris, bevindingen, wijzigingsoverzicht en handmatige acties.

Resultaten:

- `python manage.py check`: geen problemen.
- `python manage.py test LeefNatuurlijkenGezond.tests_canonical_urls blogs products.tests`:
  alle 257 tests geslaagd.
- Alle 274 sitemaplocaties lokaal getest: HTTP 200 zonder redirect,
  exact één overeenkomende HTTPS-non-www-canonical en `og:url`, geen noindex.
- Alle negen actieve blogs en alle belangrijke categorieën aanwezig.
- Sitemap geldige XML, uitsluitend unieke non-www-URLs, geen queryvarianten.
- Filters behouden de bestaande basiscanonical.
- Metadata en JSON-LD zijn onafhankelijk van www-/preview-requesthosts.
- Bestaande trailing-slashredirect `/wokpannen` → `/wokpannen/` behouden.
- Draaiende ontwikkelapp na herstart: `/wokpannen/`, `/sitemap.xml`,
  `/robots.txt` geven 200; canonical/OG/robots/sitemap bevestigen non-www.
- Screenshot van `/wokpannen/` toont een normaal geladen pagina.
- Diffcontrole bevestigt dat de 25 templates uitsluitend de eigen origin
  veranderen; productdata, rankings, contentbestanden en styling niet gewijzigd.

### Bewust resterende verwijzingen naar de oude www-host

- `LeefNatuurlijkenGezond/settings.py`: CSRF-allowlist behoudt beide
  productiehosts; dit declareert geen canonical en veroorzaakt geen redirect.
- `LeefNatuurlijkenGezond/tests_canonical_urls.py`: legacy-host als negatieve
  testinput, zodat www niet terugkeert in metadata of sitemap.
- `.local/url-structure-audit.md`: vier verwijzingen in een historisch
  auditrapport; expliciet gemarkeerd als achterhaald, niet uitvoerbaar.
- De oorspronkelijke bijlage en automatisch opgeslagen agenttranscripten
  bevatten historische/gevraagde voorbeelden; geen actieve websitebestanden
  en niet aangepast.
- Dit auditrapport beschrijft de oude hostname bewust; geen publieke output.

De Render-publicatie en externe redirectconfiguratie zijn tijdens de lokale
correctie niet gewijzigd. Destijds bleef de live site de oude signalen leveren
tot publicatie. De onderstaande nacontrole vervangt die historische livestatus.

## Live nacontrole na Render-publicatie — 7 oktober 2026

Controle voltooid om **19:18:49 UTC**. Rechtstreekse openbare GET-verzoeken,
zonder account of deploymentwijzigingen. De centrale origin in de huidige
instellingen is `https://leefnatuurlijkengezond.nl`.

### Publicatievoorwaarde bevestigd

Vóór de verdere controle zijn de live wokpannen-HTML, sitemap en robots.txt
opgevraagd. Alle drie bevatten de nieuwe non-www-signalen. Daarmee is de
gevraagde wijziging aantoonbaar live; dit bewijst niet welke commit op Render
draait. De responsheaders vermelden Cloudflare en een Render/gunicorn-origin.
Deze audit heeft zelf niets gepubliceerd.

### Paginaresultaten

**Alle 26 gecontroleerde pagina's slagen:** HTTP 200 zonder redirect, exact
één canonical naar de eigen HTTPS-non-www-URL en exact één overeenkomende
`og:url`. Geen `noindex`/`none` in robots-meta of `X-Robots-Tag`.
Robots.txt staat toegang voor algemene crawlers, Googlebot en Bingbot toe.

| Groep | Gecontroleerde paden |
|---|---|
| Homepage | `/` |
| Categorieën (11) | `/koekenpannen/`, `/rvs-koekenpannen/`, `/koolstofstalen-koekenpannen/`, `/gietijzeren-koekenpannen/`, `/hapjespannen/`, `/wokpannen/`, `/snijplanken/`, `/airfryers/`, `/airfryers/xl/`, `/airfryers/dual/`, `/vershoudcontainers/` |
| Blogoverzicht | `/blogs/` |
| Alle negen blogs | `/blogs/beste-koekenpan-inductie-pfas-vrij/`, `/blogs/greenpan-barcelona-vs-demeyere-industry-5/`, `/blogs/is-keramische-coating-veilig/`, `/blogs/keramische-vs-rvs-koekenpan/`, `/blogs/koken-zonder-schadelijke-stoffen/`, `/blogs/koolstofstaal-vs-gietijzer-koekenpan/`, `/blogs/pfas-in-huis/`, `/blogs/rvs-pan-bakken-zonder-aanbakken/`, `/blogs/welke-maat-koekenpan/` |
| Informatief | `/over-ons/`, `/hoe-wij-beoordelen/`, `/privacy/` |
| Productsteekproef | `/product/be-living-28/` |

De publieke wokpannenpagina is daarnaast visueel gecontroleerd en laadt normaal.
Indexeerbaarheid betekent hier: geen technische blokkade in de gecontroleerde
HTTP-respons, metadata en robots.txt. Het is geen bewijs van Google-indexering.

### Sitemap en robots

- `/sitemap.xml`: HTTP 200, `application/xml`, geldige XML met de juiste
  sitemap-namespace en een `urlset`.
- **274 unieke locaties**, allemaal met de centrale HTTPS-non-www-origin;
  geen duplicaten, querystrings of fragmenten.
- Verdeling: 16 vaste pagina's, negen blogs en 249 productpagina's.
- De 25 niet-productpagina's en één product zijn ook daadwerkelijk opgehaald
  en met hun canonical vergeleken. De andere 248 productpagina's zijn tijdens
  deze live nacontrole **niet individueel opgehaald**; hun sitemap-URL's zijn
  wel op origin en uniciteit gecontroleerd.
- `/robots.txt`: HTTP 200, `User-agent: *`, `Allow: /`, en exact de verwijzing
  `Sitemap: https://leefnatuurlijkengezond.nl/sitemap.xml`.

### Host- en protocolredirects

Elk van de vier combinaties getest voor zowel `/` als
`/wokpannen/?seo_audit=1&bron=live%20test`.

| Ingang | Gemeten keten | Redirects |
|---|---|---|
| HTTPS non-www | 200 op dezelfde URL | 0 |
| HTTPS www | 301 → HTTPS non-www → 200 | 1 |
| HTTP non-www | 301 → HTTPS non-www → 200 | 1 |
| HTTP www | 301 → HTTPS www → 301 → HTTPS non-www → 200 | 2 |

Alle redirects zijn permanent (301); geen loops of tijdelijke redirects.
In alle gevallen blijven het volledige pad, beide queryparameters en de
gecodeerde spatie `%20` behouden. De querypagina canonicaliseert bewust naar
de basispagina, niet naar een URL met trackingparameters.
Ook `/wokpannen` geeft de bestaande 301 naar `/wokpannen/`, gevolgd door 200.

### Wat eventueel handmatig moet worden aangepast

**Geen noodzakelijke applicatiefix gevonden voor de gecontroleerde SEO-signalen.**
De tweestapsketen van HTTP-www is een resterende optimalisatie, geen blokkade.

1. Controleer in Render **Settings → Custom Domains** of beide hosts nog naar
   dezelfde juiste service wijzen en hun TLS-certificaten geldig zijn.
2. Stel, indien de DNS/proxyprovider dit ondersteunt, voor HTTP-www een
   rechtstreekse permanente 301/308 naar HTTPS-non-www in. De doel-URL moet
   exact `https://leefnatuurlijkengezond.nl` plus het ongewijzigde pad en de
   ongewijzigde querystring zijn.
3. Verifieer vóór wijziging welke laag de eerste HTTPS-redirect uitvoert.
   De responsheaders bewijzen niet welke dashboardregel deze beheert.
   Een automatische HTTPS-regel op Render kan vóór eigen regels ingrijpen;
   combineer host/protocolnormalisatie dan in de daarvoor geschikte proxylaag.
   Wijzig niet blind DNS-records: DNS alleen voert geen HTTP-redirect uit.
4. Test na zo'n wijziging dezelfde acht combinaties opnieuw. Verwacht voor
   HTTP-www één permanente redirect naar de eind-URL, zonder verlies van
   pad/query en zonder lus.

Geen Django-middleware toegevoegd en geen Render-, DNS- of proxyinstellingen
gewijzigd. Productinhoud, selectie, slugs, affiliate-URL's en styling zijn
ongewijzigd.

### Concrete Google Search Console-verificatie

Deze stappen moeten door iemand met toegang tot de property worden uitgevoerd;
Search Console is niet via deze audit ingezien.

1. Open de domeinproperty `leefnatuurlijkengezond.nl`, of de geverifieerde
   URL-prefixproperty `https://leefnatuurlijkengezond.nl/`.
   Een www-prefixproperty is niet voldoende om non-www-eindpagina's te beoordelen.
2. Dien onder **Sitemaps** `https://leefnatuurlijkengezond.nl/sitemap.xml` in
   (bij een prefixproperty kan het invoerveld alleen `sitemap.xml` vragen).
   Controleer na verwerking de status **Succes**, de laatste leesdatum en
   eventuele fouten. Een gevonden URL is niet automatisch een geïndexeerde URL.
3. Inspecteer ten minste de non-www-URL's voor wokpannen, RVS, koolstofstaal,
   gietijzer, één blog en `/product/be-living-28/`. Kies **Live URL testen**:
   controleer toegankelijkheid, toegestane crawl/indexering en de geteste HTML.
   De door de gebruiker opgegeven canonical moet de exacte non-www-URL zijn.
4. Bekijk daarnaast het bestaande indexeringsresultaat: vergelijk
   **Door gebruiker aangegeven canonical** met **Door Google geselecteerde
   canonical**. Het opgeslagen resultaat kan nog van vóór publicatie zijn.
   De live-test kan Google's toekomstige canonicalkeuze niet bevestigen.
5. Vraag waar passend één keer indexering aan voor belangrijke gewijzigde
   eindpagina's. Inspecteer een HTTPS-www-variant: **Pagina met omleiding**
   is daar normaal; vraag geen indexering aan voor die redirect-URL.
6. Controleer na een nieuwe crawl opnieuw de canonicalkeuze en het rapport
   **Pagina-indexering**. Vergelijk de laatste crawldatum met deze publicatie/
   audit; beoordeel oude www-meldingen niet als bewijs dat de nieuwe HTML fout is.

Google beslist zelf over canonicalkeuze en opname in de index. Deze geslaagde
technische controle geeft geen garantie op indexering, rankings of een termijn.

### Herhaalbaarheid

`python scripts/check_live_seo.py` voert dezelfde read-only controles uit met
maximaal drie gelijktijdige paginaverzoeken en schrijft JSON naar stdout.
Het script leest de centrale `SITE_URL` zonder Django/database te starten.
Een afwijking in pagina-, sitemap-, robots- of hostredirectcontroles geeft
exitcode 1. Een geldige tweestapsketen wordt gerapporteerd, niet als fout behandeld.
