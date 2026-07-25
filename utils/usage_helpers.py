"""Helpers voor gestructureerde gebruiksinformatie ("Geschikt voor").

Productdicts kunnen een optionele ``usage``-structuur hebben:

    "usage": {
        "oven": {"container": True, "lid": False, "note": "Alleen het glazen bakje"},
        "microwave": {"container": True, "lid": True, "note": "Ventiel openen"},
        "freezer": {"container": True, "lid": None, "note": None},
        "dishwasher": {"container": None, "lid": None, "note": None},
    }

Regels:
- ``None`` betekent onbekend en wordt nooit als "Nee" getoond;
- een rij zonder bekende bakje-waarde wordt niet getoond;
- varianten mogen per veld afwijken via een eigen (gedeeltelijke)
  ``usage``-dict die over de productbasis wordt samengevoegd.
"""

USAGE_KEYS = ("oven", "microwave", "freezer", "dishwasher")

USAGE_LABELS = {
    "oven": "Oven",
    "microwave": "Magnetron",
    "freezer": "Vriezer",
    "dishwasher": "Vaatwasser",
}

_FIELD_KEYS = ("container", "lid", "note")


def merge_usage(base, override):
    """Merge a variant-level (partial) usage dict over the product-level
    base. Only keys/fields present in the override replace base values."""
    if not base and not override:
        return None
    result = {}
    for key in USAGE_KEYS:
        base_entry = (base or {}).get(key)
        over_entry = (override or {}).get(key)
        if base_entry is None and over_entry is None:
            continue
        entry = dict(base_entry or {})
        if over_entry:
            for field in _FIELD_KEYS:
                if field in over_entry:
                    entry[field] = over_entry[field]
        result[key] = entry
    return result or None


def _row_text(entry):
    container = entry.get("container")
    lid = entry.get("lid")
    note = entry.get("note")
    if container is None:
        return None  # onbekend: niet tonen
    if container is False:
        return "Nee"
    # container is True
    if lid is False:
        text = "Ja, alleen zonder deksel"
        if note:
            text = f"Ja, {_lower_first(note)}"
        return text
    if lid is True:
        if note:
            return f"Ja, {_lower_first(note)}"
        return "Ja"
    # lid onbekend
    if note:
        return f"Bakje: ja, {_lower_first(note)}"
    return "Bakje: ja"


def _lower_first(text):
    text = str(text).strip()
    return text[:1].lower() + text[1:] if text else text


def build_usage_display(usage):
    """Return a list of ``{"key", "label", "text"}`` rows for the template.
    Unknown values are skipped entirely; returns [] when nothing is known."""
    if not usage:
        return []
    rows = []
    for key in USAGE_KEYS:
        entry = usage.get(key)
        if not isinstance(entry, dict):
            continue
        text = _row_text(entry)
        if text:
            rows.append({"key": key, "label": USAGE_LABELS[key], "text": text})
    return rows


def validate_usage(usage, where=""):
    """Return a list of issue strings for an invalid usage structure."""
    issues = []
    if usage is None:
        return issues
    if not isinstance(usage, dict):
        return [f"{where}: usage is geen dict"]
    for key, entry in usage.items():
        if key not in USAGE_KEYS:
            issues.append(f"{where}: onbekende usage-sleutel '{key}'")
            continue
        if not isinstance(entry, dict):
            issues.append(f"{where}: usage['{key}'] is geen dict")
            continue
        for field, value in entry.items():
            if field not in _FIELD_KEYS:
                issues.append(f"{where}: onbekend usage-veld '{key}.{field}'")
            elif field in ("container", "lid") and value not in (True, False, None):
                issues.append(
                    f"{where}: usage['{key}']['{field}'] moet True/False/None zijn"
                )
            elif field == "note" and value is not None and not isinstance(value, str):
                issues.append(f"{where}: usage['{key}']['note'] moet tekst of None zijn")
    return issues
