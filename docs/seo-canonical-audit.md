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

De Render-publicatie en externe redirectconfiguratie zijn niet gewijzigd.
De live site blijft dus de oude signalen leveren totdat de nieuwe versie
op Render is gepubliceerd.
