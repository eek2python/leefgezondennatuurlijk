"""Reusable helpers for products with variant selectors.

A product family may be sold in multiple executions (shapes, capacities,
colours-as-buttons, set compositions, …). The generic structure is:

    "variant_selectors": [
        {"key": "shape", "label": "Vorm"},
        {"key": "capacity", "label": "Inhoud"},
    ],
    "variants": [
        {
            "id": "round-750",
            "options": {"shape": "round", "capacity": 750},
            "option_labels": {"shape": "Rond", "capacity": "750 ml"},
            "capacities": [750],
            "image": "...", "price": ..., "affiliate_url": ...,
            "is_default": True,
        },
        ...
    ]

Only combinations that really exist are listed; every variant carries its
own commercial data (image, price, affiliate_url, availability,
price_last_checked) while shared editorial data (name, description, pros,
cons, rating, verdict, award) stays at product-family level.

Backward compatibility: the older single-selector structure
(``variant_label`` + variants with ``label``/``shape``/``capacity_ml``
fields) is normalised on the fly by :func:`normalize_product_variant_schema`.

Colour-swatch variants (used on airfryers) do not have an ``id`` key and are
intentionally left untouched by these helpers — they are handled by the
existing swatch system in ``templates/partials/product_block.html``.
"""

import logging

from django.templatetags.static import static as static_url

from utils.product_helpers import (
    _clean_capacities,
    calculate_total_capacity,
    format_capacities,
    format_total_capacity,
)
from utils.usage_helpers import build_usage_display, merge_usage

logger = logging.getLogger(__name__)

#: Selector keys the system knows how to treat specially. Unknown keys are
#: allowed but produce a development warning.
KNOWN_SELECTOR_KEYS = {"shape", "capacity", "color", "composition"}

_LEGACY_LABEL_TO_KEY = {
    "inhoud": "capacity",
    "vorm": "shape",
    "kleur": "color",
    "samenstelling": "composition",
}


def _is_button_variant_list(variants):
    return (
        isinstance(variants, list)
        and bool(variants)
        and all(isinstance(v, dict) and v.get("id") for v in variants)
    )


def normalize_product_variant_schema(product):
    """Normalise a product's variant data to the generic multi-selector
    structure, in place.

    Returns a list of selector dicts (``[{"key", "label"}, …]``) or ``None``
    when the product has no button-variant data (no variants at all, or
    colour-swatch variants without ``id``).

    Products that already define ``variant_selectors`` plus per-variant
    ``options`` are left as-is. Legacy products using ``variant_label`` and
    flat fields (``label``, ``shape``, ``capacity_ml``) are converted:

    - ``variant_label`` "Inhoud" becomes one ``capacity`` selector,
      "Vorm" becomes one ``shape`` selector;
    - ``capacity_ml`` becomes ``options["capacity"]``;
    - a single-value ``capacities`` list is used as capacity value when
      ``capacity_ml`` is absent;
    - visible labels are built from the existing ``label`` field.
    """
    variants = product.get("variants")
    if not _is_button_variant_list(variants):
        return None

    selectors = product.get("variant_selectors")
    if isinstance(selectors, list) and selectors:
        _validate_selectors(product, selectors)
        for v in variants:
            v.setdefault("options", {})
            v.setdefault("option_labels", {})
        return selectors

    # Legacy single-selector structure.
    legacy_label = product.get("variant_label") or "Uitvoering"
    key = _LEGACY_LABEL_TO_KEY.get(legacy_label.strip().lower(), "shape")
    selectors = [{"key": key, "label": legacy_label}]
    product["variant_selectors"] = selectors

    for v in variants:
        options = dict(v.get("options") or {})
        option_labels = dict(v.get("option_labels") or {})
        label = v.get("label") or v["id"]
        if key not in options:
            if key == "capacity":
                value = v.get("capacity_ml")
                caps = _clean_capacities(v.get("capacities"))
                if value is None and len(caps) == 1:
                    value = caps[0]
                options[key] = value if value is not None else label
            elif key == "shape" and v.get("shape"):
                options[key] = v["shape"]
            else:
                options[key] = label
        option_labels.setdefault(key, label)
        v["options"] = options
        v["option_labels"] = option_labels
    return selectors


def _validate_selectors(product, selectors):
    keys = []
    for sel in selectors:
        if not isinstance(sel, dict) or not sel.get("key") or not sel.get("label"):
            raise ValueError(
                f"Variant selector without key/label on product "
                f"'{product.get('slug')}': {sel!r}"
            )
        keys.append(sel["key"])
        if sel["key"] not in KNOWN_SELECTOR_KEYS:
            logger.warning(
                "Product '%s' uses unknown variant selector key '%s'",
                product.get("slug"),
                sel["key"],
            )
    if len(keys) != len(set(keys)):
        raise ValueError(
            f"Duplicate variant selector keys on product "
            f"'{product.get('slug')}': {keys}"
        )


def _validate_variants(product, selectors, variants):
    ids = [v["id"] for v in variants]
    if len(ids) != len(set(ids)):
        raise ValueError(
            f"Duplicate variant ids for product '{product.get('slug')}': {ids}"
        )

    combos = set()
    selector_keys = [s["key"] for s in selectors]
    for v in variants:
        options = v.get("options") or {}
        for key in selector_keys:
            if key not in options or options[key] in (None, ""):
                raise ValueError(
                    f"Variant '{v['id']}' of product '{product.get('slug')}' "
                    f"misses a value for selector '{key}'"
                )
            label = (v.get("option_labels") or {}).get(key)
            if not label:
                raise ValueError(
                    f"Variant '{v['id']}' of product '{product.get('slug')}' "
                    f"misses a visible label for selector '{key}'"
                )
        combo = tuple(options[k] for k in selector_keys)
        if combo in combos:
            raise ValueError(
                f"Duplicate option combination {combo!r} on product "
                f"'{product.get('slug')}'"
            )
        combos.add(combo)

        caps = v.get("capacities")
        if caps is not None:
            for c in caps:
                if isinstance(c, (int, float)) and c <= 0:
                    raise ValueError(
                        f"Non-positive capacity {c!r} in variant '{v['id']}' "
                        f"of product '{product.get('slug')}'"
                    )

    defaults = [v for v in variants if v.get("is_default")]
    if len(defaults) > 1:
        raise ValueError(
            f"More than one default variant on product '{product.get('slug')}'"
        )
    if not defaults:
        logger.warning(
            "Product '%s' has no default variant; using the first one",
            product.get("slug"),
        )


def _variant_display_label(variant, selectors):
    labels = [
        (variant.get("option_labels") or {}).get(s["key"], "") for s in selectors
    ]
    labels = [l for l in labels if l]
    return " · ".join(labels) if labels else variant.get("label") or variant["id"]


def build_selector_options(selectors, variants):
    """Return ``{selector_key: [{"value", "label"}, …]}`` with unique options
    in consistent order: capacities numerically sorted, everything else in
    first-seen (data) order."""
    result = {}
    for sel in selectors:
        key = sel["key"]
        seen = {}
        for v in variants:
            value = v["options"][key]
            if value not in seen:
                seen[value] = (v.get("option_labels") or {}).get(key, str(value))
        items = [{"value": val, "label": lab} for val, lab in seen.items()]
        if key == "capacity" and all(
            isinstance(i["value"], (int, float)) for i in items
        ):
            items.sort(key=lambda i: i["value"])
        result[key] = items
    return result


def _option_available(variants, key, value, selections, earlier_keys):
    """True when at least one variant has ``options[key] == value`` and
    matches the current selections of all *earlier* (higher-priority)
    selectors. Options that fail this check are hidden: earlier selectors
    always show all their options, later selectors only show options that
    actually exist for the combination chosen so far."""
    for v in variants:
        options = v["options"]
        if options.get(key) != value:
            continue
        if all(options.get(k) == selections.get(k) for k in earlier_keys):
            return True
    return False


def rebuild_variant_selector_groups(product):
    """(Re)compute ``variant_selector_groups`` — the template-facing list of
    selector groups with per-option active/available state — based on the
    current ``default_variant``. Call again after swapping the display
    variant (e.g. under an active size filter)."""
    selectors = product.get("variant_selectors") or []
    variants = product.get("shape_variants") or []
    display = product.get("default_variant")
    if not selectors or not variants or not display:
        return
    selections = display["options"]
    options_by_key = product.get("variant_selector_options") or {}
    groups = []
    earlier_keys = []
    for sel in selectors:
        key = sel["key"]
        options = []
        for opt in options_by_key.get(key, []):
            options.append(
                {
                    "value": opt["value"],
                    "label": opt["label"],
                    "active": selections.get(key) == opt["value"],
                    "available": _option_available(
                        variants, key, opt["value"], selections, earlier_keys
                    ),
                }
            )
        groups.append(
            {
                "key": key,
                "label": sel["label"],
                "options": options,
                "show": len([o for o in options if o["available"]]) > 1
                or len(options) > 1,
            }
        )
        earlier_keys.append(key)
    product["variant_selector_groups"] = groups


def _copy_commercial_fields(product, variant):
    for field in (
        "image",
        "image_path",
        "capacities",
        "price",
        "currency",
        "availability",
        "affiliate_url",
        "price_last_checked",
    ):
        value = variant.get(field)
        if value not in (None, "", []):
            product[field] = value


def prepare_product_variants(product):
    """Enrich a product dict that has button-style variants (one or more
    selectors).

    Adds:
      - ``variant_selectors`` (normalised) and ``variant_selector_options``
      - ``shape_variants``: enriched variant dicts, each with
        ``formatted_capacity``, ``total_capacity_ml``,
        ``formatted_total_capacity``, ``container_count``, ``image_url``,
        ``alt_text``, ``selected_summary``, ``options``, ``option_labels``
      - ``default_variant``: the variant marked ``is_default`` (or the first)
      - ``variant_selector_groups``: per-selector option lists with
        active/available state for the server-rendered default
      - ``variant_json_data``: JSON-safe payload for the front-end script
      - ``capacity_summary``: family-level capacity text for comparison
        tables ("Afhankelijk van uitvoering" unless all variants share the
        same valid capacities)
    Also copies the default variant's commercial fields (image, capacities,
    price, affiliate_url, availability, currency, price_last_checked) up to
    product level so detail pages, JSON-LD and no-JS rendering keep working.

    Products without button variants are returned unchanged.
    """
    selectors = normalize_product_variant_schema(product)
    if selectors is None:
        return
    variants = product["variants"]
    _validate_variants(product, selectors, variants)

    family_name = product.get("name", "")
    prepared = []
    default = None
    for v in variants:
        pv = dict(v)
        pv["options"] = dict(v["options"])
        pv["option_labels"] = dict(v["option_labels"])
        caps = _clean_capacities(pv.get("capacities"))
        if not caps:
            cap_value = pv["options"].get("capacity")
            if isinstance(cap_value, (int, float)) and cap_value > 0:
                caps = [cap_value]
                pv["capacities"] = caps
        pv["container_count"] = len(caps)
        pv["formatted_capacity"] = format_capacities(caps)
        pv["total_capacity_ml"] = calculate_total_capacity(caps)
        pv["formatted_total_capacity"] = (
            format_total_capacity(pv["total_capacity_ml"]) if len(caps) > 1 else ""
        )
        pv["label"] = pv.get("label") or _variant_display_label(pv, selectors)
        pv["display_label"] = _variant_display_label(pv, selectors)
        pv["shape"] = pv.get("shape") or pv["label"]
        pv["affiliate_url"] = pv.get("affiliate_url") or ""
        pv["availability"] = pv.get("availability") or ""
        pv["image_path"] = pv.get("image_path") or product.get("image_path", "")
        pv["image_url"] = (
            static_url(f"{pv['image_path']}/{pv['image']}") if pv.get("image") else ""
        )
        pv["alt_text"] = f"{family_name} {pv['display_label'].lower()}".strip()
        summary = f"Geselecteerd: {pv['display_label']}"
        formatted = pv["formatted_capacity"]
        if formatted:
            normalized = formatted.replace(",", ".")
            label_values = {pv["display_label"].replace(",", ".")} | {
                str(v).replace(",", ".") for v in pv["option_labels"].values()
            }
            if normalized not in label_values:
                summary += f" · {formatted}"
        pv["selected_summary"] = summary
        pv["usage"] = merge_usage(product.get("usage"), v.get("usage"))
        pv["usage_display"] = build_usage_display(pv["usage"])
        if default is None and pv.get("is_default"):
            default = pv
        prepared.append(pv)

    if default is None:
        default = prepared[0]

    product["shape_variants"] = prepared
    product["default_variant"] = default
    product["variant_selector_options"] = build_selector_options(
        selectors, prepared
    )
    rebuild_variant_selector_groups(product)

    _copy_commercial_fields(product, default)
    product["usage_display"] = default["usage_display"]

    product["variant_json_data"] = {
        "selectors": [
            {"key": s["key"], "label": s["label"]} for s in selectors
        ],
        "default_id": default["id"],
        "variants": [
            {
                "id": pv["id"],
                "options": pv["options"],
                "option_labels": pv["option_labels"],
                "label": pv["display_label"],
                "image": pv["image_url"],
                "alt": pv["alt_text"],
                "capacity": pv["formatted_capacity"],
                "total_capacity": pv["formatted_total_capacity"],
                "affiliate_url": pv["affiliate_url"],
                "availability": pv["availability"],
                "price": pv.get("price"),
                "price_last_checked": pv.get("price_last_checked") or "",
                "summary": pv["selected_summary"],
                "usage": [
                    {"label": row["label"], "text": row["text"]}
                    for row in pv["usage_display"]
                ],
                "is_default": pv is default,
            }
            for pv in prepared
        ],
    }

    formatted_list = [pv["formatted_capacity"] for pv in prepared]
    if all(formatted_list) and len(set(formatted_list)) == 1:
        product["capacity_summary"] = formatted_list[0]
    else:
        product["capacity_summary"] = "Afhankelijk van uitvoering"


def set_display_variant(product, variant):
    """Make ``variant`` the server-rendered display variant: updates
    ``default_variant``, copies its commercial fields to product level, and
    rebuilds selector groups and the JSON default id so both selectors
    initialise on this variant."""
    product["default_variant"] = variant
    _copy_commercial_fields(product, variant)
    product["usage_display"] = variant.get("usage_display") or []
    rebuild_variant_selector_groups(product)
    json_data = product.get("variant_json_data")
    if json_data:
        json_data["default_id"] = variant["id"]
        for v in json_data["variants"]:
            v["is_default"] = v["id"] == variant["id"]
    product["matching_variant_id"] = variant["id"]
