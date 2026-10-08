# Structured data op vergelijkingspagina’s

## Aanleiding en besluit

Google meldde bij Skeppshult Traditional:
`Either "offers", "review", or "aggregateRating" should be specified`.
Het product stond als een ingebed `Product` in de `ItemList` van de
gietijzeren-koekenpannenpagina, zonder één van deze eigenschappen.

De gebruiker heeft goedgekeurd om vergelijkbare productlijsten te corrigeren
naar gewone lijsten. Google adviseert product-rich-results voor pagina’s over
één product, niet voor categorieën met verschillende producten:
https://developers.google.com/search/docs/appearance/structured-data/product-snippet#technical-guidelines

Categorieën gebruiken daarom `ItemList` met `ListItem`, positie, productnaam
en de canonical URL van de eigen productdetailpagina. Dit is geen claim op
een product-rich-result. Geen prijzen, aanbiedingen, beoordelingen of
reviewaantallen toegevoegd om validatie te halen.

## Wijzigingen

- `products/views.py`: gedeelde lijstgenerator maakt gewone `ListItem`-entries.
  Ook RVS gebruikt deze generator; alle zichtbare producten worden opgenomen,
  niet uitsluitend producten met een affiliatelink.
- `products/tests.py`: bestaande tests volgen de nieuwe lijststructuur.
- `products/tests_structured_data.py`: regressietests voor alle categorieën,
  maatfilters, vershoudcontainerfilters, eigen productlinks en Skeppshult.

Productdetailpagina’s zijn niet gewijzigd en hebben hiermee niet automatisch
Product-rich-results gekregen. Zichtbare scores, productcontent, productselectie,
affiliate-links, slugs, styling, canonicals en overige structured data behouden.

## Verificatie

- `python manage.py check`: geen problemen.
- `python manage.py test products blogs LeefNatuurlijkenGezond.tests_canonical_urls audits`:
  alle 424 tests geslaagd.
- Alle categorieën en maatfilters: één ItemList, aantal/volgorde/naam/URL
  overeenkomend met de zichtbare producten, zonder Product/Offer/reviewmarkup.
- Productlinks van de standaardcategorieën geven HTTP 200.
- Skeppshult Traditional blijft opgenomen, met de eigen productdetail-URL.
- Voor 46 categorie- en filterpagina’s is de HTML buiten de ItemList exact
  gelijk aan de momentopname vóór deze wijziging. Producten en volgorde gelijk.

## Na publicatie op Render

Deze lokale wijziging is niet automatisch een publicatie. Test na publicatie
de non-www categorie-URL opnieuw met Googles Rich Results Test. De oude
Product-melding hoort niet meer uit deze lijst te komen: er wordt daar geen
Product-rich-result meer gedeclareerd.

Als de melding in Search Console staat, controleer de live HTML en gebruik
waar beschikbaar **Oplossing valideren**. Een historische melding kan blijven
staan totdat Google de pagina opnieuw heeft gecrawld en verwerkt. Deze correctie
is geen garantie op indexering, rankings of andere uitgebreide zoekresultaten.
