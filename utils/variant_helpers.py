"""Reusable helpers for products with shape/format variants.

A product may define a ``variants`` list where each variant is a dict with
at least an ``id`` and ``label``. Variant-specific commercial data (image,
capacities, price, affiliate_url, availability, price_last_checked) lives on
the variant; shared editorial data (name, description, pros, cons, rating,
verdict, award) stays at product-family level.

Colour-swatch variants (used on airfryers) do not have an ``id`` key and are
intentionally left untouched by these helpers — they are handled by the
existing swatch system in ``templates/partials/product_block.html``.
"""

from django.templatetags.static import static as static_url

from utils.product_helpers import (
    _clean_capacities,
    calculate_total_capacity,
    format_capacities,
    format_total_capacity,
)


def prepare_product_variants(product):
    """Enrich a product dict that has shape/format variants.

    Adds:
      - ``shape_variants``: list of enriched variant dicts, each with
        ``formatted_capacity``, ``total_capacity_ml``,
        ``formatted_total_capacity``, ``container_count``, ``image_url``,
        ``alt_text`` and ``selected_summary``
      - ``default_variant``: the variant marked ``is_default`` (or the first)
      - ``capacity_summary``: family-level capacity text for comparison
        tables ("Afhankelijk van uitvoering" unless all variants share the
        same valid capacities)
    Also copies the default variant's commercial fields (image, capacities,
    price, affiliate_url, availability, currency, price_last_checked) up to
    product level so detail pages, JSON-LD and no-JS rendering keep working.

    Products without shape variants are returned unchanged.
    """
    variants = product.get("variants")
    if not isinstance(variants, list) or not variants:
        return
    if not all(isinstance(v, dict) and v.get("id") for v in variants):
        return  # colour-swatch variants — handled by the swatch system

    ids = [v["id"] for v in variants]
    if len(ids) != len(set(ids)):
        raise ValueError(
            f"Duplicate variant ids for product '{product.get('slug')}': {ids}"
        )

    family_name = product.get("name", "")
    prepared = []
    default = None
    for v in variants:
        pv = dict(v)
        caps = _clean_capacities(pv.get("capacities"))
        pv["container_count"] = len(caps)
        pv["formatted_capacity"] = format_capacities(caps)
        pv["total_capacity_ml"] = calculate_total_capacity(caps)
        pv["formatted_total_capacity"] = (
            format_total_capacity(pv["total_capacity_ml"]) if len(caps) > 1 else ""
        )
        pv["label"] = pv.get("label") or pv["id"]
        pv["shape"] = pv.get("shape") or pv["label"]
        pv["affiliate_url"] = pv.get("affiliate_url") or ""
        pv["availability"] = pv.get("availability") or ""
        pv["image_path"] = pv.get("image_path") or product.get("image_path", "")
        pv["image_url"] = (
            static_url(f"{pv['image_path']}/{pv['image']}") if pv.get("image") else ""
        )
        pv["alt_text"] = f"{family_name} {pv['label'].lower()}".strip()
        summary = f"Geselecteerd: {pv['label']}"
        if pv["formatted_capacity"] and pv["formatted_capacity"] != pv["label"]:
            summary += f" · {pv['formatted_capacity']}"
        pv["selected_summary"] = summary
        if default is None and pv.get("is_default"):
            default = pv
        prepared.append(pv)

    if default is None:
        default = prepared[0]

    product["shape_variants"] = prepared
    product["default_variant"] = default

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
        value = default.get(field)
        if value not in (None, "", []):
            product[field] = value

    formatted_list = [pv["formatted_capacity"] for pv in prepared]
    if all(formatted_list) and len(set(formatted_list)) == 1:
        product["capacity_summary"] = formatted_list[0]
    else:
        product["capacity_summary"] = "Afhankelijk van uitvoering"
