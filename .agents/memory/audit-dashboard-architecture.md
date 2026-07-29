---
name: Audit dashboard architecture
description: Where central audit logic lives and the rule against duplicating it
---
Rule: all product-audit logic lives in `audits/checks/`; both management commands and the admin dashboard (/admin/product-audits/) must call those shared functions — never re-implement a check in a command, admin view, or template, and never parse console output to reconstruct results.
**Why:** spec requirement of the dashboard task (July 2026); duplication caused divergent results in earlier per-command audits.
**How to apply:** new audits = add a check module + `register_audit(...)` in `audits/checks/__init__.py`; network-dependent checks get `runner=None` with a CLI hint. Duplicate concurrent runs are blocked by the DB constraint `unique_running_audit_per_key`.
