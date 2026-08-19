---
name: Render migration discipline
description: Operational rule for schema changes used by catalogue rendering on Render.
---

Any Render release containing Django model changes used during catalogue
enrichment must verify and apply migrations against the deployed database
before the web service handles requests.

**Why:** Replit's post-merge setup applies migrations to its own local
database, but that does not update Render's separate database. A missing
maintenance table causes every affected catalogue request to fail before
product-specific rendering, even when the same revision works locally.

**How to apply:** Use a Render release/pre-deploy step (or an explicitly
approved manual maintenance window) to run `showmigrations` and
`migrate --noinput`, then restart and smoke-test representative detail and
category routes. Do not suppress missing-table errors in request code.