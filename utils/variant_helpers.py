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
from dataclasses import dataclass

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


#: Variant-dependent fields that must be explicitly set (or cleared) on the
#: product dict for every display-variant selection. A missing value on the
#: selected variant must never silently keep the value of a previously
#: selected variant.
_VARIANT_COMMERCIAL_FIELDS = {
    "price": None,
    "currency": None,
    "availability": "",
    "affiliate_url": "",
    "retailer_url": "",
    "official_url": "",
    "availability_label": "",
    "price_last_checked": None,
    "capacities": [],
}


def normalize_optional_url(value):
    """Normaliseer een optioneel URL-veld naar een gestripte string.

    Ontbrekende waarden, ``None`` en niet-string-waarden worden een lege
    string; bestaande URL's worden inhoudelijk NIET gewijzigd (geen
    verwijdering van trackingparameters)."""
    if not isinstance(value, str):
        return ""
    return value.strip()


#: Ondersteunde linktypen voor :func:`resolve_product_link`.
LINK_TYPE_AFFILIATE = "affiliate"
LINK_TYPE_RETAILER = "retailer"
LINK_TYPE_OFFICIAL = "official"
LINK_TYPE_NONE = "none"

#: rel-attributen per linktype. Niet-affiliatelinks krijgen NOOIT
#: ``sponsored``.
LINK_REL = {
    LINK_TYPE_AFFILIATE: "nofollow sponsored noopener",
    LINK_TYPE_RETAILER: "nofollow noopener",
    LINK_TYPE_OFFICIAL: "noopener",
}

#: Knoplabels per linktype (bestaande siteconventie voor commerciële links).
LINK_LABEL = {
    LINK_TYPE_AFFILIATE: "Bekijk prijs & reviews →",
    LINK_TYPE_RETAILER: "Bekijk prijs & reviews →",
    LINK_TYPE_OFFICIAL: "Bekijk productspecificaties →",
}


@dataclass(frozen=True)
class ProductLink:
    """Resolved productlink voor templates en JSON-payloads."""

    url: str = ""
    link_type: str = LINK_TYPE_NONE
    label: str = ""
    rel: str = ""
    is_commercial: bool = False


def resolve_product_link(product, selected_variant=None):
    """Centrale linkresolver: affiliate → retailer → official → geen link.

    Strikte variantregels (zelfde bron-selectie als
    :func:`resolve_commercial_fields`):
      - producten met button-varianten gebruiken UITSLUITEND de URL-velden
        van de geselecteerde displayvariant; een lege URL op de variant
        valt nooit terug op een andere variant of op productniveau;
      - producten zonder button-varianten gebruiken productniveau-velden.
    """
    if selected_variant is None:
        selected_variant = product.get("default_variant")
    if product.get("shape_variants") and selected_variant:
        source = selected_variant
    else:
        source = product

    return _resolve_source_link(source)


def _resolve_source_link(source):
    """Los de link op uit één bron-dict (product óf variant) volgens de
    vaste prioriteit affiliate → retailer → official → geen link."""
    for field_name, link_type, is_commercial in (
        ("affiliate_url", LINK_TYPE_AFFILIATE, True),
        ("retailer_url", LINK_TYPE_RETAILER, True),
        ("official_url", LINK_TYPE_OFFICIAL, False),
    ):
        url = normalize_optional_url(source.get(field_name))
        if url:
            return ProductLink(
                url=url,
                link_type=link_type,
                label=LINK_LABEL[link_type],
                rel=LINK_REL[link_type],
                is_commercial=is_commercial,
            )
    return ProductLink()


def resolve_availability_label(product, selected_variant=None):
    """Beschikbaarheidstekst volgens dezelfde strikte bronselectie als
    :func:`resolve_product_link` (alleen getoond wanneer er geen link is)."""
    if selected_variant is None:
        selected_variant = product.get("default_variant")
    if product.get("shape_variants") and selected_variant:
        source = selected_variant
    else:
        source = product
    label = source.get("availability_label")
    return label.strip() if isinstance(label, str) else ""


def apply_resolved_link(product, selected_variant=None):
    """Zet ``product["resolved_link"]`` en ``product["availability_label"]``
    op basis van de centrale resolver, zodat templates alleen het reeds
    bepaalde resultaat renderen."""
    product["resolved_link"] = resolve_product_link(product, selected_variant)
    product["availability_label"] = resolve_availability_label(
        product, selected_variant
    )


def _apply_display_variant_fields(product, variant):
    """Deterministically project the display variant onto product level.

    Commercial fields are taken ONLY from the variant; when the variant
    lacks a field it is explicitly cleared (no fallback to another variant
    or to stale product-level data). Image/image_path fall back to the
    family-level original image — the documented product-family fallback —
    so detail pages and no-JS rendering always have an image.
    """
    for field, empty in _VARIANT_COMMERCIAL_FIELDS.items():
        value = variant.get(field)
        product[field] = value if value not in (None, "", []) else empty
    image = variant.get("image")
    if image:
        product["image"] = image
        product["image_path"] = variant.get("image_path") or product.get(
            "_family_image_path", product.get("image_path", "")
        )
    else:
        product["image"] = product.get("_family_image", "")
        product["image_path"] = product.get(
            "_family_image_path", product.get("image_path", "")
        )


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
    product.setdefault("_family_image", product.get("image", ""))
    product.setdefault("_family_image_path", product.get("image_path", ""))
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
        pv["affiliate_url"] = normalize_optional_url(pv.get("affiliate_url"))
        pv["retailer_url"] = normalize_optional_url(pv.get("retailer_url"))
        pv["official_url"] = normalize_optional_url(pv.get("official_url"))
        pv["availability_label"] = (
            pv["availability_label"].strip()
            if isinstance(pv.get("availability_label"), str)
            else ""
        )
        pv["availability"] = pv.get("availability") or ""
        pv["resolved_link"] = _resolve_source_link(pv)
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

    _apply_display_variant_fields(product, default)
    apply_resolved_link(product, default)
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
                "retailer_url": pv["retailer_url"],
                "official_url": pv["official_url"],
                "availability_label": pv["availability_label"],
                # Resolved linkgegevens (centrale resolver in Django, geen
                # dubbele bedrijfslogica in JavaScript).
                "resolved_url": pv["resolved_link"].url,
                "resolved_link_type": pv["resolved_link"].link_type,
                "resolved_label": pv["resolved_link"].label,
                "resolved_rel": pv["resolved_link"].rel,
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


def resolve_commercial_fields(product, display_variant=None):
    """Resolve the commercial fields (affiliate_url, price, availability,
    price_last_checked) for server-side rendering.

    Strict rules:
      - products with button variants use ONLY the display variant's own
        data — a missing field never silently falls back to another
        variant or to product level;
      - products without button variants use product-level fields.
    """
    if display_variant is None:
        display_variant = product.get("default_variant")
    if product.get("shape_variants") and display_variant:
        source = display_variant
    else:
        source = product
    return {
        "affiliate_url": normalize_optional_url(source.get("affiliate_url")),
        "retailer_url": normalize_optional_url(source.get("retailer_url")),
        "official_url": normalize_optional_url(source.get("official_url")),
        "availability_label": (
            source["availability_label"].strip()
            if isinstance(source.get("availability_label"), str)
            else ""
        ),
        "price": source.get("price"),
        "availability": source.get("availability") or "",
        "price_last_checked": source.get("price_last_checked"),
    }


def set_display_variant(product, variant):
    """Make ``variant`` the server-rendered display variant: updates
    ``default_variant``, copies its commercial fields to product level, and
    rebuilds selector groups and the JSON default id so both selectors
    initialise on this variant."""
    product["default_variant"] = variant
    _apply_display_variant_fields(product, variant)
    apply_resolved_link(product, variant)
    product["usage_display"] = variant.get("usage_display") or []
    rebuild_variant_selector_groups(product)
    json_data = product.get("variant_json_data")
    if json_data:
        json_data["default_id"] = variant["id"]
        for v in json_data["variants"]:
            v["is_default"] = v["id"] == variant["id"]
    product["matching_variant_id"] = variant["id"]
