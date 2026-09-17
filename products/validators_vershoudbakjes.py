"""Datavalidator voor de vershoudbakjes-catalogus (rapporterend).

Structurele fouten (dubbele variant-ids, dubbele optiecombinaties, geen of
meerdere defaultvarianten, ongeldig usage-schema) leiden tot een ValueError
bij het opstarten. Redactionele of onzekere kwesties worden alleen als
waarschuwing gelogd; de validator wijzigt nooit zelf productfeiten.
"""

import logging
import numbers
import os
import re
from dataclasses import dataclass

from django.conf import settings

from utils.usage_helpers import validate_usage

logger = logging.getLogger(__name__)

ALLOWED_AWARDS = {"🏆 Beste keuze", "💰 Budget keuze", "💎 Premium keuze"}
ALLOWED_MATERIALS = {"Borosilicaatglas", "Gehard glas", "Glas"}

_DECIMAL_POINT_LITER = re.compile(r"\d+\.\d+\s*L\b")
_CAPACITY_IN_SHAPE = re.compile(r"\d+\s*(ml|l)\b", re.IGNORECASE)
_PLACEHOLDER = re.compile(r"\bTODO\b|\bNone\b|\bplaceholder\b", re.IGNORECASE)
_SET_COUNT = re.compile(r"(\d+)-delig")

_TEXT_FIELDS = ("name", "description", "verdict")


@dataclass(frozen=True)
class VershoudbakjesValidationIssue:
    code: str
    severity: str
    message: str
    product_key: str | None = None
    variant_id: str | None = None
    field: str | None = None


def _issue(code, severity, message, product_key=None, variant_id=None, field=None):
    return VershoudbakjesValidationIssue(
        code=code,
        severity=severity,
        message=message,
        product_key=product_key,
        variant_id=variant_id,
        field=field,
    )


def _normalise_identifier(value):
    """Maak product keys en URL-veilige slugs vergelijkbaar."""
    return value.replace("-", "_").replace("+", "_plus")


def _static_exists(image_path, image):
    if not image:
        return False
    rel = os.path.join("static", image_path or "", image)
    return os.path.exists(os.path.join(settings.BASE_DIR, rel))


def collect_vershoudbakjes_issues(products, rankings):
    """Retourneer alle structurele en redactionele problemen gestructureerd."""
    issues = []

    seen_texts = {"description": {}, "verdict": {}, "pros": {}}

    for key, product in products.items():
        where = f"vershoudbakjes '{key}'"
        slug = product.get("slug") or ""

        # key/slug-consistentie (key gebruikt underscores, slug hyphens)
        if slug and _normalise_identifier(slug) != _normalise_identifier(key):
            issues.append(_issue(
                "slug_mismatch", "warning",
                f"{where}: slug '{slug}' wijkt af van product key",
                key, field="slug",
            ))

        material = product.get("material")
        if material and material not in ALLOWED_MATERIALS:
            issues.append(_issue(
                "invalid_material_spelling", "warning",
                f"{where}: afwijkende materiaal-schrijfwijze '{material}'",
                key, field="material",
            ))

        award = product.get("award")
        if award not in (None,) and award not in ALLOWED_AWARDS:
            issues.append(_issue(
                "invalid_award", "error", f"{where}: ongeldig award '{award}'",
                key, field="award",
            ))

        price = product.get("price")
        if price is not None and not isinstance(price, numbers.Number):
            issues.append(_issue(
                "invalid_price", "warning",
                f"{where}: prijs is niet numeriek ({price!r})",
                key, field="price",
            ))

        capacities = product.get("capacities") or []
        for c in capacities:
            if not isinstance(c, numbers.Number) or c <= 0:
                issues.append(_issue(
                    "invalid_capacity", "warning",
                    f"{where}: ongeldige capaciteit {c!r}",
                    key, field="capacities",
                ))

        # aantal bakjes vs. capaciteiten wanneer '<n>-delig' in key/naam staat
        m = _SET_COUNT.search(key) or _SET_COUNT.search(product.get("name", ""))
        if m and capacities and not product.get("variants"):
            expected = int(m.group(1))
            if len(capacities) != expected:
                issues.append(_issue(
                    "capacity_count_mismatch", "warning",
                    f"{where}: {len(capacities)} capaciteiten maar naam zegt {expected}-delig",
                    key, field="capacities",
                ))

        # usage-schema (structureel)
        for message in validate_usage(product.get("usage"), where):
            issues.append(_issue(
                "invalid_usage", "error", message, key, field="usage"
            ))

        variants = product.get("variants") or []
        if variants:
            ids = [v.get("id") for v in variants if v.get("id")]
            if ids:
                if len(ids) != len(set(ids)):
                    issues.append(_issue(
                        "duplicate_variant_id", "error",
                        f"{where}: dubbele variant-ids {ids}", key,
                    ))
                defaults = [v for v in variants if v.get("is_default")]
                if len(defaults) != 1:
                    issues.append(_issue(
                        "invalid_default_variant_count", "error",
                        f"{where}: {len(defaults)} defaultvarianten (verwacht 1)", key,
                    ))
                combos = [tuple(sorted((v.get("options") or {}).items())) for v in variants]
                real = [c for c in combos if c]
                if len(real) != len(set(real)):
                    issues.append(_issue(
                        "duplicate_variant_options", "error",
                        f"{where}: dubbele optiecombinaties", key,
                    ))
            for v in variants:
                variant_id = v.get("id") or v.get("label")
                vw = f"{where} variant '{variant_id}'"
                for message in validate_usage(v.get("usage"), vw):
                    issues.append(_issue(
                        "invalid_usage", "error", message, key, variant_id, "usage"
                    ))
                shape = v.get("shape") or (v.get("options") or {}).get("shape") or ""
                if isinstance(shape, str) and _CAPACITY_IN_SHAPE.search(shape):
                    issues.append(_issue(
                        "capacity_in_shape", "warning",
                        f"{vw}: inhoudsmaat '{shape}' in shape-veld",
                        key, variant_id, "shape",
                    ))
                labels = list((v.get("option_labels") or {}).values())
                if v.get("label"):
                    labels.append(v["label"])
                for label in labels:
                    if isinstance(label, str) and _DECIMAL_POINT_LITER.search(label):
                        issues.append(_issue(
                            "decimal_point_liter_label", "warning",
                            f"{vw}: literlabel '{label}' met punt i.p.v. komma",
                            key, variant_id, "label",
                        ))
                img = v.get("image")
                if img and not _static_exists(v.get("image_path") or product.get("image_path"), img):
                    issues.append(_issue(
                        "missing_image", "warning",
                        f"{vw}: afbeelding '{img}' niet gevonden",
                        key, variant_id, "image",
                    ))
        else:
            if not _static_exists(product.get("image_path"), product.get("image")):
                issues.append(_issue(
                    "missing_image", "warning",
                    f"{where}: afbeelding '{product.get('image')}' niet gevonden",
                    key, field="image",
                ))

        # placeholders in zichtbare tekst
        for field in _TEXT_FIELDS:
            value = product.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(_issue(
                    "empty_text_field", "warning",
                    f"{where}: leeg veld '{field}'", key, field=field,
                ))
            elif isinstance(value, str) and _PLACEHOLDER.search(value):
                issues.append(_issue(
                    "placeholder_text", "warning",
                    f"{where}: placeholder-tekst in '{field}'", key, field=field,
                ))

        brand = (product.get("brand") or "").lower()
        name = (product.get("name") or "").lower()
        if brand and brand not in name:
            issues.append(_issue(
                "brand_missing_from_name", "warning",
                f"{where}: merk '{product.get('brand')}' ontbreekt in productnaam",
                key, field="name",
            ))

        # identieke redactionele teksten tussen merken
        for field in ("description", "verdict"):
            value = product.get(field)
            if isinstance(value, str) and value.strip():
                prev = seen_texts[field].get(value)
                if prev and products[prev].get("brand") != product.get("brand"):
                    issues.append(_issue(
                        f"duplicate_{field}", "warning",
                        f"{where}: identieke {field} als '{prev}' (ander merk)",
                        key, field=field,
                    ))
                seen_texts[field].setdefault(value, key)
        pros_key = tuple(product.get("pros") or [])
        if pros_key:
            prev = seen_texts["pros"].get(pros_key)
            if prev and products[prev].get("brand") != product.get("brand"):
                issues.append(_issue(
                    "duplicate_pros", "warning",
                    f"{where}: identieke pluspunten als '{prev}' (ander merk)",
                    key, field="pros",
                ))
            seen_texts["pros"].setdefault(pros_key, key)

        pros = product.get("pros") or []
        cons = product.get("cons") or []
        if len(pros) > 3:
            issues.append(_issue(
                "too_many_pros", "warning",
                f"{where}: meer dan 3 pluspunten ({len(pros)})",
                key, field="pros",
            ))
        if len(cons) > 2:
            issues.append(_issue(
                "too_many_cons", "warning",
                f"{where}: meer dan 2 minpunten ({len(cons)})",
                key, field="cons",
            ))

    # ranking: iedere key bestaat en komt maximaal één keer voor
    seen_ranked = set()
    for type_key, keys in rankings.items():
        for k in keys:
            if k not in products:
                issues.append(_issue(
                    "unknown_ranking_product", "error",
                    f"ranking '{type_key}': onbekende product key '{k}'",
                    k,
                ))
            if k in seen_ranked:
                issues.append(_issue(
                    "duplicate_ranking_product", "error",
                    f"ranking: product '{k}' komt meerdere keren voor",
                    k,
                ))
            seen_ranked.add(k)

    return issues


def validate_vershoudbakjes(products, rankings):
    """Valideer de catalogus. Retourneert een lijst waarschuwingen;
    raiset ValueError bij structurele fouten."""
    issues = collect_vershoudbakjes_issues(products, rankings)
    errors = [issue.message for issue in issues if issue.severity == "error"]
    if errors:
        raise ValueError("Vershoudbakjes-validatie mislukt:\n" + "\n".join(errors))
    warnings = [issue.message for issue in issues if issue.severity == "warning"]
    for w in warnings:
        logger.warning("Vershoudbakjes-audit: %s", w)
    return warnings
