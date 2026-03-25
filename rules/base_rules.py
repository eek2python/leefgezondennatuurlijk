GLOBAL_RULES = {
    "max_products_per_brand": 2,

    "required_fields": ["name", "brand", "material", "affiliate_url"],
    "recommended_fields": ["price", "price_range", "features", "pros", "cons", "description", "rating", "rating_count"],

    "placeholder_url_indicators": ["TODO", "todo", "example.com", "placeholder", "http://#", "https://#"],
    "empty_url_values": [None, "", "#"],

    "nl_market_required": True,
    "auto_replace_allowed": False,
    "auto_publish_allowed": False,

    "replacement_match_criteria": [
        "category",
        "material",
        "size_or_capacity",
        "price_segment",
        "review_strength",
        "availability",
        "brand_diversity",
    ],

    "flag_on_uncertain_safety": True,
    "flag_on_unclear_material": True,

    "price_range_to_segment": {
        "€": "budget",
        "€€": "middenklasse",
        "€€€": "middenklasse",
        "€€€€": "premium",
    },

    "valid_availability_values": ["InStock", "instock", "in_stock", "available"],

    "guardrails": [
        "never invent safety claims",
        "never infer PFAS-free with certainty if metadata is unclear",
        "never auto-replace a product if category fit is uncertain",
        "never mix RVS and ceramic categories",
        "never add plastic/glass/marble boards to houten snijplanken",
        "never add fully plastic storage sets to glazen vershoudbakjes",
        "never accept placeholder URLs as valid product pages",
        "never auto-publish changes to live website data",
    ],
}
