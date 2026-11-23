"""Scheduling routes."""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, time, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, url_for

logger = logging.getLogger(__name__)


def create_scheduling_blueprint(
    *,
    session_factory,
    Employee,
    Site,
    Shift,
    login_required,
    reportlab_available: bool,
    find_employee_schedule_conflict,
    get_day_range,
    load_schedule_context,
    add_weeks_fn,
    week_range_by_offset_fn,
    generate_schedule_pdf_fn,
):
    blueprint = Blueprint("scheduling", __name__)

    @blueprint.route("/schedule/import-previous-month", methods=["POST"])
    @login_required
    def schedule_import_previous_month():
        db = session_factory()
        try:
            payload = request.get_json(silent=True) or {}
            selected_ids_raw = payload.get("selected_ids") if isinstance(payload, dict) else None
            if selected_ids_raw is None:
                selected_ids_raw = request.form.getlist("selected_ids[]")
            source_offset_raw = payload.get("source_offset") if isinstance(payload, dict) else None
            target_offset_raw = payload.get("target_offset") if isinstance(payload, dict) else None
            if source_offset_raw is None:
                source_offset_raw = request.form.get("source_offset", "1")
            if target_offset_raw is None:
                target_offset_raw = request.form.get("target_offset", "1")
            selected_ids = []
            if selected_ids_raw:
                for sel in selected_ids_raw:
                    try:
                        selected_ids.append(int(sel))
                    except (ValueError, TypeError):
                        continue
            try:
              source_offset = max(0, min(int(source_offset_raw), 52))
            except (ValueError, TypeError):
              source_offset = 1
            try:
              target_offset = max(1, min(int(target_offset_raw), 52))
            except (ValueError, TypeError):
              target_offset = 1
            first_day, last_day = week_range_by_offset_fn(reference_day=date.today(), weeks_back=source_offset)
            query = db.query(Shift).filter(Shift.day >= first_day, Shift.day <= last_day)
            if selected_ids:
                query = query.filter(Shift.id.in_(selected_ids))
            shifts = query.order_by(Shift.day.asc()).all()
            created = 0
            skipped_conflict = 0
            skipped_existing = 0
            skipped_inactive = 0
            for s in shifts:
              emp = s.employee if s.employee else db.get(Employee, s.employee_id)
              # for target weeks 1..target_offset, create a copy per week if no existing/conflict
              for k in range(1, target_offset + 1):
                td = add_weeks_fn(s.day, k)
                # skip if exact same shift already exists
                existing = (
                  db.query(Shift)
                  .filter(
                    Shift.employee_id == s.employee_id,
                    Shift.site_id == s.site_id,
                    Shift.day == td,
                    Shift.start_time == s.start_time,
                    Shift.end_time == s.end_time,
                  )
                  .first()
                )
                if existing:
                  skipped_existing += 1
                  continue
                # check conflict for this target week
                conflict_msg = find_employee_schedule_conflict(
                  db, s.employee_id, td, s.start_time, s.end_time, s.site_id
                )
                if conflict_msg:
                  skipped_conflict += 1
                  continue
                new_shift = Shift(
                  employee_id=s.employee_id,
                  site_id=s.site_id,
                  day=td,
                  start_time=s.start_time,
                  end_time=s.end_time,
                  instructions=s.instructions,
                )
                db.add(new_shift)
                created += 1
            if created > 0:
                db.commit()
            return jsonify({
                "created": created,
                "skipped_conflict": skipped_conflict,
                "skipped_existing": skipped_existing,
                "skipped_inactive": skipped_inactive,
            })
        finally:
            db.close()

    @blueprint.route("/schedule/preview-import-previous-month", methods=["GET"])
    @login_required
    def schedule_preview_import_previous_month():
        db = session_factory()
        try:
            source_offset_raw = request.args.get("source_offset", "1")
            target_offset_raw = request.args.get("target_offset", "1")
            try:
                source_offset = max(0, min(int(source_offset_raw), 52))
            except (ValueError, TypeError):
                source_offset = 1
            try:
                target_offset = max(1, min(int(target_offset_raw), 52))
            except (ValueError, TypeError):
                target_offset = 1
            # interpret offsets as weeks (source_offset weeks back, target_offset weeks forward)
            first_day, last_day = week_range_by_offset_fn(reference_day=date.today(), weeks_back=source_offset)
            shifts = (
                db.query(Shift)
                .filter(Shift.day >= first_day, Shift.day <= last_day)
                .order_by(Shift.day.asc())
                .all()
            )
            items = []
            for s in shifts:
                emp = s.employee if s.employee else db.get(Employee, s.employee_id)
                # skip employees explicitly marked inactive
                if not getattr(emp, 'is_active', False):
                    continue
                # check conflicts for each week 1..target_offset
                conflict_msgs: list[str] = []
                target_days: list[str] = []
                for k in range(1, target_offset + 1):
                    td = add_weeks_fn(s.day, k)
                    target_days.append(td.strftime("%Y-%m-%d"))
                    cm = find_employee_schedule_conflict(
                        db, s.employee_id, td, s.start_time, s.end_time, s.site_id
                    )
                    if cm:
                        conflict_msgs.append(f"{td.strftime('%d.%m.%Y')}: {cm}")
                site = s.site if s.site else db.get(Site, s.site_id)
                items.append({
                    "id": s.id,
                    "employee": emp.name if emp else "-",
                    "active": True,
                    "site": site.name if site else "-",
                    "from_day": s.day.strftime("%Y-%m-%d"),
                    "to_day": f"next {target_offset} week(s)",
                    "to_days": target_days,
                    "time": f"{s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')}",
                    "conflict": len(conflict_msgs) > 0,
                    "conflict_message": "\n".join(conflict_msgs) if conflict_msgs else None,
                })
            # sort items by employee name ascending
            items = sorted(items, key=lambda it: (it.get('employee') or '').lower())
            return jsonify(items=items)
        finally:
            db.close()

    @blueprint.route("/schedule/free-available", methods=["GET"])
    @login_required
    def schedule_free_available():
        """Return JSON list of active employees who are free for the given date range and time interval.

        Query params:
          - free_start_date (YYYY-MM-DD) required
          - free_end_date (YYYY-MM-DD) optional (defaults to start_date)
          - free_start_time (HH:MM) optional
          - free_end_time (HH:MM) optional
          - site_id optional to limit by site
        """
        db = session_factory()
        try:
          start_date_str = (request.args.get("free_start_date") or "").strip()
          if not start_date_str:
            return jsonify({"error":"missing free_start_date"}), 400
          try:
            start_date_val = datetime.strptime(start_date_str, "%Y-%m-%d").date()
          except ValueError:
            return jsonify({"error":"invalid free_start_date"}), 400
          end_date_str = (request.args.get("free_end_date") or start_date_str).strip()
          try:
            end_date_val = datetime.strptime(end_date_str, "%Y-%m-%d").date()
          except ValueError:
            return jsonify({"error":"invalid free_end_date"}), 400
          if end_date_val < start_date_val:
            return jsonify({"error":"end date before start date"}), 400

          start_time_str = (request.args.get("free_start_time") or "").strip()
          end_time_str = (request.args.get("free_end_time") or "").strip()
          interval_start = None
          interval_end = None
          if start_time_str and end_time_str:
            try:
              interval_start = datetime.strptime(start_time_str, "%H:%M").time()
              interval_end = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError:
              return jsonify({"error":"invalid time format"}), 400

          site_id = request.args.get("site_id", type=int)

          # collect candidate employees (only active ones)
          employees = (
            db.query(Employee)
            .filter((Employee.is_active == True) | (Employee.is_active == None))
            .order_by(Employee.name.asc())
            .all()
          )
          free_list = []
          # iterate employees and check for any overlapping shift in the interval
          delta_days = (end_date_val - start_date_val).days
          for emp in employees:
            has_conflict = False
            for d_off in range(delta_days + 1):
              day = start_date_val + timedelta(days=d_off)
              q = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.day == day)
              if site_id:
                q = q.filter(Shift.site_id == site_id)
              shifts = q.all()
              for s in shifts:
                # if no time interval specified, any shift on that day counts as conflict
                if interval_start is None or interval_end is None:
                  has_conflict = True
                  break
                # check time overlap: shift.start < interval_end and shift.end > interval_start
                try:
                  s_start = s.start_time
                  s_end = s.end_time
                except Exception:
                  continue
                if (s_start < interval_end) and (s_end > interval_start):
                  has_conflict = True
                  break
              if has_conflict:
                break
            if not has_conflict:
              free_list.append({"id": emp.id, "name": emp.name, "role": emp.role})

          return jsonify(items=free_list)
        finally:
          db.close()

    @blueprint.route("/shift/<int:shift_id>/move", methods=["POST"])
    @login_required
    def move_shift_day(shift_id: int):
        db = session_factory()
        try:
            shift = db.get(Shift, shift_id)
            if not shift:
                return jsonify({"ok": False, "error": "Shift not found"}), 404

            day_str = (request.form.get("day") or "").strip()
            if not day_str:
                return jsonify({"ok": False, "error": "Missing day"}), 400

            try:
                new_day = datetime.strptime(day_str, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                return jsonify({"ok": False, "error": "Invalid day format"}), 400

            employee_id_str = (request.form.get("employee_id") or "").strip()
            new_employee_id = shift.employee_id
            if employee_id_str:
                try:
                    new_employee_id = int(employee_id_str)
                except (TypeError, ValueError):
                    return jsonify({"ok": False, "error": "Invalid employee id"}), 400
                if new_employee_id != shift.employee_id:
                    new_employee = db.get(Employee, new_employee_id)
                    if not new_employee:
                        return jsonify({"ok": False, "error": "Target employee not found"}), 404

            conflict_message = find_employee_schedule_conflict(
              db,
              employee_id=new_employee_id,
              day=new_day,
              start_time=shift.start_time,
              end_time=shift.end_time,
              site_id=shift.site_id,
              exclude_shift_id=shift.id,
            )
            if conflict_message:
              return jsonify({"ok": False, "error": conflict_message}), 400

            shift.day = new_day
            shift.employee_id = new_employee_id
            db.commit()
            return jsonify({"ok": True})
        except Exception as exc:
            db.rollback()
            logger.error("Error moving shift %s: %s", shift_id, exc)
            return jsonify({"ok": False, "error": "Failed to move shift"}), 500
        finally:
            db.close()

    @blueprint.route("/shift/batch-delete", methods=["POST"])
    @login_required
    def batch_delete_shifts():
        db = session_factory()
        try:
            shift_ids = request.form.getlist("shift_ids[]")
            if shift_ids:
                deleted_count = 0
                for shift_id in shift_ids:
                    try:
                        shift = db.get(Shift, int(shift_id))
                        if shift:
                            db.delete(shift)
                            deleted_count += 1
                    except (ValueError, TypeError):
                        continue
                if deleted_count > 0:
                    db.commit()
                    flash(f"{deleted_count} shift(s) deleted successfully.")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        finally:
            db.close()

    @blueprint.route("/shift/delete/<int:shift_id>", methods=["GET"])
    @login_required
    def delete_shift(shift_id):
        db = session_factory()
        try:
            shift = db.get(Shift, shift_id)
            if shift:
                db.delete(shift)
                db.commit()
            return redirect(request.referrer or url_for("schedule_dashboard"))
        finally:
            db.close()

    @blueprint.route("/schedule/pdf", methods=["GET"])
    @login_required
    def schedule_pdf():
        if not reportlab_available:
            return jsonify({"error": "reportlab not installed"}), 503

        week_param = request.args.get("week")
        employee_id = request.args.get("employee_id", type=int)
        weeks = request.args.get("weeks", default=1, type=int) or 1
        weeks = max(1, min(weeks, 12))
        ref_date = None
        if week_param:
            try:
                ref_date = datetime.strptime(week_param, "%Y-%m-%d").date()
            except ValueError:
                ref_date = None
        week_days = get_day_range(ref_date, weeks=weeks)

        db = session_factory()
        try:
            employees, _, matrix = load_schedule_context(db, week_days)
            if employee_id:
                employees = [e for e in employees if e.id == employee_id]
                if not employees:
                    return jsonify({"error": "Employee not found"}), 404
            pdf_buffer = generate_schedule_pdf_fn(week_days, employees, matrix)
        finally:
            db.close()

        filename = f"schedule_{week_days[0].isoformat()}_{week_days[-1].isoformat()}.pdf"
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    @blueprint.route("/shift/<int:shift_id>/edit", methods=["POST"])
    @login_required
    def edit_shift(shift_id: int):
        db = session_factory()
        try:
            shift = db.get(Shift, shift_id)
            if not shift:
                flash("Shift not found.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))
        
            # Get form data
            employee_id_raw = (request.form.get("employee_id") or "").strip()
            day_str = (request.form.get("day") or "").strip()
            start_str = (request.form.get("start_time") or "").strip()
            end_str = (request.form.get("end_time") or "").strip()
            instructions = (request.form.get("instructions") or "").strip() or None

            if employee_id_raw:
                try:
                    new_employee_id = int(employee_id_raw)
                except (TypeError, ValueError):
                    flash("Invalid employee selected.", "warning")
                    return redirect(request.referrer or url_for("schedule_dashboard"))

                employee_exists = db.query(Employee.id).filter(Employee.id == new_employee_id).first()
                if not employee_exists:
                    flash("Selected employee was not found.", "warning")
                    return redirect(request.referrer or url_for("schedule_dashboard"))
            else:
                flash("Please select an employee.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))
        
            # Parse and validate inputs
            try:
                day = datetime.strptime(day_str, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                flash("Invalid day format.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))
        
            try:
                start_time = datetime.strptime(start_str, "%H:%M").time()
            except (ValueError, TypeError):
                flash("Invalid start time format.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))
        
            try:
                end_time = datetime.strptime(end_str, "%H:%M").time()
            except (ValueError, TypeError):
                flash("Invalid end time format.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))
        
            # Validate that end time is after start time
            if end_time <= start_time:
                flash("End time must be after start time.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))

            conflict_message = find_employee_schedule_conflict(
              db,
              employee_id=new_employee_id,
              day=day,
              start_time=start_time,
              end_time=end_time,
              site_id=shift.site_id,
              exclude_shift_id=shift.id,
            )
            if conflict_message:
              flash(conflict_message, "warning")
              return redirect(request.referrer or url_for("schedule_dashboard"))
        
            # Update shift
            shift.employee_id = new_employee_id
            shift.day = day
            shift.start_time = start_time
            shift.end_time = end_time
            shift.instructions = instructions
        
            db.commit()
            flash("Shift updated successfully!")
        except Exception as e:
            db.rollback()
            logger.error(f"Error editing shift {shift_id}: {e}")
            flash("Error updating shift.", "warning")
        finally:
            db.close()
    
        return redirect(request.referrer or url_for("schedule_dashboard"))

    @blueprint.route("/shift/batch-edit", methods=["POST"])
    @login_required
    def batch_edit_shifts():
      db = session_factory()
      try:
        raw_shift_ids = request.form.getlist("shift_ids[]")
        shift_ids: list[int] = []
        for raw_id in raw_shift_ids:
          try:
            value = int(raw_id)
          except (TypeError, ValueError):
            continue
          if value not in shift_ids:
            shift_ids.append(value)

        if not shift_ids:
          flash("Keine Einsätze für Sammelbearbeitung ausgewählt.", "warning")
          return redirect(request.referrer or url_for("schedule_dashboard"))

        day_str = (request.form.get("day") or "").strip()
        start_str = (request.form.get("start_time") or "").strip()
        end_str = (request.form.get("end_time") or "").strip()
        instructions_str = (request.form.get("instructions") or "").strip()

        if not day_str and not start_str and not end_str and not instructions_str:
          flash("Bitte mindestens ein Feld für die Sammelbearbeitung setzen.", "warning")
          return redirect(request.referrer or url_for("schedule_dashboard"))

        new_day = None
        if day_str:
          try:
            new_day = datetime.strptime(day_str, "%Y-%m-%d").date()
          except (ValueError, TypeError):
            flash("Ungültiges Datumsformat.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        new_start = None
        new_end = None
        if start_str or end_str:
          if not (start_str and end_str):
            flash("Für Sammelzeit-Updates bitte Start- und Endzeit angeben.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
          try:
            new_start = datetime.strptime(start_str, "%H:%M").time()
            new_end = datetime.strptime(end_str, "%H:%M").time()
          except (ValueError, TypeError):
            flash("Ungültiges Zeitformat.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

          if new_end <= new_start:
            flash("Endzeit muss nach der Startzeit liegen.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        shifts = db.query(Shift).filter(Shift.id.in_(shift_ids)).all()
        if not shifts:
          flash("Keine gültigen Einsätze gefunden.", "warning")
          return redirect(request.referrer or url_for("schedule_dashboard"))

        updated_count = 0
        for shift in shifts:
          target_day = new_day if new_day is not None else shift.day
          target_start = new_start if new_start is not None else shift.start_time
          target_end = new_end if new_end is not None else shift.end_time

          conflict_message = find_employee_schedule_conflict(
            db,
            employee_id=shift.employee_id,
            day=target_day,
            start_time=target_start,
            end_time=target_end,
            site_id=shift.site_id,
            exclude_shift_id=shift.id,
          )
          if conflict_message:
            flash(f"Einsatz #{shift.id}: {conflict_message}", "warning")
            continue

          if new_day is not None:
            shift.day = new_day
          if new_start is not None and new_end is not None:
            shift.start_time = new_start
            shift.end_time = new_end
          if instructions_str:
            shift.instructions = instructions_str
          updated_count += 1

        if updated_count > 0:
          db.commit()
          flash(f"{updated_count} Einsatz/Einsätze erfolgreich aktualisiert.")
        else:
          flash("Es wurden keine Einsätze aktualisiert.", "warning")

        return redirect(request.referrer or url_for("schedule_dashboard"))
      except Exception as exc:
        db.rollback()
        logger.error("Error during batch shift edit: %s", exc)
        flash("Fehler beim Aktualisieren der ausgewählten Einsätze.", "warning")
        return redirect(request.referrer or url_for("schedule_dashboard"))
      finally:
        db.close()

    @blueprint.route("/schedule", methods=["GET", "POST"])
    @login_required
    def schedule_dashboard():
        db = session_factory()
        try:
            if request.method == "POST":
                employee_ids_raw = [ (e or "").strip() for e in request.form.getlist("employee_id") ]
                employee_ids = []
                for emp_str in employee_ids_raw:
                  if not emp_str:
                    continue
                  try:
                    employee_ids.append(int(emp_str))
                  except ValueError:
                    continue
                site_id = request.form.get("site_id")
                day_values_raw = [ (d or "").strip() for d in request.form.getlist("day") ]
                if not any(day_values_raw):
                  fallback_days = (request.form.get("day_display") or "").strip()
                  if fallback_days:
                    day_values_raw = [part.strip() for part in fallback_days.split(",") if part.strip()]
                start_str = request.form.get("start_time")
                duration_hours_str = request.form.get("duration_hours")
                instructions_raw = (request.form.get("instructions") or "").strip()
                instructions_val = instructions_raw or None
                day_values: list[date] = []
                seen_days: set[date] = set()
                for day_str in day_values_raw:
                  if not day_str:
                    continue
                  try:
                    day_val = datetime.strptime(day_str, "%Y-%m-%d").date()
                  except ValueError:
                    continue
                  if day_val in seen_days:
                    continue
                  seen_days.add(day_val)
                  day_values.append(day_val)
                if employee_ids and site_id and day_values and start_str and duration_hours_str:
                  try:
                    start_val = datetime.strptime(start_str, "%H:%M").time()
                  except ValueError:
                    start_val = None
                  try:
                    duration_hours = float(duration_hours_str)
                  except (TypeError, ValueError):
                    duration_hours = 0
                  if start_val and 0 < duration_hours <= 24:
                    duration_delta = timedelta(hours=duration_hours)
                    created = 0
                    blocked_messages: list[str] = []
                    for employee_id in employee_ids:
                      employee = db.get(Employee, employee_id)
                      employee_label = employee.name if employee else f"Mitarbeiter {employee_id}"
                      for day_val in day_values:
                        end_dt = datetime.combine(day_val, start_val) + duration_delta
                        end_val = end_dt.time()

                        conflict_message = find_employee_schedule_conflict(
                          db,
                          employee_id=employee_id,
                          day=day_val,
                          start_time=start_val,
                          end_time=end_val,
                          site_id=int(site_id),
                        )
                        if conflict_message:
                          blocked_messages.append(f"{employee_label} ({day_val.strftime('%d.%m.%Y')}): {conflict_message}")
                          continue

                        shift = Shift(
                          employee_id=employee_id,
                          site_id=int(site_id),
                          day=day_val,
                          start_time=start_val,
                          end_time=end_val,
                          instructions=instructions_val,
                        )
                        db.add(shift)
                        created += 1
                    if created:
                      db.commit()
                      flash(f"{created} Einsatz/Einsätze wurden eingeplant.")
                    if blocked_messages:
                      flash(blocked_messages[0], "warning")
                    if not created and not blocked_messages:
                      flash("Es konnte kein Einsatz eingeplant werden.", "warning")
                query_args = request.args.to_dict(flat=False)
                return redirect(url_for("schedule_dashboard", **query_args))

            selected_employee_id = request.args.get("employee_id", type=int)
            selected_site_id = request.args.get("site_id", type=int)
            free_day_str = (request.args.get("free_day") or "").strip()
            free_week_start_str = (request.args.get("free_week_start") or "").strip()
            free_day = None
            free_week_start = None
            if free_day_str:
                try:
                    free_day = datetime.strptime(free_day_str, "%Y-%m-%d").date()
                except ValueError:
                    free_day = None
            if not free_day and free_week_start_str:
                try:
                    free_week_start = datetime.strptime(free_week_start_str, "%Y-%m-%d").date()
                except ValueError:
                    free_week_start = None

            # Support both weeks (legacy) and explicit days view: `?days=3` overrides weeks.
            days = request.args.get("days", type=int)
            weeks = request.args.get("weeks", default=8, type=int) or 8
            weeks = max(1, min(weeks, 12))
            if days:
                # clamp days between 1 and 84 (12 weeks)
                days = max(1, min(int(days), 84))
            start_date_str = request.args.get("start_date")
            start_date_val = None
            if start_date_str:
                try:
                    start_date_val = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                except ValueError:
                    start_date_val = None
            else:
                # If the user didn't choose a start date, anchor the default view to
                # the next upcoming shift (or the most recent shift) so the grid isn't empty.
                today = date.today()
                next_row = (
                  db.query(Shift.day)
                  .filter(Shift.day >= today)
                  .order_by(Shift.day.asc())
                  .first()
                )
                if next_row and next_row[0]:
                  start_date_val = next_row[0]
                else:
                  last_row = (
                    db.query(Shift.day)
                    .order_by(Shift.day.desc())
                    .first()
                  )
                  if last_row and last_row[0]:
                    start_date_val = last_row[0]

            week_days = get_day_range(start=start_date_val, weeks=weeks, days=days)
            employees, sites, matrix = load_schedule_context(db, week_days)

            selected_employee = None
            selected_site = None
            # Employee focus only affects the grid columns (filter dropdown still uses `employees`).
            visible_employees = employees
            if selected_employee_id:
              selected_employee = next((e for e in employees if e.id == selected_employee_id), None)
              if selected_employee:
                visible_employees = [selected_employee]

            filtered_matrix = matrix
            if selected_site_id:
              selected_site = next((s for s in sites if s.id == selected_site_id), None)
              filtered_matrix = {}
              for key, shifts in matrix.items():
                matched = [shift for shift in shifts if shift.get("site_id") == selected_site_id]
                if matched:
                  filtered_matrix[key] = matched

            grid_employee_ids = {e.id for e in visible_employees}
            shift_days_for_grid = {day for (emp_id, day) in filtered_matrix.keys() if emp_id in grid_employee_ids}
            # Keep the full selected period in the grid, even when some days are empty.
            visible_days = week_days
            has_any_shifts = bool(shift_days_for_grid)

            if not selected_employee:
              shift_employee_ids_for_grid = {emp_id for (emp_id, _day) in filtered_matrix.keys()}
              visible_employees = [e for e in employees if e.id in shift_employee_ids_for_grid]

            pdf_params = {"week": week_days[0].isoformat()}
            pdf_params["weeks"] = weeks
            if selected_employee_id:
                pdf_params["employee_id"] = selected_employee_id
            if start_date_val:
                pdf_params["week"] = week_days[0].isoformat()
            pdf_url = url_for("schedule_pdf", **pdf_params)

            hours_params = {
              "start_date": week_days[0].isoformat(),
              "end_date": week_days[-1].isoformat(),
            }
            if selected_employee_id:
              hours_params["employee_id"] = selected_employee_id
            hours_pdf_url = url_for("hours_pdf", **hours_params)

            schedule_html = render_template(
                "schedule.html",
                employees=employees,
                visible_employees=visible_employees,
                sites=sites,
                week_days=week_days,
                visible_days=visible_days,
                has_any_shifts=has_any_shifts,
                weeks=weeks,
                start_date=start_date_val.isoformat() if start_date_val else "",
                cells=filtered_matrix,
                reportlab_available=reportlab_available,
                selected_employee_id=selected_employee_id,
                selected_site_id=selected_site_id,
                selected_employee=selected_employee,
                selected_site=selected_site,
                pdf_url=pdf_url,
                hours_pdf_url=hours_pdf_url,
                free_day=free_day_str,
                free_week_start=free_week_start_str,
                active_page="schedule",
            )
            return schedule_html
        finally:
            db.close()

    return blueprint
