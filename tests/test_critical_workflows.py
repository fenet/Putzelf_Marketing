"""Regression checks for high-impact scheduling, billing, and access rules."""

from __future__ import annotations

import atexit
import io
import os
import tempfile
import unittest
from datetime import date, datetime, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


# Configure an isolated database before importing the application. The app reads
# its settings at import time and otherwise defaults to the real schedule.db.
_test_root = tempfile.TemporaryDirectory(prefix="putzelf-tests-")
_test_db = Path(_test_root.name) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db.as_posix()}"
os.environ["FLASK_SECRET_KEY"] = "test-only-secret"
os.environ["AUTH_USERNAME"] = "test-admin"
os.environ["AUTH_PASSWORD"] = "test-password"
os.environ["INTEGRATION_KEY"] = "test-integration-key"

import app as application  # noqa: E402


def _cleanup_test_database() -> None:
    application.SessionLocal.remove()
    application.engine.dispose()
    _test_root.cleanup()


atexit.register(_cleanup_test_database)


class CriticalWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        application.SessionLocal.remove()
        application.Base.metadata.drop_all(bind=application.engine)
        application.Base.metadata.create_all(bind=application.engine)
        application.app.config.update(TESTING=True)
        self.upload_dir = Path(_test_root.name) / f"uploads-{id(self)}"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        application.app.config["UPLOAD_FOLDER"] = str(self.upload_dir)
        self.db = application.SessionLocal()
        self.client = application.app.test_client()

    def tearDown(self) -> None:
        self.db.rollback()
        self.db.close()
        application.SessionLocal.remove()

    def make_employee(self, name: str = "Cleaner"):
        employee = application.Employee(name=name)
        self.db.add(employee)
        self.db.flush()
        return employee

    def make_api_employee(self, name: str = "API cleaner", code: str = "API-1"):
        employee = self.make_employee(name)
        employee.login_code = code
        employee.login_pin_hash = application.generate_password_hash("1234")
        self.db.flush()
        return employee

    @staticmethod
    def integration_headers():
        return {"X-INTEGRATION-KEY": "test-integration-key"}

    def make_site(self, name: str = "Office", rate: float = 100.0):
        site = application.Site(name=name, address="Main Street", hourly_rate=rate)
        self.db.add(site)
        self.db.flush()
        return site

    def make_shift(
        self,
        employee_id: int,
        site_id: int,
        day: date,
        start: time,
        end: time,
        **kwargs,
    ):
        shift = application.Shift(
            employee_id=employee_id,
            site_id=site_id,
            day=day,
            start_time=start,
            end_time=end,
            **kwargs,
        )
        self.db.add(shift)
        self.db.flush()
        return shift

    def set_admin_session(self) -> None:
        with self.client.session_transaction() as session:
            session["auth"] = True
            session["role"] = "admin"

    def test_overlapping_shift_is_reported_as_conflict(self) -> None:
        employee = self.make_employee()
        site = self.make_site()
        other_site = self.make_site("Second office")
        day = date(2025, 5, 12)
        self.make_shift(employee.id, site.id, day, time(9), time(11))

        conflict = application._find_employee_schedule_conflict(
            self.db, employee.id, day, time(10, 30), time(12), other_site.id
        )

        self.assertIsNotNone(conflict)
        self.assertIn("Planungs-Konflikt", conflict)

    def test_different_sites_require_a_thirty_minute_travel_gap(self) -> None:
        employee = self.make_employee()
        first_site = self.make_site()
        second_site = self.make_site("Second office")
        day = date(2025, 5, 12)
        self.make_shift(employee.id, first_site.id, day, time(9), time(10))

        too_short = application._find_employee_schedule_conflict(
            self.db, employee.id, day, time(10, 20), time(11), second_site.id
        )
        enough_time = application._find_employee_schedule_conflict(
            self.db, employee.id, day, time(10, 30), time(11), second_site.id
        )

        self.assertIsNotNone(too_short)
        self.assertIn("mindestens 30 Minuten", too_short)
        self.assertIsNone(enough_time)

    def test_monthly_invoice_uses_actual_hours_and_is_idempotent(self) -> None:
        employee = self.make_employee()
        site = self.make_site(rate=100.0)
        self.make_shift(
            employee.id,
            site.id,
            date(2024, 2, 5),
            time(9),
            time(12),
            clock_in_at=datetime(2024, 2, 5, 9),
            clock_out_at=datetime(2024, 2, 5, 11),
        )
        self.make_shift(
            employee.id, site.id, date(2024, 2, 6), time(9), time(12)
        )
        self.db.commit()

        result = application._auto_generate_monthly_invoices(
            self.db, billing_month="2024-02", tax_rate_percent=20, days_until_due=30
        )
        invoice = self.db.query(application.Invoice).one()
        second_result = application._auto_generate_monthly_invoices(
            self.db, billing_month="2024-02", tax_rate_percent=20, days_until_due=30
        )

        self.assertEqual(result["created"], 1)
        self.assertEqual(invoice.total_hours, 5.0)
        self.assertEqual(invoice.subtotal, 500.0)
        self.assertEqual(invoice.tax_amount, 100.0)
        self.assertEqual(invoice.total_amount, 600.0)
        self.assertEqual(second_result["created"], 0)
        self.assertEqual(second_result["skipped_existing"], 1)
        self.assertEqual(self.db.query(application.Invoice).count(), 1)

    def test_admin_route_requires_admin_session(self) -> None:
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_employee_session_cannot_open_admin_route(self) -> None:
        employee = self.make_employee()
        employee_id = employee.id
        self.db.commit()
        with self.client.session_transaction() as session:
            session["role"] = "employee"
            session["employee_id"] = employee_id

        response = self.client.get("/admin/employees")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_employee_cannot_clock_in_for_another_employee(self) -> None:
        owner = self.make_employee("Shift owner")
        other_employee = self.make_employee("Other cleaner")
        site = self.make_site()
        shift = self.make_shift(
            other_employee.id,
            site.id,
            date.today(),
            time(9),
            time(10),
        )
        owner_id = owner.id
        self.db.commit()
        shift_id = shift.id
        with self.client.session_transaction() as session:
            session["role"] = "employee"
            session["employee_id"] = owner_id

        response = self.client.post(f"/employee/shifts/{shift_id}/clock-in")
        stored_shift = self.db.get(application.Shift, shift_id)

        self.assertEqual(response.status_code, 302)
        self.assertIsNone(stored_shift.clock_in_at)

    def test_admin_login_sets_admin_session(self) -> None:
        response = self.client.post(
            "/login", data={"username": "test-admin", "password": "test-password"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin", response.headers["Location"])
        with self.client.session_transaction() as session:
            self.assertTrue(session.get("auth"))
            self.assertEqual(session.get("role"), "admin")

    def test_login_page_renders_extracted_template(self) -> None:
        response = self.client.get("/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign in", response.data)

    def test_employee_login_with_code_and_pin_sets_employee_session(self) -> None:
        employee = self.make_employee("Login cleaner")
        employee.login_code = "CLEAN1"
        employee.login_pin_hash = application.generate_password_hash("1234")
        employee_id = employee.id
        self.db.commit()

        response = self.client.post(
            "/login", data={"username": "CLEAN1", "password": "1234"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/employee", response.headers["Location"])
        with self.client.session_transaction() as session:
            self.assertEqual(session.get("role"), "employee")
            self.assertEqual(session.get("employee_id"), employee_id)

    def test_employee_dashboard_renders_extracted_template(self) -> None:
        employee = self.make_employee("Dashboard cleaner")
        site = self.make_site("Dashboard site")
        self.make_shift(employee.id, site.id, date.today(), time(9), time(10))
        employee_id = employee.id
        self.db.commit()
        with self.client.session_transaction() as session:
            session["role"] = "employee"
            session["employee_id"] = employee_id
            session["employee_name"] = "Dashboard cleaner"

        response = self.client.get("/employee/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Crew dashboard".encode("utf-8"), response.data)

    def test_employee_can_upload_shift_photo_to_test_storage(self) -> None:
        employee = self.make_employee("Photo cleaner")
        site = self.make_site()
        shift = self.make_shift(
            employee.id, site.id, date.today(), time(9), time(10)
        )
        employee_id = employee.id
        shift_id = shift.id
        self.db.commit()
        with self.client.session_transaction() as session:
            session["role"] = "employee"
            session["employee_id"] = employee_id

        response = self.client.post(
            f"/employee/shifts/{shift_id}/upload",
            data={"photo_type": "before", "photo": (io.BytesIO(b"photo"), "proof.jpg")},
            content_type="multipart/form-data",
        )
        self.db.expire_all()
        stored_shift = self.db.get(application.Shift, shift_id)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(stored_shift.before_photo_path.startswith("uploads/proofs/"))
        relative_file = Path(*stored_shift.before_photo_path.split("/")[1:])
        self.assertTrue((self.upload_dir / relative_file).is_file())

    def test_employee_can_complete_todays_shift_with_location(self) -> None:
        employee = self.make_employee("Completion cleaner")
        site = self.make_site()
        shift = self.make_shift(
            employee.id, site.id, date.today(), time(9), time(10)
        )
        employee_id = employee.id
        shift_id = shift.id
        self.db.commit()
        with self.client.session_transaction() as session:
            session["role"] = "employee"
            session["employee_id"] = employee_id

        response = self.client.post(
            f"/employee/shifts/{shift_id}/complete",
            data={"lat": "48.2082", "lng": "16.3738"},
        )
        self.db.expire_all()
        completed_shift = self.db.get(application.Shift, shift_id)

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(completed_shift.clock_in_at)
        self.assertIsNotNone(completed_shift.clock_out_at)
        self.assertEqual(completed_shift.clock_out_lat, 48.2082)
        self.assertEqual(completed_shift.clock_out_lng, 16.3738)

    def test_admin_can_edit_schedule_shift(self) -> None:
        employee = self.make_employee()
        site = self.make_site()
        shift = self.make_shift(
            employee.id, site.id, date(2025, 5, 12), time(9), time(10)
        )
        shift_id = shift.id
        employee_id = employee.id
        self.db.commit()
        self.set_admin_session()

        response = self.client.post(
            f"/shift/{shift_id}/edit",
            data={
                "employee_id": str(employee_id),
                "day": "2025-05-13",
                "start_time": "10:30",
                "end_time": "12:00",
                "instructions": "Use side entrance",
            },
        )
        self.db.expire_all()
        updated_shift = self.db.get(application.Shift, shift_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(updated_shift.day, date(2025, 5, 13))
        self.assertEqual(updated_shift.start_time, time(10, 30))
        self.assertEqual(updated_shift.end_time, time(12))
        self.assertEqual(updated_shift.instructions, "Use side entrance")

    def test_schedule_dashboard_renders_extracted_template(self) -> None:
        self.set_admin_session()

        response = self.client.get(
            "/schedule", query_string={"start_date": "2025-05-12", "days": "7"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Mitarbeiterplan".encode("utf-8"), response.data)

    def test_schedule_pdf_route_returns_pdf(self) -> None:
        if not application.REPORTLAB_AVAILABLE:
            self.skipTest("reportlab is not installed")
        employee = self.make_employee("PDF cleaner")
        site = self.make_site("PDF schedule site")
        self.make_shift(
            employee.id, site.id, date(2025, 5, 12), time(9), time(11)
        )
        self.db.commit()
        self.set_admin_session()

        response = self.client.get("/schedule/pdf?week=2025-05-12")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF"))

    def test_batch_schedule_creates_non_conflicting_shifts(self) -> None:
        first_employee = self.make_employee("First cleaner")
        second_employee = self.make_employee("Second cleaner")
        site = self.make_site()
        first_id = first_employee.id
        second_id = second_employee.id
        site_id = site.id
        first_day = date(2025, 5, 12)
        second_day = date(2025, 5, 13)
        self.make_shift(
            first_id, site_id, first_day, time(9), time(10)
        )
        self.db.commit()
        self.set_admin_session()

        response = self.client.post(
            "/schedule",
            data={
                "employee_id": [str(first_id), str(second_id)],
                "site_id": str(site_id),
                "day": [first_day.isoformat(), second_day.isoformat()],
                "start_time": "09:00",
                "duration_hours": "2",
                "instructions": "Bring supplies",
            },
        )
        created = (
            self.db.query(application.Shift)
            .filter(
                application.Shift.employee_id.in_([first_id, second_id]),
                application.Shift.day.in_([first_day, second_day]),
            )
            .all()
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(created), 4)  # One existing plus three new shifts.
        new_shifts = [shift for shift in created if shift.day != first_day or shift.employee_id != first_id]
        self.assertEqual(len(new_shifts), 3)
        self.assertTrue(all(shift.instructions == "Bring supplies" for shift in new_shifts))

    def test_invoice_status_updates_paid_at_and_clears_it_when_reopened(self) -> None:
        site = self.make_site()
        invoice = application.Invoice(
            invoice_number="RE-1000",
            site_id=site.id,
            hourly_rate=100.0,
            total_hours=2.0,
            subtotal=200.0,
            tax_rate=0.2,
            tax_amount=40.0,
            total_amount=240.0,
            status="draft",
        )
        self.db.add(invoice)
        self.db.flush()
        invoice_id = invoice.id
        self.db.commit()
        self.set_admin_session()

        paid_response = self.client.post(
            f"/admin/invoices/{invoice_id}/status", data={"status": "paid"}
        )
        self.db.expire_all()
        paid_invoice = self.db.get(application.Invoice, invoice_id)
        paid_at = paid_invoice.paid_at
        paid_status = paid_invoice.status
        sent_response = self.client.post(
            f"/admin/invoices/{invoice_id}/status", data={"status": "sent"}
        )
        self.db.expire_all()
        sent_invoice = self.db.get(application.Invoice, invoice_id)

        self.assertEqual(paid_response.status_code, 302)
        self.assertEqual(paid_status, "paid")
        self.assertIsNotNone(paid_at)
        self.assertEqual(sent_response.status_code, 302)
        self.assertEqual(sent_invoice.status, "sent")
        self.assertIsNone(sent_invoice.paid_at)

    def test_invoice_pdf_route_returns_pdf(self) -> None:
        if not application.REPORTLAB_AVAILABLE:
            self.skipTest("reportlab is not installed")
        site = self.make_site("PDF customer")
        invoice = application.Invoice(
            invoice_number="RE-1000",
            site_id=site.id,
            site_company_name="PDF customer GmbH",
            site_contact_email="billing@example.com",
            site_billing_address="Main Street 1, Vienna",
            hourly_rate=100.0,
            total_hours=2.0,
            subtotal=200.0,
            tax_rate=0.2,
            tax_amount=40.0,
            total_amount=240.0,
            status="draft",
        )
        self.db.add(invoice)
        self.db.flush()
        invoice_id = invoice.id
        self.db.commit()
        self.set_admin_session()

        response = self.client.get(f"/admin/invoices/{invoice_id}/pdf")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF"))

    def test_invoice_email_uses_mock_smtp_and_attaches_pdf(self) -> None:
        site = self.make_site("Email customer")
        invoice = application.Invoice(
            invoice_number="RE-1001",
            site_id=site.id,
            site_company_name="Email customer GmbH",
            site_contact_name="Billing Contact",
            site_contact_email="billing@example.com",
            hourly_rate=100.0,
            total_hours=2.0,
            subtotal=200.0,
            tax_rate=0.2,
            tax_amount=40.0,
            total_amount=240.0,
            status="draft",
        )
        self.db.add(invoice)
        self.db.flush()
        invoice.site = site
        pdf_buffer = io.BytesIO(b"%PDF-test-content")

        with patch.dict(
            os.environ,
            {
                "SMTP_SERVER": "smtp.example.test",
                "SMTP_PORT": "587",
                "SMTP_USE_TLS": "true",
                "SMTP_USE_SSL": "false",
                "SMTP_SECURE": "",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "test-password",
                "SENDER_EMAIL": "sender@example.com",
                "SENDER_NAME": "Test Sender",
            },
        ), patch("smtplib.SMTP") as smtp_class:
            success, detail = application.send_invoice_email(invoice, pdf_buffer)

        smtp_class.assert_called_once_with("smtp.example.test", 587)
        smtp_server = smtp_class.return_value
        smtp_server.starttls.assert_called_once()
        smtp_server.login.assert_called_once_with("sender@example.com", "test-password")
        smtp_server.send_message.assert_called_once()
        sent_message = smtp_server.send_message.call_args.args[0]
        attachment_parts = [part for part in sent_message.walk() if part.get_filename()]

        self.assertTrue(success, detail)
        self.assertIn("billing@example.com", sent_message["To"])
        self.assertEqual(len(attachment_parts), 1)
        self.assertIn("invoice_RE-1001.pdf", attachment_parts[0].get_filename())

    def test_lead_dashboard_requires_admin_session(self) -> None:
        response = self.client.get("/leads")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_lead_dashboard_renders_extracted_template(self) -> None:
        self.set_admin_session()

        response = self.client.get("/leads")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lead-Center", response.data)

    def test_lead_creation_and_stage_update(self) -> None:
        self.set_admin_session()

        create_response = self.client.post(
            "/leads",
            data={
                "action": "create",
                "name": "New customer",
                "email": "customer@example.com",
                "stage": "Qualified",
            },
        )
        lead = self.db.query(application.Lead).one()
        stage_response = self.client.post(
            "/leads/stage",
            json={"id": lead.id, "stage": "Contacted"},
        )
        self.db.refresh(lead)

        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(create_response.headers["Location"], "/leads")
        self.assertEqual(stage_response.status_code, 200)
        self.assertEqual(lead.stage, "Contacted")

    def test_lead_stage_rejects_unknown_stage(self) -> None:
        self.set_admin_session()

        response = self.client.post(
            "/leads/stage", json={"id": 1, "stage": "Not a stage"}
        )

        self.assertEqual(response.status_code, 400)

    def test_integration_employee_list_requires_key_and_returns_employees(self) -> None:
        employee = self.make_api_employee("API cleaner", "API-1")
        employee_id = employee.id
        self.db.commit()

        unauthorized = self.client.get("/api/integrations/employees")
        authorized = self.client.get(
            "/api/integrations/employees", headers=self.integration_headers()
        )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(authorized.status_code, 200)
        payload = authorized.get_json()["employees"]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["code"], "API-1")
        self.assertEqual(payload[0]["name"], "API cleaner")
        self.assertTrue(payload[0]["active"])

    def test_booking_integration_is_idempotent_and_rejects_conflict(self) -> None:
        employee = self.make_api_employee()
        employee_id = employee.id
        self.db.commit()
        booking = {
            "booking_id": "B-100",
            "employee_code": "API-1",
            "day": "2025-05-12",
            "start_time": "09:00",
            "duration_hours": 2,
            "address": "Main Street 1",
            "instructions": "Website booking #B-100",
        }

        created_response = self.client.post(
            "/api/integrations/shifts/from-booking",
            json=booking,
            headers=self.integration_headers(),
        )
        created_id = created_response.get_json()["shiftId"]
        repeated_response = self.client.post(
            "/api/integrations/shifts/from-booking",
            json=booking,
            headers=self.integration_headers(),
        )
        conflict_response = self.client.post(
            "/api/integrations/shifts/from-booking",
            json={**booking, "booking_id": "B-101", "instructions": "Second booking"},
            headers=self.integration_headers(),
        )
        self.db.expire_all()
        stored_shift = self.db.get(application.Shift, created_id)

        self.assertEqual(created_response.status_code, 201)
        self.assertEqual(repeated_response.status_code, 200)
        self.assertEqual(repeated_response.get_json()["shiftId"], created_id)
        self.assertEqual(conflict_response.status_code, 409)
        self.assertEqual(stored_shift.employee_id, employee_id)
        self.assertIn("Address: Main Street 1", stored_shift.instructions)
        self.assertEqual(self.db.query(application.Shift).count(), 1)

    def test_availability_slots_exclude_booked_intervals(self) -> None:
        employee = self.make_api_employee()
        site = self.make_site()
        self.make_shift(
            employee.id, site.id, date(2025, 5, 12), time(9), time(10)
        )
        self.db.commit()

        response = self.client.get(
            "/api/integrations/availability/slots",
            query_string={
                "employee_code": "API-1",
                "day": "2025-05-12",
                "duration_hours": "1",
            },
            headers=self.integration_headers(),
        )
        slots = response.get_json()["slots"]

        self.assertEqual(response.status_code, 200)
        self.assertIn("08:00", slots)
        self.assertNotIn("09:00", slots)
        self.assertIn("10:00", slots)

    def test_month_availability_excludes_fully_booked_day(self) -> None:
        employee = self.make_api_employee()
        site = self.make_site()
        self.make_shift(
            employee.id, site.id, date(2025, 5, 1), time(8), time(18)
        )
        self.db.commit()

        response = self.client.get(
            "/api/integrations/availability/month",
            query_string={
                "employee_code": "API-1",
                "month": "2025-05",
                "duration_hours": "10",
            },
            headers=self.integration_headers(),
        )
        available_days = response.get_json()["availableDays"]

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("2025-05-01", available_days)
        self.assertIn("2025-05-02", available_days)

    def test_crawler_page_renders_and_requires_admin(self) -> None:
        denied = self.client.get("/crawler")
        self.set_admin_session()
        allowed = self.client.get("/crawler")

        self.assertEqual(denied.status_code, 302)
        self.assertIn("/login", denied.headers["Location"])
        self.assertEqual(allowed.status_code, 200)
        self.assertIn(b"URL Contact Crawler", allowed.data)

    def test_crawler_post_uses_same_domain_fetch_and_returns_pdf(self) -> None:
        if not application.REPORTLAB_AVAILABLE:
            self.skipTest("reportlab is not installed")
        self.set_admin_session()
        html = """<!doctype html><html><head><title>Acme Cleaning</title></head>
        <body><h1>Acme Cleaning</h1><a href="mailto:hello@acme.test">Email us</a>
        <a href="https://external.example/contact">External</a></body></html>"""

        with patch.object(application, "fetch_html", return_value=(html, 200)) as fetch_mock:
            response = self.client.post(
                "/crawler",
                data={"start_url": "https://acme.test/", "max_pages": "1"},
            )

        fetch_mock.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF"))

    def test_gpt_route_is_admin_protected_and_never_calls_live_service_in_test(self) -> None:
        denied = self.client.post("/gpt", json={"prompt": "Draft a message"})
        self.set_admin_session()

        if application.openai_client is None:
            response = self.client.post("/gpt", json={"prompt": "Draft a message"})
            self.assertEqual(response.status_code, 503)
        else:
            fake_completion = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Draft response"))]
            )
            with patch.object(
                application.openai_client.chat.completions,
                "create",
                return_value=fake_completion,
            ) as create_mock:
                response = self.client.post("/gpt", json={"prompt": "Draft a message"})
            create_mock.assert_called_once()
            self.assertEqual(response.get_json()["reply"], "Draft response")

        self.assertEqual(denied.status_code, 302)
        self.assertIn("/login", denied.headers["Location"])

    def test_site_management_requires_admin_and_renders_template(self) -> None:
        denied = self.client.get("/admin/sites")
        self.set_admin_session()
        allowed = self.client.get("/admin/sites")

        self.assertEqual(denied.status_code, 302)
        self.assertIn("/login", denied.headers["Location"])
        self.assertEqual(allowed.status_code, 200)
        self.assertIn(b"Standort", allowed.data)

    def test_site_create_rejects_duplicate_and_update_persists_changes(self) -> None:
        self.set_admin_session()
        create_data = {
            "entity": "site",
            "action": "create",
            "name": "Main Office",
            "address": "Main Street 1",
            "hourly_rate": "75.5",
            "is_active": "1",
        }

        created_response = self.client.post("/admin/sites", data=create_data)
        site = self.db.query(application.Site).one()
        site_id = site.id
        duplicate_response = self.client.post(
            "/admin/sites",
            data={**create_data, "name": "main office", "address": "main street 1"},
        )
        self.db.expire_all()
        stored_site = self.db.get(application.Site, site_id)
        update_response = self.client.post(
            "/admin/sites",
            data={
                "entity": "site",
                "action": "update",
                "id": str(site_id),
                "name": "Main Office Updated",
                "address": "Main Street 2",
                "hourly_rate": "80",
                "is_active": "0",
            },
        )
        self.db.expire_all()
        stored_site = self.db.get(application.Site, site_id)

        self.assertEqual(created_response.status_code, 302)
        self.assertEqual(duplicate_response.status_code, 302)
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(self.db.query(application.Site).count(), 1)
        self.assertEqual(stored_site.name, "Main Office Updated")
        self.assertEqual(stored_site.address, "Main Street 2")
        self.assertEqual(stored_site.hourly_rate, 80.0)
        self.assertFalse(stored_site.is_active)

    def test_legacy_profiles_urls_redirect_to_current_databases(self) -> None:
        self.set_admin_session()

        employee_response = self.client.get("/admin/profiles?tab=employees")
        client_response = self.client.get("/admin/profiles?tab=clients")

        self.assertEqual(employee_response.status_code, 302)
        self.assertEqual(client_response.status_code, 302)
        self.assertIn("/admin/employees", employee_response.headers["Location"])
        self.assertIn("/admin/sites", client_response.headers["Location"])

    def test_employee_profile_update_persists_profile_fields(self) -> None:
        employee = self.make_employee("Profile cleaner")
        employee_id = employee.id
        self.db.commit()
        self.set_admin_session()

        response = self.client.post(
            "/admin/employees",
            data={
                "action": "update",
                "id": str(employee_id),
                "name": "Profile cleaner",
                "profile_phone": "+43 660 1234567",
                "profile_address": "Worker Street 4",
                "profile_zip_code": "1100",
                "profile_city": "Vienna",
                "profile_employment_type": "Reinigungskraft",
                "profile_work_type": "Vollzeit",
                "profile_group_type": "Lohngruppe",
                "profile_group_number": "2",
            },
        )
        self.db.expire_all()
        stored_employee = self.db.get(application.Employee, employee_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(stored_employee.profile_phone, "+43 660 1234567")
        self.assertEqual(stored_employee.profile_address, "Worker Street 4")
        self.assertEqual(stored_employee.profile_city, "Vienna")
        self.assertEqual(stored_employee.profile_work_type, "Vollzeit")
        self.assertEqual(stored_employee.profile_group_number, "2")

    def test_client_profile_update_generates_customer_id_and_saves_contract_details(self) -> None:
        site = self.make_site("Profile client")
        site_id = site.id
        self.db.commit()
        self.set_admin_session()

        response = self.client.post(
            "/admin/sites",
            data={
                "entity": "site",
                "action": "update",
                "id": str(site_id),
                "name": "Profile client",
                "address": "Main Street",
                "profile_company_name": "Profile Client GmbH",
                "profile_contact_name": "Alex Contact",
                "profile_contact_email": "alex@example.com",
                "profile_default_hourly_rate": "87.5",
                "contract_partner_name": "Putzelf Marketing",
                "contract_contact_details": "alex@example.com, +43 123 456789",
                "contract_start_date": "2025-02-01",
                "contract_end_date": "2025-12-31",
            },
        )
        self.db.expire_all()
        stored_site = self.db.get(application.Site, site_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(stored_site.profile_company_name, "Profile Client GmbH")
        self.assertEqual(stored_site.profile_contact_name, "Alex Contact")
        self.assertEqual(stored_site.profile_default_hourly_rate, 87.5)
        self.assertRegex(stored_site.profile_tax_id or "", r"^UT- \d{4}$")
        self.assertEqual(stored_site.contract_start_date, "01-02-2025")
        self.assertEqual(stored_site.contract_end_date, "31-12-2025")


if __name__ == "__main__":
    unittest.main()
