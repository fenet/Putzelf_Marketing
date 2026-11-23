"""Client site management routes."""

from __future__ import annotations

import math
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func, or_


def _site_exists(db, Site, name: str, address: str, exclude_id: int | None = None) -> bool:
    """Return True if a site with the same name and address already exists."""
    name_norm = (name or "").strip().lower()
    address_norm = (address or "").strip().lower()
    if not name_norm or not address_norm:
        return False
    query = db.query(Site).filter(
        func.lower(Site.name) == name_norm,
        func.lower(Site.address) == address_norm,
    )
    if exclude_id:
        query = query.filter(Site.id != exclude_id)
    return db.query(query.exists()).scalar()


def create_sites_blueprint(*, session_factory, Site, Shift, login_required):
    blueprint = Blueprint("clients", __name__, url_prefix="/admin")

    @blueprint.route("/sites", methods=["GET", "POST"])
    @login_required
    def sites():
      db = session_factory()
      try:
        search_q = (request.args.get("q") or "").strip()
        if request.method == "POST":
          entity = (request.form.get("entity") or "site").strip()
          action = (request.form.get("action") or "").strip().lower()
          redirect_q = (request.form.get("redirect_q") or "").strip()
          redirect_page_raw = (request.form.get("redirect_page") or "").strip()
          redirect_page_val = None
          if redirect_page_raw.isdigit():
            redirect_page_val = max(int(redirect_page_raw), 1)
          redirect_params: dict[str, int | str] = {}
          effective_q = redirect_q or search_q
          if effective_q:
            redirect_params["q"] = effective_q
          if redirect_page_val and redirect_page_val > 1:
            redirect_params["page"] = redirect_page_val
          redirect_url = url_for("admin_sites", **redirect_params)
          if entity == "site":
            site_id = request.form.get("id")
            if action == "create":
              name = (request.form.get("name") or "").strip()
              address = (request.form.get("address") or "").strip()
              hourly_rate = request.form.get("hourly_rate", type=float)
              is_active = (request.form.get("is_active", "1") or "1").strip() != "0"
              if name and address:
                if _site_exists(db, Site, name, address):
                  flash(
                    "Site already exists with the same name and address.",
                    "warning",
                  )
                else:
                  db.add(
                    Site(
                      name=name,
                      address=address,
                      hourly_rate=hourly_rate or 50.0,
                      is_active=is_active,
                    )
                  )
                  db.commit()
            elif action == "update" and site_id:
              site = db.get(Site, int(site_id))
              if site:
                name = (request.form.get("name") or "").strip() or site.name
                address = (request.form.get("address") or "").strip() or site.address
                hourly_rate = request.form.get("hourly_rate", type=float)
                is_active = (request.form.get("is_active", "1") or "1").strip() != "0"
                if _site_exists(db, Site, name, address, exclude_id=site.id):
                  flash(
                    "Another site already uses that name and address.",
                    "warning",
                  )
                else:
                  site.name = name
                  site.address = address
                  if hourly_rate is not None:
                    site.hourly_rate = hourly_rate
                  site.is_active = is_active
                  db.commit()
            elif action == "delete" and site_id:
              site = db.get(Site, int(site_id))
              if site:
                db.delete(site)
                db.commit()
          elif entity == "site_bulk" and action == "bulk_update":
            ids = request.form.getlist("site_id")
            names = request.form.getlist("site_name")
            addresses = request.form.getlist("site_address")
            hourly_rates = request.form.getlist("site_hourly_rate")
            active_flags = request.form.getlist("site_is_active")
            seen_pairs = set()
            for sid, n, a, rate, active_flag in zip(
              ids,
              names,
              addresses,
              hourly_rates,
              active_flags,
            ):
              n = (n or "").strip()
              a = (a or "").strip()
              if not sid or not n or not a:
                continue
              key = (n.lower(), a.lower())
              if key in seen_pairs:
                continue
              seen_pairs.add(key)
              site = db.get(Site, int(sid))
              if site and not _site_exists(db, Site, n, a, exclude_id=site.id):
                site.name = n
                site.address = a
                try:
                  parsed_rate = float(rate)
                except (TypeError, ValueError):
                  parsed_rate = None
                if parsed_rate is not None:
                  site.hourly_rate = parsed_rate
                site.is_active = (active_flag or "1").strip() != "0"
            db.commit()

          return redirect(redirect_url)

        query = db.query(Site)
        if search_q:
          like = f"%{search_q}%"
          query = query.filter(
            or_(Site.name.ilike(like), Site.address.ilike(like))
          )

        filtered_sites = query.count()

        per_page = 3
        page = request.args.get("page", default=1, type=int)
        if page is None or page < 1:
          page = 1
        if filtered_sites == 0:
          total_pages = 1
          page = 1
          offset = 0
        else:
          total_pages = max(1, math.ceil(filtered_sites / per_page))
          if page > total_pages:
            page = total_pages
          offset = (page - 1) * per_page

        sites = (
          query
          .order_by(Site.id.desc())
          .offset(offset)
          .limit(per_page)
          .all()
        )

        page_sites = len(sites)
        has_prev = page > 1 and filtered_sites > 0
        has_next = page < total_pages and filtered_sites > 0
        prev_page = page - 1 if has_prev else None
        next_page = page + 1 if has_next else None

        total_sites = db.query(func.count(Site.id)).scalar() or 0
        active_sites_total = (
          db.query(func.count(Site.id))
          .filter(or_(Site.is_active.is_(True), Site.is_active.is_(None)))
          .scalar()
          or 0
        )
        inactive_sites_total = max(total_sites - active_sites_total, 0)
        site_ids = [site.id for site in sites if site.id]
        shift_counts: dict[int, int] = {}
        if site_ids:
          shift_counts = {
            site_id: count
            for site_id, count in (
              db.query(Shift.site_id, func.count(Shift.id))
              .filter(Shift.site_id.in_(site_ids))
              .group_by(Shift.site_id)
              .all()
            )
          }
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=7)
        covered_site_ids = {
          row[0]
          for row in db.query(Shift.site_id)
          .filter(Shift.day >= week_start, Shift.day < week_end)
          .distinct()
          .all()
          if row[0] is not None
        }
        active_site_ids = {
          row[0]
          for row in db.query(Site.id)
          .filter(or_(Site.is_active.is_(True), Site.is_active.is_(None)))
          .all()
          if row[0] is not None
        }
        covered_active_site_ids = covered_site_ids.intersection(active_site_ids)
        unassigned_active_sites = max(active_sites_total - len(covered_active_site_ids), 0)

        return render_template(
          "sites.html",
          active_page="sites",
          sites=sites,
          search_q=search_q,
          shift_counts=shift_counts,
          total_sites=total_sites,
          filtered_sites=filtered_sites,
          covered_sites=len(covered_active_site_ids),
          inactive_sites=inactive_sites_total,
          unassigned_active_sites=unassigned_active_sites,
          page=page,
          per_page=per_page,
          total_pages=total_pages,
          has_prev=has_prev,
          has_next=has_next,
          prev_page=prev_page,
          next_page=next_page,
          page_sites=page_sites,
        )
      finally:
        db.close()

    return blueprint
