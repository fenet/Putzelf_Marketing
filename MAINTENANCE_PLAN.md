# Maintenance and scalability plan

This is a staged plan for making feature updates safer while keeping the existing application usable. It is based on a source review; production traffic, hosting, and user counts have not yet been measured.

## Current state

- The Flask application still has a large `app.py` module with database models, shared business rules, and remaining feature routes. Leads, integrations, marketing, client sites, and scheduling routes have been extracted to separate modules.
- SQLAlchemy is used with SQLite by default. The repository contains a local `schedule.db`, which is ignored by Git and must be treated as operational data.
- Startup code creates tables and applies several SQLite-only `ALTER TABLE` additions. There is no formal migration history.
- The repository has backup/deployment scripts, but deployment notes are partly stale. `deploy.sh` hard-resets to `origin/main`; that behavior needs to be confirmed against the live hosting and branch policy before use.
- A `unittest` suite now covers key scheduling, invoice, lead, integration, and access rules. GitHub Actions runs it on pushes and pull requests.
- Leads, booking/availability APIs, crawler/AI assistant, client sites, scheduling, and employee portal have been extracted to `leads.py`, `integrations.py`, `marketing.py`, `clients.py`, `scheduling.py`, and `employee_portal.py`; employee and client profile records are managed through their respective database pages in `app.py`.
- `clients.html` links to an `admin_clients` endpoint that is not defined in the current `app.py` route map. The file's intended status needs confirmation before it is connected or retired.

## Recommended sequence

### 1. Establish a safe baseline

- Identify the production host, active Git branch, WSGI/server process, database URL, number of active users, and typical peak concurrent usage.
- Take and verify backups of the production database, `uploads/`, and `static/uploads/` before any schema or deployment change.
- Keep production secrets out of source control; confirm production does not use development defaults or Flask debug mode.
- Record core behavior for schedule creation/editing, employee clock-in/out and photo upload, and invoice generation/payment status.

**Done when:** a restorable backup is verified, production configuration is known, and the critical workflows have written expected outcomes.

### 2. Add a small safety net — started

- Create automated checks around high-impact business rules first: shift conflict detection, scheduled/actual hours, monthly invoice totals, and invoice numbering.
- Add Flask request-level checks for login boundaries, common route access, and employee shift ownership.
- Run checks against a temporary test database and temporary upload directory, never the live `schedule.db`.

**Progress:** shift conflict/travel checks, monthly invoice totals/idempotency, admin and employee login, access boundaries, employee shift ownership, isolated photo upload, shift completion, single and batch schedule edits, invoice status transitions, PDF generation, mocked SMTP email delivery, lead workflows, integration API-key enforcement, booking idempotency/conflicts, and availability results are covered with a temporary SQLite database and upload directory. Run them with `python -m unittest discover -s tests -v`.

**Remaining:** extend cases for less common validation and failure paths as updates require them. This test workflow is separate from deployment and does not publish or deploy the app.

### 3. Split the monolith incrementally

Move one bounded feature at a time. Leads, integrations, marketing, sites, and scheduling have been extracted as separate blueprints. A possible eventual package layout is:

```text
putzelf/
  __init__.py          # create_app and shared configuration
  extensions.py        # SQLAlchemy setup
  models/              # employee, site, shift, lead, invoice models
  employees/           # employee admin and employee portal
  scheduling/          # route module currently in scheduling.py
  clients/             # site/client records and contracts
  leads/               # lead pipeline (currently in leads.py)
  billing/             # invoices, email, PDF, income reports
  integrations/        # booking and availability API
  marketing/           # crawler and AI assistant
  templates/           # HTML templates currently embedded in app.py
  static/
```

Preserve existing URLs and behavior during extraction. Move templates alongside their feature, and keep shared calculations in small service modules rather than importing route modules into one another. Feature modules and templates have been drafted, but the active routes remain in `app.py`; app registration and duplicate-route removal need to be completed together. Billing routes and shared calculations remain there.

**Progress:** leads, integrations, marketing utilities, site/profile management, scheduling, and employee portal have independent blueprint modules. Lead, crawler, site, profile, schedule, login, and employee dashboard pages are external Jinja templates. Feature modules and some external templates exist, but route extraction is not yet integrated into the active application. Billing routes and shared calculations remain in the monolith.

**Done when:** each extracted area has a clear route/template/data boundary and the existing workflows still pass their checks.

### 4. Formalize schema changes

- Introduce a migration tool and capture the current schema as the initial baseline.
- Replace ad hoc startup column changes with versioned, reviewed migrations.
- Back up and rehearse each migration on a copy of production data before applying it live.

**Done when:** schema upgrades and rollback/recovery steps are documented and rehearsed.

### 5. Decide capacity from actual use

- Measure concurrent sessions, write rate, database lock errors, response times, and photo storage growth.
- SQLite may remain appropriate for modest use with light writes. If measured write contention or operational needs exceed that, move to PostgreSQL using a rehearsed data migration.
- For multiple application workers/instances, use shared persistent storage for uploads or object storage; local per-instance files will not be shared reliably.
- Use a production WSGI server, managed process restarts, HTTPS, and monitoring appropriate to the host.

**Done when:** capacity targets are agreed and measurements show the chosen database/storage/deployment can meet them.

## Suggested order for upcoming feature requests

1. Fix urgent user-visible workflow problems.
2. Add or update a focused automated check for the affected behavior.
3. Refactor only the boundaries needed for that change.
4. Review effects on employee, admin, reporting, and invoice flows.
5. Deploy after a fresh backup and a staging or copied-data check.

## Decisions needed from the project owner

- Which updates are most urgent, and what should each workflow do after the change?
- How many staff members use the system now, and what concurrent usage is expected?
- Where is the live app hosted, which branch is deployed, and what process serves Flask?
- Is `clients.html` still used, or is `/admin/profiles?tab=clients` the supported client screen?
