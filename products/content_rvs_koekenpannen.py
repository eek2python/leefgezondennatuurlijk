"""Algemene RVS-categoriecontent; productspecifieke aanbevelingen staan in de productdata.

De structuur sluit aan op die van de keramische koekenpannen. De pagina-renderer
moet {product_count} en {selected_size} invullen. De prijsniveautabel en
snelkiesproducten worden uit de bestaande configuratie/productdata gehaald.
"""

CONTENT = {
    "meta": {
        "title": "Beste RVS-koekenpannen en pannensets 2026 – ongecoat RVS",
        "description": (
            "Vergelijk ongecoate RVS-koekenpannen van 20 t/m 32 cm en pannensets. "
            "Bekijk materiaalopbouw, ovenbestendigheid, gebruiksgemak, "
            "beoordelingen en prijsniveaus."
        ),
        "og_title": "Beste ongecoate RVS-koekenpannen en pannensets van 2026",
        "og_description": (
            "Onze redactionele vergelijking van RVS-koekenpannen "
            "en sets: van capsulebodems tot volledig meerlaagse constructies."
        ),
        "canonical_path": "/rvs-koekenpannen/",
    },

    "hero": {
        "h1": (
            "De {product_count} geselecteerde ongecoate RVS-koekenpannen "
            "van {selected_size} cm (2026)"
        ),
        "paragraphs": [
            (
                "Op deze pagina vergelijken we {product_count} RVS-koekenpannen "
                "of pannensets in de maat {selected_size} cm. Voor ieder exact "
                "model moet voldoende zijn bevestigd dat het bakoppervlak "
                "uit ongecoat roestvrij staal bestaat. We vergelijken onder "
                "meer materiaalopbouw, warmtegeleidende constructie, "
                "gebruiksgemak, oven- en inductiegeschiktheid, onderhoud en prijs."
            ),
            (
                "Onze beoordelingen zijn redactioneel en gebaseerd op "
                "controleerbare productspecificaties, fabrikantdocumentatie, "
                "beschikbare onafhankelijke tests en relevante gebruikerservaringen. "
                "Winkelbeoordelingen nemen we niet rechtstreeks over als onze "
                "score. Bij koekenpannensets kijken we ook naar het werkelijke "
                "aantal pannen, de maatcombinatie en eventuele accessoires."
            ),
        ],
    },

    "products_section": {
        "h2": (
            "De {product_count} geselecteerde ongecoate RVS-koekenpannen "
            "van {selected_size} cm"
        ),
        "intro": (
            "In de productkaarten zie je per pan of set de belangrijkste "
            "eigenschappen, onze beoordeling, voor- en nadelen en eventuele "
            "Beste keuze-, Budget keuze- of Premium keuze-badge."
        ),
        "comparison_title": (
            "Vergelijking: {product_count} ongecoate RVS-koekenpannen "
            "van {selected_size} cm"
        ),
        "comparison_intro": (
            "Gebruik de vergelijkingstabel om verschillen in materiaalopbouw, "
            "bodemconstructie, bruikbare bodemmaat, ovenbestendigheid, "
            "handgrepen en andere onderscheidende kenmerken te bekijken. "
            "Het aantal lagen alleen bepaalt niet welke pan beter is."
        ),
    },

    "price_guide": {
        "title": "Prijsniveaus binnen deze vergelijking",
        "intro": (
            "Het prijsniveau (€ tot en met €€€€) laat zien waar een pan of set "
            "qua representatieve reguliere verkoopprijs binnen het gekozen "
            "formaat valt. De prijsgrenzen verschillen per diameter en "
            "setcombinatie. Een tijdelijke aanbieding verandert het "
            "structurele prijsniveau niet automatisch."
        ),
        "outro": (
            "Een hoger prijsniveau betekent niet automatisch een hogere "
            "beoordeling. Een hogere reguliere prijs moet worden afgewogen "
            "tegen concrete eigenschappen, zoals materiaalopbouw, "
            "afwerking, ovenbestendigheid, bruikbare bodemmaat en garantie. "
            "Op de productkaarten en in de vergelijkingstabel tonen we "
            "prijsniveaus in plaats van exacte verkoopprijzen."
        ),
        # De juiste prijstabel wordt gekozen op basis van het geselecteerde formaat.
        "ranges_by_size": {
            "20": [
                {"label": "€", "description": "Tot en met €50"},
                {"label": "€€", "description": "€50,01–€90"},
                {"label": "€€€", "description": "€90,01–€140"},
                {"label": "€€€€", "description": "Boven €140"},
            ],
            "24": [
                {"label": "€", "description": "Tot en met €60"},
                {"label": "€€", "description": "€60,01–€100"},
                {"label": "€€€", "description": "€100,01–€150"},
                {"label": "€€€€", "description": "Boven €150"},
            ],
            "26": [
                {"label": "€", "description": "Tot en met €60"},
                {"label": "€€", "description": "€60,01–€100"},
                {"label": "€€€", "description": "€100,01–€150"},
                {"label": "€€€€", "description": "Boven €150"},
            ],
            "28": [
                {"label": "€", "description": "Tot en met €65"},
                {"label": "€€", "description": "€65,01–€110"},
                {"label": "€€€", "description": "€110,01–€175"},
                {"label": "€€€€", "description": "Boven €175"},
            ],
            "30": [
                {"label": "€", "description": "Tot en met €70"},
                {"label": "€€", "description": "€70,01–€120"},
                {"label": "€€€", "description": "€120,01–€180"},
                {"label": "€€€€", "description": "Boven €180"},
            ],
            "32": [
                {"label": "€", "description": "Tot en met €90"},
                {"label": "€€", "description": "€90,01–€150"},
                {"label": "€€€", "description": "€150,01–€220"},
                {"label": "€€€€", "description": "Boven €220"},
            ],
            "20_28": [
                {"label": "€", "description": "Tot en met €140"},
                {"label": "€€", "description": "€140,01–€180"},
                {"label": "€€€", "description": "€180,01–€240"},
                {"label": "€€€€", "description": "Boven €240"},
            ],
            "24_28": [
                {"label": "€", "description": "Tot en met €140"},
                {"label": "€€", "description": "€140,01–€190"},
                {"label": "€€€", "description": "€190,01–€260"},
                {"label": "€€€€", "description": "Boven €260"},
            ],
            "20_24_28": [
                {"label": "€", "description": "Tot en met €150"},
                {"label": "€€", "description": "€150,01–€250"},
                {"label": "€€€", "description": "€250,01–€350"},
                {"label": "€€€€", "description": "Boven €350"},
            ],
        },
    },

    "how_we_assess": {
        "title": "Zo beoordelen we RVS-koekenpannen",
        "intro": (
            "We selecteren alleen modellen die normaal verkrijgbaar zijn "
            "voor Nederlandse consumenten en waarvan voor het exacte model "
            "betrouwbaar is vastgesteld dat het voedselcontactoppervlak uit "
            "ongecoat RVS bestaat. Pannen met een aangebrachte keramische, "
            "PTFE- of andere antiaanbaklaag op het bakoppervlak vallen buiten "
            "deze selectie. De aanwezigheid van ongecoat RVS is een "
            "toelatingsvoorwaarde en levert op zichzelf geen extra punten op."
        ),
        "criteria_intro": (
            "We beoordelen iedere pan of set op vijf onderdelen. Elk "
            "onderdeel telt voor het aangegeven percentage mee in "
            "de gewogen eindscore:"
        ),
        "score_weights": [
            {"criterion": "Bakresultaat en temperatuurgedrag", "weight": "25%"},
            {"criterion": "Constructie en verwachte duurzaamheid", "weight": "25%"},
            {"criterion": "Gebruiksgemak en veelzijdigheid", "weight": "20%"},
            {"criterion": "Reiniging en onderhoud", "weight": "15%"},
            {"criterion": "Prijs-kwaliteitverhouding", "weight": "15%"},
        ],
        "evidence": (
            "We gebruiken productspecificaties, fabrikantdocumentatie, "
            "beschikbare onafhankelijke tests en relevante gebruikerservaringen "
            "als onderbouwing. Een volledige 5-ply- of 7-plyconstructie krijgt "
            "niet automatisch een betere score dan een goed uitgevoerde "
            "3-plypan of capsulebodem. Bakprestaties worden niet uitsluitend "
            "uit het aantal lagen afgeleid. Een enkele gebruikersreview of "
            "het gemiddelde cijfer van een winkel bepaalt onze score niet."
        ),
        "score_explanation": (
            "We beoordelen elk onderdeel op een schaal van 1 tot 5 en "
            "berekenen het gewogen gemiddelde. De uiteindelijke beoordeling "
            "tonen we in stappen van een halve ster. Alleen producten "
            "met een afgeronde score van minimaal 3,5 sterren nemen we op."
        ),
        "review_note": (
            "Terugkerende, goed onderbouwde ervaringen over bijvoorbeeld "
            "vervorming, warmtegedrag, bodemcontact of losrakende handgrepen "
            "kunnen meewegen in de score. Een reviewsignaal hoeft niet "
            "automatisch als zichtbaar nadeel te worden vermeld. Bij een "
            "aannemelijk structureel kwaliteitsprobleem beoordelen we "
            "opnieuw of de pan in de selectie thuishoort. Klachten die "
            "vooral te maken hebben met normale RVS-baktechniek of "
            "cosmetische verkleuring wegen we terughoudend."
        ),
        "sets_note": (
            "Bij koekenpannensets kijken we daarnaast naar het aantal "
            "daadwerkelijk meegeleverde koekenpannen, de spreiding van "
            "formaten, mogelijke verschillen in constructie of ovenlimiet "
            "tussen de pannen en de reguliere setprijs ten opzichte van "
            "de losse pannen. Accessoires tellen niet mee als pan."
        ),
        "testing_note": (
            "De beoordeling is gebaseerd op de beschikbare informatie. "
            "We vermelden het expliciet wanneer een product zelf is getest; "
            "zonder die vermelding is geen eigen langdurige praktijktest uitgevoerd."
        ),
        "outro": (
            "Ontbreekt essentiële informatie over het bakoppervlak, "
            "de materiaalopbouw of relevante gebruiksbeperkingen, dan "
            "nemen we het model niet op. Prijzen, voorraad en "
            "productspecificaties kunnen veranderen."
        ),
    },

    "awards": {
        "title": "Wat betekenen onze badges?",
        "intro": (
            "Badges worden alleen toegekend wanneer binnen de actuele "
            "vergelijking een duidelijke kandidaat aanwezig is. Daarom "
            "heeft niet ieder formaat of iedere setcombinatie automatisch "
            "alle drie de badges."
        ),
        "items": [
            (
                "<strong>🏆 Beste keuze:</strong> de sterkste totale combinatie "
                "van bakprestaties, constructie, gebruiksgemak, verwachte "
                "duurzaamheid en prijs-kwaliteit."
            ),
            (
                "<strong>💰 Budget keuze:</strong> een relatief betaalbare "
                "pan of set die aan alle toelatingseisen voldoet, voldoende "
                "kwaliteit biedt en geen belangrijke concessies kent die "
                "de lagere prijs verklaren."
            ),
            (
                "<strong>💎 Premium keuze:</strong> een model dat zich aantoonbaar "
                "onderscheidt door constructie, afwerking, technische "
                "mogelijkheden of andere relevante kwaliteitskenmerken."
            ),
        ],
        "outro": (
            "Een hoge prijs of een groot aantal lagen is op zichzelf "
            "geen reden voor een Premium keuze-badge. De goedkoopste "
            "pan is evenmin automatisch onze Budget keuze."
        ),
    },

    "size_guide": {
        "title": "Welk formaat RVS-koekenpan heb ik nodig?",
        "intro": (
            "De juiste diameter hangt af van je porties, de beschikbare "
            "kookzones en de manier waarop je bakt. Let bij RVS niet "
            "alleen op de nominale bovenranddiameter: de werkelijke "
            "bakruimte en de bodemdiameter kunnen per model verschillen."
        ),
        "sections": [
            {
                "h3": "Veelgebruikte formaten",
                "items": [
                    "<b>Ø 20 cm</b> – Voor eieren, kleine porties, bijgerechten en koken voor één persoon.",
                    "<b>Ø 24 cm</b> – Voor kleinere dagelijkse bereidingen en ongeveer één tot twee personen.",
                    "<b>Ø 26 cm</b> – Een tussenmaat met extra bakruimte zonder direct een grote pan te gebruiken.",
                    "<b>Ø 28 cm</b> – Een veelzijdige maat voor dagelijkse maaltijden en grotere porties.",
                    "<b>Ø 30 cm</b> – Voor grotere hoeveelheden vlees of groenten, mits de kookzone past.",
                    "<b>Ø 32 cm</b> – Voor veel bakruimte en bereidingen waarbij ingrediënten voldoende afstand nodig hebben om te bruinen.",
                ],
            },
            {
                "h3": "Praktische combinaties",
                "items": [
                    (
                        "<b>20 + 28 cm:</b> een compacte pan naast een ruime "
                        "pan voor grotere gerechten; handig als een middenmaat "
                        "niet nodig is."
                    ),
                    (
                        "<b>24 + 28 cm:</b> twee veelgebruikte formaten voor "
                        "kleinere en grotere dagelijkse bereidingen."
                    ),
                    (
                        "<b>20 + 24 + 28 cm:</b> drie afzonderlijke maten "
                        "voor wie regelmatig verschillende portiegroottes "
                        "bereidt of meerdere oude pannen wil vervangen."
                    ),
                ],
            },
            {
                "h3": "Wanneer is een RVS-koekenpannenset interessant?",
                "items": [
                    (
                        "<b>Gebruik van alle maten:</b> een set is vooral "
                        "zinvol wanneer je de meegeleverde pannen ook "
                        "daadwerkelijk gebruikt."
                    ),
                    (
                        "<b>Prijs per pan:</b> vergelijk de reguliere setprijs "
                        "met de gezamenlijke reguliere prijs van precies "
                        "dezelfde losse modellen."
                    ),
                    (
                        "<b>Setinhoud:</b> controleer hoeveel koekenpannen je "
                        "krijgt en welke accessoires eventueel zijn meegeleverd."
                    ),
                    (
                        "<b>Technische uitvoering:</b> controleer of alle "
                        "pannen dezelfde laagopbouw, handgreep, "
                        "inductiegeschiktheid en ovenlimiet hebben."
                    ),
                    (
                        "<b>Opbergen:</b> drie RVS-pannen nemen meer ruimte "
                        "in dan een losse pan, zeker bij lange metalen grepen."
                    ),
                ],
            },
            {
                        "h3": "Waar moet je bij het formaat op letten?",
                        "items": [
                            (
                                "<b>Bodem en kookzone:</b> kies een pan waarvan de "
                                "bodemdiameter aansluit op je inductiezone of brander."
                            ),
                            (
                                "<b>Bruikbaar bakoppervlak:</b> een minder schuin "
                                "lopende zijwand kan bij dezelfde bovenranddiameter "
                                "meer vlak bakoppervlak opleveren."
                            ),
                            (
                                "<b>Gewicht:</b> grote, meerlaagse pannen kunnen "
                                "relatief zwaar zijn; let op hanteerbaarheid en "
                                "eventuele hulpgrepen."
                            ),
                            (
                                "<b>Constructie:</b> bij een capsule- of sandwichbodem "
                                "zit de warmtegeleidende laag vooral in de bodem; "
                                "bij volledig meerlaagse pannen loopt deze ook "
                                "door de zijwanden."
                            ),
                            (
                                "<b>Bereiding:</b> een ruime pan helpt wanneer "
                                "ingrediënten niet te dicht op elkaar moeten liggen "
                                "om goed te bruinen."
                            ),
                        ],
                    },
                ],
                "outro": (
                    "<b>Praktische vuistregel:</b> kies de pan of set die past "
                    "bij je normale porties en kookzone, niet automatisch de "
                    "grootste diameter of het hoogste aantal lagen."
                ),
            },

    "why_choose": {
        "title": "Waarom kiezen voor een ongecoate RVS-koekenpan?",
        "intro": (
            "Een ongecoate RVS-koekenpan is een logische keuze voor wie "
            "zonder aangebrachte antiaanbaklaag wil bakken en graag "
            "controle houdt over aanbraden, bruinen en afblussen."
        ),
        "bullets": [
            (
                "<strong>Ongecoat bakoppervlak:</strong> het voedsel "
                "komt in contact met roestvrij staal en niet met een "
                "aangebrachte antiaanbaklaag."
            ),
            (
                "<strong>Geschikt voor aanbraden:</strong> RVS is bruikbaar "
                "voor vlees, aardappelen en groenten die een bruine korst "
                "mogen krijgen, mits de temperatuur goed wordt geregeld."
            ),
            (
                "<strong>Afblussen en sauzen:</strong> aanbakresten kunnen "
                "met vocht worden losgemaakt en de basis vormen voor "
                "een saus."
            ),
            (
                "<strong>Geen slijtende antiaanbaklaag:</strong> de "
                "eigenschappen van het bakoppervlak zijn niet afhankelijk "
                "van een aangebrachte coating die door gebruik kan slijten."
            ),
            (
                "<strong>Keuze in constructies:</strong> er zijn pannen "
                "met een sandwich- of capsulebodem en met volledig "
                "meerlaagse RVS/aluminium-opbouw."
            ),
            (
                "<strong>Verschillen in gebruik:</strong> per model lopen "
                "gewicht, ovenbestendigheid, bodemdiameter, handgreep "
                "en onderhoudsmogelijkheden uiteen."
            ),
        ],
        "outro": (
            "Ongecoat RVS biedt geen antiaanbakeffect zoals een keramische "
            "coating. Bakken vraagt daarom enige aandacht voor voorverwarmen, "
            "voldoende olie of boter en het juiste moment van keren. "
            "Voor kwetsbare bereidingen kan een pan met antiaanbaklaag "
            "praktischer zijn."
        ),
    },

    "tips": {
        "title": "Bakken met en onderhoud van RVS-koekenpannen",
        "intro": (
            "De juiste baktechniek helpt aanbakken te beperken. Het onderhoud "
            "van ongecoat RVS is doorgaans eenvoudig, maar volg altijd "
            "de instructies voor de exacte pan en handgreep."
        ),
        "bullets": [
            (
                "Verwarm de pan geleidelijk voor. Een hoge stand of "
                "inductieboost is niet voor ieder gerecht of iedere pan nodig."
            ),
            (
                "Voeg olie of boter toe wanneer de pan voldoende warm "
                "is en gebruik een temperatuur die past bij het ingrediënt."
            ),
            (
                "Laat vlees eerst rustig bruinen voordat je het probeert "
                "los te maken of te keren."
            ),
            (
                "Gebruik de waterdruppeltest niet als vaste regel voor "
                "alle gerechten: eieren en andere kwetsbare ingrediënten "
                "vragen vaak een lagere temperatuur."
            ),
            (
                "Blus bruine aanbakresten eventueel af met water of "
                "bouillon om een saus te maken."
            ),
            (
                "Laat een hete pan afkoelen voordat je deze onder koud "
                "water houdt; plotselinge temperatuurwisselingen kunnen "
                "vervorming bevorderen."
            ),
            (
                "Verwijder aangekoekte resten met warm water, mild "
                "afwasmiddel en een geschikte spons. Laat hardnekkige "
                "resten eerst weken."
            ),
            (
                "Normale regenboogverkleuring of watervlekken zijn "
                "doorgaans cosmetisch. Een geschikt RVS-reinigingsmiddel "
                "kan helpen wanneer je ze wilt verwijderen."
            ),
            (
                "Controleer per model of de pan vaatwasserbestendig is; "
                "handwas kan de uiterlijke afwerking langer mooi houden."
            ),
        ],
        "outro": (
            "Ongecoat RVS hoeft niet te worden ingebrand zoals gietijzer "
            "of koolstofstaal. Reinig een nieuwe pan voor het eerste "
            "gebruik volgens de aanwijzingen van de fabrikant."
        ),
    },
    "faq": {
        "title": "Veelgestelde vragen over RVS-koekenpannen en koekenpannensets",
        "items": [
            {
                "q": "Hoe wordt de sterrenbeoordeling bepaald?",
                "a": (
                    "Onze redactionele beoordeling is een gewogen score. "
                    "Bakresultaat en temperatuurgedrag tellen voor 25% mee, "
                    "constructie en verwachte duurzaamheid voor 25%, "
                    "gebruiksgemak en veelzijdigheid voor 20%, reiniging "
                    "en onderhoud voor 15% en prijs-kwaliteit voor 15%. "
                    "Winkelbeoordelingen vormen niet onze sterrenbeoordeling."
                ),
            },
            {
                "q": "Worden gebruikersreviews meegenomen in de beoordeling?",
                "a": (
                    "Ja, als aanvullende bron. Een individuele review bepaalt "
                    "de score niet. Terugkerende, productspecifieke ervaringen "
                    "kunnen meewegen als duidelijk is dat ze over hetzelfde "
                    "model of dezelfde technische uitvoering gaan."
                ),
            },
            {
                "q": "Waarom krijgt niet ieder formaat een Budget- of Premium keuze?",
                "a": (
                    "We kennen een badge alleen toe wanneer een duidelijke "
                    "kandidaat aanwezig is. De laagste prijs levert niet "
                    "automatisch de Budget keuze op en de duurste pan "
                    "is niet vanzelf de Premium keuze."
                ),
            },
            {
                "q": "Heeft iedere RVS-koekenpan een ongecoat bakoppervlak?",
                "a": (
                    "Nee. Een pan kan een RVS-buitenkant combineren met "
                    "een aangebrachte antiaanbaklaag. In deze vergelijking "
                    "nemen we uitsluitend pannen op waarvan voor het exacte "
                    "model is bevestigd dat het bakoppervlak uit ongecoat "
                    "roestvrij staal bestaat."
                ),
            },
            {
                "q": "Betekent ongecoat RVS automatisch dat de pan PFAS-vrij is?",
                "a": (
                    "Een daadwerkelijk ongecoat RVS-bakoppervlak bevat geen "
                    "aangebrachte PFAS-antiaanbaklaag. Controle van het "
                    "bakoppervlak is daarom belangrijker dan alleen een "
                    "algemene PFAS-vrij- of PFOA-vrij-claim op de verpakking. "
                    "Een claim over de hele pan vergt afzonderlijke onderbouwing."
                ),
            },
            {
                "q": "Wat betekent full-clad of volledig meerlaags RVS?",
                "a": (
                    "Bij full-clad lopen de verbonden metaal­lagen door "
                    "van de bodem tot in de zijwanden. Vaak combineert "
                    "de constructie RVS met aluminium, soms met andere "
                    "warmtegeleidende materialen. Dit verschilt van een "
                    "pan waarbij de meerlaagse constructie vooral in "
                    "de bodem zit."
                ),
            },
            {
                "q": "Wat is het verschil tussen een capsulebodem en een volledig meerlaagse pan?",
                "a": (
                    "Bij een capsule- of sandwichbodem bevindt de "
                    "warmtegeleidende meerlaagse constructie zich vooral "
                    "in de bodem. Bij een volledig meerlaagse pan loopt "
                    "deze opbouw door in de zijwanden. Beide constructies "
                    "kunnen geschikt zijn; de totale uitvoering telt mee."
                ),
            },
            {
                "q": "Is een 5-ply- of 7-plypan beter dan een 3-plypan?",
                "a": (
                    "Niet automatisch. Naast het aantal lagen zijn onder "
                    "meer de dikte, het kernmateriaal, de bodemmaat en "
                    "de totale constructie bepalend. Zonder goede "
                    "testgegevens trekken we geen stellige conclusies "
                    "over de bakprestaties uitsluitend uit het aantal lagen."
                ),
            },
            {
                "q": "Zijn de geselecteerde RVS-koekenpannen geschikt voor inductie?",
                "a": (
                    "De huidige selectie bevat inductiegeschikte modellen. "
                    "Controleer per pan de productspecificaties en stem "
                    "de diameter van de bodem af op de kookzone. De "
                    "bovenranddiameter is niet hetzelfde als de bodemdiameter."
                ),
            },
            {
                "q": "Hoe voorkom ik dat eten aanbakt in een RVS-pan?",
                "a": (
                    "Verwarm geleidelijk voor, gebruik voldoende olie "
                    "of boter en pas de temperatuur aan het ingrediënt aan. "
                    "Laat vlees eerst een korst vormen voordat je het "
                    "keert. Voor eieren en vis werkt een lagere "
                    "temperatuur vaak beter dan heel heet voorverwarmen."
                ),
            },
            {
                "q": "Moet ik de waterdruppeltest gebruiken?",
                "a": (
                    "Nee. De test laat zien dat de pan een bepaalde "
                    "hoge temperatuur heeft bereikt, maar die is niet "
                    "voor alle gerechten geschikt. Kies de temperatuur "
                    "op basis van wat je bereidt."
                ),
            },
            {
                "q": "Moet een RVS-koekenpan worden ingebrand?",
                "a": (
                    "Nee. Een ongecoate RVS-pan hoeft niet te worden "
                    "ingebrand zoals gietijzer of koolstofstaal. Was "
                    "een nieuwe pan voor het eerste gebruik volgens "
                    "de aanwijzingen van de fabrikant."
                ),
            },
            {
                "q": "Mag een RVS-koekenpan in de oven of onder de ovengrill?",
                "a": (
                    "Dat verschilt per model. De toegestane temperatuur "
                    "hangt af van de panconstructie en de handgreep. "
                    "Geschiktheid voor de oven betekent niet automatisch "
                    "dat ook gebruik onder de ovengrill is toegestaan."
                ),
            },
            {
                "q": "Mag een RVS-koekenpan in de vaatwasser?",
                "a": (
                    "Veel modellen zijn vaatwasserbestendig, maar niet "
                    "allemaal. Controleer de productspecificaties. "
                    "Handwas kan bovendien helpen de afwerking "
                    "en glans te behouden."
                ),
            },
            {
                "q": "Hoe verwijder ik aangekoekte resten uit RVS?",
                "a": (
                    "Laat de pan afkoelen en week aangekoekte resten "
                    "in warm water. Een kleine hoeveelheid water zachtjes "
                    "verwarmen kan resten losmaken. Reinig daarna met "
                    "een geschikte spons en mild afwasmiddel."
                ),
            },
            {
                "q": "Wat betekent regenboogverkleuring op RVS?",
                "a": (
                    "Een gekleurde waas na verhitting is doorgaans "
                    "een cosmetische verkleuring en geen aanwijzing dat "
                    "de pan onbruikbaar is. Gebruik zo nodig een geschikt "
                    "RVS-reinigingsmiddel volgens de instructies."
                ),
            },
            {
                "q": "Welke maat RVS-koekenpan heb ik nodig?",
                "a": (
                    "Een pan van 20–24 cm is vaak voldoende voor kleine "
                    "porties. Een pan van 26–28 cm biedt meer ruimte "
                    "voor dagelijks gebruik. De formaten 30–32 cm "
                    "passen vooral bij grote porties en ruime kookzones. "
                    "Bekijk ook onze "
                    '<a href="/blogs/welke-maat-koekenpan/">uitgebreide maattabel</a>.'
                ),
            },
            {
                "q": "Welke RVS-koekenpannenset past bij mijn huishouden?",
                "a": (
                    "De combinatie 20 + 28 cm is geschikt voor wie "
                    "vooral een kleine en een ruime pan gebruikt. "
                    "Met 24 + 28 cm heb je twee dagelijkse formaten. "
                    "Een set van 20 + 24 + 28 cm biedt meer keuze, "
                    "maar is vooral interessant als je alle drie "
                    "de maten regelmatig gebruikt."
                ),
            },
            {
                "q": "Is een RVS-koekenpannenset voordeliger dan losse pannen?",
                "a": (
                    "Niet altijd. Vergelijk de reguliere prijs van "
                    "de exacte set met de totale reguliere prijs "
                    "van dezelfde losse pannen. Let ook op eventuele "
                    "accessoires en technische verschillen tussen uitvoeringen."
                ),
            },
            {
                "q": "Wat is het verschil tussen een RVS-pan en een keramische koekenpan?",
                "a": (
                    "Een RVS-pan heeft een ongecoat bakoppervlak en "
                    "is geschikt voor krachtig bruinen en afblussen, "
                    "maar vraagt meer aandacht voor baktechniek. "
                    "Een keramische koekenpan heeft een antiaanbaklaag "
                    "en is vaak praktischer voor kwetsbare ingrediënten. "
                    'Lees onze <a href="/blogs/keramische-vs-rvs-koekenpan/">'
                    "vergelijking van keramische en RVS-koekenpannen</a>."
                ),
            },
            ],
            },

            "related_categories": {
            "title": "Gerelateerde categorieën",
            "items": [
            {
                "label": "PFAS-vrije keramische koekenpannen",
                "url": "/koekenpannen/",
                "subtitle": "Koekenpannen met een keramische antiaanbaklaag",
            },
            {
                "label": "PFAS-vrije hapjespannen",
                "url": "/hapjespannen/",
                "subtitle": "Pannen met hogere rand en meer inhoud",
            },
            {
                "label": "PFAS-vrije wokpannen",
                "url": "/wokpannen/",
                "subtitle": "Voor roerbakken en snelle bereidingen",
            },
            ],
            },
            }