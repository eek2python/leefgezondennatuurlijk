"""Generic, category-agnostic capacity helpers.

Reusable for any product with one or more containers (storage containers,
meal prep boxes, lunch boxes, drink bottles, mixing bowls, baking dishes,
etc.). All values are milliliters.
"""


def _clean_capacities(capacities):
    """Return a sorted list of valid capacities (positive numbers, in ml).

    Ignores None, zero, negative numbers, booleans, strings and any other
    non-numeric values. Accepts a single number as well as a list/tuple.
    """
    if capacities is None:
        return []
    if isinstance(capacities, bool):
        return []
    if isinstance(capacities, (int, float)):
        capacities = [capacities]
    if not isinstance(capacities, (list, tuple)):
        return []
    valid = []
    for value in capacities:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and value > 0:
            valid.append(value)
    return sorted(valid)


def _format_ml(ml):
    """Format a single millilitre value: 800 -> '800 ml', 1500 -> '1,5 L'."""
    if ml >= 1000:
        liters = ml / 1000.0
        text = f"{liters:.2f}".rstrip("0").rstrip(".")
        return f"{text.replace('.', ',')} L"
    if float(ml).is_integer():
        return f"{int(ml)} ml"
    return f"{str(ml).replace('.', ',')} ml"


def format_capacities(capacities):
    """Human-friendly capacity text.

    [800]                 -> '800 ml'
    [1500]                -> '1,5 L'
    [700, 700, 1500]      -> '2 × 700 ml + 1,5 L'
    [1000, 1000, 1000]    -> '3 × 1 L'
    [370, 370, 640, 1040] -> '2 × 370 ml + 640 ml + 1,04 L'
    Invalid / empty input -> ''
    """
    values = _clean_capacities(capacities)
    if not values:
        return ""
    groups = []  # list of (value, count), ascending
    for value in values:
        if groups and groups[-1][0] == value:
            groups[-1][1] += 1
        else:
            groups.append([value, 1])
    parts = []
    for value, count in groups:
        label = _format_ml(value)
        parts.append(label if count == 1 else f"{count} × {label}")
    return " + ".join(parts)


def calculate_total_capacity(capacities):
    """Total capacity in ml. [700, 700, 1500] -> 2900. Invalid input -> 0."""
    total = sum(_clean_capacities(capacities))
    return int(total) if float(total).is_integer() else total


def format_total_capacity(total_ml):
    """800 -> '800 ml', 1500 -> '1,5 L', 2900 -> '2,9 L'. Invalid -> ''."""
    if isinstance(total_ml, bool) or not isinstance(total_ml, (int, float)):
        return ""
    if total_ml <= 0:
        return ""
    return _format_ml(total_ml)


def get_capacity_display(product):
    """Return (formatted_capacity, formatted_total_capacity) for a product dict.

    Field priority: 'capacities' -> legacy 'capacity' -> empty strings.
    The total is only returned when the product has more than one container.
    """
    raw = product.get("capacities")
    if raw is None:
        raw = product.get("capacity")
    values = _clean_capacities(raw)
    formatted = format_capacities(values)
    formatted_total = ""
    if len(values) > 1:
        formatted_total = format_total_capacity(calculate_total_capacity(values))
    return formatted, formatted_total
