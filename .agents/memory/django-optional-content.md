---
name: Optional content in Django templates
description: Missing dictionary keys can resolve to methods and leak raw content structures.
---
Do not access optional content keys named `items`, `keys`, or `values` with
Django template dot lookup. Use an explicit dictionary-only lookup.

**Why:** when the key is absent, Django can invoke the dictionary method.
For an optional `items` list this rendered entire sections as Python-style
key/value tuples. Tests checking only whether supplied strings appeared did
not detect the duplicate raw output.

**How to apply:** test both present and absent optional lists, assert the
expected list-item count, and reject raw dictionary/tuple output. Check
rendered structure, not just the presence of source text.
