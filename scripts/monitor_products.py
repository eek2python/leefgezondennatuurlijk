#!/usr/bin/env python3
"""
Phase 2: Full product monitoring script.

Loads all products from source files, runs field normalization, rule validation,
live HTTP page checks, availability/price consistency checks, and generates
detailed reports.

Usage:
    python scripts/monitor_products.py            # full run with live HTTP checks
    python scripts/monitor_products.py --no-live  # skip live HTTP checks (fast)

Output:
    reports/product_monitor_report.json
    reports/product_monitor_report.md

SAFETY GUARDRAILS:
  - NEVER modifies products_<category>.py
  - NEVER modifies rankings_<category>.py
  - NEVER auto-publishes any changes
  - All flagged items require manual editorial review
"""

import sys
import json
import datetime
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.product_sources import load_all_categories, CATEGORY_PRODUCT_SOURCES
from services.product_normalization import check_field_consistency, derive_full_image_path
from services.product_validation import validate_product, check_brand_diversity
from services.product_monitoring import monitor_product
from services.replacement_candidates import suggest_replacement_candidates
from services.monitoring_config import MONITORING_CONFIG

import rules.houten_snijplanken as r_snijplanken
import rules.keramische_koekenpannen as r_keramisch
import rules.rvs_koekenpannen as r_rvs
import rules.pfas_vrije_hapjespannen as r_hapjes
import rules.pfas_vrije_wokpannen as r_wok
import rules.pfas_vrije_airfryers as r_airfryers
import rules.glazen_vershoudbakjes as r_vershoudbakjes

RULES_BY_KEY = {
    "keramische_koekenpannen": r_keramisch.RULES,
    "rvs_koekenpannen": r_rvs.RULES,
    "houten_snijplanken": r_snijplanken.RULES,
    "pfas_vrije_hapjespannen": r_hapjes.RULES,
    "pfas_vrije_wokpannen": r_wok.RULES,
    "pfas_vrije_airfryers": r_airfryers.RULES,
    "glazen_vershoudbakjes": r_vershoudbakjes.RULES,
}


# ---------------------------------------------------------------------------
# Per-category runner
# ---------------------------------------------------------------------------

def run_category(slug: str, cat_data: dict, live_check: bool) -> dict:
    rule_key = cat_data.get("rule_key", "")
    rules = RULES_BY_KEY.get(rule_key)
    if rules is None:
        return {
            "slug": slug,
            "rule_key": rule_key,
            "error": f"Geen regel gevonden voor rule_key='{rule_key}'.",
            "products": [],
            "summary": {},
        }

    ranked = cat_data.get("ranked_products", [])
    all_products = cat_data.get("all_products", [])
    load_errors = cat_data.get("load_errors", [])

    if not ranked:
        return {
            "slug": slug,
            "rule_key": rule_key,
            "url_path": cat_data.get("url_path", ""),
            "description": cat_data.get("description", ""),
            "error": f"Geen gerankte producten geladen. Load errors: {load_errors}",
            "products": [],
            "summary": {},
        }

    print(f"  Gerankt: {len(ranked)}  |  Pool: {len(all_products)}")

    brand_check = check_brand_diversity(ranked, max_per_brand=2)

    product_results = []
    for product in ranked:
        norm_check = check_field_consistency(product, rules)
        monitor_result = monitor_product(
            product, rules, live_check=live_check, config=MONITORING_CONFIG
        )

        replacement_suggestion = None
        if monitor_result["replacement_needed"]:
            replacement_suggestion = suggest_replacement_candidates(
                product, rules, all_products, ranked, top_n=3
            )

        image_path = derive_full_image_path(product)

        product_results.append({
            "product_name": product.get("name", ""),
            "slug": product.get("slug", ""),
            "brand": product.get("brand", ""),
            "category": slug,
            "rule_key": rule_key,
            "stored_price": product.get("price"),
            "detected_price": monitor_result["price"]["detected"],
            "price_change_pct": monitor_result["price"]["change_pct"],
            "price_alert": monitor_result["price"]["alert"],
            "price_notes": monitor_result["price"]["notes"],
            "stored_availability": product.get("availability"),
            "detected_availability": monitor_result["availability"]["detected"],
            "availability_consistency": monitor_result["availability"]["consistency"],
            "availability_notes": monitor_result["availability"]["notes"],
            "page_url": product.get("affiliate_url", ""),
            "page_status": monitor_result["page_check"]["classification"],
            "page_reachable": monitor_result["page_check"]["reachable"],
            "page_http_code": monitor_result["page_check"]["status_code"],
            "page_final_url": monitor_result["page_check"]["final_url"],
            "page_error": monitor_result["page_check"]["error"],
            "image_path": image_path,
            "consistency_issues": norm_check["issues"],
            "consistency_warnings": norm_check["warnings"],
            "missing_fields": norm_check["missing_fields"],
            "validation_valid": monitor_result["validation_summary"]["valid"],
            "validation_errors": monitor_result["validation_summary"]["errors"],
            "validation_warnings": monitor_result["validation_summary"]["warnings"],
            "validation_rule_flags": monitor_result["validation_summary"]["rule_flags"],
            "inferred_price_segment": monitor_result["validation_summary"]["inferred_price_segment"],
            "overall_status": monitor_result["status"],
            "manual_review_required": monitor_result["manual_review_required"],
            "replacement_needed": monitor_result["replacement_needed"],
            "replacement_suggestion": replacement_suggestion,
        })

    n_valid = sum(1 for p in product_results if p["overall_status"] == "OK")
    n_flagged = sum(1 for p in product_results if p["overall_status"] != "OK")
    n_manual = sum(1 for p in product_results if p["manual_review_required"])
    n_broken_url = sum(1 for p in product_results if p["page_status"] == "BROKEN")
    n_avail_mismatch = sum(1 for p in product_results if p["availability_consistency"] == "MISMATCH")
    n_price_alert = sum(1 for p in product_results if p["price_alert"])
    n_missing_meta = sum(1 for p in product_results if p["missing_fields"])
    n_replacement = sum(1 for p in product_results if p["replacement_needed"])
    n_brand_violations = len(brand_check["violations"])

    return {
        "slug": slug,
        "rule_key": rule_key,
        "url_path": cat_data.get("url_path", ""),
        "description": cat_data.get("description", ""),
        "load_errors": load_errors,
        "products": product_results,
        "brand_diversity": brand_check,
        "summary": {
            "total": len(ranked),
            "valid": n_valid,
            "flagged": n_flagged,
            "manual_review": n_manual,
            "broken_urls": n_broken_url,
            "availability_mismatches": n_avail_mismatch,
            "price_alerts": n_price_alert,
            "missing_metadata": n_missing_meta,
            "replacement_needed": n_replacement,
            "brand_diversity_violations": n_brand_violations,
        },
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def render_markdown(report: dict, live_check: bool) -> str:
    now = report["generated_at"]
    mode = "met live HTTP-checks" if live_check else "zonder live HTTP-checks (--no-live)"
    lines = [
        "# Product Monitor Report — Fase 2",
        f"**Gegenereerd op:** {now}  ",
        f"**Modus:** {mode}",
        "",
        "> ⚠️ Dit rapport is uitsluitend ter informatie.",
        "> Geen producten of rankings zijn automatisch gewijzigd.",
        "> Alle gemarkeerde gevallen vereisen handmatige redactionele beoordeling.",
        "",
    ]

    s = report["summary"]
    lines += [
        "## A. Samenvatting",
        f"| Metric | Waarde |",
        f"|--------|--------|",
        f"| Categorieën gecontroleerd | **{s['categories_checked']}** |",
        f"| Totaal gecontroleerde producten | **{s['total_products']}** |",
        f"| Geldige producten (status OK) | **{s['total_valid']}** |",
        f"| Gemarkeerde producten | **{s['total_flagged']}** |",
        f"| Handmatige beoordeling vereist | **{s['total_manual_review']}** |",
        f"| Gebroken URL's | **{s['total_broken_urls']}** |",
        f"| Beschikbaarheidsmismatches | **{s['total_avail_mismatches']}** |",
        f"| Prijsalerts | **{s['total_price_alerts']}** |",
        f"| Ontbrekende metadata | **{s['total_missing_metadata']}** |",
        f"| Merkdiversiteitsovertredingen | **{s['total_brand_violations']}** |",
        f"| Vervangingsbehoeften | **{s['total_replacements']}** |",
        "",
    ]

    for cat in report["categories"]:
        slug = cat["slug"]
        if "error" in cat:
            lines.append(f"## ❌ {slug}")
            lines.append(f"**Fout:** {cat['error']}")
            lines.append("")
            continue

        cs = cat["summary"]
        lines += [
            f"## B. {slug} — {cat['description']}",
            f"**URL:** `{cat['url_path']}` | **Gerankt:** {cs['total']} | "
            f"✅ {cs['valid']} OK | ⚠️ {cs['flagged']} gemarkeerd",
            "",
            f"| Check | Resultaat |",
            f"|-------|-----------|",
            f"| Gebroken URL's | {cs['broken_urls']} |",
            f"| Beschikbaarheidsmismatches | {cs['availability_mismatches']} |",
            f"| Prijsalerts | {cs['price_alerts']} |",
            f"| Ontbrekende metadata | {cs['missing_metadata']} |",
            f"| Merkdiversiteitsovertredingen | {cs['brand_diversity_violations']} |",
            f"| Handmatige beoordeling | {cs['manual_review']} |",
            f"| Vervangingsbehoeften | {cs['replacement_needed']} |",
            "",
        ]

        if cat["brand_diversity"]["violations"]:
            lines.append("### 🏷️ Merkdiversiteitsovertredingen")
            for brand, info in cat["brand_diversity"]["violations"].items():
                lines.append(f"- {info['message']}")
            lines.append("")

        lines.append("### C. Per-product detail")
        lines.append("")

        for p in cat["products"]:
            status_icon = {
                "OK": "✅", "FLAG": "⚠️", "REPLACE": "❌", "MANUAL_REVIEW": "🔍"
            }.get(p["overall_status"], "❓")
            lines.append(f"#### {status_icon} {p['product_name']}")
            lines.append(f"- **Merk:** {p['brand']} | **Slug:** `{p['slug']}`")
            lines.append(f"- **Status:** `{p['overall_status']}`")

            lines.append(f"- **Pagina:** {p['page_status']} "
                         f"(HTTP {p['page_http_code'] or '—'}) "
                         f"| URL: `{p['page_url'][:70]}...`" if len(p['page_url']) > 70
                         else f"- **Pagina:** {p['page_status']} (HTTP {p['page_http_code'] or '—'})")

            if p["page_error"]:
                lines.append(f"- **Pagina-fout:** {p['page_error']}")

            lines.append(
                f"- **Beschikbaarheid:** opgeslagen `{p['stored_availability']}` "
                f"→ gedetecteerd `{p['detected_availability'] or 'onbekend'}` "
                f"| Consistentie: `{p['availability_consistency']}`"
            )
            if p["availability_consistency"] == "MISMATCH":
                lines.append(f"  - ⚠️ {p['availability_notes']}")

            lines.append(
                f"- **Prijs:** opgeslagen `€{p['stored_price'] or '—'}` "
                f"| gedetecteerd `{p['detected_price'] or 'n.v.t.'}` "
                f"| segment: `{p['inferred_price_segment'] or 'onbekend'}`"
            )
            if p["price_alert"]:
                lines.append(f"  - ⚠️ {p['price_notes']}")

            if p["missing_fields"]:
                lines.append(f"- **Ontbrekende velden:** {', '.join(f'`{f}`' for f in p['missing_fields'])}")

            if p["consistency_issues"]:
                for issue in p["consistency_issues"]:
                    lines.append(f"- ❌ Consistentieprobleem: {issue}")

            if p["consistency_warnings"]:
                for w in p["consistency_warnings"]:
                    lines.append(f"- ⚠️ Waarschuwing: {w}")

            if p["validation_errors"]:
                for e in p["validation_errors"]:
                    lines.append(f"- ❌ Regelovertreding: {e}")

            if p["validation_warnings"]:
                for w in p["validation_warnings"]:
                    lines.append(f"- ⚠️ Regelwaarschuwing: {w}")

            if p["manual_review_required"]:
                lines.append("- 🔍 **Handmatige beoordeling vereist.**")

            if p["replacement_needed"] and p["replacement_suggestion"]:
                sugg = p["replacement_suggestion"]
                lines.append(f"- 🔄 **Vervanging nodig.** {sugg['notes']}")
                for c in sugg["candidates"]:
                    flag = " ⚠️" if c["partial_match"] else ""
                    lines.append(f"  - Kandidaat: **{c['candidate_name']}** (score {c['score']}/7){flag}")

            lines.append("")

        lines.append("---")
        lines.append("")

    lines += [
        "## Ontbrekende fields voor vollere automatisering",
        "",
        "- `price` (absoluut bedrag) op RVS-producten — die gebruiken `price_segment`.",
        "- `availability` — sommige products tonen 'OutStock' i.p.v. het verwachte 'OutOfStock'.",
        "- `capacity` — airfryers en vershoudbakjes; vereist voor capaciteitsvergelijking.",
        "- Live prijsextractie — affiliate redirect-URL's (bol.com) zijn niet eenvoudig te parsen.",
        "",
        "## Bevestiging veiligheidsgaranties",
        "",
        "- ✅ Geen `products_<category>.py` bestanden zijn gewijzigd.",
        "- ✅ Geen `rankings_<category>.py` bestanden zijn gewijzigd.",
        "- ✅ Geen wijzigingen zijn automatisch gepubliceerd.",
        "- ✅ Alle onzekere gevallen zijn gemarkeerd voor handmatige beoordeling.",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(live_check: bool = True):
    print("=" * 60)
    print("LeefNatuurlijkenGezond — Product Monitor (Fase 2)")
    print("=" * 60)
    if live_check:
        print("Modus: LIVE — voert echte HTTP HEAD-checks uit op product-URL's.")
        print("Dit kan enkele minuten duren afhankelijk van het aantal producten.")
    else:
        print("Modus: DRY RUN — slaat HTTP-checks over (gebruik --no-live voor snelle validatie).")
    print("GARANTIE: Geen rankings of productbestanden worden gewijzigd.")
    print()

    all_categories = load_all_categories()
    category_results = []

    for slug, cat_data in all_categories.items():
        print(f"\n[{slug}] Laden en valideren...")
        if cat_data.get("load_errors"):
            for err in cat_data["load_errors"]:
                print(f"  ⚠️  {err}")
        result = run_category(slug, cat_data, live_check=live_check)
        category_results.append(result)

    total = sum(r["summary"].get("total", 0) for r in category_results)
    total_valid = sum(r["summary"].get("valid", 0) for r in category_results)
    total_flagged = sum(r["summary"].get("flagged", 0) for r in category_results)
    total_manual = sum(r["summary"].get("manual_review", 0) for r in category_results)
    total_broken = sum(r["summary"].get("broken_urls", 0) for r in category_results)
    total_avail = sum(r["summary"].get("availability_mismatches", 0) for r in category_results)
    total_price = sum(r["summary"].get("price_alerts", 0) for r in category_results)
    total_missing = sum(r["summary"].get("missing_metadata", 0) for r in category_results)
    total_brand = sum(r["summary"].get("brand_diversity_violations", 0) for r in category_results)
    total_replace = sum(r["summary"].get("replacement_needed", 0) for r in category_results)

    generated_at = datetime.datetime.now().isoformat(timespec="seconds")

    full_report = {
        "generated_at": generated_at,
        "live_checks": live_check,
        "summary": {
            "categories_checked": len(category_results),
            "total_products": total,
            "total_valid": total_valid,
            "total_flagged": total_flagged,
            "total_manual_review": total_manual,
            "total_broken_urls": total_broken,
            "total_avail_mismatches": total_avail,
            "total_price_alerts": total_price,
            "total_missing_metadata": total_missing,
            "total_brand_violations": total_brand,
            "total_replacements": total_replace,
        },
        "categories": category_results,
    }

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    json_path = reports_dir / "product_monitor_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n✅ JSON rapport: {json_path}")

    md_path = reports_dir / "product_monitor_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(full_report, live_check))
    print(f"✅ Markdown rapport: {md_path}")

    print()
    print("=" * 60)
    print("SAMENVATTING")
    print("=" * 60)
    print(f"  Categorieën          : {len(category_results)}")
    print(f"  Totaal producten     : {total}")
    print(f"  Status OK            : {total_valid}")
    print(f"  Gemarkeerd           : {total_flagged}")
    print(f"  Handmatig review     : {total_manual}")
    print(f"  Gebroken URL's       : {total_broken}")
    print(f"  Beschikbaarheid mis  : {total_avail}")
    print(f"  Prijsalerts          : {total_price}")
    print(f"  Ontbrekende metadata : {total_missing}")
    print(f"  Merkdiversiteit      : {total_brand}")
    print(f"  Vervangingsbehoeften : {total_replace}")
    print()
    print("GARANTIE: Geen rankings of productbestanden gewijzigd.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LeefNatuurlijkenGezond product monitor (Fase 2)")
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Sla live HTTP-checks over (snellere droge validatierun).",
    )
    args = parser.parse_args()
    main(live_check=not args.no_live)
