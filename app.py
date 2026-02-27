import math
import re
import io
import csv
import logging
import os
import sys
import secrets
from collections import deque
from datetime import datetime, date, timedelta
from functools import wraps
from typing import Any, Tuple
from urllib.parse import urljoin, urldefrag, urlparse, quote_plus
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
  session,
  flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import (
  create_engine,
  Column,
  Integer,
  Boolean,
  String,
  Date,
  Time,
  ForeignKey,
  or_,
  func,
  DateTime,
  Text,
  text,
  Float,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session, joinedload

ADMIN_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Admin Overview</title>
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
    body.mobile-nav-open { overflow:hidden; }
    body.mobile-nav-open { overflow:hidden; }
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
    .metrics-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; }
    .metric-card { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1rem; box-shadow:0 12px 24px rgba(15,23,42,0.08); }
    .metric-label { font-size:0.75rem; letter-spacing:0.08em; text-transform:uppercase; color:#475569; margin-bottom:0.35rem; }
    .metric-value { font-size:2rem; font-weight:600; color:#0f172a; margin-bottom:0.1rem; }
    .metric-sub { font-size:0.85rem; color:#64748b; }
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
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.2rem; height:100%; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .list-entry { border-bottom:1px solid #e2e8f0; padding:0.6rem 0; }
    .list-entry:last-child { border-bottom:none; }
    .list-title { font-weight:600; color:#0f172a; }
    .list-sub { font-size:0.85rem; color:#64748b; }
    .placeholder { color:#94a3b8; font-size:0.85rem; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    @media(max-width:992px){ .app-shell{ grid-template-columns:minmax(0,1fr);} .sidebar{ display:none;} }
    @media (max-width: 992px) {
      .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: min(82vw, 300px);
        max-width: 320px;
        z-index: 1050;
        display: flex;
        transform: translateX(-100%);
        transition: transform 0.2s ease;
        box-shadow: 0 24px 48px rgba(15,23,42,0.12);
      }
      body.mobile-nav-open .sidebar { transform: translateX(0); }
      .mobile-nav-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.35);
        z-index: 1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop { display: block; }
      .mobile-nav-toggle {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 0.75rem;
        border: 0;
        background-image: var(--btn-grad-accent);
        color: #ffffff;
        padding: 0.45rem 0.85rem;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        box-shadow: 0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus { outline: 2px solid rgba(15,118,110,0.4); outline-offset: 2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-section-title">Navigation</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">📇 <span class="nav-text">Lead-Center</span></a>
      <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill {% if active_page == 'invoices' %}active{% endif %}">📄 <span class="nav-text">Invoices</span></a>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      <div class="mt-auto small text-muted">© <span id="year"></span> Putzelf Marketing</div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category == 'warning' else 'info' }} border-0 text-dark" role="alert">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="mb-4">
        <div class="badge-soft mb-2">Operations overview</div>
        <h1 class="h4 text-dark mb-1">This week at a glance</h1>
        <p class="text-secondary mb-0">{{ today_label }} · Week {{ week_label }}</p>
      </header>

      <section class="metrics-grid mb-4">
        <div class="metric-card">
          <div class="metric-label">Employees</div>
          <div class="metric-value">{{ stats.employees }}</div>
          <div class="metric-sub">Active in the roster</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Sites</div>
          <div class="metric-value">{{ stats.sites }}</div>
          <div class="metric-sub">Locations to cover</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Shifts this week</div>
          <div class="metric-value">{{ stats.weekly_shifts }}</div>
          <div class="metric-sub">Scheduled between {{ week_label }}</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">New leads</div>
          <div class="metric-value">{{ stats.new_leads }}</div>
          <div class="metric-sub">Arrived in the last 7 days</div>
        </div>
        <div class="metric-card">
          <div class="metric-label">Unassigned sites</div>
          <div class="metric-value">{{ stats.unassigned_sites }}</div>
          <div class="metric-sub">Need a shift this week</div>
        </div>
      </section>

      <section class="row g-3">
        <div class="col-12 col-lg-6">
          <div class="card-surface">
            <h2 class="h6 text-uppercase text-secondary mb-3">Recently added employees</h2>
            {% if recent_employees %}
              {% for emp in recent_employees %}
                <div class="list-entry">
                  <div class="list-title">{{ emp.name }}</div>
                  <div class="list-sub">{{ emp.role or 'No role yet' }}</div>
                </div>
              {% endfor %}
            {% else %}
              <p class="placeholder mb-0">No employees registered yet.</p>
            {% endif %}
            <a href="{{ url_for('admin_employees') }}" class="btn btn-sm btn-outline-primary mt-3">Manage employees</a>
          </div>
        </div>
        <div class="col-12 col-lg-6">
          <div class="card-surface">
            <h2 class="h6 text-uppercase text-secondary mb-3">Newest sites</h2>
            {% if recent_sites %}
              {% for site in recent_sites %}
                <div class="list-entry">
                  <div class="list-title">{{ site.name }}</div>
                  <div class="list-sub">{{ site.address or 'Address TBD' }}</div>
                </div>
              {% endfor %}
            {% else %}
              <p class="placeholder mb-0">No sites have been added yet.</p>
            {% endif %}
            <a href="{{ url_for('admin_sites') }}" class="btn btn-sm btn-outline-primary mt-3">Manage sites</a>
          </div>
        </div>
      </section>

      <section class="row g-3 mt-1">
        <div class="col-12 col-lg-7">
          <div class="card-surface">
            <h2 class="h6 text-uppercase text-secondary mb-3">Upcoming shifts</h2>
            {% if upcoming_shifts %}
              {% for shift in upcoming_shifts %}
                <div class="list-entry d-flex justify-content-between align-items-start">
                  <div>
                    <div class="list-title">{{ shift.employee.name if shift.employee else 'Unassigned' }}</div>
                    <div class="list-sub">{{ shift.site.name if shift.site else 'No site set' }}</div>
                  </div>
                  <div class="text-end text-secondary small">
                    {{ shift.day.strftime('%d %b') }} · {{ shift.start_time.strftime('%H:%M') }} – {{ shift.end_time.strftime('%H:%M') }}
                  </div>
                </div>
              {% endfor %}
            {% else %}
              <p class="placeholder mb-0">No shifts scheduled yet. Add some from the schedule view.</p>
            {% endif %}
            <a href="{{ url_for('schedule_dashboard') }}" class="btn btn-sm btn-outline-primary mt-3">Go to schedule</a>
          </div>
        </div>
        <div class="col-12 col-lg-5">
          <div class="card-surface">
            <h2 class="h6 text-uppercase text-secondary mb-3">Sites without coverage</h2>
            {% if unassigned_sites_sample %}
              {% for site in unassigned_sites_sample %}
                <div class="list-entry">
                  <div class="list-title">{{ site.name }}</div>
                  <div class="list-sub">{{ site.address or 'Address TBD' }}</div>
                </div>
              {% endfor %}
            {% else %}
              <p class="placeholder mb-0">All sites are covered for the current week.</p>
            {% endif %}
            <a href="{{ url_for('admin_sites') }}" class="btn btn-sm btn-outline-primary mt-3">Assign coverage</a>
          </div>
        </div>
      </section>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
  </script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    (function() {
      const body = document.body;
      const toggle = document.getElementById('mobile-nav-toggle');
      const sidebar = document.getElementById('admin-sidebar');
      const backdrop = document.getElementById('mobile-nav-backdrop');
      if (!toggle || !sidebar || !backdrop) {
        return;
      }
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        if (body.classList.contains('mobile-nav-open')) {
          closeNav();
        } else {
          openNav();
        }
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', closeNav);
      });
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

ADMIN_EMPLOYEES_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Employees</title>
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
    .form-control, .form-select, .input-group-text {
      background:#ffffff;
      color:#0f172a;
      border:1.5px solid #94a3b8;
    }
    .form-control::placeholder { color:#64748b; opacity:1; }
    .form-control:focus, .form-select:focus {
      border-color:#0f766e;
      box-shadow:0 0 0 3px rgba(15,118,110,0.15);
      background:#ffffff;
      color:#0f172a;
    }
    .little-card { border-radius:0.85rem; border:1px solid #e2e8f0; background:#f8fafc; }
    .credential-box { border-radius:0.85rem; border:1px solid #cbd5f5; background:#f8fafc; padding:1rem; }
    .credential-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:0.75rem; }
    .credential-label { font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase; color:#64748b; }
    .credential-value { font-size:1rem; font-weight:600; color:#0f172a; }
    .credential-note { font-size:0.78rem; color:#0f766e; }
    .credential-actions { display:flex; flex-wrap:wrap; gap:0.5rem; }
    .employee-action-buttons { display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:flex-end; }
    .employee-action-buttons .btn { flex:1 1 120px; }
    @media(max-width:768px){ .employee-action-buttons { justify-content:flex-start; } .employee-action-buttons .btn { flex:1 1 100%; } }
    .assignment-section { border-radius:0.75rem; border:1px dashed #cbd5f5; background:#f8fafc; padding:0.85rem; }
    .assignment-collapse { margin:0; border-radius:0.6rem; overflow:hidden; background:#ffffff; border:1px solid #e2e8f0; box-shadow:0 8px 16px rgba(15,23,42,0.05); }
    .assignment-collapse + .assignment-collapse { margin-top:0.65rem; }
    .assignment-collapse summary { cursor:pointer; list-style:none; display:flex; justify-content:space-between; align-items:center; gap:0.5rem; padding:0.75rem 0.85rem; font-weight:600; color:#0f172a; user-select:none; }
    .assignment-collapse summary::-webkit-details-marker { display:none; }
    .assignment-count { font-size:0.82rem; letter-spacing:0.08em; text-transform:uppercase; color:#64748b; }
    .assignment-list { margin:0; padding:0.15rem 0.85rem 0.8rem; list-style:none; display:grid; gap:0.6rem; }
    .assignment-list li { padding:0.6rem 0.55rem 0.55rem; border-radius:0.6rem; border:1px solid #e2e8f0; background:#ffffff; }
    .assignment-primary { font-weight:600; color:#0f172a; }
    .assignment-meta { font-size:0.85rem; color:#64748b; }
    .assignment-status { font-size:0.78rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.08em; margin-top:0.2rem; }
    .credential-edit { border:1px dashed #cbd5f5; border-radius:0.75rem; padding:1rem; background:#ffffff; }
    .placeholder { color:#94a3b8; font-size:0.85rem; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    .stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin-bottom:1.5rem; }
    .stat-card { border-radius:0.85rem; border:1px solid #e2e8f0; background:#ffffff; padding:1rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .stat-label { font-size:0.75rem; letter-spacing:0.08em; text-transform:uppercase; color:#475569; margin-bottom:0.35rem; }
    .stat-value { font-size:1.6rem; font-weight:600; color:#0f172a; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn { border:1px solid rgba(15,23,42,0.18); }
    .btn i { font-size:1.05rem; }
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
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">📇 <span class="nav-text">Lead-Center</span></a>
      <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill {% if active_page == 'invoices' %}active{% endif %}">📄 <span class="nav-text">Invoices</span></a>
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
        <div class="badge-soft mb-2">Team directory</div>
        <h1 class="h4 text-dark mb-1">Manage employees</h1>
        <p class="text-secondary mb-0">
          {% if filtered_employees %}
            Showing {{ page_employees }} of {{ filtered_employees }} matching
          {% else %}
            No employees match the current filters
          {% endif %}
          · {{ total_employees }} total · {{ today_shifts }} shifts today
        </p>
      </header>
      <div class="mb-3 d-flex justify-content-end">
        <a href="{{ url_for('admin_profiles', tab='employees') }}" class="btn btn-sm btn-outline-primary">Open employee profiles</a>
      </div>

      <section class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total employees</div>
          <div class="stat-value">{{ total_employees }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Showing now</div>
          <div class="stat-value">{{ page_employees }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">On schedule today</div>
          <div class="stat-value">{{ today_shifts }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Unassigned this week</div>
          <div class="stat-value">{{ unassigned_employees }}</div>
        </div>
      </section>

      <section class="card-surface mb-4">
        <form method="get" class="row g-2 align-items-end">
          <div class="col-sm-8">
            <label class="form-label" for="employee_search">Search employees</label>
            <div class="input-group input-group-sm">
              <input type="text" class="form-control" id="employee_search" name="q" value="{{ search_q or '' }}" placeholder="Search by name or role">
              <button class="btn btn-outline-primary" type="submit" title="Search"><i class="bi bi-search"></i></button>
            </div>
          </div>
          <div class="col-sm-4">
            <a href="{{ url_for('admin_employees') }}" class="btn btn-sm btn-outline-secondary w-100" title="Clear filters"><i class="bi bi-x-circle"></i></a>
          </div>
        </form>
      </section>

      <div class="row g-3">
        <div class="col-12 col-lg-4">
          <div class="card-surface mb-3">
            <h2 class="h6 text-uppercase text-secondary mb-3">Add employee</h2>
            <form method="post" class="row g-3">
              <input type="hidden" name="action" value="create">
              <div class="col-12">
                <label class="form-label" for="new_employee_name">Name</label>
                <input type="text" class="form-control form-control-sm" id="new_employee_name" name="name" required>
              </div>
              <div class="col-12">
                <label class="form-label" for="new_employee_role">Role</label>
                <input type="text" class="form-control form-control-sm" id="new_employee_role" name="role" value="Cleaner">
              </div>
              <div class="col-12">
                <button type="submit" class="btn btn-sm btn-primary w-100" title="Add employee"><i class="bi bi-person-plus"></i></button>
              </div>
            </form>
          </div>
        </div>
        <div class="col-12 col-lg-8">
            {% if employees %}
              <div class="vstack gap-3">
                {% for emp in employees %}
                  <div class="little-card p-3">
                    <form method="post" class="row g-2 align-items-end">
                      <input type="hidden" name="id" value="{{ emp.id }}">
                      <input type="hidden" name="redirect_page" value="{{ page }}">
                      {% if search_q %}
                        <input type="hidden" name="redirect_q" value="{{ search_q }}">
                      {% endif %}
                      <div class="col-md-5 col-12">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-control form-control-sm" name="name" value="{{ emp.name }}" required>
                      </div>
                      <div class="col-md-5 col-12">
                        <label class="form-label">Role</label>
                        <input type="text" class="form-control form-control-sm" name="role" value="{{ emp.role or '' }}">
                      </div>
                      <div class="col-md-2 col-12 employee-action-buttons">
                        <button type="submit" name="action" value="update" class="btn btn-sm btn-success" title="Save"><i class="bi bi-check2"></i></button>
                        <button type="submit" name="action" value="delete" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete {{ emp.name }}?')" title="Delete"><i class="bi bi-trash"></i></button>
                      </div>
                    </form>
                    <div class="small text-secondary mt-2">Shifts scheduled: <span class="text-primary">{{ shift_counts.get(emp.id, 0) }}</span></div>

                    {% set snippet = (credential_snippets|default({})).get(emp.id|string) %}
                    {% set code_display = snippet.code if snippet and snippet.code else (emp.login_code or 'Pending') %}
                    {% set pin_display = snippet.pin if snippet and snippet.pin else None %}

                    <div class="credential-box mt-3">
                      <div class="credential-grid">
                        <div>
                          <div class="credential-label">Login code</div>
                          <div class="credential-value">{{ code_display }}</div>
                        </div>
                        <div>
                          <div class="credential-label">PIN</div>
                          <div class="credential-value">
                            {% if pin_display %}
                              {{ pin_display }}
                            {% elif emp.login_pin_hash %}
                              Hidden — use Share to refresh
                            {% else %}
                              Generating…
                            {% endif %}
                          </div>
                        </div>
                        <div>
                          <div class="credential-label">Login email</div>
                          <div class="credential-value">{{ emp.login_email or 'Not set' }}</div>
                        </div>
                      </div>
                      {% if pin_display %}
                        <div class="credential-note mt-2">New PIN generated — share it with {{ emp.name }} soon.</div>
                      {% endif %}
                    </div>

                    <div class="credential-actions mt-3">
                      <form method="post" class="d-inline">
                        <input type="hidden" name="action" value="credentials_share">
                        <input type="hidden" name="id" value="{{ emp.id }}">
                        {% if search_q %}
                          <input type="hidden" name="redirect_q" value="{{ search_q }}">
                        {% endif %}
                        <input type="hidden" name="redirect_page" value="{{ page }}">
                        <button type="submit" class="btn btn-sm btn-outline-info">Share new PIN</button>
                      </form>
                      {% if pin_display %}
                        {% set share_text = 'Login code: ' ~ code_display ~ ' · PIN: ' ~ pin_display %}
                        <button type="button" class="btn btn-sm btn-outline-light cred-copy-btn" data-credentials="{{ share_text }}">Copy details</button>
                      {% endif %}
                      <button type="button" class="btn btn-sm btn-outline-secondary cred-edit-btn" data-edit-target="cred-edit-{{ emp.id }}" aria-expanded="false">Edit</button>
                    </div>

                    <div class="credential-edit d-none mt-3" id="cred-edit-{{ emp.id }}">
                      <form method="post" class="row g-2 align-items-end">
                        <input type="hidden" name="action" value="credentials_update">
                        <input type="hidden" name="id" value="{{ emp.id }}">
                        {% if search_q %}
                          <input type="hidden" name="redirect_q" value="{{ search_q }}">
                        {% endif %}
                        <input type="hidden" name="redirect_page" value="{{ page }}">
                        <div class="col-md-4 col-12">
                          <label class="form-label">Login email</label>
                          <input type="email" class="form-control form-control-sm" name="login_email" value="{{ emp.login_email or '' }}" placeholder="Optional email">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Login code</label>
                          <input type="text" class="form-control form-control-sm" name="login_code" value="{{ code_display }}" required>
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">New PIN (4 digits)</label>
                          <input type="text" class="form-control form-control-sm" name="login_pin" pattern="\d{4}" placeholder="Leave blank to keep">
                        </div>
                        <div class="col-12 d-flex justify-content-end gap-2">
                          <button type="submit" class="btn btn-sm btn-success">Save credentials</button>
                        </div>
                      </form>
                    </div>

                    {% set shift_block = employee_shift_groups.get(emp.id, {}) %}
                    {% set future_jobs = shift_block.get('upcoming', []) %}
                    {% set past_jobs = shift_block.get('history', []) %}
                    <div class="assignment-section mt-3">
                      <details class="assignment-collapse">
                        <summary>
                          <span>Upcoming jobs</span>
                          <span class="assignment-count">{{ future_jobs|length }}</span>
                        </summary>
                        {% if future_jobs %}
                          <ul class="assignment-list">
                            {% for job in future_jobs %}
                              <li>
                                <div class="assignment-primary">{{ job.site_name }}</div>
                                <div class="assignment-meta">{{ job.day_label }} · {{ job.time_window }}</div>
                                <div class="assignment-status">{{ job.status_label }}</div>
                              </li>
                            {% endfor %}
                          </ul>
                        {% else %}
                          <div class="placeholder px-3 pb-3">No upcoming jobs yet.</div>
                        {% endif %}
                      </details>
                      <details class="assignment-collapse">
                        <summary>
                          <span>Previous jobs</span>
                          <span class="assignment-count">{{ past_jobs|length }}</span>
                        </summary>
                        {% if past_jobs %}
                          <ul class="assignment-list">
                            {% for job in past_jobs %}
                              <li>
                                <div class="assignment-primary">{{ job.site_name }}</div>
                                <div class="assignment-meta">{{ job.day_label }} · {{ job.time_window }}</div>
                                <div class="assignment-status">{{ job.status_label }}</div>
                              </li>
                            {% endfor %}
                          </ul>
                        {% else %}
                          <div class="placeholder px-3 pb-3">No completed jobs yet.</div>
                        {% endif %}
                      </details>
                    </div>
                  </div>
                {% endfor %}
              </div>
              {% if total_pages > 1 %}
                <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mt-4">
                  <span class="text-secondary small">Page {{ page }} of {{ total_pages }}</span>
                  <div class="btn-group" role="group" aria-label="Employee pagination">
                    {% if has_prev %}
                      {% if search_q %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=prev_page, q=search_q) }}">Previous</a>
                      {% else %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=prev_page) }}">Previous</a>
                      {% endif %}
                    {% else %}
                      <span class="btn btn-sm btn-outline-secondary disabled" aria-disabled="true">Previous</span>
                    {% endif %}
                    {% for page_num in range(1, total_pages + 1) %}
                      {% if page_num == page %}
                        <span class="btn btn-sm btn-primary disabled" aria-current="page">{{ page_num }}</span>
                      {% else %}
                        {% if search_q %}
                          <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=page_num, q=search_q) }}">{{ page_num }}</a>
                        {% else %}
                          <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=page_num) }}">{{ page_num }}</a>
                        {% endif %}
                      {% endif %}
                    {% endfor %}
                    {% if has_next %}
                      {% if search_q %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=next_page, q=search_q) }}">Next</a>
                      {% else %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=next_page) }}">Next</a>
                      {% endif %}
                    {% else %}
                      <span class="btn btn-sm btn-outline-secondary disabled" aria-disabled="true">Next</span>
                    {% endif %}
                  </div>
                </div>
              {% endif %}
            {% else %}
            <div class="card-surface">
              <p class="placeholder mb-0">No employees match this filter. Try broadening your search.</p>
            </div>
          {% endif %}
        </div>
      </div>
    </main>
  </div>
    <script>
      document.getElementById('year').textContent = new Date().getFullYear();
      (function() {
        const body = document.body;
        const toggle = document.getElementById('mobile-nav-toggle');
        const sidebar = document.getElementById('admin-sidebar');
        const backdrop = document.getElementById('mobile-nav-backdrop');
        if (!toggle || !sidebar || !backdrop) {
          return;
        }
        const closeNav = () => {
          body.classList.remove('mobile-nav-open');
          toggle.setAttribute('aria-expanded', 'false');
        };
        const openNav = () => {
          body.classList.add('mobile-nav-open');
          toggle.setAttribute('aria-expanded', 'true');
        };
        toggle.addEventListener('click', () => {
          if (body.classList.contains('mobile-nav-open')) {
            closeNav();
          } else {
            openNav();
          }
        });
        backdrop.addEventListener('click', closeNav);
        sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeNav));
      })();
      document.querySelectorAll('.cred-copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const payload = btn.dataset.credentials;
          if (!payload) {
            return;
          }
          const original = btn.textContent;
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(payload).then(() => {
              btn.textContent = 'Copied!';
              setTimeout(() => { btn.textContent = original; }, 1800);
            }).catch(() => {
              window.prompt('Copy credentials:', payload);
            });
          } else {
            window.prompt('Copy credentials:', payload);
          }
        });
      });
      document.querySelectorAll('.cred-edit-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const targetId = btn.dataset.editTarget;
          const target = document.getElementById(targetId);
          if (!target) {
            return;
          }
          const isHidden = target.classList.contains('d-none');
          if (isHidden) {
            target.classList.remove('d-none');
            btn.setAttribute('aria-expanded', 'true');
          } else {
            target.classList.add('d-none');
            btn.setAttribute('aria-expanded', 'false');
          }
        });
      });
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

ADMIN_SITES_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Site Library</title>
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
    body.mobile-nav-open { overflow:hidden; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); transition:grid-template-columns 0.2s ease; background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.5rem; width:260px; transition: width 0.2s ease, padding 0.2s ease; color:#0f172a; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active, .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-text { display:inline; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .main-shell { padding:1.75rem; background:#ffffff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.25rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .form-label { text-transform:uppercase; font-size:0.75rem; letter-spacing:0.08em; color:#475569; }
    .form-control, .form-select, .input-group-text {
      background:#ffffff;
      color:#0f172a;
      border:1.5px solid #94a3b8;
    }
    .form-control::placeholder { color:#64748b; opacity:1; }
    .form-control:focus, .form-select:focus {
      border-color:#0f766e;
      box-shadow:0 0 0 3px rgba(15,118,110,0.15);
      background:#ffffff;
      color:#0f172a;
    }
    .little-card { border-radius:0.85rem; border:1px solid #e2e8f0; background:#f8fafc; }
    .placeholder { color:#94a3b8; font-size:0.85rem; }
    .table thead th { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:#475569; background:#f1f5f9; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; transition:transform 0.15s ease, box-shadow 0.15s ease; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .btn { border:1px solid rgba(15,23,42,0.18); }
    .btn i { font-size:1.05rem; }
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
    .btn-clear-sites {
      min-height:2rem;
      padding:0.35rem 0.55rem;
      border-radius:0.65rem;
      background-image:linear-gradient(135deg,#e0f2fe 0%,#bae6fd 100%);
      color:#0c4a6e;
      border:1px solid #7dd3fc;
      box-shadow:0 6px 12px rgba(14,116,144,0.12);
    }
    .btn-clear-sites:hover {
      background-image:linear-gradient(135deg,#bae6fd 0%,#7dd3fc 100%);
      color:#083344;
    }
    .site-row-actions .btn {
      min-height:2rem;
      padding:0.35rem 0.55rem;
      border-radius:0.6rem;
    }
    .stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin-bottom:1.5rem; }
    .stat-card { border-radius:0.85rem; border:1px solid #e2e8f0; background:#ffffff; padding:1rem; box-shadow:0 10px 20px rgba(15,23,42,0.06); }
    .stat-label { font-size:0.75rem; letter-spacing:0.08em; text-transform:uppercase; color:#475569; margin-bottom:0.35rem; }
    .stat-value { font-size:1.6rem; font-weight:600; color:#0f172a; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
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
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">⚙ <span class="nav-text">Overview</span></a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">👥 <span class="nav-text">Manage employees</span></a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">🏢 <span class="nav-text">Manage sites</span></a>
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">📇 <span class="nav-text">Lead-Center</span></a>
      <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">◎ <span class="nav-text">Crawler</span></a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill {% if active_page == 'invoices' %}active{% endif %}">📄 <span class="nav-text">Invoices</span></a>
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
              <div class="alert alert-{{ 'warning' if category=='warning' else 'info' }} border-0 text-dark">
                {{ message }}
              </div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}
      <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-4">
        <div>
          <div class="badge-soft mb-2">Location library</div>
          <h1 class="h3 mb-1 text-dark">Manage client sites</h1>
          <p class="text-secondary mb-0">
            {% if filtered_sites %}
              Showing {{ page_sites }} of {{ filtered_sites }} matching
            {% else %}
              No sites match the current filters
            {% endif %}
            · {{ total_sites }} total sites
          </p>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <a href="{{ url_for('admin_profiles', tab='clients') }}" class="btn btn-sm btn-outline-primary">Client profiles</a>
          <a href="{{ url_for('admin_dashboard') }}" class="btn btn-sm btn-outline-secondary">Back to overview</a>
          <a href="{{ url_for('schedule_dashboard') }}" class="btn btn-sm btn-outline-primary">Open schedule</a>
        </div>
      </div>
      <section class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total sites</div>
          <div class="stat-value">{{ total_sites }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active sites with shifts this week</div>
          <div class="stat-value">{{ covered_sites }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Unassigned active sites</div>
          <div class="stat-value">{{ unassigned_active_sites }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Inactive clients</div>
          <div class="stat-value">{{ inactive_sites }}</div>
        </div>
      </section>
      <form method="get" class="row g-2 align-items-end mb-4">
        <div class="col-sm-8">
          <label class="form-label" for="site_search">Search sites</label>
          <div class="input-group input-group-sm">
            <input type="text" class="form-control" id="site_search" name="q" value="{{ search_q or '' }}" placeholder="Search by name or address">
              <button class="btn btn-outline-primary" type="submit" title="Search"><i class="bi bi-search"></i></button>
          </div>
        </div>
        <div class="col-sm-4">
          <a href="{{ url_for('admin_sites') }}" class="btn btn-sm btn-clear-sites w-100" title="Clear filters"><i class="bi bi-x-circle"></i></a>
        </div>
      </form>
      <div class="row g-3">
        <div class="col-12 col-lg-4">
          <div class="card-surface mb-3">
            <h2 class="h6 text-uppercase text-secondary mb-3">Add site</h2>
            <form method="post" class="row g-3">
              <input type="hidden" name="entity" value="site">
              <input type="hidden" name="action" value="create">
              <div class="col-12">
                <label class="form-label" for="new_site_name">Site name</label>
                <input type="text" class="form-control form-control-sm" id="new_site_name" name="name" required>
              </div>
              <div class="col-12">
                <label class="form-label" for="new_site_address">Address</label>
                <input type="text" class="form-control form-control-sm" id="new_site_address" name="address" placeholder="Street, city" required>
              </div>
              <div class="col-12">
                <label class="form-label" for="new_site_hourly_rate">Hourly rate ($)</label>
                <input type="number" class="form-control form-control-sm" id="new_site_hourly_rate" name="hourly_rate" step="0.01" min="0" value="50.00" required>
              </div>
              <div class="col-12">
                <label class="form-label" for="new_site_is_active">Status</label>
                <select class="form-select form-select-sm" id="new_site_is_active" name="is_active">
                  <option value="1" selected>Active</option>
                  <option value="0">Inactive</option>
                </select>
              </div>
              <div class="col-12">
                <a href="{{ url_for('admin_profiles', tab='clients') }}" class="btn btn-sm btn-outline-secondary w-100">Manage client profile fields</a>
              </div>
              <div class="col-12">
                <button type="submit" class="btn btn-sm btn-primary w-100" title="Add site"><i class="bi bi-building-add"></i></button>
              </div>
            </form>
          </div>
        </div>
        <div class="col-12 col-lg-8">
          {% if sites %}
            <div class="card-surface mb-3">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h2 class="h6 text-uppercase text-secondary mb-0">Bulk update</h2>
                <button form="bulk-site-update" type="submit" class="btn btn-sm btn-success">Save all</button>
              </div>
              <form id="bulk-site-update" method="post" class="table-responsive" style="max-height:260px;">
                <input type="hidden" name="entity" value="site_bulk">
                <input type="hidden" name="action" value="bulk_update">
                {% if search_q %}
                  <input type="hidden" name="redirect_q" value="{{ search_q }}">
                {% endif %}
                <input type="hidden" name="redirect_page" value="{{ page }}">
                <table class="table table-sm table-striped align-middle mb-0">
                  <thead>
                    <tr>
                      <th scope="col">Name</th>
                      <th scope="col">Address</th>
                      <th scope="col">Hourly rate</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for site in sites %}
                      <tr>
                        <td>
                          <input type="hidden" name="site_id" value="{{ site.id }}">
                          <input type="text" class="form-control form-control-sm" name="site_name" value="{{ site.name }}" required>
                        </td>
                        <td>
                          <input type="text" class="form-control form-control-sm" name="site_address" value="{{ site.address or '' }}" required>
                        </td>
                        <td>
                          <input type="number" class="form-control form-control-sm" name="site_hourly_rate" value="{{ '%.2f'|format(site.hourly_rate or 0) }}" step="0.01" min="0" required>
                        </td>
                        <td>
                          <select class="form-select form-select-sm" name="site_is_active">
                            <option value="1" {% if site.is_active != 0 %}selected{% endif %}>Active</option>
                            <option value="0" {% if site.is_active == 0 %}selected{% endif %}>Inactive</option>
                          </select>
                        </td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </form>
            </div>
            <div class="vstack gap-3">
              {% for site in sites %}
                <form method="post" class="little-card p-3">
                  <input type="hidden" name="entity" value="site">
                  <input type="hidden" name="id" value="{{ site.id }}">
                  {% if search_q %}
                    <input type="hidden" name="redirect_q" value="{{ search_q }}">
                  {% endif %}
                  <input type="hidden" name="redirect_page" value="{{ page }}">
                  <div class="row g-2 align-items-end">
                    <div class="col-md-4 col-12">
                      <label class="form-label">Name</label>
                      <input type="text" name="name" value="{{ site.name }}" class="form-control form-control-sm" required>
                    </div>
                    <div class="col-md-4 col-12">
                      <label class="form-label">Address</label>
                      <input type="text" name="address" value="{{ site.address or '' }}" class="form-control form-control-sm" required>
                    </div>
                    <div class="col-md-2 col-12">
                      <label class="form-label">Hourly rate ($)</label>
                      <input type="number" name="hourly_rate" value="{{ '%.2f'|format(site.hourly_rate or 0) }}" class="form-control form-control-sm" step="0.01" min="0" required>
                    </div>
                    <div class="col-md-2 col-12">
                      <label class="form-label">Status</label>
                      <select name="is_active" class="form-select form-select-sm">
                        <option value="1" {% if site.is_active != 0 %}selected{% endif %}>Active</option>
                        <option value="0" {% if site.is_active == 0 %}selected{% endif %}>Inactive</option>
                      </select>
                    </div>
                    <div class="col-md-2 col-12">
                      <div class="d-grid gap-2 site-row-actions">
                        <button type="submit" name="action" value="update" class="btn btn-sm btn-success" title="Save"><i class="bi bi-check2"></i></button>
                        <button type="submit" name="action" value="delete" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete {{ site.name }}?')" title="Delete"><i class="bi bi-trash"></i></button>
                      </div>
                    </div>
                  </div>
                  <div class="small text-secondary mt-2">Shifts scheduled: <span class="text-primary">{{ shift_counts.get(site.id, 0) }}</span></div>
                </form>
              {% endfor %}
            </div>
            {% if total_pages > 1 %}
              <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mt-4">
                <span class="text-secondary small">Page {{ page }} of {{ total_pages }}</span>
                <div class="btn-group" role="group" aria-label="Site pagination">
                  {% if has_prev %}
                    {% if search_q %}
                      <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=prev_page, q=search_q) }}">Previous</a>
                    {% else %}
                      <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=prev_page) }}">Previous</a>
                    {% endif %}
                  {% else %}
                    <span class="btn btn-sm btn-outline-secondary disabled" aria-disabled="true">Previous</span>
                  {% endif %}
                  {% for page_num in range(1, total_pages + 1) %}
                    {% if page_num == page %}
                      <span class="btn btn-sm btn-primary disabled" aria-current="page">{{ page_num }}</span>
                    {% else %}
                      {% if search_q %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=page_num, q=search_q) }}">{{ page_num }}</a>
                      {% else %}
                        <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=page_num) }}">{{ page_num }}</a>
                      {% endif %}
                    {% endif %}
                  {% endfor %}
                  {% if has_next %}
                    {% if search_q %}
                      <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=next_page, q=search_q) }}">Next</a>
                    {% else %}
                      <a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=next_page) }}">Next</a>
                    {% endif %}
                  {% else %}
                    <span class="btn btn-sm btn-outline-secondary disabled" aria-disabled="true">Next</span>
                  {% endif %}
                </div>
              </div>
            {% endif %}
          {% else %}
            <div class="card-surface">
              <p class="placeholder mb-0">No sites match this filter. Add locations or adjust your search.</p>
            </div>
          {% endif %}
        </div>
      </div>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function() {
      const body = document.body;
      const toggle = document.getElementById('mobile-nav-toggle');
      const sidebar = document.getElementById('admin-sidebar');
      const backdrop = document.getElementById('mobile-nav-backdrop');
      if (!toggle || !sidebar || !backdrop) {
        return;
      }
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        if (body.classList.contains('mobile-nav-open')) {
          closeNav();
        } else {
          openNav();
        }
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeNav));
    })();
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
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a>
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
                <td class="text-end"><strong>${{ "%.2f"|format(inv.total_amount) }}</strong></td>
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
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a>
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
                <div class="summary-value">${{ "%.2f"|format(summary.total_income) }}</div>
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
                        <td class="text-end">${{ "%.2f"|format(site_data.hourly_rate) }}/hr</td>
                        <td class="text-end"><strong>${{ "%.2f"|format(site_data.income) }}</strong></td>
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
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a>
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
                <div class="summary-value">${{ "%.2f"|format(summary.total_income) }}</div>
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
                        <td class="text-end">${{ "%.2f"|format(site_data.hourly_rate) }}/hr</td>
                        <td class="text-end"><strong>${{ "%.2f"|format(site_data.income) }}</strong></td>
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
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a>
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
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill">🪪 <span class="nav-text">Profiles</span></a>
      <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill">🗓 <span class="nav-text">Assign coverage</span></a>
      <a href="{{ url_for('leads_dashboard') }}" class="nav-pill">📇 <span class="nav-text">Lead-Center</span></a>
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
                <p class="mb-1"><strong>Hourly Rate:</strong> ${{ "%.2f"|format(invoice.hourly_rate) }}</p>
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
                    <td class="text-end">${{ "%.2f"|format(invoice.hourly_rate) }}/hr</td>
                    <td class="text-end"><strong>${{ "%.2f"|format(invoice.subtotal) }}</strong></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="row">
              <div class="col-md-6 offset-md-6">
                <table class="table table-sm mb-0">
                  <tr>
                    <td class="text-end">Subtotal:</td>
                    <td class="text-end"><strong>${{ "%.2f"|format(invoice.subtotal) }}</strong></td>
                  </tr>
                  <tr>
                    <td class="text-end">Tax ({{ (invoice.tax_rate * 100)|round(1) }}%):</td>
                    <td class="text-end"><strong>${{ "%.2f"|format(invoice.tax_amount) }}</strong></td>
                  </tr>
                  <tr class="table-dark">
                    <td class="text-end"><strong>TOTAL:</strong></td>
                    <td class="text-end"><strong>${{ "%.2f"|format(invoice.total_amount) }}</strong></td>
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

LOGIN_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
    }
    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f1f5f9;
      color: #0f172a;
      font-size: 1.05rem;
    }
    .login-card {
      width: min(440px, 95vw);
      background: #ffffff;
      border: 1px solid #e2e8f0;
      box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
      border-radius: 16px;
      padding: 2rem;
    }
    .brand {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 0.45rem;
      margin-bottom: 1rem;
    }
    .brand-logo {
      width: 44px; height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg,#0f766e,#0ea5e9);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .brand-logo img { max-width: 78%; max-height: 78%; object-fit: contain; }
    .brand-title { font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; font-size: 0.95rem; color:#0f172a; }
    .brand-sub { font-size: 0.82rem; color: #64748b; }
    .small-note { font-size:0.85rem; color:#64748b; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); transition:transform 0.15s ease, box-shadow 0.15s ease; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 18px 34px rgba(15,118,110,0.32); background-image:var(--btn-grad-accent-hover); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
  </style>
</head>
<body>
  <div class="login-card">
    <div class="brand">
      <div class="brand-logo">
        <img src="/static/logo.png" alt="Putzelf Marketing">
      </div>
      <div>
        <div class="brand-title">Putzelf Marketing</div>
        <div class="brand-sub">Secure access</div>
      </div>
    </div>
    <h1 class="h5 text-dark mb-3">Sign in</h1>
    <form method="post" class="needs-validation" novalidate>
      <input type="hidden" name="next" value="{{ next_value or request.args.get('next','') }}">
      <div class="mb-3">
        <label class="form-label small-note text-uppercase" for="username">Username or login code</label>
        <input class="form-control form-control-sm" id="username" name="username" required autofocus>
      </div>
      <div class="mb-3">
        <label class="form-label small-note text-uppercase" for="password">Password</label>
        <input type="password" class="form-control form-control-sm" id="password" name="password" required>
      </div>
      {% if error %}
        <div class="alert alert-danger py-2" role="alert">{{ error }}</div>
      {% endif %}
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <button class="btn btn-sm btn-primary">Login</button>
        <span class="small-note">Admins use their username and password. Employees use their work email or login code plus PIN.</span>
      </div>
    </form>
  </div>
  <script>
    (function () {
      'use strict';
      const forms = document.querySelectorAll('.needs-validation');
      Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
          if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
          }
          form.classList.add('was-validated');
        }, false);
      });
    })();
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


EMPLOYEE_DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>Putzelf Marketing — My Jobs</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="manifest" href="/static/manifest.json">
  <meta name="theme-color" content="#0f172a" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { margin: 0; background: #f1f5f9; font-family: 'Inter', sans-serif; color: #0f172a; min-height: 100vh; display: flex; justify-content: center; }
    a { color: #0f766e; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .app-shell { width: min(520px, 100%); min-height: 100vh; display: flex; flex-direction: column; background: #ffffff; box-shadow: 0 28px 80px rgba(15,23,42,0.12); position: relative; }
    .app-header { position: sticky; top: 0; z-index: 20; padding: calc(env(safe-area-inset-top, 0px) + 1rem) 1.35rem 1rem; background: rgba(255,255,255,0.95); backdrop-filter: blur(16px); border-bottom: 1px solid #e2e8f0; }
    .brand-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    .brand-group { display: flex; align-items: center; gap: 0.75rem; }
    .brand-mark { width: 2.75rem; height: 2.75rem; border-radius: 1rem; display: inline-flex; align-items: center; justify-content: center; background: #0f766e; font-size: 1.5rem; color: #ffffff; }
    .brand-text { display: grid; gap: 0.1rem; }
    .brand-label { font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; font-size: 0.82rem; color: #0f172a; }
    .brand-sub { font-size: 0.76rem; color: #475569; letter-spacing: 0.04em; text-transform: uppercase; }
    .logout-chip { display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.55rem 1.05rem; border-radius: 999px; background: #f1f5f9; color: #0f172a; text-decoration: none; font-size: 0.85rem; font-weight: 600; letter-spacing: 0.05em; border: 1px solid #cbd5f5; transition: transform 0.16s ease, background 0.16s ease; }
    .logout-chip:hover { transform: translateY(-1px); background: #e0f2fe; }
    .date-line { margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 0.65rem; align-items: center; }
    .welcome { font-size: 1.05rem; font-weight: 600; letter-spacing: 0.01em; color: #0f172a; }
    .date-chip { padding: 0.35rem 0.85rem; border-radius: 999px; background: #ecfdf5; border: 1px solid #a7f3d0; font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase; color: #047857; }
    .app-content { flex: 1; overflow-y: auto; padding: 1.25rem 1.35rem calc(84px + env(safe-area-inset-bottom, 14px)); display: grid; gap: 1.6rem; background: #f8fafc; }
    .section { display: grid; gap: 1rem; }
    .section-head { display: grid; gap: 0.4rem; }
    .section-eyebrow { font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; color: #64748b; }
    .section-title { font-size: 1.35rem; font-weight: 700; margin: 0; color: #0f172a; }
    .section-subtitle { margin: 0; color: #475569; font-size: 0.95rem; }
    .flash-stack { display: grid; gap: 0.6rem; }
    .flash-card { border-radius: 1rem; background: #fef9c3; color: #854d0e; padding: 0.85rem 1rem; border: 1px solid #facc15; font-weight: 600; }
    .job-list { display: grid; gap: 1.1rem; }
    .job-card { border-radius: 1.2rem; background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 12px 28px rgba(15,23,42,0.08); padding: 1.25rem; display: grid; gap: 0.95rem; }
    .job-card--complete { background: #ecfdf5; border-color: #bbf7d0; box-shadow: 0 12px 28px rgba(15,118,110,0.12); }
    .job-head { display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: space-between; align-items: baseline; }
    .job-title { font-size: 1.18rem; font-weight: 600; letter-spacing: 0.015em; color: #0f172a; }
    .status-pill { padding: 0.35rem 0.8rem; border-radius: 999px; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; border: 1px solid #cbd5f5; color: #0f172a; background: #f8fafc; }
    .status-pill[data-state="Scheduled"] { border-color: #38bdf8; background: #e0f2fe; color: #0369a1; }
    .status-pill[data-state="In progress"] { border-color: #fb923c; background: #ffedd5; color: #9a3412; }
    .status-pill[data-state="Completed"] { border-color: #4ade80; background: #dcfce7; color: #166534; }
    .job-meta { display: grid; gap: 0.5rem; font-size: 0.95rem; color: #0f172a; }
    .meta-label { font-size: 0.75rem; letter-spacing: 0.14em; text-transform: uppercase; color: #64748b; margin-bottom: 0.25rem; }
    .meta-chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
    .meta-chip { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0.75rem; border-radius: 999px; font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase; border: 1px solid #bae6fd; background: #f0f9ff; color: #0369a1; }
    .meta-chip--accent { border-color: #bbf7d0; background: #ecfdf5; color: #047857; }
    .checkpoint-row { display: flex; flex-wrap: wrap; gap: 0.75rem; font-size: 0.85rem; color: #475569; }
    .map-link { color: #0f766e; font-weight: 600; }
    .job-actions { display: grid; gap: 0.75rem; }
    @media (min-width: 420px) {
      .job-actions { grid-template-columns: repeat(2, minmax(0,1fr)); }
    }
    .job-actions form, .job-actions label { width: 100%; }
    .action-button, .upload-tile { width: 100%; border: none; border-radius: 1rem; padding: 1rem 1.1rem; font-size: 1.05rem; font-weight: 600; letter-spacing: 0.04em; display: inline-flex; justify-content: center; align-items: center; gap: 0.55rem; cursor: pointer; transition: transform 0.16s ease, box-shadow 0.16s ease, opacity 0.16s ease; text-align: center; }
    .action-button:disabled { opacity: 0.55; cursor: default; }
    .action-button:not(:disabled):hover, .upload-tile:hover { transform: translateY(-2px); box-shadow: 0 18px 32px rgba(15,23,42,0.18); }
    .btn-clock { background: linear-gradient(135deg, #38bdf8, #0ea5e9); color: #041725; }
    .btn-complete { background: linear-gradient(135deg, #22c55e, #14b8a6); color: #022c22; }
    .upload-tile { background: #f0f9ff; border: 1px dashed #bae6fd; color: #0f172a; position: relative; }
    .upload-tile[data-type="after"] { background: #ecfdf5; border-color: #bbf7d0; color: #0f172a; }
    .upload-tile input[type="file"] { display: none; }
    .photo-grid { display: flex; flex-wrap: wrap; gap: 0.9rem; }
    .photo-item { display: grid; gap: 0.4rem; }
    .photo-item img { width: 160px; max-width: 44vw; border-radius: 0.8rem; border: 2px solid #cbd5f5; object-fit: cover; }
    .timeline { display: grid; gap: 0.8rem; }
    .timeline-card { border-radius: 1rem; border: 1px solid #e2e8f0; background: #ffffff; padding: 0.95rem 1rem; display: grid; gap: 0.45rem; box-shadow: 0 10px 24px rgba(15,23,42,0.08); }
    .timeline-card h3 { font-size: 1rem; margin: 0; font-weight: 600; color: #0f172a; }
    .timeline-meta { font-size: 0.88rem; color: #475569; }
    .empty-state { border-radius: 1rem; border: 1px dashed #cbd5f5; background: #ffffff; padding: 2.2rem 1.4rem; text-align: center; color: #64748b; }
    .bottom-nav { position: sticky; bottom: 0; z-index: 30; display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.35rem; padding: 0.55rem 1rem calc(env(safe-area-inset-bottom, 12px) + 0.55rem); background: rgba(255,255,255,0.95); border-top: 1px solid #e2e8f0; backdrop-filter: blur(16px); }
    .nav-link { display: grid; gap: 0.15rem; justify-items: center; padding: 0.45rem 0.35rem; border-radius: 0.85rem; text-decoration: none; color: #475569; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; transition: background 0.16s ease, color 0.16s ease; }
    .nav-link .icon { font-size: 1.15rem; }
    .nav-link.active { background: #e0f2fe; color: #0f172a; border: 1px solid #bae6fd; }
    @media (min-width: 880px) {
      body { padding: 2rem 0; }
      .app-shell { border-radius: 1.6rem; overflow: hidden; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand-row">
        <div class="brand-group">
          <span class="brand-mark" aria-hidden="true">🧽</span>
          <div class="brand-text">
            <span class="brand-label">Crew dashboard</span>
            <span class="brand-sub">Putzelf Marketing</span>
          </div>
        </div>
        <a class="logout-chip" href="{{ url_for('logout') }}">Sign out</a>
      </div>
      <div class="date-line">
        <span class="welcome">Hi {{ employee_name }}!</span>
        <span class="date-chip">{{ today_label }}</span>
      </div>
    </header>
    <main class="app-content" id="content">
      <section id="today" class="section">
        <div class="section-head">
          <span class="section-eyebrow">Today</span>
          <h1 class="section-title">Your missions</h1>
          <p class="section-subtitle">{{ friendly_message }}</p>
        </div>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash-stack">
              {% for message in messages %}
                <div class="flash-card">{{ message }}</div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}
        {% if shifts %}
          <div class="job-list">
            {% for shift in shifts %}
              <article class="job-card {% if shift.clocked_out %}job-card--complete{% endif %}">
                <div class="job-head">
                  <div>
                    <div class="job-title">{{ shift.site_name }}</div>
                    <div class="timeline-meta">{{ shift.time_window }}</div>
                  </div>
                  <span class="status-pill" data-state="{{ shift.status_label }}">{{ shift.status_label }}</span>
                </div>
                <div class="job-meta">
                  <div>
                    <div class="meta-label">Location</div>
                    <div>{{ shift.address }}</div>
                    {% if shift.map_url %}
                      <a class="map-link" href="{{ shift.map_url }}" target="_blank" rel="noopener">Open in Maps</a>
                    {% endif %}
                  </div>
                  <div>
                    <div class="meta-label">Instructions</div>
                    <div>{{ shift.instructions }}</div>
                  </div>
                  <div>
                    <div class="meta-label">Duration</div>
                    <div class="meta-chip-row">
                      <span class="meta-chip">Scheduled · {{ shift.scheduled_duration }}</span>
                      {% if shift.has_actual_duration %}
                        <span class="meta-chip meta-chip--accent">Actual · {{ shift.actual_duration }}</span>
                      {% endif %}
                    </div>
                  </div>
                  <div>
                    <div class="meta-label">Checkpoints</div>
                    <div class="checkpoint-row">
                      <span>Clock-in: {{ shift.clock_in_display }}</span>
                      <span>Clock-out: {{ shift.clock_out_display }}</span>
                    </div>
                  </div>
                </div>
                <div class="job-actions">
                  <form class="geo-form" method="post" action="{{ shift.clock_in_url }}" data-action="clock-in" data-requires-geo="true">
                    <input type="hidden" name="lat" value="">
                    <input type="hidden" name="lng" value="">
                    <button type="submit" class="action-button btn-clock" {% if shift.clocked_in %}disabled{% endif %}>
                      {% if shift.clocked_in %}Clocked in ✔{% else %}Clock in{% endif %}
                    </button>
                  </form>
                  <form method="post" action="{{ shift.upload_url }}" enctype="multipart/form-data">
                    <input type="hidden" name="photo_type" value="before">
                    <label class="upload-tile" data-type="before">
                      <span class="icon" aria-hidden="true">📸</span>
                      <span>{% if shift.before_photo_url %}Replace before photo{% else %}Upload before photo{% endif %}</span>
                      <input type="file" name="photo" accept="image/*" onchange="this.form.submit()">
                    </label>
                  </form>
                  <form method="post" action="{{ shift.upload_url }}" enctype="multipart/form-data">
                    <input type="hidden" name="photo_type" value="after">
                    <label class="upload-tile" data-type="after">
                      <span class="icon" aria-hidden="true">✨</span>
                      <span>{% if shift.after_photo_url %}Replace after photo{% else %}Upload after photo{% endif %}</span>
                      <input type="file" name="photo" accept="image/*" onchange="this.form.submit()">
                    </label>
                  </form>
                  <form class="geo-form celebrate-form" method="post" action="{{ shift.complete_url }}" data-action="complete" data-requires-geo="true">
                    <input type="hidden" name="lat" value="">
                    <input type="hidden" name="lng" value="">
                    <button type="submit" class="action-button btn-complete" {% if shift.clocked_out %}disabled{% endif %}>
                      {% if shift.clocked_out %}Completed 🎉{% else %}Mark complete{% endif %}
                    </button>
                  </form>
                </div>
                {% if shift.before_photo_url or shift.after_photo_url %}
                  <div class="photo-grid">
                    {% if shift.before_photo_url %}
                      <div class="photo-item">
                        <div class="meta-label">Before</div>
                        <img src="{{ shift.before_photo_url }}" alt="Before photo for {{ shift.site_name }}">
                      </div>
                    {% endif %}
                    {% if shift.after_photo_url %}
                      <div class="photo-item">
                        <div class="meta-label">After</div>
                        <img src="{{ shift.after_photo_url }}" alt="After photo for {{ shift.site_name }}">
                      </div>
                    {% endif %}
                  </div>
                {% endif %}
              </article>
            {% endfor %}
          </div>
        {% else %}
          <div class="empty-state">
            <h2 class="h5 text-dark mb-2">You’re all clear ✨</h2>
            <p class="mb-0">No shifts scheduled for today. Check back later or reach out to your manager if you were expecting a mission.</p>
          </div>
        {% endif %}
      </section>

      <section id="upcoming" class="section">
        <div class="section-head">
          <span class="section-eyebrow">Next</span>
          <h2 class="section-title">Upcoming jobs</h2>
        </div>
        <div class="timeline">
          {% if upcoming_jobs %}
            {% for job in upcoming_jobs %}
              <article class="timeline-card">
                <h3>{{ job.site_name }}</h3>
                <div class="timeline-meta">{{ job.day_label }} · {{ job.time_window }}</div>
                {% if job.address %}
                  <div class="timeline-meta">{{ job.address }}</div>
                {% endif %}
                {% if job.instructions %}
                  <div class="timeline-meta">{{ job.instructions }}</div>
                {% endif %}
                <span class="status-pill" data-state="{{ job.status_label }}">{{ job.status_label }}</span>
              </article>
            {% endfor %}
          {% else %}
            <div class="empty-state">No upcoming jobs yet.</div>
          {% endif %}
        </div>
      </section>

      <section id="history" class="section">
        <div class="section-head">
          <span class="section-eyebrow">History</span>
          <h2 class="section-title">Recent missions</h2>
        </div>
        <div class="timeline">
          {% if history %}
            {% for item in history %}
              <article class="timeline-card">
                <h3>{{ item.site_name }}</h3>
                <div class="timeline-meta">{{ item.day_label }} · {{ item.time_window }}</div>
                <div class="meta-chip-row">
                  <span class="meta-chip">Scheduled · {{ item.scheduled_duration }}</span>
                  {% if item.has_actual_duration %}
                    <span class="meta-chip meta-chip--accent">Actual · {{ item.actual_duration }}</span>
                  {% endif %}
                </div>
                <span class="status-pill" data-state="{{ item.status_label }}">{{ item.status_label }}</span>
                {% if item.instructions %}
                  <div class="timeline-meta">{{ item.instructions }}</div>
                {% endif %}
              </article>
            {% endfor %}
          {% else %}
            <div class="empty-state">No missions logged yet.</div>
          {% endif %}
        </div>
      </section>
    </main>

    <nav class="bottom-nav">
      <a class="nav-link active" href="#today" data-target="today">
        <span class="icon" aria-hidden="true">🗓</span>
        <span>Today</span>
      </a>
      <a class="nav-link" href="#upcoming" data-target="upcoming">
        <span class="icon" aria-hidden="true">⏭</span>
        <span>Next</span>
      </a>
      <a class="nav-link" href="#history" data-target="history">
        <span class="icon" aria-hidden="true">📜</span>
        <span>History</span>
      </a>
    </nav>
  </div>

  <script>
    (function() {
      const navLinks = Array.from(document.querySelectorAll('.bottom-nav .nav-link'));
      const sections = navLinks.map(link => document.getElementById(link.dataset.target));
      const content = document.getElementById('content');

      const setActive = (targetId) => {
        navLinks.forEach(link => {
          link.classList.toggle('active', link.dataset.target === targetId);
        });
      };

      navLinks.forEach(link => {
        link.addEventListener('click', () => setActive(link.dataset.target));
      });

      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              setActive(entry.target.id);
            }
          });
        }, { root: content, threshold: 0.4 });
        sections.forEach(section => section && observer.observe(section));
      }
    })();
  </script>
  <script>
    (function() {
      const gatherGeo = (form) => {
        const latField = form.querySelector('input[name="lat"]');
        const lngField = form.querySelector('input[name="lng"]');
        if (!navigator.geolocation || !latField || !lngField) {
          return Promise.resolve();
        }
        return new Promise((resolve) => {
          navigator.geolocation.getCurrentPosition((position) => {
            latField.value = position.coords.latitude.toFixed(6);
            lngField.value = position.coords.longitude.toFixed(6);
            resolve();
          }, () => resolve(), { enableHighAccuracy: true, timeout: 4000, maximumAge: 0 });
        });
      };

      const celebrateAndSubmit = (form) => {
        const overlay = document.createElement('div');
        overlay.className = 'confetti-overlay';
        const message = document.createElement('div');
        message.className = 'confetti-message';
        message.textContent = 'Mission complete! 🎉';
        overlay.appendChild(message);

        const colors = ['#bef264', '#f97316', '#22d3ee', '#facc15', '#fb7185'];
        for (let i = 0; i < 28; i++) {
          const piece = document.createElement('span');
          piece.className = 'confetti-piece';
          piece.style.background = colors[i % colors.length];
          const startX = (Math.random() * 100 - 50).toFixed(1) + 'vw';
          const endX = (Math.random() * 120 - 60).toFixed(1) + 'vw';
          const rotate = (Math.random() * 720 - 360).toFixed(1) + 'deg';
          piece.style.setProperty('--x-start', startX);
          piece.style.setProperty('--x-end', endX);
          piece.style.setProperty('--rotate', rotate);
          overlay.appendChild(piece);
        }
        document.body.appendChild(overlay);
        requestAnimationFrame(() => { message.style.opacity = '1'; });
        setTimeout(() => { document.body.removeChild(overlay); }, 1400);
        setTimeout(() => { HTMLFormElement.prototype.submit.call(form); }, 750);
      };

      document.querySelectorAll('form[data-action]').forEach((form) => {
        form.addEventListener('submit', (event) => {
          const requiresGeo = form.dataset.requiresGeo === 'true';
          const action = form.dataset.action;
          if (requiresGeo || action === 'complete') {
            event.preventDefault();
            gatherGeo(form).finally(() => {
              if (action === 'complete') {
                celebrateAndSubmit(form);
              } else {
                HTMLFormElement.prototype.submit.call(form);
              }
            });
          }
        });
      });
    })();
  </script>
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/employee-sw.js').catch(() => {});
      });
    }
  </script>
  <style>
    .confetti-overlay { position: fixed; inset: 0; pointer-events: none; display: flex; align-items: center; justify-content: center; z-index: 9999; overflow: hidden; }
    .confetti-piece { position: absolute; width: 12px; height: 18px; border-radius: 4px; opacity: 0; animation: confetti-fall 1.05s ease-out forwards; }
    .confetti-message { position: relative; font-size: clamp(1.5rem, 4vw, 2.2rem); font-weight: 700; color: #f1f5f9; text-shadow: 0 8px 18px rgba(15,23,42,0.62); animation: pop-in 0.5s ease-out forwards; opacity: 0; }
    @keyframes confetti-fall { 0% { transform: translate3d(var(--x-start), -20vh, 0) rotate(0deg); opacity: 0; } 15% { opacity: 1; } 100% { transform: translate3d(var(--x-end), 110vh, 0) rotate(var(--rotate)); opacity: 0; } }
    @keyframes pop-in { 0% { opacity: 0; transform: scale(0.82); } 60% { opacity: 1; transform: scale(1.05); } 100% { opacity: 1; transform: scale(1); } }
  </style>
</body>
</html>
"""

LEADS_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Lead-Center</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-danger: linear-gradient(135deg,#f87171 0%,#ef4444 50%,#dc2626 100%);
      --btn-grad-danger-hover: linear-gradient(135deg,#ef4444 0%,#dc2626 50%,#b91c1c 100%);
      --btn-grad-light: linear-gradient(135deg,#ffffff 0%,#f1f5f9 100%);
      --btn-grad-light-hover: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
    }
    body { min-height: 100vh; background: #f1f5f9; color:#0f172a; font-size:1.05rem; }
    body.mobile-nav-open { overflow:hidden; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); transition: grid-template-columns 0.2s ease; background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; color:#0f172a; display:flex; flex-direction:column; padding:1.5rem 1.25rem; gap:1.5rem; width:260px; transition: width 0.2s ease, padding 0.2s ease; }
    .sidebar-brand { display:flex; align-items:center; gap:0.75rem; }
    .sidebar-logo { height:40px; width:40px; border-radius:12px; background:linear-gradient(135deg,#0f766e,#0ea5e9); display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .sidebar-logo img { max-width:80%; max-height:80%; object-fit:contain; }
    .sidebar-title { font-weight:600; letter-spacing:0.03em; font-size:0.95rem; text-transform:uppercase; color:#0f172a; }
    .sidebar-sub { font-size:0.78rem; color:#475569; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#64748b; margin-bottom:0.4rem; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; display:flex; align-items:center; gap:0.5rem; text-decoration:none; border:1px solid transparent; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill.active,
    .nav-pill:hover { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-pill-icon { width:24px; height:24px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center; background:#ecfdf5; color:#0f766e; font-size:0.9rem; }
    .nav-text { display:inline; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .sidebar-footer { margin-top:auto; font-size:0.75rem; color:#64748b; }
    .main-shell { padding:1.25rem 1.5rem; background:#ffffff; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1rem; box-shadow:0 12px 24px rgba(15,23,42,0.08); }
    .badge-soft { border-radius:999px; border:1px solid #cbd5f5; color:#0f172a; padding:0.15rem 0.6rem; font-size:0.75rem; background:#e0f2fe; }
    .small-note { font-size:0.82rem; color:#64748b; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.75rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; box-shadow:0 10px 20px rgba(15,23,42,0.08); transition:transform 0.15s ease, box-shadow 0.15s ease; }
    .btn-sm { font-size:0.95rem; padding:0.55rem 0.95rem; border-radius:0.7rem; min-height:2.5rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 16px 28px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-outline-danger,
    .btn-danger { background-image:var(--btn-grad-danger); color:#ffffff; box-shadow:0 12px 24px rgba(220,38,38,0.25); }
    .btn-outline-danger:hover,
    .btn-danger:hover { background-image:var(--btn-grad-danger-hover); color:#ffffff; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    .sidebar-collapsed .app-shell { grid-template-columns: 72px minmax(0, 1fr); }
    .sidebar-collapsed .sidebar { width: 72px; padding: 1.1rem 0.6rem; }
    .sidebar-collapsed .nav-text,
    .sidebar-collapsed .sidebar-title,
    .sidebar-collapsed .sidebar-sub,
    .sidebar-collapsed .sidebar-section-title,
    .sidebar-collapsed .sidebar-footer { display: none; }
    .sidebar-collapsed .nav-pill { justify-content: center; padding: 0.45rem; }
    .sidebar-collapsed .nav-pill-icon { margin: 0 auto; }
    .sidebar-collapsed .sidebar-logo { margin: 0 auto; }
    .kanban { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1rem; }
    .kanban-column { border:1px solid #e2e8f0; border-radius:0.9rem; background:#f8fafc; padding:0.75rem; min-height:240px; box-shadow:0 8px 16px rgba(15,23,42,0.08); }
    .kanban-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:0.35rem; color:#0f172a; font-weight:600; font-size:0.95rem; }
    .lead-card { border:1px solid #cbd5f5; border-radius:0.7rem; padding:0.65rem; background:#ffffff; color:#0f172a; margin-bottom:0.5rem; cursor:grab; box-shadow:0 4px 12px rgba(15,23,42,0.08); }
    .lead-card.dragging { opacity:0.6; }
    .kanban-column.drop-target { border-color:#0f766e; box-shadow:inset 0 0 0 2px rgba(15,118,110,0.35); }
    .lead-meta { font-size:0.8rem; color:#64748b; }
    .mobile-nav-toggle { display:none; }
    .mobile-nav-backdrop { display:none; }
    @media (max-width: 992px) {
      .app-shell { grid-template-columns:minmax(0, 1fr); }
      .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: min(82vw, 300px);
        max-width: 320px;
        z-index: 1050;
        display: flex;
        transform: translateX(-100%);
        transition: transform 0.2s ease;
        box-shadow: 0 24px 48px rgba(15,23,42,0.18);
      }
      body.mobile-nav-open .sidebar { transform: translateX(0); }
      .mobile-nav-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.35);
        z-index: 1040;
      }
      body.mobile-nav-open .mobile-nav-backdrop { display: block; }
      .mobile-nav-toggle {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 0.75rem;
        border: 0;
        background-image: var(--btn-grad-accent);
        color: #ffffff;
        padding: 0.45rem 0.85rem;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        box-shadow: 0 12px 24px rgba(15,118,110,0.25);
      }
      .mobile-nav-toggle:focus { outline: 2px solid rgba(15,118,110,0.4); outline-offset: 2px; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside id="admin-sidebar" class="sidebar">
      <div class="sidebar-brand">
        <div class="sidebar-logo">
          <img src="/static/logo.png" alt="Putzelf Marketing">
        </div>
        <div>
          <div class="sidebar-title">Putzelf Marketing</div>
          <div class="sidebar-sub">Lead-Center</div>
        </div>
      </div>
      <div>
        <div class="sidebar-section-title">Navigation</div>
        <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">
          <span class="nav-pill-icon">⚙</span>
          <span class="nav-text">Overview</span>
        </a>
        <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">
          <span class="nav-pill-icon">👥</span>
          <span class="nav-text">Manage employees</span>
        </a>
        <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">
          <span class="nav-pill-icon">🏢</span>
          <span class="nav-text">Manage sites</span>
        </a>
        <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">
          <span class="nav-pill-icon">🪪</span>
          <span class="nav-text">Profiles</span>
        </a>
        <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">
          <span class="nav-pill-icon">🗓</span>
          <span class="nav-text">Assign coverage</span>
        </a>
        <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">
          <span class="nav-pill-icon">📇</span>
          <span class="nav-text">Lead-Center</span>
        </a>
        <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">
          <span class="nav-pill-icon">◎</span>
          <span class="nav-text">Crawler</span>
        </a>
      </div>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="sidebar-footer">
        <div>© <span id="year"></span> Putzelf Marketing</div>
        <div class="mt-1">Track and advance leads with drag & drop.</div>
      </div>
    </aside>
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar">☰ Menu</button>
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <div>
          <div class="badge-soft mb-2">Leads</div>
          <h1 class="h4 mb-1 text-dark">Lead-Center</h1>
          <p class="small-note mb-0">Manage leads through New → Qualified → Contacted → Converted.</p>
        </div>
        <div class="d-flex gap-2 flex-wrap">
          <button id="sidebar-toggle" type="button" class="btn btn-sm btn-outline-primary">☰</button>
          <a href="{{ url_for('logout') }}" class="btn btn-sm btn-outline-secondary">Logout</a>
        </div>
      </div>
      <div class="row g-3 mb-3">
        <div class="col-12 col-lg-4">
          <div class="card-surface h-100">
            <h2 class="h6 text-uppercase text-secondary">Add lead</h2>
            <form method="post" class="small needs-validation" novalidate>
              <input type="hidden" name="action" value="create">
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="lead_name">Name</label>
                <input type="text" class="form-control form-control-sm" id="lead_name" name="name" required>
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="lead_email">Email</label>
                <input type="email" class="form-control form-control-sm" id="lead_email" name="email">
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="lead_phone">Phone</label>
                <input type="text" class="form-control form-control-sm" id="lead_phone" name="phone">
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="lead_source">Source</label>
                <input type="text" class="form-control form-control-sm" id="lead_source" name="source" placeholder="e.g. Web form, Import">
              </div>
              <div class="mb-2">
                <label class="form-label small-note text-uppercase" for="lead_notes">Notes</label>
                <textarea class="form-control form-control-sm" id="lead_notes" name="notes" rows="2"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label small-note text-uppercase" for="lead_stage">Stage</label>
                <select class="form-select form-select-sm" id="lead_stage" name="stage">
                  {% for s in stages %}
                    <option value="{{ s }}">{{ s }}</option>
                  {% endfor %}
                </select>
              </div>
              <button type="submit" class="btn btn-sm btn-primary">Save lead</button>
            </form>
          </div>
        </div>
        <div class="col-12 col-lg-8">
          <div class="card-surface h-100">
            <div class="d-flex flex-wrap gap-2 align-items-end mb-2">
              <div>
                <label class="form-label small-note text-uppercase mb-1" for="filter_stage">Stage</label>
                <select class="form-select form-select-sm" id="filter_stage" name="stage" form="filters-form">
                  <option value="">All stages</option>
                  {% for s in stages %}
                    <option value="{{ s }}" {% if stage_filter==s %}selected{% endif %}>{{ s }}</option>
                  {% endfor %}
                </select>
              </div>
              <div>
                <label class="form-label small-note text-uppercase mb-1" for="filter_start">From</label>
                <input type="date" class="form-control form-control-sm" id="filter_start" name="start" form="filters-form" value="{{ start_filter or '' }}">
              </div>
              <div>
                <label class="form-label small-note text-uppercase mb-1" for="filter_end">To</label>
                <input type="date" class="form-control form-control-sm" id="filter_end" name="end" form="filters-form" value="{{ end_filter or '' }}">
              </div>
              <div>
                <label class="form-label small-note text-uppercase mb-1" for="filter_sort">Sort</label>
                <select class="form-select form-select-sm" id="filter_sort" name="sort" form="filters-form">
                  <option value="desc" {% if sort=='desc' %}selected{% endif %}>Newest first</option>
                  <option value="asc" {% if sort=='asc' %}selected{% endif %}>Oldest first</option>
                </select>
              </div>
              <div class="ms-auto d-flex gap-2">
                <form id="filters-form" method="get" class="d-flex gap-2">
                  <button class="btn btn-sm btn-outline-primary" type="submit">Apply</button>
                  <a href="{{ url_for('leads_dashboard') }}" class="btn btn-sm btn-outline-secondary">Clear</a>
                </form>
              </div>
            </div>
            <div class="kanban">
              {% for stage, stage_leads in grouped_leads.items() %}
                <div class="kanban-column" data-stage="{{ stage }}">
                  <div class="kanban-header">
                    <span>{{ stage }}</span>
                    <span class="badge bg-secondary">{{ stage_leads|length }}</span>
                  </div>
                  <div class="kanban-body" data-stage="{{ stage }}">
                    {% for lead in stage_leads %}
                      <div class="lead-card" draggable="true" data-lead-id="{{ lead.id }}" data-lead-name="{{ lead.name|e }}" data-lead-email="{{ (lead.email or '')|e }}" data-lead-phone="{{ (lead.phone or '')|e }}" data-lead-source="{{ (lead.source or '')|e }}" data-lead-notes="{{ (lead.notes or '')|e }}" data-lead-stage="{{ lead.stage|e }}">
                        <div class="d-flex justify-content-between align-items-start gap-2">
                          <div>
                            <strong>{{ lead.name }}</strong><br>
                            <span class="lead-meta">{{ (lead.email or '—') }}</span>
                          </div>
                          <div class="text-end">
                            <span class="small-note d-block">{{ lead.created_at.strftime('%d.%m.%Y') }}</span>
                            <div class="btn-group btn-group-sm mt-1" role="group" aria-label="Lead actions">
                              <button type="button" class="btn btn-outline-primary btn-sm py-0 lead-edit" data-bs-toggle="modal" data-bs-target="#leadModal" title="Edit lead">
                                ✎
                              </button>
                              <button type="button" class="btn btn-outline-danger btn-sm py-0 lead-delete" data-lead-id="{{ lead.id }}" title="Delete lead">
                                ✕
                              </button>
                            </div>
                          </div>
                        </div>
                        {% if lead.phone %}
                          <div class="lead-meta mt-1">📞 {{ lead.phone }}</div>
                        {% endif %}
                        {% if lead.source %}
                          <div class="lead-meta">Source: {{ lead.source }}</div>
                        {% endif %}
                        {% if lead.notes %}
                          <div class="lead-meta">Notes: {{ lead.notes }}</div>
                        {% endif %}
                      </div>
                    {% else %}
                      <div class="small-note text-secondary">No leads</div>
                    {% endfor %}
                  </div>
                </div>
              {% endfor %}
            </div>
          </div>
        </div>
      </div>
      <form id="lead-delete-form" method="post" action="{{ url_for('leads_dashboard') }}" class="d-none">
        <input type="hidden" name="action" value="delete">
        <input type="hidden" name="id" id="lead-delete-id">
      </form>
      <div class="modal fade" id="leadModal" tabindex="-1" aria-labelledby="leadModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content border border-light-subtle">
            <form id="lead-edit-form" method="post" action="{{ url_for('leads_dashboard') }}" class="needs-validation" novalidate>
              <input type="hidden" name="action" value="update">
              <input type="hidden" name="id" id="lead-edit-id">
              <div class="modal-header border-0 pb-0">
                <h5 class="modal-title" id="leadModalLabel">Edit lead</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body pb-0">
                <div class="mb-2">
                  <label for="lead-edit-name" class="form-label small-note text-uppercase">Name</label>
                  <input type="text" class="form-control form-control-sm" id="lead-edit-name" name="name" required>
                </div>
                <div class="mb-2">
                  <label for="lead-edit-email" class="form-label small-note text-uppercase">Email</label>
                  <input type="email" class="form-control form-control-sm" id="lead-edit-email" name="email">
                </div>
                <div class="mb-2">
                  <label for="lead-edit-phone" class="form-label small-note text-uppercase">Phone</label>
                  <input type="text" class="form-control form-control-sm" id="lead-edit-phone" name="phone">
                </div>
                <div class="mb-2">
                  <label for="lead-edit-source" class="form-label small-note text-uppercase">Source</label>
                  <input type="text" class="form-control form-control-sm" id="lead-edit-source" name="source">
                </div>
                <div class="mb-2">
                  <label for="lead-edit-notes" class="form-label small-note text-uppercase">Notes</label>
                  <textarea class="form-control form-control-sm" id="lead-edit-notes" name="notes" rows="3"></textarea>
                </div>
                <div class="mb-2">
                  <label for="lead-edit-stage" class="form-label small-note text-uppercase">Stage</label>
                  <select class="form-select form-select-sm" id="lead-edit-stage" name="stage">
                    {% for s in stages %}
                      <option value="{{ s }}">{{ s }}</option>
                    {% endfor %}
                  </select>
                </div>
              </div>
              <div class="modal-footer border-0 d-flex justify-content-between">
                <button type="button" class="btn btn-sm btn-outline-secondary" data-bs-dismiss="modal" title="Cancel"><i class="bi bi-x-circle"></i></button>
                <button type="submit" class="btn btn-sm btn-primary">Save changes</button>
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
    (function() {
      const body = document.body;
      const toggle = document.getElementById('mobile-nav-toggle');
      const sidebar = document.getElementById('admin-sidebar');
      const backdrop = document.getElementById('mobile-nav-backdrop');
      if (!toggle || !sidebar || !backdrop) {
        return;
      }
      const closeNav = () => {
        body.classList.remove('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      };
      const openNav = () => {
        body.classList.add('mobile-nav-open');
        toggle.setAttribute('aria-expanded', 'true');
      };
      toggle.addEventListener('click', () => {
        if (body.classList.contains('mobile-nav-open')) {
          closeNav();
        } else {
          openNav();
        }
      });
      backdrop.addEventListener('click', closeNav);
      sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeNav));
    })();
    (function () {
      const KEY = 'pm-sidebar-collapsed';
      const body = document.body;
      const btn = document.getElementById('sidebar-toggle');
      const setState = (val) => {
        body.classList.toggle('sidebar-collapsed', val);
        try { localStorage.setItem(KEY, val ? '1' : '0'); } catch (e) {}
      };
      const initial = (() => {
        try { return localStorage.getItem(KEY) === '1'; } catch (e) { return false; }
      })();
      setState(initial);
      if (btn) btn.addEventListener('click', () => setState(!body.classList.contains('sidebar-collapsed')));
    })();

    // Drag & drop
    (() => {
      const cards = document.querySelectorAll('.lead-card');
      const columns = document.querySelectorAll('.kanban-body');
      let dragged = null;
      cards.forEach(card => {
        card.addEventListener('dragstart', e => {
          dragged = card;
          card.classList.add('dragging');
          e.dataTransfer.effectAllowed = 'move';
          try { e.dataTransfer.setData('text/plain', card.dataset.leadId || '0'); } catch (err) {}
        });
        card.addEventListener('dragend', () => {
          card.classList.remove('dragging');
          dragged = null;
          columns.forEach(c => c.classList.remove('drop-target'));
        });
      });
      columns.forEach(col => {
        const highlight = () => col.classList.add('drop-target');
        const removeHighlight = () => col.classList.remove('drop-target');
        col.addEventListener('dragenter', e => {
          if (!dragged) return;
          e.preventDefault();
          highlight();
        });
        col.addEventListener('dragover', e => {
          if (!dragged) return;
          e.preventDefault();
          e.dataTransfer.dropEffect = 'move';
          highlight();
          const siblings = [...col.querySelectorAll('.lead-card:not(.dragging)')];
          const afterEl = siblings.find(el => {
            const box = el.getBoundingClientRect();
            return e.clientY < box.top + box.height / 2;
          });
          if (afterEl) {
            col.insertBefore(dragged, afterEl);
          } else {
            col.appendChild(dragged);
          }
        });
        col.addEventListener('dragleave', () => {
          if (!dragged) removeHighlight();
        });
        col.addEventListener('drop', async e => {
          e.preventDefault();
          removeHighlight();
          if (!dragged) return;
          const stage = col.dataset.stage;
          const id = dragged.dataset.leadId;
          dragged.dataset.leadStage = stage;
          try {
            await fetch('{{ url_for("leads_stage") }}', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ id, stage })
            });
          } catch (err) {
            console.error('Failed to update stage', err);
          }
        });
      });
    })();

    // Lead modals and actions
    (() => {
      const editForm = document.getElementById('lead-edit-form');
      const deleteForm = document.getElementById('lead-delete-form');
      if (!editForm || !deleteForm) return;
      const editModalEl = document.getElementById('leadModal');
      const stageSelect = document.getElementById('lead-edit-stage');
      const nameInput = document.getElementById('lead-edit-name');
      const emailInput = document.getElementById('lead-edit-email');
      const phoneInput = document.getElementById('lead-edit-phone');
      const sourceInput = document.getElementById('lead-edit-source');
      const notesInput = document.getElementById('lead-edit-notes');
      const idInput = document.getElementById('lead-edit-id');
      document.querySelectorAll('.lead-edit').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const card = btn.closest('.lead-card');
          if (!card) return;
          idInput.value = card.dataset.leadId || '';
          nameInput.value = card.dataset.leadName || '';
          emailInput.value = card.dataset.leadEmail || '';
          phoneInput.value = card.dataset.leadPhone || '';
          sourceInput.value = card.dataset.leadSource || '';
          notesInput.value = card.dataset.leadNotes || '';
          const currentStage = card.dataset.leadStage || '';
          if (stageSelect) {
            [...stageSelect.options].forEach(opt => {
              opt.selected = opt.value === currentStage;
            });
          }
        });
      });
      document.querySelectorAll('.lead-delete').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const id = btn.dataset.leadId;
          if (!id) return;
          if (!confirm('Delete this lead?')) return;
          const hiddenId = document.getElementById('lead-delete-id');
          hiddenId.value = id;
          deleteForm.submit();
        });
      });
      editForm.addEventListener('submit', function (event) {
        if (!editForm.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        editForm.classList.add('was-validated');
      });
      if (editModalEl) {
        editModalEl.addEventListener('shown.bs.modal', () => {
          nameInput && nameInput.focus();
        });
      }
    })();
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

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — URL Contact Crawler</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-info: linear-gradient(135deg,#38bdf8 0%,#0ea5e9 50%,#2563eb 100%);
      --btn-grad-info-hover: linear-gradient(135deg,#0ea5e9 0%,#2563eb 50%,#1d4ed8 100%);
      --btn-grad-light: linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
      --btn-grad-light-hover: linear-gradient(135deg,#f1f5f9 0%,#e2e8f0 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; min-height:100vh; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:#ffffff; transition:grid-template-columns 0.2s ease; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; color:#0f172a; display:flex; flex-direction:column; padding:1.5rem 1.25rem; gap:1.5rem; width:260px; transition:width 0.2s ease, padding 0.2s ease; }
    .sidebar-brand { display:flex; align-items:center; gap:0.75rem; }
    .sidebar-logo { height:40px; width:40px; border-radius:12px; background:radial-gradient(circle at 10% 0, #22c55e 0%, #0ea5e9 45%, #1d4ed8 100%); display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .sidebar-logo img { max-width:80%; max-height:80%; object-fit:contain; }
    .sidebar-title { font-weight:600; letter-spacing:0.03em; font-size:0.95rem; text-transform:uppercase; color:#0f172a; }
    .sidebar-sub { font-size:0.78rem; color:#475569; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; margin-bottom:0.4rem; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; display:flex; align-items:center; gap:0.5rem; text-decoration:none; border:1px solid transparent; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill:hover, .nav-pill.active { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-pill-icon { width:24px; height:24px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center; background:#ecfdf5; color:#0f766e; font-size:0.9rem; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .sidebar-footer { margin-top:auto; font-size:0.75rem; color:#475569; }
    .main-shell { background:#ffffff; padding:1.6rem 1.75rem; display:flex; flex-direction:column; gap:1rem; }
    .topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
    .topbar-title { color:#64748b; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; font-size:0.78rem; }
    .topbar-heading { color:#0f172a; margin:0.05rem 0 0.2rem; font-size:1.4rem; font-weight:600; }
    .topbar-subtitle { color:#475569; font-size:0.9rem; max-width:480px; }
    .topbar-chip { font-size:0.72rem; padding:0.2rem 0.55rem; border-radius:999px; border:1px solid rgba(15,118,110,0.35); color:#0f766e; background:#ecfdf5; text-transform:uppercase; letter-spacing:0.08em; }
    .topbar-user { display:flex; align-items:center; gap:0.75rem; color:#0f172a; }
    .user-avatar { width:32px; height:32px; border-radius:999px; background:radial-gradient(circle at 10% 0, #0ea5e9 0%, #6366f1 60%, #4f46e5 100%); display:inline-flex; align-items:center; justify-content:center; font-size:0.9rem; font-weight:600; color:#ffffff; }
    .user-meta { font-size:0.8rem; text-align:right; }
    .user-meta span { display:block; }
    .user-meta span:first-child { color:#0f172a; font-weight:600; }
    .user-meta span:nth-child(2) { color:#0f766e; }
    .user-meta span:last-child { color:#64748b; }
    .content-shell { margin-top:0.25rem; border-radius:1rem; background:#ffffff; border:1px solid #e2e8f0; box-shadow:0 24px 48px rgba(15,23,42,0.08); padding:1.25rem 1.35rem 1.4rem; display:flex; flex-direction:column; gap:1.1rem; }
    .card-surface { border-radius:0.9rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.15rem; color:#0f172a; box-shadow:0 12px 24px rgba(15,23,42,0.06); }
    .card-header-line { display:flex; align-items:center; justify-content:space-between; gap:0.75rem; margin-bottom:0.9rem; }
    .card-title { font-size:0.95rem; font-weight:600; color:#0f172a; }
    .card-subtitle { font-size:0.82rem; color:#64748b; margin-bottom:0; }
    .badge-soft { border-radius:999px; border:1px solid #cbd5f5; color:#4c51bf; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .btn { font-size:1rem; padding:0.65rem 1.1rem; border-radius:0.75rem; min-height:2.7rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; box-shadow:0 10px 20px rgba(15,23,42,0.08); transition:transform 0.15s ease, box-shadow 0.15s ease; }
    .btn-sm { font-size:0.92rem; padding:0.5rem 0.9rem; border-radius:0.7rem; min-height:2.4rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 16px 28px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-link { background:none; box-shadow:none; color:#0f766e; }
    .btn-link:hover { color:#0c615b; }
    .small-note { font-size:0.82rem; color:#64748b; }
    .divider-label { text-transform:uppercase; font-size:0.72rem; letter-spacing:0.08em; color:#94a3b8; }
    .chat-bubble { border-radius:0.75rem; background:#f8fafc; padding:0.65rem 0.8rem; font-size:0.86rem; border:1px dashed #cbd5f5; color:#475569; }
    .assistant-badge { font-size:0.78rem; padding:0.15rem 0.6rem; border-radius:999px; background:#eef2ff; color:#4c51bf; border:1px solid #cbd5f5; }
    .chat-output { white-space:pre-wrap; font-size:0.86rem; color:#0f172a; background:#f8fafc; border:1px solid #e2e8f0; border-radius:0.75rem; }
    .sidebar-collapsed .app-shell { grid-template-columns:72px minmax(0,1fr); }
    .sidebar-collapsed .sidebar { width:72px; padding:1.1rem 0.6rem; }
    .sidebar-collapsed .nav-text,
    .sidebar-collapsed .sidebar-title,
    .sidebar-collapsed .sidebar-sub,
    .sidebar-collapsed .sidebar-section-title,
    .sidebar-collapsed .sidebar-footer { display:none; }
    .sidebar-collapsed .nav-pill { justify-content:center; padding:0.45rem; }
    .sidebar-collapsed .nav-pill-icon { margin:0 auto; }
    .sidebar-collapsed .sidebar-logo { margin:0 auto; }
    @media (max-width: 992px) {
      .app-shell { grid-template-columns:minmax(0,1fr); }
      .sidebar { display:none; }
      .main-shell { padding:1.25rem; }
      .content-shell { padding:1rem; }
    }
    @media (max-width: 640px) {
      .topbar { flex-direction:column; align-items:flex-start; }
      .topbar-user { align-self:stretch; justify-content:space-between; }
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
        <div class="sidebar-section-title">Navigation</div>
        <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">
          <span class="nav-pill-icon">⚙</span>
          <span class="nav-text">Overview</span>
        </a>
        <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">
          <span class="nav-pill-icon">👥</span>
          <span class="nav-text">Manage employees</span>
        </a>
        <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">
          <span class="nav-pill-icon">🏢</span>
          <span class="nav-text">Manage sites</span>
        </a>
        <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">
          <span class="nav-pill-icon">🪪</span>
          <span class="nav-text">Profiles</span>
        </a>
        <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">
          <span class="nav-pill-icon">🗓</span>
          <span class="nav-text">Assign coverage</span>
        </a>
        <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">
          <span class="nav-pill-icon">📇</span>
          <span class="nav-text">Lead-Center</span>
        </a>
        <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">
          <span class="nav-pill-icon">◎</span>
          <span class="nav-text">Crawler</span>
        </a>
      </div>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
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
          <button id="sidebar-toggle" type="button" class="btn btn-sm btn-outline-secondary">☰</button>
          <div class="text-end user-meta">
            <span>Prospecting workspace</span>
            <span>{{ 'GPT connected' if gpt_enabled else 'GPT not configured' }}</span>
            <span><a href="{{ url_for('logout') }}" class="link-secondary small-note text-decoration-none">Logout</a></span>
          </div>
          <div class="user-avatar">PM</div>
        </div>
      </header>
      <main class="content-shell">
        <section class="row g-3 mt-1">
          <div class="col-12 col-lg-6">
            <div class="card-surface h-100">
              <div class="card-header-line">
                <div>
                  <div class="card-title">1. Crawl new contacts</div>
                  <div class="card-subtitle">
                    Start from any page on a domain and collect emails and phone numbers into a polished PDF report.
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
                <div class="mb-3">
                  <label for="max_pages" class="form-label small-note text-uppercase">Max pages</label>
                  <input type="number" class="form-control form-control-sm" id="max_pages" name="max_pages" min="1" max="200" value="100" required>
                </div>
                <div class="d-flex align-items-center gap-2 flex-wrap">
                  <button id="submit-btn" type="submit" class="btn btn-sm btn-primary">
                    <span id="btn-spinner" class="spinner-border spinner-border-sm me-2 d-none" role="status" aria-hidden="true"></span>
                    Crawl &amp; download PDF
                  </button>
                  <button id="reset-btn" type="button" class="btn btn-sm btn-outline-secondary" onclick="document.getElementById('crawl-form').reset()">
                    Reset
                  </button>
                  <div id="status" class="ms-1 small-note" aria-live="polite"></div>
                </div>
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
                <div id="gpt-output" class="chat-output border rounded-3 p-2 flex-grow-1" style="min-height:120px; max-height:260px; overflow:auto;"></div>
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
      const KEY = 'pm-sidebar-collapsed';
      const body = document.body;
      const btn = document.getElementById('sidebar-toggle');
      const setState = (val) => {
        body.classList.toggle('sidebar-collapsed', val);
        try { localStorage.setItem(KEY, val ? '1' : '0'); } catch (e) {}
      };
      const initial = (() => {
        try { return localStorage.getItem(KEY) === '1'; } catch (e) { return false; }
      })();
      setState(initial);
      if (btn) {
        btn.addEventListener('click', () => setState(!body.classList.contains('sidebar-collapsed')));
      }
    })();
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
          let filename = 'contacts.pdf';
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
  <link href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --btn-grad-accent: linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%);
      --btn-grad-accent-hover: linear-gradient(135deg,#0ea5e9 0%,#14b8a6 50%,#22d3ee 100%);
      --btn-grad-neutral: linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);
      --btn-grad-neutral-hover: linear-gradient(135deg,#e2e8f0 0%,#cbd5f5 100%);
      --btn-grad-success: linear-gradient(135deg,#22c55e 0%,#16a34a 50%,#15803d 100%);
      --btn-grad-success-hover: linear-gradient(135deg,#16a34a 0%,#15803d 50%,#166534 100%);
      --btn-grad-danger: linear-gradient(135deg,#f87171 0%,#ef4444 50%,#dc2626 100%);
      --btn-grad-danger-hover: linear-gradient(135deg,#ef4444 0%,#dc2626 50%,#b91c1c 100%);
    }
    body { background:#f1f5f9; color:#0f172a; font-size:1.05rem; min-height:100vh; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); transition:grid-template-columns 0.2s ease; background:#ffffff; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; color:#0f172a; display:flex; flex-direction:column; padding:1.5rem 1.25rem; gap:1.5rem; width:260px; transition:width 0.2s ease, padding 0.2s ease; }
    .sidebar-brand { display:flex; align-items:center; gap:0.75rem; }
    .sidebar-logo { height:40px; width:40px; border-radius:12px; background:radial-gradient(circle at 10% 0, #22c55e 0%, #0ea5e9 45%, #1d4ed8 100%); display:flex; align-items:center; justify-content:center; overflow:hidden; }
    .sidebar-logo img { max-width:80%; max-height:80%; object-fit:contain; }
    .sidebar-title { font-weight:600; letter-spacing:0.03em; font-size:0.95rem; text-transform:uppercase; color:#0f172a; }
    .sidebar-sub { font-size:0.78rem; color:#475569; }
    .sidebar-section-title { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.12em; color:#475569; margin-bottom:0.4rem; }
    .nav-text { display:inline; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; display:flex; align-items:center; gap:0.5rem; text-decoration:none; border:1px solid transparent; transition:background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease; }
    .nav-pill:hover, .nav-pill.active { background-image:var(--btn-grad-accent); border-color:transparent; color:#ffffff; box-shadow:0 12px 24px rgba(15,118,110,0.25); }
    .nav-pill-icon { width:24px; height:24px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center; background:#ecfdf5; color:#0f766e; font-size:0.9rem; }
    .nav-pill-logout { margin-top:0.3rem; background-image:var(--btn-grad-neutral); border-color:transparent; color:#0f172a; box-shadow:0 8px 18px rgba(15,23,42,0.08); }
    .nav-pill-logout:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .sidebar-footer { margin-top:auto; font-size:0.75rem; color:#475569; }
    .main-shell { background:#ffffff; padding:1.6rem 1.75rem; display:flex; flex-direction:column; gap:1.5rem; }
    .page-header { display:flex; align-items:flex-start; justify-content:space-between; gap:1.5rem; margin-bottom:0.5rem; }
    .page-header-actions { display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap; }
    .btn { font-size:1rem; padding:0.65rem 1.15rem; border-radius:0.75rem; min-height:2.7rem; border:0; background-image:var(--btn-grad-neutral); color:#0f172a; box-shadow:0 10px 20px rgba(15,23,42,0.08); transition:transform 0.15s ease, box-shadow 0.15s ease; }
    .btn-sm { font-size:0.92rem; padding:0.5rem 0.9rem; border-radius:0.7rem; min-height:2.4rem; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 16px 28px rgba(15,23,42,0.12); }
    .btn:focus-visible { outline:none; box-shadow:0 0 0 3px rgba(14,165,233,0.25); }
    .btn-icon { width:34px; height:34px; display:inline-flex; align-items:center; justify-content:center; padding:0; border-radius:0.65rem; }
    .btn-primary,
    .btn-outline-primary { background-image:var(--btn-grad-accent); color:#ffffff; box-shadow:0 14px 26px rgba(15,118,110,0.25); }
    .btn-primary:hover,
    .btn-outline-primary:hover { background-image:var(--btn-grad-accent-hover); color:#ffffff; }
    .btn-outline-secondary { background-image:var(--btn-grad-neutral); color:#0f172a; }
    .btn-outline-secondary:hover { background-image:var(--btn-grad-neutral-hover); color:#0f172a; }
    .btn-success { background-image:var(--btn-grad-success); color:#ffffff; box-shadow:0 12px 24px rgba(34,197,94,0.25); }
    .btn-success:hover { background-image:var(--btn-grad-success-hover); color:#ffffff; }
    .btn-danger { background-image:var(--btn-grad-danger); color:#ffffff; box-shadow:0 12px 24px rgba(220,38,38,0.25); }
    .btn-danger:hover { background-image:var(--btn-grad-danger-hover); color:#ffffff; }
    .page-header a.btn-outline-secondary { color:#0f172a; }
    .content-shell { margin-top:0.25rem; border-radius:1.15rem; background:#ffffff; border:1px solid #e2e8f0; box-shadow:0 24px 48px rgba(15,23,42,0.08); padding:1.35rem 1.35rem 1.6rem; color:#0f172a; display:flex; flex-direction:column; gap:1.5rem; }
    .section-card { background:#ffffff; border:1px solid #e2e8f0; border-radius:1rem; padding:1.5rem; box-shadow:0 16px 32px rgba(15,23,42,0.08); }
    .section-header { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1.25rem; }
    .section-kicker { font-size:0.68rem; letter-spacing:0.14em; text-transform:uppercase; color:#0f766e; margin-bottom:0.4rem; }
    .section-title { font-size:1.35rem; font-weight:600; color:#0f172a; margin-bottom:0.35rem; }
    .section-subtitle { font-size:0.9rem; color:#475569; max-width:560px; margin-bottom:0; }
    .section-actions { display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap; }
    .insight-badges { display:flex; flex-wrap:wrap; gap:0.5rem; margin-bottom:1.1rem; }
    .insight-badge { display:inline-flex; align-items:center; gap:0.4rem; padding:0.35rem 0.65rem; border-radius:999px; border:1px solid #cbd5f5; background:#ecfdf5; color:#0f766e; font-size:0.72rem; letter-spacing:0.04em; text-transform:uppercase; }
    .filter-toolbar { display:grid; gap:0.75rem; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); background:#f8fafc; border:1px solid #e2e8f0; border-radius:0.85rem; padding:1rem; margin-bottom:1.25rem; }
    .filter-toolbar .form-label { font-size:0.7rem; letter-spacing:0.1em; text-transform:uppercase; color:#64748b; margin-bottom:0.35rem; }
    .filter-toolbar .form-select,
    .filter-toolbar input[type="date"] { background:#ffffff; border:1px solid #cbd5f5; color:#0f172a; font-size:0.82rem; border-radius:0.6rem; }
    .filter-toolbar .form-select:focus,
    .filter-toolbar input[type="date"]:focus { box-shadow:0 0 0 3px rgba(15,118,110,0.15); border-color:#0f766e; }
    .table-wrapper { background:#ffffff; border:1px solid #e2e8f0; border-radius:0.85rem; overflow:hidden; }
    .table-scroll { max-height:460px; overflow:auto; }
    .schedule-table { margin-bottom:0; color:#0f172a; }
    .schedule-table th,
    .schedule-table td { font-size:0.82rem; vertical-align:top; border-color:#e2e8f0; }
    .schedule-table th { background:#f1f5f9; color:#475569; position:sticky; top:0; z-index:5; }
    .schedule-table th:first-child { position:sticky; left:0; z-index:10; background:#f1f5f9; }
    .schedule-table td:first-child { position:sticky; left:0; z-index:3; background:inherit; }
    .schedule-table tbody tr:nth-child(odd) { background:#ffffff; }
    .schedule-table tbody tr:nth-child(even) { background:#f8fafc; }
    .shift-pill { display:inline-flex; align-items:center; gap:0.3rem; padding:0.18rem 0.6rem; border-radius:999px; background:#ecfdf5; border:1px solid #16a34a26; color:#0f766e; font-size:0.74rem; margin-bottom:0.25rem; white-space:nowrap; }
    .shift-delete { display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#ef4444; color:#ffffff; font-size:0.85rem; line-height:1; text-decoration:none; opacity:0.7; transition:opacity 0.15s ease; }
    .shift-delete:hover { opacity:1; color:#ffffff; }
    .free-pill { display:inline-flex; align-items:center; padding:0.18rem 0.6rem; border-radius:999px; border:1px dashed #cbd5f5; color:#94a3b8; font-size:0.74rem; }
    .form-card .section-subtitle { max-width:600px; }
    .form-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:1rem; margin-bottom:1.1rem; }
    .form-grid .form-field { display:flex; flex-direction:column; gap:0.35rem; }
    .form-field-span { grid-column:1 / -1; }
    .form-grid .form-select,
    .form-grid input[type="text"],
    .form-grid input[type="time"],
    .form-grid input[type="number"],
    .form-grid textarea { background:#ffffff; border:1px solid #cbd5f5; color:#0f172a; border-radius:0.6rem; }
    #day-picker { background:#ffffff; border:1px solid #cbd5f5; color:#0f172a; border-radius:0.6rem; }
    #day-picker:focus,
    .form-grid .form-select:focus,
    .form-grid input:focus,
    .form-grid textarea:focus { border-color:#0f766e; box-shadow:0 0 0 3px rgba(15,118,110,0.15); }
    .selected-days { display:flex; flex-wrap:wrap; gap:0.35rem; }
    .day-chip { display:inline-flex; align-items:center; padding:0.18rem 0.6rem; border-radius:999px; background:#ecfdf5; border:1px solid #cbd5f5; color:#0f766e; font-size:0.72rem; letter-spacing:0.04em; text-transform:uppercase; }
    .form-actions { display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap; }
    .tip-callout { margin-top:1.25rem; border-radius:0.85rem; background:#f1f5f9; border:1px dashed #cbd5f5; padding:0.9rem 1rem; color:#475569; font-size:0.85rem; }
    .tag-muted { display:inline-flex; align-items:center; gap:0.3rem; font-size:0.75rem; color:#94a3b8; }
    .small-note { font-size:0.82rem; color:#64748b; }
    .sidebar-collapsed .app-shell { grid-template-columns:72px minmax(0,1fr); }
    .sidebar-collapsed .sidebar { width:72px; padding:1.1rem 0.6rem; }
    .sidebar-collapsed .nav-text,
    .sidebar-collapsed .sidebar-title,
    .sidebar-collapsed .sidebar-sub,
    .sidebar-collapsed .sidebar-section-title,
    .sidebar-collapsed .sidebar-footer { display:none; }
    .sidebar-collapsed .nav-pill { justify-content:center; padding:0.45rem; }
    .sidebar-collapsed .nav-pill-icon { margin:0 auto; }
    .sidebar-collapsed .sidebar-logo { margin:0 auto; }
    @media (max-width: 992px) {
      .app-shell { grid-template-columns:minmax(0,1fr); }
      .sidebar { display:none; }
      .main-shell { padding:1.25rem; }
      .content-shell { padding:1rem; }
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
        <div class="sidebar-section-title">Navigation</div>
        <a href="{{ url_for('admin_dashboard') }}" class="nav-pill {% if active_page == 'dashboard' %}active{% endif %}">
          <span class="nav-pill-icon">⚙</span>
          <span class="nav-text">Overview</span>
        </a>
        <a href="{{ url_for('admin_employees') }}" class="nav-pill {% if active_page == 'employees' %}active{% endif %}">
          <span class="nav-pill-icon">👥</span>
          <span class="nav-text">Manage employees</span>
        </a>
        <a href="{{ url_for('admin_sites') }}" class="nav-pill {% if active_page == 'sites' %}active{% endif %}">
          <span class="nav-pill-icon">🏢</span>
          <span class="nav-text">Manage sites</span>
        </a>
        <a href="{{ url_for('admin_profiles') }}" class="nav-pill {% if active_page == 'profiles' %}active{% endif %}">
          <span class="nav-pill-icon">🪪</span>
          <span class="nav-text">Profiles</span>
        </a>
        <a href="{{ url_for('schedule_dashboard') }}" class="nav-pill {% if active_page == 'schedule' %}active{% endif %}">
          <span class="nav-pill-icon">🗓</span>
          <span class="nav-text">Assign coverage</span>
        </a>
        <a href="{{ url_for('leads_dashboard') }}" class="nav-pill {% if active_page == 'leads' %}active{% endif %}">
          <span class="nav-pill-icon">📇</span>
          <span class="nav-text">Lead-Center</span>
        </a>
        <a href="{{ url_for('index') }}" class="nav-pill {% if active_page == 'crawler' %}active{% endif %}">
          <span class="nav-pill-icon">◎</span>
          <span class="nav-text">Crawler</span>
        </a>
      </div>
      <div class="sidebar-section-title">Account</div>
      <a href="{{ url_for('logout') }}" class="nav-pill nav-pill-logout">⇦ <span class="nav-text">Log out</span></a>
      <div class="sidebar-footer">
        <div>© <span id="year"></span> Putzelf Marketing</div>
        <div class="mt-1">Simple schedule overview for field teams.</div>
      </div>
    </aside>
    <div class="main-shell">
      <header class="page-header">
        <div>
          <div class="topbar-title">People</div>
          <h1 class="topbar-heading mb-0">Employee schedule</h1>
          <p class="topbar-subtitle mb-0">
            See who is on which site this week, when they are free, and assign new shifts.
          </p>
          <p class="small-note mb-0">
            Showing {{ week_days[0].strftime('%d.%m.%Y') }} – {{ week_days[-1].strftime('%d.%m.%Y') }} ({{ weeks }} week{% if weeks > 1 %}s{% endif %})
          </p>
        </div>
        <div class="page-header-actions">
          <button id="sidebar-toggle" type="button" class="btn btn-sm btn-outline-secondary btn-icon" title="Toggle navigation">☰</button>
          <a href="{{ url_for('admin_dashboard') }}" class="btn btn-sm btn-outline-secondary">Admin panel</a>
          <a href="{{ url_for('logout') }}" class="btn btn-sm btn-outline-secondary">Logout</a>
        </div>
      </header>
      <main class="content-shell">
        <section class="section-card schedule-card">
          <div class="section-header">
            <div>
              <div class="section-kicker">Team planner</div>
              <h2 class="section-title">Schedule overview</h2>
              <p class="section-subtitle">
                Manage weekly coverage and spot availability across every employee at a glance.
              </p>
            </div>
            <div class="section-actions">
              {% if reportlab_available %}
                <a href="{{ pdf_url }}" class="btn btn-sm btn-primary">Schedule PDF</a>
                <a href="{{ hours_pdf_url }}" class="btn btn-sm btn-outline-secondary">Hours report</a>
              {% else %}
                <span class="tag-muted">Install reportlab to export PDF</span>
              {% endif %}
            </div>
          </div>
          <div class="insight-badges">
            <span class="insight-badge">Week {{ week_days[0].strftime('%d.%m') }} – {{ week_days[-1].strftime('%d.%m') }}</span>
            <span class="insight-badge">Range {{ weeks }} week{% if weeks > 1 %}s{% endif %}</span>
            {% if selected_employee %}
              <span class="insight-badge">Focused: {{ selected_employee.name }}</span>
            {% else %}
              <span class="insight-badge">All employees</span>
            {% endif %}
            {% if selected_site %}
              <span class="insight-badge">Site: {{ selected_site.name }}</span>
            {% endif %}
          </div>
          <form method="get" action="{{ url_for('schedule_dashboard') }}" class="filter-toolbar">
            <div>
              <label class="form-label" for="filter_employee_id">Focus on employee</label>
              <select class="form-select form-select-sm" id="filter_employee_id" name="employee_id" onchange="this.form.submit()">
                <option value="">All employees</option>
                {% for emp in employees %}
                  <option value="{{ emp.id }}" {% if selected_employee_id == emp.id %}selected{% endif %}>{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
                {% endfor %}
              </select>
            </div>
            <div>
              <label class="form-label" for="filter_site_id">Focus on site</label>
              <select class="form-select form-select-sm" id="filter_site_id" name="site_id" onchange="this.form.submit()">
                <option value="">All sites</option>
                {% for site in sites %}
                  <option value="{{ site.id }}" {% if selected_site_id == site.id %}selected{% endif %}>{{ site.name }}</option>
                {% endfor %}
              </select>
            </div>
            <div>
              <label class="form-label" for="start_date">Start week (Monday)</label>
              <input type="date" class="form-control form-control-sm" id="start_date" name="start_date" value="{{ start_date or week_days[0].isoformat() }}" onchange="this.form.submit()">
            </div>
            <div>
              <label class="form-label" for="weeks">Range (weeks)</label>
              <select class="form-select form-select-sm" id="weeks" name="weeks" onchange="this.form.submit()">
                {% for n in [1,2,4,8,12] %}
                  <option value="{{ n }}" {% if weeks == n %}selected{% endif %}>{{ n }} week{% if n>1 %}s{% endif %}</option>
                {% endfor %}
              </select>
            </div>
          </form>
          <div class="table-wrapper">
            <div class="table-scroll">
              <table class="table table-bordered table-sm align-middle schedule-table">
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
                            {% for shift in cell %}
                              <div class="shift-pill">
                                {{ shift.label }}
                                <a href="{{ url_for('delete_shift', shift_id=shift.id) }}" class="shift-delete" onclick="return confirm('Delete this shift?')" title="Delete shift">×</a>
                              </div>
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
        </section>

        <section class="section-card form-card">
          <div class="section-header">
            <div>
              <div class="section-kicker">Create shift</div>
              <h2 class="section-title">Assign a new shift</h2>
              <p class="section-subtitle">
                Choose an employee, match them to a site, then add the time window and days in one go.
              </p>
            </div>
          </div>
          <form method="post" class="small">
            <div class="form-grid">
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="employee_id">Employee</label>
                <select class="form-select form-select-sm" id="employee_id" name="employee_id" required>
                  <option value="">Select employee…</option>
                  {% for emp in employees %}
                    <option value="{{ emp.id }}">{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="site_id">Site</label>
                <select class="form-select form-select-sm" id="site_id" name="site_id" required>
                  <option value="">Select site…</option>
                  {% for site in sites %}
                    <option value="{{ site.id }}">{{ site.name }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="form-field form-field-span">
                <label class="form-label small-note text-uppercase" for="day-picker">Day(s)</label>
                <input type="text" class="form-control form-control-sm" id="day-picker" name="day_display" placeholder="Pick one or more days" required autocomplete="off">
                <div id="selected-days" class="selected-days mt-2"></div>
                <div id="day-hidden-inputs" hidden></div>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="start_time">Start time</label>
                <input type="time" class="form-control form-control-sm" id="start_time" name="start_time" required>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="duration_hours">Duration (hours)</label>
                <input type="number" step="0.25" min="0.25" max="24" class="form-control form-control-sm" id="duration_hours" name="duration_hours" placeholder="e.g. 8" required>
              </div>
              <div class="form-field form-field-span">
                <label class="form-label small-note text-uppercase" for="instructions">Special instructions</label>
                <textarea class="form-control form-control-sm" id="instructions" name="instructions" rows="3" placeholder="Optional notes for this shift"></textarea>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary btn-sm">Save shift</button>
              <span class="small-note">Calendar picks are duplicated for every day you select.</span>
            </div>
          </form>
          <div class="tip-callout mt-3">
            Tip: An empty cell in the grid means the employee is free for that entire day.
          </div>
        </section>
      </main>
    </div>
  </div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function () {
      const KEY = 'pm-sidebar-collapsed';
      const body = document.body;
      const btn = document.getElementById('sidebar-toggle');
      const setState = (val) => {
        body.classList.toggle('sidebar-collapsed', val);
        try { localStorage.setItem(KEY, val ? '1' : '0'); } catch (e) {}
      };
      const initial = (() => {
        try { return localStorage.getItem(KEY) === '1'; } catch (e) { return false; }
      })();
      setState(initial);
      if (btn) {
        btn.addEventListener('click', () => setState(!body.classList.contains('sidebar-collapsed')));
      }
    })();
    window.addEventListener('DOMContentLoaded', () => {
      if (typeof flatpickr === 'undefined') {
        return;
      }
      const dayPicker = document.getElementById('day-picker');
      if (!dayPicker) {
        return;
      }
      const selectedContainer = document.getElementById('selected-days');
      const hiddenContainer = document.getElementById('day-hidden-inputs');
      const renderSelections = (dates, instance) => {
        if (selectedContainer) {
          selectedContainer.innerHTML = '';
        }
        if (hiddenContainer) {
          hiddenContainer.innerHTML = '';
        }
        const format = (dateObj) => instance.formatDate(dateObj, 'Y-m-d');
        dates.forEach((dateObj) => {
          const iso = format(dateObj);
          if (selectedContainer) {
            const badge = document.createElement('span');
            badge.className = 'day-chip';
            badge.textContent = iso;
            selectedContainer.appendChild(badge);
          }
          if (hiddenContainer) {
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'day';
            hidden.value = iso;
            hiddenContainer.appendChild(hidden);
          }
        });
        dayPicker.required = dates.length === 0;
        if (dates.length === 0) {
          dayPicker.setCustomValidity('Select at least one day.');
        } else {
          dayPicker.setCustomValidity('');
        }
      };
      const picker = flatpickr(dayPicker, {
        mode: 'multiple',
        dateFormat: 'Y-m-d',
        disableMobile: true,
        locale: {
          firstDayOfWeek: 1
        },
        onChange(selectedDates, _dateStr, instance) {
          renderSelections(selectedDates, instance);
        },
      });
      renderSelections(picker.selectedDates, picker);
      const form = dayPicker.form;
      if (form) {
        form.addEventListener('reset', () => {
          picker.clear();
          renderSelections([], picker);
        });
        form.addEventListener('submit', () => {
          renderSelections(picker.selectedDates, picker);
        });
      }
    });
  </script>
  <script src="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


# --- Application configuration -------------------------------------------------

logging.basicConfig(level=logging.INFO)

APP_ROOT = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")
app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
app.config.setdefault("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)

UPLOAD_FOLDER = os.path.join(APP_ROOT, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic", "heif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
  DATABASE_URL = "sqlite:///" + os.path.join(APP_ROOT, "schedule.db")

_engine_kwargs: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
  _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, future=True, **_engine_kwargs)
SessionLocal = scoped_session(
  sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)
Base = declarative_base()


# --- Optional integrations -----------------------------------------------------

try:
  from reportlab.lib import colors
  from reportlab.lib.pagesizes import A4, landscape
  from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
  from reportlab.lib.units import inch
  from reportlab.pdfgen import canvas
  from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
  )
  REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - degrade gracefully when missing
  colors = None
  A4 = None
  landscape = None
  ParagraphStyle = None
  getSampleStyleSheet = None
  inch = None
  canvas = None
  Image = None
  Paragraph = None
  SimpleDocTemplate = None
  Spacer = None
  Table = None
  TableStyle = None
  REPORTLAB_AVAILABLE = False

try:
  from pypdf import PdfReader, PdfWriter
  PYPDF_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
  try:
    _pypdf2 = __import__("PyPDF2", fromlist=["PdfReader", "PdfWriter"])
    PdfReader = getattr(_pypdf2, "PdfReader", None)
    PdfWriter = getattr(_pypdf2, "PdfWriter", None)
    PYPDF_AVAILABLE = True
  except Exception:
    PdfReader = None
    PdfWriter = None
    PYPDF_AVAILABLE = False

try:
  from pypdf.generic import BooleanObject, NameObject
except Exception:  # pragma: no cover - optional dependency / version differences
  try:
    _pypdf2_generic = __import__("PyPDF2.generic", fromlist=["BooleanObject", "NameObject"])
    BooleanObject = getattr(_pypdf2_generic, "BooleanObject", None)
    NameObject = getattr(_pypdf2_generic, "NameObject", None)
  except Exception:
    BooleanObject = None
    NameObject = None

try:
  from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
  OpenAI = None
  openai_client = None
else:
  _openai_key = os.getenv("OPENAI_API_KEY")
  openai_client = OpenAI(api_key=_openai_key) if _openai_key else None

try:
  import phonenumbers
  from phonenumbers import PhoneNumberFormat
except Exception:  # pragma: no cover - dependency optional
  phonenumbers = None
  PhoneNumberFormat = None
  PHONENUMBERS_AVAILABLE = False
else:
  PHONENUMBERS_AVAILABLE = True


# --- Business constants --------------------------------------------------------

DEFAULT_PHONE_REGION = os.getenv("CRAWLER_DEFAULT_REGION", "US").upper()

LEAD_STAGES = ["New Leads", "Qualified", "Contacted", "Converted"]

EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_TOKEN_REGEX = re.compile(r"\+?\d[\d\s().\/\-]{6,20}")
PHONE_LABEL_REGEX = re.compile(
  r"(?:tel|telefon|phone|mobil|handy|kontakt|contact|rufnummer|call)[:\s-]*([+0][\d\s().\/-]{5,})",
  re.IGNORECASE,
)


def _looks_like_date_sequence(candidate: str, digits: str) -> bool:
  if len(digits) not in (6, 8):
    return False
  compact_candidate = re.sub(r"\D", "", candidate)
  if compact_candidate != digits:
    return False
  if len(digits) == 8:
    for fmt in ("%Y%m%d", "%d%m%Y", "%m%d%Y"):
      try:
        parsed = datetime.strptime(digits, fmt)
      except ValueError:
        continue
      if 1900 <= parsed.year <= 2100:
        return True
  elif len(digits) == 6:
    for fmt in ("%y%m%d", "%d%m%y", "%m%d%y"):
      try:
        parsed = datetime.strptime(digits, fmt)
      except ValueError:
        continue
      if 1930 <= parsed.year <= 2100:
        return True
  return False


REGION_FROM_TLD = {
  "US": "US",
  "COM": "US",
  "NET": "US",
  "ORG": "US",
  "CA": "CA",
  "AU": "AU",
  "NZ": "NZ",
  "UK": "GB",
  "GB": "GB",
  "IE": "IE",
  "DE": "DE",
  "AT": "AT",
  "CH": "CH",
  "FR": "FR",
  "ES": "ES",
  "IT": "IT",
  "NL": "NL",
  "BE": "BE",
  "SE": "SE",
  "NO": "NO",
  "DK": "DK",
  "FI": "FI",
  "PL": "PL",
  "CZ": "CZ",
  "SK": "SK",
  "HU": "HU",
  "PT": "PT",
  "GR": "GR",
  "RO": "RO",
  "BG": "BG",
  "HR": "HR",
  "SI": "SI",
  "LV": "LV",
  "LT": "LT",
  "EE": "EE",
  "MX": "MX",
  "BR": "BR",
  "AR": "AR",
  "CL": "CL",
  "CO": "CO",
  "PE": "PE",
  "ZA": "ZA",
  "IN": "IN",
  "SG": "SG",
  "MY": "MY",
  "PH": "PH",
  "TH": "TH",
  "JP": "JP",
  "KR": "KR",
  "CN": "CN",
  "HK": "HK",
  "TW": "TW",
}


def _infer_region_from_netloc(netloc: str) -> str | None:
  if not netloc:
    return None
  parts = netloc.lower().split(".")
  if not parts:
    return None
  tld = parts[-1].upper()
  return REGION_FROM_TLD.get(tld)


def _parse_phone_candidate(raw: str | None, region: str | None = None) -> str | None:
  if not raw:
    return None
  candidate = raw.strip().replace("\u00a0", " ")
  if not candidate:
    return None
  if PHONENUMBERS_AVAILABLE:
    region_code = None if candidate.startswith("+") else (region or DEFAULT_PHONE_REGION)
    try:
      parsed = phonenumbers.parse(candidate, region_code)
    except phonenumbers.NumberParseException:
      return None
    if phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed):
      return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    return None

  digits = re.sub(r"\D", "", candidate)
  if not digits or len(digits) < 7 or len(digits) > 15:
    return None
  if _looks_like_date_sequence(candidate, digits):
    return None
  if len(set(digits)) == 1:
    return None
  if digits in {"0123456789", "1234567890", "9876543210", "0987654321"}:
    return None

  if candidate.startswith("+"):
    return "+" + digits
  if candidate.startswith("00") and len(digits) > 2:
    trimmed = digits.lstrip("0")
    return "+" + trimmed if trimmed else None
  return digits


def normalize_phone(raw: str | None, region: str | None = None) -> str:
  normalized = _parse_phone_candidate(raw, region=region)
  return normalized or ""


def is_valid_phone(number: str | None, region: str | None = None) -> bool:
  return bool(_parse_phone_candidate(number, region=region))


def find_labelled_phones(text: str | None, region: str | None = None) -> list[str]:
  if not text:
    return []
  seen: set[str] = set()
  results: list[str] = []
  for match in PHONE_LABEL_REGEX.finditer(text):
    normalized = normalize_phone(match.group(1), region=region)
    if normalized and normalized not in seen:
      seen.add(normalized)
      results.append(normalized)
  if not results:
    for match in PHONE_TOKEN_REGEX.finditer(text):
      normalized = normalize_phone(match.group(0), region=region)
      if normalized and normalized not in seen:
        seen.add(normalized)
        results.append(normalized)
  return results


ADMIN_PROFILES_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Profiles</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root {
      --accent: #0f766e;
      --bg-soft: #f1f5f9;
      --panel: #ffffff;
      --line: #dbe5f2;
      --muted: #64748b;
    }
    body { background:linear-gradient(180deg,#f8fbff 0%, #eef6ff 100%); color:#0f172a; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:260px minmax(0,1fr); background:transparent; }
    .sidebar { background:#eef2ff; border-right:1px solid #cbd5f5; padding:1.5rem 1.25rem; display:flex; flex-direction:column; gap:1.25rem; }
    .nav-pill { border-radius:0.75rem; padding:0.45rem 0.75rem; font-size:0.9rem; color:#0f172a; text-decoration:none; border:1px solid transparent; display:flex; align-items:center; gap:0.5rem; }
    .nav-pill.active, .nav-pill:hover { background:var(--accent); color:#fff; }
    .main-shell { padding:1.5rem; }
    .badge-soft { border-radius:999px; border:1px solid #d6d3f0; color:#6366f1; padding:0.2rem 0.65rem; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; background:#eef2ff; }
    .tab-btn { text-decoration:none; display:inline-flex; align-items:center; gap:.4rem; padding:0.5rem 0.85rem; border-radius:0.7rem; border:1px solid #cbd5f5; color:#1e293b; background:#fff; }
    .tab-btn.active { background:#0f766e; color:#fff; border-color:#0f766e; }
    .card-surface { border-radius:1rem; border:1px solid var(--line); background:var(--panel); padding:1rem; box-shadow:0 12px 24px rgba(15,23,42,0.06); }
    .registration-card {
      border:1px solid #e2e8f0;
      border-radius:1rem;
      background:#f8fbff;
      padding:0.95rem;
    }
    .registration-grid { display:grid; grid-template-columns:120px minmax(0,1fr); gap:0.9rem; align-items:start; }
    .avatar-wrap { display:flex; justify-content:center; }
    .avatar-uploader {
      position:relative;
      width:88px;
      height:88px;
      border-radius:999px;
      cursor:pointer;
      border:2px solid #cbd5f5;
      background:#e2e8f0;
      overflow:hidden;
      display:flex;
      align-items:center;
      justify-content:center;
      color:#334155;
      font-weight:700;
      font-size:1.2rem;
    }
    .avatar-uploader img {
      width:100%;
      height:100%;
      object-fit:cover;
      display:none;
    }
    .avatar-badge {
      position:absolute;
      right:-2px;
      bottom:-2px;
      width:28px;
      height:28px;
      border-radius:999px;
      background:#0f766e;
      color:#fff;
      display:flex;
      align-items:center;
      justify-content:center;
      border:2px solid #fff;
      font-size:.82rem;
    }
    .form-label { text-transform:uppercase; font-size:0.71rem; letter-spacing:0.08em; color:#475569; margin-bottom:.3rem; }
    .form-control, .form-select {
      background:#ffffff;
      color:#0f172a;
      border:1.5px solid #94a3b8;
    }
    .form-control::placeholder { color:#64748b; opacity:1; }
    .form-control:focus, .form-select:focus {
      border-color:#0f766e;
      box-shadow:0 0 0 3px rgba(15,118,110,0.15);
      background:#ffffff;
      color:#0f172a;
    }
    .muted { color:var(--muted); }
    .icon-btn {
      min-width:2.4rem;
      height:2.4rem;
      border-radius:.65rem;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      padding:0;
    }
    .btn { border:1px solid rgba(15,23,42,0.18); }
    @media(max-width:992px){
      .app-shell{ grid-template-columns:minmax(0,1fr);} .sidebar{display:none;}
      .registration-grid{ grid-template-columns:minmax(0,1fr); }
      .avatar-wrap{ justify-content:flex-start; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <a href="{{ url_for('admin_dashboard') }}" class="nav-pill">⚙ Overview</a>
      <a href="{{ url_for('admin_employees') }}" class="nav-pill">👥 Manage employees</a>
      <a href="{{ url_for('admin_sites') }}" class="nav-pill">🏢 Manage sites</a>
      <a href="{{ url_for('admin_profiles') }}" class="nav-pill active">🪪 Profiles</a>
      <a href="{{ url_for('admin_invoices') }}" class="nav-pill">📄 Invoices</a>
      <a href="{{ url_for('logout') }}" class="nav-pill">⇦ Log out</a>
    </aside>
    <main class="main-shell">
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
        <div class="badge-soft mb-2">Profiles</div>
        <h1 class="h4 text-dark mb-1">Profile Center</h1>
      </header>

      <div class="d-flex gap-2 mb-3">
        <a class="tab-btn {% if active_tab == 'employees' %}active{% endif %}" href="{{ url_for('admin_profiles', tab='employees') }}"><i class="bi bi-person-vcard"></i> Employee profiles</a>
        <a class="tab-btn {% if active_tab == 'clients' %}active{% endif %}" href="{{ url_for('admin_profiles', tab='clients') }}"><i class="bi bi-building"></i> Client profiles</a>
      </div>

      {% if active_tab == 'employees' %}
        <div class="card-surface">
          <h2 class="h6 text-uppercase text-secondary mb-3">Employee registration</h2>
          {% if employees %}
            <div class="vstack gap-3">
              {% for emp in employees %}
                <form method="post" enctype="multipart/form-data" class="registration-card">
                  <input type="hidden" name="entity" value="employee_profile">
                  <input type="hidden" name="id" value="{{ emp.id }}">
                  <input type="hidden" name="tab" value="employees">
                  <div class="registration-grid">
                    <div class="avatar-wrap">
                      <label class="avatar-uploader" title="Upload photo">
                        <img class="avatar-preview" alt="Profile image preview" {% if emp.profile_image_path %}src="/static/{{ emp.profile_image_path }}" style="display:block;"{% endif %}>
                        <span class="avatar-initials" {% if emp.profile_image_path %}style="display:none;"{% endif %}>{{ (emp.name or 'U')[:1]|upper }}</span>
                        <span class="avatar-badge"><i class="bi bi-camera-fill"></i></span>
                        <input type="file" name="employee_profile_image" class="d-none avatar-input" accept="image/*">
                      </label>
                    </div>
                    <div>
                      <div class="mb-2"><strong>{{ emp.name }}</strong> <span class="muted">· {{ emp.role or 'No role' }}</span></div>
                      <div class="row g-2">
                        <div class="col-md-4 col-12">
                          <label class="form-label">Phone</label>
                          <input type="text" class="form-control form-control-sm" name="profile_phone" value="{{ emp.profile_phone or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Emergency contact name</label>
                          <input type="text" class="form-control form-control-sm" name="profile_emergency_name" value="{{ emp.profile_emergency_name or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Emergency contact phone</label>
                          <input type="text" class="form-control form-control-sm" name="profile_emergency_phone" value="{{ emp.profile_emergency_phone or '' }}">
                        </div>
                        <div class="col-md-6 col-12">
                          <label class="form-label">Address</label>
                          <input type="text" class="form-control form-control-sm" name="profile_address" value="{{ emp.profile_address or '' }}">
                        </div>
                        <div class="col-md-6 col-12">
                          <label class="form-label">Notes</label>
                          <input type="text" class="form-control form-control-sm" name="profile_notes" value="{{ emp.profile_notes or '' }}">
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="mt-2 d-flex justify-content-end">
                    <button class="btn btn-sm btn-primary icon-btn" type="submit" title="Save profile"><i class="bi bi-check2-circle"></i></button>
                  </div>
                </form>
              {% endfor %}
            </div>
          {% else %}
            <p class="muted mb-0">No employees found.</p>
          {% endif %}
        </div>
      {% else %}
        <div class="card-surface">
          <h2 class="h6 text-uppercase text-secondary mb-3">Client registration</h2>
          {% if sites %}
            <div class="vstack gap-3">
              {% for site in sites %}
                <form method="post" enctype="multipart/form-data" class="registration-card">
                  <input type="hidden" name="entity" value="site_profile">
                  <input type="hidden" name="id" value="{{ site.id }}">
                  <input type="hidden" name="tab" value="clients">
                  <div class="registration-grid">
                    <div class="avatar-wrap">
                      <label class="avatar-uploader" title="Upload logo">
                        <img class="avatar-preview" alt="Logo preview" {% if site.profile_image_path %}src="/static/{{ site.profile_image_path }}" style="display:block;"{% endif %}>
                        <span class="avatar-initials" {% if site.profile_image_path %}style="display:none;"{% endif %}>{{ (site.name or 'C')[:1]|upper }}</span>
                        <span class="avatar-badge"><i class="bi bi-camera-fill"></i></span>
                        <input type="file" name="site_profile_image" class="d-none avatar-input" accept="image/*">
                      </label>
                    </div>
                    <div>
                      <div class="mb-2"><strong>{{ site.name }}</strong> <span class="muted">· {{ site.address or 'No address' }}</span></div>
                      <div class="row g-2">
                        <div class="col-md-4 col-12">
                          <label class="form-label">Firma</label>
                          <input type="text" class="form-control form-control-sm" name="profile_company_name" value="{{ site.profile_company_name or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Billing contact name</label>
                          <input type="text" class="form-control form-control-sm" name="profile_contact_name" value="{{ site.profile_contact_name or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Billing contact email</label>
                          <input type="email" class="form-control form-control-sm" name="profile_contact_email" value="{{ site.profile_contact_email or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Billing phone</label>
                          <input type="text" class="form-control form-control-sm" name="profile_phone" value="{{ site.profile_phone or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Customer ID</label>
                          <input type="text" class="form-control form-control-sm" name="profile_tax_id" value="{{ site.profile_tax_id or '' }}" readonly>
                        </div>
                        <div class="col-md-6 col-12">
                          <label class="form-label">Notes</label>
                          <input type="text" class="form-control form-control-sm" name="profile_notes" value="{{ site.profile_notes or '' }}">
                        </div>
                        <div class="col-md-4 col-12">
                          <label class="form-label">Name des partners</label>
                          <input type="text" class="form-control form-control-sm" name="contract_partner_name" value="{{ site.contract_partner_name or '' }}">
                        </div>
                        <div class="col-md-8 col-12">
                          <label class="form-label">Tel./ Fax / E-Mail</label>
                          <input type="text" class="form-control form-control-sm" name="contract_contact_details" value="{{ site.contract_contact_details or '' }}">
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="mt-2 d-flex justify-content-end gap-2">
                    <button class="btn btn-sm btn-outline-primary icon-btn" type="submit" name="profile_action" value="generate_contract" title="Generate contract PDF"><i class="bi bi-file-earmark-pdf"></i></button>
                    <button class="btn btn-sm btn-primary icon-btn" type="submit" name="profile_action" value="save" title="Save profile"><i class="bi bi-check2-circle"></i></button>
                  </div>
                </form>
              {% endfor %}
            </div>
          {% else %}
            <p class="muted mb-0">No sites found.</p>
          {% endif %}
        </div>
      {% endif %}
    </main>
  </div>
  <script>
    document.querySelectorAll('.avatar-input').forEach((input) => {
      input.addEventListener('change', (event) => {
        const file = event.target.files && event.target.files[0];
        const wrap = event.target.closest('.avatar-uploader');
        if (!file || !wrap) return;
        const img = wrap.querySelector('.avatar-preview');
        const initials = wrap.querySelector('.avatar-initials');
        if (!img) return;
        const reader = new FileReader();
        reader.onload = (e) => {
          img.src = e.target && e.target.result ? e.target.result : '';
          img.style.display = 'block';
          if (initials) initials.style.display = 'none';
        };
        reader.readAsDataURL(file);
      });
    });
  </script>
</body>
</html>
"""


# --- ORM models ----------------------------------------------------------------


class Employee(Base):
  __tablename__ = "employees"

  id = Column(Integer, primary_key=True)
  name = Column(String(255), nullable=False)
  role = Column(String(255))
  login_email = Column(String(255), unique=True)
  login_code = Column(String(64), unique=True)
  login_pin_hash = Column(String(255))
  profile_phone = Column(String(64))
  profile_emergency_name = Column(String(255))
  profile_emergency_phone = Column(String(64))
  profile_address = Column(String(255))
  profile_notes = Column(Text)
  profile_image_path = Column(String(255))

  shifts = relationship("Shift", back_populates="employee", cascade="all, delete-orphan")


class Site(Base):
  __tablename__ = "sites"

  id = Column(Integer, primary_key=True)
  name = Column(String(255), nullable=False)
  address = Column(String(255))
  hourly_rate = Column(Float, nullable=False, default=50.0)
  contact_name = Column(String(255))
  contact_email = Column(String(255))
  is_active = Column(Boolean, nullable=False, default=True)
  profile_company_name = Column(String(255))
  profile_contact_name = Column(String(255))
  profile_contact_email = Column(String(255))
  profile_phone = Column(String(64))
  profile_billing_address = Column(String(255))
  profile_tax_id = Column(String(128))
  profile_default_hourly_rate = Column(Float)
  profile_notes = Column(Text)
  profile_image_path = Column(String(255))
  contract_partner_name = Column(String(255))
  contract_contact_details = Column(String(255))

  shifts = relationship("Shift", back_populates="site", cascade="all, delete-orphan")


class Shift(Base):
  __tablename__ = "shifts"

  id = Column(Integer, primary_key=True)
  employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
  site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
  day = Column(Date, nullable=False)
  start_time = Column(Time, nullable=False)
  end_time = Column(Time, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  instructions = Column(Text)
  clock_in_at = Column(DateTime)
  clock_in_lat = Column(Float)
  clock_in_lng = Column(Float)
  clock_out_at = Column(DateTime)
  clock_out_lat = Column(Float)
  clock_out_lng = Column(Float)
  before_photo_path = Column(String(255))
  after_photo_path = Column(String(255))

  employee = relationship("Employee", back_populates="shifts")
  site = relationship("Site", back_populates="shifts")


class Lead(Base):
  __tablename__ = "leads"

  id = Column(Integer, primary_key=True)
  name = Column(String(255), nullable=False)
  email = Column(String(255))
  phone = Column(String(64))
  source = Column(String(255))
  notes = Column(Text)
  stage = Column(String(64), nullable=False, default="New Leads")
  created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
  __tablename__ = "invoices"

  id = Column(Integer, primary_key=True)
  invoice_number = Column(String(64), unique=True, nullable=False)
  site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
  site_company_name = Column(String(255))
  site_contact_name = Column(String(255))
  site_contact_email = Column(String(255))
  site_phone = Column(String(64))
  site_billing_address = Column(String(255))
  site_tax_id = Column(String(128))
  hourly_rate = Column(Float, nullable=False, default=50.0)
  tax_rate = Column(Float, nullable=False, default=0.0)  # e.g., 0.19 for 19% VAT
  total_hours = Column(Float, nullable=False)
  subtotal = Column(Float)
  tax_amount = Column(Float)
  total_amount = Column(Float)
  issued_date = Column(DateTime, default=datetime.utcnow)
  due_date = Column(DateTime)
  billing_month = Column(String(7))  # YYYY-MM
  status = Column(String(64), default="draft")  # draft, sent, paid, overdue
  paid_at = Column(DateTime)
  notes = Column(Text)
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  site = relationship("Site", backref="invoices")


Base.metadata.create_all(bind=engine)


def _ensure_sqlite_column(engine, table: str, column: str, ddl: str):
  if not DATABASE_URL.startswith("sqlite"):
    return
  with engine.begin() as conn:
    result = conn.execute(text(f"PRAGMA table_info('{table}')"))
    existing = {row[1] for row in result}
    if column not in existing:
      conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


_ensure_sqlite_column(engine, "shifts", "created_at", "DATETIME")
_ensure_sqlite_column(engine, "employees", "login_email", "TEXT")
_ensure_sqlite_column(engine, "employees", "login_code", "TEXT")
_ensure_sqlite_column(engine, "employees", "login_pin_hash", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_phone", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_emergency_name", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_emergency_phone", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_address", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_notes", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_image_path", "TEXT")
_ensure_sqlite_column(engine, "shifts", "instructions", "TEXT")
_ensure_sqlite_column(engine, "shifts", "clock_in_at", "DATETIME")
_ensure_sqlite_column(engine, "shifts", "clock_in_lat", "FLOAT")
_ensure_sqlite_column(engine, "shifts", "clock_in_lng", "FLOAT")
_ensure_sqlite_column(engine, "shifts", "clock_out_at", "DATETIME")
_ensure_sqlite_column(engine, "shifts", "clock_out_lat", "FLOAT")
_ensure_sqlite_column(engine, "shifts", "clock_out_lng", "FLOAT")
_ensure_sqlite_column(engine, "shifts", "before_photo_path", "TEXT")
_ensure_sqlite_column(engine, "shifts", "after_photo_path", "TEXT")
_ensure_sqlite_column(engine, "sites", "hourly_rate", "FLOAT")
_ensure_sqlite_column(engine, "sites", "contact_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "contact_email", "TEXT")
_ensure_sqlite_column(engine, "sites", "is_active", "INTEGER NOT NULL DEFAULT 1")
_ensure_sqlite_column(engine, "sites", "profile_company_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_contact_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_contact_email", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_phone", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_billing_address", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_tax_id", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_default_hourly_rate", "FLOAT")
_ensure_sqlite_column(engine, "sites", "profile_notes", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_image_path", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_partner_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_contact_details", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_company_name", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_phone", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_billing_address", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_tax_id", "TEXT")
_ensure_sqlite_column(engine, "invoices", "paid_at", "DATETIME")
_ensure_sqlite_column(engine, "invoices", "billing_month", "TEXT")


def _allowed_image(filename: str | None) -> bool:
  if not filename or "." not in filename:
    return False
  ext = filename.rsplit(".", 1)[1].lower()
  return ext in ALLOWED_IMAGE_EXTENSIONS


def _coerce_float(value: str | None) -> float | None:
  try:
    if value is None:
      return None
    return float(value)
  except (TypeError, ValueError):
    return None


def _remove_photo(path: str | None) -> None:
  if not path:
    return
  try:
    absolute = path if os.path.isabs(path) else os.path.join(APP_ROOT, "static", path)
    if os.path.isfile(absolute):
      os.remove(absolute)
  except OSError:
    logging.debug("Failed to remove photo %s", path)


def _save_profile_image(file_obj, prefix: str, replace_path: str | None = None) -> str | None:
  if not file_obj or not getattr(file_obj, "filename", None):
    return None
  if not _allowed_image(file_obj.filename):
    return None

  ext = os.path.splitext(file_obj.filename)[1].lower()
  if not ext:
    return None

  safe_name = secure_filename(f"{prefix}_{secrets.token_hex(8)}{ext}")
  profile_dir = os.path.join(app.config["UPLOAD_FOLDER"], "profiles")
  os.makedirs(profile_dir, exist_ok=True)
  destination = os.path.join(profile_dir, safe_name)
  try:
    file_obj.save(destination)
  except Exception:
    logging.exception("Failed to save profile image for %s", prefix)
    return None

  if replace_path:
    _remove_photo(replace_path)
  return os.path.join("uploads", "profiles", safe_name).replace(os.sep, "/")


def _generate_employee_pin(length: int = 4) -> str:
  """Return a simple numeric PIN with the desired length."""
  alphabet = "0123456789"
  return "".join(secrets.choice(alphabet) for _ in range(max(4, length)))


def _collect_existing_codes(db, exclude_id: int | None = None) -> set[str]:
  codes: set[str] = set()
  query = db.query(Employee.id, Employee.login_code)
  if exclude_id is not None:
    query = query.filter(Employee.id != exclude_id)
  for _, code in query:
    if code:
      normalized = code.strip().lower()
      if normalized:
        codes.add(normalized)
  return codes


def _generate_employee_login_code(name: str, existing_codes: set[str]) -> str:
  base = re.sub(r"[^A-Za-z]", "", name or "").upper()
  if len(base) >= 3:
    prefix = base[:3]
  elif base:
    prefix = (base + "TEAM")[:3]
  else:
    prefix = "TEAM"

  attempt = 0
  while True:
    suffix = "".join(secrets.choice("0123456789") for _ in range(3))
    code = f"{prefix}{suffix}"
    key = code.lower()
    if key not in existing_codes:
      existing_codes.add(key)
      return code
    attempt += 1
    if attempt > 20:
      prefix = "PXF"


def _remember_credentials_for_session(employee_id: int, code: str, pin: str) -> None:
  snippets = session.get("credential_snippets", {})
  snippets[str(employee_id)] = {"code": code, "pin": pin}
  session["credential_snippets"] = snippets


def _generate_missing_employee_credentials(db) -> dict[int, dict[str, str | None]]:
  existing_codes = _collect_existing_codes(db)
  updated: dict[int, dict[str, str | None]] = {}
  any_changes = False
  for emp in db.query(Employee).all():
    current_code = (emp.login_code or "").strip()
    current_pin_hash = (emp.login_pin_hash or "").strip()
    code_generated = None
    pin_generated = None
    if not current_code:
      code_generated = _generate_employee_login_code(emp.name, existing_codes)
      emp.login_code = code_generated
      any_changes = True
    if not current_pin_hash:
      pin_generated = _generate_employee_pin()
      emp.login_pin_hash = generate_password_hash(pin_generated)
      any_changes = True
    if code_generated or pin_generated:
      updated[emp.id] = {
        "code": emp.login_code,
        "pin": pin_generated,
      }
  if any_changes:
    db.commit()
  return updated


def login_required(view_func):
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    if session.get("role") == "admin" and session.get("auth"):
      return view_func(*args, **kwargs)
    return redirect(url_for("login", next=request.url))

  return wrapper


def employee_login_required(view_func):
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    if session.get("role") == "employee" and session.get("employee_id"):
      return view_func(*args, **kwargs)
    return redirect(url_for("login", next=request.url))

  return wrapper


@app.teardown_appcontext
def _remove_scoped_session(_exc=None):
  SessionLocal.remove()


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
    phone_region = _infer_region_from_netloc(parsed_start.netloc) or DEFAULT_PHONE_REGION

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
                n = normalize_phone(num, region=phone_region)
                if n:
                    phones.add(n)

        for tag_name in VISIBLE_TAGS:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(" ", strip=True)
                if not text:
                    continue
                if len(text) > 300:
                    continue
                for n in find_labelled_phones(text, region=phone_region):
                    phones.add(n)

        for tag in soup.find_all(attrs=True):
            if tag.name in {"script", "style", "noscript", "svg"}:
                continue
            for attr, val in tag.attrs.items():
                if isinstance(val, str):
                    lower_attr = attr.lower()
                    if lower_attr == "style":
                        continue
                    if any(k in lower_attr for k in ("tel", "phone", "kontakt", "mobil", "fax")):
                        n = normalize_phone(val, region=phone_region)
                        if n:
                            phones.add(n)
                    else:
                        for n in find_labelled_phones(val, region=phone_region):
                            phones.add(n)
                elif isinstance(val, (list, tuple)):
                    for part in val:
                        for n in find_labelled_phones(str(part), region=phone_region):
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
                    n = normalize_phone(num, region=phone_region)
                    if n:
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
                        for n in find_labelled_phones(t, region=phone_region):
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

      normalized_phones: list[str] = []
      for phone in phones:
        p = normalize_phone(phone, region=phone_region)
        if not p or p in seen_phones:
          continue
        seen_phones.add(p)
        normalized_phones.append(p)

      new_emails: list[str] = []
      for email in emails:
        e = email.lower().strip()
        if not e or e in seen_emails:
          continue
        seen_emails.add(e)
        new_emails.append(email)

      if new_emails:
        phone_sample = normalized_phones[0] if normalized_phones else ""
        for email in new_emails:
          rows.append({"url": url, "email": email, "phone": phone_sample})
      else:
        for phone in normalized_phones:
          rows.append({"url": url, "email": "", "phone": phone})

    app.logger.info("Crawl finished: found %d contact rows", len(rows))
    return rows


def _get_day_range(start: date | None = None, weeks: int = 1):
    """
    Return list of dates covering the given number of weeks (starting Monday of the reference week).
    Clamped to max 12 weeks to keep the grid manageable.
    """
    weeks = max(1, min(int(weeks or 1), 12))
    if start is None:
        start = date.today()
    monday = start - timedelta(days=start.weekday())
    total_days = weeks * 7
    return [monday + timedelta(days=i) for i in range(total_days)]


def _load_schedule_context(db, week_days):
    employees = db.query(Employee).order_by(Employee.name).all()
    sites = db.query(Site).order_by(Site.name).all()
    shifts = db.query(Shift).filter(Shift.day >= week_days[0], Shift.day <= week_days[-1]).all()

    matrix = {}
    for s in shifts:
        key = (s.employee_id, s.day)
        shift_info = {
            'id': s.id,
        'site_id': s.site_id,
            'label': f"{s.site.name} — {s.site.address or 'No address'} ({s.start_time.strftime('%H:%M')}–{s.end_time.strftime('%H:%M')})"
        }
        matrix.setdefault(key, []).append(shift_info)
    for key in matrix:
        matrix[key].sort(key=lambda x: x['label'])
    return employees, sites, matrix


def _shift_scheduled_duration(shift: Shift) -> timedelta:
  start_dt = datetime.combine(shift.day, shift.start_time)
  end_dt = datetime.combine(shift.day, shift.end_time)
  if end_dt <= start_dt:
    end_dt += timedelta(days=1)
  return end_dt - start_dt


def _shift_actual_duration(shift: Shift) -> timedelta | None:
  if not (shift.clock_in_at and shift.clock_out_at):
    return None
  delta = shift.clock_out_at - shift.clock_in_at
  if delta.total_seconds() < 0:
    delta += timedelta(days=1)
  return delta


def _format_hours(delta: timedelta | None, *, signed: bool = False) -> str:
  if delta is None:
    return "—"
  hours = delta.total_seconds() / 3600
  hours = round(hours + 0.0000001, 2)
  if signed:
    return f"{hours:+.2f} h"
  return f"{hours:.2f} h"


def _format_clock(dt_val: datetime | None, *, reference_day: date | None = None) -> str:
  if not dt_val:
    return "—"
  if reference_day and dt_val.date() != reference_day:
    return dt_val.strftime("%d.%m %H:%M")
  return dt_val.strftime("%H:%M")


def _month_range(month_value: str | None) -> tuple[date, date] | None:
  if not month_value:
    return None
  try:
    start_dt = datetime.strptime(month_value, "%Y-%m")
  except ValueError:
    return None
  start_date = date(start_dt.year, start_dt.month, 1)
  if start_dt.month == 12:
    next_month = date(start_dt.year + 1, 1, 1)
  else:
    next_month = date(start_dt.year, start_dt.month + 1, 1)
  end_date = next_month - timedelta(days=1)
  return start_date, end_date


def _calculate_site_hours_for_range(
  db,
  site_id: int,
  start_date: date,
  end_date: date,
) -> float:
  shifts = (
    db.query(Shift)
    .filter(
      Shift.site_id == site_id,
      Shift.day >= start_date,
      Shift.day <= end_date,
    )
    .all()
  )
  total_delta = timedelta(0)
  for shift in shifts:
    actual = _shift_actual_duration(shift)
    total_delta += actual if actual is not None else _shift_scheduled_duration(shift)
  hours = total_delta.total_seconds() / 3600
  return round(hours + 0.0000001, 2)


def _calculate_monthly_income(db, year: int, month: int) -> dict[str, float]:
  """Calculate income for a given month grouped by site."""
  start_date = date(year, month, 1)
  if month == 12:
    end_date = date(year + 1, 1, 1) - timedelta(days=1)
  else:
    end_date = date(year, month + 1, 1) - timedelta(days=1)

  shifts = (
    db.query(Shift)
    .options(joinedload(Shift.site))
    .filter(Shift.day >= start_date, Shift.day <= end_date)
    .all()
  )

  income_by_site: dict[int, dict[str, float]] = {}
  for shift in shifts:
    if not shift.site:
      continue
    site_id = shift.site.id
    if site_id not in income_by_site:
      income_by_site[site_id] = {
        "site_name": shift.site.name,
        "hourly_rate": shift.site.hourly_rate or 50.0,
        "hours": 0.0,
        "income": 0.0,
      }

    actual_delta = _shift_actual_duration(shift)
    delta = actual_delta if actual_delta is not None else _shift_scheduled_duration(shift)
    hours = delta.total_seconds() / 3600
    hours = round(hours + 0.0000001, 2)

    income_by_site[site_id]["hours"] += hours
    income_by_site[site_id]["income"] = income_by_site[site_id]["hours"] * income_by_site[site_id]["hourly_rate"]

  return {
    site_id: data
    for site_id, data in sorted(
      income_by_site.items(),
      key=lambda x: x[1]["site_name"],
    )
  }


def _get_all_monthly_summaries(
  db,
  start_year: int = 2025,
  start_month: int = 12,
) -> list[dict]:
  """Get income summaries from a fixed start month up to the current month."""
  if start_month < 1 or start_month > 12:
    start_month = 12

  start_point = date(start_year, start_month, 1)
  today = date.today()
  end_point = date(today.year, today.month, 1)

  if start_point > end_point:
    return []

  summaries: list[dict] = []
  current = start_point
  while current <= end_point:
    current_year = current.year
    current_month = current.month

    income_by_site = _calculate_monthly_income(db, current_year, current_month)
    total_income = sum(data["income"] for data in income_by_site.values())
    total_hours = sum(data["hours"] for data in income_by_site.values())

    summaries.append({
      "year": current_year,
      "month": current_month,
      "month_name": date(current_year, current_month, 1).strftime("%B %Y"),
      "total_income": round(total_income, 2),
      "total_hours": round(total_hours, 2),
      "sites": income_by_site,
    })

    if current_month == 12:
      current = date(current_year + 1, 1, 1)
    else:
      current = date(current_year, current_month + 1, 1)

  return sorted(summaries, key=lambda x: (x["year"], x["month"]), reverse=True)


def _collect_hours_report(
  db,
  start_date: date,
  end_date: date,
  employee_id: int | None = None,
) -> list[dict[str, Any]]:
  query = (
    db.query(Shift)
    .options(joinedload(Shift.employee), joinedload(Shift.site))
    .filter(Shift.day >= start_date, Shift.day <= end_date)
  )
  if employee_id:
    query = query.filter(Shift.employee_id == employee_id)

  shifts = query.order_by(Shift.employee_id, Shift.day, Shift.start_time).all()

  report_map: dict[int, dict[str, Any]] = {}
  for shift in shifts:
    employee = shift.employee
    if not employee:
      continue
    site = shift.site
    record = report_map.setdefault(
      employee.id,
      {
        "employee": employee,
        "rows": [],
        "scheduled_total": timedelta(0),
        "actual_total": timedelta(0),
        "actual_count": 0,
        "diff_total": timedelta(0),
        "diff_count": 0,
      },
    )

    scheduled_delta = _shift_scheduled_duration(shift)
    actual_delta = _shift_actual_duration(shift)
    diff_delta = actual_delta - scheduled_delta if actual_delta is not None else None

    record["rows"].append(
      {
        "date": shift.day,
        "site_name": site.name if site else "Unassigned",
        "site_address": site.address if site and site.address else "",
        "start_time": shift.start_time,
        "end_time": shift.end_time,
        "clock_in": shift.clock_in_at,
        "clock_out": shift.clock_out_at,
        "scheduled_delta": scheduled_delta,
        "actual_delta": actual_delta,
        "diff_delta": diff_delta,
        "crosses_midnight": shift.end_time <= shift.start_time,
      }
    )

    record["scheduled_total"] += scheduled_delta
    if actual_delta is not None:
      record["actual_total"] += actual_delta
      record["actual_count"] += 1
    if diff_delta is not None:
      record["diff_total"] += diff_delta
      record["diff_count"] += 1

  if employee_id and employee_id not in report_map:
    employee = db.get(Employee, employee_id)
    if employee:
      report_map[employee_id] = {
        "employee": employee,
        "rows": [],
        "scheduled_total": timedelta(0),
        "actual_total": timedelta(0),
        "actual_count": 0,
        "diff_total": timedelta(0),
        "diff_count": 0,
      }

  return sorted(
    report_map.values(),
    key=lambda item: item["employee"].name.lower(),
  )


def _generate_hours_pdf(
  start_date: date,
  end_date: date,
  report_rows: list[dict[str, Any]],
) -> io.BytesIO:
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
  subtitle_style = ParagraphStyle(
    "HoursSubtitle",
    parent=styles["Heading4"],
    textColor=colors.HexColor("#475569"),
  )
  section_style = ParagraphStyle(
    "HoursSection",
    parent=styles["Heading3"],
    fontSize=14,
    leading=16,
    spaceBefore=12,
    spaceAfter=6,
    textColor=colors.HexColor("#0f172a"),
  )
  header_style = ParagraphStyle(
    "HoursHeader",
    parent=styles["Heading5"],
    alignment=1,
    fontSize=10,
    leading=12,
    textColor=colors.whitesmoke,
  )
  cell_style = ParagraphStyle(
    "HoursCell",
    parent=styles["BodyText"],
    fontSize=9,
    leading=12,
    textColor=colors.HexColor("#0f172a"),
  )

  elements: list[Any] = []

  logo_path = os.path.join(app.root_path, "static", "logo.png")
  if os.path.exists(logo_path):
    logo = Image(logo_path, width=1.0 * inch, height=1.0 * inch)
    logo.hAlign = "LEFT"
    elements.append(logo)
    elements.append(Spacer(1, 8))

  elements.append(Paragraph("Employee Hours Report", title_style))
  elements.append(
    Paragraph(
      f"Period: {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}",
      subtitle_style,
    )
  )

  total_scheduled = sum((row["scheduled_total"] for row in report_rows), timedelta(0))
  recorded_actual = sum((row["actual_total"] for row in report_rows), timedelta(0))
  has_recorded = any(row["actual_count"] > 0 for row in report_rows)
  total_diff = sum((row["diff_total"] for row in report_rows), timedelta(0)) if has_recorded else None

  summary_parts = [f"Scheduled hours: {_format_hours(total_scheduled)}"]
  if has_recorded:
    summary_parts.append(
      f"Recorded hours: {_format_hours(recorded_actual)}"
    )
    summary_parts.append(
      f"Recorded vs scheduled: {_format_hours(total_diff, signed=True)}"
    )
  else:
    summary_parts.append("Recorded hours: —")
  elements.append(Paragraph(" | ".join(summary_parts), styles["Normal"]))
  elements.append(Spacer(1, 12))

  if not report_rows:
    elements.append(Paragraph("No shifts found for the selected period.", styles["Normal"]))
    doc.build(elements)
    buf.seek(0)
    return buf

  for entry in report_rows:
    employee = entry["employee"]
    header_text = employee.name
    if employee.role:
      header_text += f" ({employee.role})"
    elements.append(Paragraph(header_text, section_style))

    table_data: list[list[Any]] = [
      [
        Paragraph("<b>Date</b>", header_style),
        Paragraph("<b>Site</b>", header_style),
        Paragraph("<b>Scheduled</b>", header_style),
        Paragraph("<b>Clocked in</b>", header_style),
        Paragraph("<b>Clocked out</b>", header_style),
        Paragraph("<b>Scheduled hrs</b>", header_style),
        Paragraph("<b>Worked hrs</b>", header_style),
        Paragraph("<b>Difference</b>", header_style),
      ]
    ]

    for row in entry["rows"]:
      date_str = row["date"].strftime("%a %d %b %Y")
      site_line = row["site_name"]
      if row["site_address"]:
        site_line += f"<br/><font size='8' color='#64748b'>{row['site_address']}</font>"
      scheduled_window = f"{row['start_time'].strftime('%H:%M')} - {row['end_time'].strftime('%H:%M')}"
      if row["crosses_midnight"]:
        scheduled_window += " (+1 day)"

      table_data.append(
        [
          Paragraph(date_str, cell_style),
          Paragraph(site_line, cell_style),
          Paragraph(scheduled_window, cell_style),
          Paragraph(_format_clock(row["clock_in"], reference_day=row["date"]), cell_style),
          Paragraph(_format_clock(row["clock_out"], reference_day=row["date"]), cell_style),
          Paragraph(_format_hours(row["scheduled_delta"]), cell_style),
          Paragraph(_format_hours(row["actual_delta"]), cell_style),
          Paragraph(_format_hours(row["diff_delta"], signed=True), cell_style),
        ]
      )

    totals_row = [
      Paragraph("", cell_style),
      Paragraph("", cell_style),
      Paragraph("", cell_style),
      Paragraph("", cell_style),
      Paragraph("Totals", cell_style),
      Paragraph(_format_hours(entry["scheduled_total"]), cell_style),
      Paragraph(
        _format_hours(entry["actual_total"] if entry["actual_count"] else None),
        cell_style,
      ),
      Paragraph(
        _format_hours(entry["diff_total"] if entry["diff_count"] else None, signed=True),
        cell_style,
      ),
    ]
    table_data.append(totals_row)

    col_widths = [1.4 * inch, 2.1 * inch, 1.2 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch]

    table = Table(table_data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
      TableStyle(
        [
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
          ("ALIGN", (0, 0), (-1, -1), "LEFT"),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("FONTSIZE", (0, 0), (-1, 0), 10),
          (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -2),
            [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")],
          ),
          ("ROWBACKGROUNDS", (0, -1), (-1, -1), [colors.HexColor("#dbeafe")]),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5f5")),
          ("LEFTPADDING", (0, 0), (-1, -1), 8),
          ("RIGHTPADDING", (0, 0), (-1, -1), 8),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
          ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]
      )
    )
    elements.append(table)
    elements.append(Spacer(1, 16))

  doc.build(elements)
  buf.seek(0)
  return buf


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

    len_days = max(len(week_days), 1)
    employee_col_width = 1.8 * inch
    remaining_width = max(doc.width - employee_col_width, 0.0)
    per_day_width = remaining_width / len_days if len_days else 1.0 * inch
    col_widths = [employee_col_width] + [per_day_width] * len_days

    table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=col_widths)
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



def _generate_contacts_pdf(rows: list[dict[str, str]]):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=32,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ContactsTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "ContactsSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )

    elements: list = []
    generated_at = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    elements.append(Paragraph("Putzelf Marketing - Contact Crawl", title_style))
    elements.append(Paragraph(f"Generated {generated_at}", subtitle_style))

    table_data = [["Email", "Phone"]]
    for row in rows:
        email = (row.get("email") or "").strip() or "-"
        phone = (row.get("phone") or "").strip() or "-"
        table_data.append([email, phone])
    if len(table_data) == 1:
        table_data.append(["-", "-"])

    table = Table(table_data, colWidths=[doc.width * 0.6, doc.width * 0.4], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("LINEABOVE", (0, 1), (-1, -1), 0.25, colors.HexColor("#cbd5f5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f1f5f9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#0f172a")),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf


def _site_exists(db, name: str, address: str, exclude_id: int | None = None) -> bool:
    """Return True if a site with same name+address (case-insensitive) exists."""
    name_norm = (name or "").strip().lower()
    address_norm = (address or "").strip().lower()
    if not name_norm or not address_norm:
        return False
    q = db.query(Site).filter(
        func.lower(Site.name) == name_norm,
        func.lower(Site.address) == address_norm,
    )
    if exclude_id:
        q = q.filter(Site.id != exclude_id)
    return db.query(q.exists()).scalar()


def _build_admin_dashboard_context(db):
  today = date.today()
  week_start = today - timedelta(days=today.weekday())
  week_end = week_start + timedelta(days=7)

  stats = {
    "employees": db.query(func.count(Employee.id)).scalar() or 0,
    "sites": db.query(func.count(Site.id)).scalar() or 0,
    "weekly_shifts": db.query(func.count(Shift.id))
    .filter(Shift.day >= week_start, Shift.day < week_end)
    .scalar()
    or 0,
    "new_leads": db.query(func.count(Lead.id))
    .filter(Lead.created_at >= datetime.utcnow() - timedelta(days=7))
    .scalar()
    or 0,
  }

  assigned_site_rows = (
    db.query(Shift.site_id)
    .filter(Shift.day >= week_start, Shift.day < week_end)
    .distinct()
    .all()
  )
  assigned_site_ids = [row[0] for row in assigned_site_rows if row[0] is not None]
  if assigned_site_ids:
    unassigned_query = db.query(Site).filter(~Site.id.in_(assigned_site_ids))
  else:
    unassigned_query = db.query(Site)
  unassigned_count = unassigned_query.count()
  stats["unassigned_sites"] = unassigned_count
  unassigned_sample = unassigned_query.order_by(Site.name).limit(5).all()

  recent_employees = (
    db.query(Employee).order_by(Employee.id.desc()).limit(5).all()
  )
  recent_sites = db.query(Site).order_by(Site.id.desc()).limit(5).all()
  upcoming_shifts = (
    db.query(Shift)
    .filter(Shift.day >= today)
    .order_by(Shift.day.asc(), Shift.start_time.asc())
    .limit(6)
    .all()
  )

  week_label = f"{week_start.strftime('%d %b')} – {(week_end - timedelta(days=1)).strftime('%d %b')}"
  today_label = today.strftime("%A %d %b %Y")

  return {
    "stats": stats,
    "recent_employees": recent_employees,
    "recent_sites": recent_sites,
    "upcoming_shifts": upcoming_shifts,
    "unassigned_sites_sample": unassigned_sample,
    "week_label": week_label,
    "today_label": today_label,
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
  if next_url and next_url.startswith("/employee"):
    return next_url
  return url_for("employee_dashboard")


@app.route("/login", methods=["GET", "POST"])
def login():
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
      if username_raw == AUTH_USERNAME and password == AUTH_PASSWORD:
        session.clear()
        session["auth"] = True
        session["role"] = "admin"
        session["user"] = username_raw
        return redirect(next_url or url_for("admin_dashboard"))

      normalized = username_raw.lower()
      db = SessionLocal()
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
          return redirect(_employee_redirect_target(next_url))
      error = "Invalid credentials"
    else:
      error = "Username and password are required"

  return render_template_string(LOGIN_TEMPLATE, error=error, next_value=next_url)


@app.route("/employee")
@app.route("/employee/dashboard")
@employee_login_required
def employee_dashboard():
  employee_id = session.get("employee_id")
  employee_name = session.get("employee_name", "Team member")
  today = date.today()
  db = SessionLocal()
  shift_cards = []
  upcoming_cards = []
  history_cards = []

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
      start_label = start.strftime("%I:%M %p").lstrip("0")
      end_label = end.strftime("%I:%M %p").lstrip("0")
      return f"{start_label} – {end_label}"
    if start:
      start_label = start.strftime("%I:%M %p").lstrip("0")
      return f"Starts {start_label}"
    if end:
      end_label = end.strftime("%I:%M %p").lstrip("0")
      return f"Ends {end_label}"
    return "Time to be scheduled"

  def _status_text(shift_obj: Shift) -> str:
    if shift_obj.clock_out_at:
      return "Completed"
    if shift_obj.clock_in_at:
      return "In progress"
    return "Scheduled"

  try:
    todays_shifts = (
      db.query(Shift)
      .filter(Shift.employee_id == employee_id, Shift.day == today)
      .order_by(Shift.start_time.asc())
      .all()
    )
    for shift in todays_shifts:
      site_name = shift.site.name if shift.site else "Scheduled job"
      address = (shift.site.address or "Address coming soon") if shift.site else "Address coming soon"
      map_url = None
      if shift.site and shift.site.address:
        map_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(shift.site.address)}"

      start_label = shift.start_time.strftime("%I:%M %p").lstrip("0")
      end_label = shift.end_time.strftime("%I:%M %p").lstrip("0")

      clocked_in = bool(shift.clock_in_at)
      clocked_out = bool(shift.clock_out_at)
      if clocked_out:
        status_label = "Complete"
        status_badge = "badge-complete"
      elif clocked_in:
        status_label = "In progress"
        status_badge = "badge-progress"
      else:
        status_label = "Scheduled"
        status_badge = "badge-scheduled"

      clock_in_display = shift.clock_in_at.strftime("%I:%M %p") if shift.clock_in_at else "—"
      clock_out_display = shift.clock_out_at.strftime("%I:%M %p") if shift.clock_out_at else "—"

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
          "instructions": (shift.instructions or "No special instructions today."),
          "time_window": f"{start_label} – {end_label}",
          "status_label": status_label,
          "status_badge": status_badge,
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
      site_name = shift.site.name if shift.site else "Scheduled job"
      address = shift.site.address if shift.site and shift.site.address else None
      upcoming_cards.append(
        {
          "id": shift.id,
          "site_name": site_name,
          "day_label": shift.day.strftime("%a, %d %b %Y") if shift.day else "Date to be set",
          "time_window": _time_window_label(shift),
          "status_label": _status_text(shift),
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
        status_label = "Completed"
      elif shift.clock_in_at:
        status_label = "In progress"
      else:
        status_label = "Scheduled"

      history_cards.append(
        {
          "id": shift.id,
          "site_name": shift.site.name if shift.site else "Scheduled job",
          "day_label": shift.day.strftime("%a, %d %b %Y"),
          "time_window": _time_window_label(shift),
          "status_label": status_label,
          "scheduled_duration": _format_minutes(scheduled_minutes),
          "actual_duration": _format_minutes(actual_minutes),
          "has_actual_duration": actual_minutes is not None,
          "instructions": shift.instructions or "No notes recorded.",
        }
      )
  finally:
    db.close()

  count = len(shift_cards)
  if count == 0:
    friendly_message = "No jobs scheduled right now."
  elif count == 1:
    friendly_message = "You have 1 mission waiting."
  else:
    friendly_message = f"{count} missions lined up for today."

  today_label = today.strftime("%A %d %b %Y")
  return render_template_string(
    EMPLOYEE_DASHBOARD_TEMPLATE,
    employee_name=employee_name,
    today_label=today_label,
    friendly_message=friendly_message,
    shifts=shift_cards,
    upcoming_jobs=upcoming_cards,
    history=history_cards,
  )


@app.route("/employee/shifts/<int:shift_id>/clock-in", methods=["POST"])
@employee_login_required
def employee_clock_in(shift_id: int):
  employee_id = session.get("employee_id")
  lat = _coerce_float(request.form.get("lat"))
  lng = _coerce_float(request.form.get("lng"))

  db = SessionLocal()
  try:
    shift = db.get(Shift, shift_id)
    if not shift or shift.employee_id != employee_id:
      flash("That shift was not found for your profile.")
      return redirect(url_for("employee_dashboard"))

    if shift.day != date.today():
      flash("This shift is not scheduled for today.")
      return redirect(url_for("employee_dashboard"))

    if not shift.clock_in_at:
      shift.clock_in_at = datetime.utcnow()
    if lat is not None:
      shift.clock_in_lat = lat
    if lng is not None:
      shift.clock_in_lng = lng
    db.commit()
    flash("Clocked in. Go make it shine!")
  finally:
    db.close()

  return redirect(url_for("employee_dashboard"))


@app.route("/employee/shifts/<int:shift_id>/upload", methods=["POST"])
@employee_login_required
def employee_upload_photo(shift_id: int):
  employee_id = session.get("employee_id")
  photo_type = (request.form.get("photo_type") or "").strip().lower()
  file = request.files.get("photo")

  db = SessionLocal()
  try:
    shift = db.get(Shift, shift_id)
    if not shift or shift.employee_id != employee_id:
      flash("That shift was not found for your profile.")
      return redirect(url_for("employee_dashboard"))

    if photo_type not in {"before", "after"}:
      flash("Please choose whether this is a before or after photo.")
      return redirect(url_for("employee_dashboard"))

    if not file or not file.filename:
      flash("Choose a photo to upload first.")
      return redirect(url_for("employee_dashboard"))

    if not _allowed_image(file.filename):
      flash("Unsupported file type. Use PNG, JPG, or JPEG.")
      return redirect(url_for("employee_dashboard"))

    ext = os.path.splitext(file.filename)[1].lower()
    safe_name = secure_filename(f"shift{shift_id}_{photo_type}_{secrets.token_hex(6)}{ext}")
    destination = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    try:
      file.save(destination)
    except OSError:
      logging.exception("Failed to save uploaded photo for shift %s", shift_id)
      flash("Could not save that photo. Please try again.")
      return redirect(url_for("employee_dashboard"))

    relative_path = os.path.join("uploads", safe_name).replace(os.sep, "/")
    photo_label = "Before" if photo_type == "before" else "After"
    if photo_type == "before":
      _remove_photo(shift.before_photo_path)
      shift.before_photo_path = relative_path
    else:
      _remove_photo(shift.after_photo_path)
      shift.after_photo_path = relative_path

    db.commit()
    flash(f"{photo_label} photo saved. Nice work!")
  finally:
    db.close()

  return redirect(url_for("employee_dashboard"))


@app.route("/employee/shifts/<int:shift_id>/complete", methods=["POST"])
@employee_login_required
def employee_complete_shift(shift_id: int):
  employee_id = session.get("employee_id")
  lat = _coerce_float(request.form.get("lat"))
  lng = _coerce_float(request.form.get("lng"))

  db = SessionLocal()
  try:
    shift = db.get(Shift, shift_id)
    if not shift or shift.employee_id != employee_id:
      flash("That shift was not found for your profile.")
      return redirect(url_for("employee_dashboard"))

    if shift.day != date.today():
      flash("This shift is not scheduled for today.")
      return redirect(url_for("employee_dashboard"))

    if not shift.clock_in_at:
      shift.clock_in_at = datetime.utcnow()
    shift.clock_out_at = datetime.utcnow()
    if lat is not None:
      shift.clock_out_lat = lat
    if lng is not None:
      shift.clock_out_lng = lng

    db.commit()
    flash("Shift complete! Thanks for going the extra mile.")
  finally:
    db.close()

  return redirect(url_for("employee_dashboard"))


@app.route("/shift/delete/<int:shift_id>")
@login_required
def delete_shift(shift_id):
    db = SessionLocal()
    try:
        shift = db.get(Shift, shift_id)
        if shift:
            db.delete(shift)
            db.commit()
        return redirect(request.referrer or url_for("schedule_dashboard"))
    finally:
        db.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule_dashboard():
    db = SessionLocal()
    try:
        if request.method == "POST":
            emp_id = request.form.get("employee_id")
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
            if emp_id and site_id and day_values and start_str and duration_hours_str:
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
                for day_val in day_values:
                  end_dt = datetime.combine(day_val, start_val) + duration_delta
                  end_val = end_dt.time()
                  shift = Shift(
                    employee_id=int(emp_id),
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
            return redirect(url_for("schedule_dashboard"))

        selected_employee_id = request.args.get("employee_id", type=int)
        selected_site_id = request.args.get("site_id", type=int)
        weeks = request.args.get("weeks", default=1, type=int) or 1
        weeks = max(1, min(weeks, 12))
        start_date_str = request.args.get("start_date")
        start_date_val = None
        if start_date_str:
            try:
                start_date_val = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                start_date_val = None

        week_days = _get_day_range(start=start_date_val, weeks=weeks)
        employees, sites, matrix = _load_schedule_context(db, week_days)

        selected_employee = None
        selected_site = None
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

        schedule_html = render_template_string(
            SCHEDULE_TEMPLATE,
            employees=employees,
            visible_employees=visible_employees,
            sites=sites,
            week_days=week_days,
            weeks=weeks,
            start_date=start_date_val.isoformat() if start_date_val else "",
            cells=filtered_matrix,
            reportlab_available=REPORTLAB_AVAILABLE,
            selected_employee_id=selected_employee_id,
            selected_site_id=selected_site_id,
            selected_employee=selected_employee,
            selected_site=selected_site,
            pdf_url=pdf_url,
            hours_pdf_url=hours_pdf_url,
            active_page="schedule",
        )
        return schedule_html
    finally:
        db.close()


@app.route("/admin")
@login_required
def admin_dashboard():
  db = SessionLocal()
  try:
    context = _build_admin_dashboard_context(db)
    return render_template_string(
      ADMIN_TEMPLATE,
      active_page="dashboard",
      **context,
    )
  finally:
    db.close()


@app.route("/dashboard")
@login_required
def dashboard_redirect():
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/employees", methods=["GET", "POST"])
@login_required
def admin_employees():
  db = SessionLocal()
  try:
    search_q = (request.args.get("q") or "").strip()
    if request.method == "POST":
      action = (request.form.get("action") or "create").strip().lower()
      emp_id = request.form.get("id")
      redirect_q = (request.form.get("redirect_q") or "").strip()
      redirect_page_raw = (request.form.get("redirect_page") or "").strip()
      redirect_page_val = None
      if redirect_page_raw.isdigit():
        redirect_page_val = max(int(redirect_page_raw), 1)
      redirect_params: dict[str, int | str] = {}
      if redirect_q:
        redirect_params["q"] = redirect_q
      if redirect_page_val and redirect_page_val > 1:
        redirect_params["page"] = redirect_page_val
      redirect_url = url_for("admin_employees", **redirect_params)

      if action == "create":
        name = (request.form.get("name") or "").strip()
        role = (request.form.get("role") or "").strip()
        if name:
          employee = Employee(name=name, role=role or "Cleaner")
          db.add(employee)
          db.commit()
          existing_codes = _collect_existing_codes(db, exclude_id=employee.id)
          generated_pin = None
          if not (employee.login_code or "").strip():
            employee.login_code = _generate_employee_login_code(name, existing_codes)
          if not (employee.login_pin_hash or "").strip():
            generated_pin = _generate_employee_pin()
            employee.login_pin_hash = generate_password_hash(generated_pin)
          db.commit()
          if generated_pin:
            _remember_credentials_for_session(employee.id, employee.login_code, generated_pin)
      elif action == "update" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp:
          name = (request.form.get("name") or "").strip()
          role = (request.form.get("role") or "").strip()
          if name:
            emp.name = name
            emp.role = role or None
            db.commit()
      elif action == "delete" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp:
          db.delete(emp)
          db.commit()
      elif action == "credentials_share" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp:
          existing_codes = _collect_existing_codes(db, exclude_id=emp.id)
          if not (emp.login_code or "").strip():
            emp.login_code = _generate_employee_login_code(emp.name, existing_codes)
          new_pin = _generate_employee_pin()
          emp.login_pin_hash = generate_password_hash(new_pin)
          db.commit()
          _remember_credentials_for_session(emp.id, emp.login_code, new_pin)
          flash(f"Credentials refreshed for {emp.name}.")
        return redirect(redirect_url)
      elif action == "credentials_update" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp:
          new_email = (request.form.get("login_email") or "").strip()
          new_code = (request.form.get("login_code") or "").strip().upper()
          new_pin = (request.form.get("login_pin") or "").strip()
          if not new_code:
            flash("Login code is required to save credentials.", "warning")
            return redirect(redirect_url)
          existing_codes = _collect_existing_codes(db, exclude_id=emp.id)
          if new_code.lower() in existing_codes:
            flash("That login code is already in use.", "warning")
            return redirect(redirect_url)
          emp.login_code = new_code
          emp.login_email = new_email or None
          pin_snippet = None
          if new_pin:
            if not new_pin.isdigit() or len(new_pin) != 4:
              flash("PINs must be exactly 4 digits.", "warning")
              return redirect(redirect_url)
            emp.login_pin_hash = generate_password_hash(new_pin)
            pin_snippet = new_pin
          db.commit()
          if pin_snippet:
            _remember_credentials_for_session(emp.id, emp.login_code, pin_snippet)
            flash(f"Credentials updated for {emp.name}.")
          else:
            flash(f"Login details saved for {emp.name}.")
        return redirect(redirect_url)

      return redirect(redirect_url)

    credential_snippets = session.pop("credential_snippets", {})
    auto_generated = _generate_missing_employee_credentials(db)
    for emp_id, data in auto_generated.items():
      key = str(emp_id)
      if key not in credential_snippets:
        credential_snippets[key] = {
          "code": data.get("code"),
          "pin": data.get("pin"),
        }

    base_query = db.query(Employee)
    if search_q:
      like = f"%{search_q}%"
      base_query = base_query.filter(
        or_(
          Employee.name.ilike(like),
          Employee.role.ilike(like),
        )
      )

    total_employees = db.query(func.count(Employee.id)).scalar() or 0
    filtered_employees = base_query.count()

    per_page = 3
    page = request.args.get("page", default=1, type=int)
    if page is None or page < 1:
      page = 1
    if filtered_employees == 0:
      total_pages = 1
      page = 1
      offset = 0
    else:
      total_pages = max(1, math.ceil(filtered_employees / per_page))
      if page > total_pages:
        page = total_pages
      offset = (page - 1) * per_page

    employees = (
      base_query
      .order_by(Employee.id.desc())
      .offset(offset)
      .limit(per_page)
      .all()
    )

    page_employees = len(employees)
    has_prev = page > 1 and filtered_employees > 0
    has_next = page < total_pages and filtered_employees > 0
    prev_page = page - 1 if has_prev else None
    next_page = page + 1 if has_next else None

    shift_counts: dict[int, int] = {}
    employee_shift_groups: dict[int, dict[str, list[dict[str, str]]]] = {}
    employee_ids = [emp.id for emp in employees if emp.id]
    if employee_ids:
      shift_counts = {
        emp_id: count
        for emp_id, count in (
          db.query(Shift.employee_id, func.count(Shift.id))
          .filter(Shift.employee_id.in_(employee_ids))
          .group_by(Shift.employee_id)
          .all()
        )
      }
      for emp_id in employee_ids:
        employee_shift_groups[emp_id] = {"upcoming": [], "history": []}
      shift_rows = (
        db.query(Shift)
        .filter(Shift.employee_id.in_(employee_ids))
        .order_by(Shift.day.asc(), Shift.start_time.asc())
        .all()
      )
      today_marker = date.today()
      for shift in shift_rows:
        if not shift.employee_id:
          continue
        bucket = "upcoming"
        if shift.day and shift.day < today_marker:
          bucket = "history"
        site_name = shift.site.name if shift.site else "Unassigned site"
        if shift.start_time and shift.end_time:
          start_label = shift.start_time.strftime("%I:%M %p").lstrip("0")
          end_label = shift.end_time.strftime("%I:%M %p").lstrip("0")
          time_window = f"{start_label} – {end_label}"
        elif shift.start_time:
          start_label = shift.start_time.strftime("%I:%M %p").lstrip("0")
          time_window = f"Starts {start_label}"
        else:
          time_window = "Time to be set"
        status_label = "Scheduled"
        if shift.clock_out_at:
          status_label = "Completed"
        elif shift.clock_in_at:
          status_label = "In progress"
        entry = {
          "site_name": site_name,
          "day_label": shift.day.strftime("%a, %d %b %Y") if shift.day else "Date to be set",
          "time_window": time_window,
          "status_label": status_label,
        }
        groups = employee_shift_groups.setdefault(shift.employee_id, {"upcoming": [], "history": []})
        if bucket == "history":
          groups[bucket].insert(0, entry)
        else:
          groups[bucket].append(entry)

    today_shifts = (
      db.query(func.count(Shift.id)).filter(Shift.day == date.today()).scalar()
      or 0
    )
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=7)
    scheduled_emp_ids = {
      row[0]
      for row in db.query(Shift.employee_id)
      .filter(Shift.day >= week_start, Shift.day < week_end)
      .distinct()
      .all()
      if row[0] is not None
    }
    unassigned_employees = max(total_employees - len(scheduled_emp_ids), 0)

    return render_template_string(
      ADMIN_EMPLOYEES_TEMPLATE,
      active_page="employees",
      employees=employees,
      shift_counts=shift_counts,
      total_employees=total_employees,
      filtered_employees=filtered_employees,
      search_q=search_q,
      today_shifts=today_shifts,
      unassigned_employees=unassigned_employees,
      credential_snippets=credential_snippets,
      employee_shift_groups=employee_shift_groups,
      page=page,
      per_page=per_page,
      total_pages=total_pages,
      has_prev=has_prev,
      has_next=has_next,
      prev_page=prev_page,
      next_page=next_page,
      page_employees=page_employees,
    )
  finally:
    db.close()


@app.route("/admin/sites", methods=["GET", "POST"])
@login_required
def admin_sites():
  db = SessionLocal()
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
            if _site_exists(db, name, address):
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
            if _site_exists(db, name, address, exclude_id=site.id):
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
          if site and not _site_exists(db, n, a, exclude_id=site.id):
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

    return render_template_string(
      ADMIN_SITES_TEMPLATE,
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


@app.route("/admin/profiles", methods=["GET", "POST"])
@login_required
def admin_profiles():
  db = SessionLocal()
  try:
    active_tab = (request.args.get("tab") or request.form.get("tab") or "employees").strip().lower()
    if active_tab not in {"employees", "clients"}:
      active_tab = "employees"

    if request.method == "POST":
      entity = (request.form.get("entity") or "").strip().lower()
      target_id = request.form.get("id", type=int)
      profile_action = (request.form.get("profile_action") or "save").strip().lower()

      if entity == "employee_profile" and target_id:
        emp = db.get(Employee, target_id)
        if emp:
          image_file = request.files.get("employee_profile_image")
          saved_image = _save_profile_image(image_file, f"employee_{emp.id}", replace_path=emp.profile_image_path)
          if image_file and getattr(image_file, "filename", "") and not saved_image:
            flash("Invalid employee image format. Use png/jpg/jpeg/gif/webp/heic.", "warning")
            return redirect(url_for("admin_profiles", tab=active_tab))
          emp.profile_phone = (request.form.get("profile_phone") or "").strip() or None
          emp.profile_emergency_name = (request.form.get("profile_emergency_name") or "").strip() or None
          emp.profile_emergency_phone = (request.form.get("profile_emergency_phone") or "").strip() or None
          emp.profile_address = (request.form.get("profile_address") or "").strip() or None
          emp.profile_notes = (request.form.get("profile_notes") or "").strip() or None
          if saved_image:
            emp.profile_image_path = saved_image
          db.commit()
          flash(f"Profile updated for {emp.name}.")
      elif entity == "site_profile" and target_id:
        site = db.get(Site, target_id)
        if site:
          image_file = request.files.get("site_profile_image")
          saved_image = _save_profile_image(image_file, f"site_{site.id}", replace_path=site.profile_image_path)
          if image_file and getattr(image_file, "filename", "") and not saved_image:
            flash("Invalid client logo format. Use png/jpg/jpeg/gif/webp/heic.", "warning")
            return redirect(url_for("admin_profiles", tab=active_tab))
          site.profile_company_name = (request.form.get("profile_company_name") or "").strip() or None
          site.profile_contact_name = (request.form.get("profile_contact_name") or "").strip() or None
          site.profile_contact_email = (request.form.get("profile_contact_email") or "").strip() or None
          site.profile_phone = (request.form.get("profile_phone") or "").strip() or None
          if "profile_billing_address" in request.form:
            site.profile_billing_address = (request.form.get("profile_billing_address") or "").strip() or None
          submitted_customer_id = (request.form.get("profile_tax_id") or "").strip()
          site.profile_tax_id = submitted_customer_id or site.profile_tax_id
          _ensure_site_customer_id(db, site)
          site.profile_notes = (request.form.get("profile_notes") or "").strip() or None
          site.contract_partner_name = (request.form.get("contract_partner_name") or "").strip() or None
          site.contract_contact_details = (request.form.get("contract_contact_details") or "").strip() or None
          if "profile_default_hourly_rate" in request.form:
            default_rate_raw = request.form.get("profile_default_hourly_rate")
            parsed_rate = _coerce_float(default_rate_raw)
            site.profile_default_hourly_rate = parsed_rate
          if saved_image:
            site.profile_image_path = saved_image

          if profile_action == "generate_contract":
            partner_name = (site.contract_partner_name or "").strip()
            company_name = (site.profile_company_name or site.name or "").strip()
            contact_details = (site.contract_contact_details or "").strip()
            if not partner_name or not company_name or not contact_details:
              flash("Please fill Name des partners, Firma, and Tel./ Fax / E-Mail before generating contract.", "warning")
              return redirect(url_for("admin_profiles", tab=active_tab))

            session_date = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            db.commit()
            pdf_buffer = generate_contract_pdf(
              partner_name,
              company_name,
              contact_details,
            )
            return send_file(
              pdf_buffer,
              mimetype="application/pdf",
              as_attachment=True,
              download_name=f"client_contract_{site.id}_{session_date}.pdf",
            )

          db.commit()
          flash(f"Client profile updated for {site.name}.")

      return redirect(url_for("admin_profiles", tab=active_tab))

    employees = db.query(Employee).order_by(Employee.name.asc()).all()
    sites = db.query(Site).order_by(Site.name.asc()).all()
    generated_any_customer_ids = False
    for site in sites:
      if not (site.profile_tax_id or "").strip():
        _ensure_site_customer_id(db, site)
        generated_any_customer_ids = True
    if generated_any_customer_ids:
      db.commit()
    return render_template_string(
      ADMIN_PROFILES_TEMPLATE,
      active_page="profiles",
      active_tab=active_tab,
      employees=employees,
      sites=sites,
    )
  finally:
    db.close()


@app.route("/leads", methods=["GET", "POST"])
@login_required
def leads_dashboard():
    db = SessionLocal()
    try:
        if request.method == "POST":
            action = (request.form.get("action") or "create").strip().lower()
            if action == "delete":
                lead_id = request.form.get("id")
                if lead_id:
                    lead = db.get(Lead, int(lead_id))
                    if lead:
                        db.delete(lead)
                        db.commit()
            elif action == "update":
                lead_id = request.form.get("id")
                if lead_id:
                    lead = db.get(Lead, int(lead_id))
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
                    lead = Lead(
                        name=name,
                        email=(request.form.get("email") or "").strip() or None,
                        phone=(request.form.get("phone") or "").strip() or None,
                        source=(request.form.get("source") or "").strip() or None,
                        notes=(request.form.get("notes") or "").strip() or None,
                        stage=(request.form.get("stage") or "New Leads"),
                    )
                    if lead.stage not in LEAD_STAGES:
                        lead.stage = "New Leads"
                    db.add(lead)
                    db.commit()
            return redirect(url_for("leads_dashboard"))

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

        leads = query.all()
        grouped = {stage: [] for stage in LEAD_STAGES}
        for lead in leads:
            grouped.setdefault(lead.stage, []).append(lead)

        return render_template_string(
            LEADS_TEMPLATE,
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


@app.route("/leads/stage", methods=["POST"])
@login_required
def leads_stage():
    data = request.get_json(silent=True) or {}
    lead_id = data.get("id")
    stage = data.get("stage")
    if not lead_id or stage not in LEAD_STAGES:
        return jsonify({"error": "Invalid request"}), 400
    db = SessionLocal()
    try:
        lead = db.get(Lead, int(lead_id))
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        lead.stage = stage
        db.commit()
        return jsonify({"status": "ok"})
    finally:
        db.close()


@app.route("/schedule/pdf")
@login_required
def schedule_pdf():
    if not REPORTLAB_AVAILABLE:
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
    week_days = _get_day_range(ref_date, weeks=weeks)

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


@app.route("/reports/hours.pdf")
@login_required
def hours_pdf():
  if not REPORTLAB_AVAILABLE:
    return jsonify({"error": "reportlab not installed"}), 503

  start_str = request.args.get("start_date")
  end_str = request.args.get("end_date")
  employee_id = request.args.get("employee_id", type=int)

  today = date.today()
  if start_str:
    try:
      start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    except ValueError:
      return jsonify({"error": "Invalid start_date"}), 400
  else:
    start_date = today - timedelta(days=today.weekday())

  if end_str:
    try:
      end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
      return jsonify({"error": "Invalid end_date"}), 400
  else:
    end_date = start_date + timedelta(days=6)

  if end_date < start_date:
    start_date, end_date = end_date, start_date

  db = SessionLocal()
  try:
    report_rows = _collect_hours_report(db, start_date, end_date, employee_id=employee_id)
    if employee_id and not report_rows:
      return jsonify({"error": "Employee not found"}), 404
    pdf_buffer = _generate_hours_pdf(start_date, end_date, report_rows)
  finally:
    db.close()

  filename = f"hours_{start_date.isoformat()}_{end_date.isoformat()}"
  if employee_id:
    filename += f"_employee_{employee_id}"
  filename += ".pdf"

  return send_file(
    pdf_buffer,
    mimetype="application/pdf",
    as_attachment=True,
    download_name=filename,
  )


@app.route("/", methods=["GET"])
@login_required
def home():
  return redirect(url_for("admin_dashboard"))


@app.route("/crawler", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template_string(
            HTML_TEMPLATE,
            gpt_enabled=bool(openai_client),
            active_page="crawler",
        )

    if not REPORTLAB_AVAILABLE:
        return (
            jsonify({"error": "reportlab not installed; cannot generate PDF output."}),
            503,
        )

    start_url = (request.form.get("start_url") or "").strip()
    if not start_url:
        return jsonify({"error": "Missing start URL"}), 400

    try:
        max_pages = int(request.form.get("max_pages", "100"))
    except (TypeError, ValueError):
        max_pages = 100
    max_pages = max(1, min(max_pages, 200))

    render_js = bool(request.form.get("render_js"))

    data = crawl(start_url, max_pages=max_pages, render_js=render_js)

    pdf_buffer = _generate_contacts_pdf(data)
    filename = f"putzelf_contacts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/gpt", methods=["POST"])
@login_required
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
        prompt = (data.get("prompt") or "").strip()
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


# --- Invoice functionality --------------------------------------------------

def _format_invoice_number(invoice_number: str | None) -> str:
  """Return invoice number for display."""
  value = (invoice_number or "").strip()
  if not value:
    return ""
  return value


def _generate_invoice_number(session_obj) -> str:
  """Generate continuous invoice numbers: RE-1000, RE-1001, ..."""
  start_number = 1000
  highest = start_number - 1

  existing_numbers = session_obj.query(Invoice.invoice_number).all()
  for (raw_number,) in existing_numbers:
    value = (raw_number or "").strip().upper()
    match = re.fullmatch(r"RE-(\d+)", value)
    if not match:
      continue
    number = int(match.group(1))
    if number > highest:
      highest = number

  next_number = max(start_number, highest + 1)
  candidate = f"RE-{next_number}"

  # Safety check in case of rare race conditions.
  while session_obj.query(Invoice.id).filter(Invoice.invoice_number == candidate).first():
    next_number += 1
    candidate = f"RE-{next_number}"

  return candidate


def _parse_customer_id_sequence(raw_value: str | None) -> int | None:
  """Parse UT customer ID sequence from strings like 'UT- 0001' or 'UT-1'."""
  value = (raw_value or "").strip().upper()
  match = re.fullmatch(r"UT-\s*(\d+)", value)
  if not match:
    return None
  return int(match.group(1))


def _format_customer_id(sequence: int) -> str:
  return f"UT- {sequence:04d}"


def _generate_customer_id(session_obj) -> str:
  """Generate continuous customer IDs: UT- 0001, UT- 0002, ..."""
  start_sequence = 1
  highest = start_sequence - 1

  existing_site_ids = session_obj.query(Site.profile_tax_id).all()
  existing_invoice_ids = session_obj.query(Invoice.site_tax_id).all()

  for (raw_value,) in [*existing_site_ids, *existing_invoice_ids]:
    parsed = _parse_customer_id_sequence(raw_value)
    if parsed is None:
      continue
    if parsed > highest:
      highest = parsed

  next_sequence = max(start_sequence, highest + 1)
  candidate = _format_customer_id(next_sequence)

  while (
    session_obj.query(Site.id).filter(Site.profile_tax_id == candidate).first()
    or session_obj.query(Invoice.id).filter(Invoice.site_tax_id == candidate).first()
  ):
    next_sequence += 1
    candidate = _format_customer_id(next_sequence)

  return candidate


def _ensure_site_customer_id(session_obj, site: Site | None) -> str:
  """Return a site's customer ID, creating one when missing."""
  if not site:
    return ""
  current_value = (site.profile_tax_id or "").strip()
  if current_value:
    return current_value
  generated = _generate_customer_id(session_obj)
  site.profile_tax_id = generated
  return generated


def _previous_month_range(reference_day: date | None = None) -> tuple[date, date]:
  """Return first/last day of previous month."""
  ref = reference_day or date.today()
  first_of_current = date(ref.year, ref.month, 1)
  previous_month_last = first_of_current - timedelta(days=1)
  previous_month_first = date(previous_month_last.year, previous_month_last.month, 1)
  return previous_month_first, previous_month_last


def _auto_generate_monthly_invoices(
  session_obj,
  billing_month: str | None = None,
  tax_rate_percent: float = 20.0,
  days_until_due: int = 30,
) -> dict[str, int | str]:
  """Generate one draft invoice per site for the target month (idempotent by site+month)."""
  if billing_month:
    month_range = _month_range(billing_month)
    if not month_range:
      raise ValueError("Invalid billing month format. Use YYYY-MM.")
    month_start, month_end = month_range
  else:
    month_start, month_end = _previous_month_range()

  month_key = month_start.strftime("%Y-%m")
  created_count = 0
  skipped_existing = 0
  skipped_zero_hours = 0

  sites = session_obj.query(Site).order_by(Site.name.asc()).all()
  for site in sites:
    existing = (
      session_obj.query(Invoice.id)
      .filter(Invoice.site_id == site.id, Invoice.billing_month == month_key)
      .first()
    )
    if existing:
      skipped_existing += 1
      continue

    total_hours = _calculate_site_hours_for_range(session_obj, site.id, month_start, month_end)
    if total_hours <= 0:
      skipped_zero_hours += 1
      continue

    hourly_rate = site.hourly_rate or site.profile_default_hourly_rate or 50.0
    subtotal = total_hours * hourly_rate
    tax_decimal = (tax_rate_percent or 0.0) / 100
    tax_amount = subtotal * tax_decimal
    total_amount = subtotal + tax_amount

    invoice = Invoice(
      invoice_number=_generate_invoice_number(session_obj),
      site_id=site.id,
      site_company_name=((site.profile_company_name or "").strip() or (site.name or "").strip()),
      site_contact_name=((site.profile_contact_name or "").strip() or (site.contact_name or "").strip()),
      site_contact_email=((site.profile_contact_email or "").strip() or (site.contact_email or "").strip()),
      site_phone=(site.profile_phone or "").strip(),
      site_billing_address=((site.profile_billing_address or "").strip() or (site.address or "").strip()),
      site_tax_id=_ensure_site_customer_id(session_obj, site),
      hourly_rate=hourly_rate,
      tax_rate=tax_decimal,
      total_hours=total_hours,
      subtotal=subtotal,
      tax_amount=tax_amount,
      total_amount=total_amount,
      due_date=datetime.utcnow() + timedelta(days=days_until_due),
      billing_month=month_key,
      status="draft",
      notes=f"Auto-generated for billing month {month_key}",
    )
    session_obj.add(invoice)
    created_count += 1

  session_obj.commit()
  return {
    "month": month_key,
    "created": created_count,
    "skipped_existing": skipped_existing,
    "skipped_zero_hours": skipped_zero_hours,
  }

def generate_invoice_pdf(invoice: Invoice) -> io.BytesIO:
    """Generate a professional PDF invoice matching German invoice format."""
    if not REPORTLAB_AVAILABLE:
        raise ValueError("reportlab is required for PDF generation")
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles matching the invoice design
    sender_style = ParagraphStyle(
        'SenderStyle',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        leading=9
    )
    
    address_style = ParagraphStyle(
        'AddressStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#000000')
    )
    
    invoice_header_style = ParagraphStyle(
      'InvoiceHeader',
      parent=styles['Normal'],
      fontSize=8,
      leading=10,
      textColor=colors.HexColor('#666666'),
      alignment=2  # Right align
    )

    invoice_header_label_style = ParagraphStyle(
      'InvoiceHeaderLabel',
      parent=styles['Normal'],
      fontSize=8,
      leading=10,
      textColor=colors.HexColor('#666666'),
      alignment=0
    )

    invoice_header_value_style = ParagraphStyle(
      'InvoiceHeaderValue',
      parent=styles['Normal'],
      fontSize=8,
      leading=10,
      textColor=colors.HexColor('#000000'),
      alignment=2
    )
    
    invoice_number_style = ParagraphStyle(
        'InvoiceNumber',
        parent=styles['Normal'],
        fontSize=16,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#000000'),
        spaceAfter=30
    )
    
    greeting_style = ParagraphStyle(
        'GreetingStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#000000')
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#000000')
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#666666')
    )
    
    # Content
    elements = []
    
    # Top section with sender info and invoice details
    sender_text = "Staffconnecting • Simmeringer Hauptstraße 24 - 1110 Wien"
    # Use current date for invoice and delivery date
    current_date = datetime.now().strftime("%d.%m.%Y")
    invoice_date = current_date
    delivery_date = current_date
    
    # Customer number from profile-generated customer ID
    customer_number = (
      (invoice.site_tax_id or "").strip()
      or ((invoice.site.profile_tax_id or "").strip() if invoice.site else "")
      or (str(invoice.site_id) if invoice.site_id else "")
    )

    # Client profile for recipient block
    recipient_name = (
      (invoice.site_contact_name or "").strip()
      or (invoice.site_company_name or "").strip()
      or (invoice.site.name if invoice.site else "")
      or ""
    )
    recipient_contact_line = (invoice.site_contact_name or "").strip()
    recipient_address_raw = (
      (invoice.site_billing_address or "").strip()
      or (invoice.site.address if invoice.site and invoice.site.address else "").strip()
    )
    recipient_address_lines: list[str] = []
    if recipient_address_raw:
      if "\n" in recipient_address_raw:
        recipient_address_lines = [line.strip() for line in recipient_address_raw.splitlines() if line.strip()]
      else:
        recipient_address_lines = [part.strip() for part in recipient_address_raw.split(",") if part.strip()]

    recipient_extra_lines: list[str] = []
    if recipient_contact_line and recipient_contact_line != recipient_name:
      recipient_extra_lines.append(recipient_contact_line)
    
    # Logo path (drawn on canvas to avoid layout shifts)
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'stafflogo.png')
    logo_flowable = None
    if os.path.exists(logo_path):
      logo_flowable = Image(logo_path, width=1.6 * inch, height=0.4 * inch)
      logo_flowable.hAlign = "LEFT"
    
    # Create header table with sender and invoice info
    right_details_data = [
      [Paragraph('Rechnungs-Nr.', invoice_header_label_style), Paragraph(_format_invoice_number(invoice.invoice_number), invoice_header_value_style)],
      [Paragraph('Rechnungsdatum', invoice_header_label_style), Paragraph(invoice_date, invoice_header_value_style)],
      [Paragraph('Lieferdatum', invoice_header_label_style), Paragraph(delivery_date, invoice_header_value_style)],
      [Paragraph('Ihre Kundennummer', invoice_header_label_style), Paragraph(customer_number, invoice_header_value_style)],
      [Paragraph('Ihr Ansprechpartner', invoice_header_label_style), Paragraph('Sebastijan Kerculj', invoice_header_value_style)],
    ]
    right_details_table = Table(right_details_data, colWidths=[1.6*inch, 1.2*inch])
    right_details_table.setStyle(TableStyle([
      ('ALIGN', (0, 0), (0, -1), 'LEFT'),
      ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('TOPPADDING', (0, 0), (-1, -1), 1),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    left_header_cell = []
    if logo_flowable:
      left_header_cell.extend([logo_flowable, Spacer(1, 0.08 * inch)])
    left_header_cell.append(Paragraph(sender_text, sender_style))

    header_data = [
      [
        left_header_cell,
        right_details_table
      ],
      [
        Paragraph(f'<font size=10>{recipient_name}</font>', address_style),
        ''
      ],
      [
        Paragraph(f'<font size=10>{"<br/>".join(recipient_address_lines) if recipient_address_lines else ""}</font>', address_style),
        ''
      ],
      [
        Paragraph(f'<font size=10>{"<br/>".join(recipient_extra_lines) if recipient_extra_lines else ""}</font>', address_style),
        ''
      ],
    ]

    header_table = Table(header_data, colWidths=[3.6*inch, 2.9*inch])
    header_table.setStyle(TableStyle([
      ('ALIGN', (0, 0), (0, -1), 'LEFT'),
      ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
      ('VALIGN', (0, 0), (-1, -1), 'TOP'),
      ('TOPPADDING', (0, 0), (-1, -1), 2),
      ('TOPPADDING', (1, 0), (1, 0), 7),
      ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Invoice title
    elements.append(Paragraph(f'Rechnung Nr. {_format_invoice_number(invoice.invoice_number)}', invoice_number_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Greeting
    elements.append(Paragraph('Sehr geehrte Damen und Herren,', greeting_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Intro text
    intro_text = "vielen Dank für Ihren Auftrag und das damit verbundene Vertrauen!<br/>Hiermit stelle ich Ihnen die folgenden Leistungen in Rechnung."
    elements.append(Paragraph(intro_text, greeting_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Calculate totals (no discount shown)
    unit_price = invoice.hourly_rate
    quantity = invoice.total_hours
    discount_rate = 0.0
    original_total = unit_price * quantity
    discount_amount = original_total * discount_rate
    discounted_total = original_total - discount_amount
    
    # Items table
    table_data = [
        [
            Paragraph('<b>Pos.</b>', table_header_style),
            Paragraph('<b>Beschreibung</b>', table_header_style),
            Paragraph('<b>Menge</b>', table_header_style),
            Paragraph('<b>Einzelpreis</b>', table_header_style),
            Paragraph('<b>Gesamtpreis</b>', table_header_style)
        ],
        [
            '1.',
            'Reinigungsservice',
            f'{quantity:.2f}',
            f'{unit_price:.2f} EUR',
            f'{original_total:.2f} EUR'
        ]
    ]
    
    # No discount row
    
    invoice_table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.5*inch])
    invoice_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (-1, 0), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        # Data rows
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        # Grid
        ('GRID', (0, 0), (-1, 0), 0.5, colors.HexColor('#cccccc')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cccccc')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Totals section
    net_total = invoice.subtotal if invoice.subtotal else discounted_total
    tax_amount = invoice.tax_amount if invoice.tax_amount else 0
    tax_rate_percent = invoice.tax_rate * 100 if invoice.tax_rate else 20
    gross_total = invoice.total_amount if invoice.total_amount else (net_total + tax_amount)
    
    totals_data = [
        ['', '', '', 'Gesamtbetrag netto', f'{net_total:.2f} EUR'],
        ['', '', '', f'zzgl. Umsatzsteuer {tax_rate_percent:.0f}%', f'{tax_amount:.2f} EUR'],
        ['', '', '', 'Gesamtbetrag brutto', f'{gross_total:.2f} EUR']
    ]
    
    totals_table = Table(totals_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (4, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        # Bold the last row (gross total)
        ('FONTNAME', (3, 2), (4, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 2), (4, 2), 10),
        ('TOPPADDING', (0, 2), (-1, 2), 6),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 6),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Payment terms
    due_days = 31
    if invoice.due_date:
        due_days = (invoice.due_date - invoice.issued_date).days if invoice.issued_date else 31
    
    payment_text = f'Zahlungsbedingungen: Zahlung innerhalb von {due_days} Tagen ab Rechnungseingang ohne Abzüge.'
    elements.append(Paragraph(payment_text, greeting_style))
    elements.append(Spacer(1, 0.1*inch))
    
    bank_info_text = f'Bitte überweisen Sie den Rechnungsbetrag unter Angabe der Rechnungsnummer auf das unten angegebene Konto.'
    elements.append(Paragraph(bank_info_text, greeting_style))
    elements.append(Spacer(1, 0.05*inch))
    
    # Due date
    due_date_str = invoice.due_date.strftime("%d.%m.%Y") if invoice.due_date else (datetime.now() + timedelta(days=31)).strftime("%d.%m.%Y")
    due_date_text = f'Der Rechnungsbetrag ist bis zum {due_date_str} fällig.'
    elements.append(Paragraph(due_date_text, greeting_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Closing
    elements.append(Paragraph('Mit freundlichen Grüßen<br/>Sebastijan Kerculj', greeting_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Build PDF
    def _draw_header_footer(canvas_obj, doc_obj):
      canvas_obj.saveState()
      canvas_obj.setFont('Helvetica', 6.6)
      canvas_obj.setFillColor(colors.HexColor('#666666'))

      col_1 = [
        "Sebastijan Aleksandar Kerculj",
        "Staffconnecting",
        "Simmeringer Hauptstraße 24",
        "1110 Wien",
        "Österreich",
      ]

      col_2 = [
        "Tel. 06766300167",
        "E-Mail s.kerculj@staffconnecting.at",
      ]

      col_3 = [
        "Amtsgericht Wien",
        "USt.-ID ATU78448967",
        "Steuer-Nr. 04 544/9573",
        "Geschäftsführung Sebastijan Aleksandar",
        "Kerculj",
      ]

      col_4 = [
        "Bank UniCredit Bank Austria AG",
        "Konto 51488162831",
        "BLZ 12000",
        "IBAN AT8312000051488162831",
        "BIC BKAUATWWXXX",
      ]

      line_height = 8
      top_y = doc_obj.bottomMargin + 32

      col_1_x = doc_obj.leftMargin
      col_2_x = doc_obj.leftMargin + 1.85 * inch
      col_3_x = doc_obj.leftMargin + 3.70 * inch
      col_4_x = doc_obj.leftMargin + 5.45 * inch

      def _draw_column(lines: list[str], x_pos: float) -> None:
        y = top_y
        for line in lines:
          canvas_obj.drawString(x_pos, y, line)
          y -= line_height

      _draw_column(col_1, col_1_x)
      _draw_column(col_2, col_2_x)
      _draw_column(col_3, col_3_x)
      _draw_column(col_4, col_4_x)

      canvas_obj.restoreState()

    doc.build(elements, onFirstPage=_draw_header_footer)
    pdf_buffer.seek(0)
    return pdf_buffer


def send_invoice_email(invoice: Invoice, pdf_buffer: io.BytesIO) -> Tuple[bool, str]:
    """Send invoice PDF via email. Returns (success, message)."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email import encoders
        
        smtp_server = (os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        smtp_secure_raw = (os.getenv("SMTP_SECURE") or "").strip().lower()
        if smtp_secure_raw:
            smtp_use_ssl = smtp_secure_raw in {"1", "true", "yes", "on"}
            smtp_use_tls = not smtp_use_ssl
        else:
            smtp_use_tls = (os.getenv("SMTP_USE_TLS", "true") or "").strip().lower() in {"1", "true", "yes", "on"}
            smtp_use_ssl = (os.getenv("SMTP_USE_SSL", "false") or "").strip().lower() in {"1", "true", "yes", "on"}

        sender_email = (
            os.getenv("SENDER_EMAIL")
            or os.getenv("SMTP_FROM_EMAIL")
            or os.getenv("SMTP_FROM")
            or ""
        ).strip()
        sender_name = (os.getenv("SENDER_NAME") or os.getenv("SMTP_FROM_NAME") or "").strip()
        smtp_username = (os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or sender_email).strip()
        smtp_password = (
            os.getenv("SMTP_PASSWORD")
            or os.getenv("SMTP_PASS")
            or os.getenv("SENDER_PASSWORD")
            or ""
        ).strip()

        if not sender_email or not smtp_password:
            msg = "Email configuration missing. Set sender email and SMTP password."
            app.logger.warning(msg)
            return False, msg
        
        recipient_email = (
          (invoice.site_contact_email or "").strip()
          or ((invoice.site.profile_contact_email or "").strip() if invoice.site else "")
        )
        if not recipient_email:
            msg = f"No recipient email set for invoice {invoice.invoice_number}."
            app.logger.warning(msg)
            return False, msg
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f'Invoice {invoice.invoice_number} - {(invoice.site_company_name or invoice.site.name)}'
        
        # Body
        body = f"""
Dear {invoice.site_contact_name or invoice.site_company_name or 'Customer'},

Please find attached your invoice {invoice.invoice_number}.

Invoice Details:
- Site: {invoice.site.name}
- Company: {invoice.site_company_name or invoice.site.name}
- Hours Worked: {invoice.total_hours}
- Hourly Rate: ${invoice.hourly_rate:.2f}
- Total Amount: ${invoice.total_amount:.2f}
- Due Date: {invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else "Upon receipt"}
{f"- Customer ID: {invoice.site_tax_id}" if invoice.site_tax_id else ""}

{f"Additional Notes: {invoice.notes}" if invoice.notes else ""}

Thank you for your business!

Best regards,
Your Company
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(pdf_buffer.getvalue())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename= invoice_{invoice.invoice_number}.pdf')
        msg.attach(attachment)
        
        # Send email
        if smtp_use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)

        with server:
            if smtp_use_tls and not smtp_use_ssl:
                server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        app.logger.info(f"Invoice {invoice.invoice_number} sent to {recipient_email}")
        return True, f"Invoice {invoice.invoice_number} sent to {recipient_email}"
        
    except Exception as e:
        app.logger.error(f"Failed to send invoice email: {e}")
        return False, str(e)


def _resolve_contract_template_path() -> str | None:
  configured = (os.getenv("CONTRACT_TEMPLATE_PATH") or "").strip()
  if configured:
    candidate = configured if os.path.isabs(configured) else os.path.join(APP_ROOT, configured)
    if os.path.exists(candidate):
      return candidate

  candidates = [
    os.path.join(APP_ROOT, "uploads", "contract_template.pdf"),
    os.path.join(APP_ROOT, "static", "uploads", "contract_template.pdf"),
  ]
  for candidate in candidates:
    if os.path.exists(candidate):
      return candidate
  return None


def generate_contract_pdf(
  partner_name: str,
  company_name: str,
  contact_details: str,
  template_pdf_bytes: bytes | None = None,
) -> io.BytesIO:
    """Generate a client contract PDF with editable form inputs applied."""
    if not REPORTLAB_AVAILABLE:
        raise ValueError("reportlab is required for PDF generation")

    partner_name = (partner_name or "").strip()
    company_name = (company_name or "").strip()
    contact_details = (contact_details or "").strip()

    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=A4)
    _, page_height = A4

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, page_height - 70, "Client Contract")

    c.setFont("Helvetica", 10)
    c.drawString(50, page_height - 105, f"Name des partners: {partner_name}")
    c.drawString(50, page_height - 125, f"Firma: {company_name}")
    c.drawString(50, page_height - 145, f"Tel./ Fax / E-Mail: {contact_details}")

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
      50,
      35,
      f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    )
    c.save()
    overlay_buffer.seek(0)

    template_reader = None
    if template_pdf_bytes and PYPDF_AVAILABLE:
      template_reader = PdfReader(io.BytesIO(template_pdf_bytes))
    elif PYPDF_AVAILABLE:
      template_path = _resolve_contract_template_path()
      if template_path:
        template_reader = PdfReader(template_path)

    def _contains_any(value: str, tokens: list[str]) -> bool:
      lowered = (value or "").lower()
      return any(token in lowered for token in tokens)

    # Preferred path: update true AcroForm fields (fillable PDF)
    if template_reader and PYPDF_AVAILABLE:
      fields = template_reader.get_fields() or {}
      field_names = list(fields.keys())

      field_value_map: dict[str, str] = {}

      for fname in field_names:
        # Raw internal field name from the PDF
        raw = (fname or "").strip()
        fl = raw.lower()

        # 1) Match common exact names first (your typical German labels)
        if fl in {
          "name des partners",
          "name_des_partners",
          "name_des partners",
        }:
          field_value_map[fname] = partner_name
          continue
        elif fl in {
          "firma",
          "firma:",
          "firma_name",
          "company",
          "company_name",
        }:
          field_value_map[fname] = company_name
          continue
        elif fl in {
          "tel./ fax / e-mail",
          "tel./ fax / e-mail:",
          "kontakt",
          "kontakt_daten",
          "contact_details",
        }:
          field_value_map[fname] = contact_details
          continue

        # 2) Fallback: heuristic matching based on substrings
        if _contains_any(fl, ["partner", "ansprech", "name des partners"]) and "firma" not in fl:
          field_value_map[fname] = partner_name
        elif _contains_any(fl, ["firma", "company"]):
          field_value_map[fname] = company_name
        elif _contains_any(fl, ["tel", "fax", "mail", "email", "e-mail", "kontakt", "contact"]):
          field_value_map[fname] = contact_details

      if field_value_map:
        writer = PdfWriter()
        writer.clone_document_from_reader(template_reader)
        for page in writer.pages:
          writer.update_page_form_field_values(page, field_value_map, auto_regenerate=False)

        # Improve compatibility with viewers that rely on appearances
        if NameObject is not None and BooleanObject is not None and "/AcroForm" in writer._root_object:
          writer._root_object["/AcroForm"].update(
            {NameObject("/NeedAppearances"): BooleanObject(True)}
          )

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out

    if template_reader and PYPDF_AVAILABLE:
      overlay_reader = PdfReader(overlay_buffer)
      writer = PdfWriter()

      if template_reader.pages:
        target_index = 2 if len(template_reader.pages) >= 3 else 0
        for idx, page in enumerate(template_reader.pages):
          if idx == target_index:
            page.merge_page(overlay_reader.pages[0])
          writer.add_page(page)
      else:
        for page in overlay_reader.pages:
          writer.add_page(page)

      final_pdf = io.BytesIO()
      writer.write(final_pdf)
      final_pdf.seek(0)
      return final_pdf

    # Fallback: standalone generated PDF only
    return overlay_buffer


# --- Invoice Routes --------------------------------------------------------

@app.route("/admin/contracts", methods=["GET", "POST"])
@login_required
def admin_contract_builder():
  if request.method == "POST":
    partner_name = (request.form.get("partner_name") or "").strip()
    company_name = (request.form.get("company_name") or "").strip()
    contact_details = (request.form.get("contact_details") or "").strip()
    contract_pdf_file = request.files.get("contract_pdf")
    template_path = _resolve_contract_template_path()

    if not partner_name or not company_name or not contact_details:
      flash("Please fill all contract fields.", "warning")
      return render_template_string(
        CONTRACT_BUILDER_TEMPLATE,
        partner_name=partner_name,
        company_name=company_name,
        contact_details=contact_details,
      )

    uploaded_pdf_bytes = None
    if contract_pdf_file and (contract_pdf_file.filename or "").strip():
      if not (contract_pdf_file.filename or "").lower().endswith(".pdf"):
        flash("Please upload a valid PDF contract file.", "warning")
        return render_template_string(
          CONTRACT_BUILDER_TEMPLATE,
          partner_name=partner_name,
          company_name=company_name,
          contact_details=contact_details,
        )
      uploaded_pdf_bytes = contract_pdf_file.read()
      if not uploaded_pdf_bytes:
        flash("Uploaded PDF is empty.", "warning")
        return render_template_string(
          CONTRACT_BUILDER_TEMPLATE,
          partner_name=partner_name,
          company_name=company_name,
          contact_details=contact_details,
        )
    elif not template_path:
      flash("Upload a contract PDF or place a template at uploads/contract_template.pdf or static/uploads/contract_template.pdf.", "warning")
      return render_template_string(
        CONTRACT_BUILDER_TEMPLATE,
        partner_name=partner_name,
        company_name=company_name,
        contact_details=contact_details,
      )

    if (uploaded_pdf_bytes or template_path) and not PYPDF_AVAILABLE:
      flash("PDF template merge is unavailable on this server. Install pypdf (or PyPDF2) in production.", "warning")
      return render_template_string(
        CONTRACT_BUILDER_TEMPLATE,
        partner_name=partner_name,
        company_name=company_name,
        contact_details=contact_details,
      )

    pdf_buffer = generate_contract_pdf(
      partner_name,
      company_name,
      contact_details,
      template_pdf_bytes=uploaded_pdf_bytes,
    )
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return send_file(
      pdf_buffer,
      mimetype="application/pdf",
      as_attachment=True,
      download_name=f"client_contract_{timestamp}.pdf",
    )

    return render_template_string(CONTRACT_BUILDER_TEMPLATE)

@app.route("/admin/invoices/generate-monthly", methods=["POST"])
@login_required
def admin_generate_monthly_invoices():
  """Generate monthly invoices for previous month (or provided YYYY-MM month)."""
  session_obj = SessionLocal()
  try:
    month = (request.form.get("month") or "").strip()
    tax_rate = request.form.get("tax_rate", type=float, default=20.0)
    due_days = request.form.get("days_until_due", type=int, default=30)

    result = _auto_generate_monthly_invoices(
      session_obj,
      billing_month=month or None,
      tax_rate_percent=tax_rate or 20.0,
      days_until_due=due_days or 30,
    )
    flash(
      (
        f"Monthly invoices generated for {result['month']}: "
        f"created {result['created']}, "
        f"skipped existing {result['skipped_existing']}, "
        f"skipped zero-hours {result['skipped_zero_hours']}."
      ),
      "success",
    )
  except ValueError as exc:
    flash(str(exc), "warning")
  finally:
    session_obj.close()

  return redirect(url_for("admin_invoices"))

@app.route("/admin/invoices", methods=["GET"])
@login_required
def admin_invoices():
    """List all invoices."""
    session_obj = SessionLocal()
    try:
        status_filter = (request.args.get("status") or "all").strip().lower()
        created_from_raw = (request.args.get("created_from") or "").strip()
        created_to_raw = (request.args.get("created_to") or "").strip()

        query = session_obj.query(Invoice)

        if status_filter in {"draft", "sent", "paid", "overdue"}:
            query = query.filter(Invoice.status == status_filter)
        else:
            status_filter = "all"

        created_from = None
        if created_from_raw:
            try:
                created_from = datetime.strptime(created_from_raw, "%Y-%m-%d").date()
                query = query.filter(func.date(Invoice.created_at) >= created_from)
            except ValueError:
                created_from_raw = ""
                flash("Invalid 'created from' date filter.", "warning")

        created_to = None
        if created_to_raw:
            try:
                created_to = datetime.strptime(created_to_raw, "%Y-%m-%d").date()
                query = query.filter(func.date(Invoice.created_at) <= created_to)
            except ValueError:
                created_to_raw = ""
                flash("Invalid 'created to' date filter.", "warning")

        invoices = query.order_by(Invoice.created_at.desc()).all()
        return render_template_string(
            INVOICE_LIST_TEMPLATE,
            invoices=invoices,
            status_filter=status_filter,
            created_from=created_from_raw,
            created_to=created_to_raw,
          short_invoice_number=_format_invoice_number,
        )
    finally:
        session_obj.close()


@app.route("/admin/invoices/new", methods=["GET", "POST"])
@login_required
def admin_create_invoice():
    """Create a new invoice."""
    session_obj = SessionLocal()
    try:
        if request.method == "POST":
            site_id = request.form.get("site_id", type=int)
            site_company_name = (request.form.get("site_company_name") or "").strip()
            site_contact_name = (request.form.get("site_contact_name") or "").strip()
            site_contact_email = (request.form.get("site_contact_email") or "").strip()
            site_phone = (request.form.get("site_phone") or "").strip()
            site_billing_address = (request.form.get("site_billing_address") or "").strip()
            site_tax_id = (request.form.get("site_tax_id") or "").strip()
            tax_rate = request.form.get("tax_rate", type=float, default=20.0)
            invoice_month = (request.form.get("invoice_month") or "").strip()
            notes = request.form.get("notes", "")
            days_until_due = request.form.get("days_until_due", type=int, default=30)

            site = session_obj.get(Site, site_id) if site_id else None
            if not site:
                flash("Please select a valid site.", "warning")
                return redirect(url_for("admin_create_invoice"))

            if not site_company_name:
              site_company_name = (
                (site.profile_company_name or "").strip()
                or (site.name or "").strip()
              )
            if not site_contact_name:
              site_contact_name = (
                (site.profile_contact_name or "").strip()
                or (site.contact_name or "").strip()
              )
            if not site_contact_email:
              site_contact_email = (
                (site.profile_contact_email or "").strip()
                or (site.contact_email or "").strip()
              )
            if not site_phone:
              site_phone = (site.profile_phone or "").strip()
            if not site_billing_address:
              site_billing_address = (
                (site.profile_billing_address or "").strip()
                or (site.address or "").strip()
              )
            if not site_tax_id:
              site_tax_id = _ensure_site_customer_id(session_obj, site)

            month_range = _month_range(invoice_month)
            if not month_range:
                flash("Please choose a valid invoice month.", "warning")
                return redirect(url_for("admin_create_invoice"))
            month_start, month_end = month_range
            total_hours = _calculate_site_hours_for_range(
                session_obj,
                site.id,
                month_start,
                month_end,
            )
            hourly_rate = site.hourly_rate or site.profile_default_hourly_rate or 50.0
            
            # Calculate totals
            subtotal = total_hours * hourly_rate
            tax_amount = subtotal * (tax_rate / 100)
            total_amount = subtotal + tax_amount
            
            invoice = Invoice(
              invoice_number=_generate_invoice_number(session_obj),
                site_id=site.id,
                site_company_name=site_company_name,
                site_contact_name=site_contact_name,
                site_contact_email=site_contact_email,
                site_phone=site_phone,
                site_billing_address=site_billing_address,
                site_tax_id=site_tax_id,
                hourly_rate=hourly_rate,
                tax_rate=tax_rate / 100,  # Convert percentage to decimal
                total_hours=total_hours,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                billing_month=month_start.strftime("%Y-%m"),
                due_date=datetime.utcnow() + timedelta(days=days_until_due),
                notes=notes
            )
            
            session_obj.add(invoice)
            session_obj.commit()
            
            flash(f"Invoice {invoice.invoice_number} created successfully!", "success")
            return redirect(url_for("admin_invoices"))
        
        sites = session_obj.query(Site).all()
        generated_any_customer_ids = False
        for site in sites:
          if not (site.profile_tax_id or "").strip():
            _ensure_site_customer_id(session_obj, site)
            generated_any_customer_ids = True
        if generated_any_customer_ids:
          session_obj.commit()
        current_month = datetime.utcnow().strftime("%Y-%m")
        return render_template_string(
            INVOICE_FORM_TEMPLATE,
            sites=sites,
            current_month=current_month,
        )
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>", methods=["GET"])
@login_required
def admin_view_invoice(invoice_id):
    """View invoice details."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404
        
        return render_template_string(
          INVOICE_VIEW_TEMPLATE,
          invoice=invoice,
          short_invoice_number=_format_invoice_number,
        )
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_invoice(invoice_id):
    """Edit invoice details."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404

        if request.method == "POST":
            site_id = request.form.get("site_id", type=int)
            status = (request.form.get("status") or "draft").strip().lower()
            site_company_name = (request.form.get("site_company_name") or "").strip()
            site_contact_name = (request.form.get("site_contact_name") or "").strip()
            site_contact_email = (request.form.get("site_contact_email") or "").strip()
            site_phone = (request.form.get("site_phone") or "").strip()
            site_billing_address = (request.form.get("site_billing_address") or "").strip()
            site_tax_id = (request.form.get("site_tax_id") or "").strip()
            hourly_rate = request.form.get("hourly_rate", type=float)
            total_hours = request.form.get("total_hours", type=float)
            tax_rate_percent = request.form.get("tax_rate", type=float, default=20.0)
            due_date_raw = (request.form.get("due_date") or "").strip()
            paid_at_raw = (request.form.get("paid_at") or "").strip()
            notes = request.form.get("notes", "")

            site = session_obj.get(Site, site_id) if site_id else None
            if not site:
                flash("Please select a valid site.", "warning")
                return redirect(url_for("admin_edit_invoice", invoice_id=invoice_id))

            if not site_company_name:
              site_company_name = (
                (site.profile_company_name or "").strip()
                or (site.name or "").strip()
              )
            if not site_contact_name:
              site_contact_name = (
                (site.profile_contact_name or "").strip()
                or (site.contact_name or "").strip()
              )
            if not site_contact_email:
              site_contact_email = (
                (site.profile_contact_email or "").strip()
                or (site.contact_email or "").strip()
              )
            if not site_phone:
              site_phone = (site.profile_phone or "").strip()
            if not site_billing_address:
              site_billing_address = (
                (site.profile_billing_address or "").strip()
                or (site.address or "").strip()
              )
            if not site_tax_id:
              site_tax_id = _ensure_site_customer_id(session_obj, site)

            if status not in {"draft", "sent", "paid", "overdue"}:
                flash("Invalid status selected.", "warning")
                return redirect(url_for("admin_edit_invoice", invoice_id=invoice_id))

            if hourly_rate is None or total_hours is None:
              flash("Hourly rate and total hours are required.", "warning")
              return redirect(url_for("admin_edit_invoice", invoice_id=invoice_id))

            due_date = None
            if due_date_raw:
                try:
                    due_date = datetime.strptime(due_date_raw, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid due date format.", "warning")
                    return redirect(url_for("admin_edit_invoice", invoice_id=invoice_id))

            paid_at = None
            if paid_at_raw:
                try:
                    paid_at = datetime.strptime(paid_at_raw, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid paid date format.", "warning")
                    return redirect(url_for("admin_edit_invoice", invoice_id=invoice_id))

            subtotal = total_hours * hourly_rate
            tax_rate_decimal = (tax_rate_percent or 20.0) / 100
            tax_amount = subtotal * tax_rate_decimal
            total_amount = subtotal + tax_amount

            invoice.site_id = site.id
            invoice.status = status
            invoice.site_company_name = site_company_name
            invoice.site_contact_name = site_contact_name
            invoice.site_contact_email = site_contact_email
            invoice.site_phone = site_phone
            invoice.site_billing_address = site_billing_address
            invoice.site_tax_id = site_tax_id
            invoice.hourly_rate = hourly_rate
            invoice.total_hours = total_hours
            invoice.tax_rate = tax_rate_decimal
            invoice.subtotal = subtotal
            invoice.tax_amount = tax_amount
            invoice.total_amount = total_amount
            invoice.due_date = due_date
            invoice.notes = notes
            invoice.paid_at = paid_at if status == "paid" else None

            session_obj.commit()
            flash(f"Invoice {invoice.invoice_number} updated successfully.", "success")
            return redirect(url_for("admin_view_invoice", invoice_id=invoice_id))

        sites = session_obj.query(Site).order_by(Site.name.asc()).all()
        return render_template_string(
            INVOICE_EDIT_TEMPLATE,
            invoice=invoice,
            sites=sites,
            short_invoice_number=_format_invoice_number,
        )
    finally:
        session_obj.close()


@app.route("/admin/income-report", methods=["GET"])
@login_required
def admin_income_report():
    """Display monthly income report."""
    session_obj = SessionLocal()
    try:
        monthly_summaries = _get_all_monthly_summaries(
            session_obj,
            start_year=2025,
            start_month=12,
        )
        return render_template_string(
            INCOME_REPORT_TEMPLATE,
            monthly_summaries=monthly_summaries,
        )
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>/pdf", methods=["GET"])
@login_required
def admin_invoice_pdf(invoice_id):
    """Download invoice as PDF."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404
        
        pdf_buffer = generate_invoice_pdf(invoice)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'invoice_{invoice.invoice_number}.pdf'
        )
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>/send-email", methods=["GET"])
@login_required
def admin_send_invoice_email(invoice_id):
    """Send invoice via email."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404
        
        pdf_buffer = generate_invoice_pdf(invoice)
        success, detail = send_invoice_email(invoice, pdf_buffer)
        
        if success:
            invoice.status = "sent"
            session_obj.commit()
            flash(f"Invoice {invoice.invoice_number} sent to {invoice.site_contact_email}", "success")
        else:
          flash(f"Failed to send email: {detail}", "error")
        
        return redirect(url_for("admin_view_invoice", invoice_id=invoice_id))
    finally:
        session_obj.close()

@app.route("/admin/invoices/send-bulk", methods=["POST"])
@login_required
def admin_send_bulk_invoice_emails():
    """Send multiple selected invoices by email."""
    session_obj = SessionLocal()
    try:
        invoice_ids_raw = request.form.getlist("invoice_ids")
        invoice_ids: list[int] = []
        seen: set[int] = set()
        for raw in invoice_ids_raw:
            try:
                invoice_id = int(raw)
            except (TypeError, ValueError):
                continue
            if invoice_id in seen:
                continue
            seen.add(invoice_id)
            invoice_ids.append(invoice_id)

        if not invoice_ids:
            flash("Select at least one invoice to send.", "warning")
            return redirect(url_for("admin_invoices"))

        invoices = (
            session_obj.query(Invoice)
            .options(joinedload(Invoice.site))
            .filter(Invoice.id.in_(invoice_ids))
            .all()
        )

        sent_count = 0
        failed_count = 0
        skipped_count = 0
        failure_examples: list[str] = []

        for invoice in invoices:
            recipient = (invoice.site_contact_email or "").strip()
            if not recipient:
                skipped_count += 1
                continue

            try:
                pdf_buffer = generate_invoice_pdf(invoice)
            except Exception as exc:
                failed_count += 1
                if len(failure_examples) < 3:
                    failure_examples.append(f"{invoice.invoice_number}: PDF error ({exc})")
                continue

            success, detail = send_invoice_email(invoice, pdf_buffer)
            if success:
                if invoice.status != "paid":
                    invoice.status = "sent"
                sent_count += 1
            else:
                failed_count += 1
                if len(failure_examples) < 3:
                    failure_examples.append(f"{invoice.invoice_number}: {detail}")

        session_obj.commit()

        flash(
            f"Bulk email result — sent: {sent_count}, skipped (no email): {skipped_count}, failed: {failed_count}.",
            "success" if failed_count == 0 else "warning",
        )
        if failure_examples:
            flash("; ".join(failure_examples), "warning")

        return redirect(url_for("admin_invoices"))
    finally:
        session_obj.close()

@app.route("/admin/invoices/delete-bulk", methods=["POST"])
@login_required
def admin_delete_bulk_invoices():
    """Delete multiple selected invoices."""
    session_obj = SessionLocal()
    try:
        invoice_ids_raw = request.form.getlist("invoice_ids")
        invoice_ids: list[int] = []
        seen: set[int] = set()
        for raw in invoice_ids_raw:
            try:
                invoice_id = int(raw)
            except (TypeError, ValueError):
                continue
            if invoice_id in seen:
                continue
            seen.add(invoice_id)
            invoice_ids.append(invoice_id)

        if not invoice_ids:
            flash("Select at least one invoice to delete.", "warning")
            return redirect(url_for("admin_invoices"))

        invoices = session_obj.query(Invoice).filter(Invoice.id.in_(invoice_ids)).all()
        if not invoices:
            flash("No matching invoices found to delete.", "warning")
            return redirect(url_for("admin_invoices"))

        deleted_count = 0
        for invoice in invoices:
            session_obj.delete(invoice)
            deleted_count += 1

        session_obj.commit()
        flash(f"Deleted {deleted_count} invoice(s).", "success")
        return redirect(url_for("admin_invoices"))
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>/status", methods=["POST"])
@login_required
def admin_update_invoice_status(invoice_id):
    """Update invoice status (draft, sent, paid)."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404

        new_status = (request.form.get("status") or "").strip().lower()
        allowed_statuses = {"draft", "sent", "paid"}
        if new_status not in allowed_statuses:
            flash("Invalid invoice status.", "warning")
            return redirect(url_for("admin_view_invoice", invoice_id=invoice_id))

        invoice.status = new_status
        if new_status == "paid":
            invoice.paid_at = datetime.utcnow()
        else:
            invoice.paid_at = None

        session_obj.commit()
        flash(f"Invoice {invoice.invoice_number} marked as {new_status}.", "success")
        return redirect(url_for("admin_view_invoice", invoice_id=invoice_id))
    finally:
        session_obj.close()


@app.route("/admin/invoices/<int:invoice_id>/delete", methods=["GET"])
@login_required
def admin_delete_invoice(invoice_id):
    """Delete an invoice."""
    session_obj = SessionLocal()
    try:
        invoice = session_obj.query(Invoice).get(invoice_id)
        if invoice:
            invoice_number = invoice.invoice_number
            session_obj.delete(invoice)
            session_obj.commit()
            flash(f"Invoice {invoice_number} deleted", "success")
        return redirect(url_for("admin_invoices"))
    finally:
        session_obj.close()


def _run_monthly_invoice_generation_from_cli() -> int:
    """CLI entrypoint to support cron-based monthly invoice generation."""
    month = None
    tax_rate = 20.0
    due_days = 30
    for arg in sys.argv[1:]:
        if arg.startswith("--month="):
            month = arg.split("=", 1)[1].strip()
        elif arg.startswith("--tax-rate="):
            try:
                tax_rate = float(arg.split("=", 1)[1].strip())
            except ValueError:
                print("Invalid --tax-rate value")
                return 1
        elif arg.startswith("--due-days="):
            try:
                due_days = int(arg.split("=", 1)[1].strip())
            except ValueError:
                print("Invalid --due-days value")
                return 1

    session_obj = SessionLocal()
    try:
        result = _auto_generate_monthly_invoices(
            session_obj,
            billing_month=month,
            tax_rate_percent=tax_rate,
            days_until_due=due_days,
        )
        print(
            f"Generated month {result['month']}: "
            f"created={result['created']}, "
            f"skipped_existing={result['skipped_existing']}, "
            f"skipped_zero_hours={result['skipped_zero_hours']}"
        )
        return 0
    except ValueError as exc:
        print(str(exc))
        return 1
    finally:
        session_obj.close()


if __name__ == "__main__":
    if "--generate-monthly-invoices" in sys.argv:
      raise SystemExit(_run_monthly_invoice_generation_from_cli())
    app.run(host="0.0.0.0", port=5000, debug=True)