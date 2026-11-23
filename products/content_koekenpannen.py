"""Algemene categoriecontent; productspecifieke aanbevelingen staan in de productdata."""

CONTENT = {
    "hero": {
        "h1": (
            "De {product_count} beste PFAS-vrije keramische "
            "koekenpannen van {selected_size} cm (2026)"
        ),
        "paragraphs": [
            (
                "Op deze pagina vergelijken we {product_count} keramische "
                "koekenpannen van {selected_size} cm waarvan voor het exacte "
                "model voldoende is bevestigd dat de keramische antiaanbaklaag "
                "zonder PFAS wordt geproduceerd. We vergelijken onder meer "
                "constructie, gebruiksgemak, oven- en inductiegeschiktheid, "
                "onderhoud en prijs."
            ),
            (
                "De beoordelingen zijn redactioneel en gebaseerd op "
                "productspecificaties, fabrikantdocumentatie, beschikbare "
                "onafhankelijke tests en relevante gebruikerservaringen. "
                "Winkelbeoordelingen worden niet rechtstreeks overgenomen als "
                "onze score. Bij koekenpannensets kijken we daarnaast naar het "
                "werkelijke aantal pannen, de maatcombinatie en eventuele "
                "accessoires."
            ),
        ],
    },
    "products_section": {
        "h2": (
            "De {product_count} geselecteerde PFAS-vrije keramische "
            "koekenpannen van {selected_size} cm"
        ),
        "intro": (
            "In de productkaarten zie je per pan of set de belangrijkste "
            "eigenschappen, onze beoordeling, voor- en nadelen en eventuele "
            "Beste keuze-, Budget keuze- of Premium keuze-badge."
        ),
        "comparison_title": (
            "Vergelijking: {product_count} PFAS-vrije keramische "
            "koekenpannen van {selected_size} cm"
        ),
        "comparison_intro": (
            "Gebruik de vergelijkingstabel om de belangrijkste verschillen "
            "in constructie, gewicht, ovengebruik, handgrepen en andere "
            "relevante eigenschappen naast elkaar te bekijken."
        ),
    },
    "price_guide": {
        "title": "Prijsniveaus binnen deze vergelijking",
        "intro": (
            "De prijsniveaus geven aan waar een pan of set qua reguliere "
            "verkoopprijs binnen het betreffende formaat valt. Tijdelijke "
            "aanbiedingen bepalen het prijsniveau niet."
        ),
        "outro": (
            "Een hoger prijsniveau betekent niet automatisch een hogere "
            "beoordeling. Een duurdere pan moet de meerprijs onderbouwen met "
            "bijvoorbeeld een betere constructie, meer gebruiksmogelijkheden "
            "of andere relevante voordelen."
        ),
        # De juiste prijstabel wordt gekozen op basis van het geselecteerde formaat.
        "ranges_by_size": {
            "20": [
                {"label": "€", "description": "Tot en met €25"},
                {"label": "€€", "description": "€25,01–€50"},
                {"label": "€€€", "description": "€50,01–€90"},
                {"label": "€€€€", "description": "Boven €90"},
            ],
            "24": [
                {"label": "€", "description": "Tot en met €30"},
                {"label": "€€", "description": "€30,01–€60"},
                {"label": "€€€", "description": "€60,01–€100"},
                {"label": "€€€€", "description": "Boven €100"},
            ],
            "26": [
                {"label": "€", "description": "Tot en met €35"},
                {"label": "€€", "description": "€35,01–€65"},
                {"label": "€€€", "description": "€65,01–€105"},
                {"label": "€€€€", "description": "Boven €105"},
            ],
            "28": [
                {"label": "€", "description": "Tot en met €40"},
                {"label": "€€", "description": "€40,01–€70"},
                {"label": "€€€", "description": "€70,01–€110"},
                {"label": "€€€€", "description": "Boven €110"},
            ],
            "30": [
                {"label": "€", "description": "Tot en met €45"},
                {"label": "€€", "description": "€45,01–€75"},
                {"label": "€€€", "description": "€75,01–€120"},
                {"label": "€€€€", "description": "Boven €120"},
            ],
            "32": [
                {"label": "€", "description": "Tot en met €50"},
                {"label": "€€", "description": "€50,01–€85"},
                {"label": "€€€", "description": "€85,01–€130"},
                {"label": "€€€€", "description": "Boven €130"},
            ],
            "20_28": [
                {"label": "€", "description": "Tot en met €50"},
                {"label": "€€", "description": "€50,01–€75"},
                {"label": "€€€", "description": "€75,01–€110"},
                {"label": "€€€€", "description": "Boven €110"},
            ],
            "24_28": [
                {"label": "€", "description": "Tot en met €60"},
                {"label": "€€", "description": "€60,01–€100"},
                {"label": "€€€", "description": "€100,01–€175"},
                {"label": "€€€€", "description": "Boven €175"},
            ],
            "20_24_28": [
                {"label": "€", "description": "Tot en met €75"},
                {"label": "€€", "description": "€75,01–€120"},
                {"label": "€€€", "description": "€120,01–€175"},
                {"label": "€€€€", "description": "Boven €175"},
            ],
        },
    },
    "how_we_assess": {
        "title": "Zo beoordelen we keramische koekenpannen",
        "intro": (
            "We nemen alleen modellen op die verkrijgbaar zijn voor Nederlandse "
            "consumenten en waarvan voor het exacte model voldoende is bevestigd "
            "dat de antiaanbaklaag keramisch is en zonder PFAS wordt geproduceerd. "
            "De PFAS-status is een toelatingsvoorwaarde en levert op zichzelf "
            "geen hogere score op."
        ),
        "criteria_intro": (
            "De sterrenbeoordeling is opgebouwd uit vijf onderdelen. Elk "
            "onderdeel telt voor het aangegeven deel mee in de eindscore:"
        ),
        "score_weights": [
            {"criterion": "Bakresultaat en temperatuurregeling", "weight": "25%"},
            {"criterion": "Constructie en verwachte duurzaamheid", "weight": "25%"},
            {"criterion": "Capaciteit, ontwerp en gebruiksgemak", "weight": "20%"},
            {"criterion": "Reiniging en onderhoud", "weight": "15%"},
            {"criterion": "Prijs-kwaliteitverhouding", "weight": "15%"},
        ],
        "evidence": (
            "Voor de beoordeling gebruiken we controleerbare "
            "productspecificaties, fabrikantdocumentatie, beschikbare "
            "onafhankelijke tests en relevante gebruikerservaringen. "
            "Een individuele gebruikersreview bepaalt de score niet. "
            "Terugkerende en productspecifieke ervaringen kunnen wel "
            "meewegen wanneer ze voldoende zijn onderbouwd. "
            "Winkelgemiddelden vormen niet onze sterrenbeoordeling."
        ),
        "score_explanation": (
            "We beoordelen ieder onderdeel op een schaal van 1 tot 5 en "
            "berekenen daarvan een gewogen gemiddelde. De uiteindelijke "
            "beoordeling wordt weergegeven in stappen van een halve ster. "
            "Alleen producten met minimaal 3,5 sterren worden opgenomen."
        ),
        "review_note": (
            "Een terugkerend reviewsignaal kan bijvoorbeeld meewegen in de "
            "score voor constructie, duurzaamheid of bakresultaat zonder dat "
            "dit automatisch als zichtbaar nadeel bij het product wordt "
            "vermeld. Is een kwaliteitsprobleem voldoende sterk en structureel, "
            "dan beoordelen we eerst opnieuw of het product nog in de selectie "
            "thuishoort."
        ),
        "sets_note": (
            "Bij koekenpannensets kijken we daarnaast naar het werkelijke "
            "aantal pannen, de combinatie en spreiding van formaten, eventuele "
            "technische verschillen binnen de set en de setprijs in verhouding "
            "tot de meegeleverde pannen."
        ),
        "testing_note": (
            "De beoordeling is gebaseerd op de beschikbare informatie. "
            "We vermelden het wanneer we een product zelf hebben getest; "
            "zonder die vermelding is geen eigen langdurige praktijktest "
            "uitgevoerd."
        ),
        "outro": (
            "Ontbreekt essentiële informatie om een product betrouwbaar te "
            "beoordelen, dan nemen we het niet op. Prijzen, voorraad en "
            "productspecificaties kunnen veranderen."
        ),
    },
    "awards": {
        "title": "Wat betekenen onze badges?",
        "intro": (
            "Badges worden alleen toegekend wanneer binnen de actuele selectie "
            "een duidelijke kandidaat aanwezig is. Een categorie hoeft daarom "
            "niet altijd alle drie de badges te bevatten."
        ),
        "items": [
            (
                "<strong>🏆 Beste keuze:</strong> de sterkste totale combinatie "
                "van kwaliteit, constructie, gebruiksgemak, onderbouwing en "
                "prijs-kwaliteit binnen de selectie."
            ),
            (
                "<strong>💰 Budget keuze:</strong> een relatief betaalbare pan "
                "of set die voldoende kwaliteit en gebruiksmogelijkheden biedt "
                "zonder belangrijke concessies die de lage prijs verklaren."
            ),
            (
                "<strong>💎 Premium keuze:</strong> een model waarvan de hogere "
                "prijs gepaard gaat met aantoonbaar onderscheidende constructie, "
                "afwerking of technische gebruiksmogelijkheden."
            ),
        ],
        "outro": (
            "Een hoge prijs is op zichzelf geen reden voor een Premium "
            "keuze-badge en de goedkoopste pan is niet automatisch onze "
            "Budget keuze."
        ),
    },
    "size_guide": {
        "title": "Welk formaat koekenpan heb ik nodig?",
        "intro": (
            "De juiste diameter hangt af van de hoeveelheid voedsel, de "
            "grootte van je huishouden en de diameter van je kookzone. "
            "Vooral bij inductie is het belangrijk dat de bodem van de pan "
            "voldoende aansluit op de gebruikte zone."
        ),
        "sections": [
            {
                "h3": "Veelgebruikte formaten",
                "items": [
                    "<b>Ø 20 cm</b> – Voor eieren, kleine porties, "
                    "bijgerechten en gebruik door één persoon.",
                    "<b>Ø 24 cm</b> – Geschikt voor één tot twee personen "
                    "en kleinere dagelijkse bereidingen.",
                    "<b>Ø 26 cm</b> – Een tussenmaat met meer bakruimte "
                    "zonder direct een grote pan te gebruiken.",
                    "<b>Ø 28 cm</b> – Een veelzijdig formaat voor stellen "
                    "en kleinere gezinnen.",
                    "<b>Ø 30–32 cm</b> – Voor grotere porties, mits de "
                    "kookzone en opbergruimte groot genoeg zijn.",
                ],
            },
            {
                "h3": "Praktische combinaties",
                "items": [
                    "<b>20 + 28 cm:</b> een compacte pan voor één portie "
                    "naast een ruime pan voor gezamenlijke maaltijden.",
                    "<b>24 + 28 cm:</b> twee veelgebruikte formaten voor "
                    "kleinere en grotere dagelijkse bereidingen.",
                    "<b>20 + 24 + 28 cm:</b> drie duidelijk verschillende "
                    "formaten voor wie regelmatig kleine, middelgrote en "
                    "grotere porties bereidt.",
                ],
            },
            {
                "h3": "Wanneer is een koekenpannenset interessant?",
                "items": [
                    "<b>Gebruik van alle maten:</b> een set is vooral "
                    "interessant wanneer je de meegeleverde formaten "
                    "daadwerkelijk regelmatig gebruikt.",
                    "<b>Prijs per pan:</b> vergelijk de reguliere setprijs "
                    "met de gezamenlijke prijs van dezelfde losse pannen. "
                    "Een set is niet automatisch voordeliger.",
                    "<b>Werkelijk aantal pannen:</b> tel alleen de "
                    "koekenpannen mee. Panbeschermers, deksels en andere "
                    "accessoires kunnen als afzonderlijke onderdelen worden "
                    "meegeteld.",
                    "<b>Technische uitvoering:</b> controleer of alle pannen "
                    "dezelfde coating, bodemconstructie, handgreep en "
                    "ovenlimiet hebben.",
                    "<b>Opbergen:</b> meerdere pannen vragen extra kastruimte. "
                    "Gebruik indien nodig panbeschermers wanneer de pannen "
                    "gestapeld worden bewaard.",
                ],
            },
            {
                "h3": "Waar moet je bij het formaat op letten?",
                "items": [
                    "<b>Kookzone:</b> controleer niet alleen de buitendiameter "
                    "van de pan, maar ook of de panbodem aansluit op de "
                    "diameter van je kookzone.",
                    "<b>Gewicht:</b> grotere en zwaarder uitgevoerde pannen "
                    "zijn doorgaans lastiger met één hand te verplaatsen.",
                    "<b>Bereiding:</b> voor kleine porties werkt een compacte "
                    "pan meestal praktischer dan een zeer ruime pan.",
                    "<b>Randhoogte:</b> voor gerechten met veel saus of volume "
                    "kan een hapjespan praktischer zijn dan een lage koekenpan.",
                ],
            },
        ],
        "outro": (
            "<b>Praktische vuistregel:</b> kies geen grotere pan of uitgebreidere "
            "set dan je kookzones, opbergruimte en gebruikelijke porties nodig maken."
        ),
    },
    "why_choose": {
        "title": "Waarom kiezen voor een keramische koekenpan zonder PFAS?",
        "intro": (
            "PFAS is een verzamelnaam voor een grote groep chemische stoffen. "
            "Wie deze stoffen in een antiaanbaklaag wil vermijden, kan kiezen "
            "voor een pan waarvan de fabrikant expliciet vermeldt dat de coating "
            "zonder PFAS wordt geproduceerd. In deze vergelijking nemen we alleen "
            "modellen op waarvan daarnaast voldoende is bevestigd dat het "
            "daadwerkelijk om een keramische antiaanbaklaag gaat."
        ),
        "bullets": [
            (
                "<strong>Bevestigde materiaalkeuze:</strong> de PFAS-vrije "
                "claim moet gelden voor het exacte model en de keramische "
                "antiaanbaklaag."
            ),
            (
                "<strong>Geschikt voor kwetsbare bereidingen:</strong> een "
                "keramisch antiaanbakoppervlak kan praktisch zijn voor "
                "bijvoorbeeld eieren, vis en andere ingrediënten waarbij "
                "weinig aanbakken gewenst is."
            ),
            (
                "<strong>Verschillende constructies:</strong> keramische "
                "antiaanbaklagen worden gecombineerd met onder meer aluminium, "
                "gesmeed aluminium en meerlaagse RVS-constructies met een "
                "aluminium kern."
            ),
            (
                "<strong>Verschillen in gebruik:</strong> modellen kunnen sterk "
                "verschillen in gewicht, bodemconstructie, handgreep, "
                "ovenbestendigheid en vaatwasserbestendigheid."
            ),
            (
                "<strong>Sets:</strong> een koekenpannenset kan aantrekkelijk "
                "zijn wanneer je meerdere formaten nodig hebt, maar controleer "
                "of de set daadwerkelijk voordeliger en praktisch bruikbaar is."
            ),
        ],
        "outro": (
            "Een PFAS-vrije keramische coating zegt op zichzelf niets over de "
            "totale kwaliteit van de pan of de levensduur van de coating. "
            "Daarom beoordelen we de volledige constructie en het gebruik van "
            "ieder product."
        ),
    },
    "tips": {
        "title": "Onderhoud van een keramische koekenpan",
        "intro": (
            "Keramische antiaanbaklagen zijn gebruikslagen en kunnen gevoelig "
            "zijn voor langdurige oververhitting, krassen en agressieve "
            "reiniging. De onderhoudsinstructies van de fabrikant blijven "
            "altijd leidend."
        ),
        "bullets": [
            "Verwarm een lege pan niet langdurig en gebruik voor veel "
            "bereidingen een lage tot middelhoge warmtestand.",
            "Laat een hete pan eerst afkoelen voordat je deze met koud "
            "water reinigt.",
            "Gebruik bij voorkeur houten of siliconen kookgerei, tenzij "
            "de fabrikant metalen kookgerei expliciet toestaat.",
            "Verwijder aangekoekte resten met een zachte spons en een "
            "mild afwasmiddel.",
            "Handwas is doorgaans de voorzichtigste keuze voor de coating, "
            "ook wanneer een fabrikant vaatwassergebruik toestaat.",
            "Gebruik een panbeschermer wanneer gecoate pannen op elkaar "
            "worden gestapeld.",
        ],
        "outro": (
            "Zorgvuldig gebruik kan slijtage beperken, maar iedere keramische "
            "antiaanbaklaag blijft onderhevig aan gebruik en veroudering."
        ),
    },
    "faq": {
        "title": "Veelgestelde vragen over PFAS-vrije koekenpannen en koekenpannensets",
        "items": [
            {
                "q": "Hoe wordt de sterrenbeoordeling bepaald?",
                "a": (
                    "De beoordeling is een gewogen redactionele score. "
                    "Bakresultaat en temperatuurregeling tellen voor 25% mee, "
                    "constructie en verwachte duurzaamheid voor 25%, capaciteit, "
                    "ontwerp en gebruiksgemak voor 20%, reiniging en onderhoud "
                    "voor 15% en prijs-kwaliteit voor 15%. De score is geen "
                    "gemiddelde van winkelreviews."
                ),
            },
            {
                "q": "Worden gebruikersreviews meegenomen in de beoordeling?",
                "a": (
                    "Ja, als aanvullende informatie. Een individuele positieve "
                    "of negatieve review bepaalt de score niet. Terugkerende, "
                    "productspecifieke ervaringen kunnen wel meewegen wanneer "
                    "voldoende duidelijk is dat ze relevant zijn voor het "
                    "exacte product."
                ),
            },
            {
                "q": "Waarom krijgt niet ieder formaat een Budget- of Premium keuze?",
                "a": (
                    "Een badge wordt alleen toegekend wanneer binnen de actuele "
                    "selectie een duidelijke kandidaat aanwezig is. De "
                    "goedkoopste pan is niet automatisch de Budget keuze en een "
                    "hoge prijs is op zichzelf geen reden voor een Premium "
                    "keuze-badge."
                ),
            },
            {
                "q": "Wat betekent PFAS-vrij bij een koekenpan?",
                "a": (
                    "Het betekent dat de betreffende coating volgens de "
                    "fabrikant zonder PFAS is geproduceerd. Controleer altijd "
                    "of deze claim geldt voor het exacte model en niet alleen "
                    "voor een andere productlijn of uitvoering."
                ),
            },
            {
                "q": "Is iedere keramische koekenpan automatisch PFAS-vrij?",
                "a": (
                    "Nee. Een keramische of mineraal klinkende productnaam is "
                    "op zichzelf onvoldoende bewijs. We nemen alleen modellen op "
                    "waarvan voor het exacte model voldoende is bevestigd dat de "
                    "antiaanbaklaag keramisch is en zonder PFAS wordt geproduceerd."
                ),
            },
            {
                "q": "Hoe presteert een keramische coating?",
                "a": (
                    "Een keramische coating kan goede antiaanbakeigenschappen "
                    "bieden, vooral bij lage tot middelhoge temperaturen. De "
                    "prestaties verschillen per product en kunnen afnemen door "
                    "oververhitting, krassen of agressieve reiniging."
                ),
            },
            {
                "q": "Hoe maak ik een keramische koekenpan schoon?",
                "a": (
                    "Laat de pan eerst afkoelen en gebruik warm water, een "
                    "mild afwasmiddel en een zachte spons. Volg daarnaast de "
                    "productspecifieke onderhoudsinstructies van de fabrikant."
                ),
            },
            {
                "q": "Zijn deze koekenpannen geschikt voor inductie?",
                "a": (
                    "Veel modellen zijn geschikt voor inductie, maar niet "
                    "ieder product heeft dezelfde bodemconstructie. Controleer "
                    "de specificaties van het exacte model en stem de diameter "
                    "van de panbodem af op de kookzone."
                ),
            },
            {
                "q": "Hoe lang gaat een keramische coating mee?",
                "a": (
                    "Daarvoor bestaat geen betrouwbare vaste termijn. De "
                    "levensduur hangt af van de kwaliteit van de coating, "
                    "gebruiksfrequentie, temperatuur, reiniging en het "
                    "gebruikte kookgerei."
                ),
            },
            {
                "q": "Mag een keramische koekenpan in de vaatwasser?",
                "a": (
                    "Dat verschilt per model. Sommige fabrikanten staan "
                    "vaatwassergebruik toe, terwijl andere uitsluitend met de hand "
                    "adviseren. Afwassen met de hand is doorgaans de voorzichtigste keuze "
                    "voor de antiaanbaklaag."
                ),
            },
            {
                "q": "Welke maat koekenpan heb ik nodig?",
                "a": (
                    "Voor kleine porties is 20–24 cm vaak voldoende. Een pan "
                    "van 26–28 cm biedt meer ruimte voor dagelijkse "
                    "bereidingen. Modellen van 30–32 cm zijn vooral geschikt "
                    "voor grotere porties en ruime kookzones. Bekijk ook onze "
                    '<a href="/blogs/welke-maat-koekenpan/">uitgebreide maattabel</a>.'
                ),
            },
            {
                "q": "Welke koekenpannenset past het beste bij mijn huishouden?",
                "a": (
                    "Een set van 20 + 28 cm is geschikt als je zowel zeer "
                    "kleine als grotere porties bereidt. De combinatie "
                    "24 + 28 cm bevat twee veelgebruikte dagelijkse formaten. "
                    "Een set van 20 + 24 + 28 cm biedt de meeste keuze, maar "
                    "is vooral zinvol wanneer je alle drie de maten regelmatig "
                    "gebruikt."
                ),
            },
            {
                "q": "Is een koekenpannenset voordeliger dan losse pannen?",
                "a": (
                    "Niet altijd. Vergelijk de reguliere setprijs met de "
                    "gezamenlijke prijs van exact dezelfde losse pannen. Let "
                    "daarbij ook op kleurvarianten, accessoires en verschillen "
                    "in handgrepen of coating."
                ),
            },
            {
                "q": "Wat betekent het aantal delen bij een pannenset?",
                "a": (
                    "Het aantal delen is niet altijd gelijk aan het aantal "
                    "pannen. Sommige aanbieders tellen deksels, losse grepen of "
                    "panbeschermers mee. Daarom vermelden wij bij iedere set "
                    "apart hoeveel daadwerkelijke pannen en welke diameters "
                    "worden geleverd."
                ),
            },
            {
                "q": "Wat is het verschil tussen keramische en RVS pannen?",
                "a": (
                    "Een keramische pan heeft een antiaanbaklaag en is daardoor vaak "
                    "handig voor eieren, vis en andere kwetsbare ingrediënten. Bij een "
                    "ongecoate RVS-pan moet je beter letten op de juiste temperatuur en "
                    "voldoende olie of boter gebruiken om aanbakken te voorkomen. RVS is "
                    "juist geschikt voor krachtig aanbraden en voor het maken van een saus "
                    "op basis van de aanbakresten in de pan. Lees ook onze "
                    '<a href="/blogs/keramische-vs-rvs-koekenpan/">vergelijking van '
                    "keramische en RVS-koekenpannen</a>."
                ),
            },
            {
                "q": "Wat is een hybride keramische koekenpan?",
                "a": (
                    "Bij een hybride koekenpan wordt een keramische antiaanbaklaag "
                    "gecombineerd met een zichtbaar of geëtst RVS-patroon op het "
                    "bakoppervlak. Het doel is om het gebruiksgemak van een "
                    "antiaanbaklaag te combineren met eigenschappen van RVS, zoals "
                    "een stevige constructie en directer contact tussen voedsel en "
                    "het metalen bakoppervlak. Voor delicate bereidingen kan zo'n "
                    "oppervlak iets meer aandacht voor temperatuur en vet vragen "
                    "dan een volledig gladde keramische coating."
                ),
            },
            {
                "q": "Kan een keramische koekenpan in de oven?",
                "a": (
                    "Dat hangt af van het materiaal van de pan, het type handgreep en "
                    "de maximale temperatuur die de fabrikant opgeeft. Sommige modellen "
                    "zijn niet geschikt voor gebruik in de oven, terwijl andere temperaturen "
                    "van meer dan 200 °C aankunnen. Controleer daarom altijd de specificaties "
                    "van het exacte model."
                ),
            },
            {
                "q": "Waarom kan een keramische coating zijn antiaanbakeffect verliezen?",
                "a": (
                    "Mogelijke oorzaken zijn langdurige oververhitting, "
                    "ingebrande voedsel- of vetresten, krassen, agressieve "
                    "reiniging en snelle temperatuurwisselingen. Zorgvuldig "
                    "gebruik kan slijtage beperken, maar iedere coating blijft "
                    "een gebruikslaag."
                ),
            },
        ],
    },
}
