---
name: Cold Python compilation on Render
description: Why warm local imports can hide a memory-limit failure during a clean Render deployment.
---

A successful import from cached bytecode does not establish that a clean Python build fits Render's 512 MB memory limit. When a catalogue module contains repeated top-level definitions, measure cold compilation from source under the deployment limit before calling a release safe. Preserve the last effective catalogue definition when removing copies.

**Why:** A local warm import used little memory, while compiling the repeated source under a 512 MB address-space cap raised `MemoryError`. Old definitions are overwritten at runtime but still parsed and compiled for a fresh deploy.

**How to apply:** For Render memory failures, first compare the deployed commit with local source and check for repeated catalogue definitions. Then test a cold source compile under the Render limit and inspect Render build/runtime logs to distinguish compilation from worker-related memory usage. Do not infer that a clean release is safe from a running development server or an import that uses cached bytecode.