"""Employee authentication and shift workflow routes."""

from __future__ import annotations

import logging
import os
import re
import secrets
from datetime import date, datetime, time
from functools import wraps
from urllib.parse import urljoin, urlparse, quote_plus

from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)


EMPLOYEE_LANG_DEFAULT = "en"

EMPLOYEE_LANG_SUPPORTED = ("en", "de", "uk")

EMPLOYEE_LANG_LABELS = {
  "en": "English",
  "de": "Deutsch",
  "uk": "Українська",
}

EMPLOYEE_TEXTS: dict[str, dict[str, str]] = {
  "en": {
    "login_secure_access": "Secure access",
    "login_title": "Sign in",
    "login_username": "Username or login code",
    "login_password": "Password / PIN",
    "login_button": "Login",
    "login_hint": "Admins use their username and password. Employees use their work email or login code plus PIN.",
    "login_invalid": "Invalid credentials",
    "login_required": "Username and password are required",
    "language": "Language",
    "dashboard_title": "Crew dashboard",
    "sign_out": "Sign out",
    "my_profile": "My profile",
    "staff_type": "Staff type",
    "branch_office": "Branch office",
    "contact_phone": "Phone",
    "not_set": "Not set",
    "welcome": "Hi {name}!",
    "today": "Today",
    "next": "Next",
    "history": "History",
    "your_missions": "Your missions",
    "upcoming_jobs": "Upcoming jobs",
    "recent_missions": "Recent missions",
    "location": "Location",
    "instructions": "Instructions",
    "duration": "Duration",
    "scheduled": "Scheduled",
    "actual": "Actual",
    "checkpoints": "Checkpoints",
    "clock_in": "Clock in",
    "clocked_in": "Clocked in ✔",
    "clock_out": "Clock-out",
    "open_maps": "Open in Maps",
    "mark_complete": "Mark complete",
    "completed": "Completed 🎉",
    "upload_before": "Upload before photo",
    "replace_before": "Replace before photo",
    "upload_after": "Upload after photo",
    "replace_after": "Replace after photo",
    "before": "Before",
    "after": "After",
    "today_empty_title": "You’re all clear ✨",
    "today_empty_message": "No shifts scheduled for today. Check back later or reach out to your manager if you were expecting a mission.",
    "upcoming_empty": "No upcoming jobs yet.",
    "history_empty": "No missions logged yet.",
    "friendly_none": "No jobs scheduled right now.",
    "friendly_one": "You have 1 mission waiting.",
    "friendly_many": "{count} missions lined up for today.",
    "status_scheduled": "Scheduled",
    "status_in_progress": "In progress",
    "status_completed": "Completed",
    "scheduled_job": "Scheduled job",
    "address_soon": "Address coming soon",
    "no_special_instructions": "No special instructions today.",
    "no_notes": "No notes recorded.",
    "date_tbd": "Date to be set",
    "time_tbd": "Time to be scheduled",
    "starts": "Starts {time}",
    "ends": "Ends {time}",
    "shift_not_found": "That shift was not found for your profile.",
    "shift_not_today": "This shift is not scheduled for today.",
    "clocked_in_success": "Clocked in. Go make it shine!",
    "photo_type_required": "Please choose whether this is a before or after photo.",
    "photo_select_first": "Choose a photo to upload first.",
    "photo_type_invalid": "Unsupported file type. Use PNG, JPG, or JPEG.",
    "photo_save_error": "Could not save that photo. Please try again.",
    "photo_saved": "{label} photo saved. Nice work!",
    "complete_success": "Shift complete! Thanks for going the extra mile.",
    "confetti_complete": "Mission complete! 🎉",
  },
  "de": {
    "login_secure_access": "Sicherer Zugang",
    "login_title": "Anmelden",
    "login_username": "Benutzername oder Login-Code",
    "login_password": "Passwort / PIN",
    "login_button": "Login",
    "login_hint": "Admins nutzen Benutzername und Passwort. Mitarbeitende nutzen E-Mail oder Login-Code plus PIN.",
    "login_invalid": "Ungültige Anmeldedaten",
    "login_required": "Benutzername und Passwort sind erforderlich",
    "language": "Sprache",
    "dashboard_title": "Mitarbeiter-Dashboard",
    "sign_out": "Abmelden",
    "my_profile": "Mein Profil",
    "staff_type": "Personaltyp",
    "branch_office": "Niederlassung",
    "contact_phone": "Telefon",
    "not_set": "Nicht angegeben",
    "welcome": "Hallo {name}!",
    "today": "Heute",
    "next": "Nächste",
    "history": "Verlauf",
    "your_missions": "Deine Einsätze",
    "upcoming_jobs": "Bevorstehende Einsätze",
    "recent_missions": "Letzte Einsätze",
    "location": "Ort",
    "instructions": "Anweisungen",
    "duration": "Dauer",
    "scheduled": "Geplant",
    "actual": "Ist",
    "checkpoints": "Zeitstempel",
    "clock_in": "Einstempeln",
    "clocked_in": "Eingestempelt ✔",
    "clock_out": "Ausstempeln",
    "open_maps": "In Maps öffnen",
    "mark_complete": "Als erledigt markieren",
    "completed": "Erledigt 🎉",
    "upload_before": "Vorher-Foto hochladen",
    "replace_before": "Vorher-Foto ersetzen",
    "upload_after": "Nachher-Foto hochladen",
    "replace_after": "Nachher-Foto ersetzen",
    "before": "Vorher",
    "after": "Nachher",
    "today_empty_title": "Für heute alles erledigt ✨",
    "today_empty_message": "Für heute sind keine Schichten geplant. Schau später nochmal vorbei oder kontaktiere deine Leitung.",
    "upcoming_empty": "Noch keine kommenden Einsätze.",
    "history_empty": "Noch keine Einsätze im Verlauf.",
    "friendly_none": "Aktuell sind keine Einsätze geplant.",
    "friendly_one": "Du hast 1 Einsatz heute.",
    "friendly_many": "{count} Einsätze für heute geplant.",
    "status_scheduled": "Geplant",
    "status_in_progress": "Läuft",
    "status_completed": "Erledigt",
    "scheduled_job": "Geplanter Einsatz",
    "address_soon": "Adresse folgt",
    "no_special_instructions": "Heute keine besonderen Anweisungen.",
    "no_notes": "Keine Notizen vorhanden.",
    "date_tbd": "Datum offen",
    "time_tbd": "Zeit wird geplant",
    "starts": "Start {time}",
    "ends": "Ende {time}",
    "shift_not_found": "Diese Schicht wurde für dein Profil nicht gefunden.",
    "shift_not_today": "Diese Schicht ist nicht für heute geplant.",
    "clocked_in_success": "Eingestempelt. Viel Erfolg!",
    "photo_type_required": "Bitte auswählen, ob es ein Vorher- oder Nachher-Foto ist.",
    "photo_select_first": "Bitte zuerst ein Foto auswählen.",
    "photo_type_invalid": "Dateityp nicht unterstützt. Bitte PNG, JPG oder JPEG nutzen.",
    "photo_save_error": "Foto konnte nicht gespeichert werden. Bitte erneut versuchen.",
    "photo_saved": "{label}-Foto gespeichert. Super!",
    "complete_success": "Schicht abgeschlossen. Danke für deinen Einsatz.",
    "confetti_complete": "Einsatz erledigt! 🎉",
  },
  "uk": {
    "login_secure_access": "Безпечний вхід",
    "login_title": "Увійти",
    "login_username": "Ім'я користувача або код входу",
    "login_password": "Пароль / PIN",
    "login_button": "Увійти",
    "login_hint": "Адміни входять за логіном і паролем. Співробітники — за робочим email або кодом входу та PIN.",
    "login_invalid": "Невірні облікові дані",
    "login_required": "Потрібні ім'я користувача та пароль",
    "language": "Мова",
    "dashboard_title": "Панель співробітника",
    "sign_out": "Вийти",
    "welcome": "Привіт, {name}!",
    "today": "Сьогодні",
    "next": "Далі",
    "history": "Історія",
    "your_missions": "Ваші зміни",
    "upcoming_jobs": "Майбутні зміни",
    "recent_missions": "Останні зміни",
    "location": "Локація",
    "instructions": "Інструкції",
    "duration": "Тривалість",
    "scheduled": "Заплановано",
    "actual": "Фактично",
    "checkpoints": "Відмітки",
    "clock_in": "Почати зміну",
    "clocked_in": "Почато ✔",
    "clock_out": "Завершено",
    "open_maps": "Відкрити в Maps",
    "mark_complete": "Позначити завершено",
    "completed": "Завершено 🎉",
    "upload_before": "Завантажити фото «до»",
    "replace_before": "Замінити фото «до»",
    "upload_after": "Завантажити фото «після»",
    "replace_after": "Замінити фото «після»",
    "before": "До",
    "after": "Після",
    "today_empty_title": "На сьогодні все виконано ✨",
    "today_empty_message": "На сьогодні змін немає. Перевірте пізніше або зверніться до менеджера.",
    "upcoming_empty": "Поки що немає майбутніх змін.",
    "history_empty": "Історія змін порожня.",
    "friendly_none": "Зараз немає запланованих змін.",
    "friendly_one": "На сьогодні у вас 1 зміна.",
    "friendly_many": "На сьогодні заплановано {count} змін.",
    "status_scheduled": "Заплановано",
    "status_in_progress": "В процесі",
    "status_completed": "Завершено",
    "scheduled_job": "Запланована зміна",
    "address_soon": "Адресу буде додано",
    "no_special_instructions": "Сьогодні без додаткових інструкцій.",
    "no_notes": "Немає приміток.",
    "date_tbd": "Дату буде визначено",
    "time_tbd": "Час буде визначено",
    "starts": "Початок {time}",
    "ends": "Завершення {time}",
    "shift_not_found": "Зміну для вашого профілю не знайдено.",
    "shift_not_today": "Ця зміна не запланована на сьогодні.",
    "clocked_in_success": "Ви відмітились. Гарної роботи!",
    "photo_type_required": "Вкажіть, це фото «до» чи «після».",
    "photo_select_first": "Спочатку оберіть фото для завантаження.",
    "photo_type_invalid": "Непідтримуваний тип файлу. Використайте PNG, JPG або JPEG.",
    "photo_save_error": "Не вдалося зберегти фото. Спробуйте ще раз.",
    "photo_saved": "Фото «{label}» збережено. Чудово!",
    "complete_success": "Зміну завершено. Дякуємо!",
    "confetti_complete": "Зміну завершено! 🎉",
  },
}


def _safe_next_url() -> str | None:
  candidate = request.form.get("next") or request.args.get("next")
  if not candidate:
    return None
  try:
    resolved = urlparse(urljoin(request.host_url, candidate))
  except Exception:
    return None
  if resolved.netloc and resolved.netloc != request.host:
    return None
  path = resolved.path or ""
  if not path:
    return None
  login_path = url_for("login")
  if path == login_path:
    return None
  query = f"?{resolved.query}" if resolved.query else ""
  return f"{path}{query}"

def _employee_redirect_target(next_url: str | None) -> str:
  # Employees may only land on employee-scoped routes to avoid redirect loops.
  if not next_url:
    return url_for("employee_dashboard")
  try:
    parsed = urlparse(next_url)
    path = parsed.path or ""
  except Exception:
    return url_for("employee_dashboard")
  # reject any attempt to land on the login page
  login_path = url_for("login")
  if path == login_path:
    return url_for("employee_dashboard")
  if path.startswith("/employee"):
    # keep query component if present
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{path}{query}"
  return url_for("employee_dashboard")

def _normalize_employee_lang(raw: str | None) -> str:
  value = (raw or "").strip().lower()
  alias = {
    "en": "en",
    "english": "en",
    "de": "de",
    "deutsch": "de",
    "german": "de",
    "uk": "uk",
    "ua": "uk",
    "ukrainian": "uk",
    "ukranian": "uk",
    "українська": "uk",
  }
  return alias.get(value, EMPLOYEE_LANG_DEFAULT)

def _get_employee_lang() -> str:
  selected = (
    request.args.get("lang")
    or request.form.get("lang")
    or session.get("employee_lang")
    or EMPLOYEE_LANG_DEFAULT
  )
  lang = _normalize_employee_lang(selected)
  session["employee_lang"] = lang
  return lang

def _employee_text(lang: str, key: str, **kwargs) -> str:
  bundle = EMPLOYEE_TEXTS.get(lang) or EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT]
  template = bundle.get(key) or EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT].get(key) or key
  if kwargs:
    try:
      return template.format(**kwargs)
    except Exception:
      return template
  return template

def _slugify_path_segment(value: str | None, fallback: str) -> str:
  raw = (value or "").strip()
  if not raw:
    return fallback
  safe = secure_filename(raw).lower().replace("_", "-")
  return safe or fallback

def _build_shift_proof_relative_path(shift, photo_type: str, filename: str) -> str:
  now = datetime.utcnow()
  year = now.strftime("%Y")
  month = now.strftime("%m")
  employee_segment = _slugify_path_segment(
    shift.employee.name if shift.employee else None,
    f"employee-{shift.employee_id}",
  )
  site_segment = _slugify_path_segment(
    shift.site.name if shift.site else None,
    f"place-{shift.site_id}",
  )
  ext = os.path.splitext(filename)[1].lower()
  safe_file_name = secure_filename(
    f"shift-{shift.id}-{photo_type}-{secrets.token_hex(6)}{ext}"
  )
  return os.path.join(
    "uploads",
    "proofs",
    year,
    month,
    employee_segment,
    site_segment,
    photo_type,
    safe_file_name,
  ).replace(os.sep, "/")

def create_employee_blueprint(*, session_factory, Employee, Shift, Site, auth_username: str, auth_password: str, coerce_float_fn, allowed_image_fn, remove_photo_fn, upload_folder_getter):
    blueprint = Blueprint("employee_portal", __name__)

    def employee_login_required(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if session.get("role") == "employee" and session.get("employee_id"):
                return view_func(*args, **kwargs)
            return redirect(url_for("login", next=request.url))
        return wrapper

    @blueprint.route("/login", methods=["GET", "POST"])
    def login():
      lang = _get_employee_lang()
      ui = EMPLOYEE_TEXTS.get(lang, EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT])
      next_url = _safe_next_url()
      if session.get("role") == "admin" and session.get("auth"):
        return redirect(next_url or url_for("admin_dashboard"))
      if session.get("role") == "employee" and session.get("employee_id"):
        return redirect(_employee_redirect_target(next_url))

      error = None
      if request.method == "POST":
        username_raw = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if username_raw and password:
          if username_raw == auth_username and password == auth_password:
            session.clear()
            session["auth"] = True
            session["role"] = "admin"
            session["user"] = username_raw
            return redirect(next_url or url_for("admin_dashboard"))

          normalized = username_raw.lower()
          db = session_factory()
          try:
            employee = (
              db.query(Employee)
              .filter(
                or_(
                  func.lower(Employee.login_email) == normalized,
                  func.lower(Employee.login_code) == normalized,
                )
              )
              .first()
            )
          finally:
            db.close()

          if employee and employee.login_pin_hash:
            if check_password_hash(employee.login_pin_hash, password):
              session.clear()
              session["role"] = "employee"
              session["employee_id"] = employee.id
              session["employee_name"] = employee.name
              session["employee_code"] = employee.login_code
              session["employee_lang"] = lang
              return redirect(_employee_redirect_target(next_url))
          error = _employee_text(lang, "login_invalid")
        else:
          error = _employee_text(lang, "login_required")

      return render_template(
        "login.html",
        error=error,
        next_value=next_url,
        lang=lang,
        ui=ui,
        lang_labels=EMPLOYEE_LANG_LABELS,
      )

    @blueprint.route("/employee", endpoint="employee_dashboard")
    @blueprint.route("/employee/dashboard", endpoint="employee_dashboard")
    @employee_login_required
    def employee_dashboard():
      employee_id = session.get("employee_id")
      employee_name = session.get("employee_name", "Team member")
      lang = _get_employee_lang()
      ui = EMPLOYEE_TEXTS.get(lang, EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT])
      today = date.today()
      db = session_factory()
      shift_cards = []
      upcoming_cards = []
      history_cards = []
      profile_info = {}

      def _format_minutes(total_minutes: int | None) -> str:
        if total_minutes is None or total_minutes <= 0:
          return "—"
        hours, minutes = divmod(int(total_minutes), 60)
        parts = []
        if hours:
          parts.append(f"{hours}h")
        if minutes:
          parts.append(f"{minutes}m")
        return " ".join(parts) if parts else "<1m"

      def _scheduled_minutes(shift_obj: Shift) -> int:
        baseline = datetime.combine(date.min, shift_obj.start_time)
        finish = datetime.combine(date.min, shift_obj.end_time)
        delta = finish - baseline
        return max(int(delta.total_seconds() // 60), 0)

      def _time_window_label(shift_obj: Shift) -> str:
        start = shift_obj.start_time
        end = shift_obj.end_time
        if start and end:
          start_label = start.strftime("%H:%M")
          end_label = end.strftime("%H:%M")
          return f"{start_label} – {end_label}"
        if start:
          start_label = start.strftime("%H:%M")
          return _employee_text(lang, "starts", time=start_label)
        if end:
          end_label = end.strftime("%H:%M")
          return _employee_text(lang, "ends", time=end_label)
        return _employee_text(lang, "time_tbd")

      def _status_text(shift_obj: Shift) -> str:
        if shift_obj.clock_out_at:
          return _employee_text(lang, "status_completed")
        if shift_obj.clock_in_at:
          return _employee_text(lang, "status_in_progress")
        return _employee_text(lang, "status_scheduled")

      try:
        employee = db.get(Employee, employee_id)
        if employee:
          profile_info = {
            "staff_type": employee.staff_type or employee.role or _employee_text(lang, "not_set"),
            "branch": employee.branch or "Wien",
            "phone": employee.profile_phone or _employee_text(lang, "not_set"),
          }
        todays_shifts = (
          db.query(Shift)
          .filter(Shift.employee_id == employee_id, Shift.day == today)
          .order_by(Shift.start_time.asc())
          .all()
        )
        for shift in todays_shifts:
          site_name = shift.site.name if shift.site else _employee_text(lang, "scheduled_job")
          address = (shift.site.address or _employee_text(lang, "address_soon")) if shift.site else _employee_text(lang, "address_soon")
          map_url = None
          if shift.site and shift.site.address:
            map_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(shift.site.address)}"

          start_label = shift.start_time.strftime("%H:%M")
          end_label = shift.end_time.strftime("%H:%M")

          clocked_in = bool(shift.clock_in_at)
          clocked_out = bool(shift.clock_out_at)
          if clocked_out:
            status_label = _employee_text(lang, "status_completed")
            status_key = "completed"
          elif clocked_in:
            status_label = _employee_text(lang, "status_in_progress")
            status_key = "in_progress"
          else:
            status_label = _employee_text(lang, "status_scheduled")
            status_key = "scheduled"

          clock_in_display = shift.clock_in_at.strftime("%H:%M") if shift.clock_in_at else "—"
          clock_out_display = shift.clock_out_at.strftime("%H:%M") if shift.clock_out_at else "—"

          scheduled_minutes = _scheduled_minutes(shift)
          actual_minutes = None
          if shift.clock_in_at and shift.clock_out_at:
            delta_actual = shift.clock_out_at - shift.clock_in_at
            actual_minutes = max(int(delta_actual.total_seconds() // 60), 0)

          before_url = None
          if shift.before_photo_path:
            relative = shift.before_photo_path.lstrip("/\\")
            before_url = url_for("static", filename=relative)
          after_url = None
          if shift.after_photo_path:
            relative_after = shift.after_photo_path.lstrip("/\\")
            after_url = url_for("static", filename=relative_after)

          shift_cards.append(
            {
              "id": shift.id,
              "site_name": site_name,
              "address": address,
              "map_url": map_url,
              "instructions": (shift.instructions or _employee_text(lang, "no_special_instructions")),
              "time_window": f"{start_label} – {end_label}",
              "status_label": status_label,
              "status_key": status_key,
              "clock_in_display": clock_in_display,
              "clock_out_display": clock_out_display,
              "clocked_in": clocked_in,
              "clocked_out": clocked_out,
              "scheduled_duration": _format_minutes(scheduled_minutes),
              "actual_duration": _format_minutes(actual_minutes),
              "has_actual_duration": actual_minutes is not None,
              "clock_in_url": url_for("employee_clock_in", shift_id=shift.id),
              "upload_url": url_for("employee_upload_photo", shift_id=shift.id),
              "complete_url": url_for("employee_complete_shift", shift_id=shift.id),
              "before_photo_url": before_url,
              "after_photo_url": after_url,
            }
          )

        upcoming_shifts = (
          db.query(Shift)
          .filter(Shift.employee_id == employee_id, Shift.day > today)
          .order_by(Shift.day.asc(), Shift.start_time.asc())
          .limit(20)
          .all()
        )

        for shift in upcoming_shifts:
          site_name = shift.site.name if shift.site else _employee_text(lang, "scheduled_job")
          address = shift.site.address if shift.site and shift.site.address else None
          status_key = "completed" if shift.clock_out_at else ("in_progress" if shift.clock_in_at else "scheduled")
          upcoming_cards.append(
            {
              "id": shift.id,
              "site_name": site_name,
              "day_label": shift.day.strftime("%d.%m.%Y") if shift.day else _employee_text(lang, "date_tbd"),
              "time_window": _time_window_label(shift),
              "status_label": _status_text(shift),
              "status_key": status_key,
              "address": address,
              "instructions": shift.instructions or None,
            }
          )

        history_shifts = (
          db.query(Shift)
          .filter(Shift.employee_id == employee_id, Shift.day < today)
          .order_by(Shift.day.desc(), Shift.start_time.desc())
          .limit(15)
          .all()
        )

        for shift in history_shifts:
          scheduled_minutes = _scheduled_minutes(shift)
          actual_minutes = None
          if shift.clock_in_at and shift.clock_out_at:
            delta_actual = shift.clock_out_at - shift.clock_in_at
            actual_minutes = max(int(delta_actual.total_seconds() // 60), 0)

          if shift.clock_out_at:
            status_label = _employee_text(lang, "status_completed")
            status_key = "completed"
          elif shift.clock_in_at:
            status_label = _employee_text(lang, "status_in_progress")
            status_key = "in_progress"
          else:
            status_label = _employee_text(lang, "status_scheduled")
            status_key = "scheduled"

          history_cards.append(
            {
              "id": shift.id,
              "site_name": shift.site.name if shift.site else _employee_text(lang, "scheduled_job"),
              "day_label": shift.day.strftime("%d.%m.%Y"),
              "time_window": _time_window_label(shift),
              "status_label": status_label,
              "status_key": status_key,
              "scheduled_duration": _format_minutes(scheduled_minutes),
              "actual_duration": _format_minutes(actual_minutes),
              "has_actual_duration": actual_minutes is not None,
              "instructions": shift.instructions or _employee_text(lang, "no_notes"),
            }
          )
      finally:
        db.close()

      count = len(shift_cards)
      if count == 0:
        friendly_message = _employee_text(lang, "friendly_none")
      elif count == 1:
        friendly_message = _employee_text(lang, "friendly_one")
      else:
        friendly_message = _employee_text(lang, "friendly_many", count=count)

      today_label = today.strftime("%d.%m.%Y")
      return render_template(
        "employee_dashboard.html",
        lang=lang,
        ui=ui,
        lang_labels=EMPLOYEE_LANG_LABELS,
        welcome_message=_employee_text(lang, "welcome", name=employee_name),
        employee_name=employee_name,
        profile_info=profile_info,
        today_label=today_label,
        friendly_message=friendly_message,
        shifts=shift_cards,
        upcoming_jobs=upcoming_cards,
        history=history_cards,
        todays_shifts_count=len(shift_cards),
        todays_shifts_for_notify=[{"site_name": s["site_name"], "time_window": s["time_window"]} for s in shift_cards],
      )

    @blueprint.route("/employee/shifts/<int:shift_id>/clock-in", methods=["POST"])
    @employee_login_required
    def employee_clock_in(shift_id: int):
      employee_id = session.get("employee_id")
      lang = _get_employee_lang()
      lat = coerce_float_fn(request.form.get("lat"))
      lng = coerce_float_fn(request.form.get("lng"))

      db = session_factory()
      try:
        shift = db.get(Shift, shift_id)
        if not shift or shift.employee_id != employee_id:
          flash(_employee_text(lang, "shift_not_found"))
          return redirect(url_for("employee_dashboard"))

        if shift.day != date.today():
          flash(_employee_text(lang, "shift_not_today"))
          return redirect(url_for("employee_dashboard"))

        if not shift.clock_in_at:
          shift.clock_in_at = datetime.utcnow()
        if lat is not None:
          shift.clock_in_lat = lat
        if lng is not None:
          shift.clock_in_lng = lng
        db.commit()
        flash(_employee_text(lang, "clocked_in_success"))
      finally:
        db.close()

      return redirect(url_for("employee_dashboard"))

    @blueprint.route("/employee/shifts/<int:shift_id>/upload", methods=["POST"])
    @employee_login_required
    def employee_upload_photo(shift_id: int):
      employee_id = session.get("employee_id")
      lang = _get_employee_lang()
      photo_type = (request.form.get("photo_type") or "").strip().lower()
      file = request.files.get("photo")

      db = session_factory()
      try:
        shift = db.get(Shift, shift_id)
        if not shift or shift.employee_id != employee_id:
          flash(_employee_text(lang, "shift_not_found"))
          return redirect(url_for("employee_dashboard"))

        if photo_type not in {"before", "after"}:
          flash(_employee_text(lang, "photo_type_required"))
          return redirect(url_for("employee_dashboard"))

        if not file or not file.filename:
          flash(_employee_text(lang, "photo_select_first"))
          return redirect(url_for("employee_dashboard"))

        if not allowed_image_fn(file.filename):
          flash(_employee_text(lang, "photo_type_invalid"))
          return redirect(url_for("employee_dashboard"))

        relative_path = _build_shift_proof_relative_path(shift, photo_type, file.filename)
        upload_subpath = relative_path[len("uploads/") :].replace("/", os.sep)
        destination = os.path.join(upload_folder_getter(), upload_subpath)
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        try:
          file.save(destination)
        except OSError:
          logging.exception("Failed to save uploaded photo for shift %s", shift_id)
          flash(_employee_text(lang, "photo_save_error"))
          return redirect(url_for("employee_dashboard"))

        photo_label = _employee_text(lang, "before") if photo_type == "before" else _employee_text(lang, "after")
        if photo_type == "before":
          remove_photo_fn(shift.before_photo_path)
          shift.before_photo_path = relative_path
        else:
          remove_photo_fn(shift.after_photo_path)
          shift.after_photo_path = relative_path

        db.commit()
        flash(_employee_text(lang, "photo_saved", label=photo_label))
      finally:
        db.close()

      return redirect(url_for("employee_dashboard"))

    @blueprint.route("/employee/shifts/<int:shift_id>/complete", methods=["POST"])
    @employee_login_required
    def employee_complete_shift(shift_id: int):
      employee_id = session.get("employee_id")
      lang = _get_employee_lang()
      lat = coerce_float_fn(request.form.get("lat"))
      lng = coerce_float_fn(request.form.get("lng"))

      db = session_factory()
      try:
        shift = db.get(Shift, shift_id)
        if not shift or shift.employee_id != employee_id:
          flash(_employee_text(lang, "shift_not_found"))
          return redirect(url_for("employee_dashboard"))

        if shift.day != date.today():
          flash(_employee_text(lang, "shift_not_today"))
          return redirect(url_for("employee_dashboard"))

        if not shift.clock_in_at:
          shift.clock_in_at = datetime.utcnow()
        shift.clock_out_at = datetime.utcnow()
        if lat is not None:
          shift.clock_out_lat = lat
        if lng is not None:
          shift.clock_out_lng = lng

        db.commit()
        flash(_employee_text(lang, "complete_success"))
      finally:
        db.close()

      return redirect(url_for("employee_dashboard"))

    @blueprint.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return blueprint
