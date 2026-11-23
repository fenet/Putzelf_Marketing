"""Lead pipeline routes, extracted from the legacy application module."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, redirect, render_template, request, url_for


LEAD_STAGES = ["New Leads", "Contacted", "Converted"]


def create_leads_blueprint(*, session_factory, Lead, login_required):
    """Build the lead routes with the app's existing database and auth objects."""
    blueprint = Blueprint("leads", __name__, url_prefix="/leads")

    @blueprint.route("", methods=["GET", "POST"])
    @login_required
    def dashboard():
        db = session_factory()
        try:
            if request.method == "POST":
                action = (request.form.get("action") or "create").strip().lower()
                if action == "delete":
                    lead_id = request.form.get("id", type=int)
                    if lead_id:
                        lead = db.get(Lead, lead_id)
                        if lead:
                            db.delete(lead)
                            db.commit()
                elif action == "update":
                    lead_id = request.form.get("id", type=int)
                    if lead_id:
                        lead = db.get(Lead, lead_id)
                        if lead:
                            name = (request.form.get("name") or lead.name).strip()
                            if name:
                                lead.name = name
                            lead.email = (request.form.get("email") or "").strip() or None
                            lead.phone = (request.form.get("phone") or "").strip() or None
                            lead.source = (request.form.get("source") or "").strip() or None
                            lead.notes = (request.form.get("notes") or "").strip() or None
                            stage = (request.form.get("stage") or lead.stage).strip()
                            if stage in LEAD_STAGES:
                                lead.stage = stage
                            db.commit()
                else:
                    name = (request.form.get("name") or "").strip()
                    if name:
                        stage = (request.form.get("stage") or "New Leads").strip()
                        if stage not in LEAD_STAGES:
                            stage = "New Leads"
                        lead = Lead(
                            name=name,
                            email=(request.form.get("email") or "").strip() or None,
                            phone=(request.form.get("phone") or "").strip() or None,
                            source=(request.form.get("source") or "").strip() or None,
                            notes=(request.form.get("notes") or "").strip() or None,
                            stage=stage,
                        )
                        db.add(lead)
                        db.commit()
                return redirect(url_for("leads.dashboard"))

            stage_filter = (request.args.get("stage") or "").strip() or None
            start_filter = request.args.get("start")
            end_filter = request.args.get("end")
            sort = request.args.get("sort", "desc")

            query = db.query(Lead)
            if stage_filter and stage_filter in LEAD_STAGES:
                query = query.filter(Lead.stage == stage_filter)
            if start_filter:
                try:
                    start_dt = datetime.strptime(start_filter, "%Y-%m-%d")
                    query = query.filter(Lead.created_at >= start_dt)
                except ValueError:
                    pass
            if end_filter:
                try:
                    end_dt = datetime.strptime(end_filter, "%Y-%m-%d") + timedelta(days=1)
                    query = query.filter(Lead.created_at < end_dt)
                except ValueError:
                    pass
            if sort == "asc":
                query = query.order_by(Lead.created_at.asc())
            else:
                query = query.order_by(Lead.created_at.desc())

            grouped = {stage: [] for stage in LEAD_STAGES}
            for lead in query.all():
                grouped.setdefault(lead.stage, []).append(lead)

            return render_template(
                "leads.html",
                stages=LEAD_STAGES,
                grouped_leads=grouped,
                stage_filter=stage_filter,
                start_filter=start_filter,
                end_filter=end_filter,
                sort=sort,
                active_page="leads",
            )
        finally:
            db.close()

    @blueprint.route("/stage", methods=["POST"])
    @login_required
    def stage():
        data = request.get_json(silent=True) or {}
        lead_id = data.get("id")
        stage_name = data.get("stage")
        if not lead_id or stage_name not in LEAD_STAGES:
            return jsonify({"error": "Invalid request"}), 400
        try:
            lead_id = int(lead_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid request"}), 400

        db = session_factory()
        try:
            lead = db.get(Lead, lead_id)
            if not lead:
                return jsonify({"error": "Lead not found"}), 404
            lead.stage = stage_name
            db.commit()
            return jsonify({"status": "ok"})
        finally:
            db.close()

    return blueprint
