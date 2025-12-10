import re
import io
import csv
import logging
import os
from collections import deque
from datetime import datetime, date, timedelta
from urllib.parse import urljoin, urldefrag, urlparse
from dotenv import load_dotenv
load_dotenv()
import requests
from bs4 import BeautifulSoup
from flask import (
    Flask,
    request,
    send_file,
    render_template_string,
    jsonify,
    redirect,
    url_for,
)
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session

try:
    # Optional: only used when GPT integration is configured
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image,
    )

    REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    REPORTLAB_AVAILABLE = False

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

openai_client = None
if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
    try:
        openai_client = OpenAI()
        app.logger.info("OpenAI client initialized for GPT integration.")
    except Exception as e:  # pragma: no cover - defensive
        app.logger.warning("Failed to initialize OpenAI client: %s", e)


# --- simple SQLite scheduling backend (employees / sites / shifts) ---
Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)

    shifts = relationship("Shift", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<Employee {self.id} {self.name!r}>"


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)

    shifts = relationship("Shift", back_populates="site", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<Site {self.id} {self.name!r}>"


class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    day = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    employee = relationship("Employee", back_populates="shifts")
    site = relationship("Site", back_populates="shifts")

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"<Shift {self.id} emp={self.employee_id} site={self.site_id} {self.day}>"


DB_URL = os.getenv("SCHEDULE_DB_URL", "sqlite:///schedule.db")
engine = create_engine(DB_URL, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db():
    """Create tables and some seed data if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Employee).count() == 0:
            demo_emps = [
                Employee(name="Anna", role="Cleaning"),
                Employee(name="Markus", role="Supervisor"),
                Employee(name="Sara", role="Cleaning"),
            ]
            db.add_all(demo_emps)
        if db.query(Site).count() == 0:
            demo_sites = [
                Site(name="Site A – City Center", address="Vienna, Kärntner Straße 1"),
                Site(name="Site B – Office Park", address="Graz, Office Park 12"),
                Site(name="Site C – Warehouse", address="Linz, Industrial Way 7"),
            ]
            db.add_all(demo_sites)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Initialize DB eagerly on import so it works with Flask 3.x (no before_first_request)
init_db()

# Email regex (unchanged)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}")

# Much stricter phone regex (only real-world-like patterns)
PHONE_REGEX = re.compile(
    r"""
    (?<!\d)                 # must not be part of longer number
    (?:\+|00)?\d{1,3}?      # optional country code (+43, 0043, +1, etc.)
    [\s./()\-]*             # optional separators after country code
    (?:\d[\s./()\-]*){6,12} # 7–15 digits total (digit groups with separators)
    (?!\d)                  # must not be part of longer number
    """,
    re.VERBOSE,
)

# Labels we consider authoritative for nearby phone numbers
PHONE_LABELS = ["tel", "telefon", "t:", "m:", "mobil", "mobile", "mob", "phone", "kontakt", "fax", "call"]


def normalize_phone(s: str) -> str:
    """Normalize phone: keep leading + if present, otherwise digits only. Return '' if too short."""
    if not s:
        return ""
    s = s.strip()
    has_plus = s.startswith("+")
    digits = re.sub(r"[^0-9]", "", s)
    if len(digits) < 6:
        return ""
    return ("+" + digits) if has_plus else digits


# --- validation helpers ---
def is_valid_phone(norm: str) -> bool:
    """Simple validation on normalized phone (digits w/ optional leading +)."""
    if not norm:
        return False
    digits = norm[1:] if norm.startswith("+") else norm
    if not digits.isdigit():
        return False
    if not (7 <= len(digits) <= 15):
        return False
    if len(set(digits)) == 1:
        return False
    return True


_phone_label_re = re.compile(r"(?:tel|telefon|t:|m:|mobil|mobile|mob|phone|kontakt|fax|call)", re.I)


def has_phone_label(context: str, match_start: int) -> bool:
    """Check up to 40 chars before match for common phone labels."""
    if not context:
        return False
    start = max(0, match_start - 40)
    snippet = context[start:match_start].lower()
    return bool(_phone_label_re.search(snippet))


def find_labelled_phones(text: str):
    """Return list of normalized, validated phones that appear near a phone label inside text."""
    results = []
    if not text:
        return results
    for label in PHONE_LABELS:
        pattern = rf"{re.escape(label)}[^0-9+]{{0,15}}({PHONE_REGEX.pattern})"
        try:
            for m in re.finditer(pattern, text, flags=re.I | re.VERBOSE):
                raw = m.group(1)
                n = normalize_phone(raw)
                if n and is_valid_phone(n):
                    results.append(n)
        except re.error:
            continue
    return results


# Modern HTML interface with dashboard-style layout inspired by modern B2B tools
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — URL Contact Crawler</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root { --bs-primary: #0f766e; }
    body {
      min-height: 100vh;
      background: radial-gradient(circle at top left,#0f172a 0%, #020617 40%, #020617 100%);
      color: #0f172a;
    }
    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      background: transparent;
    }
    .sidebar {
      background: radial-gradient(circle at top,#020617 0%, #020617 45%, #020617 100%);
      border-right: 1px solid rgba(148, 163, 184, 0.3);
      color: #e5e7eb;
      display: flex;
      flex-direction: column;
      padding: 1.5rem 1.25rem;
      gap: 1.5rem;
    }
    .sidebar-brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .sidebar-logo {
      height: 40px;
      width: 40px;
      border-radius: 12px;
      background: radial-gradient(circle at 10% 0, #22c55e 0%, #0ea5e9 45%, #1d4ed8 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .sidebar-logo img {
      max-width: 80%;
      max-height: 80%;
      object-fit: contain;
    }
    .sidebar-title {
      font-weight: 600;
      letter-spacing: 0.03em;
      font-size: 0.95rem;
      text-transform: uppercase;
      color: #e5e7eb;
    }
    .sidebar-sub {
      font-size: 0.78rem;
      color: #9ca3af;
    }
    .sidebar-section-title {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #6b7280;
      margin-bottom: 0.4rem;
    }
    .nav-pill {
      border-radius: 0.75rem;
      padding: 0.45rem 0.75rem;
      font-size: 0.9rem;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      text-decoration: none;
      border: 1px solid transparent;
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .nav-pill.active {
      background: rgba(15, 118, 110, 0.2);
      border-color: rgba(45, 212, 191, 0.4);
      color: #ecfeff;
    }
    .nav-pill:hover {
      background: rgba(15, 23, 42, 0.9);
      border-color: rgba(148, 163, 184, 0.5);
      color: #f9fafb;
    }
    .nav-pill-icon {
      width: 24px;
      height: 24px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(15, 23, 42, 0.9);
      color: #a5b4fc;
      font-size: 0.9rem;
    }
    .sidebar-footer {
      margin-top: auto;
      font-size: 0.75rem;
      color: #6b7280;
    }
    .main-shell {
      background: radial-gradient(circle at top,#020617 0%, #020617 40%, #020617 100%);
      padding: 1.25rem 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }
    .topbar-title {
      color: #f9fafb;
      font-weight: 500;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      font-size: 0.8rem;
    }
    .topbar-heading {
      color: #e5e7eb;
      margin: 0.1rem 0 0.15rem;
      font-size: 1.25rem;
      font-weight: 600;
    }
    .topbar-subtitle {
      color: #9ca3af;
      font-size: 0.85rem;
      max-width: 460px;
    }
    .topbar-chip {
      font-size: 0.72rem;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      border: 1px solid rgba(45, 212, 191, 0.5);
      color: #a5f3fc;
      background: rgba(8, 47, 73, 0.85);
    }
    .topbar-user {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: #e5e7eb;
    }
    .user-avatar {
      width: 32px;
      height: 32px;
      border-radius: 999px;
      background: radial-gradient(circle at 10% 0, #0ea5e9 0%, #6366f1 60%, #4f46e5 100%);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.9rem;
      font-weight: 600;
      color: #e5e7eb;
    }
    .user-meta { font-size: 0.8rem; }
    .user-meta span { display: block; }
    .user-meta span:first-child { color: #e5e7eb; }
    .user-meta span:last-child { color: #6b7280; }
    .content-shell {
      margin-top: 0.25rem;
      border-radius: 1rem;
      background: radial-gradient(circle at top,#020617 0%, #020617 18%, #020617 45%, #020617 100%);
      border: 1px solid rgba(31, 41, 55, 0.9);
      box-shadow: 0 24px 80px rgba(15, 23, 42, 0.95);
      padding: 1.1rem 1.1rem 1.3rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .metrics-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
    }
    .metric-card {
      border-radius: 0.9rem;
      border: 1px solid rgba(51, 65, 85, 0.9);
      background: radial-gradient(circle at top left,#020617 0%, #020617 35%, #020617 100%);
      padding: 0.7rem 0.8rem;
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
    }
    .metric-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.14em; }
    .metric-value { font-size: 1.1rem; font-weight: 600; color: #e5e7eb; }
    .metric-note { font-size: 0.75rem; color: #9ca3af; }
    .card-surface {
      border-radius: 0.9rem;
      border: 1px solid rgba(51, 65, 85, 0.9);
      background: radial-gradient(circle at top left,#020617 0%, #020617 35%, #020617 100%);
      padding: 1rem;
      color: #e5e7eb;
    }
    .card-header-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 0.75rem;
    }
    .card-title { font-size: 0.95rem; font-weight: 500; color: #e5e7eb; }
    .card-subtitle { font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.3rem; }
    .badge-soft {
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.6);
      color: #9ca3af;
      padding: 0.15rem 0.6rem;
      font-size: 0.75rem;
    }
    .small-note { font-size:0.82rem; color:#9ca3af; }
    .divider-label {
      text-transform:uppercase;
      font-size:0.7rem;
      letter-spacing:0.08em;
      color:#6b7280;
    }
    .chat-bubble {
      border-radius:10px;
      background:#020617;
      padding:0.65rem 0.8rem;
      font-size:0.86rem;
      border:1px dashed rgba(55,65,81,0.9);
      color:#9ca3af;
    }
    .assistant-badge {
      font-size:0.78rem;
      padding:0.15rem 0.6rem;
      border-radius:999px;
      background:rgba(37,99,235,0.18);
      color:#bfdbfe;
      border:1px solid rgba(59,130,246,0.4);
    }
    .chat-output { white-space:pre-wrap; font-size:0.86rem; color:#e5e7eb; }
    @media (max-width: 992px) {
      .app-shell { grid-template-columns: minmax(0, 1fr); }
      .sidebar { display: none; }
      .main-shell { padding: 1rem; }
      .metrics-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
      .metrics-row { grid-template-columns: minmax(0, 1fr); }
      .content-shell { padding: 0.85rem; }
    }
   
        
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="sidebar-logo">
          <img src="/static/logo.png" alt="Putzelf Marketing">
        </div>
        <div>
          <div class="sidebar-title">Putzelf Marketing</div>
          <div class="sidebar-sub">Contact Studio</div>
        </div>
      </div>
      <div>
        <div class="sidebar-section-title">Workspace</div>
        <a href="#" class="nav-pill active">
          <span class="nav-pill-icon">◎</span>
          <span>Dashboard</span>
        </a>
        <a href="#" class="nav-pill">
          <span class="nav-pill-icon">↗</span>
          <span>Crawl history <span class="small-note">(coming soon)</span></span>
        </a>
        <a href="#" class="nav-pill">
          <span class="nav-pill-icon">✉</span>
          <span>Sequences <span class="small-note">(coming soon)</span></span>
        </a>
      </div>
      <div>
        <div class="sidebar-section-title">People</div>
        <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">
          <span class="nav-pill-icon">👤</span>
          <span>Employee schedule</span>
        </a>
        <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">
          <span class="nav-pill-icon">⚙</span>
          <span>Manage employees &amp; sites</span>
        </a>
      </div>
      <div class="sidebar-footer">
        <div>© <span id="year"></span> Putzelf Marketing</div>
        <div class="mt-1">Built for fast B2B prospecting.</div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="topbar">
        <div>
          <div class="topbar-title">Dashboard</div>
          <div class="d-flex align-items-center gap-2">
            <h1 class="topbar-heading mb-0">URL Contact Crawler</h1>
            <span class="topbar-chip">Live • Internal tool</span>
          </div>
          <p class="topbar-subtitle mb-0">
            Crawl websites for verified emails and phone numbers, then let GPT draft tailored outreach — all in one place.
          </p>
        </div>
        <div class="topbar-user">
          <div class="text-end user-meta">
            <span>Prospecting workspace</span>
            <span>{{ 'GPT connected' if gpt_enabled else 'GPT not configured' }}</span>
          </div>
          <div class="user-avatar">PM</div>
        </div>
      </header>
      <main class="content-shell">
        <section class="metrics-row">
          <div class="metric-card">
            <div class="metric-label">Last export</div>
            <div class="metric-value">On demand</div>
            <div class="metric-note">Run a crawl to generate a fresh CSV.</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Crawl scope</div>
            <div class="metric-value">Same domain</div>
            <div class="metric-note">Automatically avoids external sites &amp; assets.</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">GPT status</div>
            <div class="metric-value">
              {{ 'Ready' if gpt_enabled else 'Disabled' }}
            </div>
            <div class="metric-note">
              {% if gpt_enabled %}Use the panel on the right to generate copy.{% else %}Set OPENAI_API_KEY to enable AI assistant.{% endif %}
            </div>
          </div>
        </section>
        <section class="row g-3 mt-1">
          <div class="col-12 col-lg-6">
            <div class="card-surface h-100">
              <div class="card-header-line">
                <div>
                  <div class="card-title">1. Crawl new contacts</div>
                  <div class="card-subtitle">
                    Start from any page on a domain and collect emails and phone numbers into a single CSV.
                  </div>
                </div>
                <span class="badge-soft">Crawler</span>
              </div>
              <form id="crawl-form" class="needs-validation" novalidate>
                <div class="mb-3">
                  <label for="start_url" class="form-label small-note text-uppercase">Start URL</label>
                  <input type="url" class="form-control form-control-sm" id="start_url" name="start_url" placeholder="https://example.com" required>
                  <div class="invalid-feedback">Please enter a valid URL to start crawling.</div>
                </div>
                <div class="row">
                  <div class="col-7 mb-3">
                    <label for="max_pages" class="form-label small-note text-uppercase">Max pages</label>
                    <input type="number" class="form-control form-control-sm" id="max_pages" name="max_pages" min="1" max="200" value="100" required>
                    <div class="form-text small-note">1–200 pages per crawl, same domain only.</div>
                  </div>
                  <div class="col-5 mb-3">
                    <label class="form-label small-note text-uppercase">Rendering</label>
                    <div class="form-check">
                      <input class="form-check-input" type="checkbox" value="1" id="render_js" name="render_js">
                      <label class="form-check-label small-note" for="render_js">
                        Use headless browser (JS-heavy sites)
                      </label>
                    </div>
                  </div>
                </div>
                <div class="d-flex align-items-center gap-2 flex-wrap">
                  <button id="submit-btn" type="submit" class="btn btn-sm btn-primary" style="background-color:#0f766e; border-color:#0f766e;">
                    <span id="btn-spinner" class="spinner-border spinner-border-sm me-2 d-none" role="status" aria-hidden="true"></span>
                    Crawl &amp; download CSV
                  </button>
                  <button id="reset-btn" type="button" class="btn btn-sm btn-outline-secondary" onclick="document.getElementById('crawl-form').reset()">
                    Reset
                  </button>
                  <div id="status" class="ms-1 small-note" aria-live="polite"></div>
                </div>
                <hr class="my-3">
                <p class="small-note mb-0">
                  Use only on websites you are allowed to crawl. Respect robots.txt, terms of service and local regulations.
                </p>
              </form>
            </div>
          </div>
          <div class="col-12 col-lg-6">
            <div class="card-surface h-100 d-flex flex-column">
              <div class="card-header-line">
                <div>
                  <div class="card-title">2. AI outreach assistant</div>
                  <div class="card-subtitle">
                    Turn your crawled contacts into warm outreach sequences and summaries.
                  </div>
                </div>
                <div class="text-end">
                  <div class="assistant-badge mb-1">GPT-powered</div>
                  <div class="small-note" id="gpt-status-info">
                    {% if gpt_enabled %}Connected{% else %}API key missing{% endif %}
                  </div>
                </div>
              </div>
              <div class="chat-bubble mb-3">
                <div class="small-note mb-1">Examples you can ask:</div>
                <ul class="small-note ps-3 mb-0">
                  <li>“Draft a friendly cold email for these contacts.”</li>
                  <li>“Summarize the types of companies in this CSV.”</li>
                  <li>“Create a 3-step LinkedIn outreach sequence.”</li>
                </ul>
              </div>
              <form id="gpt-form" class="d-flex flex-column flex-grow-1">
                <div class="mb-2">
                  <label for="gpt_prompt" class="form-label small-note text-uppercase">Prompt</label>
                  <textarea id="gpt_prompt" class="form-control form-control-sm" name="gpt_prompt" rows="4" placeholder="Describe what you want GPT to generate, e.g. 'Draft a warm intro email for these contacts...'" required></textarea>
                </div>
                <div class="mb-3">
                  <label for="gpt_context" class="form-label small-note text-uppercase">Optional: contacts / notes</label>
                  <textarea id="gpt_context" class="form-control form-control-sm" name="gpt_context" rows="3" placeholder="Paste a few rows from your CSV or describe your ideal customer profile..."></textarea>
                </div>
                <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
                  <button id="gpt-submit-btn" type="submit" class="btn btn-sm btn-outline-primary">
                    <span id="gpt-spinner" class="spinner-border spinner-border-sm me-2 d-none" role="status" aria-hidden="true"></span>
                    Ask GPT
                  </button>
                  <button id="gpt-clear-btn" type="button" class="btn btn-sm btn-link text-decoration-none small-note">
                    Clear output
                  </button>
                  <div id="gpt-status" class="small-note" aria-live="polite"></div>
                </div>
                <div class="divider-label mb-2">GPT response</div>
                <div id="gpt-output" class="chat-output border rounded-3 p-2 flex-grow-1" style="min-height:120px; max-height:260px; overflow:auto; border-color:rgba(55,65,81,0.95); background:#020617;"></div>
              </form>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function () {
      'use strict'
      const form = document.getElementById('crawl-form');
      form.addEventListener('submit', async function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (!form.checkValidity()) {
          form.classList.add('was-validated');
          return;
        }
        const btn = document.getElementById('submit-btn');
        const spinner = document.getElementById('btn-spinner');
        const status = document.getElementById('status');
        btn.disabled = true;
        spinner.classList.remove('d-none');
        status.textContent = 'Crawling… this may take a while';
        try {
          const formData = new FormData(form);
          const resp = await fetch('/', { method: 'POST', body: formData });
          if (!resp.ok) throw new Error('Server returned ' + resp.status);
          const blob = await resp.blob();
          let filename = 'contacts.csv';
          const cd = resp.headers.get('content-disposition');
          if (cd) {
            const m = cd.match(/filename\\*=UTF-8''([^;]+)|filename="?([^";]+)"?/);
            if (m) filename = decodeURIComponent((m[1] || m[2]).replace(/["']/g, ''));
          }
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
          status.textContent = 'Download started';
        } catch (err) {
          console.error(err);
          status.textContent = 'Error: ' + (err.message || 'Unexpected error');
        } finally {
          btn.disabled = false;
          spinner.classList.add('d-none');
          setTimeout(() => { status.textContent = ''; }, 6000);
        }
      }, false);
    })();
    (function () {
      'use strict';
      const form = document.getElementById('gpt-form');
      if (!form) return;
      const promptEl = document.getElementById('gpt_prompt');
      const contextEl = document.getElementById('gpt_context');
      const outputEl = document.getElementById('gpt-output');
      const statusEl = document.getElementById('gpt-status');
      const btn = document.getElementById('gpt-submit-btn');
      const spinner = document.getElementById('gpt-spinner');
      const clearBtn = document.getElementById('gpt-clear-btn');
      clearBtn.addEventListener('click', function () {
        outputEl.textContent = '';
        statusEl.textContent = '';
      });
      form.addEventListener('submit', async function (event) {
        event.preventDefault();
        event.stopPropagation();
        const prompt = (promptEl.value || '').trim();
        const context = (contextEl.value || '').trim();
        if (!prompt) {
          promptEl.focus();
          return;
        }
        btn.disabled = true;
        spinner.classList.remove('d-none');
        statusEl.textContent = 'Asking GPT...';
        try {
          const resp = await fetch('/gpt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, context })
          });
          if (!resp.ok) {
            const errText = await resp.text();
            throw new Error('Server returned ' + resp.status + ' – ' + errText);
          }
          const data = await resp.json();
          outputEl.textContent = data.reply || '(No response text returned)';
          statusEl.textContent = 'Done';
        } catch (err) {
          console.error(err);
          statusEl.textContent = 'Error: ' + (err.message || 'Unexpected error');
        } finally {
          btn.disabled = false;
          spinner.classList.add('d-none');
          setTimeout(() => { statusEl.textContent = ''; }, 6000);
        }
      });
    })();
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Separate template for schedule dashboard (shares overall shell look & feel)
SCHEDULE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Employee Schedule</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root { --bs-primary: #0f766e; }
    body {
      min-height: 100vh;
      background: radial-gradient(circle at top left,#0f172a 0%, #020617 40%, #020617 100%);
      color: #0f172a;
    }
    .app-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
    }
    .sidebar {
      background: radial-gradient(circle at top,#020617 0%, #020617 45%, #020617 100%);
      border-right: 1px solid rgba(148, 163, 184, 0.3);
      color: #e5e7eb;
      display: flex;
      flex-direction: column;
      padding: 1.5rem 1.25rem;
      gap: 1.5rem;
    }
    .sidebar-brand {
      display: flex;
      alignments: center;
      gap: 0.75rem;
    }
    .sidebar-logo {
      height: 40px;
      width: 40px;
      border-radius: 12px;
      background: radial-gradient(circle at 10% 0, #22c55e 0%, #0ea5e9 45%, #1d4ed8 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .sidebar-logo img {
      max-width: 80%;
      max-height: 80%;
      object-fit: contain;
    }
    .sidebar-title {
      font-weight: 600;
      letter-spacing: 0.03em;
      font-size: 0.95rem;
      text-transform: uppercase;
      color: #e5e7eb;
    }
    .sidebar-sub {
      font-size: 0.78rem;
      color: #9ca3af;
    }
    .sidebar-section-title {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #6b7280;
      margin-bottom: 0.4rem;
    }
    .nav-pill {
      border-radius: 0.75rem;
      padding: 0.45rem 0.75rem;
      font-size: 0.9rem;
      color: #e5e7eb;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      text-decoration: none;
      border: 1px solid transparent;
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .nav-pill.active {
      background: rgba(15, 118, 110, 0.2);
      border-color: rgba(45, 212, 191, 0.4);
      color: #ecfeff;
    }
    .nav-pill:hover {
      background: rgba(15, 23, 42, 0.9);
      border-color: rgba(148, 163, 184, 0.5);
      color: #f9fafb;
    }
    .nav-pill-icon {
      width: 24px;
      height: 24px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(15, 23, 42, 0.9);
      color: #a5b4fc;
      font-size: 0.9rem;
    }
    .sidebar-footer {
      margin-top: auto;
      font-size: 0.75rem;
      color: #6b7280;
    }
    .main-shell {
      background: radial-gradient(circle at top,#020617 0%, #020617 40%, #020617 100%);
      padding: 1.25rem 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .topbar-title {
      color: #f9fafb;
      font-weight: 500;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      font-size: 0.8rem;
    }
    .topbar-heading {
      color: #e5e7eb;
      margin: 0.1rem 0 0.15rem;
      font-size: 1.25rem;
      font-weight: 600;
    }
    .topbar-subtitle {
      color: #9ca3af;
      font-size: 0.85rem;
      max-width: 520px;
    }
    .content-shell {
      margin-top: 0.25rem;
      border-radius: 1rem;
      background: radial-gradient(circle at top,#020617 0%, #020617 18%, #020617 45%, #020617 100%);
      border: 1px solid rgba(31, 41, 55, 0.9);
      box-shadow: 0 24px 80px rgba(15, 23, 42, 0.95);
      padding: 1.1rem 1.1rem 1.3rem;
      color: #e5e7eb;
    }
    .small-note { font-size:0.82rem; color:#9ca3af; }
    .schedule-table th,
    .schedule-table td {
      font-size: 0.82rem;
      vertical-align: top;
    }
    .schedule-table th {
      background: #020617;
      color: #9ca3af;
      border-color: rgba(51,65,85,0.9);
      position: sticky;
      top: 0;
      z-index: 5;
    }
    .schedule-table td { border-color: rgba(31,41,55,0.9); }
    .shift-pill {
      display: inline-block;
      padding: 0.1rem 0.4rem;
      border-radius: 999px;
      background: rgba(8,47,73,0.9);
      border: 1px solid rgba(56,189,248,0.7);
      color: #e0f2fe;
      font-size: 0.75rem;
      margin-bottom: 0.15rem;
    }
    .free-pill {
      display: inline-block;
      padding: 0.1rem 0.4rem;
      border-radius: 999px;
      border: 1px dashed rgba(55,65,81,0.8);
      color: #6b7280;
      font-size: 0.75rem;
    }
    @media (max-width: 992px) {
      .app-shell { grid-template-columns: minmax(0, 1fr); }
      .sidebar { display: none; }
      .main-shell { padding: 1rem; }
      .content-shell { padding: 0.9rem; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="sidebar-logo">
          <img src="/static/logo.png" alt="Putzelf Marketing">
        </div>
        <div>
          <div class="sidebar-title">Putzelf Marketing</div>
          <div class="sidebar-sub">Contact Studio</div>
        </div>
      </div>
      <div>
        <div class="sidebar-section-title">Workspace</div>
        <a href="{{ url_for('index') }}" class="nav-pill">
          <span class="nav-pill-icon">◎</span>
          <span>Dashboard</span>
        </a>
      </div>
      <div>
        <div class="sidebar-section-title">People</div>
        <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill active">
          <span class="nav-pill-icon">👤</span>
          <span>Employee schedule</span>
        </a>
        <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">
          <span class="nav-pill-icon">⚙</span>
          <span>Manage employees &amp; sites</span>
        </a>
      </div>
      <div class="sidebar-footer">
        <div>© <span id="year"></span> Putzelf Marketing</div>
        <div class="mt-1">Simple schedule overview for field teams.</div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="mb-2">
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
          <div>
            <div class="topbar-title">People</div>
            <h1 class="topbar-heading mb-0">Employee schedule</h1>
            <p class="topbar-subtitle mb-0">
              See who is on which site this week, when they are free, and assign new shifts.
            </p>
          </div>
          <form method="get" action="{{ url_for('schedule_dashboard') }}" class="d-flex align-items-end gap-2 flex-wrap">
            <div>
              <label class="form-label small-note text-uppercase mb-1" for="filter_employee_id">Focus on employee</label>
              <select class="form-select form-select-sm" id="filter_employee_id" name="employee_id" onchange="this.form.submit()">
                <option value="">All employees</option>
                {% for emp in employees %}
                  <option value="{{ emp.id }}" {% if selected_employee_id == emp.id %}selected{% endif %}>{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
                {% endfor %}
              </select>
            </div>
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <a href="{{ url_for('admin_dashboard') }}" class="btn btn-sm btn-outline-light">Admin panel</a>
              {% if reportlab_available %}
                <a href="{{ pdf_url }}" class="btn btn-sm btn-primary" style="background-color:#0f766e; border-color:#0f766e;">
                  Download PDF
                </a>
              {% else %}
                <span class="small-note">Install <code>reportlab</code> to enable PDF export.</span>
              {% endif %}
              {% if selected_employee %}
                <span class="small-note">Showing {{ selected_employee.name }} only</span>
              {% endif %}
            </div>
          </form>
        </div>
      </header>
      <main class="content-shell">
        <div class="row g-3">
          <div class="col-12 col-lg-4">
            <h2 class="h6 mb-2">Assign a new shift</h2>
            <p class="small-note mb-2">
              Choose an employee, site and time window. Only simple, non-recurring shifts are supported in this first version.
            </p>
            <form method="post" class="small">
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="employee_id">Employee</label>
                <select class="form-select form-select-sm" id="employee_id" name="employee_id" required>
                  <option value="">Select employee…</option>
                  {% for emp in employees %}
                    <option value="{{ emp.id }}">{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="site_id">Site</label>
                <select class="form-select form-select-sm" id="site_id" name="site_id" required>
                  <option value="">Select site…</option>
                  {% for site in sites %}
                    <option value="{{ site.id }}">{{ site.name }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="day">Day</label>
                <input type="date" class="form-control form-control-sm" id="day" name="day" required>
              </div>
              <div class="row">
                <div class="col-6 mb-2">
                  <label class="form-label small-note text-uppercase" for="start_time">Start</label>
                  <input type="time" class="form-control form-control-sm" id="start_time" name="start_time" required>
                </div>
                <div class="col-6 mb-2">
                  <label class="form-label small-note text-uppercase" for="duration_hours">Duration (hours)</label>
                  <input type="number" step="0.25" min="0.25" max="24" class="form-control form-control-sm" id="duration_hours" name="duration_hours" placeholder="e.g. 8" required>
                </div>
              </div>
              <button type="submit" class="btn btn-sm btn-primary mt-2" style="background-color:#0f766e; border-color:#0f766e;">
                Save shift
              </button>
            </form>
            <hr class="my-3">
            <p class="small-note mb-0">
              Tip: An empty cell in the grid means the employee is free for that entire day.
            </p>
          </div>
          <div class="col-12 col-lg-8">
            <h2 class="h6 mb-2">This week</h2>
            <div class="table-responsive" style="max-height:480px;">
              <table class="table table-dark table-bordered table-sm align-middle schedule-table">
                <thead>
                  <tr>
                    <th scope="col">Employee</th>
                    {% for d in week_days %}
                      <th scope="col">
                        {{ d.strftime('%a') }}<br>
                        <span class="small-note">{{ d.strftime('%d.%m') }}</span>
                      </th>
                    {% endfor %}
                  </tr>
                </thead>
                <tbody>
              {% for emp in visible_employees %}
                    <tr>
                      <th scope="row">
                        {{ emp.name }}<br>
                        <span class="small-note">{{ emp.role or '' }}</span>
                      </th>
                      {% for d in week_days %}
                        {% set cell = cells.get((emp.id, d)) %}
                        <td>
                          {% if cell %}
                            {% for label in cell %}
                              <div class="shift-pill">{{ label }}</div><br>
                            {% endfor %}
                          {% else %}
                            <span class="free-pill">Free</span>
                          {% endif %}
                        </td>
                      {% endfor %}
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Admin</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
 
    <style>
    body { background: radial-gradient(circle at top left,#0f172a 0%, #020617 40%, #020617 100%); color:#e5e7eb; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); }
    .sidebar { background: radial-gradient(circle at top,#020617 0%, #020617 45%, #020617 100%); border-right:1px solid rgba(148,163,184,0.3); padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#e5e7eb; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background:rgba(15,118,110,0.2); border-color:rgba(45,212,191,0.4); color:#ecfeff; }
    .main-shell { padding:1.5rem; }
    .card-surface { border-radius:0.9rem; border:1px solid rgba(51,65,85,0.9); background:radial-gradient(circle at top left,#020617 0%, #020617 35%, #020617 100%); padding:1rem; }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#94a3b8; }
    .badge-soft { border-radius:999px; border:1px solid rgba(148,163,184,0.6); color:#9ca3af; padding:0.15rem 0.6rem; font-size:0.75rem; }
    .little-card { border-radius:0.7rem; border:1px solid rgba(51,65,85,0.9); background:rgba(15,23,42,0.8); }
    @media(max-width:992px){ .app-shell{ grid-template-columns:minmax(0,1fr);} .sidebar{ display:none;} }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-section-title text-uppercase">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill active">⚙ <span>Admin</span></a>
      <a href="{{ url_for('index') }}" class="nav-pill">◎ <span>Dashboard</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">👤 <span>Schedule</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell text-light">
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
        <div>
          <div class="badge-soft mb-2">Configuration</div>
          <h1 class="h4 mb-1 text-light">Manage employees & sites</h1>
          <p class="text-secondary mb-0">Entries here feed into the weekly schedule and shift assignments.</p>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <a href="{{ url_for('schedule_dashboard') }}" class="btn btn-sm btn-outline-light">View schedule</a>
          <a href="{{ url_for('index') }}" class="btn btn-sm btn-outline-light">Crawler</a>
        </div>
      </div>
      <div class="row g-3">
        <div class="col-12 col-lg-6">
          <div class="card-surface h-100">
            <h2 class="h6 text-uppercase text-secondary">Employees</h2>
            <form method="post" class="row g-2 mb-3">
              <input type="hidden" name="entity" value="employee">
              <input type="hidden" name="action" value="create">
              <div class="col-6">
                <label class="form-label" for="new_employee_name">Name</label>
                <input type="text" class="form-control form-control-sm" id="new_employee_name" name="name" required>
              </div>
              <div class="col-6">
                <label class="form-label" for="new_employee_role">Role</label>
                <input type="text" class="form-control form-control-sm" id="new_employee_role" name="role">
              </div>
              <div class="col-12">
                <button type="submit" class="btn btn-sm btn-primary">Add employee</button>
              </div>
            </form>
            <div class="vstack gap-2">
              {% for emp in employees %}
                <form method="post" class="little-card p-3">
                  <input type="hidden" name="entity" value="employee">
                  <input type="hidden" name="id" value="{{ emp.id }}">
                  <div class="row g-2">
                    <div class="col-5">
                      <label class="form-label">Name</label>
                      <input type="text" class="form-control form-control-sm" name="name" value="{{ emp.name }}" required>
                    </div>
                    <div class="col-5">
                      <label class="form-label">Role</label>
                      <input type="text" class="form-control form-control-sm" name="role" value="{{ emp.role or '' }}">
                    </div>
                    <div class="col-2 d-flex align-items-end justify-content-end gap-1">
                      <button type="submit" name="action" value="update" class="btn btn-sm btn-success" title="Save">
                        <i class="bi bi-check2"></i>
                      </button>
                      <button type="submit" name="action" value="delete" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete {{ emp.name }}?')" title="Delete">
                        <i class="bi bi-x-lg"></i>
                      </button>
                    </div>
                  </div>
                </form>
              {% else %}
                <p class="text-secondary small mb-0">No employees yet.</p>
              {% endfor %}
            </div>
          </div>
        </div>
        <div class="col-12 col-lg-6">
          <div class="card-surface h-100">
            <h2 class="h6 text-uppercase text-secondary">Sites</h2>
            <form method="post" class="row g-2 mb-3">
              <input type="hidden" name="entity" value="site">
              <input type="hidden" name="action" value="create">
              <div class="col-6">
                <label class="form-label" for="new_site_name">Name</label>
                <input type="text" class="form-control form-control-sm" id="new_site_name" name="name" required>
              </div>
              <div class="col-6">
                <label class="form-label" for="new_site_address">Address</label>
                <input type="text" class="form-control form-control-sm" id="new_site_address" name="address" required>
              </div>
              <div class="col-12">
                <button type="submit" class="btn btn-sm btn-primary">Add site</button>
              </div>
            </form>
            <div class="vstack gap-2">
              {% for site in sites %}
                <form method="post" class="little-card p-3">
                  <input type="hidden" name="entity" value="site">
                  <input type="hidden" name="id" value="{{ site.id }}">
                  <div class="row g-2">
                    <div class="col-5">
                      <label class="form-label">Name</label>
                      <input type="text" class="form-control form-control-sm" name="name" value="{{ site.name }}" required>
                    </div>
                    <div class="col-5">
                      <label class="form-label">Address</label>
                      <input type="text" class="form-control form-control-sm" name="address" value="{{ site.address or '' }}" required>
                    </div>
                    <div class="col-2 d-flex align-items-end justify-content-end gap-1">
                      <button type="submit" name="action" value="update" class="btn btn-sm btn-success" title="Save">
                        <i class="bi bi-check2"></i>
                      </button>
                      <button type="submit" name="action" value="delete" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete {{ site.name }}?')" title="Delete">
                        <i class="bi bi-x-lg"></i>
                      </button>
                    </div>
                  </div>
                </form>
              {% else %}
                <p class="text-secondary small mb-0">No sites yet.</p>
              {% endfor %}
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


def extract_emails(html: str):
    """Extract unique emails from HTML string."""
    return list(set(EMAIL_REGEX.findall(html or "")))


def _normalize_netloc(netloc: str) -> str:
    nl = (netloc or "").lower()
    return nl[4:] if nl.startswith("www.") else nl


def fetch_with_playwright(url: str, timeout: int = 15000) -> str | None:
    """Render page with Playwright and return HTML, or None on error."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        app.logger.debug("Playwright not available: %s", e)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        app.logger.warning("Playwright fetch failed for %s: %s", url, e)
        return None


def fetch_html(url: str, render_js: bool = False, timeout: int = 10):
    """Fetch HTML via requests or Playwright (when render_js=True). Returns (html, status)."""
    headers = {"User-Agent": "PutzelfMarketing/1.0"}
    if render_js:
        html = fetch_with_playwright(url, timeout=(timeout * 1000))
        if html is not None:
            return html, 200

    try:
        resp = requests.get(url, timeout=timeout, headers=headers)
        return resp.text, resp.status_code
    except Exception as e:
        app.logger.warning("requests.get failed for %s: %s", url, e)
        return "", 0


def crawl(start_url: str, max_pages: int = 100, render_js: bool = False):
    """
    Crawl collecting emails and phones with stricter phone extraction rules.
    """
    visited = set()
    queue = deque([start_url])
    url_map = {}

    parsed_start = urlparse(start_url)
    base_domain = _normalize_netloc(parsed_start.netloc)
    start_segments = [s for s in parsed_start.path.split("/") if s]

    VISIBLE_TAGS = ["p", "span", "div", "li", "address", "td", "th"]

    def is_probable_detail_path(path: str) -> bool:
        segs = [s for s in path.split("/") if s]
        if not segs:
            return False
        if len(segs) == 1 and "_" in segs[0] and not segs[0].startswith("_assets"):
            return True
        if len(segs) > 2 and segs[0] == "firmen":
            return True
        return False

    def enqueue(u: str, left: bool = False):
        if u in visited or u in queue:
            return
        if left:
            queue.appendleft(u)
        else:
            queue.append(u)

    while queue and len(visited) < max_pages:
        url = urldefrag(queue.popleft()).url

        if url in visited:
            continue

        parsed = urlparse(url)
        if _normalize_netloc(parsed.netloc) != base_domain:
            app.logger.debug("Skipping external host: %s", url)
            continue

        visited.add(url)
        app.logger.info("Crawling: %s", url)

        html, status = fetch_html(url, render_js=False)
        app.logger.debug("Fetched %s status=%s len=%d (requests)", url, status, len(html or ""))
        try:
            status_num = int(status)
        except Exception:
            status_num = 0
        if not (200 <= status_num < 300):
            app.logger.debug("Skipping non-2xx: %s (%s)", url, status)
            continue

        soup = BeautifulSoup(html or "", "html.parser")

        emails = set(EMAIL_REGEX.findall(html or ""))
        phones = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("tel:"):
                num = href.split("tel:")[1].split("?")[0].strip()
                n = normalize_phone(num)
                if is_valid_phone(n):
                    phones.add(n)

        for tag_name in VISIBLE_TAGS:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(" ", strip=True)
                if not text:
                    continue
                if len(text) > 300:
                    continue
                for n in find_labelled_phones(text):
                    phones.add(n)

        for tag in soup.find_all(attrs=True):
            for attr, val in tag.attrs.items():
                if isinstance(val, str):
                    lower_attr = attr.lower()
                    if any(k in lower_attr for k in ("tel", "phone", "kontakt", "mobil", "fax")):
                        n = normalize_phone(val)
                        if is_valid_phone(n):
                            phones.add(n)
                    else:
                        for n in find_labelled_phones(val):
                            phones.add(n)
                elif isinstance(val, (list, tuple)):
                    for part in val:
                        for n in find_labelled_phones(str(part)):
                            phones.add(n)

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                addr = href.split("mailto:")[1].split("?")[0].strip()
                if EMAIL_REGEX.match(addr):
                    emails.add(addr)

        if not emails and is_probable_detail_path(parsed.path) and render_js:
            app.logger.debug("No emails via requests on probable detail %s — retrying with Playwright", url)
            html_js, status_js = fetch_html(url, render_js=True)
            app.logger.debug("Fetched %s status=%s len=%d (playwright)", url, status_js, len(html_js or ""))
            if html_js:
                soup_js = BeautifulSoup(html_js, "html.parser")
                for e in EMAIL_REGEX.findall(html_js or ""):
                    emails.add(e)
                for a in soup_js.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.lower().startswith("tel:"):
                        num = href.split("tel:")[1].split("?")[0].strip()
                        n = normalize_phone(num)
                        if is_valid_phone(n):
                            phones.add(n)
                    elif href.lower().startswith("mailto:"):
                        addr = href.split("mailto:")[1].split("?")[0].strip()
                        if EMAIL_REGEX.match(addr):
                            emails.add(addr)
                for tag_name in VISIBLE_TAGS:
                    for tag in soup_js.find_all(tag_name):
                        t = tag.get_text(" ", strip=True)
                        if not t or len(t) > 300:
                            continue
                        for n in find_labelled_phones(t):
                            phones.add(n)

        if emails or phones:
            grp = url_map.setdefault(url, {"emails": set(), "phones": set()})
            grp["emails"].update(emails)
            grp["phones"].update(phones)
            for e in emails:
                app.logger.info("Found email %s on %s", e, url)
            for p in phones:
                app.logger.info("Found phone %s on %s", p, url)

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:") or href.lower().startswith("tel:"):
                continue

            link = urldefrag(urljoin(url, href)).url
            parsed_link = urlparse(link)

            if parsed_link.scheme not in ("http", "https"):
                continue
            if _normalize_netloc(parsed_link.netloc) != base_domain:
                continue

            if any(parsed_link.path.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".svg", ".css", ".js")):
                continue

            path_segments = [s for s in parsed_link.path.split("/") if s]

            if len(path_segments) == 1 and "_" in path_segments[0] and not path_segments[0].startswith("_assets"):
                app.logger.debug("Prioritizing single-segment detail link: %s", link)
                enqueue(link, left=True)
                continue

            if len(path_segments) >= 1 and path_segments[0] == "firmen" and len(path_segments) == 2:
                if path_segments != start_segments:
                    app.logger.debug("Skipping region index link: %s", link)
                    continue

            if len(path_segments) > 2 and path_segments[0] == "firmen":
                app.logger.debug("Prioritizing probable detail link: %s", link)
                enqueue(link, left=True)
                continue

            enqueue(link, left=False)

    rows = []
    seen_emails = set()
    seen_phones = set()
    for url, grp in url_map.items():
        emails = grp.get("emails", set())
        phones = grp.get("phones", set())

        if emails:
            phone_sample = next(iter(phones)) if phones else ""
            for email in emails:
                e = email.lower().strip()
                if not e or e in seen_emails:
                    continue
                seen_emails.add(e)
                rows.append({"url": url, "email": email, "phone": phone_sample})
        else:
            for phone in phones:
                p = normalize_phone(phone)
                if not p or p in seen_phones:
                    continue
                if not is_valid_phone(p):
                    continue
                seen_phones.add(p)
                rows.append({"url": url, "email": "", "phone": p})

    app.logger.info("Crawl finished: found %d contact rows", len(rows))
    return rows


def _get_week_days(start: date | None = None):
    """Return list of 7 dates for the week starting Monday containing 'start' (or today)."""
    if start is None:
        start = date.today()
    monday = start - timedelta(days=start.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def _load_schedule_context(db, week_days):
    employees = db.query(Employee).order_by(Employee.name).all()
    sites = db.query(Site).order_by(Site.name).all()
    shifts = db.query(Shift).filter(Shift.day >= week_days[0], Shift.day <= week_days[-1]).all()

    matrix = {}
    for s in shifts:
        key = (s.employee_id, s.day)
        label = f"{s.site.name} — {s.site.address or 'No address'} ({s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')})"
        matrix.setdefault(key, []).append(label)
    for key in matrix:
        matrix[key].sort()
    return employees, sites, matrix


def _generate_schedule_pdf(week_days, employees, matrix):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=32,
        rightMargin=32,
        topMargin=32,
        bottomMargin=28,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontName = "Helvetica-Bold"
    title_style.textColor = colors.HexColor("#0f172a")
    subtitle_style = styles["Heading4"]
    subtitle_style.fontName = "Helvetica"
    subtitle_style.textColor = colors.HexColor("#475569")
    header_style = ParagraphStyle(
        "ScheduleHeader",
        parent=styles["Heading5"],
        alignment=1,
        fontSize=11,
        leading=13,
    )
    cell_style = ParagraphStyle(
        "ScheduleCell",
        parent=styles["BodyText"],
        leading=12,
    )
    elements = []

    logo_path = os.path.join(app.root_path, "static", "logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.2 * inch, height=1.2 * inch)
        logo.hAlign = "LEFT"
        elements.append(logo)
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("Weekly Employee Schedule", title_style))
    elements.append(
        Paragraph(
            f"{week_days[0].strftime('%d %b %Y')} &ndash; {week_days[-1].strftime('%d %b %Y')}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 16))

    header = [Paragraph("<b>Employee</b>", header_style)]
    for d in week_days:
        header.append(
            Paragraph(
                f"{d.strftime('%a')}<br/><font size='9'>{d.strftime('%d %b')}</font>",
                header_style,
            )
        )
    data = [header]
    for emp in employees:
        header_line = emp.name
        if emp.role:
            header_line += f"<br/><font color='#94a3b8' size='9'>{emp.role}</font>"
        row = [Paragraph(header_line, cell_style)]
        for day in week_days:
            cell_items = matrix.get((emp.id, day), [])
            if not cell_items:
                row.append(Paragraph("<font color='#9ca3af'>Free</font>", cell_style))
            else:
                bullet = "<br/>".join(
                    f"<font color='#0f172a'><b>{item.split(' — ')[0]}</b></font>"
                    f"<br/><font color='#475569'>{' — '.join(item.split(' — ')[1:])}</font>"
                    for item in cell_items
                )
                row.append(Paragraph(bullet, cell_style))
        data.append(row)

    table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[1.9 * inch] + [1.2 * inch] * 7)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
                ("LINEBEFORE", (1, 0), (-1, -1), 0.4, colors.HexColor("#cbd5f5")),
                ("LINEABOVE", (0, 1), (-1, -1), 0.3, colors.HexColor("#cbd5f5")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#0f172a")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf


@app.route("/schedule", methods=["GET", "POST"])
def schedule_dashboard():
    db = SessionLocal()
    try:
        if request.method == "POST":
            emp_id = request.form.get("employee_id")
            site_id = request.form.get("site_id")
            day_str = request.form.get("day")
            start_str = request.form.get("start_time")
            duration_hours_str = request.form.get("duration_hours")
            if emp_id and site_id and day_str and start_str and duration_hours_str:
                day_val = datetime.strptime(day_str, "%Y-%m-%d").date()
                start_val = datetime.strptime(start_str, "%H:%M").time()
                try:
                    duration_hours = float(duration_hours_str)
                except (TypeError, ValueError):
                    duration_hours = 0
                if duration_hours > 0 and duration_hours <= 24:
                    duration_delta = timedelta(hours=duration_hours)
                    end_dt = datetime.combine(day_val, start_val) + duration_delta
                    end_val = end_dt.time()
                    shift = Shift(
                        employee_id=int(emp_id),
                        site_id=int(site_id),
                        day=day_val,
                        start_time=start_val,
                        end_time=end_val,
                    )
                    db.add(shift)
                    db.commit()
            return redirect(url_for("schedule_dashboard"))

        selected_employee_id = request.args.get("employee_id", type=int)

        week_days = _get_week_days()
        employees, sites, matrix = _load_schedule_context(db, week_days)

        selected_employee = None
        visible_employees = employees
        if selected_employee_id:
            selected_employee = next((e for e in employees if e.id == selected_employee_id), None)
            if selected_employee:
                visible_employees = [selected_employee]

        pdf_params = {"week": week_days[0].isoformat()}
        if selected_employee_id:
            pdf_params["employee_id"] = selected_employee_id
        pdf_url = url_for("schedule_pdf", **pdf_params)

        schedule_html = render_template_string(
            SCHEDULE_TEMPLATE,
            employees=employees,
            visible_employees=visible_employees,
            sites=sites,
            week_days=week_days,
            cells=matrix,
            reportlab_available=REPORTLAB_AVAILABLE,
            selected_employee_id=selected_employee_id,
            selected_employee=selected_employee,
            pdf_url=pdf_url,
        )
        return schedule_html
    finally:
        db.close()


@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    db = SessionLocal()
    try:
        if request.method == "POST":
            entity = (request.form.get("entity") or "").strip()
            action = (request.form.get("action") or "").strip()
            if entity == "employee":
                emp_id = request.form.get("id")
                if action == "create":
                    name = (request.form.get("name") or "").strip()
                    role = (request.form.get("role") or "").strip()
                    if name:
                        db.add(Employee(name=name, role=role or None))
                        db.commit()
                elif action == "update" and emp_id:
                    emp = db.get(Employee, int(emp_id))
                    if emp:
                        emp.name = (request.form.get("name") or "").strip() or emp.name
                        emp.role = (request.form.get("role") or "").strip() or None
                        db.commit()
                elif action == "delete" and emp_id:
                    emp = db.get(Employee, int(emp_id))
                    if emp:
                        db.delete(emp)
                        db.commit()
            elif entity == "site":
                site_id = request.form.get("id")
                if action == "create":
                    name = (request.form.get("name") or "").strip()
                    address = (request.form.get("address") or "").strip()
                    if name and address:
                        db.add(Site(name=name, address=address))
                        db.commit()
                elif action == "update" and site_id:
                    site = db.get(Site, int(site_id))
                    if site:
                        site.name = (request.form.get("name") or "").strip() or site.name
                        site.address = (request.form.get("address") or "").strip() or ""
                        db.commit()
                elif action == "delete" and site_id:
                    site = db.get(Site, int(site_id))
                    if site:
                        db.delete(site)
                        db.commit()
            return redirect(url_for("admin_dashboard"))

        employees = db.query(Employee).order_by(Employee.name).all()
        sites = db.query(Site).order_by(Site.name).all()
        return render_template_string(
            ADMIN_TEMPLATE,
            employees=employees,
            sites=sites,
        )
    finally:
        db.close()


@app.route("/schedule/pdf")
def schedule_pdf():
    if not REPORTLAB_AVAILABLE:
        return jsonify({"error": "reportlab not installed"}), 503

    week_param = request.args.get("week")
    employee_id = request.args.get("employee_id", type=int)
    ref_date = None
    if week_param:
        try:
            ref_date = datetime.strptime(week_param, "%Y-%m-%d").date()
        except ValueError:
            ref_date = None
    week_days = _get_week_days(ref_date)

    db = SessionLocal()
    try:
        employees, _, matrix = _load_schedule_context(db, week_days)
        if employee_id:
            employees = [e for e in employees if e.id == employee_id]
            if not employees:
                return jsonify({"error": "Employee not found"}), 404
        pdf_buffer = _generate_schedule_pdf(week_days, employees, matrix)
    finally:
        db.close()

    filename = f"schedule_{week_days[0].isoformat()}_{week_days[-1].isoformat()}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_TEMPLATE, gpt_enabled=bool(openai_client))

    start_url = request.form.get("start_url")
    try:
        max_pages = int(request.form.get("max_pages", "100"))
    except Exception:
        max_pages = 100
    max_pages = max(1, min(max_pages, 200))

    render_js = bool(request.form.get("render_js"))

    data = crawl(start_url, max_pages=max_pages, render_js=render_js)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["url", "email", "phone"])
    writer.writeheader()
    for row in data:
        writer.writerow({"url": row.get("url", ""), "email": row.get("email", ""), "phone": row.get("phone", "")})

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="putzelf_contacts.csv",
    )


@app.route("/gpt", methods=["POST"])
def gpt_assistant():
    if openai_client is None:
        return (
            jsonify(
                {
                    "error": "GPT integration is not configured. "
                    "Set OPENAI_API_KEY and install the 'openai' package."
                }
            ),
            503,
        )

    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get("prompt") or "").trim()
        context = (data.get("context") or "").strip()
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400

        system_message = (
            "You are a helpful outreach copywriting assistant working inside a small CRM tool. "
            "The user just crawled business websites for contact details. "
            "Write concise, professional, friendly copy. Prefer short paragraphs and bullet points. "
            "If they provide contacts or context, tailor the message to that audience."
        )

        user_content = prompt
        if context:
            user_content += "\n\n=== Context / contacts ===\n" + context

        completion = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_content},
            ],
            temperature=0.7,
        )

        reply = completion.choices[0].message.content if completion.choices else ""
        return jsonify({"reply": reply})
    except Exception as e:  # pragma: no cover - defensive
        app.logger.warning("GPT endpoint error: %s", e)
        return jsonify({"error": "Failed to contact GPT backend."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)