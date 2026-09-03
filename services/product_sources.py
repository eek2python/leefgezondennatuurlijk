"""
Category product source registry and safe loader.

Maps website category slugs to their Python data modules and rule keys.
Provides safe, graceful loading with error reporting.
Never modifies source files.
"""

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Explicit category source registry
# ---------------------------------------------------------------------------

CATEGORY_PRODUCT_SOURCES: dict[str, dict] = {
    "koekenpannen": {
        "module": "products.products_koekenpannen",
        "variable": "PRODUCTS",
        "rule_key": "keramische_koekenpannen",
        "rankings_module": "products.rankings_koekenpannen",
        "rankings_variable": "RANKINGS",
        "rankings_type": "dict_by_size",
        "url_path": "/koekenpannen/",
        "description": "Keramische PFAS-vrije koekenpannen",
    },
    "rvs-koekenpannen": {
        "module": "products.products_rvs_koekenpannen",
        "variable": "PRODUCTS",
        "rule_key": "rvs_koekenpannen",
        "rankings_module": "products.rankings_rvs_koekenpannen",
        "rankings_variable": "RANKINGS",
        "rankings_type": "list",
        "url_path": "/rvs-koekenpannen/",
        "description": "RVS koekenpannen",
    },
    "koolstofstalen-koekenpannen": {
        "module": "products.products_koolstofstaal_koekenpannen",
        "variable": "PRODUCTS",
        "rule_key": "koolstofstalen_koekenpannen",
        "rankings_module": "products.rankings_koolstofstaal_koekenpannen",
        "rankings_variable": "RANKINGS",
        "rankings_type": "dict_by_size",
        "url_path": "/koolstofstalen-koekenpannen/",
        "description": "Koolstofstalen koekenpannen",
    },
    "hapjespannen": {
        "module": "products.products_hapjespannen",
        "variable": "PRODUCTS",
        "rule_key": "pfas_vrije_hapjespannen",
        "rankings_module": "products.rankings_hapjespannen",
        "rankings_variable": "RANKINGS",
        "rankings_type": "dict_by_size",
        "url_path": "/hapjespannen/",
        "description": "PFAS-vrije hapjespannen",
    },
    "wokpannen": {
        "module": "products.products_wokpannen",
        "variable": "PRODUCTS",
        "rule_key": "pfas_vrije_wokpannen",
        "rankings_module": "products.rankings_wokpannen",
        "rankings_variable": "RANKINGS",
        "rankings_type": "dict_by_size",
        "url_path": "/wokpannen/",
        "description": "PFAS-vrije wokpannen",
    },
    "snijplanken": {
        "module": "products.products_snijplanken",
        "variable": "PRODUCTS",
        "rule_key": "houten_snijplanken",
        "rankings_module": "products.rankings_snijplanken",
        "rankings_variable": "RANKINGS",
        "rankings_type": "list",
        "url_path": "/snijplanken/",
        "description": "Houten en bamboe snijplanken",
    },
    "airfryers": {
        "module": "products.products_airfryers",
        "variable": "PRODUCTS",
        "rule_key": "pfas_vrije_airfryers",
        "rankings_module": "products.rankings_airfryers",
        "rankings_variable": "RANKINGS",
        "rankings_type": "list",
        "url_path": "/airfryers/",
        "description": "PFAS-vrije airfryers",
    },
    "vershoudcontainers": {
        "module": "products.products_vershoudcontainers",
        "variable": "PRODUCTS",
        "rule_key": "glazen_vershoudbakjes",
        "rankings_module": "products.rankings_vershoudcontainers",
        "rankings_variable": "RANKINGS",
        "rankings_type": "list",
        "url_path": "/vershoudcontainers/",
        "description": "Glazen vershoudbakjes",
    },
}


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def _import_attr(module_path: str, attr: str):
    """Safely import an attribute from a module. Returns (value, error_msg)."""
    try:
        mod = importlib.import_module(module_path)
        if not hasattr(mod, attr):
            return None, f"Module '{module_path}' has no attribute '{attr}'."
        return getattr(mod, attr), None
    except ImportError as e:
        return None, f"Cannot import module '{module_path}': {e}"
    except Exception as e:
        return None, f"Unexpected error loading '{module_path}.{attr}': {e}"


def _flatten_rankings(rankings, rankings_type: str) -> list[str]:
    """Flatten a rankings dict (size-keyed) or list into a list of unique product keys."""
    if rankings is None:
        return []
    if rankings_type == "dict_by_size":
        seen = set()
        keys = []
        for size_keys in rankings.values():
            for k in size_keys:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        return keys
    seen = set()
    keys = []
    for k in rankings:
        if k not in seen:
            seen.add(k)
            keys.append(k)
    return keys


def load_category(slug: str) -> dict:
    """
    Load a single category's products.

    Returns a dict:
      - slug: str
      - description: str
      - rule_key: str
      - url_path: str
      - products_dict: dict[str, dict]   all products in the module
      - ranked_keys: list[str]           deduplicated keys from rankings
      - ranked_products: list[dict]      ordered product dicts matching ranked_keys
      - all_products: list[dict]         all product dicts (for candidate pool)
      - load_errors: list[str]
    """
    result = {
        "slug": slug,
        "description": "",
        "rule_key": "",
        "url_path": "",
        "rankings_type": "list",
        "rankings_raw": None,
        "slug_to_sizes": {},
        "products_dict": {},
        "ranked_keys": [],
        "ranked_products": [],
        "all_products": [],
        "load_errors": [],
    }

    source = CATEGORY_PRODUCT_SOURCES.get(slug)
    if source is None:
        result["load_errors"].append(f"Unknown category slug '{slug}'. Not in CATEGORY_PRODUCT_SOURCES.")
        return result

    result["description"] = source.get("description", "")
    result["rule_key"] = source.get("rule_key", "")
    result["url_path"] = source.get("url_path", "")
    result["rankings_type"] = source.get("rankings_type", "list")

    products_dict, err = _import_attr(source["module"], source["variable"])
    if err:
        result["load_errors"].append(err)
        return result
    if not isinstance(products_dict, dict):
        result["load_errors"].append(f"PRODUCTS in '{source['module']}' is not a dict.")
        return result

    result["products_dict"] = products_dict
    result["all_products"] = list(products_dict.values())

    rankings, err = _import_attr(source["rankings_module"], source["rankings_variable"])
    if err:
        result["load_errors"].append(err)
        result["ranked_keys"] = []
        result["ranked_products"] = list(products_dict.values())
        return result

    rankings_type = source.get("rankings_type", "list")
    ranked_keys = _flatten_rankings(rankings, rankings_type)
    result["ranked_keys"] = ranked_keys
    result["rankings_raw"] = rankings

    slug_to_sizes: dict[str, list[str]] = {}
    if rankings_type == "dict_by_size" and isinstance(rankings, dict):
        for size_key, size_product_keys in rankings.items():
            for k in size_product_keys:
                if k not in slug_to_sizes:
                    slug_to_sizes[k] = []
                slug_to_sizes[k].append(str(size_key))
    result["slug_to_sizes"] = slug_to_sizes

    ranked_products = []
    for key in ranked_keys:
        p = products_dict.get(key)
        if p is None:
            result["load_errors"].append(f"Ranking key '{key}' not found in PRODUCTS dict.")
        else:
            ranked_products.append(p)

    result["ranked_products"] = ranked_products
    return result


def load_all_categories() -> dict[str, dict]:
    """Load all registered categories. Returns {slug: category_data}."""
    return {slug: load_category(slug) for slug in CATEGORY_PRODUCT_SOURCES}
