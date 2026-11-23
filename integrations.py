"""Booking and availability API routes, extracted from the legacy app module."""

from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import func


def _parse_employee_code(raw: str | None) -> str:
    return (raw or "").strip()


def _parse_day_ymd(raw: str | None) -> date | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_month_ym(raw: str | None) -> tuple[int, int] | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m")
        return parsed.year, parsed.month
    except ValueError:
        return None


def _parse_duration_hours(raw: str | None) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        hours = float(value)
    except ValueError:
        return None
    if hours <= 0:
        return None
    return int(math.ceil(hours * 60 / 30) * 30)


def _time_to_minutes(value: time) -> int:
    return int(value.hour) * 60 + int(value.minute)


def _minutes_to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and a_end > b_start


def _generate_slots_for_day(
    blocked: list[tuple[int, int]], duration_minutes: int
) -> list[str]:
    work_start = 8 * 60
    work_end = 18 * 60
    latest_start = work_end - duration_minutes
    if latest_start < work_start:
        return []

    slots: list[str] = []
    start = work_start
    while start <= latest_start:
        end = start + duration_minutes
        if not any(_intervals_overlap(start, end, b_start, b_end) for b_start, b_end in blocked):
            slots.append(_minutes_to_hhmm(start))
        start += 30
    return slots


def _parse_time_hhmm(raw: str | None) -> time | None:
    value = (raw or "").strip()
    if not value:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def _ensure_default_website_site(db, Site, address: str | None = None):
    name = "Website bookings"
    site = db.query(Site).filter(func.lower(Site.name) == name.lower()).first()
    if site:
        return site
    site = Site(name=name, address=(address or "").strip() or None, hourly_rate=0.0, is_active=True)
    db.add(site)
    db.commit()
    return site


def create_integrations_blueprint(
    *,
    session_factory,
    Employee,
    Shift,
    Site,
    integration_key: str,
    generate_missing_credentials,
):
    """Build API routes with the legacy application's configured dependencies."""
    blueprint = Blueprint("integrations", __name__, url_prefix="/api/integrations")

    def require_integration_key():
        if not integration_key:
            return False, ("Integration key not configured", 503)
        provided = (request.headers.get("X-INTEGRATION-KEY") or "").strip()
        if not provided or provided != integration_key:
            return False, ("Invalid integration key", 401)
        return True, None

    @blueprint.get("/employees")
    def employees():
        ok, error = require_integration_key()
        if not ok:
            message, status = error
            return jsonify({"error": message}), status

        db = session_factory()
        try:
            generate_missing_credentials(db)
            records = db.query(Employee).order_by(Employee.name.asc()).all()
            payload = []
            for employee in records:
                code = (employee.login_code or "").strip() or str(employee.id)
                name = (employee.name or code).strip()
                image_url = None
                try:
                    if employee.profile_image_path:
                        image_url = url_for("static", filename=employee.profile_image_path, _external=True)
                except Exception:
                    image_url = None
                try:
                    active_flag = True if getattr(employee, "is_active", None) is None else bool(employee.is_active)
                except Exception:
                    active_flag = True
                payload.append(
                    {"code": code, "name": name, "active": active_flag, "image": image_url}
                )
            return jsonify({"employees": payload})
        finally:
            db.close()

    @blueprint.post("/shifts/from-booking")
    def shift_from_booking():
        ok, error = require_integration_key()
        if not ok:
            message, status = error
            return jsonify({"error": message}), status

        payload = request.get_json(silent=True) or {}
        booking_id = payload.get("booking_id")
        employee_code = _parse_employee_code(payload.get("employee_code"))
        day = _parse_day_ymd(payload.get("day"))
        start = _parse_time_hhmm(payload.get("start_time"))
        duration_raw = payload.get("duration_hours")
        duration_minutes = _parse_duration_hours(
            str(duration_raw) if duration_raw is not None else None
        )
        address = (payload.get("address") or "").strip()
        instructions = (payload.get("instructions") or "").strip()

        if not employee_code or day is None or start is None or duration_minutes is None:
            return jsonify({"error": "employee_code, day, start_time and duration_hours are required"}), 400

        start_min = _time_to_minutes(start)
        end_min = start_min + duration_minutes
        if end_min > 24 * 60:
            return jsonify({"error": "Invalid start_time/duration_hours"}), 400
        end_time = (datetime.combine(date.today(), start) + timedelta(minutes=duration_minutes)).time()

        db = session_factory()
        try:
            generate_missing_credentials(db)
            employee = (
                db.query(Employee)
                .filter(func.lower(Employee.login_code) == employee_code.lower())
                .first()
            )
            if not employee:
                return jsonify({"error": "Employee not found"}), 404

            if booking_id is not None:
                marker = f"Website booking #{booking_id}"
                existing = (
                    db.query(Shift)
                    .filter(Shift.employee_id == employee.id, Shift.day == day)
                    .filter(Shift.instructions.ilike(f"%{marker}%"))
                    .first()
                )
                if existing:
                    return jsonify({"shiftId": existing.id})

            shifts = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.day == day).all()
            for shift in shifts:
                try:
                    blocked_start = _time_to_minutes(shift.start_time)
                    blocked_end = _time_to_minutes(shift.end_time)
                except Exception:
                    continue
                if _intervals_overlap(start_min, end_min, blocked_start, blocked_end):
                    return jsonify({"error": "Slot no longer available"}), 409

            site = _ensure_default_website_site(db, Site, address=address)
            full_instructions = instructions
            if address and address.lower() not in full_instructions.lower():
                full_instructions = (full_instructions + f"\nAddress: {address}").strip()
            shift = Shift(
                employee_id=employee.id,
                site_id=site.id,
                day=day,
                start_time=start,
                end_time=end_time,
                instructions=full_instructions or None,
            )
            db.add(shift)
            db.commit()
            return jsonify({"shiftId": shift.id}), 201
        finally:
            db.close()

    @blueprint.get("/availability/slots")
    def availability_slots():
        ok, error = require_integration_key()
        if not ok:
            message, status = error
            return jsonify({"error": message}), status

        employee_code = _parse_employee_code(request.args.get("employee_code") or request.args.get("worker"))
        day = _parse_day_ymd(request.args.get("day") or request.args.get("date"))
        duration = _parse_duration_hours(request.args.get("duration_hours") or request.args.get("duration"))
        if not employee_code or day is None or duration is None:
            return jsonify({"error": "employee_code, day and duration_hours are required"}), 400

        db = session_factory()
        try:
            generate_missing_credentials(db)
            employee = (
                db.query(Employee)
                .filter(func.lower(Employee.login_code) == employee_code.lower())
                .first()
            )
            if not employee:
                return jsonify({"error": "Employee not found"}), 404
            shifts = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.day == day).all()
            blocked = []
            for shift in shifts:
                try:
                    blocked.append((_time_to_minutes(shift.start_time), _time_to_minutes(shift.end_time)))
                except Exception:
                    continue
            return jsonify({"slots": _generate_slots_for_day(blocked, duration)})
        finally:
            db.close()

    @blueprint.get("/availability/month")
    def availability_month():
        ok, error = require_integration_key()
        if not ok:
            message, status = error
            return jsonify({"error": message}), status

        employee_code = _parse_employee_code(request.args.get("employee_code") or request.args.get("worker"))
        month_parts = _parse_month_ym(request.args.get("month"))
        duration = _parse_duration_hours(request.args.get("duration_hours") or request.args.get("duration"))
        if not employee_code or month_parts is None or duration is None:
            return jsonify({"error": "employee_code, month and duration_hours are required"}), 400

        year, month = month_parts
        month_start = date(year, month, 1)
        month_end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
        db = session_factory()
        try:
            generate_missing_credentials(db)
            employee = (
                db.query(Employee)
                .filter(func.lower(Employee.login_code) == employee_code.lower())
                .first()
            )
            if not employee:
                return jsonify({"error": "Employee not found"}), 404
            shifts = (
                db.query(Shift)
                .filter(Shift.employee_id == employee.id, Shift.day >= month_start, Shift.day <= month_end)
                .all()
            )
            blocked_by_day: dict[date, list[tuple[int, int]]] = {}
            for shift in shifts:
                try:
                    blocked_by_day.setdefault(shift.day, []).append(
                        (_time_to_minutes(shift.start_time), _time_to_minutes(shift.end_time))
                    )
                except Exception:
                    continue

            available_days = []
            cursor = month_start
            while cursor <= month_end:
                if _generate_slots_for_day(blocked_by_day.get(cursor, []), duration):
                    available_days.append(cursor.strftime("%Y-%m-%d"))
                cursor += timedelta(days=1)
            return jsonify({"availableDays": available_days})
        finally:
            db.close()

    return blueprint
