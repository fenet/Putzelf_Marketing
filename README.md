# Elf's Plan

A Flask application for managing cleaning staff, client sites, shifts, work completion, leads, contracts, invoices, and business reports. The app currently uses SQLAlchemy with SQLite by default. Core models and shared business logic remain in `app.py`; feature code and templates are being extracted incrementally.

## Run locally

Requires Python 3.8 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a unique `FLASK_SECRET_KEY`, `AUTH_USERNAME`, and `AUTH_PASSWORD`. Then start the development server:

```powershell
python app.py
```

Open `http://127.0.0.1:5000`. The built-in Flask server is for local development; use a production WSGI server and deployment-specific configuration for a live service. Never use the example credentials or `FLASK_SECRET_KEY` in production.

## Features

- **Admin and employee access:** admin login, employee login codes/PINs, employee dashboard, and language selection.
- **Scheduling:** create, edit, move, batch-edit, and delete shifts; view schedules and PDFs; check availability; import the prior month's schedule.
- **Employee shift workflow:** clock in/out with optional location, upload before/after photos, and complete assigned shifts.
- **Employees and clients:** employee records, active status, profile and contract details, generated employee documents, client sites, contacts, billing details, and profile images.
- **Leads:** confirmed website bookings create or update a lead automatically; Admins, Site Managers, and Sales Managers can manually add leads and move them between New Leads, Contacted, and Converted.
- **Invoices and finance:** create/edit invoices, generate monthly invoices from recorded shift hours, update payment status, email invoices, export PDFs, and view income/hours reports.
- **Integrations:** API endpoints to list employees, create shifts from bookings, and query availability. Integration endpoints require `INTEGRATION_KEY`.

The booking endpoint is `POST /api/integrations/shifts/from-booking`. In addition to its scheduling fields (`booking_id`, `employee_code`, `day`, `start_time`, `duration_hours`, `address`, and `instructions`), it accepts optional `customer_name`, `customer_email`, and `customer_phone` fields for the lead record. It returns `leadId` alongside `shiftId`; repeated requests with the same booking ID reuse the lead and shift. Overlapping shifts are saved, and the response includes `conflict`, `conflictingShiftIds`, and a `notification` message when the website should warn the user to review the schedule.
- **Marketing utilities:** a website contact crawler and an OpenAI-powered text assistant.
- **Installable web app assets:** separate employee/admin manifests and service worker files.

Feature module files and external templates are present, but `app.py` remains the active application entry point and still contains the main route implementations. Billing routes and shared calculations remain there.

## Configuration

Copy `.env.example` to `.env`. The app reads these settings:

| Variable | Purpose |
| --- | --- |
| `FLASK_SECRET_KEY` | Flask session signing key. Set a long random value. |
| `AUTH_USERNAME`, `AUTH_PASSWORD` | Admin credentials. |
| `DATABASE_URL` | SQLAlchemy URL; defaults to `sqlite:///schedule.db` in the project directory. |
| `INTEGRATION_KEY` | Shared key required by integration API requests. |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | Optional AI assistant configuration. |
| `CRAWLER_DEFAULT_REGION` | Default region used by crawler phone-number parsing. |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USE_TLS`, `SMTP_USE_SSL`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SENDER_EMAIL`, `SENDER_NAME` | SMTP connection and invoice email configuration. |
| `EMPLOYEE_CREDENTIALS_FROM_EMAIL`, `EMPLOYEE_CREDENTIALS_FROM_NAME` | Sender shown on employee sign-in emails. Defaults to `office@putzelf.com` and `Elf's Plan`; the SMTP account must be allowed to send from this address. |

The app allows uploads up to 16 MB. Employee/client images and shift photos are stored under `static/uploads/`; document templates are under `uploads/`.

## Data and deployment

- `schedule.db` is the default SQLite database and is intentionally ignored by Git.
- `uploads/` contains operational files and is intentionally excluded from Git apart from its placeholder file. Back up both uploads and generated files under `static/uploads/` before deployment.
- `.env` contains credentials and must remain private.
- `backup.sh` creates local timestamped backups. `deploy.sh` currently performs a hard reset to `origin/main` and reinstalls dependencies; review its target branch and backup/restore behavior before using it on a live server.
- `DEPLOYMENT.md` contains the existing server notes. It includes older instructions and should be reconciled with the actual production hosting setup.

## Current architecture and limitations

- `app.py` remains a large module containing SQLAlchemy models, shared business logic, and the active feature routes. Separate feature modules and templates are present, but their integration with the app entry point is incomplete. Billing routes and shared calculations remain in `app.py`.
- SQLite is the local default. It is convenient for a single small installation, but write contention and operational constraints should be evaluated against real concurrent usage before scaling.
- A small `unittest` regression suite now covers core scheduling, billing, lead, and access behavior. There is not yet a migration framework; schema evolution is handled partly through startup-time SQLite column additions.
- GitHub Actions runs the regression suite on pushes and pull requests; it does not deploy the application.
- `clients.html` and `detail_requests.html` are standalone HTML files; they are not standard Flask templates in a `templates/` directory. Confirm their intended use before integrating or removing them.
- The README previously described only the contact crawler and was not an accurate description of the application.

See [MAINTENANCE_PLAN.md](MAINTENANCE_PLAN.md) for a staged plan to improve structure and prepare the app for safe updates and higher concurrency.
