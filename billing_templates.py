"""Invoice and billing page templates."""

INVOICE_LIST_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Invoices</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-danger: linear-gradient(135deg,#f87171 0%,#ef4444 50%,#dc2626 100%);
      --btn-grad-danger-hover: linear-gradient(135deg,#ef4444 0%,#dc2626 50%,#b91c1c 100%);
      --btn-grad-info: linear-gradient(135deg,#38bdf8 0%,#0ea5e9 50%,#2563eb 100%);
      --btn-grad-info-hover: linear-gradient(135deg,#0ea5e9 0%,#2563eb 50%,#1d4ed8 100%);
      --btn-grad-success: linear-gradient(135deg,#22c55e 0%,#16a34a 50%,#15803d 100%);
      --btn-grad-success-hover: linear-gradient(135deg,#16a34a 0%,#15803d 50%,#166534 100%);
      --btn-grad-light: linear-gradient(135deg,#ffffff 0%,#f1f5f9 100%);
      --btn-grad-light-hover: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; color:#0f172a; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-text { display:inline; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .main-shell { padding:1.75rem; background:#ffffff; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.25rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#475569; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 14px 26px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-outline-light { background-image:var(--btn-grad-light); color:#0f172a; }
    .btn-outline-light:hover { background-image:var(--btn-grad-light-hover); color:#0f172a; }
    .btn-outline-info,
    .btn-info { background-image:var(--btn-grad-info); color:#ffffff; box-shadow:0 12px 24px rgba(14,165,233,0.25); }
    .btn-outline-info:hover,
    .btn-info:hover { background-image:var(--btn-grad-info-hover); color:#ffffff; }
    .btn-outline-danger,
    .btn-danger { background-image:var(--btn-grad-danger); color:#ffffff; box-shadow:0 12px 24px rgba(220,38,38,0.25); }
    .btn-outline-danger:hover,
    .btn-danger:hover { background-image:var(--btn-grad-danger-hover); color:#ffffff; }
    .btn-success { background-image:var(--btn-grad-success); color:#ffffff; box-shadow:0 12px 24px rgba(34,197,94,0.25); }
    .btn-success:hover { background-image:var(--btn-grad-success-hover); color:#ffffff; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    .metric-card { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.5rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .metric-label { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:0.5rem; }
    .metric-value { font-size:1.8rem; font-weight:700; color:#0f172a; }
    .metric-sub { font-size:0.9rem; color:#64748b; margin-top:0.25rem; }
    @media(max-width:992px){
      .app-shell{ grid-template-columns:minmax(0,1fr);} 
      .sidebar{
        position:fixed;
        top:0;
        left:0;
        height:100vh;
        width:min(82vw,300px);
        max-width:320px;
        z-index:1050;
        display:flex;
        transform:translateX(-100%);
        transition:transform 0.2s ease;
        box-shadow:0 24px 48px rgba(15,23,42,0.12);
      }
      body.mobile-nav-open .sidebar{ transform:translateX(0); }
      .mobile-nav-backdrop{
        position:fixed;
        inset:0;
        background:rgba(15,23,42,0.35);
        z-index:1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop{ display:block; }
      .mobile-nav-toggle{
        display:inline-flex;
        align-items:center;
        gap:0.4rem;
        border-radius:0.75rem;
        border:0;
        background-image:var(--btn-grad-accent);
        color:#ffffff;
        padding:0.45rem 0.85rem;
        font-size:0.95rem;
        margin-bottom:1rem;
        box-shadow:0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus{ outline:2px solid rgba(15,118,110,0.4); outline-offset:2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-section-title">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      {# <a href="{{ url_for('leads.dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a> #}
      <a href="{{ url_for('index') }}" class="nav-pill">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill active">📄 <span class="nav-text">Invoices</span></a>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category=='warning' else 'info' }} border-0 text-dark">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="mb-4">
        <div class="badge-soft mb-2">Billing & Invoicing</div>
        <h1 class="h4 text-dark mb-1">Invoices</h1>
        <p class="text-secondary mb-0">{{ invoices|length }} total invoices</p>
      </header>

      <div class="mb-3">
        <a href="/admin/invoices/new" class="btn btn-primary">+ Create Invoice</a>
        <a href="{{ url_for('admin_income_report') }}" class="btn btn-outline-primary">💰 Monthly Income</a>
        <button form="bulk-invoice-email-form" type="submit" class="btn btn-outline-primary" onclick="return confirm('Send selected invoices by email now?');">✉ Send selected emails</button>
        <button
          form="bulk-invoice-email-form"
          type="submit"
          formaction="{{ url_for('admin_delete_bulk_invoices') }}"
          class="btn btn-outline-danger"
          onclick="return confirm('Delete selected invoices? This cannot be undone.');"
        >🗑 Delete selected</button>
      </div>

      <div class="card-surface mb-3">
        <form method="POST" action="{{ url_for('admin_generate_monthly_invoices') }}" class="row g-2 align-items-end">
          <div class="col-md-4">
            <label for="month" class="form-label">Billing Month (optional)</label>
            <input type="month" id="month" name="month" class="form-control" placeholder="YYYY-MM">
          </div>
          <div class="col-md-3">
            <label for="tax_rate_auto" class="form-label">Tax Rate (%)</label>
            <input type="number" id="tax_rate_auto" name="tax_rate" step="0.01" value="20" class="form-control" readonly>
          </div>
          <div class="col-md-3">
            <label for="due_days_auto" class="form-label">Days Until Due</label>
            <input type="number" id="due_days_auto" name="days_until_due" value="30" class="form-control">
          </div>
          <div class="col-md-2 d-grid">
            <button type="submit" class="btn btn-outline-primary" onclick="return confirm('Generate monthly invoices now?');">Auto Generate</button>
          </div>
        </form>
      </div>

      <div class="card-surface mb-3">
        <form method="GET" action="{{ url_for('admin_invoices') }}" class="row g-3 align-items-end">
          <div class="col-md-3">
            <label for="status" class="form-label">Status</label>
            <select id="status" name="status" class="form-select">
              <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All</option>
              <option value="draft" {% if status_filter == 'draft' %}selected{% endif %}>Draft</option>
              <option value="sent" {% if status_filter == 'sent' %}selected{% endif %}>Sent</option>
              <option value="paid" {% if status_filter == 'paid' %}selected{% endif %}>Paid</option>
              <option value="overdue" {% if status_filter == 'overdue' %}selected{% endif %}>Overdue</option>
            </select>
          </div>
          <div class="col-md-3">
            <label for="created_from" class="form-label">Created From</label>
            <input type="date" id="created_from" name="created_from" value="{{ created_from }}" class="form-control">
          </div>
          <div class="col-md-3">
            <label for="created_to" class="form-label">Created To</label>
            <input type="date" id="created_to" name="created_to" value="{{ created_to }}" class="form-control">
          </div>
          <div class="col-md-3 d-flex gap-2">
            <button type="submit" class="btn btn-primary w-100">Apply Filters</button>
            <a href="{{ url_for('admin_invoices') }}" class="btn btn-outline-secondary">Reset</a>
          </div>
        </form>
      </div>

      {% if invoices %}
      <div class="card-surface">
        <form id="bulk-invoice-email-form" method="POST" action="{{ url_for('admin_send_bulk_invoice_emails') }}">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr>
                <th>
                  <input type="checkbox" id="select-all-invoices" aria-label="Select all invoices">
                </th>
                <th>Invoice #</th>
                <th>Site</th>
                <th>Contact</th>
                <th class="text-end">Hours</th>
                <th class="text-end">Total</th>
                <th>Status</th>
                <th>Date</th>
                <th class="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {% for inv in invoices %}
              <tr>
                <td>
                  <input type="checkbox" name="invoice_ids" value="{{ inv.id }}" class="invoice-select" aria-label="Select invoice {{ short_invoice_number(inv.invoice_number) }}">
                </td>
                <td><strong>{{ short_invoice_number(inv.invoice_number) }}</strong></td>
                <td>{{ inv.site.name }}</td>
                <td>{{ inv.site_contact_name or 'N/A' }}</td>
                <td class="text-end">{{ inv.total_hours }}</td>
                <td class="text-end"><strong>{{ "%.2f"|format(inv.total_amount) }} €</strong></td>
                <td>
                  {% if inv.status == 'draft' %}
                    <span class="badge bg-warning text-dark">DRAFT</span>
                  {% elif inv.status == 'sent' %}
                    <span class="badge bg-info text-white">SENT</span>
                  {% elif inv.status == 'paid' %}
                    <span class="badge bg-success text-white">PAID</span>
                  {% elif inv.status == 'overdue' %}
                    <span class="badge bg-danger text-white">OVERDUE</span>
                  {% endif %}
                </td>
                <td>{{ inv.created_at.strftime('%d %b %Y') }}</td>
                <td class="text-end">
                  <a href="/admin/invoices/{{ inv.id }}" class="btn btn-sm btn-outline-info" title="View" aria-label="View invoice">
                    <i class="bi bi-eye"></i>
                  </a>
                  <a href="/admin/invoices/{{ inv.id }}/edit" class="btn btn-sm btn-outline-primary" title="Edit" aria-label="Edit invoice">
                    <i class="bi bi-pencil-square"></i>
                  </a>
                  <a href="/admin/invoices/{{ inv.id }}/pdf" class="btn btn-sm btn-outline-secondary" target="_blank" title="PDF" aria-label="Download PDF">
                    <i class="bi bi-file-earmark-pdf"></i>
                  </a>
                  <a href="/admin/invoices/{{ inv.id }}/delete" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete this invoice?');" title="Delete" aria-label="Delete invoice">
                    <i class="bi bi-trash"></i>
                  </a>
                </td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
        </form>
      </div>
      {% else %}
      <div class="card-surface">
        {% if status_filter != 'all' or created_from or created_to %}
        <p class="text-muted mb-0">No invoices match the selected filters.</p>
        {% else %}
        <p class="text-muted mb-0">No invoices yet. Create your first invoice above.</p>
        {% endif %}
      </div>
      {% endif %}
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function() {
      const selectAll = document.getElementById('select-all-invoices');
      if (!selectAll) return;
      const boxes = Array.from(document.querySelectorAll('.invoice-select'));
      selectAll.addEventListener('change', () => {
        boxes.forEach((box) => {
          box.checked = selectAll.checked;
        });
      });
      boxes.forEach((box) => {
        box.addEventListener('change', () => {
          if (!box.checked) {
            selectAll.checked = false;
            return;
          }
          selectAll.checked = boxes.length > 0 && boxes.every((item) => item.checked);
        });
      });
    })();
    const body = document.body;
    const toggle = document.getElementById('mobile-nav-toggle');
    const sidebar = document.getElementById('admin-sidebar');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    if (toggle && sidebar && backdrop) {
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        body.classList.contains('mobile-nav-open') ? closeNav() : openNav();
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeNav));
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/admin-sw.js').catch(() => {});
      });
    }
  </script>
</body>
</html>
"""

INCOME_REPORT_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Monthly Income Report</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-success: linear-gradient(135deg,#22c55e 0%,#16a34a 50%,#15803d 100%);
      --btn-grad-success-hover: linear-gradient(135deg,#16a34a 0%,#15803d 50%,#166534 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; color:#0f172a; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-text { display:inline; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .main-shell { padding:1.75rem; background:#ffffff; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.25rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#475569; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 14px 26px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-success { background-image:var(--btn-grad-success); color:#ffffff; box-shadow:0 12px 24px rgba(34,197,94,0.25); }
    .btn-success:hover { background-image:var(--btn-grad-success-hover); color:#ffffff; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    .month-card { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.5rem; margin-bottom:1.5rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .month-header { border-bottom:2px solid #e2e8f0; padding-bottom:1rem; margin-bottom:1rem; }
    .month-title { font-size:1.3rem; font-weight:700; color:#0f172a; }
    .income-summary { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; margin-bottom:1.5rem; }
    .summary-stat { border-radius:0.7rem; border:1px solid #cbd5f5; background:#f8fafc; padding:1rem; }
    .summary-label { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; margin-bottom:0.3rem; }
    .summary-value { font-size:1.6rem; font-weight:700; color:#0f172a; }
    .summary-sub { font-size:0.85rem; color:#64748b; margin-top:0.2rem; }
    .site-breakdown table { font-size:0.95rem; }
    .site-breakdown th { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; background:#f1f5f9; }
    @media(max-width:992px){
      .app-shell{ grid-template-columns:minmax(0,1fr);} 
      .sidebar{
        position:fixed;
        top:0;
        left:0;
        height:100vh;
        width:min(82vw,300px);
        max-width:320px;
        z-index:1050;
        display:flex;
        transform:translateX(-100%);
        transition:transform 0.2s ease;
        box-shadow:0 24px 48px rgba(15,23,42,0.12);
      }
      body.mobile-nav-open .sidebar{ transform:translateX(0); }
      .mobile-nav-backdrop{
        position:fixed;
        inset:0;
        background:rgba(15,23,42,0.35);
        z-index:1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop{ display:block; }
      .mobile-nav-toggle{
        display:inline-flex;
        align-items:center;
        gap:0.4rem;
        border-radius:0.75rem;
        border:0;
        background-image:var(--btn-grad-accent);
        color:#ffffff;
        padding:0.45rem 0.85rem;
        font-size:0.95rem;
        margin-bottom:1rem;
        box-shadow:0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus{ outline:2px solid rgba(15,118,110,0.4); outline-offset:2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-section-title">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      {# <a href="{{ url_for('leads.dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a> #}
      <a href="{{ url_for('index') }}" class="nav-pill">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill active">📄 <span class="nav-text">Invoices</span></a>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category=='warning' else 'info' }} border-0 text-dark">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="mb-4">
        <div class="badge-soft mb-2">Financial Overview</div>
        <h1 class="h4 text-dark mb-1">💰 Monthly Income Report</h1>
        <p class="text-secondary mb-0">Income breakdown by month and site</p>
      </header>

      <div class="mb-3">
        <a href="{{ url_for('admin_invoices') }}" class="btn btn-outline-secondary">← Back to Invoices</a>
      </div>

      {% if monthly_summaries %}
        {% for summary in monthly_summaries %}
          <div class="month-card">
            <div class="month-header">
              <div class="month-title">{{ summary.month_name }}</div>
            </div>

            <div class="income-summary">
              <div class="summary-stat">
                <div class="summary-label">Total Income</div>
                <div class="summary-value">{{ "%.2f"|format(summary.total_income) }} €</div>
                <div class="summary-sub">Gross earnings</div>
              </div>
              <div class="summary-stat">
                <div class="summary-label">Total Hours</div>
                <div class="summary-value">{{ summary.total_hours }}</div>
                <div class="summary-sub">Hours worked</div>
              </div>
              <div class="summary-stat">
                <div class="summary-label">Sites</div>
                <div class="summary-value">{{ summary.sites|length }}</div>
                <div class="summary-sub">Active clients</div>
              </div>
            </div>

            {% if summary.sites %}
              <div class="site-breakdown">
                <table class="table table-sm table-striped mb-0">
                  <thead>
                    <tr>
                      <th>Site</th>
                      <th class="text-end">Hours</th>
                      <th class="text-end">Rate</th>
                      <th class="text-end">Income</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for site_id, site_data in summary.sites.items() %}
                      <tr>
                        <td><strong>{{ site_data.site_name }}</strong></td>
                        <td class="text-end">{{ site_data.hours }}</td>
                        <td class="text-end">{{ "%.2f"|format(site_data.hourly_rate) }} €/hr</td>
                        <td class="text-end"><strong>{{ "%.2f"|format(site_data.income) }} €</strong></td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            {% endif %}
          </div>
        {% endfor %}
      {% else %}
        <div class="card-surface">
          <p class="text-muted mb-0">No work recorded yet. Start scheduling shifts to see income data.</p>
        </div>
      {% endif %}
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const body = document.body;
    const toggle = document.getElementById('mobile-nav-toggle');
    const sidebar = document.getElementById('admin-sidebar');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    if (toggle && sidebar && backdrop) {
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        body.classList.contains('mobile-nav-open') ? closeNav() : openNav();
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeNav));
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/admin-sw.js').catch(() => {});
      });
    }
  </script>
</body>
</html>
"""


INVOICE_FORM_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Create Invoice</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-danger: linear-gradient(135deg,#f87171 0%,#ef4444 50%,#dc2626 100%);
      --btn-grad-danger-hover: linear-gradient(135deg,#ef4444 0%,#dc2626 50%,#b91c1c 100%);
      --btn-grad-info: linear-gradient(135deg,#38bdf8 0%,#0ea5e9 50%,#2563eb 100%);
      --btn-grad-info-hover: linear-gradient(135deg,#0ea5e9 0%,#2563eb 50%,#1d4ed8 100%);
      --btn-grad-success: linear-gradient(135deg,#22c55e 0%,#16a34a 50%,#15803d 100%);
      --btn-grad-success-hover: linear-gradient(135deg,#16a34a 0%,#15803d 50%,#166534 100%);
      --btn-grad-light: linear-gradient(135deg,#ffffff 0%,#f1f5f9 100%);
      --btn-grad-light-hover: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; color:#0f172a; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-text { display:inline; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .main-shell { padding:1.75rem; background:#ffffff; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.25rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#475569; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 14px 26px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-outline-light { background-image:var(--btn-grad-light); color:#0f172a; }
    .btn-outline-light:hover { background-image:var(--btn-grad-light-hover); color:#0f172a; }
    .btn-outline-info,
    .btn-info { background-image:var(--btn-grad-info); color:#ffffff; box-shadow:0 12px 24px rgba(14,165,233,0.25); }
    .btn-outline-info:hover,
    .btn-info:hover { background-image:var(--btn-grad-info-hover); color:#ffffff; }
    .btn-outline-danger,
    .btn-danger { background-image:var(--btn-grad-danger); color:#ffffff; box-shadow:0 12px 24px rgba(220,38,38,0.25); }
    .btn-outline-danger:hover,
    .btn-danger:hover { background-image:var(--btn-grad-danger-hover); color:#ffffff; }
    .btn-success { background-image:var(--btn-grad-success); color:#ffffff; box-shadow:0 12px 24px rgba(34,197,94,0.25); }
    .btn-success:hover { background-image:var(--btn-grad-success-hover); color:#ffffff; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    @media(max-width:992px){
      .app-shell{ grid-template-columns:minmax(0,1fr);} 
      .sidebar{
        position:fixed;
        top:0;
        left:0;
        height:100vh;
        width:min(82vw,300px);
        max-width:320px;
        z-index:1050;
        display:flex;
        transform:translateX(-100%);
        transition:transform 0.2s ease;
        box-shadow:0 24px 48px rgba(15,23,42,0.12);
      }
      body.mobile-nav-open .sidebar{ transform:translateX(0); }
      .mobile-nav-backdrop{
        position:fixed;
        inset:0;
        background:rgba(15,23,42,0.35);
        z-index:1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop{ display:block; }
      .mobile-nav-toggle{
        display:inline-flex;
        align-items:center;
        gap:0.4rem;
        border-radius:0.75rem;
        border:0;
        background-image:var(--btn-grad-accent);
        color:#ffffff;
        padding:0.45rem 0.85rem;
        font-size:0.95rem;
        margin-bottom:1rem;
        box-shadow:0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus{ outline:2px solid rgba(15,118,110,0.4); outline-offset:2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-section-title">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      {# <a href="{{ url_for('leads.dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a> #}
      <a href="{{ url_for('index') }}" class="nav-pill">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill active">📄 <span class="nav-text">Invoices</span></a>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category=='warning' else 'info' }} border-0 text-dark">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="mb-4">
        <div class="badge-soft mb-2">Billing & Invoicing</div>
        <h1 class="h4 text-dark mb-1">Create New Invoice</h1>
        <p class="text-secondary mb-0">Generate an invoice for work completed</p>
      </header>

      <div class="row">
        <div class="col-lg-8">
          <div class="card-surface">
            <form method="POST">
              <div class="mb-3">
                <label for="site_id" class="form-label fw-bold">Site *</label>
                <select id="site_id" name="site_id" class="form-select" required>
                  <option value="">Select a site</option>
                  {% for site in sites %}
                  <option
                    value="{{ site.id }}"
                    data-contact-name="{{ site.profile_contact_name or site.contact_name or '' }}"
                    data-contact-email="{{ site.profile_contact_email or site.contact_email or '' }}"
                    data-company-name="{{ site.profile_company_name or site.name or '' }}"
                    data-phone="{{ site.profile_phone or '' }}"
                    data-billing-address="{{ site.profile_billing_address or site.address or '' }}"
                    data-customer-id="{{ site.profile_tax_id or '' }}"
                  >{{ site.name }}</option>
                  {% endfor %}
                </select>
                <div class="form-text">Site profile contact details are auto-filled when available.</div>
              </div>

              <div class="mb-3">
                <label for="site_company_name" class="form-label fw-bold">Company Name</label>
                <input type="text" id="site_company_name" name="site_company_name" class="form-control" placeholder="e.g., ACME GmbH">
              </div>

              <div class="mb-3">
                <label for="site_contact_name" class="form-label fw-bold">Contact Name</label>
                <input type="text" id="site_contact_name" name="site_contact_name" class="form-control" placeholder="e.g., John Smith">
              </div>

              <div class="mb-3">
                <label for="site_contact_email" class="form-label fw-bold">Contact Email</label>
                <input type="email" id="site_contact_email" name="site_contact_email" class="form-control" placeholder="contact@site.com">
              </div>

              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="site_phone" class="form-label fw-bold">Contact Phone</label>
                  <input type="text" id="site_phone" name="site_phone" class="form-control" placeholder="+43 ...">
                </div>
                <div class="col-md-6 mb-3">
                  <label for="site_tax_id" class="form-label fw-bold">Customer ID</label>
                  <input type="text" id="site_tax_id" name="site_tax_id" class="form-control" placeholder="UT- 0001" readonly>
                </div>
              </div>

              <div class="mb-3">
                <label for="site_billing_address" class="form-label fw-bold">Billing Address</label>
                <input type="text" id="site_billing_address" name="site_billing_address" class="form-control" placeholder="Street, ZIP, City">
              </div>
              
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="invoice_month" class="form-label fw-bold">Invoice Month *</label>
                  <input type="month" id="invoice_month" name="invoice_month" class="form-control" value="{{ current_month }}" required>
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label fw-bold">Total Hours (auto)</label>
                  <input type="text" class="form-control" value="Calculated from shifts" disabled>
                  <div class="form-text">Hourly rate is pulled from the site profile.</div>
                </div>
              </div>
              
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label for="tax_rate" class="form-label fw-bold">Tax Rate (%)</label>
                  <input type="number" id="tax_rate" name="tax_rate" step="0.01" value="20" class="form-control" readonly>
                </div>
                <div class="col-md-6 mb-3">
                  <label for="days_until_due" class="form-label fw-bold">Days Until Due *</label>
                  <input type="number" id="days_until_due" name="days_until_due" value="30" class="form-control" required>
                </div>
              </div>
              
              <div class="mb-3">
                <label for="notes" class="form-label fw-bold">Notes</label>
                <textarea id="notes" name="notes" class="form-control" rows="4" placeholder="Additional notes or payment terms..."></textarea>
              </div>
              
              <div class="mt-4">
                <button type="submit" class="btn btn-primary" title="Create invoice"><i class="bi bi-file-earmark-plus"></i></button>
                <a href="/admin/invoices" class="btn btn-outline-secondary" title="Cancel"><i class="bi bi-x-circle"></i></a>
              </div>
            </form>
          </div>
        </div>
      </div>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const body = document.body;
    const toggle = document.getElementById('mobile-nav-toggle');
    const sidebar = document.getElementById('admin-sidebar');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    if (toggle && sidebar && backdrop) {
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        body.classList.contains('mobile-nav-open') ? closeNav() : openNav();
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeNav));
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    (function() {
      const siteSelect = document.getElementById('site_id');
      const companyInput = document.getElementById('site_company_name');
      const nameInput = document.getElementById('site_contact_name');
      const emailInput = document.getElementById('site_contact_email');
      const phoneInput = document.getElementById('site_phone');
      const billingAddressInput = document.getElementById('site_billing_address');
      const customerIdInput = document.getElementById('site_tax_id');
      if (!siteSelect || !nameInput || !emailInput || !companyInput || !phoneInput || !billingAddressInput || !customerIdInput) {
        return;
      }
      const applyProfile = () => {
        const selected = siteSelect.options[siteSelect.selectedIndex];
        if (!selected) {
          return;
        }
        const profileCompany = selected.dataset.companyName || '';
        const profileName = selected.dataset.contactName || '';
        const profileEmail = selected.dataset.contactEmail || '';
        const profilePhone = selected.dataset.phone || '';
        const profileBillingAddress = selected.dataset.billingAddress || '';
        const profileCustomerId = selected.dataset.customerId || '';
        if (profileCompany) {
          companyInput.value = profileCompany;
        }
        if (profileName) {
          nameInput.value = profileName;
        }
        if (profileEmail) {
          emailInput.value = profileEmail;
        }
        if (profilePhone) {
          phoneInput.value = profilePhone;
        }
        if (profileBillingAddress) {
          billingAddressInput.value = profileBillingAddress;
        }
        if (profileCustomerId) {
          customerIdInput.value = profileCustomerId;
        }
      };
      siteSelect.addEventListener('change', applyProfile);
    })();
  </script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/admin-sw.js').catch(() => {});
      });
    }
  </script>
</body>
</html>
"""

INVOICE_EDIT_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Edit Invoice</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">Edit Invoice {{ short_invoice_number(invoice.invoice_number) }}</h1>
      <a href="{{ url_for('admin_view_invoice', invoice_id=invoice.id) }}" class="btn btn-outline-secondary" title="Back"><i class="bi bi-arrow-left"></i></a>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="mb-3">
          {% for category, message in messages %}
            <div class="alert alert-{{ 'warning' if category=='warning' else 'success' if category=='success' else 'info' }}">{{ message }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <form method="POST">
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Site</label>
              <select name="site_id" class="form-select" required>
                {% for site in sites %}
                  <option value="{{ site.id }}" {% if site.id == invoice.site_id %}selected{% endif %}>{{ site.name }}</option>
                {% endfor %}
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">Status</label>
              <select name="status" class="form-select">
                <option value="draft" {% if invoice.status == 'draft' %}selected{% endif %}>Draft</option>
                <option value="sent" {% if invoice.status == 'sent' %}selected{% endif %}>Sent</option>
                <option value="paid" {% if invoice.status == 'paid' %}selected{% endif %}>Paid</option>
                <option value="overdue" {% if invoice.status == 'overdue' %}selected{% endif %}>Overdue</option>
              </select>
            </div>

            <div class="col-md-6">
              <label class="form-label">Company Name</label>
              <input type="text" class="form-control" name="site_company_name" value="{{ invoice.site_company_name or '' }}">
            </div>

            <div class="col-md-6">
              <label class="form-label">Contact Name</label>
              <input type="text" class="form-control" name="site_contact_name" value="{{ invoice.site_contact_name or '' }}">
            </div>
            <div class="col-md-6">
              <label class="form-label">Contact Email</label>
              <input type="email" class="form-control" name="site_contact_email" value="{{ invoice.site_contact_email or '' }}">
            </div>
            <div class="col-md-6">
              <label class="form-label">Contact Phone</label>
              <input type="text" class="form-control" name="site_phone" value="{{ invoice.site_phone or '' }}">
            </div>
            <div class="col-md-6">
              <label class="form-label">Billing Address</label>
              <input type="text" class="form-control" name="site_billing_address" value="{{ invoice.site_billing_address or '' }}">
            </div>
            <div class="col-md-6">
              <label class="form-label">Customer ID</label>
              <input type="text" class="form-control" name="site_tax_id" value="{{ invoice.site_tax_id or '' }}">
            </div>

            <div class="col-md-4">
              <label class="form-label">Hourly Rate</label>
              <input type="number" step="0.01" min="0" class="form-control" name="hourly_rate" value="{{ invoice.hourly_rate }}" required>
            </div>
            <div class="col-md-4">
              <label class="form-label">Total Hours</label>
              <input type="number" step="0.01" min="0" class="form-control" name="total_hours" value="{{ invoice.total_hours }}" required>
            </div>
            <div class="col-md-4">
              <label class="form-label">Tax Rate (%)</label>
              <input type="number" step="0.01" min="0" class="form-control" name="tax_rate" value="20" readonly>
            </div>

            <div class="col-md-6">
              <label class="form-label">Due Date</label>
              <input type="date" class="form-control" name="due_date" value="{{ invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else '' }}">
            </div>
            <div class="col-md-6">
              <label class="form-label">Paid Date</label>
              <input type="date" class="form-control" name="paid_at" value="{{ invoice.paid_at.strftime('%Y-%m-%d') if invoice.paid_at else '' }}">
            </div>

            <div class="col-12">
              <label class="form-label">Notes</label>
              <textarea class="form-control" name="notes" rows="4">{{ invoice.notes or '' }}</textarea>
            </div>
          </div>

          <div class="mt-4 d-flex gap-2">
            <button type="submit" class="btn btn-primary">Save Changes</button>
            <a href="{{ url_for('admin_view_invoice', invoice_id=invoice.id) }}" class="btn btn-outline-secondary" title="Cancel"><i class="bi bi-x-circle"></i></a>
          </div>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
"""

CONTRACT_BUILDER_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Contract PDF</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <div class="container py-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">Client contract PDF</h1>
      <a href="{{ url_for('admin_sites') }}" class="btn btn-outline-secondary">Back to manage sites</a>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="mb-3">
          {% for category, message in messages %}
            <div class="alert alert-{{ 'warning' if category=='warning' else 'info' }}">{{ message }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <div class="card border-0 shadow-sm">
      <div class="card-body">
        <form method="post" enctype="multipart/form-data">
          <div class="row g-3">
            <div class="col-12">
              <label class="form-label">Upload contract PDF</label>
              <input type="file" class="form-control" name="contract_pdf" accept="application/pdf,.pdf">
              <div class="form-text">Optional if a server template exists at uploads/contract_template.pdf or static/uploads/contract_template.pdf (or set CONTRACT_TEMPLATE_PATH). If uploaded, this file is used.</div>
            </div>
            <div class="col-md-6">
              <label class="form-label">Name des partners</label>
              <input type="text" class="form-control" name="partner_name" value="{{ partner_name or '' }}" required>
            </div>
            <div class="col-md-6">
              <label class="form-label">Firma</label>
              <input type="text" class="form-control" name="company_name" value="{{ company_name or '' }}" required>
            </div>
            <div class="col-12">
              <label class="form-label">Tel./ Fax / E-Mail</label>
              <input type="text" class="form-control" name="contact_details" value="{{ contact_details or '' }}" required>
            </div>
          </div>
          <div class="mt-4">
            <button type="submit" class="btn btn-primary">Download PDF</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
"""

INVOICE_VIEW_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — View Invoice</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-danger: linear-gradient(135deg,#f87171 0%,#ef4444 50%,#dc2626 100%);
      --btn-grad-danger-hover: linear-gradient(135deg,#ef4444 0%,#dc2626 50%,#b91c1c 100%);
      --btn-grad-info: linear-gradient(135deg,#38bdf8 0%,#0ea5e9 50%,#2563eb 100%);
      --btn-grad-info-hover: linear-gradient(135deg,#0ea5e9 0%,#2563eb 50%,#1d4ed8 100%);
      --btn-grad-success: linear-gradient(135deg,#22c55e 0%,#16a34a 50%,#15803d 100%);
      --btn-grad-success-hover: linear-gradient(135deg,#16a34a 0%,#15803d 50%,#166534 100%);
      --btn-grad-light: linear-gradient(135deg,#ffffff 0%,#f1f5f9 100%);
      --btn-grad-light-hover: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; color:#0f172a; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-text { display:inline; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .main-shell { padding:1.75rem; background:#ffffff; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.25rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#475569; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 14px 26px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-outline-light { background-image:var(--btn-grad-light); color:#0f172a; }
    .btn-outline-light:hover { background-image:var(--btn-grad-light-hover); color:#0f172a; }
    .btn-outline-info,
    .btn-info { background-image:var(--btn-grad-info); color:#ffffff; box-shadow:0 12px 24px rgba(14,165,233,0.25); }
    .btn-outline-info:hover,
    .btn-info:hover { background-image:var(--btn-grad-info-hover); color:#ffffff; }
    .btn-outline-danger,
    .btn-danger { background-image:var(--btn-grad-danger); color:#ffffff; box-shadow:0 12px 24px rgba(220,38,38,0.25); }
    .btn-outline-danger:hover,
    .btn-danger:hover { background-image:var(--btn-grad-danger-hover); color:#ffffff; }
    .btn-success { background-image:var(--btn-grad-success); color:#ffffff; box-shadow:0 12px 24px rgba(34,197,94,0.25); }
    .btn-success:hover { background-image:var(--btn-grad-success-hover); color:#ffffff; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    @media(max-width:992px){
      .app-shell{ grid-template-columns:minmax(0,1fr);} 
      .sidebar{
        position:fixed;
        top:0;
        left:0;
        height:100vh;
        width:min(82vw,300px);
        max-width:320px;
        z-index:1050;
        display:flex;
        transform:translateX(-100%);
        transition:transform 0.2s ease;
        box-shadow:0 24px 48px rgba(15,23,42,0.12);
      }
      body.mobile-nav-open .sidebar{ transform:translateX(0); }
      .mobile-nav-backdrop{
        position:fixed;
        inset:0;
        background:rgba(15,23,42,0.35);
        z-index:1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop{ display:block; }
      .mobile-nav-toggle{
        display:inline-flex;
        align-items:center;
        gap:0.4rem;
        border-radius:0.75rem;
        border:0;
        background-image:var(--btn-grad-accent);
        color:#ffffff;
        padding:0.45rem 0.85rem;
        font-size:0.95rem;
        margin-bottom:1rem;
        box-shadow:0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus{ outline:2px solid rgba(15,118,110,0.4); outline-offset:2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-section-title">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      {# <a href="{{ url_for('leads.dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a> #}
      <a href="{{ url_for('index') }}" class="nav-pill">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill active">📄 <span class="nav-text">Invoices</span></a>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category=='warning' else 'success' if category=='success' else 'info' }} border-0 text-dark">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="mb-4">
        <div class="badge-soft mb-2">Invoice Details</div>
        <h1 class="h4 text-dark mb-1">Invoice {{ short_invoice_number(invoice.invoice_number) }}</h1>
        <p class="text-secondary mb-0">
          {% if invoice.status == 'draft' %}
            <span class="badge bg-warning text-dark">DRAFT</span>
          {% elif invoice.status == 'sent' %}
            <span class="badge bg-info text-white">SENT</span>
          {% elif invoice.status == 'paid' %}
            <span class="badge bg-success text-white">PAID</span>
          {% endif %}
        </p>
      </header>

      <div class="mb-3">
        <a href="/admin/invoices" class="btn btn-outline-secondary" title="Back" aria-label="Back to invoices">
          <i class="bi bi-arrow-left"></i>
        </a>
        <a href="/admin/invoices/{{ invoice.id }}/edit" class="btn btn-outline-primary" title="Edit" aria-label="Edit invoice">
          <i class="bi bi-pencil-square"></i>
        </a>
        <a href="/admin/invoices/{{ invoice.id }}/pdf" class="btn btn-success" target="_blank" title="PDF" aria-label="Download invoice PDF">
          <i class="bi bi-file-earmark-pdf"></i>
        </a>
        <a href="/admin/invoices/{{ invoice.id }}/send-email" class="btn btn-primary" title="Send Email" aria-label="Send invoice email">
          <i class="bi bi-send"></i>
        </a>
        <a href="/admin/invoices/{{ invoice.id }}/delete" class="btn btn-outline-danger" onclick="return confirm('Delete this invoice?');" title="Delete" aria-label="Delete invoice">
          <i class="bi bi-trash"></i>
        </a>
        {% if invoice.status == 'paid' %}
        <form method="POST" action="/admin/invoices/{{ invoice.id }}/status" class="d-inline">
          <input type="hidden" name="status" value="sent">
          <button type="submit" class="btn btn-outline-warning">Mark as Unpaid</button>
        </form>
        {% else %}
        <form method="POST" action="/admin/invoices/{{ invoice.id }}/status" class="d-inline">
          <input type="hidden" name="status" value="paid">
          <button type="submit" class="btn btn-success">Mark as Paid</button>
        </form>
        {% endif %}
      </div>

      <div class="row">
        <div class="col-lg-8">
          <div class="card-surface mb-4">
            <div class="row mb-4 pb-3 border-bottom">
              <div class="col-md-6">
                <h2 class="h5 mb-3">INVOICE</h2>
                <p class="mb-1"><strong>Invoice #:</strong> {{ short_invoice_number(invoice.invoice_number) }}</p>
                <p class="mb-1"><strong>Date:</strong> {{ invoice.issued_date.strftime("%d/%m/%Y") }}</p>
                <p class="mb-0"><strong>Due Date:</strong> {{ invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else "Upon receipt" }}</p>
                {% if invoice.paid_at %}
                <p class="mb-0"><strong>Paid Date:</strong> {{ invoice.paid_at.strftime("%d/%m/%Y") }}</p>
                {% endif %}
              </div>
            </div>

            <div class="row mb-4">
              <div class="col-md-6">
                <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 0.08em;">Bill To:</h6>
                <p class="mb-1"><strong>Billing Contact Person:</strong> {{ invoice.site_contact_name or '' }}</p>
                <p class="mb-1"><strong>Address:</strong> {{ invoice.site_billing_address or invoice.site.address or '' }}</p>
              </div>
              <div class="col-md-6">
                <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 0.08em;">Invoice Details:</h6>
                <p class="mb-1"><strong>Site:</strong> {{ invoice.site.name }}</p>
                <p class="mb-1"><strong>Hourly Rate:</strong> {{ "%.2f"|format(invoice.hourly_rate) }} €</p>
                <p class="mb-1"><strong>Total Hours:</strong> {{ invoice.total_hours }}</p>
              </div>
            </div>

            <div class="table-responsive mb-4">
              <table class="table mb-0">
                <thead class="table-light">
                  <tr>
                    <th>Description</th>
                    <th class="text-end">Quantity</th>
                    <th class="text-end">Rate</th>
                    <th class="text-end">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Work at {{ invoice.site.name }}</td>
                    <td class="text-end">{{ invoice.total_hours }} hours</td>
                    <td class="text-end">{{ "%.2f"|format(invoice.hourly_rate) }} €/hr</td>
                    <td class="text-end"><strong>{{ "%.2f"|format(invoice.subtotal) }} €</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="row">
              <div class="col-md-6 offset-md-6">
                <table class="table table-sm mb-0">
                  <tr>
                    <td class="text-end">Subtotal:</td>
                    <td class="text-end"><strong>{{ "%.2f"|format(invoice.subtotal) }} €</strong></td>
                  </tr>
                  <tr>
                    <td class="text-end">Tax ({{ (invoice.tax_rate * 100)|round(1) }}%):</td>
                    <td class="text-end"><strong>{{ "%.2f"|format(invoice.tax_amount) }} €</strong></td>
                  </tr>
                  <tr class="table-dark">
                    <td class="text-end"><strong>TOTAL:</strong></td>
                    <td class="text-end"><strong>{{ "%.2f"|format(invoice.total_amount) }} €</strong></td>
                  </tr>
                </table>
              </div>
            </div>

            {% if invoice.notes %}
            <div class="mt-4 pt-3 border-top">
              <h6 class="text-muted text-uppercase mb-2" style="font-size: 0.75rem; letter-spacing: 0.08em;">Notes:</h6>
              <p class="mb-0">{{ invoice.notes }}</p>
            </div>
            {% endif %}
          </div>
        </div>
      </div>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    const body = document.body;
    const toggle = document.getElementById('mobile-nav-toggle');
    const sidebar = document.getElementById('admin-sidebar');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    if (toggle && sidebar && backdrop) {
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        body.classList.contains('mobile-nav-open') ? closeNav() : openNav();
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', closeNav));
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/admin-sw.js').catch(() => {});
      });
    }
  </script>
</body>
</html>
"""

