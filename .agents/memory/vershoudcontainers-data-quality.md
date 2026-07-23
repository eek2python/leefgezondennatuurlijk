---
name: Vershoudcontainers data quality gotchas
description: Pitfalls in user-supplied product dicts and test assertions for the vershoudcontainers category
---

- User-added product entries may be copy-pastes of an existing product with only name/brand changed (e.g. the OXO 6-delig entry duplicated Glasslock's description, capacities, and image). **Rule:** never rank/publish such placeholder entries; unrank with a comment in the rankings file and report to the user instead of inventing data.
- **Why:** the site's editorial credibility depends on verifiable product data; showing another brand's photo/specs under a different name is misleading.
- **How to apply:** when new products appear in `products_*.py`, diff their description/image/capacities against existing entries before ranking.
- Product slugs must be hyphenated ASCII; `+` in a slug breaks Django's `<slug:>` converter (URL 500s and redirects for `+` URLs are dead code — the old URL never resolved).
- Test-assertion traps seen here: `"0 ml"` substring-matches `"800 ml"`; template labels render on their own line so `">Label"` assertions fail; verdict texts can mention other set sizes, so page-scoping assertions should target full product names.
