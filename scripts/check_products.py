#!/usr/bin/env python3
"""
Weekly product validation and monitoring script.

Usage:
    python scripts/check_products.py

Output:
    reports/product_check_report.json
    reports/product_check_report.md

SAFETY GUARDRAILS:
  - This script NEVER modifies live product data.
  - This script NEVER modifies live rankings.
  - This script NEVER auto-publishes any changes.
  - All flagged cases require manual editorial review.
"""

import sys
import json
import datetime
import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import rules.base_rules as base_rules_mod
import rules.houten_snijplanken as r_snijplanken
import rules.keramische_koekenpannen as r_keramisch
import rules.rvs_koekenpannen as r_rvs
import rules.pfas_vrije_hapjespannen as r_hapjes
import rules.pfas_vrije_wokpannen as r_wok
import rules.pfas_vrije_airfryers as r_airfryers
import rules.glazen_vershoudbakjes as r_vershoudbakjes

from services.product_validation import (
    validate_category_products,
    check_brand_diversity,
    check_brand_diversity_scoped,
    classify_price_segment,
)
from services.product_monitoring import monitor_category
from services.replacement_candidates import suggest_replacement_candidates

GLOBAL_RULES = base_rules_mod.GLOBAL_RULES


# ---------------------------------------------------------------------------
# Category data source mapping
# ---------------------------------------------------------------------------

CATEGORY_CONFIG = {
    "keramische_koekenpannen": {
        "rules": r_keramisch.RULES,
        "products_module": "products.products_koekenpannen",
        "rankings_module": "products.rankings_koekenpannen",
        "url_path": "/koekenpannen/",
        "rankings_type": "dict_by_size",
    },
    "rvs_koekenpannen": {
        "rules": r_rvs.RULES,
        "products_module": "products.products_rvs_koekenpannen",
        "rankings_module": "products.rankings_rvs_koekenpannen",
        "url_path": "/rvs-koekenpannen/",
        "rankings_type": "list",
    },
    "houten_snijplanken": {
        "rules": r_snijplanken.RULES,
        "products_module": "products.products_snijplanken",
        "rankings_module": "products.rankings_snijplanken",
        "url_path": "/snijplanken/",
        "rankings_type": "list",
    },
    "pfas_vrije_hapjespannen": {
        "rules": r_hapjes.RULES,
        "products_module": "products.products_hapjespannen",
        "rankings_module": "products.rankings_hapjespannen",
        "url_path": "/hapjespannen/",
        "rankings_type": "dict_by_size",
    },
    "pfas_vrije_wokpannen": {
        "rules": r_wok.RULES,
        "products_module": "products.products_wokpannen",
        "rankings_module": "products.rankings_wokpannen",
        "url_path": "/wokpannen/",
        "rankings_type": "dict_by_size",
    },
    "pfas_vrije_airfryers": {
        "rules": r_airfryers.RULES,
        "products_module": "products.products_airfryers",
        "rankings_module": "products.rankings_airfryers",
        "url_path": "/airfryers/",
        "rankings_type": "list",
    },
    "glazen_vershoudbakjes": {
        "rules": r_vershoudbakjes.RULES,
        "products_module": "products.products_vershoudcontainers",
        "rankings_module": "products.rankings_vershoudcontainers",
        "url_path": "/vershoudcontainers/",
        "rankings_type": "list",
    },
}


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _load_module_attr(module_path: str, attr: str):
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    except Exception as e:
        print(f"  [WARN] Could not load {module_path}.{attr}: {e}")
        return None


def _flatten_rankings(rankings, rankings_type: str) -> list[str]:
    if rankings is None:
        return []
    if rankings_type == "dict_by_size":
        keys = []
        for size_keys in rankings.values():
            keys.extend(size_keys)
        return keys
    return list(rankings)


def load_category_products(config: dict) -> tuple[list[dict], list[dict]]:
    """
    Returns (ranked_products, all_products_in_module).
    ranked_products: only the products currently in the ranking.
    all_products_in_module: everything in the PRODUCTS dict (candidate pool).
    """
    products_dict = _load_module_attr(config["products_module"], "PRODUCTS")
    rankings = _load_module_attr(config["rankings_module"], "RANKINGS")

    if products_dict is None:
        return [], []

    ranked_keys = _flatten_rankings(rankings, config["rankings_type"])
    seen = set()
    unique_keys = []
    for k in ranked_keys:
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)

    ranked_products = []
    for key in unique_keys:
        p = products_dict.get(key)
        if p is not None:
            ranked_products.append(p)
        else:
            print(f"  [WARN] Ranking key '{key}' not found in PRODUCTS dict.")

    all_products = list(products_dict.values())
    return ranked_products, all_products


# ---------------------------------------------------------------------------
# Report building
# ---------------------------------------------------------------------------

def run_category_check(category_key: str, config: dict) -> dict:
    rules = config["rules"]
    print(f"\n[{category_key}] Loading products...")
    ranked_products, all_products = load_category_products(config)

    if not ranked_products:
        return {
            "category_key": category_key,
            "error": "Geen producten gevonden. Controleer de datamodule.",
            "valid_products": [],
            "flagged_products": [],
            "missing_metadata": [],
            "rule_violations": [],
            "brand_diversity_violations": [],
            "broken_urls": [],
            "replacement_needed": [],
            "replacement_suggestions": [],
            "manual_review_cases": [],
            "monitor_results": [],
            "total_ranked": 0,
        }

    print(f"  {len(ranked_products)} ranked products, {len(all_products)} total in module.")

    validation_results = validate_category_products(ranked_products, rules)
    monitor_results = monitor_category(ranked_products, rules)

    rankings_type = config.get("rankings_type", "list")
    rankings_raw = _load_module_attr(config["rankings_module"], "RANKINGS")
    products_dict_full = _load_module_attr(config["products_module"], "PRODUCTS") or {}

    if rankings_type == "dict_by_size" and isinstance(rankings_raw, dict):
        products_by_size = {
            str(size_key): [
                products_dict_full[k] for k in size_keys if k in products_dict_full
            ]
            for size_key, size_keys in rankings_raw.items()
        }
        brand_check = check_brand_diversity_scoped(products_by_size, max_per_brand=GLOBAL_RULES["max_products_per_brand"])
    else:
        brand_check = check_brand_diversity(ranked_products, GLOBAL_RULES["max_products_per_brand"])

    valid_products = []
    flagged_products = []
    missing_metadata = []
    rule_violations = []
    broken_urls = []
    replacement_needed = []
    replacement_suggestions = []
    manual_review_cases = []

    for vr in validation_results:
        if vr["valid"] and not vr["warnings"] and not vr["rule_flags"]:
            valid_products.append(vr)
        else:
            flagged_products.append(vr)

        if vr["missing_fields"]:
            missing_metadata.append({
                "product": vr["product_name"],
                "missing_fields": vr["missing_fields"],
            })

        if vr["errors"]:
            rule_violations.append({
                "product": vr["product_name"],
                "errors": vr["errors"],
            })

        if vr["manual_review_required"]:
            manual_review_cases.append({
                "product": vr["product_name"],
                "reason": vr["errors"] + vr["warnings"] + vr["rule_flags"],
            })

    for mr in monitor_results:
        url = mr.get("product_url", "")
        if not url or not str(url).startswith("http"):
            broken_urls.append({
                "product": mr["product_name"],
                "url": url,
                "issue": "URL ontbreekt of is ongeldig.",
            })
        elif "TODO" in str(url) or "placeholder" in str(url).lower():
            broken_urls.append({
                "product": mr["product_name"],
                "url": url,
                "issue": "URL lijkt een placeholder te zijn.",
            })

        if mr.get("replacement_needed"):
            original = next(
                (p for p in ranked_products if p.get("name") == mr["product_name"]),
                None,
            )
            if original:
                suggestions = suggest_replacement_candidates(
                    original,
                    rules,
                    all_products,
                    ranked_products,
                    top_n=3,
                )
                replacement_needed.append(mr["product_name"])
                replacement_suggestions.append(suggestions)

    brand_violations_list = []
    if brand_check["has_violations"]:
        for brand, info in brand_check["violations"].items():
            brand_violations_list.append(info)

    return {
        "category_key": category_key,
        "url_path": config["url_path"],
        "total_ranked": len(ranked_products),
        "valid_products": valid_products,
        "flagged_products": flagged_products,
        "missing_metadata": missing_metadata,
        "rule_violations": rule_violations,
        "brand_diversity_violations": brand_violations_list,
        "broken_urls": broken_urls,
        "replacement_needed": replacement_needed,
        "replacement_suggestions": replacement_suggestions,
        "manual_review_cases": manual_review_cases,
        "monitor_results": monitor_results,
    }


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_markdown(report: dict) -> str:
    now = report["generated_at"]
    lines = [
        "# Product Check Report",
        f"**Gegenereerd op:** {now}",
        "",
        "> ⚠️ Dit rapport is uitsluitend ter informatie. Geen wijzigingen zijn automatisch gepubliceerd.",
        "> Alle gemarkeerde gevallen vereisen handmatige redactionele beoordeling.",
        "",
    ]

    summary = report["summary"]
    lines += [
        "## Samenvatting",
        f"- Categorieën gecontroleerd: **{summary['categories_checked']}**",
        f"- Totaal gerankte producten: **{summary['total_ranked']}**",
        f"- Geldige producten: **{summary['total_valid']}**",
        f"- Gemarkeerde producten: **{summary['total_flagged']}**",
        f"- Regelovertredingen: **{summary['total_rule_violations']}**",
        f"- Ontbrekende metadata: **{summary['total_missing_metadata']}**",
        f"- Gebroken/ongeldige URL's: **{summary['total_broken_urls']}**",
        f"- Merkdiversiteitsovertredingen: **{summary['total_brand_violations']}**",
        f"- Vervangingsbehoeften: **{summary['total_replacements_needed']}**",
        f"- Handmatige beoordeling vereist: **{summary['total_manual_review']}**",
        "",
    ]

    for cat_report in report["categories"]:
        cat_key = cat_report["category_key"]
        if "error" in cat_report:
            lines.append(f"## ❌ {cat_key}")
            lines.append(f"**Fout:** {cat_report['error']}")
            lines.append("")
            continue

        lines.append(f"## {cat_key} ({cat_report['url_path']})")
        lines.append(f"**Gerankt:** {cat_report['total_ranked']} producten")
        lines.append("")

        if cat_report["valid_products"]:
            lines.append(f"### ✅ Geldige producten ({len(cat_report['valid_products'])})")
            for vp in cat_report["valid_products"]:
                seg = f" · {vp['inferred_price_segment']}" if vp.get("inferred_price_segment") else ""
                lines.append(f"- {vp['product_name']}{seg}")
            lines.append("")

        if cat_report["flagged_products"]:
            lines.append(f"### ⚠️ Gemarkeerde producten ({len(cat_report['flagged_products'])})")
            for fp in cat_report["flagged_products"]:
                lines.append(f"- **{fp['product_name']}**")
                for e in fp.get("errors", []):
                    lines.append(f"  - ❌ {e}")
                for w in fp.get("warnings", []):
                    lines.append(f"  - ⚠️ {w}")
                for mf in fp.get("missing_fields", []):
                    lines.append(f"  - 📋 Ontbrekend veld: `{mf}`")
            lines.append("")

        if cat_report["missing_metadata"]:
            lines.append(f"### 📋 Ontbrekende metadata ({len(cat_report['missing_metadata'])})")
            for mm in cat_report["missing_metadata"]:
                lines.append(f"- **{mm['product']}**: ontbrekend: {', '.join(f'`{f}`' for f in mm['missing_fields'])}")
            lines.append("")

        if cat_report["rule_violations"]:
            lines.append(f"### ❌ Regelovertredingen ({len(cat_report['rule_violations'])})")
            for rv in cat_report["rule_violations"]:
                lines.append(f"- **{rv['product']}**:")
                for e in rv["errors"]:
                    lines.append(f"  - {e}")
            lines.append("")

        if cat_report["brand_diversity_violations"]:
            lines.append(f"### 🏷️ Merkdiversiteitsovertredingen ({len(cat_report['brand_diversity_violations'])})")
            for bv in cat_report["brand_diversity_violations"]:
                lines.append(f"- {bv['message']}")
            lines.append("")

        if cat_report["broken_urls"]:
            lines.append(f"### 🔗 Gebroken of ongeldige URL's ({len(cat_report['broken_urls'])})")
            for bu in cat_report["broken_urls"]:
                lines.append(f"- **{bu['product']}**: {bu['issue']} (`{bu['url']}`)")
            lines.append("")

        if cat_report["replacement_needed"]:
            lines.append(f"### 🔄 Vervangingsbehoeften ({len(cat_report['replacement_needed'])})")
            for prod_name in cat_report["replacement_needed"]:
                lines.append(f"- **{prod_name}** dient vervangen te worden.")
            lines.append("")

        if cat_report["replacement_suggestions"]:
            lines.append(f"### 💡 Vervangingskandidaten")
            for sugg in cat_report["replacement_suggestions"]:
                lines.append(f"#### {sugg['product_name']}")
                if sugg["manual_review_required"]:
                    lines.append("> ⚠️ Handmatige beoordeling vereist. Geen kandidaat is automatisch goedgekeurd.")
                if not sugg["candidates"]:
                    lines.append("- Geen geschikte kandidaten gevonden. Handmatige selectie vereist.")
                for c in sugg["candidates"]:
                    flag = " ⚠️ (gedeeltelijke match)" if c["partial_match"] else ""
                    lines.append(f"- **{c['candidate_name']}** (score: {c['score']}/7){flag}")
                    for r in c["reasons"]:
                        lines.append(f"  - ✓ {r}")
                    for f in c["flags"]:
                        lines.append(f"  - ⚠️ {f}")
                lines.append("")

        if cat_report["manual_review_cases"]:
            lines.append(f"### 🔍 Handmatige beoordeling vereist ({len(cat_report['manual_review_cases'])})")
            for mc in cat_report["manual_review_cases"]:
                lines.append(f"- **{mc['product']}**: {'; '.join(mc['reason'])}")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## Ontbrekende metadata velden voor vollere automatisering",
        "",
        "De volgende velden ontbreken in sommige productdicts en beperken de automatische validatie:",
        "- `price` (absoluut bedrag): gebruikt voor prijssegmentinferring als `price_range` ontbreekt.",
        "- `availability`: vereist voor beschikbaarheidscontrole.",
        "- `rating` / `rating_count`: vereist voor beoordelingssterktevergelijking bij vervangingssuggesties.",
        "- `capacity` (airfryers/vershoudbakjes): vereist voor capaciteitsvergelijking.",
        "- RVS-categorie gebruikt `price_segment` in plaats van `price_range` en `diameter_cm` in plaats van `diameter`.",
        "",
        "## Bevestiging veiligheidsgaranties",
        "",
        "- ✅ Geen wijzigingen zijn automatisch gepubliceerd.",
        "- ✅ Geen rankings zijn automatisch gewijzigd.",
        "- ✅ Alle onzekere gevallen zijn gemarkeerd voor handmatige beoordeling.",
        "- ✅ Vervangingssuggesties zijn uitsluitend ter informatie.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("LeefNatuurlijkenGezond — Product Check Script")
    print("=" * 60)
    print("VEILIGHEIDSGARANTIE: Dit script publiceert NOOIT automatisch wijzigingen.")
    print()

    category_reports = []
    for cat_key, config in CATEGORY_CONFIG.items():
        cat_report = run_category_check(cat_key, config)
        category_reports.append(cat_report)

    total_valid = sum(len(r.get("valid_products", [])) for r in category_reports)
    total_flagged = sum(len(r.get("flagged_products", [])) for r in category_reports)
    total_ranked = sum(r.get("total_ranked", 0) for r in category_reports)
    total_rule_violations = sum(len(r.get("rule_violations", [])) for r in category_reports)
    total_missing = sum(len(r.get("missing_metadata", [])) for r in category_reports)
    total_broken = sum(len(r.get("broken_urls", [])) for r in category_reports)
    total_brand = sum(len(r.get("brand_diversity_violations", [])) for r in category_reports)
    total_replacements = sum(len(r.get("replacement_needed", [])) for r in category_reports)
    total_manual = sum(len(r.get("manual_review_cases", [])) for r in category_reports)

    generated_at = datetime.datetime.now().isoformat(timespec="seconds")

    full_report = {
        "generated_at": generated_at,
        "guardrails": GLOBAL_RULES["guardrails"],
        "summary": {
            "categories_checked": len(category_reports),
            "total_ranked": total_ranked,
            "total_valid": total_valid,
            "total_flagged": total_flagged,
            "total_rule_violations": total_rule_violations,
            "total_missing_metadata": total_missing,
            "total_broken_urls": total_broken,
            "total_brand_violations": total_brand,
            "total_replacements_needed": total_replacements,
            "total_manual_review": total_manual,
        },
        "categories": category_reports,
    }

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "product_check_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✅ JSON rapport opgeslagen: {json_path}")

    md_path = reports_dir / "product_check_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(full_report))
    print(f"✅ Markdown rapport opgeslagen: {md_path}")

    print()
    print("=" * 60)
    print("SAMENVATTING")
    print("=" * 60)
    print(f"  Categorieën gecontroleerd : {len(category_reports)}")
    print(f"  Totaal gerankte producten : {total_ranked}")
    print(f"  Geldig                    : {total_valid}")
    print(f"  Gemarkeerd                : {total_flagged}")
    print(f"  Regelovertredingen        : {total_rule_violations}")
    print(f"  Ontbrekende metadata      : {total_missing}")
    print(f"  Gebroken URL's            : {total_broken}")
    print(f"  Merkdiversiteit           : {total_brand}")
    print(f"  Vervangingsbehoeften      : {total_replacements}")
    print(f"  Handmatige beoordeling    : {total_manual}")
    print()
    print("VEILIGHEIDSBEVESTIGING: Geen rankings gewijzigd. Geen wijzigingen gepubliceerd.")
    print("=" * 60)


if __name__ == "__main__":
    main()
