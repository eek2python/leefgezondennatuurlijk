"""Shared navigation and presentation metadata for available appliances."""

APPLIANCE_CATEGORIES = (
    {
        "key": "airfryers",
        "label": "Airfryers",
        "url_name": "airfryers",
        "image": "images/airfryers.jpg",
        "description": (
            "Heteluchtbereiding met compacte elektrische verwarming. Vergelijk "
            "inhoud, bakresultaat, gebruiksgemak, reiniging en materialen en "
            "coatings van mand en bakoppervlak."
        ),
    },
    {
        "key": "gourmetsets",
        "label": "Gourmetsets",
        "url_name": "gourmetsets",
        "image": "",
        "description": (
            "Vergelijk aantal personen, bakoppervlak, pannetjes, vermogen en "
            "temperatuurregeling. We controleren per onderdeel welke "
            "PFAS-vrije coating of materiaalkeuze is bevestigd."
        ),
    },
)


def gourmet_specifications(product):
    """Display supplied facts only; zero pans is a fact, not a missing value."""
    fields = (
        ("Materiaal", "material"),
        ("Aantal personen", "capacity_persons"),
        ("Aantal pannetjes", "number_of_pans"),
        ("Bakoppervlak", "cooking_surface_dimensions"),
        ("Type plaat", "plate_type"),
        ("Vermogen (W)", "power_w"),
        ("Temperatuurregeling", "temperature_control"),
        ("Afneembare onderdelen", "removable_parts"),
        ("Vaatwasserbestendige onderdelen", "dishwasher_safe_parts"),
        ("Reiniging", "cleaning"),
        ("Extra functies", "extra_functions"),
    )
    rows = []
    for label, key in fields:
        value = product.get(key)
        if value is None or value == "" or value == []:
            continue
        if isinstance(value, list):
            value = " · ".join(value)
        rows.append({"label": label, "value": value})
    claim = product.get("pfas_claim") or {}
    for label, key in (("PFAS-vrij: bakplaat", "grill_plate"), ("PFAS-vrij: pannetjes", "pans")):
        if claim.get(key):
            rows.append({"label": label, "value": claim[key]})
    return rows
