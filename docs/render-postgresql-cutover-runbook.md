# Render PostgreSQL Cutover Runbook

## Scope and current status

This is a pre-cutover procedure only. It does not authorize creating a Render
PostgreSQL database, changing Render variables, deploying, restarting the
service, migrating production, syncing production affiliate states, or changing
production data.

Task #15 prepared the repository for explicit database selection:

```text
Development/Replit: SQLite by default
Production/Render: PostgreSQL only when explicitly configured
```

The repository was validated against a disposable local PostgreSQL instance.
The live service described in this runbook is a separate Render service. No
Render connector or Shell access is available in this workspace, so its live
SQLite inventory has **not** been read. Run the commands below in the Render
Dashboard Shell (or an SSH session to the actual running service), save the
sanitized output with the change record, and do not proceed to cutover until it
has been reviewed.

The repository's Replit-only post-merge script contains
`python manage.py migrate --noinput`. It is not a Render configuration in this
repository, but it proves that a migration-capable script exists. The future
cutover must explicitly prove that no Render build, pre-deploy, start, or
custom shell command invokes this script from an old SQLite-only revision.

> Do not use Render's ephemeral SSH-instance option for inventory or backup of
> the live SQLite file. It has a fresh filesystem. Use the actual running
> production instance selected in Render Shell. If the service has more than
> one instance, inventory each instance first: filesystem SQLite may differ per
> instance, which is a stop condition.

## Repository baseline confirmed locally

The following was verified against the current repository and local SQLite
database:

| Item | Result |
| --- | --- |
| Local database engine | `django.db.backends.sqlite3` |
| Local SQLite file | `db.sqlite3` |
| Product migrations | `0001_initial`, `0002_affiliateproductstate` |
| Audit migrations | `0001_initial`, `0002_productauditrun_unique_running_audit_per_key` |
| New migrations after Task #15 | None (`makemigrations --check --dry-run`) |
| Current unique catalogue slugs | 140 |
| Local `AffiliateProductState` rows | 140 |
| Local `Category` / `Product` rows | 0 / 0 |

The 140 count is evidence from the current catalogue, not a permanent
invariant. The sync command iterates `ALL_PRODUCTS_BY_SLUG`, so its expected
row count changes whenever a parent catalogue product is added or removed. It
includes one row per catalogue parent slug; individual variants do not create
additional rows unless they are independently represented in that mapping.

## A. Production inventory commands

Run these commands in the Render Shell attached to the **currently serving**
instance. They only read the database. Never paste the output of `DATABASE_URL`
or any other secret into a ticket, chat, or source control.

### 1. Confirm database identity and SQLite-file health

```bash
python manage.py shell <<'PY'
from pathlib import Path
from django.conf import settings
from django.db import connection

name = settings.DATABASES["default"]["NAME"]
path = Path(name) if connection.vendor == "sqlite" else None

print("vendor=", connection.vendor)
print("engine=", settings.DATABASES["default"]["ENGINE"])
print("database_name=", name)
print("file_exists=", path.exists() if path else "not-applicable")
print("file_size_bytes=", path.stat().st_size if path and path.exists() else "not-applicable")
PY

python manage.py showmigrations
```

**STOP** if the reported vendor is not `sqlite` while this inventory is
intended to assess the existing SQLite deployment, if the file is missing, or
if migrations differ from the expected deployed revision. Record the actual
path; never assume it is `db.sqlite3`.

### 2. Capture application record counts

```bash
python manage.py shell <<'PY'
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, User
from django.contrib.sessions.models import Session
from audits.models import ProductAuditIssue, ProductAuditRun
from products.models import AffiliateProductState, Category, Click, Product

models = {
    "products.AffiliateProductState": AffiliateProductState,
    "products.Category": Category,
    "products.Product": Product,
    "products.Click": Click,
    "audits.ProductAuditRun": ProductAuditRun,
    "audits.ProductAuditIssue": ProductAuditIssue,
    "auth.User": User,
    "auth.Group": Group,
    "admin.LogEntry": LogEntry,
    "sessions.Session": Session,
}
for label, model in models.items():
    print(f"{label}={model.objects.count()}")
PY
```

This output contains counts only. Do not print user names, email addresses,
password hashes, IP addresses, user agents, session values, or raw audit
payloads.

### 3. Inspect only the necessary AffiliateProductState metadata

```bash
python manage.py shell <<'PY'
from products.models import AffiliateProductState
from products.views import ALL_PRODUCTS_BY_SLUG
from products.management.commands.sync_affiliate_product_states import (
    _get_effective_commercial_fields,
)

states = AffiliateProductState.objects.order_by("slug")
checked = states.exclude(price_last_checked__isnull=True)
different_from_baseline = []

for state in states:
    entry = ALL_PRODUCTS_BY_SLUG.get(state.slug)
    if entry is None:
        different_from_baseline.append(state.slug)
        continue
    baseline = _get_effective_commercial_fields(entry["data"])
    if (
        state.price != baseline["price"]
        or state.availability != baseline["availability"]
        or state.price_last_checked is not None
    ):
        different_from_baseline.append(state.slug)

print("total=", states.count())
print("price_populated=", states.exclude(price__isnull=True).count())
print("availability_populated=", states.exclude(availability="").count())
print("checked_date_populated=", checked.count())
print("oldest_checked_date=", checked.order_by("price_last_checked").values_list("price_last_checked", flat=True).first())
print("newest_checked_date=", checked.order_by("-price_last_checked").values_list("price_last_checked", flat=True).first())
print("sample_slugs=", list(states.values_list("slug", flat=True)[:10]))
print("different_or_manually_checked_count=", len(different_from_baseline))
print("different_or_manually_checked_sample=", different_from_baseline[:10])
PY
```

The last two lines identify rows worth preserving. A row equal to the current
catalogue baseline can safely be regenerated; a row with a different price or
availability, an orphaned slug, or a non-null `price_last_checked` is treated
as potentially manually maintained. This comparison does not print commercial
values.

## B. Expected safe outputs

| Command | Expected result |
| --- | --- |
| Database identity | `vendor= sqlite`, an existing file path, and a non-zero file size |
| Migration listing | Existing migrations are applied; record the exact output |
| Record counts | Counts only, without personal or secret data |
| Affiliate metadata | Counts, dates, and limited slug samples; no prices, users, or URLs |

The live database is not assumed to match local counts. In particular, local
`Product`, `Category`, `Click`, audit, user, and session counts provide no
evidence about production data.

## C. Production model classification

| Model or data | Default classification | Decision rule |
| --- | --- | --- |
| `AffiliateProductState` | Regenerate or Preserve | Regenerate an empty/baseline-only table; preserve potential manual overrides |
| `Category`, `Product` | Discard unless inventory proves business use | The public catalogue renders from Python data; retain only if production has meaningful legacy records required by another workflow |
| `Click` | Optional history | Preserve only for a defined analytics, legal, or reporting need; it includes IP/user-agent data and needs `Product` rows first |
| `ProductAuditRun`, `ProductAuditIssue` | Optional history | Preserve only if audit history is operationally needed; import runs before issues |
| `auth.User`, `auth.Group` | Preserve selectively | Preserve only accounts and groups needed to administer the new service; handle export as sensitive data |
| `admin.LogEntry` | Discard / optional history | Do not migrate by default because it depends on users and content types |
| `sessions.Session` | Discard | Users can sign in again after the cutover |
| `django_migrations`, `contenttypes`, generated permissions | Regenerate | Django migration process creates the appropriate new PostgreSQL state |

## D. AffiliateProductState decision tree

```text
Production count = 0
  -> Do not export state rows.
  -> After PostgreSQL migrations, run the sync once.
  -> Verify resulting count against the current catalogue slug count.

Production rows are all baseline-only
  -> Do not migrate the rows.
  -> After PostgreSQL migrations, run the sync once.
  -> Confirm no manual differences or non-null checked dates were omitted.

Production contains manual overrides
  -> Export only rows that differ from the current baseline, have a checked
     date, or use an orphaned slug.
  -> Import those rows into PostgreSQL before running sync.
  -> Run sync once; it creates only missing slugs and does not overwrite
     existing manual rows without --force.
  -> Verify preserved-row count, samples, and total state count.
```

## E. Consistent SQLite backup procedure

Run this only after the inventory has been reviewed and **before** changing any
Render database configuration. It uses Python's SQLite backup API, which creates
a consistent backup instead of copying a possibly active database file.

```bash
export SQLITE_BACKUP_PATH="/tmp/leefnatuurlijk-sqlite-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"

python manage.py shell <<'PY'
import hashlib
import os
import sqlite3
from pathlib import Path
from django.conf import settings
from django.db import connection

if connection.vendor != "sqlite":
    raise SystemExit("STOP: current database is not SQLite")

source = Path(settings.DATABASES["default"]["NAME"])
target = Path(os.environ["SQLITE_BACKUP_PATH"])
if not source.exists():
    raise SystemExit(f"STOP: SQLite source does not exist: {source}")
if target.exists():
    raise SystemExit(f"STOP: backup target already exists: {target}")

with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src, sqlite3.connect(target) as dst:
    src.backup(dst)

with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as check:
    print("integrity_check=", check.execute("PRAGMA integrity_check").fetchone()[0])
    print("tables=", [row[0] for row in check.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )])

digest = hashlib.sha256(target.read_bytes()).hexdigest()
print("backup_path=", target)
print("backup_size_bytes=", target.stat().st_size)
print("backup_sha256=", digest)
PY
```

**VERIFY**:

```text
integrity_check= ok
backup_size_bytes > 0
the expected tables are present
```

Do not continue if the SQLite integrity check fails or the backup cannot be
copied outside Render.

## F. External backup handling

Render documents that service filesystems are ephemeral by default. A backup
left only in `/tmp` is not a backup. For a paid Render web service with SSH
enabled, use the exact SSH/SCP hostname shown in the Render Dashboard and copy
the file to an encrypted local or organization-controlled backup location:

```bash
scp -s YOUR_SERVICE@ssh.YOUR_REGION.render.com:/tmp/leefnatuurlijk-sqlite-YYYYMMDDTHHMMSSZ.sqlite3 \
  /secure/local/backup/location/

sha256sum /secure/local/backup/location/leefnatuurlijk-sqlite-YYYYMMDDTHHMMSSZ.sqlite3
```

Compare the local checksum with the checksum printed in the Render Shell. Store
the backup using the organization's approved encrypted storage and retention
policy. Do not store it in a repository, issue tracker, or chat. If SSH/SCP is
not available, **STOP** and arrange an approved encrypted transfer method
before changing the service. Do not rely on a persistent disk that does not
already exist, and do not create one as part of the cutover.

## G. First PostgreSQL cutover runbook

1. **STOP — freeze deployment changes.** Confirm the exact current Render
   commit, service instance count, linked branch, and automatic-deploy behavior.
   Pause/disable automatic deploys for the window and do not merge or deploy
   unrelated changes.
2. **VERIFY — inventory SQLite.** Run sections A and B on the actual serving
   instance. Review model counts and the affiliate-state decision tree.
3. **STOP — external backup.** Run section E and complete the external transfer
   in section F. Verify integrity, size, and checksum.
4. **STOP — audit every production hook.** Capture the Render Build Command,
   Pre-Deploy Command, Start Command, deploy branch, and any custom scripts.
   Prove none invokes `scripts/post-merge.sh`, `manage.py migrate`, or another
   migration command from the current SQLite-only commit. Pin the exact Task
   #15-ready commit that will be deployed.
5. **STOP — resolve required-data preservation.** If inventory shows manual
   affiliate overrides, required users, or required audit history, do not
   promote PostgreSQL until a reviewed, tested importer can consume the
   externally verified backup. Section J defines this hard gate.
6. **CONTINUE — create Render PostgreSQL.** Create the database only after the
   inventory, external backup, hook audit, and data-preservation decision are
   signed off. Record its internal connection string in Render's secret
   configuration, never in source control.
7. **VERIFY — environment contract.** Configure the variables in section H.
   Confirm the active service still uses the known SQLite release until the
   controlled deployment begins.
8. **CONTINUE — set a one-time pre-deploy command.** For this first release,
   configure only `python manage.py migrate --noinput`. Render runs a
   pre-deploy command from the new Task #15-ready build before it is made live.
   Do not add affiliate-state sync to this command.
9. **CONTINUE — deploy the pinned Task #15-ready revision.** The pre-deploy
   migration must succeed before the new web release is accepted. If a
   preservation importer is required, it must have completed in a separate
   rehearsed release gate before public traffic is switched.
10. **VERIFY — PostgreSQL schema.** In a Shell from the new deployment, run the
    commands in section I and confirm `connection.vendor` is `postgresql`.
11. **CONTINUE — seed missing affiliate state.** Run the sync once, then execute
    the dynamic verification in section K.
12. **VERIFY — application and admin.** Complete every smoke check in section
    L and inspect Render logs for 500s.
13. **STOP / rollback if a gate fails.** Follow section M. Keep the SQLite
    backup until the cutover has been formally accepted.
14. **CONTINUE — remove the one-time pre-deploy command only after review.**
    Decide on durable migration automation using section N; do not make the
    sync command an automatic release step during the first cutover.

## H. Required Render variables

| Variable | Required value/source |
| --- | --- |
| `DJANGO_ENV` | Literal `production` |
| `DJANGO_DB_BACKEND` | Literal `postgres` |
| `DATABASE_URL` | Render PostgreSQL **internal** connection string, stored as a secret |
| `DEBUG` | Literal `False` |
| `SECRET_KEY` | Existing production secret; retain it, do not print or rotate during this cutover |
| `GA_MEASUREMENT_ID` | Existing value only if analytics is currently configured |

No other application environment variables are required by the current Python
code. `REPLIT_DEV_DOMAIN` is development-only and is not a production
requirement. Confirm in Render whether linking the database automatically
creates `DATABASE_URL` for this service; if it does not, add the internal URL
explicitly as a secret. Never use an external URL if an internal URL is
available.

## I. First-migration verification commands

Run these only from the newly deployed PostgreSQL-ready release, after the
one-time pre-deploy migration has succeeded:

```bash
python manage.py showmigrations

python manage.py shell <<'PY'
from django.conf import settings
from django.db import connection

print("vendor=", connection.vendor)
print("engine=", settings.DATABASES["default"]["ENGINE"])
if connection.vendor != "postgresql":
    raise SystemExit("STOP: service is not using PostgreSQL")
PY
```

Expected:

```text
vendor= postgresql
engine= django.db.backends.postgresql
all required migrations marked [X]
```

Do not run migrations from the old SQLite-only release after setting
PostgreSQL variables: that release does not contain Task #15's explicit
PostgreSQL settings and can still target SQLite. Do not trigger a deployment
until the hook audit in step 4 proves that no old build/deploy hook can run
`scripts/post-merge.sh` or another migration command.

## J. Scoped data import procedure

Only execute a data export/import after inventory establishes a preservation
need and the externally stored SQLite backup has been verified.

### Mandatory preservation gate

There is currently no repository command that imports a selected SQLite backup
into PostgreSQL. Therefore:

```text
No manual overrides / users / audit history to retain:
  The first cutover may continue with the migration-only pre-deploy gate.

Any manually maintained state, required user, or required audit history:
  STOP. Build and rehearse a dedicated importer against a disposable
  PostgreSQL database before configuring or promoting the production release.
```

The verified external SQLite backup is the authoritative import source. Do not
depend on the old Render filesystem remaining available after a deployment.

### AffiliateProductState

The future dedicated importer must extract only the rows selected by section D
from the **external verified SQLite backup** to a restricted JSON file,
preserving:

```text
slug, price, availability, price_last_checked
```

It must validate the source-backup checksum, record the selected row count and
slug sample, and import to PostgreSQL by `slug` with `update_or_create(slug=...)`
inside a transaction. It must then verify the imported-row count before public
traffic is switched. Do not use `--force` with the sync command; that would
overwrite manual values.

The importer must be run from a temporary controlled migration environment
using the Task #15-ready code and PostgreSQL connection, before the web release
is promoted. It must receive the restricted export from approved encrypted
external storage by a short-lived credential, not from source control or the
old service filesystem.

### Audit history

Treat audit history as optional. If approved for preservation, import in this
order:

```text
required users -> ProductAuditRun parents -> ProductAuditRun children ->
ProductAuditIssue
```

Preserve or map parent relationships and requested-user references. Do not
blindly preserve primary keys if they collide; a dedicated importer should map
old IDs to newly created IDs.

### Users and groups

Only migrate users if the inventory proves they are needed for administration.
Use a Django-native, encrypted export handled by an authorized operator. Such
an export contains password hashes and personal data, so do not print it, put
it in source control, or attach it to this runbook. Recreate generated
permissions through migrations instead of migrating `contenttypes` or
permission rows. Do not migrate sessions.

## K. Affiliate-state sync procedure

After any required manual overrides have been imported:

```bash
python manage.py sync_affiliate_product_states

python manage.py shell <<'PY'
from products.models import AffiliateProductState
from products.views import ALL_PRODUCTS_BY_SLUG

# Copy these two reviewed sets from the preservation-import manifest.
# Keep both empty for the regenerate-only and baseline-only paths.
approved_preserved_orphan_slugs = set()
approved_preserved_override_slugs = set()

catalogue_slugs = set(ALL_PRODUCTS_BY_SLUG)
actual_slugs = set(AffiliateProductState.objects.values_list("slug", flat=True))
expected_count = len(catalogue_slugs) + len(approved_preserved_orphan_slugs)
actual_count = len(actual_slugs)
missing_catalogue_slugs = catalogue_slugs - actual_slugs
unexpected_extra_slugs = (
    actual_slugs - catalogue_slugs - approved_preserved_orphan_slugs
)
missing_approved_override_slugs = approved_preserved_override_slugs - actual_slugs

print("catalogue_slug_count=", len(catalogue_slugs))
print("approved_preserved_orphan_count=", len(approved_preserved_orphan_slugs))
print("expected_affiliate_state_count=", expected_count)
print("actual_affiliate_state_count=", actual_count)
print("missing_catalogue_state_count=", len(missing_catalogue_slugs))
print("missing_catalogue_state_sample=", sorted(missing_catalogue_slugs)[:10])
print("unexpected_extra_state_count=", len(unexpected_extra_slugs))
print("unexpected_extra_state_sample=", sorted(unexpected_extra_slugs)[:10])
print("missing_approved_override_count=", len(missing_approved_override_slugs))

if missing_catalogue_slugs:
    raise SystemExit("STOP: not every current catalogue slug has a state row")
if unexpected_extra_slugs:
    raise SystemExit("STOP: unapproved non-catalogue state rows exist")
if missing_approved_override_slugs:
    raise SystemExit("STOP: an approved preserved override is missing")
if actual_count != expected_count:
    raise SystemExit("STOP: state count differs from the reviewed dynamic expectation")
PY
```

The expected count is calculated at cutover time. Do not use 138 or 140 as a
hard-coded production assertion. For regenerate-only and baseline-only paths,
both approved sets are empty and zero extra rows are allowed. For a
preservation path, only orphan slugs approved in the importer manifest may add
to the expected count; the same manifest defines the required override slug
set. Do not automatically delete a discrepancy—stop and review it.

## L. Smoke-test checklist

After the PostgreSQL release, verify all of the following:

```text
GET /                                             -> HTTP 200
GET /product/greenpan-barcelona-pro-hapjespan-28/ -> HTTP 200
GET /product/ninja-crispi-4-in-1/                 -> HTTP 200
GET /koekenpannen/                                -> HTTP 200
GET /vershoudcontainers/?uitvoering=3-delig       -> HTTP 200
```

Also verify:

- Product content and affiliate buttons render.
- Swatch and button variants work.
- A known preserved maintenance override renders correctly, if one exists.
- The public app works with the populated state table and has no Django 500s.
- Django admin loads and `AffiliateProductState` is accessible to an authorized
  administrator.
- `connection.vendor` reports `postgresql`.
- The state count and missing-slug check in section K succeed.
- Render application logs contain no database, migration, or missing-table
  errors.

## M. Rollback plan

| Failure point | Action |
| --- | --- |
| Inventory or external backup incomplete | **STOP.** Do not create/configure PostgreSQL or deploy. |
| Pre-deploy migration fails | Do not promote the new build. Keep the current SQLite release running; inspect the PostgreSQL error separately. |
| Hook audit is incomplete or an old hook can migrate SQLite | **STOP.** Disable or remove that hook from the cutover path and repeat the audit before changing Render variables. |
| Required-data importer is not rehearsed | **STOP.** Keep SQLite live. Do not promote PostgreSQL based on an assumption that the old filesystem will remain available. |
| New application does not start | Roll back the Render service to the known-good SQLite release and restore its previous SQLite configuration. Do not delete the PostgreSQL database or SQLite backup during diagnosis. |
| PostgreSQL starts but import is incorrect | Stop the cutover acceptance. Prefer correcting forward from the verified SQLite backup; do not rerun sync with `--force`. |
| Smoke test fails | Treat the cutover as incomplete. Restore the old service configuration/release if public service is impacted, then diagnose with PostgreSQL preserved for analysis. |
| Affiliate sync fails | The public catalogue can technically render from Python defaults when the migrated `AffiliateProductState` table is empty, but do not accept cutover until the schema, missing-state condition, and logs are understood. |

Do not reverse Django migrations as an automatic rollback action. The safer
first response is normally restoring the known-good service release and
configuration, then correcting the new PostgreSQL state forward.

## N. Future deployment automation recommendation

After the first successful cutover, a permanent Render pre-deploy command of:

```bash
python manage.py migrate --noinput
```

is appropriate because migrations must complete before the application serves a
new schema-dependent release.

Do **not** automatically add:

```bash
python manage.py sync_affiliate_product_states
```

to every deploy yet. The command is idempotent and preserves existing rows
unless `--force` is used, but automatic sync still introduces catalogue/data
coupling and a release failure mode. Keep it as an explicit maintenance action
until a separate operational decision covers catalogue additions, removed
slugs, override preservation, monitoring, and recovery on failure.

## O. Risks

| Severity | Risk | Mitigation |
| --- | --- | --- |
| Critical | Existing SQLite data is lost because no externally verified backup exists | Do not begin cutover without a verified, externally stored backup |
| Critical | SQLite differs across Render instances or an ephemeral SSH instance is inspected | Inventory the actual serving instance(s); stop on divergence |
| High | Old SQLite-only code or a post-merge hook runs a supposed PostgreSQL migration | Freeze auto deploys, audit all hooks, and migrate only from the pinned Task #15-ready build via one-time pre-deploy |
| High | Manual affiliate overrides are overwritten | Export/import differential rows before sync; never use sync `--force` |
| High | Deployment is promoted before schema verification | Require pre-deploy migration success, `showmigrations`, and `connection.vendor=postgresql` |
| Medium | Audit history or admin accounts are silently lost | Decide from inventory before cutover; export only approved data |
| Medium | Click history containing personal data is copied without a purpose | Preserve only with an explicit analytics/legal retention decision |
| Low | Count check becomes stale | Calculate expected state count from the live catalogue at cutover time |

## P. Go / no-go recommendation

**Current recommendation: NO-GO for the actual Render PostgreSQL cutover.**

The repository is ready, and local PostgreSQL compatibility has been proven.
However, the production SQLite inventory has not been run from this workspace,
and no externally verified production SQLite backup exists yet.

Proceed to the controlled cutover only after:

1. the Render Shell inventory has been captured and reviewed;
2. data classifications have been approved;
3. a consistent SQLite backup has passed integrity and checksum verification;
4. that backup has been stored outside Render; and
5. every Render hook has been audited and the exact Task #15-ready commit has
   been pinned; and
6. either no production data needs preservation or a dedicated importer has
   been rehearsed against disposable PostgreSQL; and
7. the deployment window and one-time pre-deploy migration gate have been
   explicitly approved.