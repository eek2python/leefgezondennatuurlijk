"""
Replacement candidate selection logic.

Suggests replacement candidates when a product becomes invalid or unavailable.
NEVER auto-approves or auto-publishes replacements.
NEVER writes into rankings files.
If no safe replacement is found, outputs manual_review_required.
"""

from services.product_validation import validate_product, _infer_price_segment


def _score_candidate(
    original: dict,
    candidate: dict,
    rules: dict,
    ranked_products: list[dict],
) -> tuple[float, list[str], list[str]]:
    """
    Score a candidate replacement against the original product.

    Returns (score, reasons, flags).
    Score 0.0–7.0; higher is better.
    reasons: why this candidate was chosen.
    flags: partial matches or concerns.
    """
    score = 0.0
    reasons = []
    flags = []

    validation = validate_product(candidate, rules)
    if not validation["valid"] or validation.get("errors"):
        return -1.0, [], [f"Kandidaat is ongeldig voor deze categorie: {validation['errors']}"]

    score += 1.0
    reasons.append("Categorie: geldig voor de categorie-regels.")

    original_material = str(original.get("material", "")).lower()
    candidate_material = str(candidate.get("material", "")).lower()

    field_aliases = rules.get("field_aliases", {})

    def get_field(p, field):
        actual = field_aliases.get(field, field)
        return p.get(actual)

    if original_material and candidate_material:
        allowed_kw = rules.get("allowed_material_keywords", [])
        orig_match = any(kw.lower() in original_material for kw in allowed_kw) if allowed_kw else True
        cand_match = any(kw.lower() in candidate_material for kw in allowed_kw) if allowed_kw else True
        if orig_match and cand_match:
            score += 1.0
            reasons.append("Materiaal: vergelijkbaar keramisch/RVS/hout materiaaltype.")
        else:
            flags.append("Materiaaltype komt niet volledig overeen.")
    else:
        flags.append("Materiaalveld ontbreekt bij origineel of kandidaat — handmatige beoordeling vereist.")

    size_sensitive = rules.get("size_sensitive", False)
    size_field = rules.get("size_field", "diameter")
    if size_sensitive:
        orig_size = get_field(original, size_field)
        cand_size = get_field(candidate, size_field)
        if orig_size is not None and cand_size is not None:
            try:
                if abs(float(orig_size) - float(cand_size)) < 2:
                    score += 1.0
                    reasons.append(f"Formaat: vergelijkbaar ({cand_size} cm).")
                else:
                    flags.append(f"Formaatverschil: origineel {orig_size} cm, kandidaat {cand_size} cm.")
            except (TypeError, ValueError):
                flags.append("Formaatvergelijking mislukt — controleer manueel.")
        else:
            flags.append("Formaatveld ontbreekt — formaatvergelijking niet mogelijk.")

    orig_segment = _infer_price_segment(original, rules)
    cand_segment = _infer_price_segment(candidate, rules)
    if orig_segment and cand_segment:
        if orig_segment == cand_segment:
            score += 1.0
            reasons.append(f"Prijssegment: zelfde segment ({cand_segment}).")
        else:
            flags.append(f"Prijssegment verschilt: origineel '{orig_segment}', kandidaat '{cand_segment}'.")
    else:
        flags.append("Prijssegment kon niet worden bepaald — handmatige beoordeling aanbevolen.")

    orig_rating = original.get("rating", 0) or 0
    cand_rating = candidate.get("rating", 0) or 0
    orig_count = original.get("rating_count", 0) or 0
    cand_count = candidate.get("rating_count", 0) or 0

    if cand_rating >= orig_rating:
        score += 1.0
        reasons.append(f"Beoordelingsscore: {cand_rating} (origineel: {orig_rating}).")
    elif cand_rating >= orig_rating - 0.5:
        score += 0.5
        flags.append(f"Beoordelingsscore iets lager: {cand_rating} vs {orig_rating}.")
    else:
        flags.append(f"Lagere beoordelingsscore: {cand_rating} vs {orig_rating}.")

    if cand_count >= 50:
        score += 0.5
        reasons.append(f"Voldoende reviews: {cand_count}.")
    else:
        flags.append(f"Weinig reviews ({cand_count}) — betrouwbaarheid onzeker.")

    avail = str(candidate.get("availability", "")).lower()
    if "instock" in avail or "available" in avail:
        score += 1.0
        reasons.append("Beschikbaarheid: in voorraad.")
    else:
        flags.append(f"Beschikbaarheid onduidelijk: '{candidate.get('availability', 'onbekend')}'.")

    ranked_brands = [str(p.get("brand", "")).lower() for p in ranked_products]
    cand_brand = str(candidate.get("brand", "")).lower()
    orig_brand = str(original.get("brand", "")).lower()
    brand_occurrences = ranked_brands.count(cand_brand)

    max_per_brand = 2
    if cand_brand == orig_brand:
        reasons.append(f"Merkdiversiteit: zelfde merk als vervangen product ({cand_brand}) — acceptabel.")
        score += 0.5
    elif brand_occurrences < max_per_brand:
        score += 0.5
        reasons.append(f"Merkdiversiteit: merk '{cand_brand}' heeft {brand_occurrences} product(en) in de lijst.")
    else:
        flags.append(
            f"Merkdiversiteitswaarschuwing: '{cand_brand}' heeft al {brand_occurrences} producten "
            f"in de lijst (max {max_per_brand})."
        )

    return score, reasons, flags


def suggest_replacement_candidates(
    product: dict,
    category_rules: dict,
    candidate_pool: list[dict],
    ranked_products: list[dict] | None = None,
    top_n: int = 3,
) -> dict:
    """
    Suggest replacement candidates for a product that needs to be replaced.

    Parameters
    ----------
    product : dict
        The product that needs replacement.
    category_rules : dict
        The category rules dict.
    candidate_pool : list[dict]
        All possible replacement candidates to evaluate.
    ranked_products : list[dict]
        The currently ranked products (for brand diversity checking).
    top_n : int
        Maximum number of candidates to return.

    Returns
    -------
    dict with:
      - product_name
      - category_key
      - candidates: list of scored candidates
      - manual_review_required: bool
      - notes: str

    IMPORTANT: This function NEVER writes to rankings files.
    IMPORTANT: Any returned candidate requires manual editorial review before use.
    """
    if ranked_products is None:
        ranked_products = []

    scored = []
    for candidate in candidate_pool:
        slug = candidate.get("slug", "")
        orig_slug = product.get("slug", "")
        if slug == orig_slug:
            continue

        score, reasons, flags = _score_candidate(product, candidate, category_rules, ranked_products)

        if score < 0:
            continue

        partial_match = len(flags) > 0
        scored.append({
            "candidate_name": candidate.get("name", ""),
            "slug": slug,
            "brand": candidate.get("brand", ""),
            "score": round(score, 2),
            "reasons": reasons,
            "flags": flags,
            "partial_match": partial_match,
            "inferred_price_segment": _infer_price_segment(candidate, category_rules),
            "requires_manual_review": partial_match or score < 4.0,
            "warning": "Dit is een kandidaatsuggestie. NOOIT automatisch publiceren. Altijd handmatig beoordelen.",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = scored[:top_n]

    manual_review = len(top_candidates) == 0 or all(c["requires_manual_review"] for c in top_candidates)

    notes = (
        "Alle suggesties vereisen handmatige redactionele beoordeling. "
        "Dit systeem publiceert nooit automatisch wijzigingen in productrankings."
    )
    if not top_candidates:
        notes = (
            "Geen geschikte vervangingskandidaten gevonden. "
            "Handmatige beoordeling en selectie vereist. "
            "Verwijder het product niet automatisch uit de ranking."
        )

    return {
        "product_name": product.get("name", ""),
        "slug": product.get("slug", ""),
        "category_key": category_rules.get("category_key", "unknown"),
        "candidates": top_candidates,
        "manual_review_required": manual_review,
        "notes": notes,
    }
