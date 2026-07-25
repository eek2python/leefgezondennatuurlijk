"""Tests voor de gebruiksinformatie ("Geschikt voor") en de
vershoudbakjes-datakwaliteit (spec §13)."""

import copy
import re

from django.test import TestCase

from products.products_vershoudcontainers import PRODUCTS
from products.rankings_vershoudcontainers import RANKINGS
from utils.usage_helpers import build_usage_display, merge_usage, validate_usage
from utils.variant_helpers import prepare_product_variants


class UsageDisplayTests(TestCase):
    def test_usage_rows_rendered_correctly(self):
        usage = {
            "oven": {"container": True, "lid": False, "note": "Alleen het glazen bakje"},
            "microwave": {"container": True, "lid": True, "note": "Ventiel openen"},
        }
        rows = build_usage_display(usage)
        self.assertEqual([r["label"] for r in rows], ["Oven", "Magnetron"])
        self.assertEqual(rows[0]["text"], "Ja, alleen het glazen bakje")
        self.assertEqual(rows[1]["text"], "Ja, ventiel openen")

    def test_unknown_values_are_hidden_never_shown_as_nee(self):
        usage = {
            "oven": {"container": None, "lid": None, "note": None},
            "freezer": {"container": True, "lid": None, "note": None},
            "dishwasher": {"container": False, "lid": None, "note": None},
        }
        rows = build_usage_display(usage)
        keys = [r["key"] for r in rows]
        self.assertNotIn("oven", keys)  # onbekend: geen rij, geen "Nee"
        self.assertIn("freezer", keys)
        self.assertEqual(rows[keys.index("freezer")]["text"], "Bakje: ja")
        self.assertEqual(rows[keys.index("dishwasher")]["text"], "Nee")

    def test_variant_inherits_product_level_usage(self):
        merged = merge_usage({"oven": {"container": True, "lid": False}}, None)
        self.assertEqual(merged["oven"], {"container": True, "lid": False})

    def test_variant_usage_overrides_product_level(self):
        base = {"microwave": {"container": True, "lid": True, "note": "Ventiel openen"}}
        override = {"microwave": {"lid": False, "note": "Zonder deksel verwarmen"}}
        merged = merge_usage(base, override)
        self.assertEqual(
            merged["microwave"],
            {"container": True, "lid": False, "note": "Zonder deksel verwarmen"},
        )

    def test_usage_schema_validation(self):
        self.assertEqual(validate_usage(None), [])
        self.assertTrue(validate_usage({"grill": {}}, "x"))
        self.assertTrue(validate_usage({"oven": {"container": "ja"}}, "x"))
        self.assertEqual(
            validate_usage({"oven": {"container": True, "lid": None, "note": None}}, "x"),
            [],
        )


class UsagePageTests(TestCase):
    def test_page_shows_geschikt_voor_and_variant_payload(self):
        html = self.client.get("/vershoudcontainers/?uitvoering=enkel").content.decode()
        self.assertIn("Geschikt voor", html)
        self.assertIn("Ja, alleen het glazen bakje", html)
        # variantwissel: usage-rijen zitten in de JSON-payload per variant
        self.assertIn('data-shape-usage', html)
        self.assertIn('"usage"', html)

    def test_lid_not_ovenproof_not_required_in_cons(self):
        for key in ("pyrex_cook_store_enkel", "mepal_easyclip_glass_enkel"):
            cons = PRODUCTS[key]["cons"]
            self.assertFalse(
                any("oven" in c.lower() for c in cons),
                f"'{key}' hoort dekselinfo in usage te hebben, niet in cons",
            )
            self.assertFalse(PRODUCTS[key]["usage"]["oven"]["lid"])


class EditorialRulesTests(TestCase):
    def test_max_three_pros_two_cons(self):
        for key, p in PRODUCTS.items():
            self.assertLessEqual(len(p.get("pros") or []), 3, key)
            self.assertLessEqual(len(p.get("cons") or []), 2, key)

    def test_no_capacity_values_in_shape_field(self):
        pattern = re.compile(r"\d+\s*(ml|l)\b", re.IGNORECASE)
        for key, p in PRODUCTS.items():
            for v in p.get("variants") or []:
                shape = v.get("shape") or (v.get("options") or {}).get("shape") or ""
                if isinstance(shape, str):
                    self.assertIsNone(pattern.search(shape), f"{key}: {shape!r}")

    def test_liter_labels_use_dutch_comma(self):
        pattern = re.compile(r"\d+\.\d+\s*L\b")
        for key, p in PRODUCTS.items():
            for v in p.get("variants") or []:
                labels = list((v.get("option_labels") or {}).values())
                if v.get("label"):
                    labels.append(v["label"])
                for label in labels:
                    self.assertIsNone(pattern.search(str(label)), f"{key}: {label!r}")

    def test_material_spelling_consistent(self):
        for key, p in PRODUCTS.items():
            self.assertNotEqual(p.get("material"), "Borosilicaat glas", key)


class StructuralTests(TestCase):
    def test_each_family_ranked_at_most_once(self):
        seen = set()
        for keys in RANKINGS.values():
            for k in keys:
                self.assertNotIn(k, seen)
                seen.add(k)
                self.assertIn(k, PRODUCTS)

    def test_exactly_one_default_variant_per_family(self):
        for key, p in PRODUCTS.items():
            variants = [v for v in (p.get("variants") or []) if v.get("id")]
            if variants:
                defaults = [v for v in variants if v.get("is_default")]
                self.assertEqual(len(defaults), 1, key)

    def test_variant_ids_and_option_combos_unique(self):
        for key, p in PRODUCTS.items():
            variants = [v for v in (p.get("variants") or []) if v.get("id")]
            ids = [v["id"] for v in variants]
            self.assertEqual(len(ids), len(set(ids)), key)
            combos = [
                tuple(sorted((v.get("options") or {}).items()))
                for v in variants
                if v.get("options")
            ]
            self.assertEqual(len(combos), len(set(combos)), key)

    def test_recent_3delig_images_still_exist(self):
        import os
        from django.conf import settings
        for key in ("mepal_easyclip_glass_3delig", "igluu_meal_prep_3delig",
                    "pyrex_cook_heat_3delig", "bormioli_frigoverre_3delig",
                    "luminarc_purebox_3delig"):
            p = PRODUCTS[key]
            variants = p.get("variants") or []
            checks = [(v.get("image_path") or p["image_path"], v["image"]) for v in variants if v.get("image")]
            if not checks:
                checks = [(p["image_path"], p["image"])]
            for path, image in checks:
                full = os.path.join(settings.BASE_DIR, "static", path, image)
                self.assertTrue(os.path.exists(full), full)

    def test_existing_selectors_still_work(self):
        # Igluu vorm-selector en Lock&Lock inhoud-selector blijven functioneren
        igluu = copy.deepcopy(PRODUCTS["igluu_meal_prep_3delig"])
        prepare_product_variants(igluu)
        self.assertTrue(igluu.get("shape_variants"))
        locknlock = copy.deepcopy(PRODUCTS["locknlock_enkel"])
        prepare_product_variants(locknlock)
        self.assertEqual(len(locknlock["shape_variants"]), 3)
        # gemigreerde IKEA/Mepal capaciteitsselectors
        for key in ("ikea_365+_enkel", "mepal_easyclip_glass_enkel"):
            p = copy.deepcopy(PRODUCTS[key])
            prepare_product_variants(p)
            self.assertTrue(p.get("shape_variants"), key)
            self.assertEqual(
                [sel["key"] for sel in p.get("variant_selectors") or []], ["capacity"], key
            )

    def test_validator_reports_but_page_renders(self):
        from products.views import VERSHOUDBAKJES_AUDIT_WARNINGS
        self.assertIsInstance(VERSHOUDBAKJES_AUDIT_WARNINGS, list)
        for slug in ("enkel", "3-delig", "5-delig"):
            response = self.client.get(f"/vershoudcontainers/?uitvoering={slug}")
            self.assertEqual(response.status_code, 200)
