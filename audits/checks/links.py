"""Productlink-audit: affiliate- versus retailer- versus fabrikantlinks.

Controleert per product en per variant of de drie URL-velden
(``affiliate_url``, ``retailer_url``, ``official_url``) en
``availability_label`` correct worden gebruikt en of de centrale resolver
(:func:`utils.variant_helpers.resolve_product_link`) de juiste link, het
juiste rel-attribuut en het juiste label oplevert.

Belangrijk:
- meerdere URL's tegelijk zijn technisch toegestaan (de resolver heeft een
  vaste prioriteit) en worden daarom als INFO gemeld, niet als fout;
- er wordt NIET domeingebaseerd geraden of een URL werkelijk een actieve
  affiliatelink is; affiliate-URL's zonder expliciete bevestiging
  (``affiliate_confirmed: True`` in de data) worden alleen als
  handmatige-reviewmelding (INFO) gerapporteerd;
- de audit is read-only en wijzigt nooit productdata.
"""

import copy
from importlib import import_module
from urllib.parse import parse_qsl, urlparse

from audits.result import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    AuditIssue,
)
from audits.checks.variants import CATEGORY_SOURCES
from utils.variant_helpers import (
    LINK_TYPE_OFFICIAL,
    apply_resolved_link,
    normalize_optional_url,
    prepare_product_variants,
    resolve_product_link,
    resolve_swatch_variant_links,
    set_display_variant,
)

#: Queryparameters die op tracking duiden. Alleen gebruikt voor
#: retailer_url/official_url (die horen bij voorkeur schoon te zijn);
#: affiliate-URL's worden bewust NIET op trackingparameters beoordeeld.
_TRACKING_PARAM_PREFIXES = ("utm_", "aff", "partner", "pk_", "mc_")
_TRACKING_PARAM_EXACT = {"tag", "ref", "referrer", "gclid", "fbclid", "tt", "t"}

_URL_FIELDS = ("affiliate_url", "retailer_url", "official_url")


def _load_products(category):
    module = import_module(CATEGORY_SOURCES[category])
    products = getattr(module, "PRODUCTS", None)
    if isinstance(products, dict):
        return list(products.values())
    return list(products or [])


def _is_invalid_url(url):
    parsed = urlparse(url)
    return parsed.scheme not in ("http", "https") or not parsed.netloc


def _tracking_params(url):
    try:
        params = parse_qsl(urlparse(url).query, keep_blank_values=True)
    except ValueError:
        return []
    found = []
    for key, _ in params:
        lowered = key.lower()
        if lowered in _TRACKING_PARAM_EXACT or lowered.startswith(
            _TRACKING_PARAM_PREFIXES
        ):
            found.append(key)
    return found


def _check_source(issues, category, slug, source, variant_id=None):
    """Statische controles op één bron-dict (product of variant)."""
    urls = {f: normalize_optional_url(source.get(f)) for f in _URL_FIELDS}

    combos = (
        ("affiliate_url", "retailer_url", "affiliate_url_and_retailer_url_both_present"),
        ("affiliate_url", "official_url", "affiliate_url_and_official_url_both_present"),
        ("retailer_url", "official_url", "retailer_url_and_official_url_both_present"),
    )
    for f1, f2, code in combos:
        if urls[f1] and urls[f2]:
            issues.append(AuditIssue(
                code=code,
                severity=SEVERITY_INFO,
                message=(
                    f"Zowel {f1} als {f2} aanwezig; de resolver kiest "
                    f"{f1} (vaste prioriteit). Controleer of dit klopt."
                ),
                category=category,
                product_slug=slug,
                variant_id=variant_id,
            ))

    if urls["affiliate_url"] and not source.get("affiliate_confirmed"):
        issues.append(AuditIssue(
            code="affiliate_url_without_affiliate_confirmation",
            severity=SEVERITY_INFO,
            message=(
                "affiliate_url zonder expliciete affiliatebevestiging "
                "(affiliate_confirmed). Handmatig beoordelen of dit een "
                "echte affiliatelink is of naar retailer_url moet."
            ),
            category=category,
            product_slug=slug,
            variant_id=variant_id,
            field="affiliate_url",
            actual=urls["affiliate_url"],
        ))

    for field_name, url in urls.items():
        if url and _is_invalid_url(url):
            issues.append(AuditIssue(
                code="invalid_product_url",
                severity=SEVERITY_WARNING,
                message=f"Ongeldige URL in {field_name}: geen geldige http(s)-URL.",
                category=category,
                product_slug=slug,
                variant_id=variant_id,
                field=field_name,
                actual=url,
            ))

    for field_name in ("retailer_url", "official_url"):
        url = urls[field_name]
        if url:
            params = _tracking_params(url)
            if params:
                issues.append(AuditIssue(
                    code=f"tracking_parameters_in_{field_name}",
                    severity=SEVERITY_WARNING,
                    message=(
                        f"{field_name} bevat vermoedelijke trackingparameters "
                        f"({', '.join(params)}); deze horen bij voorkeur "
                        "niet in een niet-affiliatelink."
                    ),
                    category=category,
                    product_slug=slug,
                    variant_id=variant_id,
                    field=field_name,
                    actual=url,
                ))

    return urls


def _family_link_urls(product):
    """Oorspronkelijke productniveau-URL's (familie-fallbackbron)."""
    family = product.get("_family_links")
    source = family if family is not None else product
    return {f: normalize_optional_url(source.get(f)) for f in _URL_FIELDS}


def _expected_fallback_url(family_urls):
    """De URL die de familie-fallback volgens de vaste prioriteit oplevert."""
    for field_name in _URL_FIELDS:
        if family_urls[field_name]:
            return family_urls[field_name]
    return ""


def _check_resolved(issues, category, slug, product, variant, urls, variant_id):
    """Controleer het resolverresultaat voor één bron (rel, label,
    variantveiligheid)."""
    link = resolve_product_link(product, variant)
    source_has_url = any(urls.values())

    if link.url and not source_has_url:
        # Toegestaan is uitsluitend de gedocumenteerde familie-fallback
        # naar de oorspronkelijke productniveau-URL's; elke andere URL
        # (bijv. van een andere variant) is een verboden fallback.
        expected = _expected_fallback_url(_family_link_urls(product))
        if link.url != expected:
            issues.append(AuditIssue(
                code="variant_link_fallback_to_other_variant",
                severity=SEVERITY_ERROR,
                message=(
                    "Resolver leverde een URL die niet van de geselecteerde "
                    "variant en niet van de familie-fallback "
                    "(productniveau) afkomstig is — verboden fallback."
                ),
                category=category,
                product_slug=slug,
                variant_id=variant_id,
                expected=expected,
                actual=link.url,
            ))

    if link.url:
        if link.link_type in ("retailer", "official") and "sponsored" in link.rel:
            issues.append(AuditIssue(
                code=f"{link.link_type}_url_with_sponsored_rel",
                severity=SEVERITY_ERROR,
                message=(
                    f"{link.link_type}-link krijgt rel met 'sponsored'; "
                    "alleen affiliatelinks mogen sponsored zijn."
                ),
                category=category,
                product_slug=slug,
                variant_id=variant_id,
                actual=link.rel,
            ))
        if link.link_type == LINK_TYPE_OFFICIAL and "prijs" in link.label.lower():
            issues.append(AuditIssue(
                code="official_url_using_price_button_label",
                severity=SEVERITY_ERROR,
                message=(
                    "official_url gebruikt een prijs-knoplabel; een "
                    "fabrikantpagina mag niet als kooplink worden "
                    "gepresenteerd."
                ),
                category=category,
                product_slug=slug,
                variant_id=variant_id,
                actual=link.label,
            ))
    else:
        label = urls_source_availability(variant if variant is not None else product)
        if not label and variant is not None:
            family = product.get("_family_links") or {}
            label = urls_source_availability(family)
        if not label:
            issues.append(AuditIssue(
                code="missing_link_with_empty_button",
                severity=SEVERITY_INFO,
                message=(
                    "Geen enkele URL en geen availability_label; er wordt "
                    "geen knop getoond. Overweeg een availability_label."
                ),
                category=category,
                product_slug=slug,
                variant_id=variant_id,
            ))


def urls_source_availability(source):
    label = source.get("availability_label")
    return label.strip() if isinstance(label, str) else ""


def _check_variant_projection(issues, category, slug, raw_product):
    """Controleer per variant dat de displayprojectie (set_display_variant)
    exact de eigen URL's van die variant oplevert — geen stale link van een
    eerder geselecteerde variant."""
    product = copy.deepcopy(raw_product)
    try:
        prepare_product_variants(product)
    except ValueError:
        # Structuurfouten worden al door de variantenaudit gerapporteerd.
        return
    variants = product.get("shape_variants") or []
    if not variants:
        return
    for pv in variants:
        set_display_variant(product, pv)
        for field_name in _URL_FIELDS:
            expected = normalize_optional_url(pv.get(field_name))
            actual = normalize_optional_url(product.get(field_name))
            if actual != expected:
                issues.append(AuditIssue(
                    code="stale_variant_link",
                    severity=SEVERITY_ERROR,
                    message=(
                        f"Na variantwissel wijkt {field_name} op "
                        "productniveau af van de geselecteerde variant "
                        "(stale of verkeerde link)."
                    ),
                    category=category,
                    product_slug=slug,
                    variant_id=pv.get("id"),
                    field=field_name,
                    expected=expected,
                    actual=actual,
                ))
        resolved = product.get("resolved_link")
        own = resolve_product_link({"shape_variants": [pv]}, pv)
        expected_url = own.url or _expected_fallback_url(
            _family_link_urls(product)
        )
        if resolved and resolved.url != expected_url:
            issues.append(AuditIssue(
                code="variant_link_fallback_to_other_variant",
                severity=SEVERITY_ERROR,
                message=(
                    "resolved_link na variantwissel is niet de eigen link "
                    "van de geselecteerde variant en ook niet de "
                    "familie-fallback (productniveau)."
                ),
                category=category,
                product_slug=slug,
                variant_id=pv.get("id"),
                expected=expected_url,
                actual=resolved.url,
            ))


def run_product_link_check(category=None, params=None):
    """Auditrunner voor het linkonderscheid affiliate/retailer/official."""
    categories = [category] if category else sorted(CATEGORY_SOURCES)
    for cat in categories:
        if cat not in CATEGORY_SOURCES:
            raise ValueError(f"Onbekende categorie: {cat!r}")

    issues = []
    products_checked = 0
    variants_checked = 0
    for cat in categories:
        for raw in _load_products(cat):
            slug = raw.get("slug") or raw.get("name") or "?"
            products_checked += 1
            product = copy.deepcopy(raw)
            try:
                prepare_product_variants(product)
            except ValueError:
                product = copy.deepcopy(raw)

            shape_variants = product.get("shape_variants") or []
            if shape_variants:
                for pv in shape_variants:
                    variants_checked += 1
                    urls = _check_source(
                        issues, cat, slug, pv, variant_id=pv.get("id")
                    )
                    _check_resolved(
                        issues, cat, slug, product, pv, urls, pv.get("id")
                    )
                _check_variant_projection(issues, cat, slug, raw)
            else:
                urls = _check_source(issues, cat, slug, product)
                _check_resolved(issues, cat, slug, product, None, urls, None)
                # Kleurswatch-varianten (zonder id): statische checks plus
                # controle van de per-swatch resolved link (eigen
                # prioriteit, daarna familie-fallback — nooit een andere
                # swatch).
                apply_resolved_link(product)
                resolve_swatch_variant_links(product)
                family_urls = {
                    f: normalize_optional_url(product.get(f))
                    for f in _URL_FIELDS
                }
                for sv in product.get("variants") or []:
                    if isinstance(sv, dict) and not sv.get("id"):
                        variants_checked += 1
                        sv_id = sv.get("name") or "kleurvariant"
                        sv_urls = _check_source(
                            issues, cat, slug, sv, variant_id=sv_id
                        )
                        link = sv.get("resolved_link")
                        if link is None:
                            continue
                        # Verwacht resultaat voor ELKE swatch: eerst de
                        # eigen prioriteit, anders de familie-fallback.
                        expected = _expected_fallback_url(sv_urls) or \
                            _expected_fallback_url(family_urls)
                        if link.url != expected:
                            issues.append(AuditIssue(
                                code="variant_link_fallback_to_other_variant",
                                severity=SEVERITY_ERROR,
                                message=(
                                    "Swatch-resolved link is niet de eigen "
                                    "link van de swatch en ook niet de "
                                    "familie-fallback (productniveau)."
                                ),
                                category=cat,
                                product_slug=slug,
                                variant_id=sv_id,
                                expected=expected,
                                actual=link.url,
                            ))
                        if link.url and link.link_type in (
                            "retailer", "official"
                        ) and "sponsored" in link.rel:
                            issues.append(AuditIssue(
                                code=f"{link.link_type}_url_with_sponsored_rel",
                                severity=SEVERITY_ERROR,
                                message=(
                                    f"Swatch-{link.link_type}-link krijgt rel "
                                    "met 'sponsored'; alleen affiliatelinks "
                                    "mogen sponsored zijn."
                                ),
                                category=cat,
                                product_slug=slug,
                                variant_id=sv_id,
                                actual=link.rel,
                            ))

    metadata = {
        "categories": categories,
        "products_checked": products_checked,
        "variants_checked": variants_checked,
        "manual_review_affiliate_urls": sum(
            1 for i in issues
            if i.code == "affiliate_url_without_affiliate_confirmation"
        ),
    }
    return issues, metadata
