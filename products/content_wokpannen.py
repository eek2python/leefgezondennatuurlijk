"""Algemene categoriecontent; productspecifieke aanbevelingen staan in de productdata."""

CONTENT = {
    "hero": {
        "h1": (
            "De {product_count} beste PFAS-vrije keramische wokpannen van {selected_size} "
            "cm (2026)"
        ),
        "paragraphs": [
            (
                "Op deze pagina vergelijken we {product_count} keramische wokpannen van "
                "{selected_size} cm waarvan voor het exacte model voldoende is bevestigd dat "
                "de keramische antiaanbaklaag zonder PFAS wordt geproduceerd. We vergelijken "
                "onder meer constructie, inhoud, bodemdiameter, gebruiksgemak, oven- en "
                "inductiegeschiktheid, onderhoud en prijs."
            ),
            (
                "De beoordelingen zijn redactioneel en gebaseerd op productspecificaties, "
                "fabrikantdocumentatie, beschikbare onafhankelijke tests en relevante "
                "gebruikerservaringen. Winkelbeoordelingen worden niet rechtstreeks "
                "overgenomen als onze score. De nadruk ligt op wokpannen voor dagelijks "
                "roerbakken op een huishoudelijke kookplaat, niet op traditioneel wokken op "
                "zeer hoge temperatuur."
            ),
        ],
    },
    "products_section": {
        "h2": (
            "De {product_count} geselecteerde PFAS-vrije keramische wokpannen van "
            "{selected_size} cm"
        ),
        "intro": (
            "In de productkaarten zie je per wokpan de belangrijkste eigenschappen, onze "
            "beoordeling, voor- en nadelen en eventuele Beste keuze-, Budget keuze- of "
            "Premium keuze-badge."
        ),
        "comparison_title": (
            "Vergelijking: {product_count} PFAS-vrije keramische wokpannen van "
            "{selected_size} cm"
        ),
        "comparison_intro": (
            "Gebruik de vergelijkingstabel om de belangrijkste verschillen in "
            "constructie, inhoud, bodemdiameter, gewicht, ovengebruik, handgrepen en "
            "andere relevante eigenschappen naast elkaar te bekijken."
        ),
    },
    "price_guide": {
        "title": "Prijsniveaus binnen deze vergelijking",
        "intro": (
            "De prijsniveaus geven aan waar een wokpan qua reguliere verkoopprijs binnen "
            "het betreffende formaat valt. Tijdelijke aanbiedingen bepalen het "
            "prijsniveau niet."
        ),
        "outro": (
            "Een hoger prijsniveau betekent niet automatisch een hogere beoordeling. Een "
            "duurdere wokpan moet de meerprijs onderbouwen met bijvoorbeeld een betere "
            "constructie, meer gebruiksmogelijkheden of andere relevante voordelen."
        ),
        # De juiste prijstabel wordt gekozen op basis van het geselecteerde formaat.
        "ranges_by_size": {
            "28": [
                {"label": "€", "description": "Tot en met €30"},
                {"label": "€€", "description": "Tussen €30 en €60"},
                {"label": "€€€", "description": "Tussen €60 en €100"},
                {"label": "€€€€", "description": "Boven €100"},
            ],
            "30": [
                {"label": "€", "description": "Tot en met €35"},
                {"label": "€€", "description": "Tussen €35 en €60"},
                {"label": "€€€", "description": "Tussen €60 en €110"},
                {"label": "€€€€", "description": "Boven €110"},
            ],
        },
    },
    "how_we_assess": {
        "title": "Zo beoordelen we keramische wokpannen",
        "intro": (
            "We nemen alleen modellen op die verkrijgbaar zijn voor Nederlandse "
            "consumenten en waarvan voor het exacte model voldoende is bevestigd dat de "
            "antiaanbaklaag keramisch is en zonder PFAS wordt geproduceerd. De "
            "PFAS-status is een toelatingsvoorwaarde en levert op zichzelf geen hogere "
            "score op."
        ),
        "criteria_intro": (
            "De sterrenbeoordeling is opgebouwd uit vijf onderdelen. Elk onderdeel telt "
            "voor het aangegeven deel mee in de eindscore:"
        ),
        "score_weights": [
            {"criterion": "Bakresultaat en temperatuurregeling", "weight": "25%"},
            {"criterion": "Constructie en verwachte duurzaamheid", "weight": "25%"},
            {"criterion": "Capaciteit, ontwerp en gebruiksgemak", "weight": "20%"},
            {"criterion": "Reiniging en onderhoud", "weight": "15%"},
            {"criterion": "Prijs-kwaliteitverhouding", "weight": "15%"},
        ],
        "evidence": (
            "Voor de beoordeling gebruiken we controleerbare productspecificaties, "
            "fabrikantdocumentatie, beschikbare onafhankelijke tests en relevante "
            "gebruikerservaringen. Een individuele gebruikersreview bepaalt de score "
            "niet. Terugkerende en productspecifieke ervaringen kunnen wel meewegen "
            "wanneer ze voldoende zijn onderbouwd. Winkelgemiddelden vormen niet onze "
            "sterrenbeoordeling."
        ),
        "score_explanation": (
            "We beoordelen ieder onderdeel op een schaal van 1 tot 5 en berekenen daarvan "
            "een gewogen gemiddelde. De uiteindelijke beoordeling wordt weergegeven in "
            "stappen van een halve ster. Alleen producten met minimaal 3,5 sterren worden "
            "opgenomen."
        ),
        "review_note": (
            "Een terugkerend reviewsignaal over bijvoorbeeld afnemende antiaanbakwerking, "
            "slijtage van de coating of vervorming van de bodem kan meewegen in de score "
            "zonder dat dit automatisch als zichtbaar nadeel bij het product wordt "
            "vermeld. Is een kwaliteitsprobleem voldoende sterk en structureel, dan "
            "beoordelen we eerst opnieuw of het product nog in de selectie thuishoort."
        ),
        "testing_note": (
            "De beoordeling is gebaseerd op de beschikbare informatie. We vermelden het "
            "wanneer we een product zelf hebben getest; zonder die vermelding is geen "
            "eigen langdurige praktijktest uitgevoerd."
        ),
        "outro": (
            "Ontbreekt essentiële informatie om een product betrouwbaar te beoordelen, "
            "dan nemen we het niet op. Prijzen, voorraad en productspecificaties kunnen "
            "veranderen."
        ),
    },
    "awards": {
        "title": "Wat betekenen onze badges?",
        "intro": (
            "Badges worden alleen toegekend wanneer binnen de actuele selectie een "
            "duidelijke kandidaat aanwezig is. Een categorie hoeft daarom niet altijd "
            "alle drie de badges te bevatten."
        ),
        "items": [
            (
                "<strong>🏆 Beste keuze:</strong> de sterkste totale combinatie van kwaliteit, "
                "constructie, gebruiksgemak, onderbouwing en prijs-kwaliteit binnen de "
                "selectie."
            ),
            (
                "<strong>💰 Budget keuze:</strong> een relatief betaalbare wokpan die "
                "voldoende kwaliteit en gebruiksmogelijkheden biedt zonder belangrijke "
                "concessies die de lage prijs verklaren."
            ),
            (
                "<strong>💎 Premium keuze:</strong> een model waarvan de hogere prijs gepaard "
                "gaat met aantoonbaar onderscheidende constructie, afwerking of technische "
                "gebruiksmogelijkheden."
            ),
        ],
        "outro": (
            "Een hoge prijs is op zichzelf geen reden voor een Premium keuze-badge en de "
            "goedkoopste wokpan is niet automatisch onze Budget keuze."
        ),
    },
    "size_guide": {
        "title": "Welk formaat wokpan heb ik nodig?",
        "intro": (
            "De juiste diameter hangt af van de hoeveelheid voedsel, de grootte van je "
            "huishouden en de diameter van je kookzone. Bij een wokpan is de opgegeven "
            "diameter doorgaans de maat aan de bovenrand. De vlakke bodem is kleiner en "
            "bepaalt mede hoeveel ingrediënten direct contact maken met het bakoppervlak."
        ),
        "sections": [
            {
                "h3": "Veelgebruikte formaten",
                "items": [
                    (
                        "<b>Ø 28 cm</b> – Een praktisch formaat voor kleinere tot normale porties en "
                        "dagelijkse roerbakgerechten."
                    ),
                    (
                        "<b>Ø 30 cm</b> – Biedt doorgaans meer ruimte voor grotere porties en "
                        "gerechten met veel groenten, mits de inhoud en de kookzone voldoende groot "
                        "zijn."
                    ),
                ],
            },
            {
                "h3": "Waar moet je bij het formaat op letten?",
                "items": [
                    (
                        "<b>Bodemdiameter:</b> controleer of de diameter van de vlakke panbodem "
                        "aansluit op de kookzone. Vooral bij inductie is ook het "
                        "inductiecontactoppervlak van belang."
                    ),
                    (
                        "<b>Inhoud en randhoogte:</b> kijk naast de diameter naar de inhoud in liters "
                        "en de hoogte van de rand. Wokpannen met dezelfde diameter kunnen verschillen "
                        "in capaciteit."
                    ),
                    (
                        "<b>Gewicht:</b> houd rekening met het gewicht van een gevulde pan. Een extra "
                        "hulpgreep kan het optillen en verplaatsen vergemakkelijken."
                    ),
                    (
                        "<b>Opbergruimte:</b> let ook op de totale afmetingen inclusief handgreep, "
                        "hulpgreep en eventueel deksel."
                    ),
                    (
                        "<b>Bereiding:</b> voor roerbakgerechten is voldoende ruimte op de bodem en "
                        "langs de randen belangrijker dan alleen een grote nominale diameter."
                    ),
                ],
            },
        ],
        "outro": (
            "<b>Praktische vuistregel:</b> kies een wokpan die past bij je gebruikelijke "
            "porties en kookzone. Een grotere diameter betekent niet automatisch een "
            "groter vlak bakoppervlak."
        ),
    },
    "why_choose": {
        "title": "Waarom kiezen voor een keramische wokpan zonder PFAS?",
        "intro": (
            "PFAS is een verzamelnaam voor een grote groep chemische stoffen. Wie deze "
            "stoffen in een antiaanbaklaag wil vermijden, kan kiezen voor een wokpan "
            "waarvan de fabrikant expliciet vermeldt dat de coating zonder PFAS wordt "
            "geproduceerd. In deze vergelijking nemen we alleen modellen op waarvan "
            "daarnaast voldoende is bevestigd dat het daadwerkelijk om een keramische "
            "antiaanbaklaag gaat."
        ),
        "bullets": [
            (
                "<strong>Bevestigde materiaalkeuze:</strong> de PFAS-vrije claim moet gelden "
                "voor het exacte model en de keramische antiaanbaklaag."
            ),
            (
                "<strong>Geschikt voor dagelijks roerbakken:</strong> een keramisch "
                "antiaanbakoppervlak kan praktisch zijn voor groenten, rijst, noedels en "
                "kleinere stukken vlees of vis."
            ),
            (
                "<strong>Hoge, schuine randen:</strong> bieden ruimte om ingrediënten te "
                "bewegen en helpen morsen tijdens het roerbakken te beperken."
            ),
            (
                "<strong>Direct antiaanbakgemak:</strong> een keramische coating hoeft niet "
                "te worden ingebrand zoals doorgaans wel nodig is bij een ongecoate "
                "koolstofstalen wok."
            ),
            (
                "<strong>Verschillende constructies:</strong> keramische antiaanbaklagen "
                "worden gecombineerd met onder meer aluminium, geanodiseerd aluminium en "
                "meerlaagse RVS-constructies met een aluminium kern."
            ),
            (
                "<strong>Verschillen in gebruik:</strong> modellen kunnen sterk verschillen "
                "in inhoud, bodemdiameter, gewicht, handgrepen, ovenbestendigheid en "
                "onderhoud."
            ),
        ],
        "outro": (
            "Een PFAS-vrije keramische coating zegt op zichzelf niets over de totale "
            "kwaliteit van de wokpan of de levensduur van de coating. Keramische "
            "wokpannen zijn vooral bedoeld voor gecontroleerd roerbakken op lage tot "
            "middelhoge temperatuur. Voor traditionele woktechnieken op zeer hoge hitte "
            "is een ongecoate koolstofstalen wok doorgaans geschikter."
        ),
    },
    "tips": {
        "title": "Onderhoud van een keramische wokpan",
        "intro": (
            "Keramische antiaanbaklagen zijn gebruikslagen en kunnen gevoelig zijn voor "
            "langdurige oververhitting, krassen en agressieve reiniging. De "
            "onderhoudsinstructies van de fabrikant blijven altijd leidend."
        ),
        "bullets": [
            (
                "Verwarm een lege wokpan niet langdurig en gebruik voor het roerbakken bij "
                "voorkeur een lage tot middelhoge warmtestand."
            ),
            "Laat een hete pan eerst afkoelen voordat je deze met koud water reinigt.",
            (
                "Gebruik bij voorkeur houten of siliconen kookgerei, tenzij de fabrikant "
                "metalen kookgerei expliciet toestaat."
            ),
            "Verwijder aangekoekte resten met een zachte spons en een mild afwasmiddel.",
            (
                "Handwas is doorgaans de voorzichtigste keuze voor de coating, ook wanneer "
                "een fabrikant vaatwassergebruik toestaat."
            ),
            "Gebruik een panbeschermer wanneer gecoate pannen op elkaar worden gestapeld.",
            (
                "Controleer voor gebruik in de oven de maximale temperatuur van de pan, "
                "handgrepen en eventueel het deksel."
            ),
        ],
        "outro": (
            "Zorgvuldig gebruik kan slijtage beperken, maar iedere keramische "
            "antiaanbaklaag blijft onderhevig aan gebruik en veroudering."
        ),
    },
    "faq": {
        "title": "Veelgestelde vragen over PFAS-vrije keramische wokpannen",
        "items": [
            {
                "q": "Hoe wordt de sterrenbeoordeling bepaald?",
                "a": (
                    "De beoordeling is een gewogen redactionele score. Bakresultaat en "
                    "temperatuurregeling tellen voor 25% mee, constructie en verwachte "
                    "duurzaamheid voor 25%, capaciteit, ontwerp en gebruiksgemak voor 20%, "
                    "reiniging en onderhoud voor 15% en prijs-kwaliteit voor 15%. De score is "
                    "geen gemiddelde van winkelreviews."
                ),
            },
            {
                "q": "Worden gebruikersreviews meegenomen in de beoordeling?",
                "a": (
                    "Ja, als aanvullende informatie. Een individuele positieve of negatieve "
                    "review bepaalt de score niet. Terugkerende, productspecifieke ervaringen "
                    "kunnen wel meewegen wanneer voldoende duidelijk is dat ze relevant zijn voor "
                    "het exacte product."
                ),
            },
            {
                "q": "Waarom krijgt niet ieder formaat een Budget- of Premium keuze?",
                "a": (
                    "Een badge wordt alleen toegekend wanneer binnen de actuele selectie een "
                    "duidelijke kandidaat aanwezig is. De goedkoopste wokpan is niet automatisch "
                    "de Budget keuze en een hoge prijs is op zichzelf geen reden voor een Premium "
                    "keuze-badge."
                ),
            },
            {
                "q": "Wat betekent PFAS-vrij bij een wokpan?",
                "a": (
                    "Het betekent dat de betreffende coating volgens de fabrikant zonder PFAS is "
                    "geproduceerd. Controleer altijd of deze claim geldt voor het exacte model en "
                    "niet alleen voor een andere productlijn of uitvoering."
                ),
            },
            {
                "q": "Is iedere keramische wokpan automatisch PFAS-vrij?",
                "a": (
                    "Nee. Een keramische of mineraal klinkende productnaam is op zichzelf "
                    "onvoldoende bewijs. We nemen alleen modellen op waarvan voor het exacte "
                    "model voldoende is bevestigd dat de antiaanbaklaag keramisch is en zonder "
                    "PFAS wordt geproduceerd."
                ),
            },
            {
                "q": "Hoe presteert een keramische coating?",
                "a": (
                    "Een keramische coating kan goede antiaanbakeigenschappen bieden, vooral bij "
                    "lage tot middelhoge temperaturen. De prestaties verschillen per product en "
                    "kunnen afnemen door oververhitting, krassen of agressieve reiniging."
                ),
            },
            {
                "q": "Waar moet ik op letten bij inductie?",
                "a": (
                    "De wokpannen in deze selectie hebben een inductiegeschikte vlakke bodem. "
                    "Controleer of de diameter van het inductiecontactoppervlak aansluit op de "
                    "gebruikte kookzone. De opgegeven diameter aan de bovenrand is daarvoor niet "
                    "voldoende."
                ),
            },
            {
                "q": "Welk formaat wokpan heb ik nodig?",
                "a": (
                    "Een wokpan van 28 cm is vaak praktisch voor kleinere tot normale porties. "
                    "Een model van 30 cm biedt doorgaans meer ruimte voor grotere hoeveelheden. "
                    "Kijk naast de diameter ook naar de inhoud in liters, randhoogte, "
                    "bodemdiameter en het gewicht."
                ),
            },
            {
                "q": "Waarom hebben wokpannen hoge, schuine randen?",
                "a": (
                    "De hoge en schuin oplopende randen bieden ruimte om ingrediënten tijdens het "
                    "roerbakken te bewegen. De vorm helpt ook om ingrediënten vanaf de bodem naar "
                    "de koelere zijkanten te verplaatsen."
                ),
            },
            {
                "q": (
                    "Wat is het verschil tussen een keramische wokpan en een traditionele "
                    "koolstofstalen wok?"
                ),
                "a": (
                    "Een keramische wokpan heeft een antiaanbaklaag en hoeft niet te worden "
                    "ingebrand. De modellen in deze selectie hebben een vlakke bodem voor "
                    "huishoudelijke kookplaten. Een traditionele koolstofstalen wok is meestal "
                    "dunwandig en geschikt voor snel roerbakken op hoge temperatuur. Veel "
                    "traditionele uitvoeringen hebben een ronde bodem. Ongecoat koolstofstaal "
                    "vraagt doorgaans een inbrandlaag en zorgvuldig onderhoud om roest te "
                    "voorkomen."
                ),
            },
            {
                "q": "Kan ik op hoog vuur wokken met een keramische wokpan?",
                "a": (
                    "Keramische wokpannen zijn doorgaans bedoeld voor gecontroleerd roerbakken op "
                    "lage tot middelhoge temperatuur. Langdurig gebruik op maximale hitte kan de "
                    "antiaanbakeigenschappen aantasten. Voor traditionele woktechnieken op zeer "
                    "hoge temperatuur is koolstofstaal meestal geschikter. Volg altijd de "
                    "instructies van de fabrikant."
                ),
            },
            {
                "q": "Moet ik een keramische wokpan voorverwarmen?",
                "a": (
                    "Een korte voorverwarming op lage tot middelhoge stand kan passend zijn, maar "
                    "laat de pan niet langdurig leeg heet worden. Volg de temperatuur- en "
                    "gebruiksinstructies van de fabrikant."
                ),
            },
            {
                "q": "Hoe lang gaat een keramische coating mee?",
                "a": (
                    "Daarvoor bestaat geen betrouwbare vaste termijn. De levensduur hangt af van "
                    "de kwaliteit van de coating, gebruiksfrequentie, temperatuur, reiniging en "
                    "het gebruikte kookgerei."
                ),
            },
            {
                "q": "Waarom kan een keramische coating zijn antiaanbakeffect verliezen?",
                "a": (
                    "Mogelijke oorzaken zijn langdurige oververhitting, ingebrande voedsel- of "
                    "vetresten, krassen, agressieve reiniging en snelle temperatuurwisselingen. "
                    "Zorgvuldig gebruik kan slijtage beperken, maar iedere coating blijft een "
                    "gebruikslaag."
                ),
            },
            {
                "q": "Hoe maak ik een keramische wokpan schoon?",
                "a": (
                    "Laat de pan eerst afkoelen en gebruik warm water, een mild afwasmiddel en "
                    "een zachte spons. Volg daarnaast de productspecifieke onderhoudsinstructies "
                    "van de fabrikant."
                ),
            },
            {
                "q": "Mag een keramische wokpan in de vaatwasser?",
                "a": (
                    "Dat verschilt per model. Sommige fabrikanten staan vaatwassergebruik toe, "
                    "terwijl andere uitsluitend met de hand adviseren. Afwassen met de hand is "
                    "doorgaans de voorzichtigste keuze voor de antiaanbaklaag."
                ),
            },
            {
                "q": "Welk kookgerei gebruik ik in een keramische wokpan?",
                "a": (
                    "Houten of siliconen kookgerei is doorgaans de voorzichtigste keuze voor de "
                    "coating. Gebruik metalen kookgerei alleen wanneer de fabrikant dit voor het "
                    "exacte model expliciet toestaat."
                ),
            },
            {
                "q": "Kan een keramische wokpan in de oven?",
                "a": (
                    "Dat hangt af van het materiaal van de pan, het type handgreep en de maximale "
                    "temperatuur die de fabrikant opgeeft. Sommige modellen zijn niet geschikt "
                    "voor gebruik in de oven, terwijl andere temperaturen van meer dan 200 °C "
                    "aankunnen. Controleer daarom altijd de specificaties van het exacte model."
                ),
            },
        ],
    },
}
