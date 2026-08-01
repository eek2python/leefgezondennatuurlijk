#!/bin/bash
# Post-merge setup: idempotent, non-interactief, fail fast.
set -e

cd "$(dirname "$0")/.."

# Databasemigraties (no-op als er niets te migreren valt).
python manage.py migrate --noinput

# Snelle sanity check dat het project importeert en configuratie klopt.
python manage.py check
