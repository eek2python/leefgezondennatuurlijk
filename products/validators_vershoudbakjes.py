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


def _static_exists(image_path, image):
    if not image:
        return False
    rel = os.path.join("static", image_path or "", image)
    return os.path.exists(os.path.join(settings.BASE_DIR, rel))


def validate_vershoudbakjes(products, rankings):
    """Valideer de catalogus. Retourneert een lijst waarschuwingen;
    raiset ValueError bij structurele fouten."""
    warnings = []
    errors = []

    seen_texts = {"description": {}, "verdict": {}, "pros": {}}

    for key, product in products.items():
        where = f"vershoudbakjes '{key}'"
        slug = product.get("slug") or ""

        # key/slug-consistentie (key gebruikt underscores, slug hyphens)
        if slug and slug.replace("-", "_").replace("+", "+") != key.replace("+", "+") and \
                slug.replace("-", "_") != key:
            warnings.append(f"{where}: slug '{slug}' wijkt af van product key")

        material = product.get("material")
        if material and material not in ALLOWED_MATERIALS:
            warnings.append(f"{where}: afwijkende materiaal-schrijfwijze '{material}'")

        award = product.get("award")
        if award not in (None,) and award not in ALLOWED_AWARDS:
            errors.append(f"{where}: ongeldig award '{award}'")

        price = product.get("price")
        if price is not None and not isinstance(price, numbers.Number):
            warnings.append(f"{where}: prijs is niet numeriek ({price!r})")

        capacities = product.get("capacities") or []
        for c in capacities:
            if not isinstance(c, numbers.Number) or c <= 0:
                warnings.append(f"{where}: ongeldige capaciteit {c!r}")

        # aantal bakjes vs. capaciteiten wanneer '<n>-delig' in key/naam staat
        m = _SET_COUNT.search(key) or _SET_COUNT.search(product.get("name", ""))
        if m and capacities and not product.get("variants"):
            expected = int(m.group(1))
            if len(capacities) != expected:
                warnings.append(
                    f"{where}: {len(capacities)} capaciteiten maar naam zegt {expected}-delig"
                )

        # usage-schema (structureel)
        errors.extend(validate_usage(product.get("usage"), where))

        variants = product.get("variants") or []
        if variants:
            ids = [v.get("id") for v in variants if v.get("id")]
            if ids:
                if len(ids) != len(set(ids)):
                    errors.append(f"{where}: dubbele variant-ids {ids}")
                defaults = [v for v in variants if v.get("is_default")]
                if len(defaults) != 1:
                    errors.append(f"{where}: {len(defaults)} defaultvarianten (verwacht 1)")
                combos = [tuple(sorted((v.get("options") or {}).items())) for v in variants]
                real = [c for c in combos if c]
                if len(real) != len(set(real)):
                    errors.append(f"{where}: dubbele optiecombinaties")
            for v in variants:
                vw = f"{where} variant '{v.get('id') or v.get('label')}'"
                errors.extend(validate_usage(v.get("usage"), vw))
                shape = v.get("shape") or (v.get("options") or {}).get("shape") or ""
                if isinstance(shape, str) and _CAPACITY_IN_SHAPE.search(shape):
                    warnings.append(f"{vw}: inhoudsmaat '{shape}' in shape-veld")
                labels = list((v.get("option_labels") or {}).values())
                if v.get("label"):
                    labels.append(v["label"])
                for label in labels:
                    if isinstance(label, str) and _DECIMAL_POINT_LITER.search(label):
                        warnings.append(f"{vw}: literlabel '{label}' met punt i.p.v. komma")
                img = v.get("image")
                if img and not _static_exists(v.get("image_path") or product.get("image_path"), img):
                    warnings.append(f"{vw}: afbeelding '{img}' niet gevonden")
        else:
            if not _static_exists(product.get("image_path"), product.get("image")):
                warnings.append(f"{where}: afbeelding '{product.get('image')}' niet gevonden")

        # placeholders in zichtbare tekst
        for field in _TEXT_FIELDS:
            value = product.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                warnings.append(f"{where}: leeg veld '{field}'")
            elif isinstance(value, str) and _PLACEHOLDER.search(value):
                warnings.append(f"{where}: placeholder-tekst in '{field}'")

        brand = (product.get("brand") or "").lower()
        name = (product.get("name") or "").lower()
        if brand and brand not in name:
            warnings.append(f"{where}: merk '{product.get('brand')}' ontbreekt in productnaam")

        # identieke redactionele teksten tussen merken
        for field in ("description", "verdict"):
            value = product.get(field)
            if isinstance(value, str) and value.strip():
                prev = seen_texts[field].get(value)
                if prev and products[prev].get("brand") != product.get("brand"):
                    warnings.append(
                        f"{where}: identieke {field} als '{prev}' (ander merk)"
                    )
                seen_texts[field].setdefault(value, key)
        pros_key = tuple(product.get("pros") or [])
        if pros_key:
            prev = seen_texts["pros"].get(pros_key)
            if prev and products[prev].get("brand") != product.get("brand"):
                warnings.append(f"{where}: identieke pluspunten als '{prev}' (ander merk)")
            seen_texts["pros"].setdefault(pros_key, key)

        pros = product.get("pros") or []
        cons = product.get("cons") or []
        if len(pros) > 3:
            warnings.append(f"{where}: meer dan 3 pluspunten ({len(pros)})")
        if len(cons) > 2:
            warnings.append(f"{where}: meer dan 2 minpunten ({len(cons)})")

    # ranking: iedere key bestaat en komt maximaal één keer voor
    seen_ranked = set()
    for type_key, keys in rankings.items():
        for k in keys:
            if k not in products:
                errors.append(f"ranking '{type_key}': onbekende product key '{k}'")
            if k in seen_ranked:
                errors.append(f"ranking: product '{k}' komt meerdere keren voor")
            seen_ranked.add(k)

    if errors:
        raise ValueError("Vershoudbakjes-validatie mislukt:\n" + "\n".join(errors))
    for w in warnings:
        logger.warning("Vershoudbakjes-audit: %s", w)
    return warnings
