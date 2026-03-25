RULES = {
    "category_key": "houten_snijplanken",
    "description": "Houten en bamboe snijplanken voor dagelijks gebruik. Geen kunststof, glas of composiet.",

    "allowed_material_keywords": ["hout", "bamboe", "esdoorn", "walnoot", "beuk", "eik", "acacia", "teak", "rubber", "wood", "bamboo", "maple", "walnut", "beech"],
    "forbidden_material_keywords": ["kunststof", "plastic", "glas", "glass", "marmer", "marble", "composiet", "composite", "epoxy", "silicoon"],

    "pfas_free_required": False,
    "pfas_free_keywords": [],

    "product_type_keywords": ["snijplank", "cutting board", "chopping board", "hakblok"],

    "size_sensitive": False,
    "size_field": None,
    "capacity_sensitive": False,

    "price_segments": {
        "budget": ["€"],
        "middenklasse": ["€€", "€€€"],
        "premium": ["€€€€"],
    },
    "price_thresholds": {
        "budget_max": 25.0,
        "premium_min": 70.0,
    },

    "badge_policy": {
        "core": ["Beste keuze", "Budget keuze", "Premium keuze"],
        "optional": ["Beste houtsoort"],
        "max_total": 4,
    },

    "preferred_criteria": [
        "hardhout of kwalitatief degelijk hout",
        "end-grain of stevige massieve opbouw",
        "goede dikte/stabiliteit",
        "praktisch formaat voor thuisgebruik",
        "aantoonbaar geschikt voor dagelijks gebruik",
    ],

    "exclusion_criteria": [
        {"field": "material", "keyword": "kunststof", "severity": "error", "message": "Kunststof snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "plastic", "severity": "error", "message": "Plastic snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "glas", "severity": "error", "message": "Glazen snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "glass", "severity": "error", "message": "Glazen snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "marmer", "severity": "error", "message": "Marmeren snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "composiet", "severity": "error", "message": "Composiet snijplanken zijn uitgesloten van deze categorie."},
        {"field": "material", "keyword": "silicoon", "severity": "warning", "message": "Siliconen materialen zijn niet toegestaan als hoofdmateriaal."},
    ],

    "replacement_rules": {
        "must_match_category": True,
        "must_match_material": True,
        "must_match_size": False,
        "must_match_price_segment": True,
        "require_pfas_free": False,
        "forbidden_materials": ["kunststof", "plastic", "glas", "marmer", "composiet"],
        "notes": "Vervang alleen door houten of bamboe snijplank. Vergelijkbaar formaat en kwaliteitssegment.",
    },

    "notes": "Glas, kunststof, marmer en composiet snijplanken zijn altijd uitgesloten. Zeer dunne, decoratieve plankjes met lage duurzaamheid kritisch beoordelen.",
}
