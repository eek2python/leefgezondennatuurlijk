---
name: Server restart required after Python changes
description: Django dev server in this repl does not reliably autoreload; restart workflow before verifying.
---
The rule: after editing Python code (helpers, views, templatetags), restart the "Start application" workflow before checking rendered pages with curl/screenshot.

**Why:** Twice a page kept serving old behavior (missing `static_version` tag → 500; old button labels) even though the code on disk was correct — the running process predated the change and autoreload did not pick it up.

**How to apply:** Treat "code correct but page unchanged" as a stale-process symptom first; restart the workflow, then re-verify. Template-only edits usually don't need it.
