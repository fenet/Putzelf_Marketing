"""Public safety resources and site inspection workflows."""

from __future__ import annotations

import csv
import io
import os
import secrets
from datetime import date, datetime
from urllib.parse import urlparse

from flask import Blueprint, abort, flash, redirect, render_template_string, request, send_file, session, url_for
from sqlalchemy import func
from werkzeug.utils import secure_filename


SHELL = """
<!doctype html><html lang="{{ 'de' if current_lang == 'de' else 'en' }}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ page_title }} - Putzelf's</title>
<meta name="theme-color" content="#014D4E">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
{% if show_admin_sidebar %}<link rel="stylesheet" href="{{ url_for('static', filename='admin-sidebar.css') }}">{% endif %}
<style>body{background:#f5f7fb;color:#19233b}.wrap{width:min(1100px,100%);margin:2rem auto;padding:0 1rem}.ep-portal-shell{min-height:100vh;display:grid;grid-template-columns:248px minmax(0,1fr);background:#f5f7fb}.ep-portal-shell .wrap{width:100%;max-width:none;margin:0;padding:2rem clamp(1rem,3vw,2.5rem)}.card{border:1px solid #e2e8f0;border-radius:1rem;box-shadow:0 8px 24px #17213b0a}.top{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1.3rem}.muted{color:#64748b}.checked{color:#16804a;font-weight:700}.unchecked{color:#c24132;font-weight:700}.area-card{border:1px solid #e2e8f0;border-radius:.8rem;padding:1rem;background:#fff}.area-card+.area-card{margin-top:.7rem}nav a{margin-right:.6rem}.tag{border-radius:2rem;padding:.2rem .65rem;background:#edf2ff}</style></head><body>{% if show_admin_sidebar %}<div class="ep-portal-shell">{% include 'partials/admin_sidebar.html' %}{% endif %}<main class="wrap {{ 'inspection-page' if active_page|default('') in ['inspection', 'inspection_report', 'inspection_areas'] else '' }}">
{% with messages = get_flashed_messages(with_categories=true) %}{% for category,message in messages %}<div class="alert alert-{{ 'warning' if category == 'warning' else 'success' if category == 'success' else 'info' }}">{{ message }}</div>{% endfor %}{% endwith %}
{{ body|safe }}
 </main>{% if show_admin_sidebar %}</div>{% endif %}</body></html>
"""


def create_service_portal_blueprint(
    *, session_factory, Employee, Site, SiteInspectionArea, SiteInspection, InspectionItem,
    PublicDocument, manager_required, login_required, public_document_folder,
    inspection_photo_folder, public_app_url, reportlab_available, pdf_canvas, page_size,
):
    bp = Blueprint("ops", __name__)
    suggested_areas = (
        "Entrance and reception", "Floors and common areas", "Work areas", "Restrooms",
        "Kitchen and break room", "Storage and supplies", "Equipment",
        "Safety and emergency access",
    )
    os.makedirs(public_document_folder, exist_ok=True)
    os.makedirs(inspection_photo_folder, exist_ok=True)

    def _is_main_admin() -> bool:
        return session.get("role") == "admin" and bool(session.get("auth"))

    def _period(raw: str | None) -> str:
        candidate = (raw or "").strip()
        try:
            datetime.strptime(candidate, "%Y-%m")
            return candidate
        except ValueError:
            return date.today().strftime("%Y-%m")

    def _inspection_status(inspection, configured_count=None):
        if inspection is None:
            return "Checklist not configured" if configured_count == 0 else "Not started"
        items = [item for item in inspection.items if item.site_area_id is not None]
        total = len(items)
        complete = sum(bool(item.checked) for item in items)
        if total and complete == total:
            return "Complete"
        if complete:
            return "In progress"
        return "Not started" if total or configured_count else "Checklist not configured"

    def _inspection_items(inspection):
        if not inspection:
            return []
        return sorted(
            (item for item in inspection.items if item.site_area_id is not None),
            key=lambda item: (item.id, item.area_name.casefold()),
        )

    def _site_is_available_to_manager(site) -> bool:
        if _is_main_admin():
            return True
        return site.manager_employee_id == session.get("employee_id")

    def _find_or_create_inspection(db, site, month: str):
        inspection = db.query(SiteInspection).filter_by(site_id=site.id, month=month).first()
        areas = db.query(SiteInspectionArea).filter_by(site_id=site.id, is_active=True).order_by(SiteInspectionArea.sort_order, SiteInspectionArea.id).all()
        if not areas:
            return inspection
        if inspection and _inspection_items(inspection):
            return inspection
        if not inspection:
            inspection = SiteInspection(
                site_id=site.id,
                month=month,
                inspected_by_employee_id=session.get("employee_id") if not _is_main_admin() else None,
                updated_at=datetime.utcnow(),
            )
            db.add(inspection)
            db.flush()
        for area in areas:
            db.add(InspectionItem(inspection_id=inspection.id, site_area_id=area.id, area_name=area.name, checked=False))
        db.flush()
        return inspection

    def _report_rows(db, month: str):
        sites = db.query(Site).order_by(Site.name.asc(), Site.id.asc()).all()
        report = []
        for site in sites:
            inspection = db.query(SiteInspection).filter_by(site_id=site.id, month=month).first()
            current_items = _inspection_items(inspection)
            configured_count = db.query(SiteInspectionArea.id).filter_by(site_id=site.id, is_active=True).count()
            if current_items:
                items = current_items
                item_rows = [{"area": item.area_name, "checked": bool(item.checked), "notes": item.notes or "", "item": item} for item in items]
                status = _inspection_status(inspection, configured_count)
            else:
                site_areas = db.query(SiteInspectionArea).filter_by(site_id=site.id, is_active=True).order_by(SiteInspectionArea.sort_order, SiteInspectionArea.id).all()
                item_rows = [{"area": area.name, "checked": False, "notes": "", "item": None} for area in site_areas]
                status = _inspection_status(inspection, configured_count)
            report.append({"site": site, "inspection": inspection if current_items else None, "inspector_name": inspection.inspector.name if current_items and inspection.inspector else "", "areas": item_rows, "status": status})
        return report

    def _render(page_title: str, body: str, **context):
        return render_template_string(SHELL, page_title=page_title, body=render_template_string(body, **context), **context)

    @bp.route("/site-manager")
    @manager_required
    def site_manager_home():
        db = session_factory()
        try:
            month = date.today().strftime("%Y-%m")
            manager_id = session.get("employee_id") if not _is_main_admin() else None
            query = db.query(Site)
            if manager_id:
                query = query.filter(Site.manager_employee_id == manager_id)
            sites = query.order_by(Site.name.asc()).all()
            area_counts = {
                site.id: db.query(SiteInspectionArea.id).filter_by(site_id=site.id, is_active=True).count()
                for site in sites
            }
            inspection_by_site = {
                inspection.site_id: inspection
                for inspection in db.query(SiteInspection).filter(SiteInspection.month == month).all()
            }
            completed = sum(_inspection_status(inspection_by_site.get(site.id), area_counts[site.id]) == "Complete" for site in sites)
            configured_sites = sum(count > 0 for count in area_counts.values())
            unconfigured_sites = len(sites) - configured_sites
            employees_count = db.query(func.count(Employee.id)).filter(Employee.access_role != "site_manager").scalar() or 0
        finally:
            db.close()
        body = """
<div class="top"><div><div class="muted">Operations portal</div><h1>Welcome, {{ manager_name }}</h1><div class="muted">Manage your team, sites, schedule, and monthly inspections.</div></div><a class="btn btn-outline-secondary" href="{{ url_for('logout') }}">Sign out</a></div>
<nav class="mb-3"><a href="{{ url_for('ops.manager_inspections') }}">Inspections</a><a href="{{ url_for('schedule_dashboard') }}">Schedule</a><a href="{{ url_for('admin_sites') }}">Sites</a><a href="{{ url_for('admin_employees') }}">Employees</a><a href="{{ url_for('ops.public_resources') }}" target="_blank">Public safety library</a></nav>
<div class="row g-3 mb-4"><div class="col-md-4"><div class="card p-3"><div class="muted">Assigned sites</div><h2>{{ sites|length }}</h2></div></div><div class="col-md-4"><div class="card p-3"><div class="muted">Inspections complete · {{ month }}</div><h2>{{ completed }} / {{ configured_sites }}</h2>{% if unconfigured_sites %}<div class="small muted">{{ unconfigured_sites }} sites need their own areas set up</div>{% endif %}</div></div><div class="col-md-4"><div class="card p-3"><div class="muted">Employees</div><h2>{{ employees_count }}</h2></div></div></div>
<div class="card p-4"><h2 class="h5">Assigned sites</h2>{% if sites %}<div class="list-group list-group-flush">{% for site in sites %}<div class="list-group-item d-flex justify-content-between align-items-center gap-3"><div><strong>{{ site.profile_company_name or site.name }}</strong><div class="muted">{{ site.address or '' }} · {{ area_counts[site.id] }} inspection areas</div></div><div class="d-flex flex-wrap gap-2"><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}">Manage areas</a>{% if area_counts[site.id] %}<a class="btn btn-sm btn-primary" href="{{ url_for('ops.manager_inspection_detail', site_id=site.id, month=month) }}">Inspect this month</a>{% endif %}</div></div>{% endfor %}</div>{% else %}<p class="muted mb-0">No sites are assigned to your account yet. Ask the main manager to assign sites.</p>{% endif %}</div>
"""
        name = session.get("employee_name") or "Site manager"
        return _render("Site manager", body, manager_name=name, sites=sites, area_counts=area_counts, configured_sites=configured_sites, unconfigured_sites=unconfigured_sites, completed=completed, month=month, employees_count=employees_count, manager_pwa=True, show_admin_sidebar=True, active_page="dashboard")

    @bp.route("/resources")
    def public_resources():
        db = session_factory()
        try:
            documents = db.query(PublicDocument).order_by(PublicDocument.category.asc(), PublicDocument.title.asc()).all()
        finally:
            db.close()
        categories = {}
        for document in documents:
            categories.setdefault(document.category or "General", []).append(document)
        all_documents = [document for items in categories.values() for document in items]
        body = """
<div class="public-resources-page">
  <header class="public-resources-header"><div><span class="inspection-index-eyebrow"><i class="bi bi-shield-check"></i> Putzelf Public resources</span><h1>Safety and work documents</h1><p>Find and download the latest safety rules and work instructions.</p></div><a class="btn btn-outline-secondary" href="{{ url_for('login') }}"><i class="bi bi-person-lock"></i> Manager / employee sign in</a></header>
  <section class="public-resources-welcome"><span><i class="bi bi-folder2-open"></i></span><div><strong><span>{{ all_documents|length }}</span> <span>documents</span> <span>in</span> <span>{{ categories|length }}</span> <span>categories</span></strong><small>These resources are available without signing in.</small></div><label class="public-library-search"><i class="bi bi-search"></i><input id="public-resource-search" type="search" placeholder="Search documents" aria-label="Search documents"></label></section>
  {% if categories %}<nav class="public-library-filter-row public-resources-categories" aria-label="Browse document categories"><button type="button" class="is-active" data-resource-category="all" aria-pressed="true">All documents <span>{{ all_documents|length }}</span></button>{% for category,items in categories.items() %}<button type="button" data-resource-category="{{ category|lower|e }}" aria-pressed="false">{{ category }} <span>{{ items|length }}</span></button>{% endfor %}</nav><div class="public-resources-grid" id="public-resource-grid">{% for category,items in categories.items() %}{% for document in items %}{% set is_pdf = document.original_filename.lower().endswith('.pdf') %}<article class="public-resource-card" data-resource-category="{{ category|lower|e }}" data-resource-search="{{ (document.title ~ ' ' ~ category ~ ' ' ~ document.original_filename)|lower|e }}"><span class="public-resource-file-icon {{ 'is-pdf' if is_pdf else 'is-docx' }}"><i class="bi {{ 'bi-filetype-pdf' if is_pdf else 'bi-file-earmark-word' }}"></i></span><span class="public-resource-copy"><small>{{ category }}</small><strong>{{ document.title }}</strong><span>{{ document.original_filename }}</span></span><a href="{{ url_for('ops.public_document_download', document_id=document.id) }}" aria-label="Download {{ document.title }}"><i class="bi bi-download"></i><span>Download</span></a></article>{% endfor %}{% endfor %}</div><div class="public-library-empty" id="public-resource-empty" hidden><i class="bi bi-search"></i><strong>No documents match this search.</strong><span>Try another title or category.</span></div>{% else %}<div class="public-library-empty"><i class="bi bi-folder2-open"></i><strong>No public documents have been published yet.</strong><span>Please check back later for safety and work resources.</span></div>{% endif %}
</div>
<script>
(() => {
  const search = document.getElementById('public-resource-search');
  const cards = [...document.querySelectorAll('.public-resource-card')];
  const filters = [...document.querySelectorAll('[data-resource-category]')];
  const empty = document.getElementById('public-resource-empty');
  let category = 'all';
  const apply = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const show = (category === 'all' || card.dataset.resourceCategory === category) && (card.dataset.resourceSearch || '').includes(query);
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.hidden = visible > 0;
  };
  filters.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.resourceCategory || 'all';
    filters.forEach(item => {
      const selected = item === button;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    apply();
  }));
  search?.addEventListener('input', apply);
})();
</script>
"""

        return _render("Public documents", body, categories=categories, all_documents=all_documents)

    @bp.route("/resources/<int:document_id>/download")
    def public_document_download(document_id: int):
        db = session_factory()
        try:
            document = db.get(PublicDocument, document_id)
            if not document:
                abort(404)
            storage_name = os.path.basename(document.storage_name or "")
            path = os.path.join(public_document_folder, storage_name)
            if not storage_name or not os.path.isfile(path):
                abort(404)
            return send_file(path, as_attachment=True, download_name=document.original_filename)
        finally:
            db.close()

    @bp.route("/admin/resources", methods=["GET", "POST"])
    @login_required
    def admin_public_documents():
        db = session_factory()
        try:
            if request.method == "POST":
                action = (request.form.get("action") or "upload").strip().lower()
                if action == "delete":
                    document = db.get(PublicDocument, request.form.get("id", type=int))
                    if document:
                        try:
                            os.remove(os.path.join(public_document_folder, os.path.basename(document.storage_name)))
                        except OSError:
                            pass
                        db.delete(document)
                        db.commit()
                        flash("Public document removed.", "success")
                    return redirect(url_for("ops.admin_public_documents"))
                upload = request.files.get("document")
                title = (request.form.get("title") or "").strip()[:200]
                category = (request.form.get("category") or "General").strip()[:100] or "General"
                original = secure_filename(upload.filename or "") if upload else ""
                extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
                if not upload or not original or extension not in {"pdf", "docx"}:
                    flash("Choose a PDF or DOCX document to publish.", "warning")
                elif not title:
                    flash("Enter a title for this document.", "warning")
                else:
                    storage_name = f"{secrets.token_hex(16)}.{extension}"
                    upload.save(os.path.join(public_document_folder, storage_name))
                    db.add(PublicDocument(title=title, category=category, original_filename=original, storage_name=storage_name))
                    db.commit()
                    flash("Public document published.", "success")
                return redirect(url_for("ops.admin_public_documents"))
            documents = db.query(PublicDocument).order_by(PublicDocument.category.asc(), PublicDocument.title.asc()).all()
            categories = sorted({(document.category or "General").strip() or "General" for document in documents}, key=str.casefold)
        finally:
            db.close()
        category_counts = {category: sum(((document.category or "General").strip() or "General") == category for document in documents) for category in categories}
        pdf_count = sum(document.original_filename.lower().endswith(".pdf") for document in documents)
        docx_count = len(documents) - pdf_count
        body = """
<div class="public-library-admin">
  <header class="inspection-report-header"><div><span class="inspection-index-eyebrow"><i class="bi bi-folder2-open"></i> Resource center</span><h1>Public document library</h1><p>Publish and organize documents that anyone can open from your QR landing page.</p></div><div class="inspection-index-header-actions"><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_qr_code') }}"><i class="bi bi-qr-code"></i> Public QR code</a><a class="btn btn-outline-secondary" href="{{ url_for('ops.public_resources') }}" target="_blank" rel="noopener"><i class="bi bi-box-arrow-up-right"></i> View public library</a></div></header>
  <section class="public-library-stats" aria-label="Document library summary"><article><span><i class="bi bi-files"></i></span><div><small>Published documents</small><strong>{{ documents|length }}</strong></div></article><article><span class="is-category"><i class="bi bi-collection"></i></span><div><small>Categories</small><strong>{{ categories|length }}</strong></div></article><article><span class="is-pdf"><i class="bi bi-filetype-pdf"></i></span><div><small>PDF files</small><strong>{{ pdf_count }}</strong></div></article><article><span class="is-docx"><i class="bi bi-file-earmark-word"></i></span><div><small>DOCX files</small><strong>{{ docx_count }}</strong></div></article></section>
  <div class="public-library-layout">
    <section class="public-library-upload"><div class="public-library-section-title"><span><i class="bi bi-cloud-arrow-up"></i></span><div><h2>Publish a document</h2><p>Add a resource to the public library.</p></div></div><form method="post" enctype="multipart/form-data" class="public-library-upload-form"><label for="public-doc-title">Document title</label><input id="public-doc-title" class="form-control" name="title" required maxlength="200" placeholder="e.g. Safety rules for cleaning staff"><label for="public-doc-category">Category</label><input id="public-doc-category" class="form-control" name="category" list="document-categories" value="Safety rules" maxlength="100" placeholder="Choose or enter a category"><datalist id="document-categories">{% for category in categories %}<option value="{{ category }}">{% endfor %}</datalist><label for="public-doc-file">File</label><label class="public-library-file-input" for="public-doc-file"><i class="bi bi-file-earmark-arrow-up"></i><span><strong>Choose a PDF or DOCX file</strong><small>PDF and Word documents are supported</small></span><i class="bi bi-plus-circle"></i></label><input id="public-doc-file" class="visually-hidden" type="file" name="document" accept=".pdf,.docx" required><div class="public-library-selected-file" id="public-doc-selected-file" aria-live="polite">No file selected</div><button class="btn btn-primary" type="submit"><i class="bi bi-cloud-arrow-up"></i> Publish document</button></form><p class="public-library-upload-note"><i class="bi bi-info-circle"></i> Published files are accessible without signing in.</p></section>
    <section class="public-library-documents"><header class="public-library-list-header"><div class="public-library-section-title"><span class="is-list"><i class="bi bi-collection"></i></span><div><h2>Published documents</h2><p>Organized resources available in the public library.</p></div></div><label class="public-library-search"><i class="bi bi-search"></i><input id="public-doc-search" type="search" placeholder="Search documents" aria-label="Search documents"></label></header>
      <div class="public-library-filter-row" role="group" aria-label="Filter documents by category"><button type="button" class="is-active" data-doc-category="all" aria-pressed="true">All <span>{{ documents|length }}</span></button>{% for category in categories %}<button type="button" data-doc-category="{{ category|lower|e }}" aria-pressed="false">{{ category }} <span>{{ category_counts[category] }}</span></button>{% endfor %}</div>
      {% if documents %}<div class="public-library-document-list" id="public-doc-list">{% for document in documents %}{% set is_pdf = document.original_filename.lower().endswith('.pdf') %}{% set doc_category = (document.category or 'General')|trim or 'General' %}<article class="public-library-document" data-doc-category="{{ doc_category|lower|e }}" data-doc-search="{{ (document.title ~ ' ' ~ doc_category ~ ' ' ~ document.original_filename)|lower|e }}"><span class="public-library-document-icon {{ 'is-pdf' if is_pdf else 'is-docx' }}"><i class="bi {{ 'bi-filetype-pdf' if is_pdf else 'bi-file-earmark-word' }}"></i></span><div class="public-library-document-copy"><h3>{{ document.title }}</h3><div><span class="public-library-category">{{ doc_category }}</span><span class="public-library-filename" title="{{ document.original_filename }}">{{ document.original_filename }}</span></div></div><div class="public-library-document-actions"><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('ops.public_document_download', document_id=document.id) }}"><i class="bi bi-download"></i><span>Download</span></a><form method="post" onsubmit="return confirm('Remove this public document?')"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ document.id }}"><button class="btn btn-sm btn-outline-danger" type="submit" aria-label="Remove {{ document.title }}"><i class="bi bi-trash3"></i><span>Remove</span></button></form></div></article>{% endfor %}</div><div class="public-library-empty" id="public-doc-empty" hidden><i class="bi bi-search"></i><strong>No documents match these filters.</strong><span>Try another search or choose a different category.</span></div>{% else %}<div class="public-library-empty"><i class="bi bi-folder2-open"></i><strong>No documents published yet</strong><span>Upload a PDF or DOCX file to make it available in the public library.</span></div>{% endif %}
    </section>
  </div>
</div>
<script>
(() => {
  const file = document.getElementById('public-doc-file');
  const fileName = document.getElementById('public-doc-selected-file');
  const search = document.getElementById('public-doc-search');
  const cards = [...document.querySelectorAll('.public-library-document')];
  const filters = [...document.querySelectorAll('[data-doc-category]')];
  const empty = document.getElementById('public-doc-empty');
  let category = 'all';
  file?.addEventListener('change', () => { if (fileName) fileName.textContent = file.files?.[0]?.name || 'No file selected'; });
  const apply = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const matches = (category === 'all' || card.dataset.docCategory === category) && (card.dataset.docSearch || '').includes(query);
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    if (empty) empty.hidden = visible > 0;
  };
  filters.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.docCategory || 'all';
    filters.forEach(item => {
      const selected = item === button;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    apply();
  }));
  search?.addEventListener('input', apply);
})();
</script>
"""

        return _render("Public documents", body, documents=documents, categories=categories, category_counts=category_counts, pdf_count=pdf_count, docx_count=docx_count, show_admin_sidebar=True, active_page="resources")

    @bp.route("/admin/resources/qr")
    @login_required
    def admin_qr_code():
        configured = (public_app_url or "").strip().rstrip("/")
        target_url = f"{configured}{url_for('ops.public_resources')}" if configured else ""
        body = """
<div class="top"><div><h1>Public document QR code</h1><p class="muted">Download this QR code and place it on your PDF documents. It links to the public document library.</p></div><a href="{{ url_for('ops.admin_public_documents') }}">Manage documents</a></div>
{% if target_url %}<div class="card p-4 text-center"><p><strong>QR destination:</strong> <a href="{{ target_url }}">{{ target_url }}</a></p><img class="mx-auto" style="width:280px;height:280px;object-fit:contain" src="{{ url_for('ops.admin_qr_png') }}" alt="QR code for the public document library"><div class="d-flex justify-content-center flex-wrap gap-2 mt-3"><a class="btn btn-primary" href="{{ url_for('ops.admin_qr_png', download=1) }}"><i class="bi bi-image me-1"></i>Download PNG</a><a class="btn btn-outline-primary" href="{{ url_for('ops.admin_qr_pdf') }}"><i class="bi bi-file-earmark-pdf me-1"></i>Download PDF</a></div></div>{% else %}<div class="alert alert-warning">Set <code>PUBLIC_APP_URL</code> in the app's <code>.env</code> to the live HTTPS base URL, restart the app, then download the QR code. For example: <code>PUBLIC_APP_URL=https://your-domain.example</code></div>{% endif %}
"""
        return _render("QR code", body, target_url=target_url, show_admin_sidebar=True, active_page="qr")

    @bp.route("/admin/resources/qr.png")
    @login_required
    def admin_qr_png():
        configured = (public_app_url or "").strip().rstrip("/")
        parsed = urlparse(configured)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            abort(503, "Configure PUBLIC_APP_URL to the live application URL first.")
        target_url = f"{configured}{url_for('ops.public_resources')}"
        download = request.args.get("download") == "1"
        try:
            import qrcode
            output = io.BytesIO()
            qrcode.make(target_url).save(output, format="PNG")
            output.seek(0)
            return send_file(output, mimetype="image/png", as_attachment=download, download_name="putzelf-public-resources-qr.png")
        except ImportError:
            try:
                from reportlab.graphics import renderSVG
                from reportlab.graphics.barcode.qr import QrCodeWidget
                from reportlab.graphics.shapes import Drawing
            except ImportError:
                abort(503, "Install qrcode[pil] or ReportLab to generate the QR code.")
            qr = QrCodeWidget(target_url)
            x1, y1, x2, y2 = qr.getBounds()
            width, height = x2 - x1, y2 - y1
            drawing = Drawing(width, height, transform=[1, 0, 0, 1, -x1, -y1])
            drawing.add(qr)
            output = io.BytesIO(renderSVG.drawToString(drawing).encode("utf-8"))
            return send_file(output, mimetype="image/svg+xml", as_attachment=download, download_name="putzelf-public-resources-qr.svg")

    @bp.route("/admin/resources/qr.pdf")
    @login_required
    def admin_qr_pdf():
        configured = (public_app_url or "").strip().rstrip("/")
        parsed = urlparse(configured)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            abort(503, "Configure PUBLIC_APP_URL to the live application URL first.")
        if not reportlab_available or pdf_canvas is None:
            abort(503, "Install ReportLab to generate a PDF QR code.")
        target_url = f"{configured}{url_for('ops.public_resources')}"
        try:
            from reportlab.graphics import renderPDF
            from reportlab.graphics.barcode.qr import QrCodeWidget
            from reportlab.graphics.shapes import Drawing
        except ImportError:
            abort(503, "ReportLab QR rendering support is unavailable on this server.")

        from reportlab.lib.colors import HexColor

        qr = QrCodeWidget(target_url)
        x1, y1, x2, y2 = qr.getBounds()
        qr_width, qr_height = x2 - x1, y2 - y1
        output = io.BytesIO()
        pdf = pdf_canvas.Canvas(output, pagesize=page_size)
        page_width, page_height = page_size
        primary = HexColor("#014D4E")
        primary_dark = HexColor("#003C3D")
        pale = HexColor("#EAF4F3")
        ink = HexColor("#193238")
        muted = HexColor("#66797C")
        margin = 30

        pdf.setTitle("Putzelf - QR-Code Dokumentenbibliothek")
        pdf.setAuthor("Putzelf")
        pdf.setFillColor(HexColor("#F4F8F8"))
        pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        # Branded header panel in the app's dark teal primary color.
        header_y = page_height - 207
        pdf.setFillColor(primary)
        pdf.roundRect(margin, header_y, page_width - 2 * margin, 181, 18, fill=1, stroke=0)
        pdf.setFillColor(primary_dark)
        pdf.circle(page_width - 74, page_height - 58, 42, fill=1, stroke=0)

        # Reuse the existing Putzelf logo when it is present in the deployment.
        logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
        logo_x, logo_y = 53, page_height - 101
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.roundRect(logo_x, logo_y, 88, 60, 10, fill=1, stroke=0)
        if os.path.isfile(logo_path):
            pdf.drawImage(
                logo_path,
                logo_x + 3,
                logo_y + 3,
                width=82,
                height=54,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(153, page_height - 68, "Putzelf")
        pdf.setFillColor(HexColor("#CDE5E2"))
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(53, page_height - 126, "\u00d6FFENTLICHE DOKUMENTENBIBLIOTHEK")
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawString(53, page_height - 151, "Sicherheits- und Arbeitsunterlagen")
        pdf.setFillColor(HexColor("#D9EAE8"))
        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(53, page_height - 172, "Wichtige Informationen f\u00fcr unsere Standorte - direkt am Smartphone.")

        # Compact white content card with a large, vector-sharp QR code.
        card_x = margin
        card_y = 83
        card_w = page_width - 2 * margin
        card_h = page_height - 235 - card_y
        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.roundRect(card_x, card_y, card_w, card_h, 18, fill=1, stroke=0)
        pdf.setFillColor(primary)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(page_width / 2, card_y + card_h - 43, "Dokumente f\u00fcr Ihren Arbeitsalltag")
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 9.5)
        pdf.drawCentredString(page_width / 2, card_y + card_h - 64, "Scannen Sie den QR-Code mit der Handykamera, um die aktuelle")
        pdf.drawCentredString(page_width / 2, card_y + card_h - 78, "Dokumentenbibliothek zu \u00f6ffnen.")

        qr_size = min(page_width, page_height) * 0.34
        scale = qr_size / max(qr_width, qr_height)
        qr_x = (page_width - qr_size) / 2
        qr_y = card_y + 135
        drawing = Drawing(
            qr_size,
            qr_size,
            transform=[scale, 0, 0, scale, -x1 * scale, -y1 * scale],
        )
        drawing.add(qr)
        renderPDF.draw(drawing, pdf, qr_x, qr_y)

        callout_x = 64
        callout_y = card_y + 29
        callout_w = page_width - 2 * callout_x
        pdf.setFillColor(pale)
        pdf.roundRect(callout_x, callout_y, callout_w, 58, 11, fill=1, stroke=0)
        pdf.setFillColor(primary)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(page_width / 2, callout_y + 36, "KEIN LOGIN ERFORDERLICH")
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(page_width / 2, callout_y + 19, "Freigegebene Dokumente jederzeit abrufen.")

        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(page_width / 2, 49, "putzelf.com | +43 676 6300167 | office@putzelf.com")
        pdf.save()
        output.seek(0)
        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="elfs-plan-public-documents-qr.pdf",
        )

    @bp.route("/admin/inspection-areas", methods=["GET", "POST"])
    @manager_required
    def admin_inspection_areas():
        selected_site_id = request.values.get("site_id", type=int)
        db = session_factory()
        try:
            sites = db.query(Site).order_by(Site.name.asc(), Site.id.asc()).all()
            selected_site = db.get(Site, selected_site_id) if selected_site_id else None
            if selected_site_id and not selected_site:
                abort(404)
            if request.method == "POST":
                if not selected_site:
                    abort(400)
                action = (request.form.get("action") or "add").strip().lower()
                area_id = request.form.get("area_id", type=int)
                area = None
                if area_id:
                    area = db.query(SiteInspectionArea).filter_by(id=area_id, site_id=selected_site.id).first()
                name = (request.form.get("name") or "").strip()[:160]
                if action == "add_all_suggestions":
                    existing_names = {
                        row[0].casefold()
                        for row in db.query(SiteInspectionArea.name).filter_by(site_id=selected_site.id).all()
                    }
                    missing_suggestions = [
                        suggestion for suggestion in suggested_areas
                        if suggestion.casefold() not in existing_names
                    ]
                    if missing_suggestions:
                        highest = db.query(func.max(SiteInspectionArea.sort_order)).filter_by(site_id=selected_site.id).scalar() or 0
                        for offset, suggestion in enumerate(missing_suggestions, start=1):
                            db.add(SiteInspectionArea(
                                site_id=selected_site.id,
                                name=suggestion,
                                sort_order=highest + offset,
                                is_active=True,
                            ))
                        db.commit()
                        flash("All missing suggested areas have been added.", "success")
                    else:
                        flash("All suggestions are already on this checklist.", "info")
                elif action == "archive_all":
                    active_areas = db.query(SiteInspectionArea).filter_by(
                        site_id=selected_site.id,
                        is_active=True,
                    ).all()
                    for active_area in active_areas:
                        active_area.is_active = False
                    if active_areas:
                        db.commit()
                        flash("All active areas for this site were archived.", "success")
                    else:
                        flash("There are no active areas to archive.", "info")
                elif action in {"add", "add_suggestion"}:
                    if action == "add_suggestion" and name not in suggested_areas:
                        abort(400)
                    duplicate = db.query(SiteInspectionArea.id).filter(
                        SiteInspectionArea.site_id == selected_site.id,
                        func.lower(SiteInspectionArea.name) == name.lower(),
                    ).first() if name else None
                    if not name:
                        flash("Enter an area name.", "warning")
                    elif duplicate:
                        flash("That area already exists for this site.", "warning")
                    else:
                        highest = db.query(func.max(SiteInspectionArea.sort_order)).filter_by(site_id=selected_site.id).scalar() or 0
                        db.add(SiteInspectionArea(site_id=selected_site.id, name=name, sort_order=highest + 1, is_active=True))
                        db.commit()
                        flash("Inspection area added to this site.", "success")
                elif area and action == "rename":
                    duplicate = db.query(SiteInspectionArea.id).filter(
                        SiteInspectionArea.site_id == selected_site.id,
                        func.lower(SiteInspectionArea.name) == name.lower(),
                        SiteInspectionArea.id != area.id,
                    ).first() if name else None
                    if name and not duplicate:
                        area.name = name
                        db.commit()
                        flash("Area renamed. Existing inspections keep their saved area names.", "success")
                    else:
                        flash("Enter a unique area name for this site.", "warning")
                elif area and action in {"archive", "restore"}:
                    area.is_active = action == "restore"
                    db.commit()
                    flash("Site inspection areas updated.", "success")
                return redirect(url_for("ops.admin_inspection_areas", site_id=selected_site.id))

            area_counts = {
                site.id: db.query(SiteInspectionArea.id).filter_by(site_id=site.id, is_active=True).count()
                for site in sites
            }
            configured_site_count = sum(count > 0 for count in area_counts.values())
            sites_needing_setup_count = len(sites) - configured_site_count
            total_active_area_count = sum(area_counts.values())
            areas = db.query(SiteInspectionArea).filter_by(site_id=selected_site.id).order_by(
                SiteInspectionArea.is_active.desc(), SiteInspectionArea.sort_order, SiteInspectionArea.id
            ).all() if selected_site else []
            existing_area_names = {area.name.casefold() for area in areas}
            active_area_count = sum(1 for area in areas if area.is_active)
            archived_area_count = len(areas) - active_area_count
            available_suggestion_count = sum(1 for suggestion in suggested_areas if suggestion.casefold() not in existing_area_names)
        finally:
            db.close()
        body = """
{% if selected_site %}
<div class="inspection-site-editor">
  <header class="inspection-editor-header"><div><a class="inspection-editor-back" href="{{ url_for('ops.admin_inspection_areas') }}"><i class="bi bi-arrow-left"></i> All sites</a><span class="inspection-index-eyebrow"><i class="bi bi-clipboard2-check"></i> Site checklist</span><h1>{{ selected_site.profile_company_name or selected_site.name }}</h1><p>Choose the areas that apply to this site. Active areas appear in each new monthly inspection.</p></div><a class="btn btn-outline-secondary" href="{{ url_for('admin_sites') }}"><i class="bi bi-building"></i> Site details</a></header>
  <section class="inspection-editor-stats" aria-label="Checklist summary"><article><span class="is-ready"><i class="bi bi-check2-circle"></i></span><div><small>Active areas</small><strong>{{ active_area_count }}</strong></div></article><article><span><i class="bi bi-archive"></i></span><div><small>Archived</small><strong>{{ archived_area_count }}</strong></div></article><article><span class="is-suggestion"><i class="bi bi-lightbulb"></i></span><div><small>Suggestions available</small><strong>{{ available_suggestion_count }}</strong></div></article></section>
  <section class="inspection-editor-add"><div class="inspection-editor-section-title"><span class="inspection-editor-section-icon"><i class="bi bi-plus-lg"></i></span><div><h2>Add an inspection area</h2><p>Create a custom area for this site.</p></div></div><form method="post" class="inspection-area-add-form"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="action" value="add"><label class="visually-hidden" for="new-inspection-area">Area name</label><input id="new-inspection-area" class="form-control" name="name" maxlength="160" placeholder="e.g. Loading bay, stairwell, or patient rooms" required><button class="btn btn-primary" type="submit"><i class="bi bi-plus-lg"></i> Add area</button></form></section>
  <section class="inspection-editor-suggestions"><div class="inspection-editor-suggestions-head"><div class="inspection-editor-section-title"><span class="inspection-editor-section-icon is-soft"><i class="bi bi-stars"></i></span><div><h2>Common suggestions</h2><p>Add only what applies. You can rename areas below at any time.</p></div></div>{% if available_suggestion_count %}<form method="post" class="inspection-editor-bulk-form"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="action" value="add_all_suggestions"><button class="btn btn-sm btn-primary" type="submit"><i class="bi bi-plus-circle"></i> Add all missing suggestions</button></form>{% endif %}</div><div class="inspection-suggestion-list">{% for suggestion in suggested_areas %}{% if (suggestion|lower) not in existing_area_names %}<form method="post"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="action" value="add_suggestion"><input type="hidden" name="name" value="{{ suggestion }}"><button type="submit" class="inspection-suggestion-chip"><i class="bi bi-plus-circle"></i>{{ suggestion }}</button></form>{% endif %}{% endfor %}{% if not available_suggestion_count %}<span class="inspection-suggestions-done"><i class="bi bi-check2"></i> All suggestions are already on this checklist.</span>{% endif %}</div></section>
  <section class="inspection-editor-list"><div class="inspection-editor-list-head"><div class="inspection-editor-section-title"><span class="inspection-editor-section-icon"><i class="bi bi-list-check"></i></span><div><h2>Checklist areas</h2><p>Rename, archive, or restore areas for this site.</p></div></div><div class="inspection-editor-list-tools"><label class="inspection-area-search"><i class="bi bi-search"></i><input id="inspection-area-search" type="search" placeholder="Search areas" aria-label="Search areas"></label><div class="inspection-area-filters" role="group" aria-label="Filter checklist areas"><button type="button" data-area-filter="all" class="is-active" aria-pressed="true">All <span>{{ areas|length }}</span></button><button type="button" data-area-filter="active" aria-pressed="false">Active <span>{{ active_area_count }}</span></button><button type="button" data-area-filter="archived" aria-pressed="false">Archived <span>{{ archived_area_count }}</span></button></div></div></div>
    {% if active_area_count %}<div class="inspection-editor-bulk-actions"><form method="post" class="inspection-editor-bulk-form" onsubmit="return confirm('Archive all active inspection areas for this site? You can restore them later.')"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="action" value="archive_all"><button class="btn btn-sm btn-outline-secondary" type="submit"><i class="bi bi-archive"></i> Archive all active</button></form></div>{% endif %}
    <div class="inspection-area-rows" id="inspection-area-rows">{% for area in areas %}<article class="inspection-area-row" data-area-status="{{ 'active' if area.is_active else 'archived' }}" data-area-name="{{ area.name|lower|e }}"><span class="inspection-area-row-icon {{ 'is-active' if area.is_active else '' }}"><i class="bi {{ 'bi-check2' if area.is_active else 'bi-archive' }}"></i></span><form method="post" class="inspection-area-rename-form"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="area_id" value="{{ area.id }}"><input type="hidden" name="action" value="rename"><label class="visually-hidden" for="inspection-area-{{ area.id }}">Area name</label><input id="inspection-area-{{ area.id }}" class="form-control" name="name" value="{{ area.name }}" maxlength="160" required><span class="inspection-area-status {{ 'is-active' if area.is_active else '' }}">{{ 'Active' if area.is_active else 'Archived' }}</span><button class="btn btn-sm btn-outline-primary" type="submit"><i class="bi bi-check2"></i> Save</button></form><form method="post" class="inspection-area-state-form"><input type="hidden" name="site_id" value="{{ selected_site.id }}"><input type="hidden" name="area_id" value="{{ area.id }}"><input type="hidden" name="action" value="{{ 'archive' if area.is_active else 'restore' }}"><button class="btn btn-sm {{ 'btn-light' if area.is_active else 'btn-outline-primary' }}" type="submit"><i class="bi {{ 'bi-archive' if area.is_active else 'bi-arrow-counterclockwise' }}"></i> {{ 'Archive' if area.is_active else 'Restore' }}</button></form></article>{% else %}<div class="inspection-area-list-empty"><i class="bi bi-clipboard2-plus"></i><strong>No inspection areas yet</strong><span>Add a custom area or choose from the suggestions above.</span></div>{% endfor %}</div><div class="inspection-area-filter-empty" id="inspection-area-filter-empty" hidden>No checklist areas match this search.</div>
  </section>
</div>
<script>
(() => {
  const search = document.getElementById('inspection-area-search');
  const rows = [...document.querySelectorAll('.inspection-area-row')];
  const filters = [...document.querySelectorAll('[data-area-filter]')];
  const empty = document.getElementById('inspection-area-filter-empty');
  let status = 'all';
  const update = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let visible = 0;
    rows.forEach(row => {
      const show = (status === 'all' || row.dataset.areaStatus === status) && (row.dataset.areaName || '').includes(query);
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (empty) empty.hidden = visible > 0 || rows.length === 0;
  };
  filters.forEach(button => button.addEventListener('click', () => {
    status = button.dataset.areaFilter || 'all';
    filters.forEach(item => {
      const selected = item === button;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    update();
  }));
  search?.addEventListener('input', update);
})();
</script>
{% else %}
<div class="inspection-area-index">
  <header class="inspection-index-header">
    <div><span class="inspection-index-eyebrow"><i class="bi bi-clipboard2-check"></i> Inspection setup</span><h1>Inspection areas by site</h1><p>Each site has its own checklist. Set up only the areas that apply to that location.</p></div>
    <div class="inspection-index-header-actions"><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_inspection_report') }}"><i class="bi bi-file-earmark-bar-graph"></i> Inspection report</a><a class="btn btn-primary" href="{{ url_for('admin_sites') }}"><i class="bi bi-buildings"></i> Manage sites</a></div>
  </header>
  <section class="inspection-index-stats" aria-label="Inspection area setup summary">
    <article class="inspection-index-stat"><span class="inspection-index-stat-icon"><i class="bi bi-buildings"></i></span><div><span>Sites</span><strong>{{ sites|length }}</strong></div></article>
    <article class="inspection-index-stat"><span class="inspection-index-stat-icon is-ready"><i class="bi bi-check2-circle"></i></span><div><span>Ready for inspections</span><strong>{{ configured_site_count }}</strong></div></article>
    <article class="inspection-index-stat"><span class="inspection-index-stat-icon is-pending"><i class="bi bi-exclamation-circle"></i></span><div><span>Needs areas</span><strong>{{ sites_needing_setup_count }}</strong></div></article>
    <article class="inspection-index-stat"><span class="inspection-index-stat-icon"><i class="bi bi-list-check"></i></span><div><span>Active areas</span><strong>{{ total_active_area_count }}</strong></div></article>
  </section>
  {% if sites %}
  <section class="inspection-index-browser" aria-label="Find and filter sites">
    <div class="inspection-index-search"><i class="bi bi-search" aria-hidden="true"></i><input id="inspection-site-search" type="search" placeholder="Search by site name or address" aria-label="Search by site name or address"><kbd>⌘ K</kbd></div>
    <div class="inspection-index-filter-group" role="group" aria-label="Filter sites by area setup">
      <button type="button" class="inspection-index-filter is-active" data-inspection-filter="all" aria-pressed="true">All sites <span>{{ sites|length }}</span></button>
      <button type="button" class="inspection-index-filter" data-inspection-filter="ready" aria-pressed="false">Ready <span>{{ configured_site_count }}</span></button>
      <button type="button" class="inspection-index-filter" data-inspection-filter="setup" aria-pressed="false">Needs setup <span>{{ sites_needing_setup_count }}</span></button>
    </div>
    <div class="inspection-index-result" aria-live="polite"><strong id="inspection-site-result-count">{{ sites|length }}</strong><span>sites shown</span></div>
  </section>
  <section class="inspection-site-grid" id="inspection-site-grid" aria-label="Sites and inspection checklists">
    {% for site in sites %}{% set active_area_count = area_counts[site.id] %}
    <article class="inspection-site-card" data-area-state="{{ 'ready' if active_area_count else 'setup' }}" data-search="{{ ((site.profile_company_name or site.name) ~ ' ' ~ (site.address or ''))|lower|e }}">
      <div class="inspection-site-card-top"><span class="inspection-site-icon"><i class="bi bi-building"></i></span><span class="inspection-site-state {{ 'is-ready' if active_area_count else 'is-pending' }}"><span></span>{{ 'Ready for inspections' if active_area_count else 'Needs setup' }}</span></div>
      <div class="inspection-site-card-copy"><h2>{{ site.profile_company_name or site.name }}</h2><p>{{ site.address or 'No address added' }}</p></div>
      <div class="inspection-site-card-footer"><span><i class="bi bi-list-check"></i>{{ active_area_count }} {{ 'active areas' if active_area_count != 1 else 'active area' }}</span><a href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}" aria-label="Manage inspection areas for {{ site.profile_company_name or site.name }}">{{ 'Manage areas' if active_area_count else 'Set up checklist' }}<i class="bi bi-arrow-right"></i></a></div>
    </article>
    {% endfor %}
  </section>
  <div class="inspection-index-no-results" id="inspection-site-no-results" hidden><i class="bi bi-search"></i><strong>No sites match these filters.</strong><span>Try a different search or show all sites.</span></div>
  <script>
    (() => {
      const search = document.getElementById('inspection-site-search');
      const cards = [...document.querySelectorAll('.inspection-site-card')];
      const filters = [...document.querySelectorAll('[data-inspection-filter]')];
      const count = document.getElementById('inspection-site-result-count');
      const empty = document.getElementById('inspection-site-no-results');
      let activeFilter = 'all';
      const apply = () => {
        const query = (search?.value || '').trim().toLocaleLowerCase();
        let visible = 0;
        cards.forEach(card => {
          const matches = (activeFilter === 'all' || card.dataset.areaState === activeFilter) && (card.dataset.search || '').includes(query);
          card.hidden = !matches;
          if (matches) visible += 1;
        });
        if (count) count.textContent = String(visible);
        if (empty) empty.hidden = visible > 0;
      };
      filters.forEach(button => button.addEventListener('click', () => {
        activeFilter = button.dataset.inspectionFilter || 'all';
        filters.forEach(item => {
          const selected = item === button;
          item.classList.toggle('is-active', selected);
          item.setAttribute('aria-pressed', String(selected));
        });
        apply();
      }));
      search?.addEventListener('input', apply);
      document.addEventListener('keydown', event => {
        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
          event.preventDefault();
          search?.focus();
        }
      });
    })();
  </script>
  {% else %}<div class="inspection-index-empty"><span><i class="bi bi-buildings"></i></span><h2>No sites to configure yet</h2><p>Add a site first, then build its inspection checklist.</p><a class="btn btn-primary" href="{{ url_for('admin_sites') }}"><i class="bi bi-plus-lg"></i> Add a site</a></div>{% endif %}
</div>
{% endif %}
"""
        return _render("Inspection areas by site", body, sites=sites, selected_site=selected_site, areas=areas, area_counts=area_counts, configured_site_count=configured_site_count, sites_needing_setup_count=sites_needing_setup_count, total_active_area_count=total_active_area_count, active_area_count=active_area_count, archived_area_count=archived_area_count, available_suggestion_count=available_suggestion_count, suggested_areas=suggested_areas, existing_area_names=existing_area_names, show_admin_sidebar=True, active_page="inspection_areas")

    @bp.route("/manager/inspections")
    @manager_required
    def manager_inspections():
        month = _period(request.args.get("month"))
        db = session_factory()
        try:
            query = db.query(Site)
            if not _is_main_admin():
                query = query.filter(Site.manager_employee_id == session.get("employee_id"))
            sites = query.order_by(Site.name.asc()).all()
            summaries = []
            for site in sites:
                inspection = db.query(SiteInspection).filter_by(site_id=site.id, month=month).first()
                configured_count = db.query(SiteInspectionArea.id).filter_by(site_id=site.id, is_active=True).count()
                current_items = _inspection_items(inspection)
                total = len(current_items) if current_items else configured_count
                checked = sum(bool(item.checked) for item in current_items)
                summaries.append({"site": site, "inspection": inspection, "total": total, "checked": checked, "status": _inspection_status(inspection, configured_count)})
        finally:
            db.close()
        body = """
<div class="top"><div><h1>Monthly site inspections</h1><p class="muted">Check each assigned site once per month using the areas configured for that site.</p></div><a href="{{ url_for('ops.site_manager_home') }}">Operations home</a></div>
<form method="get" class="card p-3 mb-3 d-flex flex-row gap-2 align-items-end"><label class="flex-grow-1">Month<input type="month" class="form-control" name="month" value="{{ month }}"></label><button class="btn btn-primary">View month</button></form>
<div class="card p-3">{% for row in summaries %}<div class="list-group-item d-flex justify-content-between align-items-center gap-3"><div><strong>{{ row.site.profile_company_name or row.site.name }}</strong><div class="muted">{{ row.site.address or '' }}</div></div><div class="text-end"><span class="tag">{{ row.status }}</span><div class="small muted">{{ row.checked }} / {{ row.total }} areas</div></div>{% if row.total %}<a class="btn btn-sm btn-primary" href="{{ url_for('ops.manager_inspection_detail', site_id=row.site.id, month=month) }}">Open checklist</a>{% else %}<a class="btn btn-sm btn-outline-secondary" href="{{ url_for('ops.admin_inspection_areas', site_id=row.site.id) }}">Set up areas</a>{% endif %}</div>{% else %}<p class="muted mb-0">No sites are assigned to this account.</p>{% endfor %}</div>
"""
        return _render("Monthly inspections", body, month=month, summaries=summaries, show_admin_sidebar=True, active_page="inspection")

    @bp.route("/manager/inspections/<int:site_id>", methods=["GET", "POST"])
    @manager_required
    def manager_inspection_detail(site_id: int):
        month = _period(request.values.get("month"))
        db = session_factory()
        try:
            site = db.get(Site, site_id)
            if not site:
                abort(404)
            if not _site_is_available_to_manager(site):
                abort(403)
            configured_count = db.query(SiteInspectionArea.id).filter_by(site_id=site.id, is_active=True).count()
            inspection = _find_or_create_inspection(db, site, month)
            db.commit()
            if request.method == "POST":
                if not inspection:
                    flash("Add inspection areas for this site before starting its inspection.", "warning")
                    return redirect(url_for("ops.admin_inspection_areas", site_id=site.id))
                checked_ids = {int(value) for value in request.form.getlist("checked_item") if value.isdigit()}
                for item in _inspection_items(inspection):
                    item.checked = item.id in checked_ids
                    item.checked_at = datetime.utcnow() if item.checked else None
                    item.notes = (request.form.get(f"notes_{item.id}") or "").strip()[:4000] or None
                    photo = request.files.get(f"photo_{item.id}")
                    if photo and photo.filename:
                        original = secure_filename(photo.filename)
                        extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
                        if extension not in {"png", "jpg", "jpeg", "webp"}:
                            flash("Inspection photos must be PNG, JPG, or WEBP.", "warning")
                        else:
                            stored = f"inspection_{item.id}_{secrets.token_hex(12)}.{extension}"
                            photo.save(os.path.join(inspection_photo_folder, stored))
                            if item.photo_path:
                                try:
                                    os.remove(os.path.join(inspection_photo_folder, os.path.basename(item.photo_path)))
                                except OSError:
                                    pass
                            item.photo_path = stored
                inspection.inspected_by_employee_id = session.get("employee_id") if not _is_main_admin() else None
                inspection.updated_at = datetime.utcnow()
                db.commit()
                flash("Inspection saved.", "success")
                return redirect(url_for("ops.manager_inspection_detail", site_id=site.id, month=month))
            items = _inspection_items(inspection)
            status = _inspection_status(inspection, configured_count)
            checked_area_count = sum(bool(item.checked) for item in items)
            area_count = len(items)
            # The session closes below; keep template data as plain values so
            # SQLAlchemy never has to refresh a detached Site instance.
            site_id_value = site.id
            site_name = site.profile_company_name or site.name
            site_address = site.address or ""
        finally:
            db.close()
        body = """
<div class="top"><div><div class="muted">{{ month }} | {{ status }}</div><h1>{{ site_name }}</h1><p class="muted">{{ site_address }} | {{ items|selectattr('checked')|list|length }} / {{ items|length }} areas checked</p></div><a class="btn btn-outline-secondary" href="{{ url_for('ops.manager_inspections', month=month) }}">All inspections</a></div>
{% if not items %}<div class="alert alert-warning">No inspection areas are configured for this site yet. Add the areas that apply to this location before beginning its monthly inspection.<p class="mt-3 mb-0"><a class="btn btn-primary" href="{{ url_for('ops.admin_inspection_areas', site_id=site_id) }}">Manage this site's areas</a></p></div>{% else %}
<div class="inspection-checklist-toolbar"><div class="inspection-checklist-progress-copy"><span class="inspection-index-stat-icon is-ready"><i class="bi bi-check2-circle"></i></span><div><strong><span id="inspection-checked-count">{{ checked_area_count }}</span> / {{ area_count }} <span>areas checked</span></strong><small>Use the quick actions or check areas one by one.</small></div></div><div class="inspection-checklist-quick-actions"><button type="button" class="btn btn-sm btn-outline-primary" id="inspection-check-all"><i class="bi bi-check2-all"></i> Mark all checked</button><button type="button" class="btn btn-sm btn-outline-secondary" id="inspection-clear-all"><i class="bi bi-arrow-counterclockwise"></i> Clear all checks</button></div><div class="inspection-checklist-progress-track"><span id="inspection-progress-fill" style="width:{{ ((checked_area_count / area_count * 100)|round|int) if area_count else 0 }}%"></span></div></div>
<form class="inspection-checklist-form" id="manager-inspection-form" method="post" enctype="multipart/form-data"><input type="hidden" name="month" value="{{ month }}">{% for item in items %}<section class="inspection-check-area {{ 'is-checked' if item.checked else '' }}" data-inspection-area><div class="inspection-check-area-head"><input class="form-check-input inspection-area-checkbox" type="checkbox" name="checked_item" value="{{ item.id }}" id="item-{{ item.id }}" {% if item.checked %}checked{% endif %}><label class="inspection-check-area-name" for="item-{{ item.id }}"><span>{{ item.area_name }}</span><small class="inspection-area-status-label">{{ 'Checked' if item.checked else 'Not checked' }}</small></label><details class="inspection-area-extra" {% if item.notes or item.photo_path %}open{% endif %}><summary><i class="bi bi-chat-left-text"></i><span>{{ 'Edit note and photo' if item.notes or item.photo_path else 'Add note or photo' }}</span><i class="bi bi-chevron-down"></i></summary><div class="inspection-area-extra-fields"><label><span>Optional note</span><textarea class="form-control" name="notes_{{ item.id }}" rows="2" maxlength="4000" placeholder="Add a note about this area">{{ item.notes or '' }}</textarea></label><label><span>Optional photo</span><input class="form-control" type="file" name="photo_{{ item.id }}" accept="image/png,image/jpeg,image/webp">{% if item.photo_path %}<a class="small" href="{{ url_for('ops.inspection_photo', item_id=item.id) }}"><i class="bi bi-image"></i> View saved photo</a>{% endif %}</label></div></details></div></section>{% endfor %}
<div class="inspection-checklist-savebar"><span><i class="bi bi-cloud-check"></i> Inspection changes save to the selected month.</span><button class="btn btn-primary" type="submit"><i class="bi bi-check2-circle"></i> Save inspection</button></div></form>
<script>
(() => {
  const checkboxes = [...document.querySelectorAll('.inspection-area-checkbox')];
  const count = document.getElementById('inspection-checked-count');
  const fill = document.getElementById('inspection-progress-fill');
  const checkedLabel = {{ ('Kontrolliert' if current_lang == 'de' else 'Checked')|tojson }};
  const uncheckedLabel = {{ ('Nicht kontrolliert' if current_lang == 'de' else 'Not checked')|tojson }};
  const update = () => {
    const checked = checkboxes.filter(box => box.checked).length;
    if (count) count.textContent = String(checked);
    if (fill) fill.style.width = `${checkboxes.length ? checked / checkboxes.length * 100 : 0}%`;
    checkboxes.forEach(box => {
      const card = box.closest('[data-inspection-area]');
      card?.classList.toggle('is-checked', box.checked);
      const label = card?.querySelector('.inspection-area-status-label');
      if (label) label.textContent = box.checked ? checkedLabel : uncheckedLabel;
    });
  };
  document.getElementById('inspection-check-all')?.addEventListener('click', () => { checkboxes.forEach(box => { box.checked = true; }); update(); });
  document.getElementById('inspection-clear-all')?.addEventListener('click', () => { checkboxes.forEach(box => { box.checked = false; }); update(); });
  checkboxes.forEach(box => box.addEventListener('change', update));
})();
</script>{% endif %}
"""
        return _render("Site inspection", body, month=month, site_id=site_id_value, site_name=site_name, site_address=site_address, items=items, status=status, checked_area_count=checked_area_count, area_count=area_count, show_admin_sidebar=True, active_page="inspection")

    @bp.route("/manager/inspections/photo/<int:item_id>")
    @manager_required
    def inspection_photo(item_id: int):
        db = session_factory()
        try:
            item = db.get(InspectionItem, item_id)
            if not item:
                abort(404)
            inspection = db.get(SiteInspection, item.inspection_id)
            site = db.get(Site, inspection.site_id) if inspection else None
            if not site or not _site_is_available_to_manager(site) or not item.photo_path:
                abort(404)
            path = os.path.join(inspection_photo_folder, os.path.basename(item.photo_path))
            if not os.path.isfile(path):
                abort(404)
            return send_file(path)
        finally:
            db.close()

    @bp.route("/admin/inspection-report")
    @login_required
    def admin_inspection_report():
        month = _period(request.args.get("month"))
        db = session_factory()
        try:
            rows = _report_rows(db, month)
        finally:
            db.close()
        report_stats = {
            "sites": len(rows),
            "complete": sum(row["status"] == "Complete" for row in rows),
            "in_progress": sum(row["status"] == "In progress" for row in rows),
            "not_started": sum(row["status"] == "Not started" for row in rows),
            "needs_setup": sum(row["status"] == "Checklist not configured" for row in rows),
            "checked_areas": sum(area["checked"] for row in rows for area in row["areas"]),
            "total_areas": sum(len(row["areas"]) for row in rows),
        }
        body = """
<div class="inspection-report-page">
  <header class="inspection-report-header"><div><span class="inspection-index-eyebrow"><i class="bi bi-file-earmark-bar-graph"></i> Inspection overview</span><h1>Monthly inspection report</h1><p>Track completion by site and see which areas still need attention.</p></div><div class="inspection-index-header-actions"><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_inspection_areas') }}"><i class="bi bi-list-check"></i> Edit checklists</a><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_public_documents') }}"><i class="bi bi-folder2-open"></i> Public documents</a></div></header>
  <section class="inspection-report-toolbar"><form method="get" class="inspection-report-month"><label for="inspection-report-month">Report month</label><input id="inspection-report-month" type="month" class="form-control" name="month" value="{{ month }}"><button class="btn btn-primary" type="submit"><i class="bi bi-calendar2-check"></i> View report</button></form><div class="inspection-report-exports"><span>Download report</span><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_inspection_csv', month=month) }}"><i class="bi bi-filetype-csv"></i> CSV</a><a class="btn btn-outline-secondary" href="{{ url_for('ops.admin_inspection_pdf', month=month) }}"><i class="bi bi-filetype-pdf"></i> PDF</a></div></section>
  <section class="inspection-report-stats" aria-label="Report summary"><article><span class="is-teal"><i class="bi bi-buildings"></i></span><div><small>Sites</small><strong>{{ report_stats.sites }}</strong></div></article><article><span class="is-green"><i class="bi bi-check2-circle"></i></span><div><small>Complete</small><strong>{{ report_stats.complete }}</strong></div></article><article><span class="is-amber"><i class="bi bi-hourglass-split"></i></span><div><small>In progress</small><strong>{{ report_stats.in_progress }}</strong></div></article><article><span class="is-muted"><i class="bi bi-circle"></i></span><div><small>Not started</small><strong>{{ report_stats.not_started }}</strong></div></article><article><span class="is-red"><i class="bi bi-exclamation-circle"></i></span><div><small>Needs setup</small><strong>{{ report_stats.needs_setup }}</strong></div></article><article><span class="is-teal"><i class="bi bi-list-check"></i></span><div><small>Areas checked</small><strong>{{ report_stats.checked_areas }} / {{ report_stats.total_areas }}</strong></div></article></section>
  {% if rows %}<section class="inspection-report-browser"><label class="inspection-area-search"><i class="bi bi-search"></i><input id="inspection-report-search" type="search" placeholder="Search sites or areas" aria-label="Search sites or areas"></label><div class="inspection-report-filters" role="group" aria-label="Filter sites by inspection status"><button type="button" class="is-active" data-report-filter="all" aria-pressed="true">All <span>{{ report_stats.sites }}</span></button><button type="button" data-report-filter="attention" aria-pressed="false">Needs attention <span>{{ report_stats.in_progress + report_stats.not_started + report_stats.needs_setup }}</span></button><button type="button" data-report-filter="complete" aria-pressed="false">Complete <span>{{ report_stats.complete }}</span></button><button type="button" data-report-filter="setup" aria-pressed="false">Needs setup <span>{{ report_stats.needs_setup }}</span></button></div><span class="inspection-report-result"><strong id="inspection-report-result-count">{{ report_stats.sites }}</strong> sites</span></section>
  <div class="inspection-report-cards" id="inspection-report-cards">{% for row in rows %}{% set area_total = row.areas|length %}{% set area_checked = row.areas|selectattr('checked')|list|length %}{% set progress = ((area_checked / area_total * 100)|round|int) if area_total else 0 %}{% set status_key = 'complete' if row.status == 'Complete' else ('setup' if row.status == 'Checklist not configured' else ('attention' if row.status == 'In progress' else 'not-started')) %}
    <details class="inspection-report-card" data-report-status="{{ status_key }}" data-report-search="{{ ((row.site.profile_company_name or row.site.name) ~ ' ' ~ (row.site.address or '') ~ ' ' ~ (row.areas|map(attribute='area')|join(' ')))|lower|e }}"><summary class="inspection-report-card-head"><span class="inspection-report-site-icon"><i class="bi bi-building"></i></span><div class="inspection-report-site-name"><h2>{{ row.site.profile_company_name or row.site.name }}</h2><p>{{ row.site.address or 'No address added' }}</p></div><span class="inspection-report-status {{ 'is-complete' if status_key == 'complete' else ('is-setup' if status_key == 'setup' else ('is-progress' if status_key == 'attention' else 'is-not-started')) }}"><i class="bi {{ 'bi-check-circle-fill' if status_key == 'complete' else ('bi-exclamation-circle-fill' if status_key == 'setup' else ('bi-arrow-repeat' if status_key == 'attention' else 'bi-circle')) }}"></i>{{ row.status }}</span><span class="inspection-report-summary-progress">{{ area_checked }} / {{ area_total }} <span>areas</span></span><i class="bi bi-chevron-down inspection-report-chevron"></i></summary><div class="inspection-report-card-content">
      {% if area_total %}<div class="inspection-report-progress"><div><span>Inspection progress</span><strong>{{ area_checked }} / {{ area_total }} areas</strong></div><div class="inspection-report-progress-track"><span style="width:{{ progress }}%"></span></div></div><div class="inspection-report-area-list">{% for area in row.areas %}<div class="inspection-report-area {{ 'is-checked' if area.checked else 'is-unchecked' }}"><span class="inspection-report-area-mark"><i class="bi {{ 'bi-check2' if area.checked else 'bi-circle' }}"></i></span><span class="inspection-report-area-name">{{ area.area }}</span><span class="inspection-report-area-state">{{ 'Checked' if area.checked else 'Not checked' }}</span>{% if area.notes %}<span class="inspection-report-area-note" title="{{ area.notes }}"><i class="bi bi-chat-left-text"></i>{{ area.notes }}</span>{% endif %}</div>{% endfor %}</div>{% else %}<div class="inspection-report-unconfigured"><i class="bi bi-clipboard2-x"></i><span>No checklist areas configured.</span><a href="{{ url_for('ops.admin_inspection_areas', site_id=row.site.id) }}">Set up checklist <i class="bi bi-arrow-right"></i></a></div>{% endif %}
      <footer class="inspection-report-card-foot">{% if row.inspection %}<span><i class="bi bi-clock-history"></i> Updated {{ row.inspection.updated_at.strftime('%d.%m.%Y %H:%M') }}{% if row.inspector_name %} by {{ row.inspector_name }}{% endif %}</span>{% else %}<span><i class="bi bi-info-circle"></i> No inspection submitted this month</span>{% endif %}<a href="{{ url_for('ops.admin_inspection_areas', site_id=row.site.id) }}">Manage areas <i class="bi bi-arrow-right"></i></a></footer></div>
    </details>{% endfor %}</div><div class="inspection-report-empty" id="inspection-report-empty" hidden><i class="bi bi-search"></i><strong>No sites match this search or filter.</strong><span>Try a different search or select all sites.</span></div>{% else %}<div class="inspection-report-empty"><i class="bi bi-buildings"></i><strong>No sites are in the database.</strong><span>Add a site to start tracking inspections.</span><a class="btn btn-primary" href="{{ url_for('admin_sites') }}"><i class="bi bi-plus-lg"></i> Add a site</a></div>{% endif %}
</div>
<script>
(() => {
  const search = document.getElementById('inspection-report-search');
  const cards = [...document.querySelectorAll('.inspection-report-card')];
  const filters = [...document.querySelectorAll('[data-report-filter]')];
  const count = document.getElementById('inspection-report-result-count');
  const empty = document.getElementById('inspection-report-empty');
  let filter = 'all';
  const apply = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const status = card.dataset.reportStatus || '';
      const matchesFilter = filter === 'all' || (filter === 'attention' ? ['attention', 'not-started', 'setup'].includes(status) : status === filter);
      const matchesSearch = (card.dataset.reportSearch || '').includes(query);
      card.hidden = !(matchesFilter && matchesSearch);
      if (!card.hidden) visible += 1;
    });
    if (count) count.textContent = String(visible);
    if (empty) empty.hidden = visible > 0;
  };
  filters.forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.reportFilter || 'all';
    filters.forEach(item => {
      const selected = item === button;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    apply();
  }));
  search?.addEventListener('input', apply);
})();
</script>
"""
        return _render("Inspection report", body, rows=rows, month=month, report_stats=report_stats, show_admin_sidebar=True, active_page="inspection_report")

    @bp.route("/admin/inspection-report.csv")
    @login_required
    def admin_inspection_csv():
        month = _period(request.args.get("month"))
        db = session_factory()
        try:
            rows = _report_rows(db, month)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Month", "Site", "Address", "Inspection status", "Area", "Area status", "Notes", "Last updated", "Inspector"])
            for row in rows:
                inspection = row["inspection"]
                if not row["areas"]:
                    writer.writerow([month, row["site"].profile_company_name or row["site"].name, row["site"].address or "", row["status"], "", "Not configured", "", inspection.updated_at.isoformat() if inspection else "", row["inspector_name"]])
                    continue
                for area in row["areas"]:
                    writer.writerow([month, row["site"].profile_company_name or row["site"].name, row["site"].address or "", row["status"], area["area"], "Checked" if area["checked"] else "Not checked", area["notes"], inspection.updated_at.isoformat() if inspection else "", row["inspector_name"]])
            data = "\ufeff" + output.getvalue()
        finally:
            db.close()
        return send_file(io.BytesIO(data.encode("utf-8")), mimetype="text/csv; charset=utf-8", as_attachment=True, download_name=f"inspection-report-{month}.csv")

    @bp.route("/admin/inspection-report.pdf")
    @login_required
    def admin_inspection_pdf():
        if not reportlab_available:
            abort(503, "Install reportlab to download the PDF report.")
        month = _period(request.args.get("month"))
        db = session_factory()
        try:
            rows = _report_rows(db, month)
            output = io.BytesIO()
            pdf = pdf_canvas.Canvas(output, pagesize=page_size)
            width, height = page_size
            y = height - 48
            pdf.setTitle(f"Site inspection report {month}")
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(42, y, f"Monthly Site Inspection Report · {month}")
            y -= 30
            for row in rows:
                if y < 90:
                    pdf.showPage(); y = height - 48
                pdf.setFont("Helvetica-Bold", 11)
                pdf.drawString(42, y, f"{row['site'].profile_company_name or row['site'].name} — {row['status']}")
                y -= 17
                pdf.setFont("Helvetica", 9)
                if not row["areas"]:
                    pdf.drawString(52, y, "No inspection areas configured for this site")
                    y -= 13
                for area in row["areas"]:
                    line = f"[{'X' if area['checked'] else ' '}] {area['area']}"
                    if area["notes"]:
                        line += f" — {area['notes'][:100]}"
                    pdf.drawString(52, y, line[:125])
                    y -= 13
                    if y < 48:
                        pdf.showPage(); y = height - 48
                y -= 10
            pdf.save()
            output.seek(0)
            return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"inspection-report-{month}.pdf")
        finally:
            db.close()

    return bp
