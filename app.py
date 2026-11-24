import math
import re
import io
import csv
import json
import html
import logging
import os
import sys
import secrets
from collections import deque
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from functools import wraps
from typing import Any, Tuple
from urllib.parse import urljoin, urldefrag, urlparse, quote_plus, urlencode
from dotenv import load_dotenv

_APP_DOTENV_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=_APP_DOTENV_PATH, override=False)

import requests
from bs4 import BeautifulSoup
from flask import (
  Flask,
  request,
  render_template,
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
  UniqueConstraint,
  event,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session, joinedload, Session as SQLAlchemySession
from sqlalchemy import inspect as sqlalchemy_inspect

ADMIN_TEMPLATE = """
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Elf's Plan — {{ i18n.financial_dashboard }}</title>
  <meta name="theme-color" content="#ffffff" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/logo.png">
  <link rel="manifest" href="/static/admin-manifest.json">
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
    .summary-meter { width: 100%; height: 0.55rem; border-radius: 999px; background:#e2e8f0; overflow:hidden; }
    .summary-meter-fill { height:100%; background-image:linear-gradient(135deg,#0f766e 0%,#14b8a6 50%,#0ea5e9 100%); border-radius:999px; }
    .chart-card { border-radius:1rem; border:1px solid #e2e8f0; background:#ffffff; padding:1.4rem; min-height:420px; box-shadow:0 18px 32px rgba(15,23,42,0.08); }
    .chart-header { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:flex-start; gap:1rem; margin-bottom:1.5rem; }
    .chart-summary-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1rem; margin-bottom:1.5rem; }
    .chart-summary-item { border-radius:0.85rem; border:1px solid #e2e8f0; background:#f8fafc; padding:1rem; }
    .chart-summary-item .metric-label { margin-bottom:0.35rem; color:#475569; }
    .chart-summary-item .metric-value { font-size:1.35rem; font-weight:700; color:#0f172a; }
    .chart-wrapper { position:relative; min-height:320px; }
    canvas { width:100% !important; }
    .chart-pill { display:inline-flex; align-items:center; gap:0.35rem; border-radius:999px; padding:0.35rem 0.8rem; background:#eef2ff; color:#0f172a; font-size:0.85rem; }
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
    .monthly-breakdown { max-height: calc(100vh - 420px); overflow:auto; padding-right:0.5rem; }
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
    /* Admin overview refresh */
    .admin-dashboard { --dash-ink:#17233b; --dash-muted:#72809a; --dash-blue:#356ae6; --dash-canvas:#f4f6fb; min-height:100vh; background:var(--dash-canvas); color:var(--dash-ink); font-size:15px; }
    .admin-shell { grid-template-columns:252px minmax(0,1fr); min-height:100vh; background:var(--dash-canvas); transition:grid-template-columns .22s ease; }
    .admin-sidebar { position:sticky; top:0; height:100vh; min-width:0; padding:1.15rem .9rem; gap:.45rem; color:#f7f9ff; background:linear-gradient(180deg,#17233b 0%,#202f51 100%); border-right:1px solid #273754; box-shadow:8px 0 28px rgba(16,29,53,.08); }
    .admin-brand { display:flex; align-items:center; gap:.75rem; min-height:58px; padding:.25rem .4rem .8rem; margin-bottom:.45rem; border-bottom:1px solid rgba(226,232,240,.14); color:#fff; text-decoration:none; }
    .admin-brand-mark { width:42px; height:42px; display:grid; place-items:center; flex:none; overflow:hidden; border-radius:13px; background:#fff; box-shadow:0 5px 14px rgba(7,16,36,.2); }
    .admin-brand-mark img { width:100%; height:100%; object-fit:contain; }
    .admin-brand-text { min-width:0; display:grid; line-height:1.2; }
    .admin-brand-text strong { color:#fff; font-size:.98rem; letter-spacing:-.02em; }
    .admin-brand-text small { margin-top:.25rem; color:#aebbd2; font-size:.72rem; }
    .admin-sidebar .sidebar-section-title { padding:.75rem .7rem .35rem; color:#9eacc5; font-size:.67rem; font-weight:700; letter-spacing:.12em; }
    .admin-sidebar .nav-pill { min-height:42px; padding:.57rem .7rem; border-radius:10px; color:#d4dced; font-size:.88rem; font-weight:550; }
    .admin-sidebar .nav-pill .nav-icon { width:1.25rem; flex:none; color:#aebbd2; text-align:center; font-size:1rem; }
    .admin-sidebar .nav-pill.active { color:#fff; background:linear-gradient(100deg,rgba(70,119,235,.33),rgba(70,119,235,.13)); box-shadow:inset 3px 0 #78a2ff; }
    .admin-sidebar .nav-pill.active .nav-icon { color:#a9c4ff; }
    .admin-sidebar .nav-pill:hover { color:#fff; background:rgba(226,232,240,.09); box-shadow:none; }
    .admin-sidebar .nav-pill-logout { margin-top:.2rem; border:1px solid rgba(226,232,240,.15); background:rgba(226,232,240,.06); color:#e4eaf5; }
    .admin-sidebar .nav-pill-logout .nav-icon { color:#e4eaf5; }
    .admin-sidebar-footer { margin-top:auto; padding:.8rem .55rem .15rem; border-top:1px solid rgba(226,232,240,.14); color:#9eacc5; font-size:.73rem; }
    .admin-sidebar-collapse { width:32px; height:32px; display:grid; place-items:center; align-self:flex-end; margin:0 .2rem .1rem; border:1px solid rgba(226,232,240,.2); border-radius:9px; color:#d8e2f3; background:rgba(226,232,240,.07); }
    .admin-sidebar-collapse:hover { color:#fff; background:rgba(226,232,240,.15); }
    .admin-main { min-width:0; padding:1.45rem clamp(1rem,2.2vw,2.25rem) 2.25rem; background:var(--dash-canvas); }
    .admin-topbar { display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:1.55rem; }
    .admin-mobile-menu { display:none; }
    .admin-heading { min-width:0; }
    .admin-heading-eyebrow { display:flex; align-items:center; gap:.45rem; margin-bottom:.35rem; color:var(--dash-muted); font-size:.74rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }
    .admin-heading-eyebrow i { color:var(--dash-blue); }
    .admin-heading h1 { margin:0; color:var(--dash-ink); font-size:clamp(1.35rem,2vw,1.75rem); font-weight:720; letter-spacing:-.04em; }
    .admin-heading p { margin:.35rem 0 0; color:var(--dash-muted); font-size:.88rem; }
    .admin-topbar-actions { display:flex; align-items:center; justify-content:flex-end; gap:.8rem; }
    .admin-date-chip { display:flex; align-items:center; gap:.5rem; padding:.55rem .75rem; border:1px solid #e1e7f0; border-radius:11px; color:#52617a; background:#fff; font-size:.79rem; white-space:nowrap; }
    .admin-date-chip i { color:#7384a1; }
    .language-picker { display:flex; gap:.22rem; padding:.22rem; border:1px solid #e1e7f0; border-radius:11px; background:#fff; box-shadow:0 3px 10px rgba(28,44,72,.04); }
    .language-option { display:inline-flex; align-items:center; gap:.36rem; min-height:34px; padding:.32rem .58rem; border:0; border-radius:8px; color:#69778f; background:transparent; font-size:.78rem; font-weight:650; }
    .language-option:hover { color:#253653; background:#f4f6fa; }
    .language-option.is-active { color:#244fba; background:#edf3ff; }
    .language-option .flag { font-size:1rem; line-height:1; }
    .dashboard-notices:empty { display:none; }
    .dashboard-notices .alert { border:1px solid #e1e7f0; border-radius:12px; box-shadow:0 5px 15px rgba(27,43,69,.04); }
    .metrics-grid { grid-template-columns:repeat(5,minmax(0,1fr)); gap:.85rem; margin-bottom:1.1rem!important; }
    .metric-card { position:relative; min-width:0; min-height:142px; padding:1rem 1rem .9rem; overflow:hidden; border:1px solid #e5eaf2; border-radius:15px; background:#fff; box-shadow:0 8px 24px rgba(28,44,72,.045); }
    .metric-card::after { position:absolute; top:-34px; right:-28px; width:100px; height:100px; content:""; border-radius:50%; background:var(--metric-tint,#eff4ff); opacity:.75; }
    .metric-topline { position:relative; z-index:1; display:flex; align-items:center; justify-content:space-between; gap:.5rem; margin-bottom:.7rem; }
    .metric-label { margin:0; color:#687790; font-size:.69rem; font-weight:700; letter-spacing:.055em; line-height:1.3; text-transform:uppercase; }
    .metric-icon { position:relative; z-index:1; width:32px; height:32px; display:grid; place-items:center; flex:none; border-radius:10px; color:var(--metric-color,#356ae6); background:var(--metric-tint,#eff4ff); font-size:.95rem; }
    .metric-value { position:relative; z-index:1; margin:0; color:#1d2b43; font-size:clamp(1.28rem,1.8vw,1.75rem); font-weight:720; letter-spacing:-.04em; line-height:1.15; overflow-wrap:anywhere; }
    .metric-sub { position:relative; z-index:1; margin-top:.42rem; color:#8a96aa; font-size:.73rem; line-height:1.3; }
    .dashboard-panel { padding:1.25rem; border:1px solid #e4e9f1; border-radius:16px; background:#fff; box-shadow:0 9px 26px rgba(28,44,72,.045); }
    .dashboard-panel-heading { display:flex; justify-content:space-between; align-items:flex-start; gap:1rem; padding-bottom:.95rem; border-bottom:1px solid #edf0f5; }
    .dashboard-panel-heading h2 { margin:0; color:#25344d; font-size:1rem; font-weight:700; letter-spacing:-.02em; text-transform:none!important; }
    .dashboard-panel-heading p { margin:.3rem 0 0; color:#8390a4; font-size:.81rem; }
    .dashboard-panel-actions { display:flex; flex-wrap:wrap; gap:.45rem; }
    .monthly-breakdown { max-height:calc(100vh - 400px); min-height:210px; overflow:auto; padding:.25rem .25rem 0 0; }
    .month-entry { padding:.88rem .15rem; border-bottom:1px solid #f0f2f6; }
    .month-entry:last-child { border-bottom:0; }
    .month-entry-top { display:flex; justify-content:space-between; align-items:center; gap:.8rem; }
    .month-entry-title { display:flex; align-items:center; gap:.6rem; color:#34435c; font-size:.86rem; font-weight:650; }
    .month-entry-dot { width:8px; height:8px; border-radius:50%; background:#4e7bea; box-shadow:0 0 0 4px #edf2ff; }
    .month-entry-amount { color:#1e2e48; font-size:.9rem; font-weight:700; white-space:nowrap; }
    .month-entry-meta { display:flex; justify-content:space-between; gap:.8rem; margin:.56rem 0 .38rem; color:#8995a8; font-size:.73rem; }
    .month-entry-track { height:5px; overflow:hidden; border-radius:99px; background:#edf0f5; }
    .month-entry-track span { display:block; height:100%; min-width:2px; border-radius:99px; background:linear-gradient(90deg,#4f7bea,#72a0ff); }
    .btn { font-size:.84rem; font-weight:650; }
    .btn-sm { font-size:.78rem; }
    .admin-sidebar-collapsed .admin-shell { grid-template-columns:78px minmax(0,1fr); }
    .admin-sidebar-collapsed .admin-sidebar { padding-inline:.65rem; }
    .admin-sidebar-collapsed .admin-brand { justify-content:center; padding-inline:0; }
    .admin-sidebar-collapsed .admin-brand-text, .admin-sidebar-collapsed .admin-sidebar .sidebar-section-title, .admin-sidebar-collapsed .admin-sidebar-footer { display:none; }
    .admin-sidebar-collapsed .admin-sidebar .nav-pill { justify-content:center; padding-inline:.4rem; }
    .admin-sidebar-collapsed .admin-sidebar .nav-text { display:none; }
    .admin-sidebar-collapsed .admin-sidebar .nav-pill .nav-icon { width:auto; font-size:1.05rem; }
    .admin-sidebar-collapsed .admin-sidebar-collapse { align-self:center; }
    @media(max-width:1200px) { .metrics-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } }
    @media(max-width:992px) {
      .admin-shell { grid-template-columns:minmax(0,1fr); }
      .admin-sidebar { position:fixed; left:0; top:0; z-index:1050; display:flex; width:min(84vw,290px); height:100dvh; transform:translateX(-105%); transition:transform .22s ease; }
      body.mobile-nav-open .admin-sidebar { transform:translateX(0); }
      .admin-sidebar-collapse { display:none; }
      .admin-mobile-menu { width:38px; height:38px; display:grid; place-items:center; flex:none; border:1px solid #dfe5ef; border-radius:11px; color:#40516d; background:#fff; }
      .admin-topbar { align-items:flex-start; }
      .admin-topbar-actions { flex-wrap:wrap; }
      .admin-date-chip { display:none; }
    }
    @media(max-width:640px) {
      .admin-main { padding:1rem .8rem 1.4rem; }
      .admin-topbar { align-items:center; gap:.55rem; margin-bottom:1.15rem; }
      .admin-heading { flex:1; }
      .admin-heading h1 { font-size:1.25rem; }
      .admin-heading p { font-size:.76rem; }
      .admin-topbar-actions { gap:.4rem; }
      .language-picker { padding:.16rem; }
      .language-option { min-height:32px; padding:.27rem .38rem; font-size:.72rem; }
      .metrics-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:.6rem; }
      .metric-card { min-height:128px; padding:.78rem; }
      .metric-label { font-size:.63rem; }
      .metric-icon { width:29px; height:29px; }
      .metric-sub { font-size:.68rem; }
      .dashboard-panel { padding:.9rem; }
      .dashboard-panel-heading { flex-direction:column; }
      .dashboard-panel-actions { width:100%; }
      .dashboard-panel-actions .btn { flex:1; }
      .monthly-breakdown { max-height:none; }
    }
  </style>
</head>
<body>
  <div class="app-shell admin-shell">
{% include "partials/admin_sidebar.html" %}
    <main class="main-shell admin-main">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          <div class="dashboard-notices mb-3">
            {% for category, message in messages %}
              <div class="alert alert-{{ 'warning' if category == 'warning' else 'info' }} border-0 text-dark" role="alert">{{ message }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <header class="admin-topbar">

        <div class="admin-heading">
          <div class="admin-heading-eyebrow"><i class="bi bi-bar-chart-line-fill" aria-hidden="true"></i>{{ i18n.financial_dashboard }}</div>
          <h1>{{ i18n.revenue_invoice_analytics }}</h1>
          <p>{{ today_label }}</p>
        </div>
        <div class="admin-topbar-actions">
          <div class="admin-date-chip"><i class="bi bi-calendar3" aria-hidden="true"></i><span>{{ period_label }}</span></div>
          <form method="get" class="language-picker" aria-label="{{ i18n.language_label }}">
            <button type="submit" name="lang" value="en" class="language-option {{ 'is-active' if lang == 'en' else '' }}" aria-pressed="{{ 'true' if lang == 'en' else 'false' }}" title="English"><span class="flag" aria-hidden="true">&#127468;&#127463;</span><span>EN</span></button>
            <button type="submit" name="lang" value="de" class="language-option {{ 'is-active' if lang == 'de' else '' }}" aria-pressed="{{ 'true' if lang == 'de' else 'false' }}" title="Deutsch"><span class="flag" aria-hidden="true">&#127465;&#127466;</span><span>DE</span></button>
          </form>
        </div>
      </header>

      <section class="metrics-grid mb-4" aria-label="{{ i18n.financial_dashboard }}">
        <article class="metric-card" style="--metric-color:#416fe0;--metric-tint:#edf2ff">
          <div class="metric-topline"><div class="metric-label">{{ i18n.total_invoices }}</div><span class="metric-icon"><i class="bi bi-receipt"></i></span></div>
          <div class="metric-value">{{ stats.total_invoices }}</div><div class="metric-sub">{{ i18n.this_month }} &middot; {{ stats.invoices_this_month }} {{ i18n.invoices|lower }}</div>
        </article>
        <article class="metric-card" style="--metric-color:#12856b;--metric-tint:#e8f7f2">
          <div class="metric-topline"><div class="metric-label">{{ i18n.total_billed }}</div><span class="metric-icon"><i class="bi bi-currency-euro"></i></span></div>
          <div class="metric-value">{{ "%.2f"|format(stats.total_revenue) }} &euro;</div><div class="metric-sub">{{ i18n.this_month }} &middot; {{ "%.2f"|format(stats.income_this_month) }} &euro;</div>
        </article>
        <article class="metric-card" style="--metric-color:#23815e;--metric-tint:#eaf6ef">
          <div class="metric-topline"><div class="metric-label">{{ i18n.collected }}</div><span class="metric-icon"><i class="bi bi-check2-circle"></i></span></div>
          <div class="metric-value">{{ "%.2f"|format(stats.paid_revenue) }} &euro;</div><div class="metric-sub">{{ i18n.paid_invoices }}</div>
        </article>
        <article class="metric-card" style="--metric-color:#a16a12;--metric-tint:#fff5df">
          <div class="metric-topline"><div class="metric-label">{{ i18n.outstanding }}</div><span class="metric-icon"><i class="bi bi-hourglass-split"></i></span></div>
          <div class="metric-value">{{ "%.2f"|format(stats.outstanding_revenue) }} &euro;</div><div class="metric-sub">{{ i18n.open_invoices }}</div>
        </article>
        <article class="metric-card" style="--metric-color:#c04e46;--metric-tint:#fff0ee">
          <div class="metric-topline"><div class="metric-label">{{ i18n.overdue_invoices }}</div><span class="metric-icon"><i class="bi bi-exclamation-circle"></i></span></div>
          <div class="metric-value">{{ stats.overdue_invoices }}</div><div class="metric-sub">{{ i18n.needs_attention }}</div>
        </article>
      </section>

      <section class="dashboard-panel">
        <div class="dashboard-panel-heading">
          <div><h2>{{ i18n.monthly_breakdown }}</h2><p>{{ i18n.revenue_hours_hint }}</p></div>
          <div class="dashboard-panel-actions">
            <a href="{{ url_for('admin_invoices') }}" class="btn btn-sm btn-outline-primary"><i class="bi bi-receipt me-1"></i>{{ i18n.open_invoices }}</a>
            <a href="{{ url_for('admin_dashboard_download_report') }}" class="btn btn-sm btn-primary"><i class="bi bi-download me-1"></i>{{ i18n.download_csv }}</a>
          </div>
        </div>
        <div class="monthly-breakdown">
          <ul class="list-unstyled mb-0">
            {% for summary in monthly_summaries %}
              <li class="month-entry">
                <div class="month-entry-top"><div class="month-entry-title"><span class="month-entry-dot" aria-hidden="true"></span>{{ summary.month_name }}</div><span class="month-entry-amount">{{ "%.2f"|format(summary.total_income) }} &euro;</span></div>
                <div class="month-entry-meta"><span>{{ summary.invoice_count }} {{ i18n.invoices|lower }}</span><span>{{ summary.total_hours }} {{ i18n.hours|lower }}</span></div>
                <div class="month-entry-track" role="img" aria-label="{{ summary.fill_ratio }}% {{ i18n.of }} {{ i18n.total_billed|lower }}"><span style="width:{{ summary.fill_ratio }}%"></span></div>
              </li>
            {% endfor %}
          </ul>
        </div>
      </section>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();
    (function() {
      const body = document.body;
      const button = document.getElementById('admin-sidebar-collapse');
      const icon = button?.querySelector('i');
      const key = 'elfs-plan-admin-sidebar';
      const setCollapsed = (collapsed) => {
        body.classList.toggle('admin-sidebar-collapsed', collapsed);
        button?.setAttribute('aria-expanded', String(!collapsed));
        button?.setAttribute('aria-label', collapsed ? 'Expand navigation' : 'Collapse navigation');
        button?.setAttribute('title', collapsed ? 'Expand navigation' : 'Collapse navigation');
        if (icon) icon.className = collapsed ? 'bi bi-chevron-bar-right' : 'bi bi-chevron-bar-left';
        try { localStorage.setItem(key, collapsed ? '1' : '0'); } catch (_error) {}
      };
      try { setCollapsed(localStorage.getItem(key) === '1'); } catch (_error) { setCollapsed(false); }
      button?.addEventListener('click', () => setCollapsed(!body.classList.contains('admin-sidebar-collapsed')));
    })();

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
<html lang="{{ current_lang }}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Elf's Plan - Employee database</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root { --accent:#0f766e; --line:#e2e8f0; --muted:#64748b; }
    * { box-sizing:border-box; }
    body { margin:0; background:#f8fafc; color:#17213b; font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:228px minmax(0,1fr); background:#fff; }
    .sidebar { background:#111b3d; color:#fff; padding:1.2rem .85rem; display:flex; flex-direction:column; gap:.4rem; }
    .sidebar .brand { padding:.5rem .8rem 1rem; color:#fff; font-weight:700; }
    .sidebar a { color:#dce4ff; padding:.7rem .8rem; border-radius:.6rem; text-decoration:none; }
    .sidebar a:hover,.sidebar a.active { color:#fff; background:#26366c; }
    .main { min-width:0; padding:1.7rem; }
    .page-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin:0 0 1.25rem; }
    .page-header h1 { margin:.2rem 0; font-size:1.45rem; }
    .page-header p { margin:0; color:var(--muted); }
    .eyebrow { color:#64748b; text-transform:uppercase; letter-spacing:.08em; font-size:.72rem; }
    .employee-directory-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:0 0 .85rem; }
    .employee-heading { display:flex; align-items:center; gap:.8rem; min-width:0; }
    .employee-heading-mark { width:42px; height:42px; display:grid; place-items:center; flex:none; border:1px solid #dbe7ff; border-radius:13px; color:#2563eb; background:linear-gradient(145deg,#eff6ff,#e5efff); font-size:1.15rem; }
    .employee-heading-copy { min-width:0; }
    .employee-heading-copy .eyebrow { margin-bottom:.08rem; }
    .employee-heading-copy h1 { margin:0; font-size:1.3rem; font-weight:720; letter-spacing:-.035em; }
    .employee-heading-copy p { margin:.12rem 0 0; color:#718096; font-size:.8rem; }
    .employee-count-pill { display:inline-flex; align-items:center; gap:.35rem; margin-left:.45rem; padding:.25rem .55rem; border:1px solid #e1e8f2; border-radius:999px; color:#52617a; background:#fff; font-size:.73rem; font-weight:650; white-space:nowrap; }
    .employee-directory-header > .btn { min-height:38px; padding:.48rem .8rem; white-space:nowrap; }
    .employee-status-tabs { display:flex; gap:1.35rem; align-items:center; min-height:43px; padding:0 .45rem; margin:0 0 .8rem; border-bottom:1px solid #e2e8f0; overflow-x:auto; }
    .employee-status-tab { position:relative; display:inline-flex; align-items:center; gap:.42rem; flex:none; height:43px; padding:.3rem .1rem; color:#68758a; font-size:.89rem; font-weight:600; text-decoration:none; white-space:nowrap; }
    .employee-status-tab:hover { color:#2563eb; text-decoration:none; }
    .employee-status-tab.active { color:#1877f2; }
    .employee-status-tab.active::after { position:absolute; right:0; bottom:-1px; left:0; height:3px; content:""; border-radius:3px 3px 0 0; background:#1877f2; }
    .employee-status-tab-count { color:#9aa5b5; font-size:.72rem; font-weight:600; }
    .employee-status-button { min-width:92px; min-height:32px; padding:.34rem .68rem; border:1px solid transparent; border-radius:8px; font-size:.76rem; font-weight:700; cursor:pointer; }
    .employee-status-button.is-active { color:#087443; border-color:#a7e5c2; background:#e8f8ef; }
    .employee-status-button.is-passive { color:#b42318; border-color:#f0c2bd; background:#fff0ee; }
    .employee-status-button:hover { filter:brightness(.97); }
    .employee-contract-link { display:inline-flex; align-items:center; gap:.35rem; color:#2563eb; font-size:.78rem; font-weight:650; text-decoration:none; white-space:nowrap; }
    .employee-contract-link:hover { color:#1d4ed8; text-decoration:underline; }
    .btn { border-radius:.7rem; font-size:.9rem; }
    .btn-primary { border-color:#1877f2; background:#1877f2; }
    .summary-grid { display:flex; flex-wrap:wrap; gap:.45rem; margin-bottom:.75rem; }
    .summary-card { display:flex; align-items:center; gap:.4rem; min-height:32px; padding:.34rem .62rem; border:1px solid #e5eaf2; border-radius:999px; background:#fff; }
    .summary-card span { color:#718096; font-size:.73rem; }
    .summary-card strong { color:#263854; font-size:.78rem; font-weight:700; }
    .employee-filter-toolbar { display:flex; align-items:center; gap:.45rem; flex-wrap:wrap; margin:0 0 .8rem; padding:.48rem; border:1px solid #e2e8f0; border-radius:13px; background:#fff; box-shadow:0 5px 16px rgba(20,38,67,.045); }
    .employee-search-box { position:relative; display:flex; align-items:center; flex:1 1 220px; min-width:180px; }
    .employee-search-box > i { position:absolute; left:.72rem; color:#8190a6; pointer-events:none; }
    .employee-search-box .form-control { height:36px; padding-left:2.15rem; border:1px solid #e7ecf3; border-radius:9px; background:#f9fbfd; box-shadow:none; font-size:.83rem; }
    .employee-filter-toolbar .form-select,.employee-filter-toolbar .form-control { height:36px; border:1px solid #e7ecf3; border-radius:9px; background-color:#fff; box-shadow:none; font-size:.81rem; }
    .employee-filter-toolbar .employee-quick-filter { flex:0 1 165px; min-width:125px; }
    .employee-filter-toolbar .employee-branch-filter { flex:0 1 125px; min-width:105px; }
    .employee-advanced-filter { position:relative; }
    .employee-advanced-filter > summary { display:inline-flex; align-items:center; gap:.4rem; min-height:36px; padding:.42rem .68rem; border:1px solid #e7ecf3; border-radius:9px; color:#52617a; background:#fff; cursor:pointer; font-size:.81rem; font-weight:600; list-style:none; white-space:nowrap; }
    .employee-advanced-filter > summary::-webkit-details-marker { display:none; }
    .employee-advanced-filter[open] > summary { color:#1d4ed8; border-color:#b9cffb; background:#f5f8ff; }
    .employee-advanced-panel { position:absolute; top:calc(100% + 8px); right:0; z-index:20; display:grid; grid-template-columns:repeat(2,minmax(160px,1fr)); gap:.65rem; width:min(390px,calc(100vw - 32px)); padding:.85rem; border:1px solid #e0e7f1; border-radius:12px; background:#fff; box-shadow:0 16px 40px rgba(19,35,60,.16); }
    .employee-advanced-panel label { display:grid; gap:.25rem; color:#69778c; font-size:.7rem; font-weight:650; }
    .employee-filter-toolbar .btn { min-height:36px; padding:.42rem .68rem; font-size:.8rem; }
    .employee-filter-clear { display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; border:1px solid #e7ecf3; border-radius:9px; color:#77849a; background:#fff; text-decoration:none; }
    .employee-filter-clear:hover { color:#b42318; border-color:#f2c9c5; background:#fff8f7; }
    .table-card { overflow:hidden; border:1px solid var(--line); border-radius:.85rem; background:#fff; }
    .table-wrap { overflow:auto; }
    .employee-table { min-width:780px; margin:0; }
    .employee-table thead th { padding:.8rem; color:#64748b; background:#f8fafc; font-size:.75rem; text-transform:uppercase; white-space:nowrap; }
    .employee-table td { padding:.75rem .8rem; vertical-align:middle; }
    .employee-link { color:#17213b; font-weight:600; text-decoration:none; }
    .employee-link:hover { color:#1877f2; text-decoration:underline; }
    .employee-row-clickable { cursor:pointer; }
    .employee-row-clickable:focus-visible { outline:3px solid rgba(37,99,235,.35); outline-offset:-3px; }
    .employee-meta { display:flex; flex-direction:column; min-width:0; }
    .employee-meta small { color:var(--muted); }
    .employee-directory-cell { display:flex; align-items:center; gap:.8rem; min-width:250px; }
    .employee-directory-cell .employee-meta { gap:.12rem; }
    .employee-directory-cell .employee-link { color:#202124; font-size:1rem; font-weight:700; line-height:1.3; }
    .employee-directory-title { color:#30343b; font-size:.9rem; line-height:1.35; }
    .employee-directory-email { color:#68798d!important; font-size:.85rem; line-height:1.35; overflow-wrap:anywhere; }
    .employee-photo { width:54px; height:54px; flex:none; border:1px solid var(--line); border-radius:50%; object-fit:cover; }
    .employee-initial { display:grid; place-items:center; color:#1877f2; background:#e3f3ff; font-weight:700; }
    .employee-status { display:inline-block; padding:.22rem .6rem; border-radius:999px; color:#087443; background:#d1fae5; font-size:.75rem; font-weight:700; }
    .employee-status.inactive { color:#596273; background:#e9edf2; }
    .empty-state { display:flex; align-items:center; flex-direction:column; gap:.35rem; padding:3rem 1rem; color:var(--muted); }
    .empty-state i { font-size:2rem; color:#94a3b8; }
    .credential-notice { padding:1rem; border:1px solid #bfdbfe; border-radius:.8rem; background:#eff6ff; margin-bottom:1rem; }
    .employee-modal-backdrop { display:none; position:fixed; inset:0; z-index:1100; align-items:center; justify-content:center; padding:1rem; background:rgba(15,23,42,.48); }
    .employee-modal-backdrop.is-open { display:flex; }
    body.employee-modal-open { overflow:hidden; }
    .employee-modal { display:flex; flex-direction:column; width:min(800px,100%); max-height:92vh; overflow:hidden; border-radius:1rem; background:#fff; box-shadow:0 28px 90px rgba(15,23,42,.28); }
    .employee-modal-header { display:flex; justify-content:space-between; align-items:center; flex:none; padding:1rem 1.25rem; border-bottom:1px solid var(--line); }
    .employee-modal-header h2 { margin:0; font-size:1.2rem; }
    .employee-modal-header button { border:0; background:none; color:#64748b; font-size:1.6rem; }
    #employee-form { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
    .employee-modal-body { overflow-y:auto; padding:1rem 1.25rem; }
    .employee-form-section { padding:1rem; margin-bottom:.8rem; border:1px solid #edf0f5; border-radius:.8rem; }
    .employee-form-section h3 { margin:0 0 .9rem; font-size:.95rem; font-weight:600; }
    .employee-form-section .form-label { margin-bottom:.35rem; color:#596273; font-size:.82rem; }
    .employee-form-section .form-control,.employee-form-section .form-select { min-height:2.6rem; border-color:#dce3ec; border-radius:.6rem; font-size:.9rem; }
    .employee-platform-access-card { padding:.85rem; border:1px solid #dce7f7; border-radius:.75rem; background:#f8fbff; }
    .employee-platform-access-card .form-check-label { color:#23324b; font-weight:650; }
    .employee-function-picker { position:relative; }
    .employee-function-toggle { display:flex; width:100%; justify-content:space-between; align-items:center; min-height:42px; border:1px solid #dce3ec; border-radius:.65rem; background:#fff; padding:.55rem .75rem; color:#263449; text-align:left; }
    .employee-function-menu { position:absolute; z-index:20; inset:calc(100% + .35rem) 0 auto; max-height:min(70vh,460px); overflow:auto; padding:.45rem; border:1px solid #dce3ec; border-radius:.7rem; background:#fff; box-shadow:0 12px 30px #14233724; }
    .employee-function-menu[hidden] { display:none; }
    .employee-function-option-row { display:flex; gap:.6rem; align-items:center; padding:.5rem .55rem; border-radius:.45rem; cursor:pointer; }
    .employee-function-option-row:hover { background:#f1f7f7; }
    .employee-access-options { display:flex; flex-wrap:wrap; gap:.5rem; }
    .employee-access-options label { display:flex; align-items:center; gap:.35rem; padding:.4rem .55rem; border:1px solid #dce3ec; border-radius:.5rem; }
    .employee-function-menu-divider { margin:.45rem 0; border-top:1px solid #e5eaf0; }
    .employee-function-menu-heading { padding:.35rem .55rem; color:#758197; font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .employee-platform-settings { display:grid; gap:.75rem; margin-top:.85rem; padding-top:.85rem; border-top:1px solid #e3ebf6; }
    .employee-platform-settings[hidden] { display:none; }
    .employee-send-credentials { justify-self:start; min-height:38px; }
    .employee-modal-footer { display:flex; flex:none; justify-content:flex-end; align-items:center; gap:.55rem; padding:.8rem 1.25rem; border-top:1px solid var(--line); }
    .employee-modal-footer .me-auto { margin-right:auto; }
    .pagination-bar { display:flex; justify-content:space-between; align-items:center; gap:.6rem; padding:.8rem; }
    @media(max-width:850px) { .app-shell { grid-template-columns:1fr; } .sidebar { display:none; } .main { padding:1rem; } }
    @media(max-width:700px) { .employee-directory-header { align-items:flex-start; } .employee-heading { align-items:flex-start; } .employee-count-pill { margin-left:0; } .employee-filter-toolbar { align-items:stretch; } .employee-search-box { flex-basis:100%; } .employee-filter-toolbar .employee-quick-filter,.employee-filter-toolbar .employee-branch-filter { flex:1 1 calc(50% - .5rem); } .employee-advanced-filter { flex:1 1 auto; } .employee-advanced-filter > summary { width:100%; justify-content:center; } .employee-filter-toolbar > .btn-primary { flex:1 1 auto; } .employee-advanced-panel { left:0; right:auto; grid-template-columns:1fr; } }
    @media(max-width:600px) { .employee-directory-header { gap:.5rem; } .employee-heading-mark { width:36px; height:36px; border-radius:11px; } .employee-heading-copy h1 { font-size:1.15rem; } .employee-directory-header > .btn { padding:.42rem .6rem; font-size:.78rem; } .employee-modal-backdrop { padding:.35rem; } .employee-modal { max-height:96vh; border-radius:.75rem; } .employee-modal-header,.employee-modal-body,.employee-modal-footer { padding:.75rem; } .employee-modal-footer { flex-wrap:wrap; } .employee-modal-footer .me-auto { width:100%; } }
  </style>
</head>
<body>
  <div class="app-shell">
    {% include "partials/admin_sidebar.html" %}
    <main class="main">
      <header class="employee-directory-header"><div class="employee-heading"><span class="employee-heading-mark"><i class="bi bi-people-fill"></i></span><div class="employee-heading-copy"><div class="eyebrow">Team directory</div><h1>Employee database</h1><p>Manage staff across both branch offices <span class="employee-count-pill"><i class="bi bi-person-lines-fill"></i>{{ filtered_employees }} / {{ total_employees }}</span></p></div></div>{% if not is_sales_manager %}<button class="btn btn-primary" type="button" id="open-employee-create"><i class="bi bi-person-plus"></i><span>Add employee</span></button>{% endif %}</header>
      <nav class="employee-status-tabs" aria-label="Filter employees by status">{% for status_key, status_label in [('all','All'),('active','Active'),('passive','Passive')] %}<a class="employee-status-tab {{ 'active' if status_filter == status_key else '' }}" href="{{ url_for('admin_employees', status_filter=status_key, q=search_q or None, staff_type_filter=staff_type_filter or None, branch_filter=branch_filter or None, work_type=work_type_filter or None, role=role_filter or None) }}">{{ status_label }}<span class="employee-status-tab-count">{{ status_counts.get(status_key, 0) }}</span></a>{% endfor %}</nav>
      <section class="summary-grid"><div class="summary-card"><span>All employees</span><strong>{{ total_employees }}</strong></div><div class="summary-card"><span>Shown on this page</span><strong>{{ page_employees }}</strong></div><div class="summary-card"><span>Scheduled today</span><strong>{{ today_shifts }}</strong></div><div class="summary-card"><span>Cleaners without shifts this week</span><strong>{{ unassigned_employees }}</strong></div></section>
      {% if credential_snippets and not is_sales_manager %}<section class="credential-notice"><strong>New employee sign-in details</strong>{% for emp_id, credential in credential_snippets.items() %}<div class="mt-2">Employee #{{ emp_id }} &middot; Login code: <strong>{{ credential.code or '-' }}</strong> &middot; PIN: <strong>{{ credential.pin or '-' }}</strong></div>{% endfor %}<small class="d-block mt-2">Save these details before leaving this page.</small></section>{% endif %}
      <form method="get" class="employee-filter-toolbar" role="search">
        <div class="employee-search-box"><i class="bi bi-search" aria-hidden="true"></i><label class="visually-hidden" for="employee-search">Search employees</label><input class="form-control" id="employee-search" name="q" value="{{ search_q or '' }}" placeholder="Search name, role, email, phone, or city"></div>
        <label class="visually-hidden" for="employee-staff-type-filter">Functions</label><select class="form-select employee-quick-filter" id="employee-staff-type-filter" name="staff_type_filter"><option value="">All functions</option>{% for staff_type in employee_staff_types %}<option value="{{ staff_type }}" {% if staff_type_filter == staff_type %}selected{% endif %}>{{ staff_type }}</option>{% endfor %}</select>
        <label class="visually-hidden" for="employee-branch-filter">Branch</label><select class="form-select employee-branch-filter" id="employee-branch-filter" name="branch_filter"><option value="">All branches</option><option value="Wien" {% if branch_filter == 'Wien' %}selected{% endif %}>Wien</option><option value="Graz" {% if branch_filter == 'Graz' %}selected{% endif %}>Graz</option></select>
        <details class="employee-advanced-filter" {% if work_type_filter or role_filter %}open{% endif %}><summary><i class="bi bi-sliders"></i><span>More filters</span><i class="bi bi-chevron-down small"></i></summary><div class="employee-advanced-panel"><label for="employee-work-type-filter">Work type<select class="form-select" id="employee-work-type-filter" name="work_type"><option value="">All work types</option>{% for work_type in employee_work_types %}<option value="{{ work_type }}" {% if work_type_filter == work_type %}selected{% endif %}>{{ work_type }}</option>{% endfor %}</select></label><label for="employee-role-filter">Role<input class="form-control" id="employee-role-filter" name="role" value="{{ role_filter or '' }}" placeholder="Filter by role"></label></div></details>
        {% if search_q or work_type_filter or role_filter or staff_type_filter or branch_filter %}<a class="employee-filter-clear" href="{{ url_for('admin_employees') }}" aria-label="Clear filters" title="Clear filters"><i class="bi bi-x-lg"></i></a>{% endif %}<button class="btn btn-primary" type="submit"><i class="bi bi-search"></i><span>Search</span></button>
      </form>
      <section class="table-card"><div class="table-wrap"><table class="table table-hover employee-table"><thead><tr><th>Employee</th><th>Phone number</th><th>Role</th>{% if not is_site_manager and not is_sales_manager %}<th>Contract</th>{% endif %}{% if show_shifts_column %}<th>Shifts</th>{% endif %}<th>Status</th>{% if not is_sales_manager %}<th class="text-end">Actions</th>{% endif %}</tr></thead><tbody>
      {% for emp in employees %}<tr class="employee-row-clickable" data-row-url="{{ url_for('admin_employee_detail', employee_id=emp.id) }}" tabindex="0" role="link" aria-label="Open employee page for {{ emp.name|e }}">
        <td><div class="employee-directory-cell">{% if emp.profile_image_path %}<img class="employee-photo" src="{{ url_for('static', filename=emp.profile_image_path) }}" alt="">{% else %}<span class="employee-photo employee-initial">{{ emp.name[:1]|upper }}</span>{% endif %}<div class="employee-meta"><a class="employee-link" href="{{ url_for('admin_employee_detail', employee_id=emp.id) }}">{{ emp.name }}</a><span class="employee-directory-title">{{ employee_function_map[emp.id]|join(', ') }}</span><small class="employee-directory-email">{{ emp.login_email or 'No email added' }}</small></div></div></td>
        <td><div class="employee-meta"><span>{{ emp.profile_phone or '-' }}</span><small>{{ emp.profile_city or emp.profile_address or 'No contact details' }}</small></div></td><td>{{ emp.role or '-' }}</td>
        {% if not is_site_manager and not is_sales_manager %}<td>{% if emp.profile_contract_start_date or emp.profile_contract_end_date %}<a class="employee-contract-link" href="{{ url_for('admin_employee_docx', employee_id=emp.id) }}"><i class="bi bi-download"></i><span>Download</span></a>{% else %}<span class="text-secondary">-</span>{% endif %}</td>{% endif %}
        {% if show_shifts_column %}<td>{% if 'Cleaner' in employee_function_map[emp.id] %}{{ shift_counts.get(emp.id, 0) }}{% else %}<span class="text-secondary">-</span>{% endif %}</td>{% endif %}<td>{% if not is_sales_manager %}<form method="post" class="employee-status-form"><input type="hidden" name="action" value="set_status"><input type="hidden" name="id" value="{{ emp.id }}"><input type="hidden" name="worker_status" value="{{ 'passive' if emp.worker_status == 'active' else 'active' }}"><input type="hidden" name="redirect_status" value="{{ status_filter }}"><input type="hidden" name="redirect_q" value="{{ search_q }}"><input type="hidden" name="redirect_page" value="{{ page }}"><input type="hidden" name="redirect_work_type" value="{{ work_type_filter }}"><input type="hidden" name="redirect_role" value="{{ role_filter }}"><input type="hidden" name="redirect_staff_type" value="{{ staff_type_filter }}"><input type="hidden" name="redirect_branch" value="{{ branch_filter }}"><button class="employee-status-button {{ 'is-active' if emp.worker_status == 'active' else 'is-passive' }}" type="submit">{{ 'Active' if emp.worker_status == 'active' else 'Passive' }}</button></form>{% else %}<span class="employee-status {{ 'inactive' if emp.worker_status != 'active' else '' }}">{{ emp.worker_status|capitalize }}</span>{% endif %}</td>
        {% if not is_sales_manager %}<td class="text-end"><form method="post" onsubmit="return confirm(document.documentElement.lang==='de'?'Mitarbeiter wirklich l'+String.fromCharCode(246)+'schen?':'Delete this employee?')"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ emp.id }}"><input type="hidden" name="redirect_page" value="{{ page }}"><input type="hidden" name="redirect_q" value="{{ search_q }}"><button class="btn btn-sm btn-outline-danger" type="submit" aria-label="Delete employee" title="Delete employee"><i class="bi bi-trash"></i></button></form></td>
        {% else %}<td><a class="btn btn-sm btn-outline-primary" href="{{ url_for('admin_employee_detail', employee_id=emp.id) }}"><i class="bi bi-eye me-1"></i>View</a></td>{% endif %}
      </tr>{% else %}<tr><td colspan="{{ employee_column_count }}"><div class="empty-state"><i class="bi bi-people"></i><strong>No employees found</strong><span>Adjust your search or add an employee.</span>{% if not is_sales_manager %}<button type="button" class="btn btn-primary mt-2" id="open-employee-create-empty">Add employee</button>{% endif %}</div></td></tr>{% endfor %}
      </tbody></table></div>
      {% if total_pages > 1 %}<div class="pagination-bar border-top"><span class="text-secondary small">Page {{ page }} of {{ total_pages }}</span><div class="d-flex gap-2">{% if has_prev %}<a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=prev_page, q=search_q or None, work_type=work_type_filter or None, role=role_filter or None, staff_type_filter=staff_type_filter or None, branch_filter=branch_filter or None) }}">Previous</a>{% endif %}{% if has_next %}<a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_employees', page=next_page, q=search_q or None, work_type=work_type_filter or None, role=role_filter or None, staff_type_filter=staff_type_filter or None, branch_filter=branch_filter or None) }}">Next</a>{% endif %}</div></div>{% endif %}
      </section>
    </main>
  </div>
  {% if not is_sales_manager %}<div class="employee-modal-backdrop" id="employee-modal" aria-hidden="true"><section class="employee-modal" role="dialog" aria-modal="true" aria-labelledby="employee-modal-title">
    <header class="employee-modal-header"><h2 id="employee-modal-title">Add employee</h2><button type="button" id="close-employee-modal" aria-label="Close">&times;</button></header>
    <form method="post" enctype="multipart/form-data" id="employee-form"><input type="hidden" name="action" id="employee-action" value="create"><input type="hidden" name="id" id="employee-id"><input type="hidden" name="return_to" value="{{ request.args.get('return_to', '') }}"><input type="hidden" name="redirect_q" value="{{ search_q }}"><input type="hidden" name="redirect_page" value="{{ page }}"><input type="hidden" name="redirect_work_type" value="{{ work_type_filter }}"><input type="hidden" name="redirect_role" value="{{ role_filter }}"><input type="hidden" name="redirect_staff_type" value="{{ staff_type_filter }}"><input type="hidden" name="redirect_branch" value="{{ branch_filter }}"><input type="hidden" name="redirect_status" value="{{ status_filter }}">
      <div class="employee-modal-body">
        <section class="employee-form-section"><h3>Employee</h3><div class="row g-3">
          <div class="col-md-6"><label class="form-label" for="employee-name">Full name *</label><input class="form-control" id="employee-name" name="name" required></div>
          <div class="col-md-6"><label class="form-label" for="employee-role">Role / job title</label><input class="form-control" id="employee-role" name="role" placeholder="e.g. Team lead"><div class="form-text">The employee’s specific job title.</div></div>
          <div class="col-md-6"><label class="form-label" for="employee-branch">Branch office</label><select class="form-select" id="employee-branch" name="branch"><option value="Wien">Wien</option><option value="Graz">Graz</option></select></div>
          <div class="col-md-6"><label class="form-label" for="employee-status">Employee status</label><select class="form-select" id="employee-status" name="worker_status"><option value="active">Active</option><option value="passive">Passive</option></select></div>
          <div class="col-md-6"><label class="form-label" for="employee-photo">Profile photo</label><input class="form-control" type="file" id="employee-photo" name="profile_image" accept="image/png,image/jpeg,image/gif,image/webp,image/heic"></div>
          <div class="col-12" id="employee-existing-photo-wrap" hidden><img id="employee-existing-photo" class="employee-photo" alt="Employee profile photo"></div>
        </div></section>
        <section class="employee-form-section"><h3>Contact details</h3><div class="row g-3">
          <div class="col-md-4"><label class="form-label" for="employee-phone">Phone</label><input class="form-control" type="tel" id="employee-phone" name="profile_phone"></div>
          <div class="col-md-4"><label class="form-label" for="employee-address">Street address</label><input class="form-control" id="employee-address" name="profile_address"></div>
          <div class="col-md-2"><label class="form-label" for="employee-zip">Postal code</label><input class="form-control" id="employee-zip" name="profile_zip_code"></div>
          <div class="col-md-2"><label class="form-label" for="employee-city">City</label><input class="form-control" id="employee-city" name="profile_city"></div>
        </div></section>
        <section class="employee-form-section"><h3>Employment and contract</h3><div class="row g-3">
          <div class="col-md-4"><label class="form-label" for="employee-work-type">Work type</label><select class="form-select" id="employee-work-type" name="profile_work_type"><option value="Teilzeit">Part-time</option><option value="Vollzeit">Full-time</option><option value="Intern">Intern</option></select></div>
          {% if not is_site_manager %}<div class="col-md-4"><label class="form-label" for="employee-rate">Hourly pay</label><input class="form-control" id="employee-rate" name="profile_euros_per_hour" inputmode="decimal"></div>{% endif %}
          <div class="col-md-4"><label class="form-label" for="employee-hours">Weekly hours</label><input class="form-control" id="employee-hours" name="profile_working_hours"></div>
          {% if not is_site_manager %}<div class="col-md-4"><label class="form-label" for="employee-contract-start">Contract start</label><input class="form-control" type="date" id="employee-contract-start" name="profile_contract_start_date"></div>
          <div class="col-md-4"><label class="form-label" for="employee-contract-end">Contract end</label><input class="form-control" type="date" id="employee-contract-end" name="profile_contract_end_date"></div>
          <div class="col-md-6"><label class="form-label" for="employee-group-type">Pay group type</label><select class="form-select" id="employee-group-type" name="profile_group_type"><option value="Lohngruppe">Pay group</option><option value="Verwendungsgruppe">Usage group</option></select></div>
          <div class="col-md-6"><label class="form-label" for="employee-group-number">Group number</label><input class="form-control" id="employee-group-number" name="profile_group_number"></div>{% endif %}
        </div></section>
        <section class="employee-form-section"><h3>Platform access</h3><div class="employee-platform-access-card">
          <label class="form-label" for="employee-functions-toggle">Functions</label>
          <div class="employee-function-picker"><button class="employee-function-toggle" type="button" id="employee-functions-toggle" aria-expanded="false" aria-controls="employee-functions-menu"><span id="employee-functions-summary">Cleaner</span><i class="bi bi-chevron-down"></i></button>
            <div class="employee-function-menu" id="employee-functions-menu" hidden>{% if is_main_admin %}<div class="employee-function-menu-heading">System access</div><div class="employee-access-options" role="radiogroup" aria-label="System access">{% for role_value, role_label in [('none','No system access'),('employee','Cleaner'),('site_manager','Site manager'),('sales_manager','Sales manager'),('admin','Admin')] %}<label><input class="form-check-input employee-access-option" type="radio" name="employee_access_picker" value="{{ role_value }}" {% if role_value == 'none' %}checked{% endif %}><span>{{ role_label }}</span></label>{% endfor %}</div><div class="employee-function-menu-divider"></div>{% endif %}{% for function in employee_staff_types %}<label class="employee-function-option-row"><input class="form-check-input employee-function-option" type="checkbox" value="{{ function }}" {% if function == 'Cleaner' %}checked{% endif %}><span>{{ function }}</span></label>{% endfor %}</div>
          </div><input type="hidden" name="staff_functions" id="employee-staff-functions" value='["Cleaner"]'><input type="hidden" name="staff_type" id="employee-staff-type" value="Cleaner"><input type="hidden" name="access_role" id="employee-access-role" value="employee">
          <div class="form-text">Choose every function this person performs. A person can have more than one.</div>
          {% if is_main_admin %}<div class="employee-platform-settings" id="employee-platform-settings"><div><label class="form-label" for="employee-login-email">Employee email</label><input class="form-control" type="email" id="employee-login-email" name="login_email" autocomplete="email" placeholder="name@example.com"><div class="form-text">Used for sign-in and credential delivery.</div></div><div class="form-check"><input class="form-check-input" type="checkbox" id="employee-platform-access" name="has_platform_access" value="1"><label class="form-check-label" for="employee-platform-access">Enable platform access and create sign-in details</label></div><button class="btn btn-primary employee-send-credentials" id="send-employee-credentials" type="submit" name="send_credentials_email" value="1"><i class="bi bi-send-fill"></i><span>Send sign-in details by email</span></button></div>{% else %}<div class="form-text mt-2">Platform access must be enabled by an administrator before an employee can sign in. Other functions are stored on the employee record.</div>{% endif %}
        </div></section>
      </div>
      <footer class="employee-modal-footer"><a class="btn btn-outline-secondary me-auto" href="{{ url_for('admin_employees') }}">Employee database</a><button type="button" class="btn btn-outline-secondary" id="cancel-employee-modal">Cancel</button><button type="submit" class="btn btn-primary"><i class="bi bi-check-circle me-1"></i><span id="employee-submit-label">Create employee</span></button></footer>
    </form>
  </section></div>
  <script>
    (() => {
      const modal=document.getElementById('employee-modal'), form=document.getElementById('employee-form'), german=document.documentElement.lang==='de';
      const set=(id,value)=>{const el=document.getElementById(id);if(!el)return;if(el.type==='checkbox')el.checked=Boolean(value);else el.value=value??'';};
      const platformAccess=document.getElementById('employee-platform-access'), platformSettings=document.getElementById('employee-platform-settings');
      const functionToggle=document.getElementById('employee-functions-toggle'), functionMenu=document.getElementById('employee-functions-menu');
      const functionOptions=[...document.querySelectorAll('.employee-function-option')], accessOptions=[...document.querySelectorAll('.employee-access-option')];
      const syncFunctionAccess=()=>{
        let selected=functionOptions.filter(option=>option.checked).map(option=>option.value);
        if(!selected.length&&functionOptions.length){functionOptions[0].checked=true;selected=[functionOptions[0].value];}
        document.getElementById('employee-staff-functions').value=JSON.stringify(selected);
        document.getElementById('employee-staff-type').value=selected[0]||'Cleaner';
        const selectedAccess=accessOptions.find(option=>option.checked);
        const access=selectedAccess?.value||'none';
        document.getElementById('employee-access-role').value=access==='none'?'employee':access;
        if(platformAccess)platformAccess.checked=access!=='none';
        const accessLabel=selectedAccess?.parentElement.querySelector('span')?.textContent||'No system access';
        document.getElementById('employee-functions-summary').textContent=[...selected, accessLabel].join(', ');
      };
      const syncPlatformSettings=()=>{
        if(platformSettings&&platformAccess){platformSettings.querySelectorAll('input,select,button').forEach(el=>{if(el!==platformAccess)el.disabled=!platformAccess.checked;});}
      };
      const setFunctionAccess=(functions,role)=>{
        const selected=Array.isArray(functions)&&functions.length?functions:['Cleaner'];
        functionOptions.forEach(option=>{option.checked=selected.includes(option.value);});
        const normalizedRole=role||'employee';
        accessOptions.forEach(option=>{option.checked=option.value===normalizedRole;});
        syncFunctionAccess();
      };
      const chooseAccess=role=>{
        accessOptions.forEach(option=>{option.checked=option.value===role;});
        if(platformAccess)platformAccess.checked=role!=='none';
        syncFunctionAccess();syncPlatformSettings();
      };
      const open=(data=null)=>{
        form.reset(); document.getElementById('employee-modal-title').textContent=german?(data?'Mitarbeiter bearbeiten':'Mitarbeiter hinzuf'+String.fromCharCode(252)+'gen'):(data?'Edit employee':'Add employee');
        document.getElementById('employee-submit-label').textContent=german?(data?String.fromCharCode(196)+'nderungen speichern':'Mitarbeiter anlegen'):(data?'Save changes':'Create employee');
        set('employee-action',data?'update':'create'); document.getElementById('employee-existing-photo-wrap').hidden=true;
        if(data){set('employee-id',data.id);set('employee-name',data.name);set('employee-role',data.role);set('employee-status',data.workerStatus||'active');set('employee-phone',data.phone);set('employee-address',data.address);set('employee-zip',data.zip);set('employee-city',data.city);set('employee-contract-start',data.start);set('employee-contract-end',data.end);set('employee-rate',data.rate);set('employee-hours',data.hours);set('employee-work-type',data.workType);set('employee-group-type',data.groupType);set('employee-group-number',data.groupNumber);set('employee-login-email',data.loginEmail);set('employee-branch',data.branch||'Wien');set('employee-platform-access',data.platformAccess==='1');const existingFunctions=Array.isArray(data.staffFunctions)?data.staffFunctions:(data.staffFunctions||data.staffType||'Cleaner').toString().split('|').filter(Boolean);setFunctionAccess(existingFunctions,data.platformAccess==='1'?(data.accessRole||'employee'):'none');if(data.image){document.getElementById('employee-existing-photo-wrap').hidden=false;document.getElementById('employee-existing-photo').src='/static/'+data.image;}}
        else{set('employee-id','');set('employee-status','active');set('employee-work-type','Teilzeit');set('employee-group-type','Lohngruppe');set('employee-branch','Wien');set('employee-platform-access',false);setFunctionAccess(['Cleaner'],'none');}
        if(functionMenu){functionMenu.hidden=true;functionToggle?.setAttribute('aria-expanded','false');}
        syncPlatformSettings();modal.classList.add('is-open');modal.setAttribute('aria-hidden','false');document.body.classList.add('employee-modal-open');setTimeout(()=>document.getElementById('employee-name').focus(),40);
      };
      const close=()=>{
        if(!modal)return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden','true');
        document.body.classList.remove('employee-modal-open');
        if(functionMenu){functionMenu.hidden=true;functionToggle?.setAttribute('aria-expanded','false');}
        document.getElementById('open-employee-create')?.focus();
      };
      functionOptions.forEach(option=>option.addEventListener('change',()=>{
        const managerFunction=option.checked&&option.value==='Site manager'?'site_manager':option.checked&&option.value==='Sales manager'?'sales_manager':null;
        if(managerFunction&&accessOptions.some(accessOption=>accessOption.value===managerFunction))chooseAccess(managerFunction);else syncFunctionAccess();
      }));accessOptions.forEach(option=>option.addEventListener('change',()=>chooseAccess(option.value)));
      functionToggle?.addEventListener('click',()=>{functionMenu.hidden=!functionMenu.hidden;functionToggle.setAttribute('aria-expanded',String(!functionMenu.hidden));});
      document.addEventListener('click',event=>{if(functionMenu&&!functionMenu.hidden&&!event.target.closest('.employee-function-picker')){functionMenu.hidden=true;functionToggle?.setAttribute('aria-expanded','false');}});
      document.getElementById('open-employee-create').addEventListener('click',()=>open());document.getElementById('open-employee-create-empty')?.addEventListener('click',()=>open());
      platformAccess?.addEventListener('change',()=>{if(!platformAccess.checked)chooseAccess('none');else if(!accessOptions.some(option=>option.checked&&option.value!=='none'))chooseAccess('employee');syncPlatformSettings();});
      document.getElementById('close-employee-modal').addEventListener('click',close);document.getElementById('cancel-employee-modal').addEventListener('click',close);modal.addEventListener('click',event=>{if(event.target===modal)close();});document.addEventListener('keydown',event=>{if(event.key==='Escape'&&modal.classList.contains('is-open'))close();});
      const employeeToEdit={{ employee_to_edit_data|tojson }};const openCreateRequested={{ 'true' if request.args.get('create') == '1' else 'false' }};if(employeeToEdit)open(employeeToEdit);else if(openCreateRequested)open();
    })();
  </script>{% endif %}
  <script>
    document.querySelectorAll('.employee-row-clickable').forEach((row)=>{
      row.addEventListener('click',(event)=>{
        if(event.target.closest('a,button,input,select,textarea,label,form,[role="button"]')) return;
        window.location.assign(row.dataset.rowUrl);
      });
      row.addEventListener('keydown',(event)=>{
        if((event.key==='Enter'||event.key===' ')&&event.target===row){event.preventDefault();window.location.assign(row.dataset.rowUrl);}
      });
    });
  </script>
</body>
</html>
"""

ADMIN_SITES_TEMPLATE = """
<!doctype html>
<html lang="{{ current_lang }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — Standortübersicht</title>
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
    .client-search-bar { display:flex; align-items:center; gap:.65rem; padding:.6rem .75rem; border:1px solid #dbe3ef; border-radius:.85rem; background:#fff; box-shadow:0 5px 16px rgba(15,23,42,.04); }
    .client-search-bar > i { color:#64748b; }
    .client-search-bar .form-control { border:0; box-shadow:none; min-width:120px; }
    .client-table { min-width:850px; font-size:.9rem; }
    .client-table thead th { padding:.9rem .8rem; white-space:nowrap; }
    .client-table tbody td { padding:.8rem; }
    .client-main { display:flex; flex-direction:column; min-width:0; }
    .client-main strong, .client-main span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:250px; }
    .client-main small { color:#64748b; }
    .client-detail-link { color:#0f172a; text-decoration:none; }
    .client-detail-link:hover { color:#2563eb; text-decoration:underline; }
    .client-logo { width:40px; height:40px; border-radius:10px; object-fit:cover; border:1px solid #e2e8f0; }
    .client-logo-placeholder { display:inline-flex; align-items:center; justify-content:center; background:#eff6ff; color:#2563eb; font-weight:700; }
    .status-pill { display:inline-flex; border-radius:999px; padding:.24rem .65rem; font-size:.75rem; font-weight:600; }
    .status-pill.is-active { color:#047857; background:#d1fae5; }
    .status-pill.is-inactive { color:#64748b; background:#e2e8f0; }
    .shift-count { display:inline-flex; min-width:1.8rem; justify-content:center; border-radius:999px; padding:.15rem .5rem; background:#eff6ff; color:#1d4ed8; font-weight:600; }
    .empty-clients { display:flex; align-items:center; flex-direction:column; gap:.35rem; color:#64748b; }
    .empty-clients i { font-size:2rem; color:#94a3b8; }
    .empty-clients strong { color:#0f172a; }
    .client-modal-backdrop { display:none; position:fixed; inset:0; z-index:1100; align-items:center; justify-content:center; padding:1rem; background:rgba(15,23,42,.48); }
    .client-modal-backdrop.is-open { display:flex; }
    body.client-modal-open { overflow:hidden; }
    .client-modal { display:flex; flex-direction:column; width:min(760px,100%); max-height:min(92vh,900px); overflow:hidden; border-radius:1rem; background:#fff; box-shadow:0 28px 90px rgba(15,23,42,.28); }
    .client-modal-header { display:flex; align-items:center; justify-content:space-between; flex:none; padding:1rem 1.25rem; border-bottom:1px solid #e8edf4; }
    .client-modal-header h2 { margin:0; font-size:1.2rem; font-weight:600; }
    .client-modal-close { border:0; background:none; color:#64748b; font-size:1.6rem; line-height:1; }
    #client-form { display:flex; flex-direction:column; min-height:0; overflow:hidden; }
    .client-modal-body { padding:1rem 1.25rem; overflow-y:auto; overscroll-behavior:contain; }
    .client-form-section { padding:1rem; margin-bottom:.8rem; border:1px solid #edf0f5; border-radius:.8rem; background:#fff; }
    .client-form-section h3 { margin:0 0 .9rem; font-size:.95rem; font-weight:600; color:#334155; }
    .client-form-section .form-label { margin-bottom:.35rem; text-transform:none; letter-spacing:0; font-size:.82rem; }
    .client-form-section .form-control, .client-form-section .form-select { min-height:2.65rem; border:1px solid #dce3ec; border-radius:.65rem; font-size:.9rem; }
    .client-form-section textarea.form-control { min-height:6rem; }
    .client-modal-footer { flex:none; display:flex; align-items:center; justify-content:flex-end; gap:.55rem; padding:.8rem 1.25rem; border-top:1px solid #e8edf4; background:#fff; }
    .client-modal-footer .btn { min-height:2.55rem; font-size:.88rem; }
    :root { --accent:#014D4E; --btn-grad-accent:linear-gradient(135deg,#014D4E 0%,#087f7d 100%); --btn-grad-accent-hover:linear-gradient(135deg,#013f40 0%,#066967 100%); }
    body { background:#f5f7fa; color:#1d2d44; font-size:14px; }
    .main-shell { min-width:0; padding:clamp(1rem,2vw,1.6rem); background:#f5f7fa; }
    .badge-soft { color:#014D4E; background:#e8f3f2; border-color:#cce1df; }
    .stats-grid { gap:.75rem; margin-bottom:.9rem; }
    .stat-card { padding:.85rem 1rem; border-color:#e6eaf0; border-radius:13px; box-shadow:0 3px 12px rgba(25,39,61,.035); }
    .stat-label { color:#77849a; }
    .stat-value { color:#1d2d44; font-size:1.35rem; }
    .site-status-tabs { display:flex; gap:1.15rem; overflow-x:auto; margin:0 0 .85rem; padding:0 .15rem; border-bottom:1px solid #e5e9ef; white-space:nowrap; }
    .site-status-tab { display:inline-flex; align-items:center; gap:.45rem; padding:.55rem .1rem .65rem; border-bottom:3px solid transparent; color:#667287; text-decoration:none; font-weight:600; }
    .site-status-tab span { color:#8792a4; font-size:.75rem; }
    .site-status-tab.active { color:#014D4E; border-color:#014D4E; }
    .site-status-tab.active span { color:#014D4E; }
    .client-search-bar { gap:.45rem; padding:.45rem .55rem; border-color:#e5e9ef; border-radius:12px; box-shadow:0 3px 12px rgba(25,39,61,.035); }
    .client-search-bar .form-control { height:36px; font-size:.85rem; }
    .client-table { min-width:760px; font-size:.86rem; }
    .client-table thead th { padding:.7rem .75rem; color:#77849a; background:#f8fafb; font-size:.7rem; }
    .client-table tbody td { padding:.65rem .75rem; border-color:#edf0f4; }
    .site-row-clickable { cursor:pointer; }
    .site-row-clickable:hover { background:#f7fbfa; }
    .site-row-clickable:focus-visible { outline:3px solid rgba(1,77,78,.22); outline-offset:-3px; }
    .client-logo { width:42px; height:42px; border-radius:12px; }
    .client-logo-placeholder { color:#014D4E; background:#e8f3f2; }
    .client-detail-link:hover { color:#014D4E; }
    .card-surface { border-color:#e6eaf0; border-radius:14px; box-shadow:0 4px 14px rgba(25,39,61,.04); }
    .site-status-form { margin:0; }
    .site-status-button { min-width:76px; padding:.3rem .6rem; border:0; border-radius:999px; font-size:.75rem; font-weight:700; }
    .site-status-button.is-active { color:#fff; background:#16865f; }
    .site-status-button.is-inactive { color:#fff; background:#dc4545; }
    .site-status-button:hover { filter:brightness(.94); }
    .site-directory-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin:0 0 .85rem; }
    .site-heading { display:flex; align-items:center; gap:.8rem; min-width:0; }
    .site-heading-mark { width:42px; height:42px; display:grid; place-items:center; flex:none; border:1px solid #c8dfdd; border-radius:13px; color:#014D4E; background:linear-gradient(145deg,#eaf4f3,#dceceb); font-size:1.15rem; }
    .site-heading-copy { min-width:0; }
    .site-heading-copy .eyebrow { margin-bottom:.08rem; }
    .site-heading-copy h1 { margin:0; color:#1d2d44; font-size:1.3rem; font-weight:720; letter-spacing:-.035em; }
    .site-heading-copy p { margin:.12rem 0 0; color:#718096; font-size:.8rem; }
    .site-count-pill { display:inline-flex; align-items:center; gap:.35rem; margin-left:.45rem; padding:.25rem .55rem; border:1px solid #e1e8f2; border-radius:999px; color:#52617a; background:#fff; font-size:.73rem; font-weight:650; white-space:nowrap; }
    .site-directory-header > .btn { min-height:38px; padding:.48rem .8rem; white-space:nowrap; }
    .site-status-tabs { display:flex; gap:1.35rem; align-items:center; min-height:43px; padding:0 .45rem; margin:0 0 .65rem; border-bottom:1px solid #e2e8f0; overflow-x:auto; }
    .site-status-tab { position:relative; display:inline-flex; align-items:center; gap:.42rem; flex:none; height:43px; padding:.3rem .1rem; border:0; color:#68758a; font-size:.89rem; font-weight:600; text-decoration:none; white-space:nowrap; }
    .site-status-tab:hover { color:#014D4E; text-decoration:none; }
    .site-status-tab.active { color:#014D4E; }
    .site-status-tab.active::after { position:absolute; right:0; bottom:-1px; left:0; height:3px; content:""; border-radius:3px 3px 0 0; background:#014D4E; }
    .site-status-tab-count { color:#9aa5b5; font-size:.72rem; font-weight:600; }
    .site-filter-toolbar { display:flex; align-items:center; gap:.45rem; margin:0 0 .8rem; padding:.48rem; border:1px solid #e2e8f0; border-radius:13px; background:#fff; box-shadow:0 5px 16px rgba(20,38,67,.045); }
    .site-search-box { position:relative; display:flex; align-items:center; flex:1 1 260px; min-width:180px; }
    .site-search-box > i { position:absolute; left:.72rem; color:#8190a6; pointer-events:none; }
    .site-search-box .form-control { height:36px; padding-left:2.15rem; border:1px solid #e7ecf3; border-radius:9px; background:#f9fbfd; box-shadow:none; font-size:.83rem; }
    .site-filter-toolbar .form-select { flex:0 1 185px; min-width:145px; height:36px; border:1px solid #e7ecf3; border-radius:9px; background-color:#fff; box-shadow:none; font-size:.81rem; }
    .site-coverage-chip { display:inline-flex; align-items:center; gap:.35rem; min-height:36px; padding:.35rem .55rem; border:1px solid #c8dfdd; border-radius:9px; color:#014D4E; background:#f1f8f7; font-size:.76rem; font-weight:650; white-space:nowrap; }
    .site-coverage-chip a { color:inherit; text-decoration:none; }
    .site-add-filter { position:relative; flex:none; }
    .site-add-filter > summary { display:inline-flex; align-items:center; gap:.4rem; min-height:36px; padding:.42rem .65rem; border:1px solid transparent; border-radius:9px; color:#68758a; background:transparent; cursor:pointer; font-size:.81rem; font-weight:600; list-style:none; white-space:nowrap; }
    .site-add-filter > summary::-webkit-details-marker { display:none; }
    .site-add-filter[open] > summary { border-color:#dce8e7; color:#014D4E; background:#f1f8f7; }
    .site-add-filter-menu { position:absolute; top:calc(100% + 7px); right:0; z-index:30; display:grid; gap:.2rem; width:220px; padding:.4rem; border:1px solid #e1e7ef; border-radius:11px; background:#fff; box-shadow:0 14px 32px rgba(19,35,60,.14); }
    .site-add-filter-menu a { padding:.55rem .6rem; border-radius:7px; color:#48566d; font-size:.81rem; text-decoration:none; }
    .site-add-filter-menu a:hover { color:#014D4E; background:#f1f8f7; }
    .site-filter-toolbar .btn { min-height:36px; padding:.42rem .68rem; font-size:.8rem; }
    .site-filter-clear { display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; border:1px solid #e7ecf3; border-radius:9px; color:#77849a; background:#fff; text-decoration:none; }
    .site-filter-clear:hover { color:#b42318; border-color:#f2c9c5; background:#fff8f7; }
    @media(max-width:700px) { .site-directory-header { align-items:flex-start; } .site-filter-toolbar { align-items:stretch; flex-wrap:wrap; } .site-search-box { flex:1 1 100%; } .site-filter-toolbar .form-select { flex:1 1 calc(50% - .4rem); min-width:0; } .site-filter-toolbar > .btn-primary { flex:1 1 auto; } .site-add-filter { flex:1 1 auto; } .site-add-filter > summary { justify-content:center; width:100%; border-color:#e7ecf3; } }
    @media(max-width:600px) { .site-directory-header { gap:.5rem; } .site-heading-mark { width:36px; height:36px; border-radius:11px; } .site-heading-copy h1 { font-size:1.15rem; } .site-directory-header > .btn { padding:.42rem .6rem; font-size:.78rem; } }
    .btn { min-height:40px; padding:.48rem .8rem; border-radius:10px; font-size:.85rem; box-shadow:0 2px 7px rgba(25,39,61,.06); }
    .btn-sm { min-height:34px; padding:.35rem .6rem; border-radius:9px; font-size:.78rem; }
    .btn-primary,.btn-outline-primary { color:#fff; border-color:#014D4E; background-image:linear-gradient(135deg,#014D4E,#087f7d); box-shadow:0 4px 10px rgba(1,77,78,.17); }
    .btn-primary:hover,.btn-outline-primary:hover { color:#fff; background-image:linear-gradient(135deg,#013f40,#066967); }
    @media(max-width:650px) { .main-shell { padding:.75rem; } .site-status-tabs { gap:.85rem; } .stats-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
    @media(max-width:992px) { .sidebar-collapse-toggle { display:none; } }
    @media(max-width:650px) { .client-modal-backdrop { padding:.4rem; } .client-modal { max-height:96vh; border-radius:.8rem; } .client-modal-header,.client-modal-body,.client-modal-footer { padding:.75rem; } .client-modal-footer { flex-wrap:wrap; } .client-modal-footer .me-auto { margin-right:0!important; width:100%; } .client-search-bar { flex-wrap:wrap; } .client-search-bar .form-control { flex:1 1 70%; } }

    @media(min-width:993px) {
      body.sidebar-collapsed .app-shell { grid-template-columns:72px minmax(0,1fr); }
      body.sidebar-collapsed .sidebar { width:72px; padding:1.1rem .6rem; gap:1rem; }
      body.sidebar-collapsed .sidebar-section-title,
      body.sidebar-collapsed .nav-text,
      body.sidebar-collapsed .sidebar-footer { display:none; }
      body.sidebar-collapsed .nav-pill { justify-content:center; padding:.55rem .35rem; }
      body.sidebar-collapsed .sidebar-collapse-toggle { align-self:center; }
    }
    .sidebar-collapse-toggle { display:flex; align-items:center; justify-content:center; align-self:flex-end; width:34px; height:34px; border:1px solid #dbe3ef; border-radius:.65rem; color:#334155; background:#fff; }
    .sidebar-collapse-toggle:hover { color:#0f766e; border-color:#99f6e4; background:#f0fdfa; }
    .sidebar-collapse-toggle:focus-visible { outline:3px solid rgba(14,165,233,.3); outline-offset:2px; }
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
    {% include "partials/admin_sidebar.html" %}
    <main class="main-shell">
      <button type="button" id="mobile-nav-toggle" class="mobile-nav-toggle" aria-expanded="false" aria-controls="admin-sidebar"><i class="bi bi-list" aria-hidden="true"></i> Menu</button>
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
      <header class="site-directory-header">
        <div class="site-heading"><span class="site-heading-mark"><i class="bi bi-buildings-fill" aria-hidden="true"></i></span><div class="site-heading-copy"><div class="eyebrow">Site directory</div><h1>Site database</h1><p>Manage client sites and service locations <span class="site-count-pill"><i class="bi bi-buildings" aria-hidden="true"></i>{{ filtered_sites }} / {{ total_sites }}</span></p></div></div>
        <button type="button" class="btn btn-primary" id="open-client-create"><i class="bi bi-plus-lg me-1" aria-hidden="true"></i> Add site</button>
      </header>
      <nav class="site-status-tabs" aria-label="Filter sites by status">{% for status_key, status_label in [('all','All'),('active','Active'),('inactive','Inactive')] %}<a class="site-status-tab {{ 'active' if status_filter == status_key else '' }}" href="{{ url_for('admin_sites', status_filter=status_key, q=search_q or None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None) }}">{{ status_label }}<span class="site-status-tab-count">{% if status_key == 'all' %}{{ total_sites }}{% elif status_key == 'active' %}{{ active_sites_total }}{% else %}{{ inactive_sites }}{% endif %}</span></a>{% endfor %}</nav>
      <form method="get" class="site-filter-toolbar" role="search">
        <input type="hidden" name="status_filter" value="{{ status_filter }}">
        <input type="hidden" name="coverage" value="{{ coverage_filter }}">
        <label class="visually-hidden" for="site_search">Search sites</label>
        <div class="site-search-box"><i class="bi bi-search" aria-hidden="true"></i><input type="search" class="form-control" id="site_search" name="q" value="{{ search_q or '' }}" placeholder="Search site, company, contact, email, phone or address"></div>
        <label class="visually-hidden" for="site-manager-filter">Site manager</label>
        <select class="form-select" id="site-manager-filter" name="manager_id" aria-label="Site manager" onchange="this.form.requestSubmit()"><option value="">All site managers</option><option value="unassigned" {% if manager_filter == 'unassigned' %}selected{% endif %}>Unassigned manager</option>{% for manager in site_manager_filter_options %}<option value="{{ manager.id }}" {% if manager_filter == manager.id|string %}selected{% endif %}>{{ manager.name }}</option>{% endfor %}</select>
        <label class="visually-hidden" for="site-client-filter">Client</label>
        <select class="form-select" id="site-client-filter" name="client" aria-label="Client" onchange="this.form.requestSubmit()"><option value="">All clients</option>{% for client_name in client_filter_options %}<option value="{{ client_name }}" {% if client_filter == client_name %}selected{% endif %}>{{ client_name }}</option>{% endfor %}</select>
        {% if coverage_filter %}<span class="site-coverage-chip">{{ 'Scheduled this week' if coverage_filter == 'scheduled' else 'Without shifts this week' }}<a href="{{ url_for('admin_sites', status_filter=status_filter if status_filter != 'all' else None, q=search_q or None, manager_id=manager_filter or None, client=client_filter or None) }}" aria-label="Remove coverage filter" title="Remove filter"><i class="bi bi-x-lg" aria-hidden="true"></i></a></span>{% endif %}
        <details class="site-add-filter"><summary><i class="bi bi-sliders" aria-hidden="true"></i><span>+ Add filter</span><i class="bi bi-chevron-down" aria-hidden="true"></i></summary><div class="site-add-filter-menu"><a href="{{ url_for('admin_sites', status_filter=status_filter if status_filter != 'all' else None, q=search_q or None, manager_id=manager_filter or None, client=client_filter or None, coverage='scheduled') }}">Scheduled this week</a><a href="{{ url_for('admin_sites', status_filter=status_filter if status_filter != 'all' else None, q=search_q or None, manager_id=manager_filter or None, client=client_filter or None, coverage='unscheduled') }}">Without shifts this week</a></div></details>
        {% if search_q %}<a href="{{ url_for('admin_sites', status_filter=status_filter if status_filter != 'all' else None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None) }}" class="site-filter-clear" aria-label="Clear search" title="Clear search"><i class="bi bi-x-lg"></i></a>{% endif %}
        <button class="btn btn-primary" type="submit"><i class="bi bi-search me-1" aria-hidden="true"></i>Search</button>
      </form>
      <section class="card-surface p-0 overflow-hidden">
        <div class="table-responsive">
          <table class="table table-hover align-middle client-table mb-0">
            <thead><tr><th>Client</th><th>Contact</th><th>Service address</th>{% if not is_site_manager %}<th>Rate</th>{% endif %}<th>Shifts</th><th>Status</th>{% if not is_sales_manager %}<th class="text-end">Actions</th>{% endif %}</tr></thead>
            <tbody>
              {% for site in sites %}
              <tr class="site-row-clickable" data-row-url="{{ url_for('admin_site_detail', site_id=site.id, q=search_q or None, status_filter=status_filter if status_filter != 'all' else None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None, page=page if page > 1 else None) }}" tabindex="0" role="link" aria-label="Open site {{ (site.profile_company_name or site.name)|e }}">
                <td><div class="d-flex align-items-center gap-2">
                  {% if site.profile_image_path %}<img class="client-logo" src="{{ url_for('static', filename=site.profile_image_path) }}" alt="">
                  {% else %}<span class="client-logo client-logo-placeholder">{{ (site.profile_company_name or site.name)[:1]|upper }}</span>{% endif %}
                  <div class="client-main"><a class="client-detail-link" href="{{ url_for('admin_site_detail', site_id=site.id, q=search_q or None, status_filter=status_filter if status_filter != 'all' else None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None, page=page if page > 1 else None) }}"><strong>{{ site.profile_company_name or site.name }}</strong></a><small>{{ site.name }}</small></div>
                </div></td>
                <td><div class="client-main"><span>{{ site.profile_contact_name or site.contact_name or '?' }}</span><small>{{ site.profile_contact_email or site.contact_email or 'No email' }}</small></div></td>
                <td>{{ site.address or '?' }}</td>
                {% if not is_site_manager %}<td>{{ '%.2f'|format(site.profile_default_hourly_rate or site.hourly_rate or 0) }} ?</td>{% endif %}
                <td><span class="shift-count">{{ shift_counts.get(site.id, 0) }}</span></td>
                <td><form method="post" class="site-status-form"><input type="hidden" name="entity" value="site"><input type="hidden" name="action" value="set_status"><input type="hidden" name="id" value="{{ site.id }}"><input type="hidden" name="is_active" value="{{ '0' if site.is_active != 0 else '1' }}"><input type="hidden" name="redirect_q" value="{{ search_q }}"><input type="hidden" name="redirect_page" value="{{ page }}"><input type="hidden" name="redirect_status" value="{{ status_filter }}"><input type="hidden" name="redirect_manager" value="{{ manager_filter }}"><input type="hidden" name="redirect_client" value="{{ client_filter }}"><input type="hidden" name="redirect_coverage" value="{{ coverage_filter }}"><button class="site-status-button {{ 'is-active' if site.is_active != 0 else 'is-inactive' }}" type="submit"><i class="bi {{ 'bi-check-circle-fill' if site.is_active != 0 else 'bi-pause-circle-fill' }} me-1"></i>{{ 'Active' if site.is_active != 0 else 'Inactive' }}</button></form></td>
                {% if not is_sales_manager %}<td class="text-end"><a class="btn btn-sm btn-outline-primary" href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}"><i class="bi bi-clipboard-check me-1"></i>Inspection areas</a></td>{% endif %}
              </tr>
              {% else %}<tr><td colspan="{{ 6 if is_site_manager or is_sales_manager else 7 }}" class="text-center py-5"><div class="empty-clients"><i class="bi bi-buildings"></i><strong>No clients found</strong><span>Adjust your search or add a client to the database.</span><button type="button" class="btn btn-primary mt-2" id="open-client-create-empty">Add client</button></div></td></tr>{% endfor %}
            </tbody>
          </table>
        </div>
        {% if total_pages > 1 %}<div class="d-flex justify-content-between align-items-center flex-wrap gap-2 p-3 border-top"><span class="text-secondary small">Page {{ page }} of {{ total_pages }}</span><div class="d-flex gap-2">{% if has_prev %}<a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=prev_page, q=search_q or None, status_filter=status_filter if status_filter != 'all' else None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None) }}">Previous</a>{% endif %}{% if has_next %}<a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', page=next_page, q=search_q or None, status_filter=status_filter if status_filter != 'all' else None, manager_id=manager_filter or None, client=client_filter or None, coverage=coverage_filter or None) }}">Next</a>{% endif %}</div></div>{% endif %}
      </section>
      <div class="client-modal-backdrop" id="client-modal" aria-hidden="true">
        <section class="client-modal" role="dialog" aria-modal="true" aria-labelledby="client-modal-title">
          <header class="client-modal-header"><h2 id="client-modal-title">Add client</h2><button type="button" class="client-modal-close" id="close-client-modal" aria-label="Close">&times;</button></header>
          <form method="post" enctype="multipart/form-data" id="client-form">
            <input type="hidden" name="entity" value="site"><input type="hidden" name="action" id="client-action" value="create"><input type="hidden" name="id" id="client-id">
            <input type="hidden" name="redirect_q" value="{{ search_q }}"><input type="hidden" name="redirect_page" value="{{ page }}"><input type="hidden" name="redirect_status" value="{{ status_filter }}"><input type="hidden" name="redirect_manager" value="{{ manager_filter }}"><input type="hidden" name="redirect_client" value="{{ client_filter }}"><input type="hidden" name="redirect_coverage" value="{{ coverage_filter }}">
            <div class="client-modal-body">
              <section class="client-form-section"><h3>Client</h3><div class="row g-3">
                <div class="col-md-6"><label class="form-label" for="client-company">Company / client name <span class="text-danger">*</span></label><input class="form-control" id="client-company" name="profile_company_name" required></div>
                <div class="col-md-6"><label class="form-label" for="client-location">Service location name</label><input class="form-control" id="client-location" name="name" placeholder="Defaults to company name"></div>
                <div class="col-12"><label class="form-label" for="client-address">Service address</label><input class="form-control" id="client-address" name="address" autocomplete="street-address"></div>
                {% if is_main_admin %}<div class="col-md-6"><label class="form-label" for="client-manager">Assigned site manager</label><select class="form-select" id="client-manager" name="manager_employee_id"><option value="">Unassigned</option>{% for manager in site_managers %}<option value="{{ manager.id }}">{{ manager.name }}</option>{% endfor %}</select></div>{% endif %}
                <div class="col-md-6"><label class="form-label" for="client-logo">Logo / attachment</label><input class="form-control" type="file" id="client-logo" name="site_profile_image" accept="image/png,image/jpeg,image/gif,image/webp,image/heic"><small class="text-secondary">Upload a client logo or image.</small></div>
                <div class="col-md-6" id="existing-logo-wrap" hidden><label class="form-label d-block">Current logo</label><img id="existing-client-logo" class="client-logo" alt="Client logo"></div>
              </div></section>
              <section class="client-form-section"><h3>Contact</h3><div class="row g-3">
                <div class="col-md-4"><label class="form-label" for="client-contact">Contact person</label><input class="form-control" id="client-contact" name="profile_contact_name" autocomplete="name"></div>
                <div class="col-md-4"><label class="form-label" for="client-email">Email</label><input class="form-control" type="email" id="client-email" name="profile_contact_email" autocomplete="email"></div>
                <div class="col-md-4"><label class="form-label" for="client-phone">Phone</label><input class="form-control" type="tel" id="client-phone" name="profile_phone" autocomplete="tel"></div>
              </div></section>
              {% if not is_site_manager %}<section class="client-form-section"><h3>Billing and service</h3><div class="row g-3">
                <div class="col-12"><label class="form-label" for="client-billing">Billing address</label><input class="form-control" id="client-billing" name="profile_billing_address" autocomplete="billing street-address"></div>
                <div class="col-md-4"><label class="form-label" for="client-vat">VAT ID</label><input class="form-control" id="client-vat" name="profile_vat_id"></div>
                <div class="col-md-4"><label class="form-label" for="client-customer-id">Customer / tax ID</label><input class="form-control" id="client-customer-id" name="profile_tax_id"></div>
                <div class="col-md-4"><label class="form-label" for="client-rate">Hourly rate (?)</label><input class="form-control" type="number" min="0" step="0.01" id="client-rate" name="profile_default_hourly_rate"></div>
                <div class="col-md-6"><label class="form-label" for="client-contract-start">Contract start</label><input class="form-control" type="date" id="client-contract-start" name="contract_start_date"></div>
                <div class="col-md-6"><label class="form-label" for="client-contract-end">Contract end</label><input class="form-control" type="date" id="client-contract-end" name="contract_end_date"></div>
                <div class="col-md-6"><label class="form-label" for="client-contract-partner">Contract partner</label><input class="form-control" id="client-contract-partner" name="contract_partner_name"></div>
                <div class="col-md-6"><label class="form-label" for="client-contract-contact">Contract contact details</label><input class="form-control" id="client-contract-contact" name="contract_contact_details" placeholder="Phone, fax, or email"></div>
                <div class="col-md-6"><label class="form-label" for="client-active">Status</label><select class="form-select" id="client-active" name="is_active"><option value="1">Active</option><option value="0">Inactive</option></select></div>
              </div></section>{% endif %}
              <section class="client-form-section"><h3>Notes</h3><label class="visually-hidden" for="client-notes">Client notes</label><textarea class="form-control" rows="4" id="client-notes" name="profile_notes" placeholder="Add client details, access notes, or preferences"></textarea></section>
            </div>
            <footer class="client-modal-footer"><a class="btn btn-outline-secondary me-auto" href="{{ url_for('admin_sites') }}">Client database</a><button type="button" class="btn btn-outline-secondary" id="cancel-client-modal">Cancel</button>{% if not is_site_manager %}<button type="submit" name="profile_action" value="generate_contract" class="btn btn-outline-primary" id="client-contract-submit"><i class="bi bi-file-earmark-pdf me-1"></i>Save &amp; download contract</button>{% endif %}<button type="submit" class="btn btn-primary"><i class="bi bi-check-circle me-1"></i><span id="client-submit-label">Create client</span></button></footer>
          </form>
        </section>
      </div>
      <script>
        (() => {
          const modal = document.getElementById('client-modal');
          const form = document.getElementById('client-form');
          const setValue = (id, value) => { const field = document.getElementById(id); if (field) field.value = value || ''; };
          const open = (data = null) => {
            form.reset();
            document.getElementById('client-modal-title').textContent = isGerman ? (data ? 'Kunden bearbeiten' : 'Kunden hinzuf\u00fcgen') : (data ? 'Edit client' : 'Add client');
            document.getElementById('client-submit-label').textContent = isGerman ? (data ? '\u00c4nderungen speichern' : 'Kunden anlegen') : (data ? 'Save changes' : 'Create client');
            setValue('client-action', data ? 'update' : 'create');
            document.getElementById('existing-logo-wrap').hidden = true;
            if (data) {
              setValue('client-id', data.id); setValue('client-company', data.company || data.name); setValue('client-location', data.name);
              setValue('client-address', data.address); setValue('client-rate', data.defaultRate || data.rate);
              setValue('client-active', data.active); setValue('client-contact', data.contact); setValue('client-email', data.email);
              setValue('client-phone', data.phone); setValue('client-billing', data.billing); setValue('client-vat', data.vat);
              setValue('client-customer-id', data.customerId); setValue('client-notes', data.notes); setValue('client-contract-partner', data.contractPartner); setValue('client-contract-contact', data.contractContact);
              setValue('client-manager', data.managerId);
              const asDateInput = value => /^\d{2}-\d{2}-\d{4}$/.test(value || '') ? `${value.slice(6,10)}-${value.slice(3,5)}-${value.slice(0,2)}` : (value || '');
              setValue('client-contract-start', asDateInput(data.contractStart)); setValue('client-contract-end', asDateInput(data.contractEnd));
              if (data.logo) { document.getElementById('existing-logo-wrap').hidden = false; document.getElementById('existing-client-logo').src = `/static/${data.logo}`; }
            } else { setValue('client-id', ''); setValue('client-active', '1'); }
            document.getElementById('client-contract-submit').hidden = !data;
            modal.classList.add('is-open'); modal.setAttribute('aria-hidden', 'false'); document.body.classList.add('client-modal-open');
            window.setTimeout(() => document.getElementById('client-company').focus(), 40);
          };
          const close = () => { modal.classList.remove('is-open'); modal.setAttribute('aria-hidden', 'true'); document.body.classList.remove('client-modal-open'); };
          document.getElementById('open-client-create').addEventListener('click', () => open());
          document.getElementById('open-client-create-empty')?.addEventListener('click', () => open());
          document.getElementById('close-client-modal').addEventListener('click', close);
          document.getElementById('cancel-client-modal').addEventListener('click', close);
          modal.addEventListener('click', event => { if (event.target === modal) close(); });
          document.addEventListener('keydown', event => { if (event.key === 'Escape' && modal.classList.contains('is-open')) close(); });
          const clientToEdit = {{ client_to_edit_data|tojson }};
          if (clientToEdit) open(clientToEdit);
        })();
      </script>
    </main>
  </div>
  <div id="mobile-nav-backdrop" class="mobile-nav-backdrop"></div>
  <script>
    document.querySelectorAll('.site-row-clickable').forEach((row) => {
      row.addEventListener('click', (event) => {
        if (event.target.closest('a,button,input,select,textarea,label,form,[role="button"]')) return;
        window.location.assign(row.dataset.rowUrl);
      });
      row.addEventListener('keydown', (event) => {
        if ((event.key === 'Enter' || event.key === ' ') && event.target === row) {
          event.preventDefault();
          window.location.assign(row.dataset.rowUrl);
        }
      });
    });
    document.getElementById('year').textContent = new Date().getFullYear();
    (function() {
      const body = document.body;
      const collapseButton = document.getElementById('desktop-sidebar-toggle');
      const collapseIcon = collapseButton?.querySelector('i');
      const stateKey = 'pm-admin-sidebar-collapsed';
      const setCollapsed = (collapsed) => {
        body.classList.toggle('sidebar-collapsed', collapsed);
        collapseButton?.setAttribute('aria-expanded', String(!collapsed));
        collapseButton?.setAttribute('aria-label', collapsed ? 'Expand navigation' : 'Collapse navigation');
        collapseButton?.setAttribute('title', collapsed ? 'Expand navigation' : 'Collapse navigation');
        if (collapseIcon) collapseIcon.className = collapsed ? 'bi bi-chevron-bar-right' : 'bi bi-chevron-bar-left';
        try { localStorage.setItem(stateKey, collapsed ? '1' : '0'); } catch (_err) {}
      };
      try { setCollapsed(localStorage.getItem(stateKey) === '1'); } catch (_err) { setCollapsed(false); }
      collapseButton?.addEventListener('click', () => setCollapsed(!body.classList.contains('sidebar-collapsed')));
    })();
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

EMPLOYEE_DETAIL_TEMPLATE = """
<!doctype html>
<html lang="{{ current_lang }}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{{ employee.name }} - Employee profile</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root { --blue:#1877f2; --ink:#17213b; --muted:#667085; --line:#e5e8ee; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:#fff; font:14px/1.4 system-ui,-apple-system,Segoe UI,sans-serif; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:228px minmax(0,1fr); }
    .app-sidebar { background:#111b3d; color:#fff; padding:1.2rem .85rem; display:flex; flex-direction:column; gap:.4rem; }
    .app-sidebar a { color:#dce4ff; padding:.7rem .8rem; border-radius:.6rem; text-decoration:none; }
    .app-sidebar a:hover,.app-sidebar a.active { color:#fff; background:#26366c; }
    .app-sidebar .brand { padding:.5rem .8rem 1rem; color:#fff; font-weight:700; }
    .main { min-width:0; }
    .profile-header { display:flex; align-items:center; gap:1rem; min-height:82px; padding:1rem 1.5rem; border-bottom:1px solid var(--line); }
    .profile-header .employee-mark { width:64px; height:64px; }
    .profile-header .employee-identity { flex:0 1 auto; }
    .employee-identity strong { display:block; font-size:1.25rem; font-weight:600; }
    .profile-header-actions { display:flex; align-items:center; justify-content:flex-end; gap:.55rem; margin-left:auto; }
    .profile-header-actions form { margin:0; }
    .profile-header-actions .btn { min-width:48px; min-height:48px; border-radius:13px; font-size:.9rem; }
    .profile-header-actions .btn-icon { width:48px; padding:.5rem; }
    .profile-header-actions .btn-send-credentials { padding-inline:1rem; }
    .profile-header-actions .btn-danger-icon { color:#596273; background:#fff; border-color:#e2e6ed; }
    .profile-header-actions .btn-danger-icon:hover { color:#b42318; background:#fff6f5; border-color:#f0c7c3; }
    .profile-header-actions .btn:disabled { opacity:.45; cursor:not-allowed; }
    .employee-credentials-action { display:grid; justify-items:start; gap:.25rem; }
    .employee-credentials-reason { max-width:240px; color:#775313; font-size:.68rem; line-height:1.3; }
    .employee-credentials-reason a { color:#014D4E; font-weight:650; white-space:nowrap; }
    .profile-header-actions a[aria-disabled="true"] { opacity:.42; pointer-events:none; }
    .employee-mark { width:48px; height:48px; display:grid; place-items:center; flex:none; overflow:hidden; border:1px solid var(--line); border-radius:50%; color:#1479e8; background:#e3f3ff; font-size:1.15rem; font-weight:700; }
    .employee-mark img { width:100%; height:100%; object-fit:cover; }
    .employee-identity { min-width:0; flex:1; }
    .employee-identity small { display:block; color:#6b7280; }
    .profile-header .employee-identity strong { font-size:1.25rem; }
    .status-pill { display:inline-flex; padding:.22rem .65rem; border-radius:.4rem; color:#087443; background:#d1fae5; font-size:.75rem; font-weight:700; }
    .status-pill.inactive { color:#fff; background:#ef4444; }
    .profile-actions { display:flex; align-items:center; gap:.5rem; }
    .profile-actions a { text-decoration:none; }
    .profile-tabs { display:flex; gap:.2rem; overflow-x:auto; padding:.55rem 1rem; border-bottom:1px solid var(--line); white-space:nowrap; scrollbar-width:thin; }
    .profile-tabs a { padding:.6rem .8rem; border-radius:.55rem; color:#596273; font-weight:500; text-decoration:none; }
    .profile-tabs a.active,.profile-tabs a:hover { color:#fff; background:var(--blue); }
    .profile-content { display:grid; grid-template-columns:200px minmax(0,1fr); min-height:calc(100vh - 140px); }
    .section-nav { position:sticky; top:56px; align-self:start; max-height:calc(100dvh - 72px); overflow-y:auto; padding:1rem; border-right:1px solid var(--line); display:flex; flex-direction:column; gap:.25rem; }
    .section-nav a { padding:.65rem .75rem; border-radius:.55rem; color:#596273; text-decoration:none; }
    .section-nav a:hover,.section-nav a.active { background:#f2f4f7; color:#17213b; }
    .profile-sections { padding:1.25rem 2rem 3rem; min-width:0; }
    .profile-section { scroll-margin-top:1rem; max-width:1000px; padding:1rem 0 1.5rem; border-bottom:1px solid var(--line); }
    .employee-function-picker { position:relative; }
    .employee-function-toggle { display:flex; width:100%; justify-content:space-between; align-items:center; min-height:42px; border:1px solid #dce3ec; border-radius:.65rem; background:#fff; padding:.55rem .75rem; color:#263449; text-align:left; }
    .employee-function-menu { position:absolute; z-index:30; inset:calc(100% + .35rem) 0 auto; max-height:min(70vh,460px); overflow:auto; padding:.45rem; border:1px solid #dce3ec; border-radius:.7rem; background:#fff; box-shadow:0 12px 30px #14233724; }
    .employee-function-menu[hidden] { display:none; }
    .employee-function-option-row { display:flex; gap:.6rem; align-items:center; padding:.5rem .55rem; border-radius:.45rem; cursor:pointer; }
    .employee-function-option-row:hover { background:#f1f7f7; }
    .employee-function-menu-divider { margin:.45rem 0; border-top:1px solid #e5eaf0; }
    .employee-function-menu-heading { padding:.35rem .55rem; color:#758197; font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
    .employee-access-options { display:flex; flex-wrap:wrap; gap:.4rem; }
    .employee-access-options label { display:flex; align-items:center; gap:.35rem; padding:.38rem .5rem; border:1px solid #dce3ec; border-radius:.5rem; }
    .profile-section.employee-schedule-disclosure { max-width:none; padding:0; border:1px solid #e6eaf0; border-radius:14px; background:#fff; box-shadow:0 5px 16px rgba(25,39,61,.035); overflow:hidden; }
    .employee-schedule-summary { display:flex; align-items:center; justify-content:space-between; gap:1rem; min-height:76px; padding:1.2rem 1.3rem; border:0; border-radius:0; background:#fff; cursor:pointer; list-style:none; }
    .employee-schedule-summary::-webkit-details-marker { display:none; }
    .employee-schedule-summary > span { display:grid; gap:.2rem; }
    .employee-schedule-summary strong { color:#23314a; font-size:1rem; }
    .employee-schedule-summary small { color:#758197; font-size:.82rem; font-weight:400; }
    .employee-schedule-summary > i { color:#66748c; transition:transform .16s ease; }
    .employee-schedule-disclosure[open] .employee-schedule-summary { border-bottom:1px solid #e6eaf0; }
    .employee-schedule-disclosure[open] .employee-schedule-content { padding:1.2rem 1.3rem; }
    .employee-schedule-disclosure[open] .employee-schedule-summary > i { transform:rotate(180deg); }
    .employee-schedule-content { padding:1.2rem 1.3rem; }
    .profile-section h2 { font-size:1rem; margin:0 0 .25rem; }
    .section-description { color:var(--muted); margin:0 0 1rem; }
    .field-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
    .field { min-width:0; }
    .field-label { display:block; margin-bottom:.35rem; color:#687385; font-size:.8rem; }
    .field-value { min-height:42px; padding:.65rem .8rem; border:1px solid #e4e7ec; border-radius:.65rem; background:#fff; overflow-wrap:anywhere; }
    .field-value.multiline { min-height:86px; white-space:pre-wrap; }
    .data-card { padding:1rem; border:1px solid var(--line); border-radius:.8rem; background:#fff; }
    .employee-document-upload { max-width:760px; margin-bottom:1rem; }
    .employee-document-list { display:grid; gap:.65rem; }
    .employee-document-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
    .employee-document-info { display:flex; align-items:center; gap:.75rem; min-width:0; }
    .employee-document-info > i { display:grid; place-items:center; flex:none; width:40px; height:40px; border-radius:11px; color:#014D4E; background:#e8f3f2; font-size:1.15rem; }
    .employee-document-info > div { display:grid; min-width:0; }
    .employee-document-info strong { overflow-wrap:anywhere; }
    .employee-document-info small { color:#758197; }
    .data-table { width:100%; border-collapse:collapse; }
    .data-table th,.data-table td { text-align:left; padding:.7rem .65rem; border-bottom:1px solid var(--line); vertical-align:top; }
    .data-table th { color:#687385; font-size:.76rem; font-weight:600; }
    .data-table a { color:var(--blue); text-decoration:none; }
    .employee-week-toolbar { display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; margin:.5rem 0 .8rem; }
    .employee-week-toolbar .btn { min-height:40px; }
    .employee-week-range { display:inline-flex; align-items:center; gap:.55rem; min-height:40px; padding:.45rem .8rem; border:1px solid #e1e5eb; border-radius:.7rem; color:#505c70; background:#f7f8fa; font-weight:600; }
    .employee-calendar-scroll { overflow:auto; max-width:100%; border:1px solid #e1e5eb; border-radius:.8rem; background:#fff; }
    .employee-calendar { min-width:790px; }
    .employee-calendar-head,.employee-calendar-body { display:grid; grid-template-columns:72px repeat(7,minmax(0,1fr)); }
    .employee-calendar-head { position:sticky; top:0; z-index:4; background:#fafafa; }
    .employee-calendar-head > div { min-width:0; display:grid; place-content:center; min-height:62px; padding:.35rem .15rem; border-right:1px solid #e2e4e8; border-bottom:1px solid #dfe2e7; color:#81858d; text-align:center; font-size:.86rem; font-weight:650; }
    .employee-calendar-head > div:first-child { background:#fafafa; }
    .employee-calendar-head > div.is-today { color:#014D4E; background:#fff; }
    .employee-calendar-head small { font-size:.8rem; font-weight:600; }
    .employee-calendar-time-axis { display:grid; grid-template-rows:42px repeat(19,52px); background:#fff; }
    .employee-calendar-time-axis > div { display:flex; align-items:flex-start; justify-content:flex-end; padding:.55rem .4rem 0 0; border-right:1px solid #e2e4e8; border-bottom:1px solid #e5e7eb; color:#92959b; font-size:.8rem; white-space:nowrap; }
    .employee-calendar-time-axis > div:first-child { align-items:center; padding:0 .4rem 0 0; }
    .employee-calendar-day-column { position:relative; height:1030px; min-width:0; border-right:1px solid #e2e4e8; background-color:#fff; background-image:linear-gradient(to bottom, transparent 41px, #e5e7eb 42px, transparent 43px); background-size:100% 52px; background-repeat:repeat-y; }
    .employee-calendar-day-column.is-today { background-color:#fffbe2; }
    .employee-calendar-all-day { height:42px; border-bottom:1px solid #dfe2e7; background:rgba(255,255,255,.4); }
    .employee-calendar-event { position:absolute; right:3px; left:3px; z-index:2; min-height:44px; overflow:hidden; padding:.32rem .4rem; border:1px solid rgba(1,77,78,.22); border-left:3px solid #014D4E; border-radius:7px; color:#23304a; background:#f0f8f7; box-shadow:0 2px 5px rgba(20,35,55,.08); font-size:.72rem; line-height:1.25; }
    .employee-calendar-event.is-all-day { min-height:0; padding:.18rem .3rem; font-size:.65rem; }
    .employee-calendar-event.is-all-day time { display:none; }
    .employee-calendar-event time { display:block; margin-bottom:.18rem; color:#7b8290; font-size:.67rem; white-space:nowrap; }
    .employee-calendar-event strong,.employee-calendar-event small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .employee-calendar-event small { margin-top:.15rem; color:#687385; }
    .empty-state { color:var(--muted); padding:1rem; border:1px dashed #cbd5e1; border-radius:.7rem; }
    .credential-fields { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.7rem; }
    .credential-send-help { display:flex; align-items:flex-start; gap:.5rem; margin:-.35rem 0 1rem; padding:.7rem .8rem; border:1px solid #f1dfb4; border-radius:10px; color:#775313; background:#fff9e9; font-size:.82rem; }
    .credential-fields label { display:block; margin-bottom:.3rem; font-size:.78rem; color:#64748b; }
    .credential-fields input { width:100%; min-width:0; padding:.55rem .65rem; border:1px solid #dce3ec; border-radius:.55rem; }
    .mobile-menu { display:none; }
    @media(max-width:900px) { .app-shell { grid-template-columns:1fr; } .app-sidebar { display:none; } .profile-content { grid-template-columns:160px minmax(0,1fr); } .profile-sections { padding:1rem; } }
    @media(max-width:900px) { .profile-header { padding:.75rem 1rem; } .profile-header-actions { gap:.35rem; } .profile-header-actions .btn-send-credentials span { display:none; } }
    @media(max-width:620px) { .profile-header { padding:.7rem; flex-wrap:wrap; gap:.6rem; } .profile-header .employee-mark { width:48px; height:48px; } .employee-identity strong { font-size:1rem; } .profile-header-actions { width:100%; justify-content:space-between; } .profile-header-actions .btn { min-width:42px; min-height:42px; } .profile-header-actions .btn-icon { width:42px; } .profile-tabs { padding:.5rem; } .profile-content { grid-template-columns:1fr; } .section-nav { position:sticky; top:40px; z-index:40; align-self:start; max-height:none; flex-direction:row; overflow-x:auto; overflow-y:hidden; border-right:0; border-bottom:1px solid var(--line); background:#fff; padding:.4rem; white-space:nowrap; } .section-nav a { padding:.5rem .65rem; } .field-grid,.credential-fields { grid-template-columns:1fr; } .profile-sections { padding:.7rem .85rem 2rem; } .data-table { min-width:650px; } .table-wrap { overflow-x:auto; } .employee-document-row { align-items:flex-start; flex-direction:column; } }
    /* Refined employee detail workspace */
    .main { min-height:100vh; background:#f5f7fa; }
    .profile-header { position:relative; gap:1rem; min-height:94px; padding:1rem 1.5rem; background:#fff; border-bottom:1px solid #e7ebf0; box-shadow:0 4px 16px rgba(22,35,57,.035); }
    .profile-header .employee-mark { width:58px; height:58px; border:0; color:#014D4E; background:#e5f1ef; box-shadow:0 0 0 4px #f1f7f6; }
    .profile-header .employee-identity { display:grid; gap:.2rem; }
    .profile-header .employee-identity strong { color:#172a3b; font-size:1.18rem; font-weight:700; letter-spacing:-.025em; }
    .profile-header .employee-identity small { color:#748197; font-size:.82rem; }
    .profile-header .status-pill { padding:.3rem .7rem; border-radius:999px; color:#075e53; background:#e1f4ed; font-size:.74rem; letter-spacing:.01em; }
    .profile-header .status-pill.inactive { color:#fff; background:#ef4444; }
    .profile-header-actions { gap:.45rem; }
    .profile-header-actions .btn { min-height:42px; min-width:42px; border-radius:11px; }
    .profile-header-actions .btn-icon { width:42px; }
    .profile-tabs { position:sticky; top:0; z-index:30; align-items:center; gap:.35rem; padding:.65rem 1.25rem; background:rgba(255,255,255,.97); border-bottom:1px solid #e7ebf0; box-shadow:0 3px 12px rgba(25,39,61,.045); }
    .profile-tabs a { padding:.58rem .85rem; border-radius:9px; color:#667287; font-size:.84rem; font-weight:600; transition:background .15s,color .15s; }
    .profile-tabs a.active,.profile-tabs a:hover { color:#014D4E; background:#e8f3f2; }
    .profile-content { grid-template-columns:208px minmax(0,1fr); min-height:calc(100vh - 150px); background:#f5f7fa; }
    .section-nav { top:58px; max-height:calc(100dvh - 78px); padding:.85rem .7rem; border-right:1px solid #e8ecf1; background:#f9fafc; }
    .section-nav a { padding:.62rem .75rem; border-radius:9px; color:#667287; font-size:.84rem; font-weight:550; transition:background .15s,color .15s; }
    .section-nav a:hover,.section-nav a.active { color:#014D4E; background:#e8f3f2; }
    .profile-sections { display:grid; align-content:start; gap:.9rem; padding:1.1rem 1.35rem 2.5rem; }
    .employee-inline-edit-form { display:grid; gap:.9rem; }
    .profile-edit-input { min-height:44px; border-color:#e5e9ef; border-radius:9px; color:#26364d; background:#fbfcfd; }
    .profile-edit-input:focus { border-color:#7fb5b3; background:#fff; box-shadow:0 0 0 .2rem rgba(1,77,78,.1); }
    .employee-inline-save { display:flex; justify-content:flex-end; padding-top:1rem; border-top:1px solid #edf0f4; }
    .profile-sections > [data-profile-panel][hidden], .section-nav[hidden] { display:none !important; }
    .profile-section { width:100%; max-width:none; margin:0; padding:1.2rem 1.3rem; border:1px solid #e6eaf0; border-radius:14px; background:#fff; box-shadow:0 5px 16px rgba(25,39,61,.035); }
    .profile-section h2 { margin:0 0 .3rem; color:#1d2d44; font-size:1.02rem; font-weight:700; letter-spacing:-.015em; }
    .section-description { margin-bottom:1rem; color:#7a879a; font-size:.84rem; }
    .field-grid { gap:.85rem; }
    .field-label { color:#77849a; font-size:.76rem; font-weight:600; }
    .field-value { min-height:44px; padding:.68rem .8rem; border-color:#e5e9ef; border-radius:9px; color:#26364d; background:#fbfcfd; }
    .profile-section .data-card { border-color:#e6eaf0; border-radius:12px; }
    .employee-document-row { box-shadow:0 2px 8px rgba(25,39,61,.025); }
    .employee-schedule-summary { border-color:#e6eaf0; border-radius:12px; box-shadow:0 4px 14px rgba(25,39,61,.035); }
    .employee-schedule-summary strong { color:#1d2d44; }
    .employee-calendar-scroll { border-color:#e5e9ef; box-shadow:0 3px 12px rgba(25,39,61,.025); }
    .employee-calendar-head > div { background:#f8fafb; }
    .employee-calendar-event { box-shadow:0 2px 7px rgba(25,39,61,.08); }
    .credential-fields input { min-height:40px; border-color:#e1e6ed; border-radius:9px; }
    .profile-section .btn-outline-primary { color:#014D4E; border-color:#c7ddda; }
    @media(max-width:900px) {
      .profile-header { padding:.85rem 1rem; }
      .profile-content { grid-template-columns:170px minmax(0,1fr); }
      .profile-sections { padding:1rem; }
    }
    @media(max-width:620px) {
      .profile-header { padding:.7rem .8rem; }
      .profile-header .employee-mark { width:46px; height:46px; }
      .profile-header .employee-identity strong { font-size:1rem; }
      .profile-tabs { gap:.15rem; padding:.5rem; }
      .profile-tabs a { padding:.5rem .6rem; font-size:.78rem; }
      .profile-content { display:block; }
      .section-nav { top:40px; padding:.35rem .45rem; border-right:0; border-bottom:1px solid #e6eaf0; background:rgba(255,255,255,.97); box-shadow:0 3px 10px rgba(25,39,61,.04); }
      .section-nav a { padding:.48rem .6rem; font-size:.77rem; }
      .profile-sections { gap:.7rem; padding:.8rem .65rem 1.5rem; }
      .profile-section { padding:1rem; border-radius:12px; }
      .profile-section.employee-schedule-disclosure { padding:0; }
      .employee-schedule-summary { padding:1rem; }
      .employee-schedule-disclosure[open] .employee-schedule-content { padding:1rem; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    {% include "partials/admin_sidebar.html" %}
    <main class="main">
      <header class="profile-header">{% if employee.profile_image_path %}<span class="employee-mark"><img src="{{ url_for('static', filename=employee.profile_image_path) }}" alt=""></span>{% else %}<span class="employee-mark">{{ employee.name[:1]|upper }}</span>{% endif %}<div class="employee-identity"><strong>{{ employee.name }}</strong><small>{{ employee_staff_functions|join(', ') }}</small></div><span class="status-pill {{ 'inactive' if (employee.worker_status or ('active' if employee.is_active else 'passive')) != 'active' else '' }}">{{ (employee.worker_status or ('active' if employee.is_active else 'passive'))|capitalize }}</span><div class="profile-header-actions">
        {% if is_main_admin %}<div class="employee-credentials-action"><form method="post" action="{{ url_for('admin_employees') }}"><input type="hidden" name="action" value="credentials_email"><input type="hidden" name="id" value="{{ employee.id }}"><input type="hidden" name="return_to" value="{{ url_for('admin_employee_detail', employee_id=employee.id) }}"><button class="btn btn-outline-secondary btn-send-credentials" type="submit" {% if credential_email_reason %}disabled title="{{ credential_email_reason }}"{% endif %}><i class="bi bi-send-fill"></i><span>Send sign-in details</span></button></form>{% if credential_email_reason %}<small class="employee-credentials-reason">{{ credential_email_reason }} <a href="#account">Fix</a></small>{% endif %}</div>{% endif %}
        {% if not is_sales_manager %}<form method="post" action="{{ url_for('admin_employees') }}" data-confirm="Delete {{ employee.name|e }}? This cannot be undone." onsubmit="return confirm(this.dataset.confirm);"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ employee.id }}"><input type="hidden" name="return_to" value="{{ url_for('admin_employees') }}"><button class="btn btn-icon btn-danger-icon" type="submit" title="Delete employee" aria-label="Delete employee"><i class="bi bi-trash3"></i></button></form>{% endif %}
        <a class="btn btn-icon btn-outline-secondary" href="{{ url_for('admin_employees') }}" title="Close employee" aria-label="Close employee"><i class="bi bi-x-lg"></i></a>
      </div></header>
      {% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="px-3 pt-3">{% for category, message in messages %}<div class="alert alert-{{ 'success' if category == 'success' else 'warning' if category == 'warning' else 'info' }} py-2 mb-2">{{ message }}</div>{% endfor %}</div>{% endif %}{% endwith %}
      <nav class="profile-tabs" aria-label="Employee pages"><a class="active" data-profile-tab="information" href="#information">Information</a>{% if is_cleaner %}<a data-profile-tab="schedule" href="#schedule">Schedule</a>{% endif %}{% if not is_site_manager and not is_sales_manager %}<a data-profile-tab="contract" href="#contract">Contract</a>{% endif %}{% if not is_sales_manager %}<a data-profile-tab="documents" href="#documents">Documents</a>{% endif %}</nav>
      <div class="profile-content">
        <nav class="section-nav" aria-label="Employee information sections"><a class="active" href="#general">General</a><a href="#contacts">Contacts</a><a href="#employment">Employment</a>{% if not is_site_manager and not is_sales_manager %}<a href="#contract">Contract</a>{% endif %}{% if not is_sales_manager %}<a href="#account">Platform access</a>{% endif %}{% if is_cleaner %}<a href="#schedule">Schedule</a><a href="#other">Activity</a>{% endif %}{% if not is_sales_manager %}<a href="#documents">Documents</a>{% endif %}</nav>
        <div class="profile-sections">
          <form method="post" enctype="multipart/form-data" action="{{ url_for('admin_employee_detail', employee_id=employee.id) }}" class="employee-inline-edit-form" data-profile-panel="information"><input type="hidden" name="action" value="update_profile">
          <section class="profile-section" id="information"><div id="general"><h2>General</h2><p class="section-description">Edit fields here, then save your changes below.</p></div><div class="field-grid"><label class="field"><span class="field-label">Full name</span><input class="form-control profile-edit-input" name="name" value="{{ employee.name|e }}" required></label><label class="field"><span class="field-label">Role</span><input class="form-control profile-edit-input" name="role" value="{{ (employee.role or '')|e }}"></label><label class="field"><span class="field-label">Status</span><select class="form-select profile-edit-input" name="worker_status"><option value="active" {% if employee.worker_status == 'active' or not employee.worker_status and employee.is_active %}selected{% endif %}>Active</option><option value="passive" {% if employee.worker_status == 'passive' or not employee.worker_status and not employee.is_active %}selected{% endif %}>Passive</option></select></label><div class="field"><span class="field-label">Employee record ID</span><div class="field-value">#{{ employee.id }}</div></div><label class="field"><span class="field-label">Profile photo</span><input class="form-control profile-edit-input" type="file" name="profile_image" accept="image/png,image/jpeg,image/gif,image/webp"></label></div></section>
          <section class="profile-section" id="contacts"><h2>Contacts</h2><p class="section-description">Update personal contact details.</p><div class="field-grid"><div class="field"><span class="field-label">Login email</span><div class="field-value">{% if not is_sales_manager and employee.login_email %}<a href="mailto:{{ employee.login_email }}">{{ employee.login_email }}</a>{% else %}-{% endif %}</div><small class="text-secondary">Manage sign-in email in Account access.</small></div><label class="field"><span class="field-label">Phone</span><input class="form-control profile-edit-input" type="tel" name="profile_phone" value="{{ (employee.profile_phone or '')|e }}"></label><label class="field"><span class="field-label">Address</span><input class="form-control profile-edit-input" name="profile_address" value="{{ (employee.profile_address or '')|e }}"></label><label class="field"><span class="field-label">Postal code</span><input class="form-control profile-edit-input" name="profile_zip_code" value="{{ (employee.profile_zip_code or '')|e }}"></label><label class="field"><span class="field-label">City</span><input class="form-control profile-edit-input" name="profile_city" value="{{ (employee.profile_city or '')|e }}"></label></div></section>
          <section class="profile-section" id="employment"><h2>Employment</h2><p class="section-description">Update department, branch, and work information.</p><div class="field-grid"><label class="field"><span class="field-label">Branch office</span><select class="form-select profile-edit-input" name="branch"><option value="Wien" {% if (employee.branch or 'Wien') == 'Wien' %}selected{% endif %}>Wien</option><option value="Graz" {% if employee.branch == 'Graz' %}selected{% endif %}>Graz</option></select></label><label class="field"><span class="field-label">Work type</span><select class="form-select profile-edit-input" name="profile_work_type"><option value="Teilzeit" {% if employee.profile_work_type == 'Teilzeit' %}selected{% endif %}>Part-time</option><option value="Vollzeit" {% if employee.profile_work_type == 'Vollzeit' %}selected{% endif %}>Full-time</option><option value="Intern" {% if employee.profile_work_type in ['Geringfügige','Intern'] %}selected{% endif %}>Intern</option></select></label><label class="field"><span class="field-label">Weekly hours</span><input class="form-control profile-edit-input" name="profile_working_hours" value="{{ (employee.profile_working_hours or '')|e }}"></label>{% if is_main_admin %}<label class="field"><span class="field-label">Hourly pay</span><input class="form-control profile-edit-input" name="profile_euros_per_hour" inputmode="decimal" value="{{ (employee.profile_euros_per_hour or '')|e }}"></label><label class="field"><span class="field-label">Pay group type</span><select class="form-select profile-edit-input" name="profile_group_type"><option value="Lohngruppe" {% if employee.profile_group_type == 'Lohngruppe' %}selected{% endif %}>Pay group</option><option value="Verwendungsgruppe" {% if employee.profile_group_type == 'Verwendungsgruppe' %}selected{% endif %}>Usage group</option></select></label><label class="field"><span class="field-label">Group number</span><input class="form-control profile-edit-input" name="profile_group_number" value="{{ (employee.profile_group_number or '')|e }}"></label>{% endif %}</div><div class="employee-inline-save"><button class="btn btn-primary" type="submit"><i class="bi bi-check2 me-1"></i>Save profile</button></div></section>
          </form>
          {% if not is_site_manager and not is_sales_manager %}<section class="profile-section" id="contract" data-profile-panel="contract"><h2>Contract</h2><p class="section-description">Update the contract period and download the employee contract.</p>{% if is_main_admin %}<form method="post" action="{{ url_for('admin_employee_detail', employee_id=employee.id) }}" class="employee-inline-edit-form"><input type="hidden" name="action" value="update_contract"><div class="field-grid"><label class="field"><span class="field-label">Contract start</span><input class="form-control profile-edit-input" type="date" name="profile_contract_start_date" value="{{ (employee.profile_contract_start_date or '')|e }}"></label><label class="field"><span class="field-label">Contract end</span><input class="form-control profile-edit-input" type="date" name="profile_contract_end_date" value="{{ (employee.profile_contract_end_date or '')|e }}"></label></div><div class="employee-inline-save"><button class="btn btn-primary" type="submit"><i class="bi bi-check2 me-1"></i>Save contract dates</button></div></form>{% else %}<div class="field-grid"><div class="field"><span class="field-label">Contract start</span><div class="field-value">{{ employee.profile_contract_start_date or '-' }}</div></div><div class="field"><span class="field-label">Contract end</span><div class="field-value">{{ employee.profile_contract_end_date or '-' }}</div></div></div>{% endif %}<a class="btn btn-outline-primary mt-3" href="{{ url_for('admin_employee_docx', employee_id=employee.id) }}"><i class="bi bi-file-earmark-word me-1"></i>Download employee contract</a><p class="small text-secondary mt-2 mb-0">This uses the existing employee contract template.</p></section>{% endif %}
          {% if not is_sales_manager %}<section class="profile-section" id="account" data-profile-panel="information"><h2>Platform access</h2><p class="section-description">Functions and sign-in permissions for this employee.</p>
            <form method="post" action="{{ url_for('admin_employee_detail', employee_id=employee.id) }}" class="employee-inline-edit-form data-card mb-3"><input type="hidden" name="action" value="update_staff_access"><label class="field-label" for="detail-functions-toggle">Functions</label><div class="employee-function-picker"><button class="employee-function-toggle" type="button" id="detail-functions-toggle" aria-expanded="false" aria-controls="detail-functions-menu"><span id="detail-functions-summary">{{ employee_staff_functions|join(', ') }}</span><i class="bi bi-chevron-down"></i></button><div class="employee-function-menu" id="detail-functions-menu" hidden>{% if is_main_admin %}<div class="employee-function-menu-heading">System access</div><div class="employee-access-options" role="radiogroup" aria-label="System access">{% for role_value, role_label in [('none','No system access'),('employee','Cleaner'),('site_manager','Site manager'),('sales_manager','Sales manager'),('admin','Admin')] %}<label><input class="form-check-input detail-access-option" type="radio" name="detail_access_picker" value="{{ role_value }}" {% if role_value == 'none' and not employee.has_platform_access or role_value == employee.access_role and employee.has_platform_access %}checked{% endif %}><span>{{ role_label }}</span></label>{% endfor %}</div><div class="employee-function-menu-divider"></div>{% endif %}{% for function in employee_staff_types %}<label class="employee-function-option-row"><input class="form-check-input detail-function-option" type="checkbox" value="{{ function }}" {% if function in employee_staff_functions %}checked{% endif %}><span>{{ function }}</span></label>{% endfor %}</div></div><input type="hidden" name="staff_functions" id="detail-staff-functions" value='{{ employee_staff_functions|tojson }}'><input type="hidden" name="staff_type" value="{{ employee.staff_type or 'Cleaner' }}"><input type="hidden" name="access_role" id="detail-access-role" value="{{ employee.access_role or 'employee' }}"><p class="small text-secondary mt-2">Select all functions this person performs. Multiple functions are supported.</p>{% if is_main_admin %}<div class="field-grid mt-3"><label class="field"><span class="field-label">Login email</span><input class="form-control" type="email" name="login_email" value="{{ employee.login_email or '' }}"></label><label class="field"><span class="field-label">Platform sign-in</span><span><input type="checkbox" id="detail-platform-access" name="has_platform_access" value="1" {% if employee.has_platform_access %}checked{% endif %}> Enabled</span></label></div>{% endif %}<div class="employee-inline-save"><button class="btn btn-primary" type="submit"><i class="bi bi-check2 me-1"></i>Save platform access</button></div></form>
            {% if is_main_admin %}{% if credential_email_reason %}<div class="credential-send-help"><i class="bi bi-info-circle"></i><span>{{ credential_email_reason }}</span></div>{% endif %}<div class="field-grid mb-3"><div class="field"><span class="field-label">Login code</span><div class="field-value">{{ employee.login_code or '-' }}</div></div><div class="field"><span class="field-label">Current PIN</span><div class="field-value">{{ employee.login_pin_plain or '-' }}</div></div></div>
            <form method="post" action="{{ url_for('admin_employees') }}" class="data-card mb-3"><input type="hidden" name="action" value="credentials_update"><input type="hidden" name="id" value="{{ employee.id }}"><input type="hidden" name="return_to" value="{{ url_for('admin_employee_detail', employee_id=employee.id) }}"><div class="credential-fields"><div><label for="login-email">Login email</label><input id="login-email" type="email" name="login_email" value="{{ employee.login_email or '' }}"></div><div><label for="login-code">Login code</label><input id="login-code" name="login_code" value="{{ employee.login_code or '' }}" required></div><div><label for="login-pin">New 4-digit PIN</label><input id="login-pin" name="login_pin" inputmode="numeric" maxlength="4" pattern="[0-9]{4}" placeholder="Leave blank to keep current"></div></div><button class="btn btn-sm btn-outline-primary mt-3" type="submit">Save sign-in details</button></form>
            <form method="post" action="{{ url_for('admin_employees') }}"><input type="hidden" name="action" value="credentials_share"><input type="hidden" name="id" value="{{ employee.id }}"><input type="hidden" name="return_to" value="{{ url_for('admin_employee_detail', employee_id=employee.id) }}"><button class="btn btn-sm btn-outline-secondary" type="submit"><i class="bi bi-share me-1"></i>Prepare sign-in details to share</button></form>
          {% endif %}</section>{% endif %}
          {% if is_cleaner %}<section class="profile-section" id="other" data-profile-panel="information"><h2>Activity</h2><p class="section-description">Employee shift activity.</p><div class="field"><span class="field-label">Total shifts</span><div class="field-value">{{ shift_count }}</div></div></section>{% endif %}
          {% if not is_sales_manager %}<section class="profile-section" id="documents" data-profile-panel="documents"><h2>Documents</h2><p class="section-description">Upload and keep employee-related documents in one place.</p><form method="post" enctype="multipart/form-data" class="data-card employee-document-upload"><label class="form-label" for="employee-document-file">Choose a document</label><input class="form-control" type="file" id="employee-document-file" name="employee_document" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" required><button class="btn btn-primary mt-3" type="submit"><i class="bi bi-upload me-1"></i>Upload document</button></form><div class="employee-document-list">{% for document in documents %}<div class="data-card employee-document-row"><div class="employee-document-info"><i class="bi bi-file-earmark-text"></i><div><strong>{{ document.original_filename }}</strong><small>Uploaded {{ document.uploaded_at.strftime('%d.%m.%Y') }}</small></div></div><a class="btn btn-sm btn-outline-primary" href="{{ url_for('admin_employee_document_download', employee_id=employee.id, document_id=document.id) }}"><i class="bi bi-download"></i><span>Download</span></a><form method="post" onsubmit="return confirm('Delete this employee document?')"><input type="hidden" name="action" value="delete_employee_document"><input type="hidden" name="document_id" value="{{ document.id }}"><button class="btn btn-sm btn-outline-danger" type="submit" aria-label="Delete employee document" title="Delete document"><i class="bi bi-trash3"></i><span>Delete</span></button></form></div>{% else %}<div class="empty-state">No employee documents have been uploaded yet.</div>{% endfor %}</div></section>{% endif %}
          {% if is_cleaner %}<details class="profile-section employee-schedule-disclosure" id="schedule" data-profile-panel="schedule"><summary class="employee-schedule-summary"><span><strong>Schedule</strong><small>Weekly shifts in a calendar view.</small></span><i class="bi bi-chevron-down"></i></summary><div class="employee-schedule-content"><div class="employee-week-toolbar"><a class="btn btn-outline-secondary" href="{{ previous_week_url }}" aria-label="Previous week" title="Previous week"><i class="bi bi-chevron-left"></i></a><a class="btn btn-outline-secondary" href="{{ current_week_url }}">Today</a><a class="btn btn-outline-secondary" href="{{ next_week_url }}" aria-label="Next week" title="Next week"><i class="bi bi-chevron-right"></i></a><span class="employee-week-range"><i class="bi bi-calendar3"></i>{{ schedule_week_range }}</span></div><div class="employee-calendar-scroll"><div class="employee-calendar"><div class="employee-calendar-head"><div></div>{% for day in schedule_days %}<div class="{{ 'is-today' if day.is_today else '' }}"><span>{{ day.weekday }}</span><small>{{ day.day_label }}</small></div>{% endfor %}</div><div class="employee-calendar-body"><div class="employee-calendar-time-axis"><div>All day</div>{% for hour in schedule_hour_rows %}<div>{{ '%02d'|format(hour) }}:00</div>{% endfor %}</div>{% for day in schedule_days %}<div class="employee-calendar-day-column {{ 'is-today' if day.is_today else '' }}"><div class="employee-calendar-all-day"></div>{% for hour in schedule_hour_rows %}<div></div>{% endfor %}{% for event in day.events %}<article class="employee-calendar-event {{ 'is-all-day' if event.all_day else '' }}" style="top:{{ event.top_px }}px;height:{{ event.height_px }}px" title="{{ event.site_name }} · {{ event.time_window }}"><time>{{ event.time_window }}</time><strong>{{ event.site_name }}</strong>{% if event.instructions %}<small>{{ event.instructions }}</small>{% endif %}</article>{% endfor %}</div>{% endfor %}</div></div></div>{% if not shifts %}<div class="small text-secondary mt-2">No shifts scheduled this week.</div>{% endif %}</div></details>{% endif %}
        </div>
      </div>
    </main>
  </div>
  <script>
    (() => {
      const toggle=document.getElementById('detail-functions-toggle');
      const menu=document.getElementById('detail-functions-menu');
      if(!toggle||!menu)return;
      const options=[...menu.querySelectorAll('.detail-function-option')];
      const hidden=document.getElementById('detail-staff-functions');
      const summary=document.getElementById('detail-functions-summary');
      const accessOptions=[...menu.querySelectorAll('.detail-access-option')];
      const accessHidden=document.getElementById('detail-access-role');
      const platformAccess=document.getElementById('detail-platform-access');
      const sync=()=>{
        let selected=options.filter(option=>option.checked).map(option=>option.value);
        if(!selected.length){options[0].checked=true;selected=[options[0].value];}
        hidden.value=JSON.stringify(selected);
        const access=accessOptions.find(option=>option.checked);
        if(access&&accessHidden)accessHidden.value=access.value==='none'?'employee':access.value;
        if(platformAccess&&access)platformAccess.checked=access.value!=='none';
        summary.textContent=[...selected,access?.parentElement.querySelector('span').textContent||'No system access'].join(', ');
      };
      const chooseAccess=role=>{accessOptions.forEach(option=>{option.checked=option.value===role;});sync();};
      toggle.addEventListener('click',()=>{menu.hidden=!menu.hidden;toggle.setAttribute('aria-expanded',String(!menu.hidden));});
      options.forEach(option=>option.addEventListener('change',()=>{
        const managerFunction=option.checked&&option.value==='Site manager'?'site_manager':option.checked&&option.value==='Sales manager'?'sales_manager':null;
        if(managerFunction&&accessOptions.some(accessOption=>accessOption.value===managerFunction))chooseAccess(managerFunction);else sync();
      }));accessOptions.forEach(option=>option.addEventListener('change',()=>chooseAccess(option.value)));
      platformAccess?.addEventListener('change',()=>chooseAccess(platformAccess.checked?'employee':'none'));sync();
      document.addEventListener('click',event=>{if(!event.target.closest('#account .employee-function-picker')){menu.hidden=true;toggle.setAttribute('aria-expanded','false');}});
    })();
  </script>
  <script>
    (() => {
      const tabs = Array.from(document.querySelectorAll('.profile-tabs [data-profile-tab]'));
      const panels = Array.from(document.querySelectorAll('[data-profile-panel]'));
      const sectionNav = document.querySelector('.section-nav');
      const schedule = document.getElementById('schedule');
      if (!tabs.length || !panels.length) return;
      const panelForHash = (hash) => {
        const target = hash ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
        return target?.closest('[data-profile-panel]') || document.getElementById('information');
      };
      const activate = (panelName, hash, shouldScroll) => {
        tabs.forEach((tab) => {
          const active = tab.dataset.profileTab === panelName;
          tab.classList.toggle('active', active);
          tab.setAttribute('aria-current', active ? 'page' : 'false');
        });
        panels.forEach((panel) => { panel.hidden = panel.dataset.profilePanel !== panelName; });
        if (sectionNav && panelName !== 'information') {
          sectionNav.querySelectorAll('a').forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${panelName}`));
        }
        if (schedule) schedule.open = panelName === 'schedule';
        if (hash) history.replaceState(null, '', hash);
        const target = hash ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
        if (shouldScroll && target) requestAnimationFrame(() => target.scrollIntoView({ behavior:'smooth', block:'start' }));
      };
      tabs.forEach((tab) => tab.addEventListener('click', (event) => {
        event.preventDefault();
        activate(tab.dataset.profileTab, tab.getAttribute('href'), true);
      }));
      sectionNav?.querySelectorAll('a[href^="#"]').forEach((link) => link.addEventListener('click', (event) => {
        const panel = panelForHash(link.getAttribute('href'));
        const panelName = panel?.dataset.profilePanel || 'information';
        event.preventDefault();
        activate(panelName, link.getAttribute('href'), true);
        sectionNav.querySelectorAll('a').forEach((item) => item.classList.toggle('active', item === link));
      }));
      const initialPanel = panelForHash(window.location.hash);
      activate(initialPanel?.dataset.profilePanel || 'information', window.location.hash || '#information', false);
      if (sectionNav && window.location.hash) {
        const currentLink = Array.from(sectionNav.querySelectorAll('a')).find((link) => link.getAttribute('href') === window.location.hash);
        if (currentLink) sectionNav.querySelectorAll('a').forEach((item) => item.classList.toggle('active', item === currentLink));
      }
      window.addEventListener('hashchange', () => {
        const panel = panelForHash(window.location.hash);
        activate(panel?.dataset.profilePanel || 'information', window.location.hash, false);
      });
    })();
  </script>
</body>
</html>
"""

CLIENT_DETAIL_TEMPLATE = """
<!doctype html>
<html lang="{{ current_lang }}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Elf's Plan &mdash; {{ site.profile_company_name or site.name }} &middot; Client profile</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root { --blue:#1877f2; --ink:#17213b; --muted:#667085; --line:#e5e8ee; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:#fff; font:14px/1.4 system-ui,-apple-system,Segoe UI,sans-serif; }
    .app-shell { min-height:100vh; display:grid; grid-template-columns:228px minmax(0,1fr); }
    .app-sidebar { background:#111b3d; color:#fff; padding:1.2rem .85rem; display:flex; flex-direction:column; gap:.4rem; }
    .app-sidebar a { color:#dce4ff; padding:.7rem .8rem; border-radius:.6rem; text-decoration:none; }
    .app-sidebar a:hover,.app-sidebar a.active { color:#fff; background:#26366c; }
    .app-sidebar .brand { padding:.5rem .8rem 1rem; color:#fff; font-weight:700; }
    .main { min-width:0; }
    .profile-header { display:flex; align-items:center; gap:1rem; min-height:82px; padding:1rem 1.5rem; border-bottom:1px solid var(--line); }
    .client-mark { width:48px; height:48px; border-radius:50%; object-fit:cover; display:grid; place-items:center; background:#e3f3ff; color:#1479e8; font-size:1.3rem; flex:none; }
    .client-mark.placeholder { font-size:1.2rem; }
    .client-identity { min-width:0; flex:1; }
    .client-identity small { display:block; color:#6b7280; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .client-identity strong { font-size:1rem; }
    .status-pill { display:inline-flex; padding:.22rem .65rem; border-radius:.4rem; color:#087443; background:#d1fae5; font-size:.75rem; font-weight:700; }
    .status-pill.inactive { color:#596273; background:#e9edf2; }
    .profile-actions { display:flex; align-items:center; gap:.5rem; }
    .profile-actions a { text-decoration:none; }
    .profile-tabs { display:flex; gap:.2rem; overflow-x:auto; padding:.55rem 1rem; border-bottom:1px solid var(--line); white-space:nowrap; scrollbar-width:thin; }
    .profile-tabs a { padding:.6rem .8rem; border-radius:.55rem; color:#596273; font-weight:500; text-decoration:none; }
    .profile-tabs a.active,.profile-tabs a:hover { color:#fff; background:var(--blue); }
    .profile-content { display:grid; grid-template-columns:200px minmax(0,1fr); min-height:calc(100vh - 140px); }
    .section-nav { padding:1rem; border-right:1px solid var(--line); display:flex; flex-direction:column; gap:.25rem; }
    .section-nav a { padding:.65rem .75rem; border-radius:.55rem; color:#596273; text-decoration:none; }
    .section-nav a:hover,.section-nav a.active { background:#f2f4f7; color:#17213b; }
    .profile-sections { padding:1.25rem 2rem 3rem; min-width:0; }
    .profile-section { scroll-margin-top:1rem; max-width:1000px; padding:1rem 0 1.5rem; border-bottom:1px solid var(--line); }
    .profile-section h2 { font-size:1rem; margin:0 0 .25rem; }
    .section-description { color:var(--muted); margin:0 0 1rem; }
    .field-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
    .field { min-width:0; }
    .field-label { display:block; margin-bottom:.35rem; color:#687385; font-size:.8rem; }
    .field-value { min-height:42px; padding:.65rem .8rem; border:1px solid #e4e7ec; border-radius:.65rem; background:#fff; overflow-wrap:anywhere; }
    .field-value.multiline { min-height:86px; white-space:pre-wrap; }
    .profile-card { padding:1rem; border:1px solid var(--line); border-radius:.8rem; background:#fff; }
    .client-logo-large { display:block; max-width:220px; max-height:110px; object-fit:contain; object-position:left center; }
    .data-table { width:100%; border-collapse:collapse; }
    .data-table th,.data-table td { text-align:left; padding:.7rem .65rem; border-bottom:1px solid var(--line); vertical-align:top; }
    .data-table th { color:#687385; font-size:.76rem; font-weight:600; }
    .data-table a { color:var(--blue); text-decoration:none; }
    .empty-state { color:var(--muted); padding:1rem; border:1px dashed #cbd5e1; border-radius:.7rem; }
    .mobile-menu { display:none; }
    .main { background:#f5f7fa; }
    .profile-header { position:sticky; top:40px; z-index:25; min-height:76px; padding:.8rem clamp(.8rem,2vw,1.5rem); background:rgba(255,255,255,.97); box-shadow:0 3px 12px rgba(25,39,61,.045); }
    .client-mark { width:52px; height:52px; border-radius:15px; border:1px solid #e5e9ef; color:#014D4E; background:#e8f3f2; }
    .client-identity small { color:#758197; }
    .client-identity strong { color:#1d2d44; font-size:1.12rem; }
    .status-pill { padding:.32rem .7rem; border-radius:999px; color:#075e53; background:#e1f4ed; }
    .status-pill.inactive { color:#fff; background:#ef4444; }
    .profile-actions .btn { min-height:40px; border-radius:10px; font-size:.84rem; }
    .profile-tabs { position:sticky; top:116px; z-index:24; gap:.35rem; padding:.6rem 1.25rem; background:rgba(255,255,255,.97); border-bottom:1px solid #e7ebf0; box-shadow:0 3px 12px rgba(25,39,61,.035); }
    .profile-tabs a { padding:.56rem .82rem; border-radius:9px; color:#667287; font-size:.84rem; font-weight:600; }
    .profile-tabs a.active,.profile-tabs a:hover { color:#014D4E; background:#e8f3f2; }
    .profile-content { grid-template-columns:208px minmax(0,1fr); background:#f5f7fa; }
    .section-nav { position:sticky; top:168px; align-self:start; max-height:calc(100dvh - 180px); overflow:auto; padding:.85rem .7rem; border-right:1px solid #e8ecf1; background:#f9fafc; }
    .section-nav a { padding:.62rem .75rem; border-radius:9px; color:#667287; font-size:.84rem; font-weight:550; }
    .section-nav a:hover,.section-nav a.active { color:#014D4E; background:#e8f3f2; }
    .profile-sections { display:grid; align-content:start; gap:.9rem; padding:1.1rem 1.35rem 2.5rem; }
    .profile-section { width:100%; max-width:none; margin:0; padding:1.2rem 1.3rem; border:1px solid #e6eaf0; border-radius:14px; background:#fff; box-shadow:0 5px 16px rgba(25,39,61,.035); }
    .profile-section h2 { margin:0 0 .3rem; color:#1d2d44; font-size:1.02rem; font-weight:700; letter-spacing:-.015em; }
    .section-description { margin-bottom:1rem; color:#7a879a; font-size:.84rem; }
    .field-label { color:#77849a; font-size:.76rem; font-weight:600; }
    .field-value { border-color:#e5e9ef; border-radius:9px; color:#26364d; background:#fbfcfd; }
    .site-inline-edit-form { display:grid; gap:.9rem; }
    .site-edit-input { min-height:44px; border-color:#e5e9ef; border-radius:9px; color:#26364d; background:#fbfcfd; font-size:.9rem; }
    .site-edit-input:focus { border-color:#7fb5b3; background:#fff; box-shadow:0 0 0 .2rem rgba(1,77,78,.1); }
    .site-inline-save { display:flex; justify-content:flex-end; padding-top:1rem; border-top:1px solid #edf0f4; }
    .site-contract-action { display:flex; justify-content:flex-start; margin-top:1rem; }
    .site-inline-save .btn,.profile-actions .btn-primary { color:#fff; background:#014D4E; border-color:#014D4E; }
    .site-inline-save .btn:hover,.profile-actions .btn-primary:hover { color:#fff; background:#013f40; }
    .data-table { min-width:600px; }
    @media(max-width:900px) { .profile-content { grid-template-columns:160px minmax(0,1fr); } .profile-sections { padding:1rem; } }
    @media(max-width:620px) { .profile-header { top:40px; padding:.7rem .8rem; flex-wrap:wrap; } .profile-actions { width:100%; } .profile-tabs { top:126px; padding:.5rem; } .profile-content { display:block; } .section-nav { top:174px; max-height:none; flex-direction:row; overflow-x:auto; overflow-y:hidden; border-right:0; border-bottom:1px solid #e6eaf0; background:rgba(255,255,255,.97); white-space:nowrap; } .profile-sections { gap:.7rem; padding:.8rem .65rem 1.5rem; } .profile-section { padding:1rem; border-radius:12px; } }
    @media(max-width:900px) { .app-shell { grid-template-columns:1fr; } .app-sidebar { display:none; } .profile-content { grid-template-columns:160px minmax(0,1fr); } .profile-sections { padding:1rem; } }
    @media(max-width:620px) { .profile-header { padding:.8rem; flex-wrap:wrap; } .profile-actions { width:100%; } .profile-tabs { padding:.5rem; } .profile-content { grid-template-columns:1fr; } .section-nav { position:sticky; top:0; z-index:4; flex-direction:row; overflow-x:auto; border-right:0; border-bottom:1px solid var(--line); background:#fff; padding:.4rem; white-space:nowrap; } .section-nav a { padding:.5rem .65rem; } .field-grid { grid-template-columns:1fr; } .profile-sections { padding:.7rem .85rem 2rem; } .data-table { min-width:650px; } .table-wrap { overflow-x:auto; } }
  </style>
</head>
<body>
  <div class="app-shell">
    {% include "partials/admin_sidebar.html" %}
    <main class="main">
      <header class="profile-header">
        {% if site.profile_image_path %}<img class="client-mark" src="{{ url_for('static', filename=site.profile_image_path) }}" alt="Client logo">{% else %}<span class="client-mark placeholder"><i class="bi bi-building" aria-hidden="true"></i></span>{% endif %}
        <div class="client-identity"><small>{{ site.profile_company_name or site.name }}</small><strong>{{ site.name }}</strong></div>
        <span class="status-pill {{ 'inactive' if site.is_active == 0 else '' }}">{{ 'Inactive' if site.is_active == 0 else 'Active' }}</span>
        <div class="profile-actions">{% if not is_sales_manager %}<a class="btn btn-sm btn-outline-primary" href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}"><i class="bi bi-clipboard-check me-1"></i>Inspection areas</a>{% endif %}<form method="post" action="{{ url_for('admin_sites') }}" class="m-0" onsubmit="return confirm(document.documentElement.lang==='de'?'Standort wirklich löschen? Zugehörige Einsätze und Kontrollberichte werden ebenfalls gelöscht. Standorte mit Rechnungen können nicht gelöscht werden.':'Delete this site? Related shifts and inspection reports will also be deleted. Sites with invoices cannot be deleted.');"><input type="hidden" name="entity" value="site"><input type="hidden" name="action" value="delete"><input type="hidden" name="id" value="{{ site.id }}"><input type="hidden" name="redirect_q" value="{{ request.args.get('q', '') }}"><input type="hidden" name="redirect_status" value="{{ request.args.get('status_filter', 'all') }}"><input type="hidden" name="redirect_manager" value="{{ request.args.get('manager_id', '') }}"><input type="hidden" name="redirect_client" value="{{ request.args.get('client', '') }}"><input type="hidden" name="redirect_coverage" value="{{ request.args.get('coverage', '') }}"><input type="hidden" name="redirect_page" value="{{ request.args.get('page', '') }}"><button class="btn btn-sm btn-outline-danger" type="submit" title="Delete site" aria-label="Delete site"><i class="bi bi-trash3" aria-hidden="true"></i></button></form><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('admin_sites', q=request.args.get('q') or None, status_filter=request.args.get('status_filter') if request.args.get('status_filter') != 'all' else None, manager_id=request.args.get('manager_id') or None, client=request.args.get('client') or None, coverage=request.args.get('coverage') or None, page=request.args.get('page') or None) }}" title="Close site" aria-label="Close site"><i class="bi bi-x-lg" aria-hidden="true"></i></a></div>
      </header>
      {% with messages = get_flashed_messages(with_categories=true) %}{% if messages %}<div class="px-3 pt-3">{% for category, message in messages %}<div class="alert alert-{{ 'success' if category == 'success' else 'warning' if category == 'warning' else 'info' }} py-2 mb-2">{{ message }}</div>{% endfor %}</div>{% endif %}{% endwith %}
      <nav class="profile-tabs" aria-label="Client pages"><a class="active" href="#information">Information</a><a href="#schedule">Schedule</a>{% if not is_sales_manager %}<a href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}">Inspection areas</a>{% endif %}{% if not is_site_manager %}<a href="#invoices">Invoices</a>{% endif %}<a href="#documents">Documents</a></nav>
      <div class="profile-content">
        <nav class="section-nav" aria-label="Site sections"><a class="active" href="#general"><i class="bi bi-building me-2"></i>General</a><a href="#contacts"><i class="bi bi-person-lines-fill me-2"></i>Contacts</a>{% if not is_site_manager %}<a href="#contract"><i class="bi bi-file-earmark-text me-2"></i>Contract</a>{% endif %}<a href="#other"><i class="bi bi-card-text me-2"></i>Other</a><a href="#schedule"><i class="bi bi-calendar-week me-2"></i>Schedule</a>{% if not is_sales_manager %}<a href="{{ url_for('ops.admin_inspection_areas', site_id=site.id) }}"><i class="bi bi-clipboard-check me-2"></i>Inspection areas</a>{% endif %}{% if not is_site_manager %}<a href="#invoices"><i class="bi bi-receipt me-2"></i>Invoices</a>{% endif %}<a href="#documents"><i class="bi bi-folder2 me-2"></i>Documents</a></nav>
        <div class="profile-sections">
          <form method="post" enctype="multipart/form-data" action="{{ url_for('admin_site_detail', site_id=site.id) }}" id="site-profile-form" class="site-inline-edit-form">
            <input type="hidden" name="action" value="update_site_profile">
            <section class="profile-section" id="information">
              <div id="general"><h2>General</h2><p class="section-description">Site identity, service address, status, and assigned manager.</p></div>
              <div class="field-grid">
                <label class="field"><span class="field-label">Company / client name</span><input class="form-control site-edit-input" name="profile_company_name" value="{{ (site.profile_company_name or site.name or '')|e }}" required></label>
                <label class="field"><span class="field-label">Service location name</span><input class="form-control site-edit-input" name="name" value="{{ (site.name or '')|e }}" required></label>
                <label class="field"><span class="field-label">Service address</span><input class="form-control site-edit-input" name="address" value="{{ (site.address or '')|e }}"></label>
                <label class="field"><span class="field-label">Status</span><select class="form-select site-edit-input" name="is_active"><option value="1" {% if site.is_active != 0 %}selected{% endif %}>Active</option><option value="0" {% if site.is_active == 0 %}selected{% endif %}>Inactive</option></select></label>
                {% if not is_site_manager %}<label class="field"><span class="field-label">Hourly rate (EUR)</span><input class="form-control site-edit-input" type="number" min="0" step="0.01" name="profile_default_hourly_rate" value="{{ site.profile_default_hourly_rate or site.hourly_rate or '' }}"></label>{% endif %}
                {% if is_main_admin %}<label class="field"><span class="field-label">Assigned site manager</span><select class="form-select site-edit-input" name="manager_employee_id"><option value="">Unassigned</option>{% for manager in site_managers %}<option value="{{ manager.id }}" {% if site.manager_employee_id == manager.id %}selected{% endif %}>{{ manager.name }}</option>{% endfor %}</select></label>{% endif %}
                <div class="field"><span class="field-label">Shifts on record</span><div class="field-value">{{ shift_count }}</div></div>
                <label class="field"><span class="field-label">Site logo</span><input class="form-control site-edit-input" type="file" name="site_profile_image" accept="image/png,image/jpeg,image/gif,image/webp,image/heic"></label>
              </div>
            </section>
            <section class="profile-section" id="contacts">
              <h2>Contacts</h2><p class="section-description">Primary site contact and billing information.</p>
              <div class="field-grid">
                <label class="field"><span class="field-label">Contact person</span><input class="form-control site-edit-input" name="profile_contact_name" value="{{ (site.profile_contact_name or site.contact_name or '')|e }}"></label>
                <label class="field"><span class="field-label">Email</span><input class="form-control site-edit-input" type="email" name="profile_contact_email" value="{{ (site.profile_contact_email or site.contact_email or '')|e }}"></label>
                <label class="field"><span class="field-label">Phone</span><input class="form-control site-edit-input" type="tel" name="profile_phone" value="{{ (site.profile_phone or '')|e }}"></label>
                {% if not is_site_manager %}<label class="field"><span class="field-label">Billing address</span><input class="form-control site-edit-input" name="profile_billing_address" value="{{ (site.profile_billing_address or '')|e }}"></label>
                <label class="field"><span class="field-label">VAT ID</span><input class="form-control site-edit-input" name="profile_vat_id" value="{{ (site.profile_vat_id or '')|e }}"></label>
                <label class="field"><span class="field-label">Customer / tax ID</span><input class="form-control site-edit-input" name="profile_tax_id" value="{{ (site.profile_tax_id or '')|e }}"></label>{% endif %}
              </div>
            </section>
            {% if not is_site_manager %}<section class="profile-section" id="contract">
              <h2>Contract</h2><p class="section-description">Contract partner, contact, and term details.</p>
              <div class="field-grid">
                <label class="field"><span class="field-label">Contract partner</span><input class="form-control site-edit-input" name="contract_partner_name" value="{{ (site.contract_partner_name or '')|e }}"></label>
                <label class="field"><span class="field-label">Contract contact details</span><input class="form-control site-edit-input" name="contract_contact_details" value="{{ (site.contract_contact_details or '')|e }}"></label>
                <label class="field"><span class="field-label">Contract start</span><input class="form-control site-edit-input" type="date" name="contract_start_date" value="{{ contract_start_input }}"></label>
                <label class="field"><span class="field-label">Contract end</span><input class="form-control site-edit-input" type="date" name="contract_end_date" value="{{ contract_end_input }}"></label>
              </div>
              {% if is_main_admin %}<div class="site-contract-action"><button class="btn btn-outline-primary" type="submit" name="profile_action" value="generate_contract"><i class="bi bi-file-earmark-pdf me-1"></i>Save &amp; download contract</button></div>{% endif %}
            </section>{% endif %}
            <section class="profile-section" id="other">
              <h2>Other</h2><p class="section-description">Keep access instructions and internal site notes up to date.</p>
              <label class="field"><span class="field-label">Notes</span><textarea class="form-control site-edit-input" name="profile_notes" rows="4">{{ site.profile_notes or '' }}</textarea></label>
              <div class="field-grid mt-3"><div class="field"><span class="field-label">Site record</span><div class="field-value">#{{ site.id }}</div></div></div>
              <div class="site-inline-save"><button class="btn btn-primary" type="submit"><i class="bi bi-check2 me-1"></i>Save site</button></div>
            </section>
          </form>
          <section class="profile-section" id="schedule">
            <h2>Schedule</h2><p class="section-description">Recent shifts scheduled for this client location.</p>
            {% if shifts %}<div class="table-wrap"><table class="data-table"><thead><tr><th>Date</th><th>Time</th><th>Employee</th><th>Notes</th></tr></thead><tbody>{% for shift in shifts %}<tr><td>{{ shift.day.strftime('%d.%m.%Y') }}</td><td>{{ shift.start_time.strftime('%H:%M') }} &rarr; {{ shift.end_time.strftime('%H:%M') }}</td><td>{{ shift.employee.name if shift.employee else 'Open shift' }}</td><td>{{ shift.instructions or '?' }}</td></tr>{% endfor %}</tbody></table></div>{% else %}<div class="empty-state">No shifts have been scheduled for this client yet.</div>{% endif %}
          </section>
          {% if not is_site_manager %}<section class="profile-section" id="invoices">
            <h2>Invoices</h2><p class="section-description">Recent invoices linked to this client.</p>
            {% if invoices %}<div class="table-wrap"><table class="data-table"><thead><tr><th>Invoice</th><th>Issued</th><th>Due</th><th>Amount</th><th>Status</th></tr></thead><tbody>{% for invoice in invoices %}<tr><td><a href="{{ url_for('admin_invoices') }}">{{ invoice.invoice_number }}</a></td><td>{{ invoice.issued_date.strftime('%d.%m.%Y') if invoice.issued_date else '?' }}</td><td>{{ invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else '?' }}</td><td>{{ '%.2f'|format(invoice.total_amount or invoice.subtotal or 0) }} ?</td><td>{{ invoice.status|title }}</td></tr>{% endfor %}</tbody></table></div>{% else %}<div class="empty-state">No invoices have been created for this client yet.</div>{% endif %}
          </section>{% endif %}
          <section class="profile-section" id="documents">
            <h2>Documents</h2><p class="section-description">Client image and contract tools.</p>
            {% if site.profile_image_path %}<div class="profile-card"><span class="field-label">Client logo</span><img class="client-logo-large" src="{{ url_for('static', filename=site.profile_image_path) }}" alt="Client logo"></div>{% else %}<div class="empty-state">No client logo or document has been added.</div>{% endif %}
            <a class="btn btn-sm btn-outline-primary mt-3" href="#general"><i class="bi bi-pencil-square me-1"></i>Update site logo</a>
          </section>
        </div>
      </div>
    </main>
  </div>
  <script>
    (() => {
      const tabs = Array.from(document.querySelectorAll('.profile-tabs a[href^="#"]'));
      const sections = Array.from(document.querySelectorAll('.section-nav a[href^="#"]'));
      const activate = (hash) => {
        if (!hash) return;
        tabs.forEach((tab) => tab.classList.toggle('active', tab.getAttribute('href') === hash || (hash === '#general' && tab.getAttribute('href') === '#information')));
        sections.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === hash));
      };
      tabs.concat(sections).forEach((link) => link.addEventListener('click', () => activate(link.getAttribute('href'))));
      if (window.location.hash) activate(window.location.hash);
    })();
  </script>
</body>
</html>
"""

INVOICE_LIST_TEMPLATE = """
<!doctype html>
<html lang="{{ current_lang|default('de') }}">
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
    {% include "partials/admin_sidebar.html" %}
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
        <div class="badge-soft mb-2">Billing & Invoicing</div>
        <h1 class="h4 text-dark mb-1">Invoices</h1>
        <p class="text-secondary mb-0">{{ invoices|length }} total invoices</p>
      </header>

      <div class="mb-3">
        <a href="/admin/invoices/new" class="btn btn-primary">+ Create Invoice</a>
        <a href="{{ url_for('admin_income_report') }}" class="btn btn-outline-primary">ðŸ’° Monthly Income</a>
        <button form="bulk-invoice-email-form" type="submit" class="btn btn-outline-primary" onclick="return confirm('Send selected invoices by email now?');">✉ Send selected emails</button>
        <button
          form="bulk-invoice-email-form"
          type="submit"
          formaction="{{ url_for('admin_delete_bulk_invoices') }}"
          class="btn btn-outline-danger"
          onclick="return confirm('Delete selected invoices? This cannot be undone.');"
        >ðŸ—‘ Delete selected</button>
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
{% include "partials/admin_sidebar.html" %}
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
        <div class="badge-soft mb-2">Financial Overview</div>
        <h1 class="h4 text-dark mb-1">ðŸ’° Monthly Income Report</h1>
        <p class="text-secondary mb-0">Income breakdown by month and site</p>
      </header>

      <div class="mb-3">
        <a href="{{ url_for('admin_invoices') }}" class="btn btn-outline-secondary">â† Back to Invoices</a>
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
{% include "partials/admin_sidebar.html" %}
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
        <div class="badge-soft mb-2">Financial Overview</div>
        <h1 class="h4 text-dark mb-1">ðŸ’° Monthly Income Report</h1>
        <p class="text-secondary mb-0">Income breakdown by month and site</p>
      </header>

      <div class="mb-3">
        <a href="{{ url_for('admin_invoices') }}" class="btn btn-outline-secondary">â† Back to Invoices</a>
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
{% include "partials/admin_sidebar.html" %}
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
{% include "partials/admin_sidebar.html" %}
    <main class="main-shell">

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

LOGIN_TEMPLATE = """
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="theme-color" content="#014D4E" />
  <title>Elf's Plan - {{ ui.login_title }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    :root { --login-teal:#014D4E; --login-deep:#073b40; --login-ink:#17233b; --login-muted:#718096; --login-line:#e1e8ec; }
    * { box-sizing:border-box; }
    .ep-global-topbar { position:fixed; top:0; left:0; }
    body { min-height:100vh; min-height:100dvh; margin:0; padding:76px 24px 28px; display:grid; place-items:center; overflow-x:hidden; color:var(--login-ink); background:radial-gradient(ellipse at 12% 10%,#e4f2f0 0,transparent 35%),linear-gradient(145deg,#f5f8fa,#edf2f5); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }
    .login-layout { display:grid; grid-template-columns:minmax(0,1fr) minmax(390px,470px); width:min(1020px,100%); min-height:550px; overflow:hidden; border:1px solid rgba(218,228,233,.9); border-radius:24px; background:#fff; box-shadow:0 28px 80px rgba(20,52,60,.14),0 3px 10px rgba(20,52,60,.04); }
    .login-brand-panel { position:relative; isolation:isolate; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden; padding:clamp(2rem,5vw,3.5rem); color:#f4fbfa; background:linear-gradient(148deg,#073b40 0%,#014D4E 48%,#0a6968 100%); }
    .login-brand-panel::before,.login-brand-panel::after { position:absolute; z-index:-1; content:""; border:1px solid rgba(210,241,235,.12); border-radius:50%; }
    .login-brand-panel::before { width:430px; height:430px; right:-180px; top:-150px; box-shadow:0 0 0 34px rgba(255,255,255,.025),0 0 0 70px rgba(255,255,255,.02); }
    .login-brand-panel::after { width:310px; height:310px; left:-190px; bottom:-130px; background:radial-gradient(circle,rgba(255,255,255,.09),transparent 68%); }
    .login-brand { display:flex; align-items:center; gap:.85rem; }
    .login-brand-logo { display:grid; place-items:center; flex:none; width:48px; height:48px; overflow:hidden; border:1px solid rgba(223,247,242,.24); border-radius:15px; background:rgba(255,255,255,.13); box-shadow:0 8px 22px rgba(2,32,35,.16); }
    .login-brand-logo img { width:36px; height:36px; object-fit:contain; }
    .login-brand-title { color:#fff; font-size:1.25rem; font-weight:820; letter-spacing:-.045em; line-height:1.05; }
    .login-brand-title strong { color:#bce8e2; font-weight:850; }
    .login-brand-caption { margin-top:.3rem; color:rgba(235,248,246,.72); font-size:.67rem; font-weight:650; letter-spacing:.09em; text-transform:uppercase; }
    .login-brand-message { max-width:410px; margin:3rem 0; }
    .login-brand-kicker { display:inline-flex; align-items:center; gap:.42rem; margin-bottom:1rem; padding:.36rem .62rem; border:1px solid rgba(207,241,235,.22); border-radius:999px; background:rgba(255,255,255,.075); color:#d3eeea; font-size:.65rem; font-weight:700; letter-spacing:.045em; }
    .login-brand-kicker i { color:#a5dfd7; }
    .login-brand-message h1 { max-width:390px; margin:0; color:#fff; font-size:clamp(2rem,4vw,3rem); font-weight:760; letter-spacing:-.055em; line-height:1.08; }
    .login-brand-message p { max-width:350px; margin:1rem 0 0; color:rgba(235,248,246,.74); font-size:.9rem; line-height:1.7; }
    .login-brand-footer { color:rgba(235,248,246,.55); font-size:.66rem; }
    .login-form-panel { display:flex; flex-direction:column; justify-content:center; padding:clamp(1.6rem,4vw,3.1rem); }
    .login-language { position:fixed; top:18px; right:22px; z-index:1101; display:flex; align-items:center; gap:.4rem; height:38px; padding:0 .55rem; border:1px solid #dce6e9; border-radius:10px; background:rgba(255,255,255,.92); color:#53677a; box-shadow:0 4px 14px rgba(34,55,69,.07); }
    .login-language > i { color:#397a79; }
    .login-language select { width:auto; min-width:95px; padding:.3rem 1.5rem .3rem .2rem; border:0; background-color:transparent; color:#34465c; font-size:.72rem; font-weight:650; box-shadow:none; }
    .login-form-heading { margin-bottom:1.55rem; }
    .login-form-heading > span { color:var(--login-teal); font-size:.68rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; }
    .login-form-heading h2 { margin:.5rem 0 .4rem; color:#1d2d43; font-size:1.75rem; font-weight:760; letter-spacing:-.045em; }
    .login-form-heading p { margin:0; color:#77869a; font-size:.78rem; line-height:1.55; }
    .login-field { margin-bottom:1rem; }
    .login-field label { display:block; margin-bottom:.42rem; color:#46586e; font-size:.7rem; font-weight:700; }
    .login-input-wrap { position:relative; }
    .login-input-wrap > i { position:absolute; top:50%; left:.85rem; z-index:1; transform:translateY(-50%); color:#91a0ae; font-size:.92rem; pointer-events:none; }
    .login-input-wrap .form-control { min-height:47px; padding:.65rem .8rem .65rem 2.55rem; border:1px solid var(--login-line); border-radius:10px; background:#fbfcfd; color:#25364c; font-size:.82rem; box-shadow:none; }
    .login-input-wrap .form-control::placeholder { color:#a0aab6; }
    .login-input-wrap .form-control:focus { border-color:#68a09e; background:#fff; box-shadow:0 0 0 3px rgba(1,77,78,.1); }
    .login-password-toggle { position:absolute; top:50%; right:.45rem; display:grid; place-items:center; width:35px; height:35px; transform:translateY(-50%); border:0; border-radius:8px; background:transparent; color:#728295; }
    .login-password-toggle:hover { background:#eef4f4; color:var(--login-teal); }
    .login-password-toggle:focus-visible { outline:2px solid #68a09e; outline-offset:1px; }
    .login-submit { display:flex; align-items:center; justify-content:center; gap:.5rem; width:100%; min-height:47px; margin-top:.35rem; border:0; border-radius:10px; background:linear-gradient(120deg,#014D4E,#08716f); color:#fff; font-size:.82rem; font-weight:720; box-shadow:0 8px 18px rgba(1,77,78,.19); transition:transform .16s ease,box-shadow .16s ease,filter .16s ease; }
    .login-submit:hover { transform:translateY(-1px); filter:brightness(1.04); box-shadow:0 12px 22px rgba(1,77,78,.23); }
    .login-submit:focus-visible { outline:3px solid rgba(1,77,78,.25); outline-offset:3px; }
    .login-error { margin-bottom:1rem; border:1px solid #f2d2cc; border-radius:9px; background:#fff4f1; color:#a54335; font-size:.75rem; }
    .login-help { display:flex; align-items:flex-start; gap:.5rem; margin-top:1rem; padding:.75rem; border:1px solid #e8edf0; border-radius:9px; background:#f8fafb; color:#77869a; font-size:.67rem; line-height:1.55; }
    .login-help i { flex:none; margin-top:.05rem; color:#6c9694; }
    .login-mobile-footer { display:none; }
    @media(max-width:760px) { body { padding:82px 16px 24px; } .login-layout { grid-template-columns:1fr; width:min(480px,100%); min-height:auto; } .login-brand-panel { min-height:230px; padding:1.45rem 1.5rem; } .login-brand-message { margin:1.8rem 0 1rem; } .login-brand-message h1 { max-width:440px; font-size:2rem; } .login-brand-message p { margin-top:.55rem; font-size:.78rem; } .login-brand-footer { display:none; } .login-form-panel { padding:1.65rem 1.5rem 1.5rem; } .login-form-heading { margin-bottom:1.15rem; } .login-form-heading h2 { font-size:1.45rem; } }
    @media(max-width:390px) { body { padding-inline:10px; } .login-layout { border-radius:18px; } .login-brand-panel { min-height:205px; padding:1.15rem; } .login-form-panel { padding:1.25rem 1.1rem; } .login-language { top:10px; right:10px; } }
    @media(prefers-reduced-motion:reduce) { *,*::before,*::after { transition:none!important; } }
  </style>
</head>
<body>
  <form method="get" class="login-language" aria-label="{{ ui.language }}">
    {% if next_value %}<input type="hidden" name="next" value="{{ next_value }}">{% endif %}
    <i class="bi bi-translate" aria-hidden="true"></i>
    <label class="visually-hidden" for="lang">{{ ui.language }}</label>
    <select id="lang" name="lang" class="form-select form-select-sm" onchange="this.form.submit()">
      {% for code, label in lang_labels.items() %}<option value="{{ code }}" {% if code == lang %}selected{% endif %}>{{ label }}</option>{% endfor %}
    </select>
  </form>
  <main class="login-layout">
    <section class="login-brand-panel" aria-label="Elf's Plan">
      <div class="login-brand"><span class="login-brand-logo"><img src="/static/employee-icon-192.png" alt=""></span><div><div class="login-brand-title">Elf's <strong>Plan</strong></div><div class="login-brand-caption">{{ ui.login_secure_access }}</div></div></div>
      <div class="login-brand-message"><span class="login-brand-kicker"><i class="bi bi-shield-lock-fill"></i>{{ ui.login_workspace_label }}</span><h1>{{ ui.login_tagline }}</h1><p>{{ ui.login_brand_message }}</p></div>
      <div class="login-brand-footer">Elf's Plan | {{ ui.login_workspace_label }}</div>
    </section>
    <section class="login-form-panel" aria-labelledby="login-heading">
      <div class="login-form-heading"><span>{{ ui.login_secure_access }}</span><h2 id="login-heading">{{ ui.login_title }}</h2><p>{{ ui.login_form_intro }}</p></div>
      <form method="post" class="needs-validation" novalidate>
        <input type="hidden" name="next" value="{{ next_value or request.args.get('next','') }}"><input type="hidden" name="lang" value="{{ lang }}">
        <div class="login-field"><label for="username">{{ ui.login_username }}</label><div class="login-input-wrap"><i class="bi bi-person" aria-hidden="true"></i><input class="form-control" id="username" name="username" autocomplete="username" required autofocus></div></div>
        <div class="login-field"><label for="password">{{ ui.login_password }}</label><div class="login-input-wrap"><i class="bi bi-lock" aria-hidden="true"></i><input type="password" class="form-control" id="password" name="password" autocomplete="current-password" required><button class="login-password-toggle" type="button" id="toggle-password" aria-label="{{ ui.login_show_password }}" title="{{ ui.login_show_password }}"><i class="bi bi-eye"></i></button></div></div>
        {% if error %}<div class="alert login-error py-2" role="alert"><i class="bi bi-exclamation-circle me-1"></i>{{ error }}</div>{% endif %}
        <button class="login-submit" type="submit"><i class="bi bi-box-arrow-in-right"></i>{{ ui.login_button }}</button>
        <div class="login-help"><i class="bi bi-info-circle-fill"></i><span>{{ ui.login_hint }}</span></div>
      </form>
    </section>
  </main>
  <script>
    (() => {
      const form = document.querySelector('.needs-validation');
      form?.addEventListener('submit', event => {
        if (!form.checkValidity()) { event.preventDefault(); event.stopPropagation(); }
        form.classList.add('was-validated');
      });
      const toggle = document.getElementById('toggle-password');
      const password = document.getElementById('password');
      toggle?.addEventListener('click', () => {
        const showing = password.type === 'password';
        password.type = showing ? 'text' : 'password';
        toggle.innerHTML = showing ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
        toggle.setAttribute('aria-label', showing ? '{{ ui.login_hide_password }}' : '{{ ui.login_show_password }}');
        toggle.title = showing ? '{{ ui.login_hide_password }}' : '{{ ui.login_show_password }}';
      });
    })();
  </script>
</body>
</html>
"""

EMPLOYEE_DASHBOARD_TEMPLATE = """
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
  <title>Elf's Plan — {{ ui.your_missions }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <link rel="manifest" href="/static/manifest.json">
  <meta name="theme-color" content="#0f172a" />
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/employee-icon-192.png">
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
    .brand-mark { width: 2.75rem; height: 2.75rem; border-radius: 1rem; display: inline-flex; align-items: center; justify-content: center; background: #fff; object-fit: contain; padding: .12rem; }
    .brand-text { display: grid; gap: 0.1rem; }
    .brand-label { font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; font-size: 0.82rem; color: #0f172a; }
    .brand-sub { font-size: 0.76rem; color: #475569; letter-spacing: 0.04em; text-transform: uppercase; }
    .employee-header-actions { display:flex; align-items:center; gap:.45rem; }
    .employee-notification-toggle { position:relative; width:42px; height:42px; display:grid; place-items:center; border:1px solid #dbe3ed; border-radius:14px; background:#fff; color:#334155; font-size:1.1rem; }
    .employee-notification-count { position:absolute; top:-4px; right:-4px; min-width:18px; height:18px; display:grid; place-items:center; padding:0 4px; border-radius:999px; background:#2563eb; color:white; font-size:.65rem; font-weight:700; }
    .employee-notification-panel { margin-top:.75rem; padding:.8rem; border:1px solid #e2e8f0; border-radius:14px; background:#fff; box-shadow:0 12px 25px rgba(15,23,42,.08); }
    .employee-notification-panel[hidden] { display:none !important; }
    .employee-notification-panel-head { display:flex; align-items:center; justify-content:space-between; gap:.5rem; margin-bottom:.5rem; }
    .employee-notification-panel-head strong { font-size:.9rem; }
    .employee-notification-enable { border:0; border-radius:999px; padding:.35rem .65rem; background:#eff6ff; color:#1d4ed8; font-size:.74rem; font-weight:650; }
    .employee-notification-list { display:grid; gap:.45rem; max-height:min(70vh,460px); overflow:auto; }
    .employee-notification-item { width:100%; padding:.65rem; border:1px solid #e5eaf1; border-radius:11px; background:#f8fafc; color:#334155; text-align:left; }
    .employee-notification-item strong,.employee-notification-item span { display:block; }
    .employee-notification-item strong { font-size:.82rem; margin-bottom:.2rem; }
    .employee-notification-item span { font-size:.76rem; color:#64748b; }
    .employee-notification-empty { margin:0; padding:.5rem; color:#64748b; font-size:.82rem; }
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
    .status-pill[data-state="scheduled"] { border-color: #38bdf8; background: #e0f2fe; color: #0369a1; }
    .status-pill[data-state="in_progress"] { border-color: #fb923c; background: #ffedd5; color: #9a3412; }
    .status-pill[data-state="completed"] { border-color: #4ade80; background: #dcfce7; color: #166534; }
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
          <img class="brand-mark" src="/static/employee-icon-192.png" alt="Elf's Plan">
          <div class="brand-text">
            <span class="brand-label">{{ ui.dashboard_title }}</span>
            <span class="brand-sub">Elf's Plan</span>
          </div>
        </div>
        <div class="employee-header-actions">
          <button type="button" class="employee-notification-toggle" id="employee-notifications-toggle" aria-label="{{ 'Benachrichtigungen' if lang == 'de' else 'Notifications' }}" aria-expanded="false"><i class="bi bi-bell-fill" aria-hidden="true"></i><span class="employee-notification-count" id="employee-notification-count" hidden>0</span></button>
          <a class="logout-chip" href="{{ url_for('logout') }}">{{ ui.sign_out }}</a>
        </div>
      </div>
      <section class="employee-notification-panel" id="employee-notification-panel" hidden aria-label="Notifications">
        <div class="employee-notification-panel-head"><strong>{{ 'Benachrichtigungen' if lang == 'de' else 'Notifications' }}</strong><button type="button" class="employee-notification-enable" id="employee-notification-enable">{{ 'Aktivieren' if lang == 'de' else 'Enable alerts' }}</button></div>
        <p class="employee-notification-empty" id="employee-notification-status" aria-live="polite"></p>
        <div class="employee-notification-list" id="employee-notification-list"><p class="employee-notification-empty">{{ 'Lade Benachrichtigungen…' if lang == 'de' else 'Loading notifications…' }}</p></div>
      </section>
      <div class="d-flex justify-content-end mt-2">
        <form method="get" class="d-flex align-items-center gap-2">
          <label class="small-note" for="employee-lang">{{ ui.language }}</label>
          <select id="employee-lang" name="lang" class="form-select form-select-sm" style="max-width: 180px;" onchange="this.form.submit()">
            {% for code, label in lang_labels.items() %}
              <option value="{{ code }}" {% if code == lang %}selected{% endif %}>{{ label }}</option>
            {% endfor %}
          </select>
        </form>
      </div>
      <div class="date-line">
        <span class="welcome">{{ welcome_message }}</span>
        <span class="date-chip">{{ today_label }}</span>
      </div>
    </header>
    <main class="app-content" id="content">
      <section id="today" class="section">
        <div class="section-head">
          <span class="section-eyebrow">{{ ui.today }}</span>
          <h1 class="section-title">{{ ui.your_missions }}</h1>
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
                  <span class="status-pill" data-state="{{ shift.status_key }}">{{ shift.status_label }}</span>
                </div>
                <div class="job-meta">
                  <div>
                    <div class="meta-label">{{ ui.location }}</div>
                    <div>{{ shift.address }}</div>
                    {% if shift.map_url %}
                      <a class="map-link" href="{{ shift.map_url }}" target="_blank" rel="noopener">{{ ui.open_maps }}</a>
                    {% endif %}
                  </div>
                  <div>
                    <div class="meta-label">{{ ui.instructions }}</div>
                    <div>{{ shift.instructions }}</div>
                  </div>
                  <div>
                    <div class="meta-label">{{ ui.duration }}</div>
                    <div class="meta-chip-row">
                      <span class="meta-chip">{{ ui.scheduled }} · {{ shift.scheduled_duration }}</span>
                      {% if shift.has_actual_duration %}
                        <span class="meta-chip meta-chip--accent">{{ ui.actual }} · {{ shift.actual_duration }}</span>
                      {% endif %}
                    </div>
                  </div>
                  <div>
                    <div class="meta-label">{{ ui.checkpoints }}</div>
                    <div class="checkpoint-row">
                      <span>{{ ui.clock_in }}: {{ shift.clock_in_display }}</span>
                      <span>{{ ui.clock_out }}: {{ shift.clock_out_display }}</span>
                    </div>
                  </div>
                </div>
                <div class="job-actions">
                  <form class="geo-form" method="post" action="{{ shift.clock_in_url }}" data-action="clock-in" data-requires-geo="true">
                    <input type="hidden" name="lat" value="">
                    <input type="hidden" name="lng" value="">
                    <button type="submit" class="action-button btn-clock" {% if shift.clocked_in %}disabled{% endif %}>
                      {% if shift.clocked_in %}{{ ui.clocked_in }}{% else %}{{ ui.clock_in }}{% endif %}
                    </button>
                  </form>
                  <form method="post" action="{{ shift.upload_url }}" enctype="multipart/form-data">
                    <input type="hidden" name="photo_type" value="before">
                    <label class="upload-tile" data-type="before">
                      <span class="icon" aria-hidden="true">ðŸ“¸</span>
                      <span>{% if shift.before_photo_url %}{{ ui.replace_before }}{% else %}{{ ui.upload_before }}{% endif %}</span>
                      <input type="file" name="photo" accept="image/*" onchange="this.form.submit()">
                    </label>
                  </form>
                  <form method="post" action="{{ shift.upload_url }}" enctype="multipart/form-data">
                    <input type="hidden" name="photo_type" value="after">
                    <label class="upload-tile" data-type="after">
                      <span class="icon" aria-hidden="true">✨</span>
                      <span>{% if shift.after_photo_url %}{{ ui.replace_after }}{% else %}{{ ui.upload_after }}{% endif %}</span>
                      <input type="file" name="photo" accept="image/*" onchange="this.form.submit()">
                    </label>
                  </form>
                  <form class="geo-form celebrate-form" method="post" action="{{ shift.complete_url }}" data-action="complete" data-requires-geo="true">
                    <input type="hidden" name="lat" value="">
                    <input type="hidden" name="lng" value="">
                    <button type="submit" class="action-button btn-complete" {% if shift.clocked_out %}disabled{% endif %}>
                      {% if shift.clocked_out %}{{ ui.completed }}{% else %}{{ ui.mark_complete }}{% endif %}
                    </button>
                  </form>
                </div>
                {% if shift.before_photo_url or shift.after_photo_url %}
                  <div class="photo-grid">
                    {% if shift.before_photo_url %}
                      <div class="photo-item">
                        <div class="meta-label">{{ ui.before }}</div>
                        <img src="{{ shift.before_photo_url }}" alt="Before photo for {{ shift.site_name }}">
                      </div>
                    {% endif %}
                    {% if shift.after_photo_url %}
                      <div class="photo-item">
                        <div class="meta-label">{{ ui.after }}</div>
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
            <h2 class="h5 text-dark mb-2">{{ ui.today_empty_title }}</h2>
            <p class="mb-0">{{ ui.today_empty_message }}</p>
          </div>
        {% endif %}
      </section>

      <section id="upcoming" class="section">
        <div class="section-head">
          <span class="section-eyebrow">{{ ui.next }}</span>
          <h2 class="section-title">{{ ui.upcoming_jobs }}</h2>
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
                <span class="status-pill" data-state="{{ job.status_key }}">{{ job.status_label }}</span>
              </article>
            {% endfor %}
          {% else %}
            <div class="empty-state">{{ ui.upcoming_empty }}</div>
          {% endif %}
        </div>
      </section>

      <section id="history" class="section">
        <div class="section-head">
          <span class="section-eyebrow">{{ ui.history }}</span>
          <h2 class="section-title">{{ ui.recent_missions }}</h2>
        </div>
        <div class="timeline">
          {% if history %}
            {% for item in history %}
              <article class="timeline-card">
                <h3>{{ item.site_name }}</h3>
                <div class="timeline-meta">{{ item.day_label }} · {{ item.time_window }}</div>
                <div class="meta-chip-row">
                  <span class="meta-chip">{{ ui.scheduled }} · {{ item.scheduled_duration }}</span>
                  {% if item.has_actual_duration %}
                    <span class="meta-chip meta-chip--accent">{{ ui.actual }} · {{ item.actual_duration }}</span>
                  {% endif %}
                </div>
                <span class="status-pill" data-state="{{ item.status_key }}">{{ item.status_label }}</span>
                {% if item.instructions %}
                  <div class="timeline-meta">{{ item.instructions }}</div>
                {% endif %}
              </article>
            {% endfor %}
          {% else %}
            <div class="empty-state">{{ ui.history_empty }}</div>
          {% endif %}
        </div>
      </section>
    </main>

    <nav class="bottom-nav">
      <a class="nav-link active" href="#today" data-target="today">
        <span class="icon" aria-hidden="true">ðŸ—“</span>
        <span>{{ ui.today }}</span>
      </a>
      <a class="nav-link" href="#upcoming" data-target="upcoming">
        <span class="icon" aria-hidden="true">â­</span>
        <span>{{ ui.next }}</span>
      </a>
      <a class="nav-link" href="#history" data-target="history">
        <span class="icon" aria-hidden="true">ðŸ“œ</span>
        <span>{{ ui.history }}</span>
      </a>
    </nav>
  </div>

  <script>
    (function() {
      const toggle=document.getElementById('employee-notifications-toggle');
      const panel=document.getElementById('employee-notification-panel');
      const badge=document.getElementById('employee-notification-count');
      const list=document.getElementById('employee-notification-list');
      const status=document.getElementById('employee-notification-status');
      const enable=document.getElementById('employee-notification-enable');
      const lang=document.documentElement.lang==='de'?'de':'en';
      const text={
        loading:lang==='de'?'Benachrichtigungen werden geladen…':'Loading notifications…',
        empty:lang==='de'?'Keine neuen Benachrichtigungen.':'No new notifications.',
        paused:lang==='de'?'Benachrichtigungen sind pausiert. Updates erscheinen nach der Reaktivierung.':'Notifications are paused. Shift updates will appear when they resume.',
        enable:lang==='de'?'Browser-Benachrichtigungen aktivieren':'Enable browser notifications',
        allowed:lang==='de'?'Browser-Benachrichtigungen sind aktiviert.':'Browser notifications are enabled.',
        denied:lang==='de'?'Bitte Benachrichtigungen in den Browsereinstellungen erlauben.':'Allow notifications in your browser settings.',
        reminder:lang==='de'?'Deine heutigen Einsätze':'Your shifts today'
      };
      const seenKey='elfs-plan-seen-notifications';
      let pollTimer=null;
      const seenIds=()=>{try{return new Set(JSON.parse(localStorage.getItem(seenKey)||'[]'));}catch(_error){return new Set();}};
      const rememberSeen=(seen)=>{try{localStorage.setItem(seenKey,JSON.stringify(Array.from(seen).slice(-100)));}catch(_error){}};
      const updateMorningReminder=(data)=>{
        if(!('Notification' in window)||Notification.permission!=='granted'||!data.notifications_enabled)return;
        const now=new Date();if(now.getHours()<6)return;
        const localDate=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
        const key='elfs-plan-morning-reminder-'+localDate;
        try{if(localStorage.getItem(key))return;}catch(_error){}
        const shifts=data.today_shifts||[];if(!shifts.length)return;
        const body=shifts.slice(0,3).map(item=>`${item.site_name} · ${item.time_window}`).join('\n');
        try{const notice=new Notification(text.reminder,{body,icon:'/static/employee-icon-192.png',tag:key});notice.onclick=()=>{window.focus();notice.close();};localStorage.setItem(key,'1');}catch(_error){}
      };
      if(enable&&'Notification' in window){
        if(Notification.permission==='granted')enable.textContent=lang==='de'?'Browser-Benachrichtigungen aktiviert':'Browser alerts enabled';
        else if(Notification.permission==='denied')enable.textContent=lang==='de'?'In Browsereinstellungen erlauben':'Allow in browser settings';
      }
      const renderNotifications=(data)=>{
        const items=data.items||[];
        if(badge){badge.hidden=items.length===0;badge.textContent=String(items.length>9?'9+':items.length);}
        if(status)status.textContent=data.notifications_enabled?'':text.paused;
        if(!list)return;
        list.replaceChildren();
        if(!items.length){const empty=document.createElement('p');empty.className='employee-notification-empty';empty.textContent=text.empty;list.appendChild(empty);return;}
        items.forEach(item=>{
          const button=document.createElement('button');button.type='button';button.className='employee-notification-item';
          const heading=document.createElement('strong');heading.textContent=item.title;
          const description=document.createElement('span');description.textContent=item.body;
          button.append(heading,description);
          button.addEventListener('click',async()=>{await fetch(`/employee/api/notifications/${item.id}/read`,{method:'POST',credentials:'same-origin'});refreshNotifications();});
          list.appendChild(button);
        });
      };
      async function refreshNotifications(){
        try{
          const response=await fetch('/employee/api/notifications',{credentials:'same-origin',cache:'no-store'});
          if(!response.ok)return;
          const data=await response.json();renderNotifications(data);updateMorningReminder(data);
          if('Notification' in window&&Notification.permission==='granted'){
            const seen=seenIds();let changed=false;
            for(const item of data.items||[]){
              if(seen.has(item.id))continue;
              seen.add(item.id);changed=true;
              try{const notice=new Notification(item.title,{body:item.body,icon:'/static/employee-icon-192.png',tag:`elfs-plan-notification-${item.id}`});notice.onclick=()=>{window.focus();panel.hidden=false;notice.close();};}catch(_error){}
            }
            if(changed)rememberSeen(seen);
          }
        }catch(_error){/* Offline: cached planner remains usable; refresh when connected. */}
      }
      toggle?.addEventListener('click',()=>{const open=panel.hidden;panel.hidden=!open;toggle.setAttribute('aria-expanded',String(open));if(open)refreshNotifications();});
      enable?.addEventListener('click',async()=>{
        if(!('Notification' in window)){if(status)status.textContent=text.denied;return;}
        if(Notification.permission==='denied'){if(status)status.textContent=text.denied;return;}
        const permission=await Notification.requestPermission();
        if(status)status.textContent=permission==='granted'?text.allowed:text.denied;
        if(permission==='granted'&&enable)enable.textContent=lang==='de'?'Browser-Benachrichtigungen aktiviert':'Browser alerts enabled';
        if(permission==='granted')refreshNotifications();
      });
      refreshNotifications();
      pollTimer=window.setInterval(refreshNotifications,45000);
      window.addEventListener('online',refreshNotifications);
      window.addEventListener('beforeunload',()=>{if(pollTimer)clearInterval(pollTimer);});
    })();
  </script>
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
        message.textContent = {{ (ui.confetti_complete|default('Done!'))|tojson }};
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
        navigator.serviceWorker.register('/employee-sw.js', { scope: '/employee/' }).catch(() => {});
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
<html lang="{{ current_lang|default('de') }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Elf's Plan &mdash; Lead Center</title>
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
    .kanban { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; }
    .kanban-column { border:1px solid #e2e8f0; border-radius:0.9rem; background:#f8fafc; padding:0.75rem; min-height:240px; box-shadow:0 8px 16px rgba(15,23,42,0.08); }
    .kanban-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:0.35rem; color:#0f172a; font-weight:600; font-size:0.95rem; }
    .lead-card { border:1px solid #cbd5f5; border-radius:0.7rem; padding:0.65rem; background:#ffffff; color:#0f172a; margin-bottom:0.5rem; cursor:grab; box-shadow:0 4px 12px rgba(15,23,42,0.08); }
    .lead-card.dragging { opacity:0.6; }
    .kanban-column.drop-target { border-color:#0f766e; box-shadow:inset 0 0 0 2px rgba(15,118,110,0.35); }
    .lead-meta { font-size:0.8rem; color:#64748b; }
    .lead-email-copy { border:0; background:none; padding:0; color:#0f766e; text-decoration:underline; cursor:pointer; font-size:0.8rem; }
    .lead-email-copy:hover { color:#0c615b; }
    .copy-status { min-height:1.2rem; }
    :root { --accent:#014D4E; --ep-lead-canvas:#f5f7fa; --ep-lead-border:#e4e9ef; }
    body { min-height:100vh; background:var(--ep-lead-canvas); color:#1d2d44; font-size:14px; }
    .app-shell { min-height:calc(100dvh - 40px); background:var(--ep-lead-canvas); }
    .main-shell { min-width:0; padding:1.35rem clamp(.85rem,2vw,1.7rem) 2rem; background:var(--ep-lead-canvas); }
    .lead-page-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; margin-bottom:1rem; }
    .lead-page-title { display:flex; align-items:center; gap:.75rem; min-width:0; }
    .lead-page-icon { width:44px; height:44px; display:grid; place-items:center; flex:none; border:1px solid #cce1df; border-radius:13px; color:#014D4E; background:#e8f3f2; font-size:1.15rem; }
    .lead-page-title h1 { margin:.05rem 0 .1rem; color:#1d2d44; font-size:1.35rem; font-weight:720; letter-spacing:-.035em; }
    .lead-page-title .badge-soft { padding:0; border:0; color:#718096; background:transparent; font-size:.68rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
    .lead-page-title .small-note { color:#758197; font-size:.82rem; }
    .lead-summary-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.65rem; margin:0 0 .85rem; }
    .lead-summary { display:flex; align-items:center; gap:.65rem; min-width:0; padding:.7rem .85rem; border:1px solid var(--ep-lead-border); border-radius:12px; background:#fff; box-shadow:0 3px 12px rgba(25,39,61,.035); }
    .lead-summary-icon { width:34px; height:34px; display:grid; place-items:center; flex:none; border-radius:10px; color:#014D4E; background:#e8f3f2; }
    .lead-summary-copy { display:grid; min-width:0; line-height:1.25; }
    .lead-summary-copy span { color:#77849a; font-size:.7rem; }
    .lead-summary-copy strong { color:#23314a; font-size:1.05rem; }
    .lead-workspace { display:grid; grid-template-columns:minmax(230px,290px) minmax(0,1fr); gap:.85rem; align-items:start; }
    .lead-workspace { margin:0; }
    .lead-workspace > .col-12 { width:auto; max-width:none; padding:0; }
    .main-shell .card-surface { min-width:0; padding:1rem; border:1px solid var(--ep-lead-border); border-radius:14px; background:#fff; box-shadow:0 4px 14px rgba(25,39,61,.04); }
    .lead-form-card h2 { margin:0 0 .85rem; color:#23314a!important; font-size:.95rem; font-weight:700; letter-spacing:0; text-transform:none!important; }
    .lead-form-card .form-label { color:#69778c; font-size:.72rem; font-weight:650; letter-spacing:.02em; text-transform:none!important; }
    .lead-form-card .form-control,.lead-form-card .form-select,.lead-filter-panel .form-control,.lead-filter-panel .form-select { min-height:37px; border-color:#e3e8ef; border-radius:9px; font-size:.83rem; box-shadow:none; }
    .lead-form-card textarea.form-control { min-height:72px; }
    .lead-form-card .btn { min-height:38px; border-radius:9px; font-size:.82rem; }
    .lead-filter-panel { display:grid; grid-template-columns:repeat(4,minmax(110px,1fr)) auto; align-items:end; gap:.55rem; margin-bottom:.8rem; padding:.75rem; border:1px solid var(--ep-lead-border); border-radius:12px; background:#fbfcfd; }
    .lead-filter-field { min-width:0; }
    .lead-filter-field .form-label { margin-bottom:.25rem; color:#77849a; font-size:.68rem; font-weight:650; }
    .lead-filter-actions { display:flex; flex-wrap:wrap; gap:.4rem; }
    .lead-filter-actions .btn { min-height:36px; padding:.42rem .62rem; border-radius:9px; font-size:.76rem; white-space:nowrap; }
    .kanban { gap:.65rem; overflow-x:auto; padding-bottom:.35rem; }
    .kanban-column { min-width:190px; min-height:320px; padding:.65rem; border:1px solid #e6eaf0; border-radius:13px; background:#f7f9fb; box-shadow:none; }
    .kanban-header { min-height:34px; margin:0 0 .55rem; color:#35445b; font-size:.81rem; }
    .kanban-header .badge { color:#607087!important; background:#e9eef3!important; font-size:.69rem; }
    .lead-card { padding:.7rem; border:1px solid #e5eaf0; border-left:3px solid #80b9b5; border-radius:11px; background:#fff; box-shadow:0 2px 8px rgba(25,39,61,.045); transition:box-shadow .15s,border-color .15s,transform .15s; }
    .lead-card:hover { border-color:#bdd8d6; box-shadow:0 6px 16px rgba(25,39,61,.08); }
    .lead-card.dragging { opacity:.55; transform:rotate(1deg); }
    .kanban-column.drop-target { border-color:#75aaa7; background:#edf6f5; box-shadow:inset 0 0 0 1px rgba(1,77,78,.12); }
    .lead-card strong { color:#26364d; font-size:.84rem; }
    .lead-meta,.small-note { color:#78869a; font-size:.74rem; }
    .lead-email-copy { color:#014D4E; font-size:.75rem; }
    .lead-card .btn-group .btn { width:29px; height:29px; min-height:29px; padding:0; border-radius:8px!important; }
    .lead-card .btn-group .btn:hover { transform:none; }
    .main-shell .btn-primary,.main-shell .btn-outline-primary { color:#fff; background:#014D4E; background-image:none; border:1px solid #014D4E; box-shadow:0 3px 8px rgba(1,77,78,.14); }
    .main-shell .btn-primary:hover,.main-shell .btn-outline-primary:hover { color:#fff; background:#013f40; }
    .main-shell .btn-outline-secondary { color:#47566e; background:#fff; background-image:none; border:1px solid #dde4ec; box-shadow:none; }
    .main-shell .btn-outline-danger { color:#b42318; background:#fff; background-image:none; border:1px solid #f0c7c3; box-shadow:none; }
    @media(max-width:1100px) { .lead-workspace { grid-template-columns:minmax(210px,250px) minmax(0,1fr); } .lead-filter-panel { grid-template-columns:repeat(2,minmax(110px,1fr)); } }
    @media(max-width:760px) { .main-shell { padding:.8rem .7rem 1.2rem; } .lead-workspace { grid-template-columns:1fr; } .lead-summary-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .lead-page-title h1 { font-size:1.16rem; } .lead-page-icon { width:40px; height:40px; } .kanban-column { min-width:220px; } }
    @media(max-width:420px) { .lead-filter-panel { grid-template-columns:1fr 1fr; } .lead-filter-actions { grid-column:1/-1; } }
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
{% include "partials/admin_sidebar.html" %}
    <main class="main-shell">

      <header class="lead-page-header">
        <div class="lead-page-title"><span class="lead-page-icon"><i class="bi bi-funnel-fill"></i></span><div>
          <div class="badge-soft mb-2">Leads</div>
          <h1 class="h4 mb-1 text-dark">Lead-Center</h1>
          <p class="small-note mb-0">Website bookings arrive as new leads. Move each lead through Contacted to Converted.</p>
        </div></div>
      </header>
      <section class="lead-summary-grid" aria-label="Lead pipeline totals">
        {% for s in stages %}<div class="lead-summary"><span class="lead-summary-icon"><i class="bi {{ 'bi-stars' if s == 'New Leads' else 'bi-chat-dots' if s == 'Contacted' else 'bi-trophy' }}"></i></span><div class="lead-summary-copy"><span>{{ s }}</span><strong>{{ grouped_leads.get(s, [])|length }}</strong></div></div>{% endfor %}
      </section>
      <div class="row g-3 mb-3 lead-workspace">
        <div class="col-12 col-lg-4">
          <div class="card-surface h-100 lead-form-card">
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
          <div class="card-surface h-100 lead-board-card">
            <div class="lead-filter-panel">
              <div class="lead-filter-field">
                <label class="form-label small-note text-uppercase mb-1" for="filter_stage">Stage</label>
                <select class="form-select form-select-sm" id="filter_stage" name="stage" form="filters-form">
                  <option value="">All stages</option>
                  {% for s in stages %}
                    <option value="{{ s }}" {% if stage_filter==s %}selected{% endif %}>{{ s }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="lead-filter-field">
                <label class="form-label small-note text-uppercase mb-1" for="filter_start">From</label>
                <input type="date" class="form-control form-control-sm" id="filter_start" name="start" form="filters-form" value="{{ start_filter or '' }}">
              </div>
              <div class="lead-filter-field">
                <label class="form-label small-note text-uppercase mb-1" for="filter_end">To</label>
                <input type="date" class="form-control form-control-sm" id="filter_end" name="end" form="filters-form" value="{{ end_filter or '' }}">
              </div>
              <div class="lead-filter-field">
                <label class="form-label small-note text-uppercase mb-1" for="filter_sort">Sort</label>
                <select class="form-select form-select-sm" id="filter_sort" name="sort" form="filters-form">
                  <option value="desc" {% if sort=='desc' %}selected{% endif %}>Newest first</option>
                  <option value="asc" {% if sort=='asc' %}selected{% endif %}>Oldest first</option>
                </select>
              </div>
              <div class="lead-filter-actions">
                <form id="filters-form" method="get" class="d-flex flex-wrap gap-2">
                  <button class="btn btn-sm btn-outline-primary" type="submit">Apply</button>
                  <a href="{{ url_for('leads_dashboard') }}" class="btn btn-sm btn-outline-secondary">Clear</a>
                </form>
                <button id="copy-page-emails-btn" type="button" class="btn btn-sm btn-outline-primary">Copy page emails</button>
              </div>
            </div>
            <div id="copy-status" class="small-note copy-status mb-2" aria-live="polite"></div>
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
                            {% if lead.email %}
                              <button type="button" class="lead-email-copy" data-email="{{ lead.email|e }}" title="Copy email">{{ lead.email }}</button>
                            {% else %}
                              <span class="lead-meta">—</span>
                            {% endif %}
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
                          <div class="lead-meta mt-1">ðŸ“ž {{ lead.phone }}</div>
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
      const copyStatus = document.getElementById('copy-status');
      const showCopyStatus = (text) => {
        if (!copyStatus) return;
        copyStatus.textContent = text;
        setTimeout(() => {
          if (copyStatus.textContent === text) copyStatus.textContent = '';
        }, 2500);
      };
      const copyToClipboard = async (text) => {
        const payload = (text || '').trim();
        if (!payload) return false;
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(payload);
            return true;
          }
        } catch (err) {
          console.warn('Clipboard API failed', err);
        }
        try {
          const area = document.createElement('textarea');
          area.value = payload;
          area.setAttribute('readonly', '');
          area.style.position = 'absolute';
          area.style.left = '-9999px';
          document.body.appendChild(area);
          area.select();
          const ok = document.execCommand('copy');
          area.remove();
          return ok;
        } catch (err) {
          console.warn('execCommand copy failed', err);
          return false;
        }
      };

      document.querySelectorAll('.lead-email-copy').forEach(btn => {
        btn.addEventListener('click', async (event) => {
          event.stopPropagation();
          const email = (btn.dataset.email || '').trim();
          if (!email) return;
          const ok = await copyToClipboard(email);
          showCopyStatus(ok ? `Copied: ${email}` : 'Unable to copy email');
        });
      });

      const copyAllBtn = document.getElementById('copy-page-emails-btn');
      if (copyAllBtn) {
        copyAllBtn.addEventListener('click', async () => {
          const emails = [...document.querySelectorAll('.lead-card[data-lead-email]')]
            .map(card => (card.dataset.leadEmail || '').trim())
            .filter(Boolean);
          const uniqueEmails = [...new Set(emails)];
          if (!uniqueEmails.length) {
            showCopyStatus('No emails on this page');
            return;
          }
          const payload = uniqueEmails.join(';');
          const ok = await copyToClipboard(payload);
          showCopyStatus(ok ? `Copied ${uniqueEmails.length} emails` : 'Unable to copy emails');
        });
      }

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
{% include "partials/admin_sidebar.html" %}
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
                <div id="gpt-output" class="chat-output border rounded-3 p-2 flex-grow-1" style="min-height:120px; max-height:min(70vh,460px); overflow:auto;"></div>
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
        try {
          const raw = localStorage.getItem(KEY);
          if (raw === null) return true; // default: collapsed (icons only)
          return raw === '1';
        } catch (e) {
          return true;
        }
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
          const resp = await fetch('/crawler', { method: 'POST', body: formData });
          if (!resp.ok) {
            const errText = await resp.text();
            throw new Error('Server returned ' + resp.status + (errText ? ' – ' + errText : ''));
          }
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
  <title>Putzelf Marketing — Mitarbeiterplan</title>
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
    .schedule-table thead th { background:#f1f5f9; color:#475569; position:sticky; top:0; z-index:5; }
    .schedule-table thead th:first-child { position:sticky; left:0; z-index:10; background:#f1f5f9; }
    .schedule-table tbody th { position:sticky; left:0; z-index:4; background:inherit; color:#0f172a; }
    .schedule-table tbody tr:nth-child(odd) { background:#ffffff; }
    .schedule-table tbody tr:nth-child(even) { background:#f8fafc; }
    .shift-pill { display:flex; align-items:flex-start; gap:0.35rem; padding:0.3rem 0.6rem; border-radius:0.9rem; background:#ecfdf5; border:1px solid #16a34a26; color:#0f766e; font-size:0.74rem; margin-bottom:0.35rem; white-space:normal; }
    .shift-pill-text { display:flex; flex-direction:column; gap:0.1rem; line-height:1.2; min-width:0; }
    .shift-pill-title { font-weight:600; color:#0f766e; }
    .shift-pill-sub { color:#0f766e; opacity:0.9; }
    .shift-pill-time { color:#0f766e; opacity:0.9; }
    .shift-pill-actions { display:inline-flex; align-items:center; gap:0.25rem; margin-left:auto; }
    .shift-pill[draggable="true"] { cursor:grab; }
    .shift-pill.dragging { opacity:0.55; }
    .schedule-drop-target { outline:2px dashed #0ea5e9; outline-offset:-2px; background:#e0f2fe !important; }
    .shift-checkbox { cursor:pointer; margin:0; width:14px; height:14px; flex-shrink:0; }
    .shift-delete { display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#ef4444; color:#ffffff; font-size:0.85rem; line-height:1; text-decoration:none; opacity:0.7; transition:opacity 0.15s ease; }
    .shift-delete:hover { opacity:1; color:#ffffff; }
    .batch-actions { display:flex; justify-content:flex-end; align-items:center; gap:0.55rem; margin-bottom:0.55rem; }
    .btn-batch-delete,
    .btn-batch-delete:hover,
    .btn-batch-delete:focus,
    .btn-batch-delete:active {
      background-image:var(--btn-grad-danger) !important;
      color:#ffffff !important;
      border:0 !important;
      text-shadow:none;
    }
    .btn-batch-delete:disabled { opacity:0.55; color:#ffffff !important; }
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
{% include "partials/admin_sidebar.html" %}
    <div class="main-shell">
      <header class="page-header">
        <div>
          <div class="topbar-title">Personal</div>
          <h1 class="topbar-heading mb-0">Mitarbeiterplan</h1>
          <p class="topbar-subtitle mb-0">
            Sehen Sie, wer diese Woche an welchem Standort arbeitet, wann Mitarbeitende frei sind und weisen Sie neue Einsätze zu.
          </p>
          <p class="small-note mb-0">
            Zeigt {{ week_days[0].strftime('%d.%m.%Y') }} – {{ week_days[-1].strftime('%d.%m.%Y') }} ({{ weeks }} Woche{% if weeks > 1 %}n{% endif %})
          </p>
        </div>
        <div class="page-header-actions">
          <button id="sidebar-toggle" type="button" class="btn btn-sm btn-outline-secondary btn-icon" title="Navigation umschalten">☰</button>
          <a href="{{ url_for('admin_dashboard') }}" class="btn btn-sm btn-outline-secondary">Admin-Bereich</a>
          <a href="{{ url_for('logout') }}" class="btn btn-sm btn-outline-secondary">Abmelden</a>
        </div>
      </header>
      <main class="content-shell">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <section class="section-card" style="padding:1rem 1.1rem;">
              {% for category, message in messages %}
                <div class="alert {% if category in ['warning', 'error', 'danger'] %}alert-warning{% elif category == 'success' %}alert-success{% else %}alert-info{% endif %} mb-2" role="alert" style="border-radius:0.8rem;">
                  {{ message }}
                </div>
              {% endfor %}
            </section>
          {% endif %}
        {% endwith %}

        <section class="section-card schedule-card">
          <div class="section-header">
            <div>
              <div class="section-kicker">Teamplanung</div>
              <h2 class="section-title">Einsatzübersicht</h2>
              <p class="section-subtitle">
                Verwalten Sie die Wochenabdeckung und erkennen Sie freie Kapazitäten aller Mitarbeitenden auf einen Blick.
              </p>
            </div>
            <div class="section-actions">
              {% if reportlab_available %}
                <a href="{{ pdf_url }}" class="btn btn-sm btn-primary">Plan als PDF</a>
                <a href="{{ hours_pdf_url }}" class="btn btn-sm btn-outline-secondary">Stundenbericht</a>
              {% else %}
                <span class="tag-muted">Installieren Sie reportlab für den PDF-Export</span>
              {% endif %}
              <button type="button" class="btn btn-sm btn-outline-primary" id="import-previous-month-btn">Einsätze importieren</button>
            </div>
          </div>
          <div class="insight-badges">
            <span class="insight-badge">Woche {{ week_days[0].strftime('%d.%m') }} – {{ week_days[-1].strftime('%d.%m') }}</span>
            <span class="insight-badge">Zeitraum {{ weeks }} Woche{% if weeks > 1 %}n{% endif %}</span>
            {% if selected_employee %}
              <span class="insight-badge">Fokus: {{ selected_employee.name }}</span>
            {% else %}
              <span class="insight-badge">Alle Mitarbeitenden</span>
            {% endif %}
            {% if selected_site %}
              <span class="insight-badge">Standort: {{ selected_site.name }}</span>
            {% endif %}
          </div>
          <form method="get" action="{{ url_for('schedule_dashboard') }}" class="filter-toolbar">
            <input type="hidden" name="weeks" value="{{ weeks }}">
            <input type="hidden" name="days" value="{{ request.args.get('days', '') }}">
            <input type="hidden" name="free_day" value="{{ free_day or '' }}">
            <input type="hidden" name="free_week_start" value="{{ free_week_start or '' }}">
            <input type="hidden" name="free_start_time" value="{{ request.args.get('free_start_time', '') }}">
            <input type="hidden" name="free_end_time" value="{{ request.args.get('free_end_time', '') }}">
            <div>
              <label class="form-label" for="filter_employee_id">Mitarbeiterfokus</label>
              <select class="form-select form-select-sm" id="filter_employee_id" name="employee_id" onchange="this.form.submit()">
                <option value="">Alle Mitarbeitenden</option>
                {% for emp in employees %}
                  <option value="{{ emp.id }}" {% if selected_employee_id == emp.id %}selected{% endif %}>{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
                {% endfor %}
              </select>
            </div>
            <div>
              <label class="form-label" for="filter_site_id">Standortfokus</label>
              <select class="form-select form-select-sm" id="filter_site_id" name="site_id" onchange="this.form.submit()">
                <option value="">Alle Standorte</option>
                {% for site in sites %}
                  <option value="{{ site.id }}" {% if selected_site_id == site.id %}selected{% endif %}>{{ site.name }}</option>
                {% endfor %}
              </select>
            </div>
            <div>
              <div class="collapse-panel" style="padding-top:0.25rem;">
                <button type="button" id="free-filter-toggle" class="btn btn-sm btn-outline-secondary" style="width:100%; text-align:left; font-weight:600;" onclick="toggleFreeFilterPanel()">Nur freie Mitarbeitende ▾</button>
                <div id="free-filter-content" style="display:none; margin-top:0.6rem;">
                  <div style="display:grid; grid-template-columns:repeat(1,1fr); gap:0.5rem;">
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                      <div style="flex:1; min-width:170px;">
                        <label class="form-label small mb-1" for="free_start_date">Startdatum</label>
                        <input type="date" class="form-control form-control-sm" id="free_start_date" name="free_start_date" value="{{ free_day or '' }}">
                      </div>
                      <div style="flex:1; min-width:170px;">
                        <label class="form-label small mb-1" for="free_end_date">Enddatum</label>
                        <input type="date" class="form-control form-control-sm" id="free_end_date" name="free_end_date" value="{{ free_week_start or '' }}">
                      </div>
                    </div>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                      <div style="flex:1; min-width:170px;">
                        <label class="form-label small mb-1" for="free_start_time">Von (Uhrzeit)</label>
                        <input type="time" class="form-control form-control-sm" id="free_start_time" name="free_start_time" value="">
                      </div>
                      <div style="flex:1; min-width:170px;">
                        <label class="form-label small mb-1" for="free_end_time">Bis (Uhrzeit)</label>
                        <input type="time" class="form-control form-control-sm" id="free_end_time" name="free_end_time" value="">
                      </div>
                    </div>
                    <div style="display:flex; gap:0.5rem; justify-content:flex-end; margin-top:0.25rem;">
                      <button type="button" class="btn btn-sm btn-outline-primary" onclick="showFreeEmployeesModal()">Mitarbeitende anzeigen</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div>
              <label class="form-label" for="start_date">Startwoche (Montag)</label>
              <input type="date" class="form-control form-control-sm" id="start_date" name="start_date" value="{{ start_date or week_days[0].isoformat() }}" onchange="this.form.submit()">
            </div>
            <div>
              <label class="form-label" for="filter-zeitraum">Zeitraum</label>
              <select class="form-select form-select-sm" id="filter-zeitraum" onchange="handleZeitraumChange(event, '{{ url_for('schedule_dashboard') }}')">
                <option value="">— Wählen —</option>
                {% for n in [1,2,4,8,12] %}
                  <option value="weeks={{ n }}" {% if weeks == n and not request.args.get('days') %}selected{% endif %}>{{ n }} Woche{% if n>1 %}n{% endif %}</option>
                {% endfor %}
                <option value="day-picker" {% if request.args.get('days') %}selected{% endif %}>Tag auswählen</option>
              </select>
              <input type="hidden" id="filter-day-picker" class="form-control form-control-sm" placeholder="Tag wählen">
            </div>
          </form>
          <form id="batch-delete-form" method="post" action="{{ url_for('batch_delete_shifts') }}">
            <div class="batch-actions">
              <button type="button" class="btn btn-sm btn-outline-primary" id="edit-selected-btn" disabled>
                <i class="bi bi-pencil-square"></i> Ausgewählte bearbeiten (<span id="edit-selected-count">0</span>)
              </button>
              <button type="submit" class="btn btn-sm btn-batch-delete" id="delete-selected-btn" disabled>
                <i class="bi bi-trash"></i> Ausgewählte löschen (<span id="selected-count">0</span>)
              </button>
            </div>
            {% if not has_any_shifts and not free_filter %}
              <div class="alert alert-warning mb-3" role="alert" style="border-radius:0.85rem;">
                Keine Einsätze im ausgewählten Zeitraum ({{ week_days[0].strftime('%d.%m.%Y') }} – {{ week_days[-1].strftime('%d.%m.%Y') }}){% if selected_site %} für {{ selected_site.name }}{% endif %}{% if selected_employee %} ({{ selected_employee.name }}){% endif %}. Bitte Startwoche/Filter anpassen oder unten einen neuen Einsatz anlegen.
              </div>
            {% endif %}
            <div class="table-wrapper">
              <div class="table-scroll">
                <table class="table table-bordered table-sm align-middle schedule-table">
                  <thead>
                    <tr>
                      <th scope="col">Datum</th>
                      {% for emp in visible_employees %}
                        <th scope="col">
                          {{ emp.name }}<br>
                          <span class="small-note">{{ emp.role or '' }}</span>
                        </th>
                      {% endfor %}
                    </tr>
                  </thead>
                  <tbody>
                    {% for d in visible_days %}
                      <tr data-day="{{ d.isoformat() }}">
                        <th scope="row">
                          {{ ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][d.weekday()] }}<br>
                          <span class="small-note">{{ d.strftime('%d.%m') }}</span>
                        </th>
                        {% for emp in visible_employees %}
                          {% set cell = cells.get((emp.id, d)) %}
                          <td data-day="{{ d.isoformat() }}" data-employee-id="{{ emp.id }}">
                            {% if cell %}
                              {% for shift in cell %}
                                <div class="shift-pill" draggable="true" data-shift-id="{{ shift.id }}" data-employee-id="{{ emp.id }}" data-day="{{ shift.day_iso }}" data-start="{{ shift.start_time_str }}" data-end="{{ shift.end_time_str }}" data-instructions="{{ shift.instructions | e }}">
                                  <input type="checkbox" class="shift-checkbox" name="shift_ids[]" value="{{ shift.id }}" title="Zum Löschen auswählen">
                                  <div class="shift-pill-text">
                                    <div class="shift-pill-title">{{ shift.site_name }}</div>
                                    <div class="shift-pill-sub">{{ shift.site_address }}</div>
                                    <div class="shift-pill-time">{{ shift.time_window }}</div>
                                  </div>
                                  <div class="shift-pill-actions">
                                    <button type="button" class="shift-edit btn-icon-tiny" data-shift-id="{{ shift.id }}" data-employee-id="{{ emp.id }}" data-day="{{ shift.day_iso }}" data-start="{{ shift.start_time_str }}" data-end="{{ shift.end_time_str }}" data-instructions="{{ shift.instructions | e }}" title="Einsatz bearbeiten" style="background:none; border:none; padding:0; cursor:pointer; color:#0f766e; font-size:0.9rem; margin:0 2px;">✎</button>
                                    <a href="{{ url_for('delete_shift', shift_id=shift.id) }}" class="shift-delete" onclick="return confirm('Diesen Einsatz löschen?')" title="Einsatz löschen">×</a>
                                  </div>
                                </div>
                              {% endfor %}
                            {% endif %}
                          </td>
                        {% endfor %}
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
            </div>
          </form>
        </section>

        <section class="section-card form-card">
          <div class="section-header">
            <div>
              <div class="section-kicker">Einsatz erstellen</div>
              <h2 class="section-title">Neuen Einsatz zuweisen</h2>
              <p class="section-subtitle">
                Wählen Sie einen Mitarbeiter, ordnen Sie ihn einem Standort zu und hinterlegen Sie anschließend Zeitfenster und Tage.
              </p>
            </div>
          </div>
          <form method="post" class="small">
            <div class="form-grid">
              <div class="form-field">
                <label class="form-label small-note text-uppercase">Mitarbeiter</label>
                <details class="collapse-panel">
                  <summary class="form-select form-select-sm" style="cursor:pointer; padding:0.65rem 0.75rem; border:1px solid #cbd5e1; border-radius:0.5rem; background:#f8fafc;">Mitarbeiter auswählen</summary>
                  <div style="margin-top:0.75rem; display:flex; flex-direction:column; gap:0.35rem; max-height:16rem; overflow:auto; padding-right:0.25rem;">
                    {% for emp in employees %}
                      <label style="display:flex; align-items:center; gap:0.6rem;">
                        <input type="checkbox" name="employee_id" value="{{ emp.id }}">
                        <span>{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</span>
                      </label>
                    {% endfor %}
                  </div>
                </details>
                <div class="small-note mt-1">Öffnen Sie das Feld und wählen Sie mehrere Mitarbeiter.</div>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="site_id">Standort</label>
                <select class="form-select form-select-sm" id="site_id" name="site_id" required>
                  <option value="">Standort wählen…</option>
                  {% for site in sites %}
                    <option value="{{ site.id }}">{{ site.name }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="form-field form-field-span">
                <label class="form-label small-note text-uppercase" for="day-picker">Tag(e)</label>
                <input type="text" class="form-control form-control-sm" id="day-picker" name="day_display" placeholder="Einen oder mehrere Tage wählen" required autocomplete="off">
                <div id="selected-days" class="selected-days mt-2"></div>
                <div id="day-hidden-inputs" hidden></div>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="start_time">Startzeit</label>
                <input type="time" class="form-control form-control-sm" id="start_time" name="start_time" required>
              </div>
              <div class="form-field">
                <label class="form-label small-note text-uppercase" for="duration_hours">Dauer (Stunden)</label>
                <input type="number" step="0.25" min="0.25" max="24" class="form-control form-control-sm" id="duration_hours" name="duration_hours" placeholder="z. B. 8" required>
              </div>
              <div class="form-field form-field-span">
                <label class="form-label small-note text-uppercase" for="instructions">Besondere Hinweise</label>
                <textarea class="form-control form-control-sm" id="instructions" name="instructions" rows="3" placeholder="Optionale Hinweise für diesen Einsatz"></textarea>
              </div>
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary btn-sm">Einsatz speichern</button>
              <span class="small-note">Kalendereinträge werden für jeden ausgewählten Tag übernommen.</span>
            </div>
          </form>
          <div class="tip-callout mt-3">
            Tipp: Eine leere Zelle im Raster bedeutet, dass der Mitarbeiter an diesem Tag vollständig frei ist.
          </div>
        </section>
      </main>
    </div>
  </div>

  <!-- Previous month import modal -->
  <div id="previous-month-import-modal" style="display:none; position:fixed; inset:0; background:rgba(15,23,42,0.6); z-index:10010; align-items:center; justify-content:center; padding:1.5rem;">
    <div style="background:#ffffff; border-radius:1rem; padding:1.5rem; width:100%; max-width:900px; max-height:90vh; overflow-y:auto; box-shadow:0 24px 60px rgba(15,23,42,0.25);">
      <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1rem;">
        <div>
          <h3 style="margin:0; font-size:1.3rem; color:#0f172a;">Einsätze importieren</h3>
          <p style="margin:0.5rem 0 0; color:#475569;">Wählen Sie die Quellwoche (relative zur aktuellen Woche) und wie viele Wochen vorwärts kopiert werden sollen.</p>
        </div>
        <button type="button" id="previous-month-import-close" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color:#64748b;">×</button>
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:1rem; margin-bottom:1rem;">
        <div style="flex:1; min-width:220px;">
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Quellwoche (zurück)</label>
          <select id="previous-month-import-source-offset" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;">
            <option value="0" selected>Aktuelle Woche</option>
            <option value="1">1 Woche zurück</option>
            <option value="2">2 Wochen zurück</option>
            <option value="3">3 Wochen zurück</option>
          </select>
        </div>
        <div style="flex:1; min-width:220px;">
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Ziel (Wochen vorwärts)</label>
          <select id="previous-month-import-target-offset" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;">
            <option value="1" selected>+1 Woche</option>
            <option value="2">+2 Wochen</option>
            <option value="3">+3 Wochen</option>
            <option value="4">+4 Wochen</option>
          </select>
        </div>
      </div>
      <div id="previous-month-import-content">
        <div class="alert alert-info" role="alert">Lade Einsätze aus dem ausgewählten Monat...</div>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.75rem; margin-top:1rem;">
        <button type="button" class="btn btn-sm btn-outline-secondary" id="previous-month-import-cancel">Abbrechen</button>
        <button type="button" class="btn btn-sm btn-primary" id="previous-month-import-submit" disabled>Importieren</button>
      </div>
    </div>
  </div>

  <!-- Edit Shift Modal -->
  <div id="edit-shift-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:10000; align-items:center; justify-content:center;">
    <div style="background:white; border-radius:1rem; padding:1.5rem; max-width:500px; width:90%; max-height:90vh; overflow-y:auto; box-shadow:0 20px 50px rgba(0,0,0,0.3);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
        <h3 style="margin:0; font-size:1.3rem; color:#0f172a;">Einsatz bearbeiten</h3>
        <button type="button" onclick="document.getElementById('edit-shift-modal').style.display='none'" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color:#94a3b8;">×</button>
      </div>
      <form id="edit-shift-form" method="post" action="" style="display:flex; flex-direction:column; gap:1rem;">
        <input type="hidden" id="edit-shift-id" name="shift_id" value="">
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Mitarbeiter</label>
          <select id="edit-shift-employee" name="employee_id" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;" required>
            {% for emp in employees %}
              <option value="{{ emp.id }}">{{ emp.name }}{% if emp.role %} — {{ emp.role }}{% endif %}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Tag</label>
          <input type="date" id="edit-shift-day" name="day" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;" required>
        </div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Startzeit</label>
          <input type="time" id="edit-shift-start" name="start_time" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;" required>
        </div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Endzeit</label>
          <input type="time" id="edit-shift-end" name="end_time" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;" required>
        </div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Hinweise (optional)</label>
          <textarea id="edit-shift-instructions" name="instructions" rows="3" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem; font-family:inherit; resize:vertical;"></textarea>
        </div>
        <div style="display:flex; gap:0.75rem; justify-content:flex-end; margin-top:1rem;">
          <button type="button" onclick="document.getElementById('edit-shift-modal').style.display='none'" style="padding:0.65rem 1.15rem; border:1px solid #cbd5f5; border-radius:0.75rem; background:#f8fafc; color:#0f172a; cursor:pointer; font-size:0.95rem;">Abbrechen</button>
          <button type="submit" style="padding:0.65rem 1.15rem; border:none; border-radius:0.75rem; background:#0f766e; color:white; cursor:pointer; font-size:0.95rem; font-weight:500;">Änderungen speichern</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Free employees modal -->
  <div id="free-employees-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:10005; align-items:center; justify-content:center;">
    <div style="background:white; border-radius:1rem; padding:1rem; max-width:680px; width:94%; max-height:80vh; overflow-y:auto; box-shadow:0 20px 50px rgba(0,0,0,0.3);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
        <h3 style="margin:0; font-size:1.1rem; color:#0f172a;">Freie Mitarbeitende</h3>
        <button type="button" onclick="document.getElementById('free-employees-modal').style.display='none'" style="background:none; border:none; font-size:1.25rem; cursor:pointer; color:#94a3b8;">×</button>
      </div>
      <div id="free-employees-content" style="min-height:3rem;">
        <div class="small-note">Suche läuft...</div>
      </div>
      <div style="display:flex; justify-content:flex-end; gap:0.6rem; margin-top:0.75rem;">
        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="document.getElementById('free-employees-modal').style.display='none'">Schließen</button>
      </div>
    </div>
  </div>

  <script>
    async function showFreeEmployeesModal(){
      const startDate = document.getElementById('free_start_date').value;
      const endDate = document.getElementById('free_end_date').value || startDate;
      const startTime = document.getElementById('free_start_time').value;
      const endTime = document.getElementById('free_end_time').value;
      const siteIdElem = document.getElementById('filter_site_id');
      const siteId = siteIdElem ? siteIdElem.value : '';
      if(!startDate){
        alert('Bitte ein Startdatum wählen.');
        return;
      }
      const params = new URLSearchParams({free_start_date: startDate, free_end_date: endDate});
      if(startTime) params.set('free_start_time', startTime);
      if(endTime) params.set('free_end_time', endTime);
      if(siteId) params.set('site_id', siteId);
      const url = `/schedule/free-available?${params.toString()}`;
      const container = document.getElementById('free-employees-content');
      container.innerHTML = '<div class="small-note">Suche läuft...</div>';
      document.getElementById('free-employees-modal').style.display = 'flex';
      try{
        const resp = await fetch(url, {credentials: 'same-origin'});
        if(!resp.ok){
          const err = await resp.json().catch(()=>({error: 'Fehler'}));
          container.innerHTML = `<div class="alert alert-danger">Fehler: ${err.error || resp.statusText}</div>`;
          return;
        }
        const data = await resp.json();
        const items = data.items || [];
        if(items.length === 0){
          container.innerHTML = '<div class="small-note">Keine freien Mitarbeitenden im gewählten Zeitraum gefunden.</div>';
          return;
        }
        const list = document.createElement('div');
        list.style.display = 'grid';
        list.style.gridTemplateColumns = 'repeat(2, 1fr)';
        list.style.gap = '0.5rem';
        items.forEach(it => {
          const card = document.createElement('div');
          card.style.padding = '0.6rem';
          card.style.border = '1px solid #e6eef3';
          card.style.borderRadius = '0.5rem';
          card.innerHTML = `<strong>${it.name}</strong>${it.role ? ' — ' + it.role : ''}`;
          list.appendChild(card);
        });
        container.innerHTML = '';
        container.appendChild(list);
      }catch(e){
        container.innerHTML = '<div class="alert alert-danger">Netzwerkfehler beim Laden.</div>';
      }
    }

    function toggleFreeFilterPanel(){
      const content = document.getElementById('free-filter-content');
      const toggle = document.getElementById('free-filter-toggle');
      if(!content || !toggle) return;
      const isHidden = content.style.display === 'none' || content.style.display === '';
      content.style.display = isHidden ? 'block' : 'none';
      toggle.textContent = isHidden ? 'Nur freie Mitarbeitende ▴' : 'Nur freie Mitarbeitende ▾';
    }
  </script>

  <!-- Sammelbearbeitung Einsätze Modal -->
  <div id="batch-edit-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:10000; align-items:center; justify-content:center;">
    <div style="background:white; border-radius:1rem; padding:1.5rem; max-width:520px; width:90%; max-height:90vh; overflow-y:auto; box-shadow:0 20px 50px rgba(0,0,0,0.3);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <h3 style="margin:0; font-size:1.2rem; color:#0f172a;">Mehrere Einsätze bearbeiten</h3>
        <button type="button" id="batch-edit-close" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color:#94a3b8;">×</button>
      </div>
      <p class="small-note" style="margin-bottom:1rem;">Bearbeite <strong id="batch-edit-count">0</strong> ausgewählte Einsätze.</p>
      <form id="batch-edit-form" method="post" action="{{ url_for('batch_edit_shifts') }}" style="display:flex; flex-direction:column; gap:0.9rem;">
        <div id="batch-edit-hidden-inputs" hidden></div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Neuer Tag (optional)</label>
          <input type="date" id="batch-edit-day" name="day" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;">
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
          <div>
            <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Neue Startzeit (optional)</label>
            <input type="time" id="batch-edit-start" name="start_time" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;">
          </div>
          <div>
            <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Neue Endzeit (optional)</label>
            <input type="time" id="batch-edit-end" name="end_time" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem;">
          </div>
        </div>
        <div>
          <label style="display:block; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748b; margin-bottom:0.35rem;">Neue Hinweise (optional)</label>
          <textarea id="batch-edit-instructions" name="instructions" rows="3" style="width:100%; padding:0.5rem; border:1px solid #cbd5f5; border-radius:0.6rem; font-size:0.9rem; font-family:inherit; resize:vertical;" placeholder="Leer lassen, um bestehende Hinweise beizubehalten"></textarea>
        </div>
        <div style="display:flex; gap:0.75rem; justify-content:flex-end; margin-top:0.5rem;">
          <button type="button" id="batch-edit-cancel" style="padding:0.65rem 1.15rem; border:1px solid #cbd5f5; border-radius:0.75rem; background:#f8fafc; color:#0f172a; cursor:pointer; font-size:0.95rem;">Abbrechen</button>
          <button type="submit" style="padding:0.65rem 1.15rem; border:none; border-radius:0.75rem; background:#0f766e; color:white; cursor:pointer; font-size:0.95rem; font-weight:500;">Änderungen anwenden</button>
        </div>
      </form>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.js"></script>
  <script>
    document.getElementById('year').textContent = new Date().getFullYear();

    // Zeitraum (time period) filter with day picker - MUST be at global scope for inline onchange handler
    window.handleZeitraumChange = function(event, dashboardUrl) {
      const selected = event.target.value;
      if (!selected) {
        return;
      }
      if (selected === 'day-picker') {
        const dayPickerInput = document.getElementById('filter-day-picker');
        if (typeof flatpickr === 'undefined') {
          alert('Kalender konnte nicht geladen werden. Bitte Seite neu laden.');
          return;
        }
        if (!dayPickerInput._flatpickr) {
          flatpickr(dayPickerInput, {
            mode: 'single',
            dateFormat: 'Y-m-d',
            disableMobile: true,
            defaultDate: new Date(),
            onChange: function(selectedDates, dateStr, instance) {
              if (selectedDates.length > 0) {
                const url = new URL(dashboardUrl, window.location.origin);
                const params = new URLSearchParams(window.location.search);
                params.delete('weeks');
                params.set('days', '1');
                params.set('start_date', dateStr);
                window.location.href = url.toString() + '?' + params.toString();
              }
            }
          });
        }
        dayPickerInput._flatpickr.open();
      } else {
        const url = new URL(dashboardUrl, window.location.origin);
        const params = new URLSearchParams(window.location.search);
        params.delete('days');
        params.delete('start_date');
        params.set(selected.split('=')[0], selected.split('=')[1]);
        window.location.href = url.toString() + '?' + params.toString();
      }
    };

    window.addEventListener('DOMContentLoaded', () => {
      console.log('DOMContentLoaded fired for import modal');
      const importPrevMonthBtn = document.getElementById('import-previous-month-btn');
      const importModal = document.getElementById('previous-month-import-modal');
      const importContent = document.getElementById('previous-month-import-content');
      const importSubmitBtn = document.getElementById('previous-month-import-submit');
      const importCancelBtn = document.getElementById('previous-month-import-cancel');
      const importCloseBtn = document.getElementById('previous-month-import-close');
      console.log('importPrevMonthBtn:', importPrevMonthBtn);
      console.log('importModal:', importModal);

      const openImportModal = async () => {
        console.log('openImportModal called');
        if (!importModal || !importContent || !importSubmitBtn) {
          console.log('Missing elements:', { importModal, importContent, importSubmitBtn });
          return;
        }
        const sourceOffset = Number(document.getElementById('previous-month-import-source-offset')?.value || 1);
        const targetOffset = Number(document.getElementById('previous-month-import-target-offset')?.value || 1);
        console.log('Setting modal display to flex');
        importModal.style.display = 'flex';
        importContent.innerHTML = '<div class="alert alert-info" role="alert">Lade Einsätze aus der ausgewählten Woche...</div>';
        importSubmitBtn.disabled = true;
        try {
          const params = new URLSearchParams({
            source_offset: String(sourceOffset),
            target_offset: String(targetOffset),
          });
          const resp = await fetch(`/schedule/preview-import-previous-month?${params.toString()}`);
          if (!resp.ok) {
            throw new Error(`Server returned ${resp.status}`);
          }
          const data = await resp.json();
          const items = Array.isArray(data.items) ? data.items : [];
          if (!items.length) {
            importContent.innerHTML = '<div class="alert alert-warning" role="alert">Keine aktiven Einsätze im vorherigen Monat gefunden.</div>';
            return;
          }

          const table = document.createElement('table');
          table.className = 'table table-bordered table-sm';
          table.innerHTML = `
            <thead>
              <tr>
                <th style="width:1%;"><input type="checkbox" id="previous-month-import-select-all" aria-label="Alle auswählen"></th>
                <th>Mitarbeiter</th>
                <th>Aktiv</th>
                <th>Standort</th>
                <th>Quelle</th>
                <th>Ziel</th>
                <th>Zeit</th>
                <th>Konflikt</th>
              </tr>
            </thead>
            <tbody></tbody>
          `;
          const tbody = table.querySelector('tbody');
          items.forEach(item => {
            const row = document.createElement('tr');
            row.dataset.active = item.active ? 'true' : 'false';
            row.innerHTML = `
              <td><input type="checkbox" class="previous-month-import-checkbox" value="${item.id}"></td>
              <td>${item.employee}</td>
              <td>${item.active ? '<span class="badge bg-success" title="Der Mitarbeiter ist aktiv und kann importiert werden">Aktiv</span>' : '<span class="badge bg-secondary" title="Der Mitarbeiter ist inaktiv und wird standardmäßig ausgeblendet">Inaktiv</span>'}</td>
              <td>${item.site}</td>
              <td>${item.from_day}</td>
              <td>${item.to_day}</td>
              <td>${item.time}</td>
              <td>${item.conflict ? '<span class="text-warning" title="Diese Schicht verursacht einen Konflikt mit vorhandenen Planungen">Warnung</span>' : '—'}</td>
            `;
            tbody.appendChild(row);
          });

          importContent.innerHTML = '';
          // add active-only filter control
          const filterWrap = document.createElement('div');
          filterWrap.style.marginBottom = '0.5rem';
          filterWrap.innerHTML = `<label style="font-size:0.9rem;"><input type="checkbox" id="previous-month-only-active" style="margin-right:0.4rem;">Nur aktive anzeigen</label>`;
          importContent.appendChild(filterWrap);
          importContent.appendChild(table);

          const onlyActiveCheckbox = document.getElementById('previous-month-only-active');
          const applyActiveFilter = () => {
            const onlyActive = onlyActiveCheckbox && onlyActiveCheckbox.checked;
            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.forEach(r => {
              if (onlyActive && r.dataset.active !== 'true') {
                // hide and uncheck
                r.style.display = 'none';
                const cb = r.querySelector('.previous-month-import-checkbox');
                if (cb) cb.checked = false;
              } else {
                r.style.display = '';
              }
            });
            // refresh itemCheckboxes and submit button state
            const visibleChecked = Array.from(importContent.querySelectorAll('.previous-month-import-checkbox:checked')).filter(cb => cb.closest('tr').style.display !== 'none');
            importSubmitBtn.disabled = visibleChecked.length === 0;
          };
          if (onlyActiveCheckbox) {
            onlyActiveCheckbox.addEventListener('change', applyActiveFilter);
          }

          const selectAllCheckbox = document.getElementById('previous-month-import-select-all');
          const itemCheckboxes = Array.from(importContent.querySelectorAll('.previous-month-import-checkbox'));

          const updateImportSelection = () => {
            const selected = itemCheckboxes.filter(cb => cb.checked);
            importSubmitBtn.disabled = selected.length === 0;
          };

          itemCheckboxes.forEach(cb => cb.addEventListener('change', updateImportSelection));
          if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function () {
              itemCheckboxes.forEach(cb => { cb.checked = this.checked; });
              updateImportSelection();
            });
          }
        } catch (err) {
          importContent.innerHTML = `<div class="alert alert-danger" role="alert">Fehler beim Laden der Einsätze. Bitte Seite neu laden.</div>`;
          console.error(err);
        }
      };

      const closeImportModal = () => {
        if (importModal) {
          importModal.style.display = 'none';
        }
      };

      if (importPrevMonthBtn) {
        importPrevMonthBtn.addEventListener('click', openImportModal);
      }
      if (importCancelBtn) {
        importCancelBtn.addEventListener('click', closeImportModal);
      }
      if (importCloseBtn) {
        importCloseBtn.addEventListener('click', closeImportModal);
      }
      if (importModal) {
        importModal.addEventListener('click', function (e) {
          if (e.target === importModal) {
            closeImportModal();
          }
        });
      }
      if (importSubmitBtn) {
        importSubmitBtn.addEventListener('click', async () => {
          const checkedBoxes = Array.from(document.querySelectorAll('.previous-month-import-checkbox:checked'));
          const selectedIds = checkedBoxes.map(cb => cb.value).filter(Boolean);
          if (!selectedIds.length) {
            return;
          }
          const sourceOffset = Number(document.getElementById('previous-month-import-source-offset')?.value || 1);
          const targetOffset = Number(document.getElementById('previous-month-import-target-offset')?.value || 1);
          importSubmitBtn.disabled = true;
          importSubmitBtn.textContent = 'Importiere...';
          try {
            const resp = await fetch('/schedule/import-previous-month', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ selected_ids: selectedIds, source_offset: sourceOffset, target_offset: targetOffset }),
            });
            if (!resp.ok) {
              throw new Error(`Server returned ${resp.status}`);
            }
            const result = await resp.json();
            const summary = [];
            if (result.created) summary.push(`${result.created} Einsätze importiert`);
            if (result.skipped_existing) summary.push(`${result.skipped_existing} doppelt übersprungen`);
            if (result.skipped_conflict) summary.push(`${result.skipped_conflict} wegen Konflikten übersprungen`);
            if (result.skipped_inactive) summary.push(`${result.skipped_inactive} inaktive Mitarbeiter übersprungen`);
            alert(summary.join(String.fromCharCode(10)) || 'Import abgeschlossen.');
            window.location.reload();
          } catch (err) {
            importSubmitBtn.disabled = false;
            importSubmitBtn.textContent = 'Importieren';
            console.error(err);
            alert('Fehler beim Importieren. Bitte erneut versuchen.');
          }
        });
      }
    });

    (function () {
      const KEY = 'pm-sidebar-collapsed';
      const body = document.body;
      const btn = document.getElementById('sidebar-toggle');
      const setState = (val) => {
        body.classList.toggle('sidebar-collapsed', val);
        try { localStorage.setItem(KEY, val ? '1' : '0'); } catch (e) {}
      };
      const initial = (() => {
        try {
          const raw = localStorage.getItem(KEY);
          if (raw === null) return true; // default: collapsed (icons only)
          return raw === '1';
        } catch (e) {
          return true;
        }
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
          dayPicker.setCustomValidity('Bitte mindestens einen Tag auswählen.');
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

    // Batch selection/actions functionality
    const batchDeleteForm = document.getElementById('batch-delete-form');
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    const editSelectedBtn = document.getElementById('edit-selected-btn');
    const selectedCountSpan = document.getElementById('selected-count');
    const editSelectedCountSpan = document.getElementById('edit-selected-count');

    const getSelectedShiftCheckboxes = () => Array.from(document.querySelectorAll('.shift-checkbox:checked'));
    const getSelectedShiftIds = () => getSelectedShiftCheckboxes().map(cb => cb.value);

    function updateBatchActionButtons() {
      const checkboxes = document.querySelectorAll('.shift-checkbox');
      const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
      selectedCountSpan.textContent = checkedCount;
      if (editSelectedCountSpan) {
        editSelectedCountSpan.textContent = checkedCount;
      }
      deleteSelectedBtn.disabled = checkedCount === 0;
      if (editSelectedBtn) {
        editSelectedBtn.disabled = checkedCount === 0;
      }
    }

    if (batchDeleteForm) {
      batchDeleteForm.addEventListener('change', function(e) {
        if (e.target.classList.contains('shift-checkbox')) {
          updateBatchActionButtons();
        }
      });

      batchDeleteForm.addEventListener('submit', function(e) {
        const checkedCount = getSelectedShiftIds().length;
        if (checkedCount === 0) {
          e.preventDefault();
          return false;
        }
        if (!confirm(`${checkedCount} ausgewählte Einsätze löschen?`)) {
          e.preventDefault();
          return false;
        }
      });

      updateBatchActionButtons();
    }

    // Batch edit functionality
    const batchEditModal = document.getElementById('batch-edit-modal');
    const batchEditForm = document.getElementById('batch-edit-form');
    const batchEditHiddenInputs = document.getElementById('batch-edit-hidden-inputs');
    const batchEditCount = document.getElementById('batch-edit-count');

    function closeBatchEditModal() {
      if (batchEditModal) {
        batchEditModal.style.display = 'none';
      }
    }

    if (editSelectedBtn && batchEditModal && batchEditForm) {
      editSelectedBtn.addEventListener('click', function() {
        const selectedIds = getSelectedShiftIds();
        if (!selectedIds.length) {
          return;
        }

        if (batchEditHiddenInputs) {
          batchEditHiddenInputs.innerHTML = '';
          selectedIds.forEach((id) => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'shift_ids[]';
            input.value = id;
            batchEditHiddenInputs.appendChild(input);
          });
        }

        if (batchEditCount) {
          batchEditCount.textContent = String(selectedIds.length);
        }

        batchEditForm.reset();

        const firstSelectedId = selectedIds[0];
        const firstShiftPill = document.querySelector(`.shift-pill[data-shift-id="${firstSelectedId}"]`);
        if (firstShiftPill) {
          const dayInput = document.getElementById('batch-edit-day');
          const startInput = document.getElementById('batch-edit-start');
          const endInput = document.getElementById('batch-edit-end');
          const instructionsInput = document.getElementById('batch-edit-instructions');
          if (dayInput) dayInput.value = firstShiftPill.dataset.day || '';
          if (startInput) startInput.value = firstShiftPill.dataset.start || '';
          if (endInput) endInput.value = firstShiftPill.dataset.end || '';
          if (instructionsInput) instructionsInput.value = firstShiftPill.dataset.instructions || '';
        }

        batchEditModal.style.display = 'flex';
      });

      batchEditForm.addEventListener('submit', function(e) {
        const day = (document.getElementById('batch-edit-day')?.value || '').trim();
        const start = (document.getElementById('batch-edit-start')?.value || '').trim();
        const end = (document.getElementById('batch-edit-end')?.value || '').trim();
        const instructions = (document.getElementById('batch-edit-instructions')?.value || '').trim();

        if (!day && !start && !end && !instructions) {
          e.preventDefault();
          alert('Bitte mindestens ein Feld zum Aktualisieren setzen.');
          return false;
        }
        if ((start && !end) || (!start && end)) {
          e.preventDefault();
          alert('Bitte Start- und Endzeit gemeinsam angeben.');
          return false;
        }
        if (start && end && end <= start) {
          e.preventDefault();
          alert('Die End time must be after start time.');
          return false;
        }
      });

      document.getElementById('batch-edit-close')?.addEventListener('click', closeBatchEditModal);
      document.getElementById('batch-edit-cancel')?.addEventListener('click', closeBatchEditModal);
      batchEditModal.addEventListener('click', function(e) {
        if (e.target === batchEditModal) {
          closeBatchEditModal();
        }
      });
    }

    // Edit shift functionality
    const editModal = document.getElementById('edit-shift-modal');
    const editForm = document.getElementById('edit-shift-form');
    const editButtons = document.querySelectorAll('.shift-edit');

    editButtons.forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        const shiftPill = this.closest('.shift-pill') || this;
        const shiftId = shiftPill.dataset.shiftId || this.getAttribute('data-shift-id');
        const employeeId = shiftPill.dataset.employeeId || this.getAttribute('data-employee-id');
        const day = shiftPill.dataset.day || this.getAttribute('data-day');
        const start = shiftPill.dataset.start || this.getAttribute('data-start');
        const end = shiftPill.dataset.end || this.getAttribute('data-end');
        const instructions = shiftPill.dataset.instructions || this.getAttribute('data-instructions');

        document.getElementById('edit-shift-id').value = shiftId;
        document.getElementById('edit-shift-employee').value = employeeId;
        document.getElementById('edit-shift-day').value = day;
        document.getElementById('edit-shift-start').value = start;
        document.getElementById('edit-shift-end').value = end;
        document.getElementById('edit-shift-instructions').value = instructions || '';

        editForm.action = '/shift/' + shiftId + '/edit';
        editModal.style.display = 'flex';
      });
    });

    // Close modal when clicking outside
    if (editModal) {
      editModal.addEventListener('click', function(e) {
        if (e.target === editModal) {
          editModal.style.display = 'none';
        }
      });
    }

    // Drag and drop shifts between days
    let draggedShiftId = null;
    let draggedFromEmployeeId = null;

    document.querySelectorAll('.shift-pill[draggable="true"]').forEach((pill) => {
      pill.addEventListener('dragstart', (e) => {
        draggedShiftId = pill.getAttribute('data-shift-id');
        draggedFromEmployeeId = pill.getAttribute('data-employee-id') || null;
        pill.classList.add('dragging');
        if (e.dataTransfer) {
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', draggedShiftId || '');
        }
      });

      pill.addEventListener('dragend', () => {
        pill.classList.remove('dragging');
        document.querySelectorAll('.schedule-drop-target').forEach((cell) => {
          cell.classList.remove('schedule-drop-target');
        });
        draggedShiftId = null;
        draggedFromEmployeeId = null;
      });
    });

    document.querySelectorAll('.schedule-table tbody td[data-day]').forEach((cell) => {
      cell.addEventListener('dragover', (e) => {
        if (!draggedShiftId) {
          return;
        }
        const targetEmployeeId = cell.getAttribute('data-employee-id') || null;
        if (!targetEmployeeId) {
          return;
        }
        e.preventDefault();
        if (e.dataTransfer) {
          e.dataTransfer.dropEffect = 'move';
        }
        cell.classList.add('schedule-drop-target');
      });

      cell.addEventListener('dragleave', () => {
        cell.classList.remove('schedule-drop-target');
      });

      cell.addEventListener('drop', async (e) => {
        e.preventDefault();
        cell.classList.remove('schedule-drop-target');
        if (!draggedShiftId) {
          return;
        }

        const targetDay = cell.getAttribute('data-day');
        const targetEmployeeId = cell.getAttribute('data-employee-id') || null;
        if (!targetDay || !targetEmployeeId) {
          return;
        }

        try {
          const resp = await fetch(`/shift/${draggedShiftId}/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ day: targetDay, employee_id: targetEmployeeId }).toString(),
          });
          if (!resp.ok) {
            let backendMessage = '';
            try {
              const payload = await resp.json();
              backendMessage = payload && payload.error ? String(payload.error) : '';
            } catch (_err) {}
            throw new Error(backendMessage || `Server returned ${resp.status}`);
          }
          window.location.reload();
        } catch (err) {
          console.error(err);
          alert((err && err.message) ? err.message : 'Einsatz konnte nicht verschoben werden. Bitte erneut versuchen.');
        }
      });
    });
  </script>
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
app.config["PUBLIC_APP_URL"] = (os.getenv("PUBLIC_APP_URL") or "").strip().rstrip("/")

UPLOAD_FOLDER = os.path.join(APP_ROOT, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
PUBLIC_DOCUMENT_FOLDER = os.path.join(APP_ROOT, "private_uploads", "public_documents")
INSPECTION_PHOTO_FOLDER = os.path.join(APP_ROOT, "private_uploads", "inspection_photos")
EMPLOYEE_DOCUMENT_FOLDER = os.path.join(APP_ROOT, "private_uploads", "employee_documents")
os.makedirs(PUBLIC_DOCUMENT_FOLDER, exist_ok=True)
os.makedirs(INSPECTION_PHOTO_FOLDER, exist_ok=True)
os.makedirs(EMPLOYEE_DOCUMENT_FOLDER, exist_ok=True)
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic", "heif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "admin")

SUPPORTED_LANGUAGES = {"en", "de"}
DEFAULT_LANGUAGE = "de"

# Phrase-level translations applied app-wide on HTML responses.
# This keeps the single-file app maintainable without rewriting every template.
DE_HTML_REPLACEMENTS: dict[str, str] = {
  "Functions": "Funktionen",
  "All functions": "Alle Funktionen",
  "No system access": "Kein Systemzugriff",
  "Site manager": "Standortleiter",
  "Sales manager": "Vertriebsleiter",
  "Choose every function this person performs. A person can have more than one.": "W\u00e4hlen Sie alle Funktionen dieser Person aus. Mehrfachauswahl ist m\u00f6glich.",
  "Select all functions this person performs. Multiple functions are supported.": "W\u00e4hlen Sie alle Funktionen dieser Person aus. Mehrfachauswahl ist m\u00f6glich.",
  "Platform access must be enabled by an administrator before an employee can sign in. Other functions are stored on the employee record.": "Ein Administrator muss den Plattformzugang aktivieren, bevor sich ein Mitarbeiter anmelden kann. Weitere Funktionen werden im Mitarbeiterprofil gespeichert.",
  "Platform sign-in": "Plattformanmeldung",
  "Save platform access": "Plattformzugang speichern",
  "Functions and sign-in permissions for this employee.": "Funktionen und Anmeldeberechtigungen f\u00fcr diesen Mitarbeiter.",
  "Staff type": "Personaltyp",
  "Platform access": "Plattformzugang",
  "System access": "Systemzugriff",
  "Staff type / department": "Personaltyp / Abteilung",
  "Role / job title": "Rolle / Berufsbezeichnung",
  "The employee’s specific job title.": "Die konkrete Berufsbezeichnung des Mitarbeiters.",
  "The employee’s company function or department.": "Der Unternehmensbereich oder die Abteilung des Mitarbeiters.",
  "System access controls which parts of Elf’s Plan this employee can use.": "Der Systemzugriff legt fest, welche Bereiche von Elf’s Plan dieser Mitarbeiter nutzen kann.",
  "Choose the account’s permissions.": "Wählen Sie die Berechtigungen des Kontos.",
  "Employee email": "E-Mail-Adresse des Mitarbeiters",
  "Used for sign-in and credential delivery.": "Wird für die Anmeldung und den Versand der Zugangsdaten verwendet.",
  "Send sign-in details by email": "Zugangsdaten per E-Mail senden",
  "Enable platform access, set a valid email, and set the employee to Active before sending sign-in details.": "Aktivieren Sie den Plattformzugang, geben Sie eine gültige E-Mail-Adresse ein und setzen Sie den Mitarbeiter vor dem Versand der Zugangsdaten auf Aktiv.",
  "Email is not configured. Set the SMTP sender and password first.": "E-Mail ist nicht konfiguriert. Bitte richten Sie zuerst SMTP-Absender und Passwort ein.",
  "Enter a valid employee email address first.": "Geben Sie zuerst eine gültige Mitarbeiter-E-Mail-Adresse ein.",
  "Could not send the email. Check SMTP settings and try again.": "Die E-Mail konnte nicht gesendet werden. Prüfen Sie die SMTP-Einstellungen und versuchen Sie es erneut.",
  "All staff types": "Alle Funktionen",
  "All branches": "Alle Niederlassungen",
  "More filters": "Weitere Filter",
  "Manage staff across both branch offices": "Mitarbeitende an beiden Standorten verwalten",
  "All": "Alle",
  "Passive": "Passiv",
  "Employee status": "Mitarbeiterstatus",
  "Phone number": "Telefonnummer",
  "Download": "Herunterladen",
  "Employee status updated.": "Mitarbeiterstatus aktualisiert.",
  "Upload profile photo": "Profilbild hochladen",
  "Profile photo updated.": "Profilbild aktualisiert.",
  "Choose a profile photo to upload.": "Bitte ein Profilbild zum Hochladen auswählen.",
  "Choose a valid image file (PNG, JPG, GIF, or WebP).": "Bitte eine gültige Bilddatei auswählen (PNG, JPG, GIF oder WebP).",
  "Employee profile could not be found.": "Das Mitarbeiterprofil wurde nicht gefunden.",
  "Could not update your profile photo. Please try again.": "Das Profilbild konnte nicht aktualisiert werden. Bitte erneut versuchen.",
  "Cleaners without shifts this week": "Reinigungskräfte ohne Einsätze diese Woche",
  "Search name, role, email, phone, or city": "Nach Name, Rolle, E-Mail, Telefon oder Stadt suchen",
  "Cleaner": "Reinigungskraft",
  "Branch office": "Niederlassung",
  "Office administrator": "Büroadministration",
  "IT": "IT",
  "Reception": "Empfang",
  "Intern": "Praktikant/in",
  "Graphic designer": "Grafikdesigner/in",
  "Other": "Sonstiges",
  "Wien": "Wien",
  "Graz": "Graz",
  "Enable platform access and create sign-in details": "Plattformzugang und Anmeldedaten erstellen",
  "Turn this on only for employees who need an app account.": "Nur für Mitarbeitende aktivieren, die ein App-Konto benötigen.",
  "Overview": "Übersicht",
  "Manage employees": "Mitarbeiter verwalten",
  "Manage sites": "Standorte verwalten",
  "Site directory": "Standortverzeichnis",
  "Site database": "Standortdatenbank",
  "Manage client sites and service locations": "Kundenstandorte und Einsatzorte verwalten",
  "Add site": "Standort hinzuf\u00fcgen",
  "On this page": "Auf dieser Seite",
  "Scheduled this week": "Diese Woche eingeplant",
  "Delete site": "Standort löschen",
  "Close site": "Standort schließen",
  "This site has invoices and cannot be deleted. Set it to inactive instead.": "Dieser Standort hat Rechnungen und kann nicht gelöscht werden. Setzen Sie ihn stattdessen auf inaktiv.",
  "Site deleted. Its shifts and inspection reports were also deleted.": "Standort gelöscht. Zugehörige Einsätze und Kontrollberichte wurden ebenfalls gelöscht.",
  "Search sites": "Standorte suchen",
  "Search site, company, contact, email, phone or address": "Standort, Firma, Kontakt, E-Mail, Telefon oder Adresse suchen",
  "All site managers": "Alle Objektleiter",
  "Unassigned manager": "Kein Objektleiter zugewiesen",
  "All clients": "Alle Kunden",
  "+ Add filter": "+ Filter hinzufügen",
  "Scheduled this week": "Diese Woche eingeplant",
  "Profiles": "Profile",
  "Invoices": "Rechnungen",
  "Log out": "Abmelden",
  "Profile Center": "Profilzentrum",
  "Employee profiles": "Mitarbeiterprofile",
  "Client profiles": "Kundenprofile",
  "Employee registration": "Mitarbeiterprofil",
  "Client registration": "Kundenprofil",
  "Billing contact name": "Name der Rechnungs-Kontaktperson",
  "Billing contact email": "E-Mail Rechnungs-Kontakt",
  "Billing phone": "Rechnungstelefon",
  "Customer ID": "Kundennummer",
  "Notes": "Notizen",
  "Upload photo": "Foto hochladen",
  "Upload logo": "Logo hochladen",
  "Save profile": "Profil speichern",
  "Create New Invoice": "Neue Rechnung erstellen",
  "Generate an invoice for work completed": "Rechnung für erbrachte Arbeit erstellen",
  "Company Name": "Firmenname",
  "Contact Name": "Kontaktname",
  "Contact Email": "Kontakt-E-Mail",
  "Contact Phone": "Kontakttelefon",
  "Billing Address": "Rechnungsadresse",
  "Invoice Month": "Rechnungsmonat",
  "Total Hours": "Gesamtstunden",
  "Days Until Due": "Tage bis Fälligkeit",
  "Tax Rate (%)": "Steuersatz (%)",
  "Create Invoice": "Rechnung erstellen",
  "Edit Invoice": "Rechnung bearbeiten",
  "Invoice Details": "Rechnungsdetails",
  "Bill To:": "Rechnung an:",
  "Billing Contact Person:": "Rechnungs-Kontaktperson:",
  "Address:": "Adresse:",
  "Hourly Rate": "Stundensatz",
  "Due Date": "Fälligkeitsdatum",
  "Paid Date": "Bezahlt am",
  "Subtotal": "Zwischensumme",
  "TOTAL": "GESAMT",
  "Draft": "Entwurf",
  "Sent": "Gesendet",
  "Paid": "Bezahlt",
  "Overdue": "Überfällig",
  "Delete": "Löschen",
  "Back": "Zurück",
  "Send Email": "E-Mail senden",
  "Mark as Paid": "Als bezahlt markieren",
  "Mark as Unpaid": "Als unbezahlt markieren",
  "Monthly Income": "Monatseinnahmen",
  "Auto Generate": "Automatisch erstellen",
  "Created From": "Erstellt von",
  "Created To": "Erstellt bis",
  "Apply Filters": "Filter anwenden",
  "Clear": "Zurücksetzen",
  "Lead-Center": "Lead-Center",
  "Assign coverage": "Einsätze zuweisen",
  "Crawler": "Crawler",
  "No sites found.": "Keine Standorte gefunden.",
  "No employees found.": "Keine Mitarbeiter gefunden.",
  "No invoices found.": "Keine Rechnungen gefunden.",
  "Client Contract": "Kundenvertrag",
  "Operations overview": "Betriebsübersicht",
  "This week at a glance": "Diese Woche im Überblick",
  "Employees": "Mitarbeiter",
  "Sites": "Standorte",
  "Unassigned sites": "Unzugewiesene Standorte",
  "Newest sites": "Neueste Standorte",
  "Sites without coverage": "Standorte ohne Abdeckung",
  "All sites are covered for the current week.": "Alle Standorte sind für die aktuelle Woche abgedeckt.",
  "Manage": "Verwalten",
  "Team directory": "Teamverzeichnis",
  "Location library": "Standortübersicht",
  "Billing & Invoicing": "Abrechnung & Rechnungen",
  "Financial Overview": "Finanzübersicht",
  "Invoice": "Rechnung",
  "Invoice #": "Rechnungsnr.",
  "Date:": "Datum:",
  "Date": "Datum",
  "Description": "Beschreibung",
  "Quantity": "Menge",
  "Rate": "Satz",
  "Amount": "Betrag",
  "hours": "Stunden",
  "hr": "Std",
  "Work at": "Arbeit bei",
  "Upon receipt": "Bei Erhalt",
  "Status": "Status",
  "Save Changes": "Änderungen speichern",
  "Cancel": "Abbrechen",
  "Paid": "Bezahlt",
  "DRAFT": "ENTWURF",
  "SENT": "GESENDET",
  "PAID": "BEZAHLT",
  "Generate contract PDF": "Vertrags-PDF erstellen",
  "Please fill all contract fields.": "Bitte alle Vertragsfelder ausfüllen.",
  "Please upload a valid PDF contract file.": "Bitte eine gültige PDF-Vertragsdatei hochladen.",
  "Uploaded PDF is empty.": "Hochgeladene PDF ist leer.",
  "Upload a contract PDF or place a template at uploads/contract_template.pdf or static/uploads/contract_template.pdf.": "Laden Sie eine Vertrags-PDF hoch oder legen Sie eine Vorlage unter uploads/contract_template.pdf oder static/uploads/contract_template.pdf ab.",
  "Please fill Name des partners, Firma, and Tel./ Fax / E-Mail before generating contract.": "Bitte füllen Sie Name des Partners, Firma und Tel./ Fax / E-Mail aus, bevor Sie den Vertrag erstellen.",
  "Name des partners": "Name des Partners",
  "Firma": "Firma",
  "Tel./ Fax / E-Mail": "Tel./ Fax / E-Mail",
  "Upload contract PDF": "Vertrags-PDF hochladen",
  "Optional if a server template exists at uploads/contract_template.pdf or static/uploads/contract_template.pdf (or set CONTRACT_TEMPLATE_PATH). If uploaded, this file is used.": "Optional, wenn eine Servervorlage unter uploads/contract_template.pdf oder static/uploads/contract_template.pdf existiert (oder CONTRACT_TEMPLATE_PATH gesetzt ist). Bei Upload wird diese Datei verwendet.",
  "Download PDF": "PDF herunterladen",
  "Back to manage sites": "Zurück zu Standorte verwalten",
  "No address": "Keine Adresse",
  "No role": "Keine Rolle",
  "Phone": "Telefon",
  "Emergency contact name": "Name Notfallkontakt",
  "Emergency contact phone": "Telefon Notfallkontakt",
  "Address": "Adresse",
  "Page": "Seite",
  "Prev": "Zurück",
  "Next": "Weiter",
  "clients": "Kunden",
  "Lead-Center": "Lead-Center",
  "Leads": "Leads",
  "New Leads": "Neue Leads",
  "In Contact": "In Kontakt",
  "Qualified": "Qualifiziert",
  "Closed": "Abgeschlossen",
  "Source": "Quelle",
  "Stage": "Phase",
  "Add lead": "Lead hinzufügen",
  "Delete selected": "Ausgewählte löschen",
  "Send selected emails": "Ausgewählte E-Mails senden",
  "total invoices": "Rechnungen gesamt",
  "Create": "Erstellen",
  "Create New": "Neu erstellen",
  "Select a site": "Standort auswählen",
  "Site": "Standort",
  "Site *": "Standort *",
  "Please select a valid site.": "Bitte einen gültigen Standort auswählen.",
  "Please choose a valid invoice month.": "Bitte einen gültigen Rechnungsmonat auswählen.",
  "created successfully!": "erfolgreich erstellt!",
  "updated successfully.": "erfolgreich aktualisiert.",
  "deleted": "gelöscht",
  "Invalid status selected.": "Ungültiger Status ausgewählt.",
  "Invalid due date format.": "Ungültiges Fälligkeitsdatum.",
  "Invalid paid date format.": "Ungültiges Bezahldatum.",
  "Hourly rate and total hours are required.": "Stundensatz und Gesamtstunden sind erforderlich.",
  "No recipient email set for invoice": "Keine Empfänger-E-Mail für Rechnung gesetzt",
  "Email configuration missing. Set sender email and SMTP password.": "E-Mail-Konfiguration fehlt. Bitte Absender-E-Mail und SMTP-Passwort setzen.",
  "Thank you for your business!": "Vielen Dank für Ihr Vertrauen!",
  "Best regards,": "Mit freundlichen Grüßen,",
  "Your Company": "Ihr Unternehmen",
  'Client database': 'Kundendatenbank',
  'Manage clients': 'Kunden verwalten',
  'Client': 'Kunde',
  'Clients': 'Kunden',
  'All clients': 'Alle Kunden',
  'Active clients': 'Aktive Kunden',
  'With shifts this week': 'Mit Einsätzen diese Woche',
  'Without shifts this week': 'Ohne Einsätze diese Woche',
  'Search company, contact, email, phone, address or tax ID': 'Firma, Kontakt, E-Mail, Telefon, Adresse oder Steuer-ID suchen',
  'Search': 'Suchen',
  'Clear search': 'Suche zurücksetzen',
  'Contact': 'Kontakt',
  'Service address': 'Einsatzadresse',
  'Rate': 'Stundensatz',
  'Shifts': 'Einsätze',
  'Status': 'Status',
  'Actions': 'Aktionen',
  'No email': 'Keine E-Mail',
  'Active': 'Aktiv',
  'Inactive': 'Inaktiv',
  'Edit client': 'Kunden bearbeiten',
  'No clients found': 'Keine Kunden gefunden',
  'Adjust your search or add a client to the database.': 'Passen Sie die Suche an oder fügen Sie einen Kunden hinzu.',
  'Page': 'Seite',
  'Previous': 'Zurück',
  'Next': 'Weiter',
  'Add client': 'Kunden hinzufügen',
  'Company / client name': 'Firmen- / Kundenname',
  'Service location name': 'Name des Einsatzstandorts',
  'Defaults to company name': 'Standardmäßig der Firmenname',
  'Logo / attachment': 'Logo / Anhang',
  'Upload a client logo or image.': 'Laden Sie ein Kundenlogo oder Bild hoch.',
  'Current logo': 'Aktuelles Logo',
  'Contact person': 'Kontaktperson',
  'Email': 'E-Mail',
  'Phone': 'Telefon',
  'Billing and service': 'Abrechnung und Leistung',
  'Billing address': 'Rechnungsadresse',
  'VAT ID': 'USt-IdNr.',
  'Customer / tax ID': 'Kunden- / Steuer-ID',
  'Hourly rate (?)': 'Stundensatz (€)',
  'Contract start': 'Vertragsbeginn',
  'Contract end': 'Vertragsende',
  'Notes': 'Notizen',
  'Client notes': 'Kundennotizen',
  'Add client details, access notes, or preferences': 'Kundendetails, Zugangshinweise oder Präferenzen eintragen',
  'Open full client profile': 'Vollständiges Kundenprofil öffnen',
  'Cancel': 'Abbrechen',
  'Create client': 'Kunden anlegen',
  'Save changes': 'Änderungen speichern',
  'Collapse navigation': 'Navigation einklappen',
  'Expand navigation': 'Navigation ausklappen',
  'Navigation': 'Navigation',
  'Manage employees': 'Mitarbeiter verwalten',
  'Profiles': 'Profile',
  'Plan schedule': 'Planung öffnen',
  'Crawler': 'Crawler',
  'Invoices': 'Rechnungen',
  'Sign out': 'Abmelden',
  'Menu': 'Menü',
  'A client with the same name and service address already exists.': 'Ein Kunde mit demselben Namen und derselben Einsatzadresse ist bereits vorhanden.',
  'Another client already uses that name and service address.': 'Ein anderer Kunde verwendet bereits diesen Namen und diese Einsatzadresse.',
  'Enter contract dates in a valid format.': 'Geben Sie gültige Vertragsdaten ein.',
  'Invalid client image. Use PNG, JPG, GIF, WEBP, or HEIC.': 'Ungültiges Kundenbild. Erlaubte Formate: PNG, JPG, GIF, WEBP oder HEIC.',
  'Client added.': 'Kunde hinzugefügt.',
  'Client name is required.': 'Der Kundenname ist erforderlich.',
  'Client updated.': 'Kunde aktualisiert.',
  "Language switcher": "Sprachauswahl",
}

# Override client-page phrases using Unicode escapes so labels remain UTF-8 safe.
DE_HTML_REPLACEMENTS.update({
  "Lead Center": "Lead-Center",
  "Lead pipeline totals": "Lead-Pipeline-Übersicht",
  "Website bookings arrive as new leads. Move each lead through Contacted to Converted.": "Website-Buchungen werden als neue Leads übernommen. Verschieben Sie jeden Lead über Kontaktiert zu Gewonnen.",
  "New Leads": "Neue Leads",
  "Contacted": "Kontaktiert",
  "Converted": "Gewonnen",
  "Add lead": "Lead hinzufügen",
  "Save lead": "Lead speichern",
  "All stages": "Alle Phasen",
  "Newest first": "Neueste zuerst",
  "Oldest first": "Älteste zuerst",
  "Apply": "Anwenden",
  "Clear": "Zurücksetzen",
  "Copy page emails": "E-Mail-Adressen kopieren",
  "No leads": "Keine Leads",
  "Edit lead": "Lead bearbeiten",
  "shift(s) were saved despite scheduling conflicts. Review:": "Einsatz/Einsätze wurden trotz Planungskonflikten gespeichert. Bitte prüfen:",
  "Shift was saved despite scheduling conflicts. Review:": "Der Einsatz wurde trotz Planungskonflikten gespeichert. Bitte prüfen:",
  "Employees were assigned despite scheduling conflicts. Review:": "Mitarbeitende wurden trotz Planungskonflikten zugewiesen. Bitte prüfen:",
  "shift(s) were assigned despite scheduling conflicts. Review the schedule.": "Einsatz/Einsätze wurden trotz Planungskonflikten zugewiesen. Bitte prüfen Sie den Dienstplan.",
  "duplicate shift(s) were saved despite scheduling conflicts. Review the schedule.": "Doppelte Einsätze wurden trotz Planungskonflikten gespeichert. Bitte prüfen Sie den Dienstplan.",
  "Lead created": "Lead erstellt",
  "Putzelf Marketing - Employee database": "Putzelf Marketing - Mitarbeiterdatenbank",
  "Login code": "Anmeldecode",
  "Cleaner": "Reinigungskraft",
  "Usage group": "Verwendungsgruppe",
  "Edit": "Bearbeiten",
  "Employee name is required.": "Der Mitarbeitername ist erforderlich.",
  "Invalid employee image. Use PNG, JPG, GIF, WEBP, or HEIC.": "Ung\u00fcltiges Mitarbeiterbild. Erlaubte Formate: PNG, JPG, GIF, WEBP oder HEIC.",
  "Client database": "Kundendatenbank",
  "Client summary": "Kundenübersicht",
  "Search clients": "Kunden suchen",
  "Close": "Schließen",
  "Client logo": "Kundenlogo",
  "Putzelf Marketing \u2014 Client Database": "Putzelf Marketing \u2014 Kundendatenbank",
  "Manage clients": "Kunden verwalten",
  "Client": "Kunde",
  "Clients": "Kunden",
  "All clients": "Alle Kunden",
  "Active clients": "Aktive Kunden",
  "With shifts this week": "Mit Eins\u00e4tzen diese Woche",
  "Without shifts this week": "Ohne Eins\u00e4tze diese Woche",
  "Search company, contact, email, phone, address or tax ID": "Firma, Kontakt, E-Mail, Telefon, Adresse oder Steuer-ID suchen",
  "Search": "Suchen",
  "Clear search": "Suche zur\u00fccksetzen",
  "Contact": "Kontakt",
  "Service address": "Einsatzadresse",
  "Rate": "Stundensatz",
  "Shifts": "Eins\u00e4tze",
  "Actions": "Aktionen",
  "No email": "Keine E-Mail",
  "Active": "Aktiv",
  "Passive": "Passiv",
  "Inactive": "Inaktiv",
  "Edit client": "Kunden bearbeiten",
  "No clients found": "Keine Kunden gefunden",
  "Adjust your search or add a client to the database.": "Passen Sie die Suche an oder f\u00fcgen Sie einen Kunden hinzu.",
  "Page": "Seite",
  "Previous": "Zur\u00fcck",
  "Next": "Weiter",
  "Add client": "Kunden hinzuf\u00fcgen",
  "Company / client name": "Firmen- / Kundenname",
  "Service location name": "Name des Einsatzstandorts",
  "Defaults to company name": "Standardm\u00e4\u00dfig der Firmenname",
  "Logo / attachment": "Logo / Anhang",
  "Upload a client logo or image.": "Laden Sie ein Kundenlogo oder Bild hoch.",
  "Current logo": "Aktuelles Logo",
  "Contact person": "Kontaktperson",
  "Email": "E-Mail",
  "Phone": "Telefon",
  "Billing and service": "Abrechnung und Leistung",
  "Billing address": "Rechnungsadresse",
  "VAT ID": "USt-IdNr.",
  "Customer / tax ID": "Kunden- / Steuer-ID",
  "Hourly rate (€)": "Stundensatz (€)",
  "Contract start": "Vertragsbeginn",
  "Contract end": "Vertragsende",
  "Notes": "Notizen",
  "Client notes": "Kundennotizen",
  "Add client details, access notes, or preferences": "Kundendetails, Zugangshinweise oder Pr\u00e4ferenzen eintragen",
  "Open full client profile": "Vollst\u00e4ndiges Kundenprofil \u00f6ffnen",
  "Cancel": "Abbrechen",
  "Create client": "Kunden anlegen",
  "Save changes": "\u00c4nderungen speichern",
  "Collapse navigation": "Navigation einklappen",
  "Expand navigation": "Navigation ausklappen",
  "Overview": "\u00dcbersicht",
  "Manage employees": "Mitarbeiter verwalten",
  "Profiles": "Profile",
  "Plan schedule": "Planung \u00f6ffnen",
  "Invoices": "Rechnungen",
  "Sign out": "Abmelden",
  "Menu": "Men\u00fc",
  "Client name is required.": "Der Kundenname ist erforderlich.",
  "A client with the same name and service address already exists.": "Ein Kunde mit demselben Namen und derselben Einsatzadresse ist bereits vorhanden.",
  "Another client already uses that name and service address.": "Ein anderer Kunde verwendet bereits diesen Namen und diese Einsatzadresse.",
  "Enter contract dates in a valid format.": "Geben Sie g\u00fcltige Vertragsdaten ein.",
  "Invalid client image. Use PNG, JPG, GIF, WEBP, or HEIC.": "Ung\u00fcltiges Kundenbild. Erlaubte Formate: PNG, JPG, GIF, WEBP oder HEIC.",
  "Client added.": "Kunde hinzugef\u00fcgt.",
  "Client updated.": "Kunde aktualisiert.",
})


DE_HTML_REPLACEMENTS.update({
  "Client profile": "Kundenprofil",
  "Site profile": "Standortprofil",
  "All sites": "Alle Standorte",
  "Active": "Aktiv",
  "Inactive": "Inaktiv",
  "Site identity, service address, status, and assigned manager.": "Standortdaten, Einsatzadresse, Status und zuständige Standortleitung.",
  "Edit fields here, then save your changes below.": "Bearbeiten Sie die Felder direkt und speichern Sie Ihre Änderungen unten.",
  "Primary site contact and billing information.": "Hauptkontakt und Rechnungsinformationen des Standorts.",
  "Update the contract period and download the employee contract.": "Bearbeiten Sie die Vertragslaufzeit und laden Sie den Vertrag herunter.",
  "Keep access instructions and internal site notes up to date.": "Halten Sie Zugangshinweise und interne Standortnotizen aktuell.",
  "Save site": "Standort speichern",
  "Save & download contract": "Speichern und Vertrag herunterladen",
  "Assigned site manager": "Zuständige Standortleitung",
  "Site logo": "Standortlogo",
  "Site record": "Standortdatensatz",
  "Update site logo": "Standortlogo aktualisieren",
  "Site status updated.": "Standortstatus aktualisiert.",
  "Site profile saved.": "Standortprofil gespeichert.",
  "Another site already uses that name and service address.": "Ein anderer Standort verwendet bereits diesen Namen und diese Einsatzadresse.",
  "Company and service location names are required.": "Firmenname und Einsatzstandort sind erforderlich.",
  "Invalid site image. Use PNG, JPG, GIF, WEBP, or HEIC.": "Ungültiges Standortbild. Erlaubte Formate: PNG, JPG, GIF, WEBP oder HEIC.",
  "Client pages": "Kundenseiten",
  "Client information sections": "Kundeninformationsbereiche",
  "Information": "Informationen",
  "Schedule": "Einsatzplan",
  "Invoices": "Rechnungen",
  "Documents": "Dokumente",
  "General": "Allgemein",
  "Contacts": "Kontakte",
  "Contract": "Vertrag",
  "Other": "Sonstiges",
  "Client and service location information.": "Informationen zum Kunden und Einsatzstandort.",
  "Primary client contact and billing recipient information.": "Primärer Kundenkontakt und Informationen zum Rechnungsempfänger.",
  "Contract partner, contact, and term details.": "Vertragspartner, Kontakt und Vertragslaufzeit.",
  "Client notes and account details.": "Kundennotizen und Kontodetails.",
  "Recent shifts scheduled for this client location.": "Die letzten für diesen Kundenstandort geplanten Einsätze.",
  "Recent invoices linked to this client.": "Die letzten Rechnungen für diesen Kunden.",
  "Client image and contract tools.": "Kundenbild und Vertragswerkzeuge.",
  "Company / client name": "Firmen- / Kundenname",
  "Service location name": "Name des Einsatzstandorts",
  "Service address": "Einsatzadresse",
  "Status": "Status",
  "Hourly rate": "Stundensatz",
  "Shifts on record": "Erfasste Einsätze",
  "Contact person": "Kontaktperson",
  "Email": "E-Mail",
  "Phone": "Telefon",
  "Invoice recipient": "Rechnungsempfänger",
  "Billing address": "Rechnungsadresse",
  "VAT ID": "USt-IdNr.",
  "Customer / tax ID": "Kunden- / Steuer-ID",
  "Contract partner": "Vertragspartner",
  "Contract contact details": "Kontaktdaten zum Vertrag",
  "Contract start": "Vertragsbeginn",
  "Contract end": "Vertragsende",
  "No notes added yet.": "Noch keine Notizen vorhanden.",
  "Client record ID": "Kundendatensatz-ID",
  "Created / record reference": "Erstellt / Datensatzreferenz",
  "Date": "Datum",
  "Time": "Uhrzeit",
  "Employee": "Mitarbeiter",
  "Notes": "Notizen",
  "Open shift": "Offener Einsatz",
  "No shifts have been scheduled for this client yet.": "Für diesen Kunden wurden noch keine Einsätze geplant.",
  "Invoice": "Rechnung",
  "Issued": "Ausgestellt",
  "Due": "Fällig",
  "Amount": "Betrag",
  "No invoices have been created for this client yet.": "Für diesen Kunden wurden noch keine Rechnungen erstellt.",
  "Client logo": "Kundenlogo",
  "No client logo or document has been added.": "Es wurde noch kein Kundenlogo oder Dokument hinzugefügt.",
  "Open contract tools": "Vertragswerkzeuge öffnen",
})


DE_HTML_REPLACEMENTS.update({
  "Employee database": "Mitarbeiterdatenbank",
  "Employee profile": "Mitarbeiterprofil",
  "Employee profiles": "Mitarbeiterprofile",
  "Employee pages": "Mitarbeiterseiten",
  "Employee information sections": "Mitarbeiter-Informationsbereiche",
  "Team directory": "Teamverzeichnis",
  "Employee": "Mitarbeiter",
  "employees shown": "Mitarbeiter angezeigt",
  "total": "insgesamt",
  "All employees": "Alle Mitarbeiter",
  "Shown on this page": "Auf dieser Seite angezeigt",
  "Scheduled today": "Heute eingeplant",
  "Without shifts this week": "Diese Woche ohne Einsatz",
  "New employee sign-in details": "Neue Mitarbeiter-Zugangsdaten",
  "Login code:": "Anmeldecode:",
  "PIN:": "PIN:",
  "Save these details before leaving this page.": "Speichern Sie diese Daten, bevor Sie diese Seite verlassen.",
  "Search employees": "Mitarbeiter suchen",
  "Search name, role, email, phone, or city": "Name, Rolle, E-Mail, Telefon oder Stadt suchen",
  "All work types": "Alle Arbeitszeitmodelle",
  "Filter by role": "Nach Rolle filtern",
  "Marginal employment": "Geringfügige Beschäftigung",
  "Clear search": "Suche zur\u00fccksetzen",
  "Search": "Suchen",
  "Contact": "Kontakt",
  "Role": "Rolle",
  "Contract": "Vertrag",
  "Shifts": "Eins\u00e4tze",
  "Actions": "Aktionen",
  "No contact details": "Keine Kontaktdaten",
  "Active": "Aktiv",
  "Inactive": "Inaktiv",
  "Edit": "Bearbeiten",
  "No employees found": "Keine Mitarbeiter gefunden",
  "Adjust your search or add an employee.": "Passen Sie die Suche an oder f\u00fcgen Sie einen Mitarbeiter hinzu.",
  "Page": "Seite",
  "Previous": "Zur\u00fcck",
  "Next": "Weiter",
  "Add employee": "Mitarbeiter hinzuf\u00fcgen",
  "Employee profiles": "Mitarbeiterprofile",
  "Employee profile center": "Mitarbeiterprofilzentrum",
  "Create employee": "Mitarbeiter anlegen",
  "Edit employee": "Mitarbeiter bearbeiten",
  "Send sign-in details": "Zugangsdaten senden",
  "Fix": "Beheben",
  "Delete employee": "Mitarbeiter l\u00f6schen",
  "Weekly shifts in a calendar view.": "Wocheneinsätze in der Kalenderansicht.",
  "All day": "Ganztägig",
  "Today": "Heute",
  "No shifts scheduled this week.": "Für diese Woche sind keine Einsätze geplant.",
  "Documents": "Dokumente",
  "Upload and keep employee-related documents in one place.": "Laden Sie mitarbeiterbezogene Dokumente hoch und verwalten Sie diese zentral.",
  "Choose a document": "Dokument auswählen",
  "Upload document": "Dokument hochladen",
  "Uploaded": "Hochgeladen",
  "Employee document uploaded.": "Mitarbeiterdokument wurde hochgeladen.",
  "Employee document deleted.": "Mitarbeiterdokument wurde gelöscht.",
  "Delete this employee document?": "Dieses Mitarbeiterdokument löschen?",
  "Delete document": "Dokument löschen",
  "Delete": "Löschen",
  "Enable platform access to send sign-in details.": "Aktivieren Sie den Plattformzugang, um die Zugangsdaten zu senden.",
  "Set the employee to Active to send sign-in details.": "Setzen Sie den Mitarbeiterstatus auf Aktiv, um die Zugangsdaten zu senden.",
  "Add a valid login email to send sign-in details.": "Fügen Sie eine gültige Login-E-Mail-Adresse hinzu, um die Zugangsdaten zu senden.",
  "Upload a PDF, Word document, or image file.": "Laden Sie eine PDF-, Word- oder Bilddatei hoch.",
  "No employee documents have been uploaded yet.": "Es wurden noch keine Mitarbeiterdokumente hochgeladen.",
  "Save changes": "\u00c4nderungen speichern",
  "Close": "Schlie\u00dfen",
  "Employee": "Mitarbeiter",
  "Full name *": "Vollst\u00e4ndiger Name *",
  "Full name": "Vollst\u00e4ndiger Name",
  "Phone": "Telefon",
  "Street address": "Stra\u00dfe und Hausnummer",
  "Postal code": "Postleitzahl",
  "City": "Stadt",
  "Emergency contact": "Notfallkontakt",
  "Emergency phone": "Telefon des Notfallkontakts",
  "Contact details": "Kontaktdaten",
  "Employment and contract": "Besch\u00e4ftigung und Vertrag",
  "Employment type": "Besch\u00e4ftigungsart",
  "Work type": "Arbeitszeitmodell",
  "Part-time": "Teilzeit",
  "Full-time": "Vollzeit",
  "Hourly pay": "Stundenlohn",
  "Weekly hours": "Wochenstunden",
  "Contract start": "Vertragsbeginn",
  "Contract end": "Vertragsende",
  "Pay group type": "Lohngruppentyp",
  "Pay group": "Lohngruppe",
  "Usage group": "Verwendungsgruppe",
  "Group number": "Gruppennummer",
  "Profile photo": "Profilbild",
  "Notes": "Notizen",
  "Employee notes": "Mitarbeiternotizen",
  "Add notes or work preferences": "Notizen oder Arbeitspr\u00e4ferenzen eintragen",
  "Open employee profile center": "Mitarbeiterprofilzentrum \u00f6ffnen",
  "Information": "Informationen",
  "Schedule": "Einsatzplan",
  "Documents": "Dokumente",
  "General": "Allgemein",
  "Contacts": "Kontakte",
  "Employment": "Besch\u00e4ftigung",
  "Account access": "Kontozugang",
  "Other": "Sonstiges",
  "Employee identity and current work status.": "Mitarbeiteridentit\u00e4t und aktueller Arbeitsstatus.",
  "Personal contact and emergency details.": "Pers\u00f6nliche Kontakt- und Notfalldaten.",
  "Work type, pay, and group information.": "Arbeitszeitmodell, Verg\u00fctung und Lohngruppeninformationen.",
  "Contract period and the employee contract document.": "Vertragslaufzeit und Mitarbeitervertragsdokument.",
  "Employee sign-in details.": "Zugangsdaten des Mitarbeiters.",
  "Additional notes and employee preferences.": "Zus\u00e4tzliche Notizen und Arbeitspr\u00e4ferenzen.",
  "Recent shifts and assigned client locations.": "Letzte Eins\u00e4tze und zugewiesene Kundenstandorte.",
  "Employee image and contract document.": "Mitarbeiterbild und Vertragsdokument.",
  "Full name": "Vollst\u00e4ndiger Name",
  "Role": "Rolle",
  "Employee record ID": "Mitarbeiterdatensatz-ID",
  "Email": "E-Mail",
  "Address": "Adresse",
  "Postal code and city": "Postleitzahl und Stadt",
  "Work type": "Arbeitszeitmodell",
  "Employee profile": "Mitarbeiterprofil",
  "Current PIN": "Aktuelle PIN",
  "Login email": "Anmelde-E-Mail",
  "New 4-digit PIN": "Neue 4-stellige PIN",
  "Leave blank to keep current": "Leer lassen, um die aktuelle PIN beizubehalten",
  "Save sign-in details": "Zugangsdaten speichern",
  "Prepare sign-in details to share": "Zugangsdaten zum Teilen vorbereiten",
  "No notes added yet.": "Noch keine Notizen vorhanden.",
  "Total shifts": "Eins\u00e4tze gesamt",
  "Date": "Datum",
  "Time": "Uhrzeit",
  "Client / location": "Kunde / Standort",
  "Shift notes": "Einsatznotizen",
  "Open shift": "Offener Einsatz",
  "No shifts have been scheduled for this employee yet.": "F\u00fcr diesen Mitarbeiter wurden noch keine Eins\u00e4tze geplant.",
  "Download employee contract": "Mitarbeitervertrag herunterladen",
  "This uses the existing employee contract template.": "Hierf\u00fcr wird die bestehende Vertragsvorlage f\u00fcr Mitarbeitende verwendet.",
  "Generated from the configured employee contract template.": "Wird mit der konfigurierten Vertragsvorlage f\u00fcr Mitarbeitende erstellt.",
  "Save & download contract": "Speichern und Vertrag herunterladen",
  "Edit contract details and generate PDF": "Vertragsdaten bearbeiten und PDF erstellen",
  "Contract partner": "Vertragspartner",
  "Contract contact details": "Vertragskontaktdaten",
  "Phone, fax, or email": "Telefon, Fax oder E-Mail",
  "Fill in the contract partner, company, and phone, fax, or email before generating the contract.": "Bitte Vertragspartner, Firma sowie Telefon, Fax oder E-Mail ausfüllen, bevor Sie den Vertrag erstellen.",
  "Delete employee": "Mitarbeiter l\u00f6schen",
  "Delete this employee?": "Diesen Mitarbeiter l\u00f6schen?",
  "Employee added.": "Mitarbeiter hinzugef\u00fcgt.",
  "Employee updated.": "Mitarbeiter aktualisiert.",
  "Employee deleted.": "Mitarbeiter gel\u00f6scht.",
  "Login details are ready to share.": "Die Zugangsdaten k\u00f6nnen geteilt werden.",
  "Login details updated.": "Zugangsdaten aktualisiert.",
  "Could not update login details.": "Zugangsdaten konnten nicht aktualisiert werden.",
  "Login code is required to save credentials.": "Zum Speichern der Zugangsdaten ist ein Anmeldecode erforderlich.",
  "That login code is already in use.": "Dieser Anmeldecode wird bereits verwendet.",
  "PINs must be exactly 4 digits.": "PINs m\u00fcssen genau 4 Ziffern haben.",
  "Employee not found.": "Mitarbeiter nicht gefunden.",
  "Employee template not found. Place employee_template.docx in uploads/ or static/uploads/.": "Mitarbeitervorlage nicht gefunden. Legen Sie employee_template.docx in uploads/ oder static/uploads/ ab.",
  "DOCX generation is unavailable. Check the application log for the python-docx import error.": "Die DOCX-Erstellung ist nicht verf\u00fcgbar. Pr\u00fcfen Sie das Anwendungsprotokoll auf den python-docx-Importfehler.",
})




DE_HTML_REPLACEMENTS.update({
  "Operations portal": "Betriebsportal",
  "Manage your team, sites, schedule, and monthly inspections.": "Verwalten Sie Ihr Team, Standorte, Einsatzplanung und monatliche Kontrollen.",
  "Assigned sites": "Zugewiesene Standorte",
  "Inspections": "Kontrollen",
  "Monthly site inspections": "Monatliche Standortkontrollen",
  "Monthly inspection report": "Monatlicher Kontrollbericht",
  "Inspection reports": "Kontrollberichte",
  "Inspection checklist": "Kontrollliste",
  "Public document library": "\u00d6ffentliche Dokumentbibliothek",
  "Public documents": "\u00d6ffentliche Dokumente",
  "Public safety library": "\u00d6ffentliche Sicherheitsbibliothek",
  "Public QR code": "\u00d6ffentlicher QR-Code",
  "Safety and work documents": "Sicherheits- und Arbeitsdokumente",
  "These reference documents are available without signing in.": "Diese Dokumente sind ohne Anmeldung verf\u00fcgbar.",
  "Manager / employee sign in": "Anmeldung f\u00fcr Leitung / Mitarbeitende",
  "No public documents have been published yet.": "Es wurden noch keine \u00f6ffentlichen Dokumente ver\u00f6ffentlicht.",
  "Publish a document": "Dokument ver\u00f6ffentlichen",
  "Published documents": "Ver\u00f6ffentlichte Dokumente",
  "PDF or DOCX file": "PDF- oder DOCX-Datei",
  "Monthly inspection checklist": "Monatliche Kontrollliste",

  "Add an inspection area": "Kontrollbereich hinzuf\u00fcgen",
  "Add area": "Bereich hinzuf\u00fcgen",
  "Open checklist": "Kontrollliste \u00f6ffnen",
  "Inspect this month": "Diesen Monat kontrollieren",
  "Save inspection": "Kontrolle speichern",
  "Optional note": "Optionale Notiz",
  "Optional photo": "Optionales Foto",
  "Checked": "Kontrolliert",
  "Not checked": "Nicht kontrolliert",
  "In progress": "In Bearbeitung",
  "Complete": "Abgeschlossen",
  "Not started": "Nicht begonnen",
  "View report": "Bericht anzeigen",
  "Edit checklist": "Kontrollliste bearbeiten",
  "Download QR code PNG": "QR-Code-PNG herunterladen",
  "Download PNG": "PNG herunterladen",
  "Download PDF": "PDF herunterladen",
  "Scan to open the public document library": "Scannen, um die öffentliche Dokumentenbibliothek zu öffnen",
  "Site inspection": "Standortkontrolle",
  "All inspections": "Alle Kontrollen",
  "Inspection areas by site": "Kontrollbereiche je Standort",
  "Inspection setup": "Kontrollbereich einrichten",
  "Each site has its own checklist. Set up only the areas that apply to that location.": "Jeder Standort hat eine eigene Kontrollliste. Richten Sie nur die Bereiche ein, die für diesen Standort gelten.",
  "Inspection report": "Kontrollbericht",
  "Inspection overview": "Kontrollübersicht",
  "Use the quick actions or check areas one by one.": "Nutzen Sie die Schnellaktionen oder markieren Sie einzelne Bereiche.",
  "Mark all checked": "Alle als kontrolliert markieren",
  "Clear all checks": "Alle Markierungen entfernen",
  "areas checked": "Bereiche kontrolliert",
  "Edit note and photo": "Notiz und Foto bearbeiten",
  "Add note or photo": "Notiz oder Foto hinzufügen",
  "Add a note about this area": "Notiz zu diesem Bereich hinzufügen",
  "View saved photo": "Gespeichertes Foto ansehen",
  "Inspection changes save to the selected month.": "Die Kontrolländerungen werden für den ausgewählten Monat gespeichert.",
  "Track completion by site and see which areas still need attention.": "Verfolgen Sie den Fortschritt je Standort und sehen Sie, wo noch Kontrollen ausstehen.",
  "Edit checklists": "Kontrolllisten bearbeiten",
  "Report month": "Berichtsmonat",
  "Download report": "Bericht herunterladen",
  "In progress": "In Bearbeitung",
  "Not started": "Nicht begonnen",
  "Needs setup": "Einrichtung erforderlich",
  "Areas checked": "Kontrollierte Bereiche",
  "areas": "Bereiche",
  "Resource center": "Ressourcenzentrale",
  "Putzelf Public resources": "Putzelf öffentliche Ressourcen",
  "All documents": "Alle Dokumente",
  "in": "in",
  "No documents match this search.": "Keine Dokumente entsprechen dieser Suche.",
  "Find and download the latest safety rules and work instructions.": "Finden Sie aktuelle Sicherheitsregeln und Arbeitsanweisungen und laden Sie diese herunter.",
  "documents": "Dokumente",
  "categories": "Kategorien",
  "These resources are available without signing in.": "Diese Dokumente sind ohne Anmeldung verfügbar.",
  "Try another title or category.": "Suchen Sie nach einem anderen Titel oder einer anderen Kategorie.",
  "Please check back later for safety and work resources.": "Schauen Sie später wieder vorbei, um Sicherheits- und Arbeitsdokumente zu finden.",
  "Publish and organize documents that anyone can open from your QR landing page.": "Veröffentlichen und organisieren Sie Dokumente, die über den QR-Code öffentlich zugänglich sind.",
  "Public QR code": "Öffentlicher QR-Code",
  "View public library": "Öffentliche Bibliothek ansehen",
  "Published documents": "Veröffentlichte Dokumente",
  "PDF files": "PDF-Dateien",
  "DOCX files": "DOCX-Dateien",
  "Add a resource to the public library.": "Fügen Sie ein Dokument zur öffentlichen Bibliothek hinzu.",
  "Document title": "Dokumenttitel",
  "e.g. Safety rules for cleaning staff": "z. B. Sicherheitsregeln für Reinigungskräfte",
  "Choose or enter a category": "Kategorie auswählen oder eingeben",
  "Choose a PDF or DOCX file": "PDF- oder DOCX-Datei auswählen",
  "PDF and Word documents are supported": "PDF- und Word-Dokumente werden unterstützt",
  "No file selected": "Keine Datei ausgewählt",
  "Publish document": "Dokument veröffentlichen",
  "Published files are accessible without signing in.": "Veröffentlichte Dateien sind ohne Anmeldung zugänglich.",
  "Organized resources available in the public library.": "Sortierte Dokumente in der öffentlichen Bibliothek.",
  "Search documents": "Dokumente suchen",
  "Filter documents by category": "Dokumente nach Kategorie filtern",
  "Download": "Herunterladen",
  "Remove": "Entfernen",
  "No documents match these filters.": "Keine Dokumente entsprechen diesen Filtern.",
  "Try another search or choose a different category.": "Ändern Sie die Suche oder wählen Sie eine andere Kategorie.",
  "No documents published yet": "Noch keine Dokumente veröffentlicht",
  "Upload a PDF or DOCX file to make it available in the public library.": "Laden Sie eine PDF- oder DOCX-Datei hoch, um sie in der öffentlichen Bibliothek bereitzustellen.",
  "Search sites or areas": "Standorte oder Bereiche suchen",
  "Filter sites by inspection status": "Standorte nach Kontrollstatus filtern",
  "Needs attention": "Offene Kontrollen",
  "Inspection progress": "Kontrollfortschritt",
  "areas": "Bereiche",
  "No inspection submitted this month": "Diesen Monat wurde keine Kontrolle eingereicht.",
  "No sites match this search or filter.": "Keine Standorte entsprechen dieser Suche oder diesem Filter.",
  "Try a different search or select all sites.": "Ändern Sie die Suche oder wählen Sie alle Standorte aus.",
  "No sites are in the database.": "Es sind keine Standorte in der Datenbank vorhanden.",
  "Add a site to start tracking inspections.": "Legen Sie einen Standort an, um Kontrollen zu verfolgen.",
  "Site details": "Standortdetails",
  "Save": "Speichern",
  "Archive": "Archivieren",
  "Restore": "Reaktivieren",
  "Choose the areas that apply to this site. Active areas appear in each new monthly inspection.": "Wählen Sie die passenden Bereiche für diesen Standort aus. Aktive Bereiche erscheinen in jeder neuen Monatskontrolle.",
  "Archived": "Archiviert",
  "Suggestions available": "Verfügbare Vorschläge",
  "Add an inspection area": "Kontrollbereich hinzufügen",
  "Create a custom area for this site.": "Erstellen Sie einen eigenen Bereich für diesen Standort.",
  "Area name": "Bereichsname",
  "e.g. Loading bay, stairwell, or patient rooms": "z. B. Ladebereich, Treppenhaus oder Patientenzimmer",
  "Add area": "Bereich hinzufügen",
  "Add only what applies. You can rename areas below at any time.": "Fügen Sie nur passende Bereiche hinzu. Sie können diese unten jederzeit umbenennen.",
  "All suggestions are already on this checklist.": "Alle Vorschläge sind bereits in dieser Kontrollliste enthalten.",
  "Checklist areas": "Kontrolllistenbereiche",
  "Rename, archive, or restore areas for this site.": "Benennen Sie Bereiche um, archivieren oder reaktivieren Sie sie.",
  "Search areas": "Bereiche suchen",
  "Filter checklist areas": "Kontrolllistenbereiche filtern",
  "All": "Alle",
  "No inspection areas yet": "Noch keine Kontrollbereiche",
  "Add a custom area or choose from the suggestions above.": "Fügen Sie einen eigenen Bereich hinzu oder wählen Sie einen der obigen Vorschläge.",
  "No checklist areas match this search.": "Keine Kontrolllistenbereiche entsprechen dieser Suche.",
  "Ready for inspections": "Bereit für Kontrollen",
  "Needs areas": "Bereiche erforderlich",
  "Active areas": "Aktive Bereiche",
  "Search by site name or address": "Standortname oder Adresse suchen",
  "Ready": "Bereit",
  "Needs setup": "Einrichtung erforderlich",
  "sites shown": "Standorte angezeigt",
  "No address added": "Keine Adresse hinterlegt",
  "active area": "aktiver Bereich",
  "Set up checklist": "Kontrollliste einrichten",
  "No sites match these filters.": "Keine Standorte entsprechen diesen Filtern.",
  "Try a different search or show all sites.": "Ändern Sie die Suche oder zeigen Sie alle Standorte an.",
  "No sites to configure yet": "Noch keine Standorte vorhanden",
  "Add a site first, then build its inspection checklist.": "Legen Sie zuerst einen Standort an und erstellen Sie danach die Kontrollliste.",
  "Inspection areas": "Kontrollbereiche",
  "Site checklist": "Standort-Prüfliste",
  "These areas belong only to this site. New monthly inspections use its active areas; saved inspection records keep their original area names.": "Diese Bereiche gehören nur zu diesem Standort. Neue Monatskontrollen verwenden die aktiven Bereiche; gespeicherte Kontrollen behalten ihre ursprünglichen Bereichsnamen.",
  "Each site has its own checklist. Add only the areas that apply to that location.": "Jeder Standort hat eine eigene Prüfliste. Fügen Sie nur Bereiche hinzu, die für diesen Standort gelten.",
  "Add an area for this site": "Bereich für diesen Standort hinzufügen",
  "Areas for this site": "Bereiche für diesen Standort",
  "No inspection areas have been added to this site yet.": "Diesem Standort wurden noch keine Kontrollbereiche hinzugefügt.",
  "No inspection areas are configured for this site yet. Add the areas that apply to this location before beginning its monthly inspection.": "Für diesen Standort sind noch keine Kontrollbereiche eingerichtet. Fügen Sie die passenden Bereiche hinzu, bevor Sie mit der Monatskontrolle beginnen.",
  "Manage this site's areas": "Bereiche dieses Standorts verwalten",
  "Set up areas": "Bereiche einrichten",
  "Manage areas": "Bereiche verwalten",
  "active areas": "aktive Bereiche",
  "sites need their own areas set up": "Standorte benötigen eigene Kontrollbereiche",
  "Common suggestions": "Häufige Vorschläge",
  "Add all missing suggestions": "Alle fehlenden Vorschl\u00e4ge hinzuf\u00fcgen",
  "Archive all active": "Alle aktiven archivieren",
  "All missing suggested areas have been added.": "Alle fehlenden vorgeschlagenen Bereiche wurden hinzugef\u00fcgt.",
  "All active areas for this site were archived.": "Alle aktiven Bereiche dieses Standorts wurden archiviert.",
  "There are no active areas to archive.": "Es gibt keine aktiven Bereiche zum Archivieren.",
  "Archive all active inspection areas for this site? You can restore them later.": "Alle aktiven Pr\u00fcfbereiche dieses Standorts archivieren? Sie k\u00f6nnen sie sp\u00e4ter wiederherstellen.",
  "Add only the areas that apply to this site.": "Fügen Sie nur Bereiche hinzu, die für diesen Standort gelten.",
  "Inspections complete": "Kontrollen abgeschlossen",
  "Checklist not configured": "Kontrollliste nicht eingerichtet",
  "No checklist areas configured.": "Keine Kontrollbereiche eingerichtet.",
})

SCHEDULE_DE_REPLACEMENTS = {
  "Management": "Verwaltung", "Workspace": "Arbeitsbereich", "Overview": "\u00dcbersicht",
  "Clients & Sites": "Kunden und Standorte", "Schedule": "Einsatzplanung", "Inspections": "Kontrollen",
  "Inspection reports": "Kontrollberichte", "Inspection areas": "Kontrollbereiche", "Public documents": "\u00d6ffentliche Dokumente",
  "Account": "Konto", "Log out": "Abmelden", "Collapse menu": "Men\u00fc einklappen", "Open menu": "Men\u00fc \u00f6ffnen",
  "Today": "Heute", "View": "Ansicht", "Notifications are active": "Benachrichtigungen sind aktiv",
  "Notifications are paused": "Benachrichtigungen sind pausiert", "Employees receive alerts when shifts are added, changed, assigned, or removed.": "Mitarbeitende erhalten eine Benachrichtigung, wenn Eins\u00e4tze erstellt, ge\u00e4ndert, zugewiesen oder entfernt werden.",
  "Shift updates and daily reminders are paused": "Einsatz\u00e4nderungen und t\u00e4gliche Erinnerungen sind pausiert",
  "Resume to send queued employee alerts.": "Setzen Sie die Benachrichtigungen fort, um vorgemerkte Hinweise zu senden.",
  "Daily reminders are sent at 6:00 AM while notifications are active.": "T\u00e4gliche Erinnerungen werden bei aktiven Benachrichtigungen um 6:00 Uhr gesendet.",
  "No queued employee alerts.": "Keine vorgemerkten Mitarbeiterbenachrichtigungen.", "employee alert(s) queued.": "Mitarbeiterbenachrichtigung(en) vorgemerkt.",
  "Checking connection...": "Verbindung wird gepr\u00fcft...", "Connected. Notification status is synced.": "Verbunden. Der Benachrichtigungsstatus ist synchronisiert.",
  "Offline. Notification settings will sync after reconnecting.": "Offline. Die Benachrichtigungseinstellungen werden nach der Verbindung synchronisiert.",
  "Notification status could not be loaded. Check your connection and retry.": "Der Benachrichtigungsstatus konnte nicht geladen werden. Pr\u00fcfen Sie die Verbindung und versuchen Sie es erneut.",
  "Offline \u2014 notification status may be out of date": "Offline \u2013 der Benachrichtigungsstatus ist m\u00f6glicherweise veraltet",
  "Notifications active": "Benachrichtigungen aktiv", "Notifications paused": "Benachrichtigungen pausiert",
  "Pause notifications": "Benachrichtigungen pausieren", "Resume notifications": "Benachrichtigungen fortsetzen",
  "Pause notifications for all employees": "Benachrichtigungen f\u00fcr alle Mitarbeitenden pausieren",
  "Resume notifications and release queued alerts": "Benachrichtigungen fortsetzen und vorgemerkte Hinweise senden",
  "Pausing queues shift alerts and daily reminders. Resume sends queued alerts. The pause ends automatically at midnight.": "W\u00e4hrend der Pause werden Einsatzbenachrichtigungen und t\u00e4gliche Erinnerungen vorgemerkt. Beim Fortsetzen werden die vorgemerkten Hinweise gesendet. Die Pause endet automatisch um Mitternacht.",
  "Pause notifications?": "Benachrichtigungen pausieren?", "Resume notifications?": "Benachrichtigungen fortsetzen?",
  "When you resume, each affected employee will receive their queued shift updates. Notifications automatically resume at midnight.": "Beim Fortsetzen erhalten die jeweils betroffenen Mitarbeitenden ihre vorgemerkten Einsatz\u00e4nderungen. Um Mitternacht werden die Benachrichtigungen automatisch fortgesetzt.",
  "queued employee alert(s) will become available as soon as notifications resume.": "vorgemerkte Mitarbeiterbenachrichtigung(en) werden beim Fortsetzen verf\u00fcgbar.",
  "Confirm pause": "Pause best\u00e4tigen", "Resume and notify": "Fortsetzen und benachrichtigen", "Saving...": "Wird gespeichert...",
  "Week navigation": "Wochennavigation", "Previous week": "Vorherige Woche", "Next week": "N\u00e4chste Woche",
  "Choose schedule date range": "Einsatzzeitraum ausw\u00e4hlen", "Previous month": "Vorheriger Monat", "Next month": "N\u00e4chster Monat",
  "Calendar days": "Kalendertage", "Quick date ranges": "Schnellauswahl f\u00fcr Zeitr\u00e4ume",
  "Unassigned shifts": "Unbesetzte Eins\u00e4tze", "All shifts": "Alle Eins\u00e4tze", "0\u201324 hours": "0\u201324 Stunden",
  "Split by": "Aufteilung", "Time window": "Zeitraum", "Employees": "Mitarbeitende", "Employee": "Mitarbeiter",
  "Objects": "Standorte", "All employees": "Alle Mitarbeitenden", "Orders": "Auftr\u00e4ge", "Day": "Tag", "Week": "Woche", "2 weeks": "2 Wochen", "Month": "Monat", "Custom range": "Benutzerdefinierter Zeitraum",
  "Schedule overview": "Einsatz\u00fcbersicht", "Create shift": "Einsatz erstellen", "Search employees or shifts": "Mitarbeitende oder Eins\u00e4tze suchen",
  "Employee groups": "Mitarbeitergruppen", "Add filter": "Filter hinzuf\u00fcgen", "Work type": "Arbeitszeitmodell", "All work types": "Alle Arbeitszeitmodelle",
  "Employee role": "Mitarbeiterrolle", "All roles": "Alle Rollen", "Shift assignment": "Einsatzzuweisung", "Assigned shifts": "Zugewiesene Eins\u00e4tze",
  "Open shifts": "Offene Eins\u00e4tze", "Day of week": "Wochentag", "Every day": "Jeden Tag",
  "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch", "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag", "Sunday": "Sonntag",
  "Employee availability": "Mitarbeiterverf\u00fcgbarkeit", "Availability start date": "Beginn der Verf\u00fcgbarkeit", "Availability end date": "Ende der Verf\u00fcgbarkeit",
  "Available from": "Verf\u00fcgbar ab", "Available until": "Verf\u00fcgbar bis", "Find available employees": "Verf\u00fcgbare Mitarbeitende finden",
  "Clear filters": "Filter zur\u00fccksetzen", "filters": "Filter", "shifts selected": "Eins\u00e4tze ausgew\u00e4hlt", "shift selected": "Einsatz ausgew\u00e4hlt",
  "Clear selection": "Auswahl aufheben", "Duplicate": "Duplizieren", "Release": "Freigeben", "Assign": "Zuweisen", "Delete": "L\u00f6schen",
  "No shifts in the selected period": "Keine Eins\u00e4tze im ausgew\u00e4hlten Zeitraum", "Adjust the dates or filters, or create a shift.": "Passen Sie den Zeitraum oder die Filter an oder erstellen Sie einen Einsatz.",
  "Sites": "Standorte", "Resize employee column": "Mitarbeiterspalte anpassen", "Drag to resize employee column": "Ziehen, um die Mitarbeiterspalte anzupassen",
  "Select site shift": "Standorteinsatz ausw\u00e4hlen", "Select shift for ": "Einsatz ausw\u00e4hlen f\u00fcr ", "Click to edit shift": "Klicken, um den Einsatz zu bearbeiten",
  "Edit shift": "Einsatz bearbeiten", "Editing": "Bearbeiten", "Add employees": "Mitarbeitende hinzuf\u00fcgen", "Remove assignment": "Zuweisung entfernen",
  "Create shift on this date": "Einsatz an diesem Tag erstellen", "Create shift at this site": "Einsatz an diesem Standort erstellen", "Create open shift": "Offenen Einsatz erstellen",
  "Repeating schedule": "Wiederkehrender Einsatz", "employee(s) assigned": "Mitarbeitende zugewiesen", "Assigned employees": "Zugewiesene Mitarbeitende",
  "Schedule type": "Einsatzart", "Split schedule by": "Einsatzplan aufteilen nach", "Language selector": "Sprachauswahl", "One-time": "Einmalig", "Repeating": "Wiederholend", "Site": "Standort", "Select a site": "Standort ausw\u00e4hlen",
  "Select employees": "Mitarbeitende ausw\u00e4hlen", "Select one or more employees.": "W\u00e4hlen Sie eine oder mehrere Mitarbeitende aus.",
  "Create without assigning an employee": "Ohne Mitarbeiterzuweisung erstellen", "Date": "Datum", "Start date": "Startdatum", "Start": "Beginn", "Start time": "Beginn",
  "End": "Ende", "End time": "Ende", "Duration": "Dauer", "Comment": "Kommentar", "Optional notes for this shift": "Optionale Notiz zu diesem Einsatz",
  "Review the time and employees before creating the shift.": "Pr\u00fcfen Sie Zeit und Mitarbeitende, bevor Sie den Einsatz erstellen.", "Create another shift": "Weiteren Einsatz erstellen",
  "Add employees to this shift": "Mitarbeitende zu diesem Einsatz hinzuf\u00fcgen", "Date, site, and time will match the selected shift.": "Datum, Standort und Uhrzeit entsprechen dem ausgew\u00e4hlten Einsatz.",
  "Select one or more employees": "Eine oder mehrere Mitarbeitende ausw\u00e4hlen", "Add selected": "Auswahl hinzuf\u00fcgen", "Search employees": "Mitarbeitende suchen",
  "Optional notes for this shift": "Optionale Notiz zu diesem Einsatz", "Leave blank to keep existing notes": "Leer lassen, um die bisherigen Notizen beizubehalten",
  "Import shifts": "Eins\u00e4tze importieren", "Choose the source week and how many weeks ahead to copy.": "W\u00e4hlen Sie die Quellwoche und wie viele Wochen voraus kopiert werden soll.",
  "Source week (back)": "Quellwoche (zur\u00fcck)", "Current week": "Aktuelle Woche", "1 week back": "Vor 1 Woche", "2 weeks back": "Vor 2 Wochen", "3 weeks back": "Vor 3 Wochen",
  "Target (weeks ahead)": "Ziel (Wochen voraus)", "+1 week": "+1 Woche", "+2 weeks": "+2 Wochen", "+3 weeks": "+3 Wochen", "+4 weeks": "+4 Wochen",
  "Loading shifts for the selected month...": "Eins\u00e4tze f\u00fcr den ausgew\u00e4hlten Monat werden geladen...", "Loading shifts for the selected week...": "Eins\u00e4tze f\u00fcr die ausgew\u00e4hlte Woche werden geladen...",
  "No active shifts found in the previous month.": "Im Vormonat wurden keine aktiven Eins\u00e4tze gefunden.", "Show active shifts only": "Nur aktive Eins\u00e4tze anzeigen",
  "This employee is active and can be imported": "Dieser Mitarbeiter ist aktiv und kann importiert werden", "Active": "Aktiv", "Inactive": "Inaktiv",
  "This shift conflicts with an existing schedule": "Dieser Einsatz \u00fcberschneidet sich mit einem bestehenden Einsatzplan", "Warning": "Warnung",
  "Could not load shifts. Please reload the page.": "Eins\u00e4tze konnten nicht geladen werden. Bitte laden Sie die Seite neu.",
  "Importing...": "Import wird ausgef\u00fchrt...", "Import complete.": "Import abgeschlossen.", "Import failed. Please try again.": "Import fehlgeschlagen. Bitte versuchen Sie es erneut.",
  "Edit multiple shifts": "Mehrere Eins\u00e4tze bearbeiten", "selected shifts.": "ausgew\u00e4hlte Eins\u00e4tze.", "New date (optional)": "Neues Datum (optional)",
  "New start time (optional)": "Neue Startzeit (optional)", "New end time (optional)": "Neue Endzeit (optional)", "New notes (optional)": "Neue Notizen (optional)",
  "Apply changes": "\u00c4nderungen anwenden", "New start date": "Neues Startdatum", "Selected shifts will be copied to the new dates, preserving their spacing, times, and employees.": "Die ausgew\u00e4hlten Eins\u00e4tze werden auf die neuen Daten kopiert. Zeitabst\u00e4nde, Uhrzeiten und Mitarbeitende bleiben erhalten.",
  "Assign shifts": "Eins\u00e4tze zuweisen", "Select an employee": "Mitarbeiter ausw\u00e4hlen", "Cancel": "Abbrechen", "Close": "Schlie\u00dfen", "Save changes": "\u00c4nderungen speichern",
  "Available employees": "Verf\u00fcgbare Mitarbeitende", "Searching...": "Suche l\u00e4uft...", "No available employees found for this period.": "F\u00fcr diesen Zeitraum wurden keine verf\u00fcgbaren Mitarbeitenden gefunden.",
  "Network error while loading.": "Netzwerkfehler beim Laden.", "Choose a start date.": "W\u00e4hlen Sie ein Startdatum aus.", "Could not load the calendar. Please reload the page.": "Der Kalender konnte nicht geladen werden. Bitte laden Sie die Seite neu.",
  "Select a start date.": "W\u00e4hlen Sie ein Startdatum aus.", "Invalid time": "Ung\u00fcltige Uhrzeit", "Select an employee or create the shift as unassigned.": "W\u00e4hlen Sie eine mitarbeitende Person aus oder erstellen Sie den Einsatz unbesetzt.",
  "The end time must be after the start time.": "Die Endzeit muss nach der Startzeit liegen.", "Choose at least one field to update.": "W\u00e4hlen Sie mindestens ein Feld zum Aktualisieren aus.",
  "Enter both a start and end time.": "Geben Sie sowohl eine Start- als auch eine Endzeit ein.", "Keep at least one employee assigned to this shift.": "Lassen Sie mindestens eine Person diesem Einsatz zugewiesen.",
  "Select at least one employee.": "W\u00e4hlen Sie mindestens eine mitarbeitende Person aus.", "Could not move the shift. Please try again.": "Der Einsatz konnte nicht verschoben werden. Bitte versuchen Sie es erneut.",
  "Custom range": "Benutzerdefinierter Zeitraum", "Could not update notifications.": "Benachrichtigungen konnten nicht aktualisiert werden.",
  "Pause": "Pausieren", "Resume": "Fortsetzen", "Checking connection...": "Verbindung wird geprüft...", "Unassigned": "Unbesetzt",
  "Repeat every": "Wiederholen alle", "week(s)": "Woche(n)", "Repeat on": "Wiederholen am", "End date": "Enddatum", "hrs": "Std.",
  "Mon": "Mo", "Tue": "Di", "Wed": "Mi", "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So",
  "Source": "Quelle", "Target": "Ziel", "Time": "Uhrzeit", "Conflict": "Konflikt", "Import": "Importieren",
  "Show active shifts only": "Nur aktive Einsätze anzeigen", "Available employees only": "Nur verfügbare Mitarbeitende",
  "Remove this employee from the shift?": "Diese Person aus dem Einsatz entfernen?", "Create": "Erstellen", "Select": "Auswählen",
  "Unassign selected employee(s); keep the shift open for reassignment": "Ausgewählte Mitarbeiterzuweisungen lösen; Einsätze zur Neuzuweisung offen lassen",
  "Add employee": "Mitarbeiter hinzufügen", "Notifications": "Benachrichtigungen", "Notifications: checking status": "Benachrichtigungen: Status wird geprüft",
}
SCHEDULE_HTML_REPLACEMENTS = {**DE_HTML_REPLACEMENTS, **SCHEDULE_DE_REPLACEMENTS}


def _build_translation_pattern(replacements: dict[str, str]):
  keys = sorted(replacements, key=len, reverse=True)
  return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(key) for key in keys) + r")(?!\w)")


_DE_HTML_PATTERN = _build_translation_pattern(DE_HTML_REPLACEMENTS)
_SCHEDULE_HTML_PATTERN = _build_translation_pattern(SCHEDULE_HTML_REPLACEMENTS)

def _get_current_language() -> str:
  value = (session.get("lang") or DEFAULT_LANGUAGE).strip().lower()
  return value if value in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def _t(text: str) -> str:
  if _get_current_language() != "de":
    return text
  return DE_HTML_REPLACEMENTS.get(text, text)


def _translate_text_fragment(text: str, schedule_page: bool = False) -> str:
  replacements = SCHEDULE_HTML_REPLACEMENTS if schedule_page else DE_HTML_REPLACEMENTS
  pattern = _SCHEDULE_HTML_PATTERN if schedule_page else _DE_HTML_PATTERN
  return pattern.sub(lambda match: replacements[match.group(0)], text)


def _translate_html_content(content: str) -> str:
  if _get_current_language() != "de":
    return content
  schedule_page = request.path.rstrip("/") == "/schedule"
  try:
    soup = BeautifulSoup(content, "html.parser")
    for node in soup.find_all(string=True):
      parent_name = (node.parent.name or "").lower() if node.parent else ""
      if parent_name in {"script", "style"}:
        continue
      original = str(node)
      replaced = _translate_text_fragment(original, schedule_page)
      if replaced != original:
        node.replace_with(replaced)
    for element in soup.find_all(True):
      for attribute in ("placeholder", "title", "aria-label", "alt"):
        value = element.get(attribute)
        if isinstance(value, str):
          element[attribute] = _translate_text_fragment(value, schedule_page)
    return str(soup)
  except Exception:
    return content


def _build_language_switcher_markup() -> str:
  args_next = request.args.to_dict(flat=True)
  args_next.pop("lang", None)
  next_query = urlencode(args_next)
  next_path = f"{request.path}?{next_query}" if next_query else request.path
  href_en = url_for("set_language", lang_code="en", next=next_path)
  href_de = url_for("set_language", lang_code="de", next=next_path)
  current = _get_current_language()
  en_active = "active" if current == "en" else ""
  de_active = "active" if current == "de" else ""
  en_current = 'aria-current="true"' if current == "en" else ""
  de_current = 'aria-current="true"' if current == "de" else ""
  pwa_install_button = ""
  if session.get("role") == "site_manager":
    pwa_install_button = '<button type="button" id="manager-pwa-install" class="ep-pwa-install-button" aria-label="Install site manager app" title="Install site manager app"><i class="bi bi-download" aria-hidden="true"></i><span>Install app</span></button>'
  return f'''
  <div id="global-page-navbar" class="ep-global-topbar">
    <span class="ep-global-brand"><img class="ep-global-brand-mark" src="/static/employee-icon-192.png" alt=""><span class="ep-global-brand-name">Elf's <strong>Plan</strong></span></span>
    <div class="ep-global-topbar-actions">{pwa_install_button}
    <nav id="global-language-switcher" class="lang-switcher" aria-label="Language selector">
    <a href="{href_en}" class="{en_active}" title="Switch to English" aria-label="Switch to English" {en_current}><span>EN</span></a>
    <a href="{href_de}" class="{de_active}" title="Auf Deutsch (&Ouml;sterreich) wechseln" aria-label="Auf Deutsch (&Ouml;sterreich) wechseln" {de_current}><span aria-hidden="true">&#x1F1E6;&#x1F1F9;</span><span>DE</span></a>
    </nav>
    </div>
  </div>
  '''


@app.before_request
def _language_before_request():
  requested = (request.args.get("lang") or "").strip().lower()
  if requested in SUPPORTED_LANGUAGES:
    session["lang"] = requested


@app.before_request
def _cleanup_shift_photos_before_request():
  global _LAST_SHIFT_PHOTO_CLEANUP_DATE
  if request.path.startswith("/static/"):
    return
  today_marker = date.today()
  if _LAST_SHIFT_PHOTO_CLEANUP_DATE == today_marker:
    return
  db = SessionLocal()
  try:
    _cleanup_expired_shift_photos(db)
    _LAST_SHIFT_PHOTO_CLEANUP_DATE = today_marker
  finally:
    db.close()


@app.route("/set-language/<lang_code>")
def set_language(lang_code: str):
  normalized = (lang_code or "").strip().lower()
  if normalized in SUPPORTED_LANGUAGES:
    session["lang"] = normalized
  next_target = (request.args.get("next") or "").strip()
  if not next_target.startswith("/"):
    next_target = url_for("admin_dashboard")
  return redirect(next_target)


@app.context_processor
def _language_context_processor():
  return {
    "t": _t,
    "current_lang": _get_current_language(),
  }


@app.after_request
def _language_after_request(response):
  content_type = (response.content_type or "").lower()
  if "text/html" not in content_type:
    return response
  try:
    html = response.get_data(as_text=True)
  except Exception:
    return response
  if request.endpoint in {"ops.admin_public_documents", "ops.public_resources"}:
    html = html.replace("Putzelf Marketing", "Putzelf")
  else:
    html = html.replace("Putzelf Marketing", "Elf's Plan").replace("Putzelf", "Elf's Plan")
  is_site_manager = session.get("role") == "site_manager"
  def _set_theme_color(match):
    tag = match.group(0)
    if re.search(r"\bcontent\s*=", tag, flags=re.IGNORECASE):
      return re.sub(r"(\bcontent\s*=\s*[\"'])[^\"']*([\"'])", r"\g<1>#014D4E\2", tag, count=1, flags=re.IGNORECASE)
    return tag[:-1] + ' content="#014D4E">'
  html = re.sub(r"<meta\b(?=[^>]*\bname\s*=\s*[\"']theme-color[\"'])[^>]*>", _set_theme_color, html, flags=re.IGNORECASE)
  if "</head>" in html:
    if is_site_manager and "/static/site-manager-manifest.json" not in html:
      manager_pwa_head = (
        '<link rel="manifest" href="/static/site-manager-manifest.json?v=2">'
        '<link rel="apple-touch-icon" href="/static/employee-icon-192.png">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
      )
      html = html.replace("</head>", manager_pwa_head + "</head>", 1)
    shared_assets = (
      '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">'
      '<link rel="stylesheet" href="/static/elfs-plan.css?v=mobile-1">'
    )
    html = html.replace("</head>", shared_assets + "</head>", 1)
  if "</body>" in html:
    body_open = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
    if body_open and request.endpoint != "login":
      language_nav = _build_language_switcher_markup()
      html = html[:body_open.end()] + language_nav + html[body_open.end():]
    if is_site_manager:
      manager_pwa_runtime = (
        '<dialog class="ep-pwa-help" id="manager-pwa-help" aria-labelledby="manager-pwa-help-title">'
        '<div class="ep-pwa-help-card"><span class="ep-pwa-help-icon"><i class="bi bi-phone"></i></span>'
        '<h2 id="manager-pwa-help-title">Install Putzelf Manager</h2>'
        '<p id="manager-pwa-help-copy" class="mb-3"></p>'
        '<button type="button" class="btn btn-primary" id="manager-pwa-help-close">Close</button></div></dialog>'
        '<script src="/static/site-manager-pwa.js?v=1" defer></script>'
      )
      html = html.replace("</body>", manager_pwa_runtime + "</body>", 1)
    shared_script = '<script src="/static/elfs-plan.js" defer></script>'
    html = html.replace("</body>", shared_script + "</body>", 1)
  html = _translate_html_content(html)
  response.set_data(html)
  return response

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
  DATABASE_URL = "sqlite:///" + os.path.join(APP_ROOT, "schedule.db")

# If DATABASE_URL is a relative SQLite path (e.g. sqlite:///schedule.db), make it
# relative to APP_ROOT rather than the current working directory.
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
  sqlite_path = DATABASE_URL.removeprefix("sqlite:///")
  if sqlite_path and not sqlite_path.startswith("/") and sqlite_path != ":memory:":
    DATABASE_URL = "sqlite:///" + os.path.join(APP_ROOT, sqlite_path)

_engine_kwargs: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
  _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, future=True, **_engine_kwargs)
SessionLocal = scoped_session(
  sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)
Base = declarative_base()

INTEGRATION_KEY = (os.getenv("INTEGRATION_KEY") or "").strip()


def _ensure_employee_is_active_column():
  try:
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    tables = insp.get_table_names()
    if "employees" not in tables:
      return
    cols = [c["name"] for c in insp.get_columns("employees")]
    if "is_active" in cols:
      return
    # Add column depending on dialect
    if engine.dialect.name == "sqlite":
      engine.execute(text('ALTER TABLE employees ADD COLUMN is_active INTEGER DEFAULT 1'))
    else:
      engine.execute(text('ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'))
    logging.info("Added is_active column to employees table")
  except Exception:
    logging.exception("Failed to ensure is_active column on employees table")


# Try to ensure the column exists at startup (safe no-op if already present)
try:
  _ensure_employee_is_active_column()
except Exception:
  pass


def _require_integration_key():
  if not INTEGRATION_KEY:
    return False, ("Integration key not configured", 503)
  provided = (request.headers.get("X-INTEGRATION-KEY") or "").strip()
  if not provided or provided != INTEGRATION_KEY:
    return False, ("Invalid integration key", 401)
  return True, None


@app.route("/api/integrations/employees")
def api_integrations_employees():
  ok, error = _require_integration_key()
  if not ok:
    message, status = error
    return jsonify({"error": message}), status

  db = SessionLocal()
  try:
    _generate_missing_employee_credentials(db)
    employees = db.query(Employee).order_by(Employee.name.asc()).all()
    payload = []
    for emp in employees:
      code = (emp.login_code or "").strip() or str(emp.id)
      name = (emp.name or code).strip()
      image_url = None
      try:
        if emp.profile_image_path:
          image_url = url_for('static', filename=emp.profile_image_path, _external=True)
      except Exception:
        image_url = None
      # Respect employee active flag when present, default to True
      try:
        active_flag = True if getattr(emp, 'is_active', None) is None else bool(emp.is_active)
      except Exception:
        active_flag = True
      payload.append({
        "code": code,
        "name": name,
        "active": active_flag,
        "image": image_url,
      })
    return jsonify({"employees": payload})
  finally:
    db.close()


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
  # Round up to the next 30 minute block.
  minutes = int(math.ceil(hours * 60 / 30) * 30)
  return minutes


def _time_to_minutes(t: time) -> int:
  return int(t.hour) * 60 + int(t.minute)


def _minutes_to_hhmm(minutes: int) -> str:
  h = minutes // 60
  m = minutes % 60
  return f"{h:02d}:{m:02d}"


def _intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
  return a_start < b_end and a_end > b_start


def _generate_slots_for_day(blocked: list[tuple[int, int]], duration_minutes: int) -> list[str]:
  # Simple, opinionated working window.
  work_start = 8 * 60
  work_end = 18 * 60
  step = 30
  latest_start = work_end - duration_minutes
  if latest_start < work_start:
    return []

  slots: list[str] = []
  t = work_start
  while t <= latest_start:
    end = t + duration_minutes
    ok = True
    for b_start, b_end in blocked:
      if _intervals_overlap(t, end, b_start, b_end):
        ok = False
        break
    if ok:
      slots.append(_minutes_to_hhmm(t))
    t += step
  return slots


def _parse_time_hhmm(raw: str | None) -> time | None:
  value = (raw or "").strip()
  if not value:
    return None
  try:
    return datetime.strptime(value, "%H:%M").time()
  except ValueError:
    try:
      return datetime.strptime(value, "%H:%M:%S").time()
    except ValueError:
      return None


def _ensure_default_website_site(db, address: str | None = None):
  name = "Website bookings"
  site = db.query(Site).filter(func.lower(Site.name) == name.lower()).first()
  if site:
    return site
  site = Site(name=name, address=(address or "").strip() or None, hourly_rate=0.0, is_active=True)
  db.add(site)
  db.commit()
  return site


def _upsert_website_booking_lead(db, payload, booking_id, address, day, start, duration_minutes):
  """Record a confirmed website booking in Lead Center, idempotent by booking ID."""
  marker = f"Website booking #{booking_id}" if booking_id is not None else None
  lead = None
  if marker:
    lead = (
      db.query(Lead)
      .filter(Lead.source == "Website booking", Lead.notes.ilike(f"%{marker}%"))
      .first()
    )

  customer_name = str(
    payload.get("customer_name") or payload.get("full_name") or payload.get("name") or ""
  ).strip()
  customer_email = str(payload.get("customer_email") or payload.get("email") or "").strip() or None
  customer_phone = str(payload.get("customer_phone") or payload.get("phone") or "").strip() or None
  booking_details = [marker or "Confirmed website booking"]
  if address:
    booking_details.append(f"Address: {address}")
  booking_details.append(f"Service: {day:%Y-%m-%d} {start:%H:%M} ({duration_minutes / 60:g} hours)")
  instructions = str(payload.get("instructions") or "").strip()
  if instructions:
    booking_details.append(f"Instructions: {instructions}")
  details = "\n".join(booking_details)

  if lead is None:
    lead = Lead(
      name=customer_name or (f"Website booking #{booking_id}" if booking_id is not None else "Website booking"),
      email=customer_email,
      phone=customer_phone,
      source="Website booking",
      notes=details,
      stage="New Leads",
    )
    db.add(lead)
  else:
    # Fill in customer details if a repeated webhook supplies information later.
    if customer_name and (not lead.name or lead.name.startswith("Website booking #")):
      lead.name = customer_name
    if customer_email:
      lead.email = customer_email
    if customer_phone:
      lead.phone = customer_phone
    lead.notes = details
  return lead


@app.route("/api/integrations/shifts/from-booking", methods=["POST"])
def api_integrations_shift_from_booking():
  ok, error = _require_integration_key()
  if not ok:
    message, status = error
    return jsonify({"error": message}), status

  payload = request.get_json(silent=True) or {}
  booking_id = payload.get("booking_id")
  employee_code = _parse_employee_code(payload.get("employee_code"))
  day = _parse_day_ymd(payload.get("day"))
  start = _parse_time_hhmm(payload.get("start_time"))
  duration_raw = payload.get("duration_hours")
  duration_minutes = _parse_duration_hours(str(duration_raw) if duration_raw is not None else None)
  address = (payload.get("address") or "").strip()
  instructions = (payload.get("instructions") or "").strip()

  if not employee_code or day is None or start is None or duration_minutes is None:
    return jsonify({"error": "employee_code, day, start_time and duration_hours are required"}), 400

  start_min = _time_to_minutes(start)
  end_min = start_min + duration_minutes
  if end_min > 24 * 60:
    return jsonify({"error": "Invalid start_time/duration_hours"}), 400

  end_time_obj = (datetime.combine(date.today(), start) + timedelta(minutes=duration_minutes)).time()

  db = SessionLocal()
  try:
    # The integration endpoint represents a confirmed booking. Record it independently
    # from worker availability so scheduling conflicts do not erase the sales lead.
    lead = _upsert_website_booking_lead(db, payload, booking_id, address, day, start, duration_minutes)
    db.commit()

    # Ensure employee login codes exist (so the website's employee_code always resolves).
    _generate_missing_employee_credentials(db)

    emp = (
      db.query(Employee)
      .filter(func.lower(Employee.login_code) == employee_code.strip().lower(), Employee.has_platform_access.is_(True), _employee_staff_function_filter("Cleaner"), Employee.is_active.is_(True))
      .first()
    )
    if not emp:
      return jsonify({"error": "Employee not found"}), 404

    # Idempotency: recognize the booking before checking for overlaps so a retry
    # does not report its own previously-created shift as a conflict.
    existing = None
    if booking_id is not None:
      needle = f"Website booking #{booking_id}"
      existing = (
        db.query(Shift)
        .filter(Shift.employee_id == emp.id, Shift.day == day)
        .filter(Shift.instructions.ilike(f"%{needle}%"))
        .first()
      )

    # Preserve confirmed bookings even if the employee has an overlapping shift.
    # Return the conflict details so the website can show the user a warning.
    conflicting_shift_ids = []
    shifts = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.day == day).all()
    for s in shifts:
      if existing and s.id == existing.id:
        continue
      try:
        b_start = _time_to_minutes(s.start_time)
        b_end = _time_to_minutes(s.end_time)
      except Exception:
        continue
      if _intervals_overlap(start_min, end_min, b_start, b_end):
        conflicting_shift_ids.append(s.id)

    result = {
      "leadId": lead.id,
      "conflict": bool(conflicting_shift_ids),
      "conflictingShiftIds": conflicting_shift_ids,
    }
    if conflicting_shift_ids:
      result["notification"] = "This confirmed booking overlaps an existing shift. The shift was saved; please review the schedule."
    if existing:
      result["shiftId"] = existing.id
      return jsonify(result)

    site = _ensure_default_website_site(db, address=address)
    full_instructions = instructions
    if booking_id is not None:
      booking_marker = f"Website booking #{booking_id}"
      if booking_marker.lower() not in full_instructions.lower():
        full_instructions = f"{booking_marker}\n{full_instructions}".strip()
    if address and address.lower() not in full_instructions.lower():
      full_instructions = (full_instructions + f"\nAddress: {address}").strip()

    shift = Shift(
      employee_id=emp.id,
      site_id=site.id,
      day=day,
      start_time=start,
      end_time=end_time_obj,
      instructions=full_instructions or None,
    )
    db.add(shift)
    db.commit()
    result["shiftId"] = shift.id
    return jsonify(result), 201
  finally:
    db.close()


@app.route("/api/integrations/availability/slots")
def api_integrations_availability_slots():
  ok, error = _require_integration_key()
  if not ok:
    message, status = error
    return jsonify({"error": message}), status

  employee_code = _parse_employee_code(request.args.get("employee_code") or request.args.get("worker"))
  day = _parse_day_ymd(request.args.get("day") or request.args.get("date"))
  duration_minutes = _parse_duration_hours(request.args.get("duration_hours") or request.args.get("duration"))

  if not employee_code or day is None or duration_minutes is None:
    return jsonify({"error": "employee_code, day and duration_hours are required"}), 400

  db = SessionLocal()
  try:
    _generate_missing_employee_credentials(db)
    emp = (
      db.query(Employee)
      .filter(func.lower(Employee.login_code) == employee_code.strip().lower(), Employee.has_platform_access.is_(True), _employee_staff_function_filter("Cleaner"), Employee.is_active.is_(True))
      .first()
    )
    if not emp:
      return jsonify({"error": "Employee not found"}), 404

    shifts = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.day == day).all()
    blocked: list[tuple[int, int]] = []
    for s in shifts:
      try:
        blocked.append((_time_to_minutes(s.start_time), _time_to_minutes(s.end_time)))
      except Exception:
        continue

    slots = _generate_slots_for_day(blocked, duration_minutes)
    return jsonify({"slots": slots})
  finally:
    db.close()


@app.route("/api/integrations/availability/month")
def api_integrations_availability_month():
  ok, error = _require_integration_key()
  if not ok:
    message, status = error
    return jsonify({"error": message}), status

  employee_code = _parse_employee_code(request.args.get("employee_code") or request.args.get("worker"))
  month_parts = _parse_month_ym(request.args.get("month"))
  duration_minutes = _parse_duration_hours(request.args.get("duration_hours") or request.args.get("duration"))

  if not employee_code or month_parts is None or duration_minutes is None:
    return jsonify({"error": "employee_code, month and duration_hours are required"}), 400

  year, month = month_parts
  month_start = date(year, month, 1)
  if month == 12:
    month_end = date(year + 1, 1, 1) - timedelta(days=1)
  else:
    month_end = date(year, month + 1, 1) - timedelta(days=1)

  db = SessionLocal()
  try:
    _generate_missing_employee_credentials(db)
    emp = (
      db.query(Employee)
      .filter(func.lower(Employee.login_code) == employee_code.strip().lower(), Employee.has_platform_access.is_(True), _employee_staff_function_filter("Cleaner"), Employee.is_active.is_(True))
      .first()
    )
    if not emp:
      return jsonify({"error": "Employee not found"}), 404

    shifts = (
      db.query(Shift)
      .filter(
        Shift.employee_id == emp.id,
        Shift.day >= month_start,
        Shift.day <= month_end,
      )
      .all()
    )

    blocked_by_day: dict[date, list[tuple[int, int]]] = {}
    for s in shifts:
      try:
        blocked_by_day.setdefault(s.day, []).append(
          (_time_to_minutes(s.start_time), _time_to_minutes(s.end_time))
        )
      except Exception:
        continue

    available_days: list[str] = []
    cursor = month_start
    while cursor <= month_end:
      blocked = blocked_by_day.get(cursor, [])
      if _generate_slots_for_day(blocked, duration_minutes):
        available_days.append(cursor.strftime("%Y-%m-%d"))
      cursor += timedelta(days=1)

    return jsonify({"availableDays": available_days})
  finally:
    db.close()


# --- Optional integrations -----------------------------------------------------

try:
  from reportlab.lib import colors
  from reportlab.lib.pagesizes import A4, landscape
  from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
  from reportlab.lib.units import inch
  from reportlab.pdfgen import canvas
  from reportlab.platypus import (
    Image,
    PageBreak,
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
  PageBreak = None
  Paragraph = None
  SimpleDocTemplate = None
  Spacer = None
  Table = None
  TableStyle = None
  REPORTLAB_AVAILABLE = False

try:
  import pandas as pd
  PANDAS_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
  pd = None
  PANDAS_AVAILABLE = False

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

PYTHON_DOCX_IMPORT_ERROR: str | None = None
try:
  from docx import Document
  PYTHON_DOCX_AVAILABLE = True
except Exception as exc:  # pragma: no cover - optional dependency
  Document = None
  PYTHON_DOCX_AVAILABLE = False
  PYTHON_DOCX_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
  logging.exception("Could not import python-docx in the Flask application")

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

EU_COUNTRY_CODES = {
  "30", "31", "32", "33", "34", "36", "39",
  "40", "41", "43", "44", "45", "46", "47", "48", "49",
  "350", "351", "352", "353", "354", "355", "356", "357", "358", "359",
  "370", "371", "372", "373", "374", "375", "376", "377", "378", "380", "381", "382", "383", "385", "386", "387", "389",
  "420", "421", "423",
}

LEAD_STAGES = ["New Leads", "Contacted", "Converted"]

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


# --- ORM models ----------------------------------------------------------------


class Employee(Base):
  __tablename__ = "employees"

  id = Column(Integer, primary_key=True)
  name = Column(String(255), nullable=False)
  is_active = Column(Boolean, nullable=False, default=True)
  role = Column(String(255))
  access_role = Column(String(32), nullable=False, default="employee")
  login_email = Column(String(255), unique=True)
  login_code = Column(String(64), unique=True)
  login_pin_hash = Column(String(255))
  login_pin_plain = Column(String(32))
  staff_type = Column(String(64), nullable=False, default="Cleaner")
  staff_functions = Column(Text, nullable=False, default="[]")
  branch = Column(String(32), nullable=False, default="Wien")
  has_platform_access = Column(Boolean, nullable=False, default=True)
  worker_status = Column(String(16), nullable=False, default="active")
  profile_phone = Column(String(64))
  profile_emergency_name = Column(String(255))
  profile_emergency_phone = Column(String(64))
  profile_address = Column(String(255))
  profile_zip_code = Column(String(32))
  profile_city = Column(String(128))
  profile_contract_start_date = Column(String(10))
  profile_contract_end_date = Column(String(10))
  profile_employment_type = Column(String(128))
  profile_group_type = Column(String(64))
  profile_group_number = Column(String(16))
  profile_euros_per_hour = Column(String(32))
  profile_working_hours = Column(String(32))
  profile_work_type = Column(String(32))
  profile_notes = Column(Text)
  profile_image_path = Column(String(255))

  shifts = relationship("Shift", back_populates="employee", cascade="all, delete-orphan")


STAFF_FUNCTION_OPTIONS = ("Cleaner", "Office administrator", "IT", "Reception", "Intern", "Graphic designer", "Site manager", "Sales manager", "Other")


def _normalize_staff_functions(raw, fallback="Cleaner"):
  try:
    values = json.loads(raw) if isinstance(raw, str) else raw
  except (TypeError, ValueError):
    values = []
  if not isinstance(values, (list, tuple, set)):
    values = [values] if isinstance(values, str) else []
  selected = []
  for value in values:
    value = str(value).strip()
    if value in STAFF_FUNCTION_OPTIONS and value not in selected:
      selected.append(value)
  if not selected and fallback in STAFF_FUNCTION_OPTIONS:
    selected = [fallback]
  return selected


def _employee_staff_functions(employee):
  stored = getattr(employee, "staff_functions", None)
  functions = _normalize_staff_functions(stored, fallback="")
  if functions:
    return functions
  legacy = getattr(employee, "staff_type", None)
  return [legacy] if legacy in STAFF_FUNCTION_OPTIONS else ["Cleaner"]


def _employee_has_staff_function(employee, function):
  return function in _employee_staff_functions(employee)


def _employee_staff_function_filter(function):
  return or_(Employee.staff_type == function, Employee.staff_functions.like(f'%"{function}"%'))


class EmployeeDocument(Base):
  __tablename__ = "employee_documents"
  id = Column(Integer, primary_key=True)
  employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
  original_filename = Column(String(255), nullable=False)
  storage_name = Column(String(255), nullable=False, unique=True)
  uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  employee = relationship("Employee", backref="documents")


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
  profile_vat_id = Column(String(128))
  profile_tax_id = Column(String(128))
  profile_default_hourly_rate = Column(Float)
  profile_notes = Column(Text)
  profile_image_path = Column(String(255))
  contract_partner_name = Column(String(255))
  contract_contact_details = Column(String(255))
  contract_start_date = Column(String(10))
  contract_end_date = Column(String(10))
  manager_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

  shifts = relationship("Shift", back_populates="site", cascade="all, delete-orphan")
  site_manager = relationship("Employee", foreign_keys=[manager_employee_id])


class Shift(Base):
  __tablename__ = "shifts"

  id = Column(Integer, primary_key=True)
  employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
  site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
  day = Column(Date, nullable=False)
  start_time = Column(Time, nullable=False)
  end_time = Column(Time, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  instructions = Column(Text)
  is_recurring = Column(Boolean, nullable=False, default=False)
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
  tour_links = relationship("TourStop", back_populates="shift", cascade="all, delete-orphan")


class NotificationSettings(Base):
  __tablename__ = "notification_settings"

  id = Column(Integer, primary_key=True, default=1)
  paused_until = Column(DateTime, nullable=True)
  paused_by = Column(String(255), nullable=True)
  updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmployeeNotification(Base):
  __tablename__ = "employee_notifications"

  id = Column(Integer, primary_key=True)
  employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
  shift_id = Column(Integer, nullable=True, index=True)
  kind = Column(String(40), nullable=False, default="shift_updated")
  title = Column(String(180), nullable=False)
  body = Column(Text, nullable=False)
  payload = Column(Text, nullable=False, default="{}")
  created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
  available_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
  read_at = Column(DateTime, nullable=True)


class Tour(Base):
  __tablename__ = "schedule_tours"

  id = Column(Integer, primary_key=True)
  name = Column(String(160), nullable=False)
  day = Column(Date, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  stops = relationship("TourStop", back_populates="tour", cascade="all, delete-orphan", order_by="TourStop.position")


class TourStop(Base):
  __tablename__ = "schedule_tour_stops"

  id = Column(Integer, primary_key=True)
  tour_id = Column(Integer, ForeignKey("schedule_tours.id", ondelete="CASCADE"), nullable=False)
  shift_id = Column(Integer, ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
  position = Column(Integer, nullable=False)
  tour = relationship("Tour", back_populates="stops")
  shift = relationship("Shift", back_populates="tour_links")


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


class InspectionArea(Base):
  """Legacy area names retained for older inspection records."""
  __tablename__ = "inspection_areas"
  id = Column(Integer, primary_key=True)
  name = Column(String(160), nullable=False, unique=True)
  sort_order = Column(Integer, nullable=False, default=0)
  is_active = Column(Boolean, nullable=False, default=True)


class SiteInspectionArea(Base):
  __tablename__ = "site_inspection_areas"
  __table_args__ = (UniqueConstraint("site_id", "name", name="uq_site_inspection_area_name"),)
  id = Column(Integer, primary_key=True)
  site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
  name = Column(String(160), nullable=False)
  sort_order = Column(Integer, nullable=False, default=0)
  is_active = Column(Boolean, nullable=False, default=True)
  site = relationship("Site")


class SiteInspection(Base):
  __tablename__ = "site_inspections"
  __table_args__ = (UniqueConstraint("site_id", "month", name="uq_site_inspection_month"),)
  id = Column(Integer, primary_key=True)
  site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
  month = Column(String(7), nullable=False)  # YYYY-MM
  inspected_by_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
  updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  site = relationship("Site")
  inspector = relationship("Employee")
  items = relationship("InspectionItem", back_populates="inspection", cascade="all, delete-orphan")


class InspectionItem(Base):
  __tablename__ = "inspection_items"
  __table_args__ = (
    UniqueConstraint("inspection_id", "area_id", name="uq_inspection_area"),
    UniqueConstraint("inspection_id", "site_area_id", name="uq_inspection_site_area"),
  )
  id = Column(Integer, primary_key=True)
  inspection_id = Column(Integer, ForeignKey("site_inspections.id", ondelete="CASCADE"), nullable=False)
  area_id = Column(Integer, ForeignKey("inspection_areas.id"), nullable=True)
  site_area_id = Column(Integer, ForeignKey("site_inspection_areas.id"), nullable=True)
  area_name = Column(String(160), nullable=False)  # snapshot preserves report history
  checked = Column(Boolean, nullable=False, default=False)
  notes = Column(Text)
  photo_path = Column(String(255))
  checked_at = Column(DateTime)
  inspection = relationship("SiteInspection", back_populates="items")
  area = relationship("InspectionArea")
  site_area = relationship("SiteInspectionArea")


class PublicDocument(Base):
  __tablename__ = "public_documents"
  id = Column(Integer, primary_key=True)
  title = Column(String(200), nullable=False)
  category = Column(String(100), nullable=False, default="General")
  original_filename = Column(String(255), nullable=False)
  storage_name = Column(String(255), nullable=False, unique=True)
  uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def _shift_notification_description(shift, overrides=None):
  values = overrides or {}
  site_id = values.get("site_id", shift.site_id)
  site = None
  if site_id:
    site = shift.site if site_id == shift.site_id else None
    site_name = (site.profile_company_name or site.name) if site else f"Site #{site_id}"
  else:
    site_name = "Site"
  day_value = values.get("day", shift.day)
  start_value = values.get("start_time", shift.start_time)
  end_value = values.get("end_time", shift.end_time)
  day_label = day_value.strftime("%d.%m.%Y") if day_value else "Date to be confirmed"
  start_label = start_value.strftime("%H:%M") if start_value else "--:--"
  end_label = end_value.strftime("%H:%M") if end_value else "--:--"
  return f"{site_name} · {day_label}, {start_label}–{end_label}"


@event.listens_for(SQLAlchemySession, "before_flush")
def _collect_shift_notification_events(db_session, flush_context, instances):
  changes = db_session.info.setdefault("_employee_shift_notification_changes", [])
  deleted_employee_ids = {item.id for item in db_session.deleted if isinstance(item, Employee) and item.id}
  important_fields = ("site_id", "day", "start_time", "end_time", "instructions")

  for shift in tuple(db_session.new):
    if not isinstance(shift, Shift) or not shift.employee_id:
      continue
    changes.append({
      "employee_id": shift.employee_id, "shift": shift, "kind": "shift_assigned",
      "title": "New shift assigned", "body": _shift_notification_description(shift),
      "summary": "A new shift was added to your schedule.",
    })

  for shift in tuple(db_session.dirty):
    if not isinstance(shift, Shift) or shift in db_session.new or shift in db_session.deleted:
      continue
    state = sqlalchemy_inspect(shift)
    employee_history = state.attrs.employee_id.history
    old_employee_id = employee_history.deleted[0] if employee_history.deleted else shift.employee_id
    new_employee_id = None if shift in db_session.deleted else shift.employee_id
    changed_fields = {name for name in important_fields if state.attrs[name].history.has_changes()}
    if not employee_history.has_changes() and not changed_fields:
      continue
    if old_employee_id and old_employee_id not in deleted_employee_ids and (employee_history.has_changes() or shift in db_session.deleted):
      changes.append({
        "employee_id": old_employee_id, "shift": shift, "kind": "shift_cancelled",
        "title": "Shift removed", "body": _shift_notification_description(shift),
        "summary": "A shift was removed from your schedule.",
      })
    if new_employee_id and new_employee_id not in deleted_employee_ids:
      if employee_history.has_changes():
        kind, title, summary = "shift_assigned", "New shift assigned", "A shift was assigned to your schedule."
      elif changed_fields:
        kind, title, summary = "shift_updated", "Shift updated", "A shift in your schedule was changed."
      else:
        continue
      changes.append({
        "employee_id": new_employee_id, "shift": shift, "kind": kind, "title": title,
        "body": _shift_notification_description(shift), "summary": summary,
      })

  for shift in tuple(db_session.deleted):
    if not isinstance(shift, Shift) or not shift.employee_id or shift.employee_id in deleted_employee_ids:
      continue
    changes.append({
      "employee_id": shift.employee_id, "shift": shift, "kind": "shift_cancelled",
      "title": "Shift removed", "body": _shift_notification_description(shift),
      "summary": "A shift was removed from your schedule.",
    })


@event.listens_for(SQLAlchemySession, "after_flush_postexec")
def _persist_shift_notifications(db_session, flush_context):
  changes = db_session.info.pop("_employee_shift_notification_changes", [])
  if not changes:
    return
  now = datetime.utcnow()
  settings = db_session.get(NotificationSettings, 1)
  pause_is_active = bool(settings and settings.paused_until and settings.paused_until > now)
  available_at = settings.paused_until if pause_is_active else now
  queued_by_shift = {}
  for change in changes:
    shift = change["shift"]
    notification_values = {
      "kind": change["kind"],
      "title": change["title"],
      "body": change["body"],
      "payload": json.dumps({"summary": change["summary"], "shift_id": shift.id}, ensure_ascii=False),
      "created_at": now,
    }
    key = (change["employee_id"], shift.id)
    pending = queued_by_shift.get(key)
    if pause_is_active and pending is None and shift.id:
      pending = db_session.query(EmployeeNotification).filter(
        EmployeeNotification.employee_id == change["employee_id"],
        EmployeeNotification.shift_id == shift.id,
        EmployeeNotification.available_at > now,
        EmployeeNotification.read_at.is_(None),
      ).order_by(EmployeeNotification.id.desc()).first()
    if pause_is_active and pending:
      for name, value in notification_values.items():
        setattr(pending, name, value)
      queued_by_shift[key] = pending
      continue
    notification = EmployeeNotification(
      employee_id=change["employee_id"], shift_id=shift.id,
      available_at=available_at, **notification_values,
    )
    db_session.add(notification)
    if pause_is_active:
      queued_by_shift[key] = notification


Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
  connection.execute(text("UPDATE leads SET stage = 'Contacted' WHERE stage = 'Qualified'"))


def _notification_state(db):
  now = datetime.utcnow()
  settings = db.get(NotificationSettings, 1)
  if settings and settings.paused_until and settings.paused_until <= now:
    settings.paused_until = None
    settings.paused_by = None
    db.query(EmployeeNotification).filter(EmployeeNotification.available_at > now).update(
      {EmployeeNotification.available_at: now}, synchronize_session=False
    )
    db.commit()
    settings = db.get(NotificationSettings, 1)
  pending = db.query(func.count(EmployeeNotification.id)).filter(EmployeeNotification.available_at > now).scalar() or 0
  return {
    "paused": bool(settings and settings.paused_until and settings.paused_until > now),
    "paused_until": settings.paused_until.isoformat() + "Z" if settings and settings.paused_until else None,
    "paused_by": settings.paused_by if settings else None,
    "pending_count": int(pending),
  }



def _ensure_sqlite_column(engine, table: str, column: str, ddl: str):
  if not DATABASE_URL.startswith("sqlite"):
    return
  with engine.begin() as conn:
    result = conn.execute(text(f"PRAGMA table_info('{table}')"))
    existing = {row[1] for row in result}
    if column not in existing:
      conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


_ensure_sqlite_column(engine, "inspection_items", "site_area_id", "INTEGER REFERENCES site_inspection_areas(id)")
if engine.dialect.name == "postgresql":
  with engine.begin() as conn:
    conn.execute(text(
      "ALTER TABLE inspection_items ADD COLUMN IF NOT EXISTS "
      "site_area_id INTEGER REFERENCES site_inspection_areas(id)"
    ))
    conn.execute(text(
      "ALTER TABLE shifts ADD COLUMN IF NOT EXISTS "
      "is_recurring BOOLEAN NOT NULL DEFAULT FALSE"
    ))
    conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS staff_type VARCHAR(64) NOT NULL DEFAULT 'Cleaner'"))
    conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS staff_functions TEXT NOT NULL DEFAULT '[]'"))
    conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS branch VARCHAR(32) NOT NULL DEFAULT 'Wien'"))
    conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS has_platform_access BOOLEAN NOT NULL DEFAULT TRUE"))
    conn.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS worker_status VARCHAR(16) NOT NULL DEFAULT 'active'"))


_ensure_sqlite_column(engine, "shifts", "created_at", "DATETIME")
_ensure_sqlite_column(engine, "shifts", "is_recurring", "BOOLEAN NOT NULL DEFAULT 0")
_ensure_sqlite_column(engine, "employees", "login_email", "TEXT")
_ensure_sqlite_column(engine, "employees", "access_role", "TEXT NOT NULL DEFAULT 'employee'")
_ensure_sqlite_column(engine, "employees", "login_code", "TEXT")
_ensure_sqlite_column(engine, "employees", "login_pin_hash", "TEXT")
_ensure_sqlite_column(engine, "employees", "login_pin_plain", "TEXT")
_ensure_sqlite_column(engine, "employees", "staff_type", "TEXT NOT NULL DEFAULT 'Cleaner'")
_ensure_sqlite_column(engine, "employees", "staff_functions", "TEXT NOT NULL DEFAULT '[]'")
_ensure_sqlite_column(engine, "employees", "branch", "TEXT NOT NULL DEFAULT 'Wien'")
_ensure_sqlite_column(engine, "employees", "has_platform_access", "BOOLEAN NOT NULL DEFAULT 1")
_ensure_sqlite_column(engine, "employees", "worker_status", "TEXT NOT NULL DEFAULT 'active'")
employee_columns = {column["name"] for column in sqlalchemy_inspect(engine).get_columns("employees")}
with engine.begin() as conn:
  conn.execute(text("UPDATE employees SET worker_status = 'active' WHERE worker_status IS NULL"))
  conn.execute(text("UPDATE employees SET worker_status = 'passive' WHERE worker_status = 'interested'"))
  if "is_active" in employee_columns:
    conn.execute(text("UPDATE employees SET worker_status = 'passive' WHERE is_active = 0 AND worker_status = 'active'"))
_ensure_sqlite_column(engine, "employees", "profile_phone", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_emergency_name", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_emergency_phone", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_address", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_zip_code", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_city", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_contract_start_date", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_contract_end_date", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_employment_type", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_group_type", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_group_number", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_euros_per_hour", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_working_hours", "TEXT")
_ensure_sqlite_column(engine, "employees", "profile_work_type", "TEXT")
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
_ensure_sqlite_column(engine, "sites", "manager_employee_id", "INTEGER")
_ensure_sqlite_column(engine, "sites", "profile_company_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_contact_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_contact_email", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_phone", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_billing_address", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_vat_id", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_tax_id", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_default_hourly_rate", "FLOAT")
_ensure_sqlite_column(engine, "sites", "profile_notes", "TEXT")
_ensure_sqlite_column(engine, "sites", "profile_image_path", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_partner_name", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_contact_details", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_start_date", "TEXT")
_ensure_sqlite_column(engine, "sites", "contract_end_date", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_company_name", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_phone", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_billing_address", "TEXT")
_ensure_sqlite_column(engine, "invoices", "site_tax_id", "TEXT")
_ensure_sqlite_column(engine, "invoices", "paid_at", "DATETIME")
_ensure_sqlite_column(engine, "invoices", "billing_month", "TEXT")


def _ensure_nullable_shift_employee_id():
  """Allow a released shift to remain on the board as an open assignment."""
  if engine.dialect.name == "postgresql":
    with engine.begin() as conn:
      conn.execute(text("ALTER TABLE shifts ALTER COLUMN employee_id DROP NOT NULL"))
    return
  if engine.dialect.name != "sqlite":
    return

  raw = engine.raw_connection()
  cursor = raw.cursor()
  try:
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.execute("PRAGMA legacy_alter_table=ON")
    table_sql = cursor.execute(
      "SELECT sql FROM sqlite_master WHERE type='table' AND name='shifts'"
    ).fetchone()
    columns = cursor.execute("PRAGMA table_info('shifts')").fetchall()
    employee_column = next((column for column in columns if column[1] == "employee_id"), None)
    if not table_sql or not employee_column or not employee_column[3]:
      return
    create_sql = table_sql[0]
    create_sql = create_sql.replace("CREATE TABLE shifts", "CREATE TABLE shifts_new", 1)
    create_sql = create_sql.replace("employee_id INTEGER NOT NULL", "employee_id INTEGER", 1)
    indexes = [row[0] for row in cursor.execute(
      "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='shifts' AND sql IS NOT NULL"
    ).fetchall()]
    column_names = [column[1] for column in columns]
    quoted_names = ", ".join('"' + name.replace('"', '""') + '"' for name in column_names)
    cursor.execute("BEGIN IMMEDIATE")
    cursor.execute("ALTER TABLE shifts RENAME TO shifts_old_employee_required")
    cursor.execute(create_sql)
    cursor.execute(
      f"INSERT INTO shifts_new ({quoted_names}) SELECT {quoted_names} FROM shifts_old_employee_required"
    )
    cursor.execute("DROP TABLE shifts_old_employee_required")
    cursor.execute("ALTER TABLE shifts_new RENAME TO shifts")
    for index_sql in indexes:
      cursor.execute(index_sql)
    raw.commit()
  except Exception:
    raw.rollback()
    raise
  finally:
    try:
      cursor.execute("PRAGMA foreign_keys=ON")
      cursor.execute("PRAGMA legacy_alter_table=OFF")
    except Exception:
      pass
    cursor.close()
    raw.close()


_ensure_nullable_shift_employee_id()


def _allowed_image(filename: str | None) -> bool:
  if not filename or "." not in filename:
    return False
  ext = filename.rsplit(".", 1)[1].lower()
  return ext in ALLOWED_IMAGE_EXTENSIONS


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


def _coerce_float(value: str | None) -> float | None:
  try:
    if value is None:
      return None
    return float(value)
  except (TypeError, ValueError):
    return None


def _coerce_optional_dmy_date(value: str | None) -> tuple[str | None, bool]:
  raw = (value or "").strip()
  if not raw:
    return None, True
  for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y"):
    try:
      parsed = datetime.strptime(raw, fmt)
      return parsed.strftime("%d-%m-%Y"), True
    except ValueError:
      continue
  return None, False


def _remove_photo(path: str | None) -> None:
  if not path:
    return
  try:
    absolute = path if os.path.isabs(path) else os.path.join(APP_ROOT, "static", path)
    if os.path.isfile(absolute):
      os.remove(absolute)
  except OSError:
    logging.debug("Failed to remove phot/o %s", path)


SHIFT_PHOTO_RETENTION_DAYS = 30
_LAST_SHIFT_PHOTO_CLEANUP_DATE: date | None = None


def _cleanup_expired_shift_photos(db) -> int:
  cutoff = datetime.utcnow() - timedelta(days=SHIFT_PHOTO_RETENTION_DAYS)
  removed_count = 0
  changed = False
  shifts = (
    db.query(Shift)
    .filter(or_(Shift.before_photo_path.isnot(None), Shift.after_photo_path.isnot(None)))
    .all()
  )
  for shift in shifts:
    for field_name in ("before_photo_path", "after_photo_path"):
      path = getattr(shift, field_name)
      if not path:
        continue
      absolute = path if os.path.isabs(path) else os.path.join(APP_ROOT, "static", path)
      try:
        if not os.path.isfile(absolute):
          setattr(shift, field_name, None)
          changed = True
          continue
        mtime = datetime.utcfromtimestamp(os.path.getmtime(absolute))
        if mtime < cutoff:
          _remove_photo(path)
          setattr(shift, field_name, None)
          removed_count += 1
          changed = True
      except OSError:
        logging.exception("Failed checking expiry for shift photo %s", path)
  if changed:
    db.commit()
  return removed_count


def _build_admin_shift_photo_items(db, limit: int = 24) -> list[dict[str, Any]]:
  items: list[dict[str, Any]] = []
  shifts = (
    db.query(Shift)
    .options(joinedload(Shift.employee), joinedload(Shift.site))
    .filter(or_(Shift.before_photo_path.isnot(None), Shift.after_photo_path.isnot(None)))
    .order_by(Shift.created_at.desc(), Shift.id.desc())
    .all()
  )
  for shift in shifts:
    for kind, path in (("before", shift.before_photo_path), ("after", shift.after_photo_path)):
      if not path:
        continue
      absolute = path if os.path.isabs(path) else os.path.join(APP_ROOT, "static", path)
      if not os.path.isfile(absolute):
        continue
      try:
        modified_at = datetime.utcfromtimestamp(os.path.getmtime(absolute))
      except OSError:
        continue
      age_days = max((datetime.utcnow() - modified_at).days, 0)
      items.append({
        "kind": kind,
        "url": url_for("static", filename=path),
        "employee_name": shift.employee.name if shift.employee else "—",
        "site_name": shift.site.name if shift.site else "—",
        "day": shift.day.strftime("%d.%m.%Y") if shift.day else "—",
        "time_window": f"{shift.start_time.strftime('%H:%M')} – {shift.end_time.strftime('%H:%M')}",
        "age_days": age_days,
      })
  return items[:limit]


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
  for emp in db.query(Employee).filter(Employee.has_platform_access.is_(True)).all():
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
      emp.login_pin_plain = pin_generated
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


def site_manager_required(view_func):
  """Allow the main admin or an active employee account with manager access."""
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    if session.get("role") == "admin" and session.get("auth"):
      return view_func(*args, **kwargs)
    employee_id = session.get("employee_id")
    if session.get("role") == "site_manager" and employee_id:
      db = SessionLocal()
      try:
        employee = db.get(Employee, employee_id)
        if employee and employee.is_active and employee.has_platform_access and employee.access_role == "site_manager":
          return view_func(*args, **kwargs)
      finally:
        db.close()
    return redirect(url_for("login", next=request.url))

  return wrapper


def _active_employee_has_role(role: str) -> bool:
  employee_id = session.get("employee_id")
  if not employee_id or session.get("role") != role:
    return False
  db = SessionLocal()
  try:
    employee = db.get(Employee, employee_id)
    return bool(employee and employee.is_active and employee.has_platform_access and employee.access_role == role)
  finally:
    db.close()


def site_or_sales_manager_required(view_func):
  """Allow admins and operational managers into site/client management."""
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    if session.get("role") == "admin" and session.get("auth"):
      return view_func(*args, **kwargs)
    if _active_employee_has_role("site_manager") or _active_employee_has_role("sales_manager"):
      return view_func(*args, **kwargs)
    return redirect(url_for("login", next=request.url))
  return wrapper


def sales_manager_or_admin_required(view_func):
  """Limit sales accounts to their crawler tools and configured admin access."""
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    if session.get("role") == "admin" and session.get("auth"):
      return view_func(*args, **kwargs)
    if _active_employee_has_role("sales_manager"):
      return view_func(*args, **kwargs)
    return redirect(url_for("login", next=request.url))
  return wrapper


def employee_login_required(view_func):
  @wraps(view_func)
  def wrapper(*args, **kwargs):
    employee_id = session.get("employee_id")
    if session.get("role") in {"employee", "site_manager"} and employee_id:
      db = SessionLocal()
      try:
        employee = db.get(Employee, int(employee_id))
        if employee and employee.is_active and employee.has_platform_access:
          return view_func(*args, **kwargs)
      finally:
        db.close()
      session.clear()
    return redirect(url_for("login", next=request.url))

  return wrapper


@app.route("/admin/notifications/state", methods=["GET", "POST"])
@site_manager_required
def admin_notification_state():
  db = SessionLocal()
  try:
    state = _notification_state(db)
    if request.method == "GET":
      return jsonify(state)
    action = (request.form.get("action") or "").strip().lower()
    settings = db.get(NotificationSettings, 1)
    if not settings:
      settings = NotificationSettings(id=1)
      db.add(settings)
    now = datetime.utcnow()
    if action == "pause":
      local_zone = ZoneInfo(os.getenv("APP_TIMEZONE", "Europe/Vienna"))
      local_now = datetime.now(local_zone)
      next_midnight = datetime.combine(local_now.date() + timedelta(days=1), time.min, tzinfo=local_zone)
      settings.paused_until = next_midnight.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
      settings.paused_by = session.get("employee_name") or session.get("username") or "Manager"
      db.commit()
      return jsonify({**_notification_state(db), "message": "Notifications paused until midnight."})
    if action == "resume":
      settings.paused_until = None
      settings.paused_by = None
      resumed = db.query(EmployeeNotification).filter(EmployeeNotification.available_at > now).update(
        {EmployeeNotification.available_at: now}, synchronize_session=False
      )
      db.commit()
      return jsonify({**_notification_state(db), "released_count": int(resumed), "message": "Queued employee notifications are now available."})
    return jsonify({"error": "Choose pause or resume."}), 400
  except Exception:
    db.rollback()
    app.logger.exception("Unable to update notification pause state")
    return jsonify({"error": "Could not update notifications."}), 500
  finally:
    db.close()


@app.route("/employee/api/notifications", methods=["GET"])
@employee_login_required
def employee_notifications_api():
  employee_id = session.get("employee_id")
  db = SessionLocal()
  try:
    state = _notification_state(db)
    now = datetime.utcnow()
    state["pending_count"] = db.query(func.count(EmployeeNotification.id)).filter(
      EmployeeNotification.employee_id == employee_id,
      EmployeeNotification.available_at > now,
      EmployeeNotification.read_at.is_(None),
    ).scalar() or 0
    notifications = db.query(EmployeeNotification).filter(
      EmployeeNotification.employee_id == employee_id,
      EmployeeNotification.available_at <= now,
      EmployeeNotification.read_at.is_(None),
    ).order_by(EmployeeNotification.created_at.desc()).limit(30).all()
    today = date.today()
    shifts = db.query(Shift).options(joinedload(Shift.site)).filter(
      Shift.employee_id == employee_id, Shift.day == today
    ).order_by(Shift.start_time.asc()).all()
    return jsonify({
      "notifications_enabled": not state["paused"],
      "paused_until": state["paused_until"],
      "pending_count": state["pending_count"],
      "today_shifts": [{
        "site_name": (shift.site.profile_company_name or shift.site.name) if shift.site else "Scheduled shift",
        "time_window": f"{shift.start_time.strftime('%H:%M')}–{shift.end_time.strftime('%H:%M')}",
      } for shift in shifts],
      "items": [{
        "id": item.id, "kind": item.kind, "title": item.title, "body": item.body,
        "created_at": item.created_at.isoformat() + "Z",
      } for item in notifications],
    })
  finally:
    db.close()


@app.route("/employee/api/notifications/<int:notification_id>/read", methods=["POST"])
@employee_login_required
def employee_notification_mark_read(notification_id: int):
  db = SessionLocal()
  try:
    notification = db.query(EmployeeNotification).filter_by(
      id=notification_id, employee_id=session.get("employee_id")
    ).first()
    if not notification:
      return jsonify({"error": "Notification not found."}), 404
    notification.read_at = datetime.utcnow()
    db.commit()
    return jsonify({"ok": True})
  finally:
    db.close()


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

    def extract_business_name_from_soup(soup_obj: BeautifulSoup | None) -> str:
      if not soup_obj:
        return ""

      aggregator_markers = {
        "herold", "yelp", "google", "maps", "tripadvisor", "foursquare", "yellowpages", "gelbeseiten",
      }
      base_label = (base_domain.split(".")[0] if base_domain else "").lower().strip()
      is_aggregator_domain = any(marker in (base_domain or "") for marker in aggregator_markers)

      def _normalize_name(value: str | None) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        if not text or len(text) < 2:
          return ""
        lowered = text.lower()
        if lowered in {"home", "startseite", "homepage"}:
          return ""
        if base_label and lowered == base_label:
          return ""
        if is_aggregator_domain and any(marker == lowered for marker in aggregator_markers):
          return ""
        return text

      def _types_from_node(node: dict) -> set[str]:
        raw_types = node.get("@type")
        if isinstance(raw_types, str):
          return {raw_types.lower()}
        if isinstance(raw_types, list):
          return {str(t).lower() for t in raw_types}
        return set()

      def _is_business_like_schema(types: set[str]) -> bool:
        if "localbusiness" in types:
          return True
        business_tokens = (
          "business", "store", "restaurant", "cafe", "hotel", "bar", "bakery", "lodging", "foodestablishment",
        )
        return any(any(token in t for token in business_tokens) for t in types)

      candidates: list[tuple[int, str]] = []

      # 1) JSON-LD (prefer listing-level business entities over portal org)
      for script in soup_obj.find_all("script", attrs={"type": "application/ld+json"}):
        content = (script.string or script.get_text("", strip=True) or "").strip()
        if not content:
          continue
        try:
          payload = json.loads(content)
        except Exception:
          continue

        stack = [payload]
        while stack:
          node = stack.pop()
          if isinstance(node, list):
            stack.extend(node)
            continue
          if not isinstance(node, dict):
            continue

          node_types = _types_from_node(node)
          name_val = node.get("legalName") or node.get("name")
          name = _normalize_name(name_val if isinstance(name_val, str) else "")
          if name:
            score = 0
            if _is_business_like_schema(node_types):
              score += 120
            elif "organization" in node_types:
              score += 20
            if node.get("address") or node.get("telephone") or node.get("email"):
              score += 20
            if score > 0:
              candidates.append((score, name))

          item_list = node.get("itemListElement")
          if isinstance(item_list, list):
            for item in item_list:
              entry = item.get("item") if isinstance(item, dict) else None
              if isinstance(entry, dict):
                entry_name = _normalize_name(entry.get("name") if isinstance(entry.get("name"), str) else "")
                if entry_name:
                  candidates.append((110, entry_name))

          stack.extend(node.values())

      if candidates:
        candidates.sort(key=lambda pair: (pair[0], len(pair[1])), reverse=True)
        return candidates[0][1]

      # 2) Visible listing content fallback (h1/itemprop/class-based)
      selector_candidates = [
        ('[itemprop="name"]', 95),
        ("h1", 90),
        ('[class*="business"][class*="name"]', 85),
        ('[class*="company"][class*="name"]', 85),
        ('[class*="listing"][class*="title"]', 80),
        ('[class*="entry"][class*="title"]', 80),
        ('[class*="result"][class*="title"]', 75),
      ]
      for selector, score in selector_candidates:
        for el in soup_obj.select(selector):
          text = _normalize_name(el.get_text(" ", strip=True))
          if text:
            candidates.append((score, text))
            break
        if candidates:
          break

      # 3) Title fallback (avoid site/platform labels)
      title_tag = soup_obj.find("title")
      if title_tag:
        title_text = _normalize_name(title_tag.get_text(" ", strip=True))
        if title_text:
          for sep in ("|", " - ", " – ", " :: "):
            parts = [p.strip() for p in title_text.split(sep) if p.strip()]
            for part in parts:
              normalized_part = _normalize_name(part)
              if normalized_part and normalized_part.lower() != base_label:
                candidates.append((70, normalized_part))
                break
            if candidates:
              break
          if not candidates:
            candidates.append((60, title_text))

      if candidates:
        candidates.sort(key=lambda pair: (pair[0], len(pair[1])), reverse=True)
        return candidates[0][1]

      return ""

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

    def fallback_business_name_from_url(raw_url: str) -> str:
      netloc = (urlparse(raw_url).netloc or "").lower().strip()
      if netloc.startswith("www."):
        netloc = netloc[4:]
      if any(marker in netloc for marker in ("herold", "yelp", "google", "maps", "tripadvisor", "foursquare", "yellowpages", "gelbeseiten")):
        return ""
      if not netloc:
        return ""
      host_label = netloc.split(".")[0]
      if not host_label:
        return ""
      cleaned = re.sub(r"[^a-z0-9]+", " ", host_label, flags=re.IGNORECASE).strip()
      return cleaned.title() if cleaned else ""

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

        business_name = extract_business_name_from_soup(soup)

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
                if not business_name:
                    business_name = extract_business_name_from_soup(soup_js)
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
            grp = url_map.setdefault(url, {"emails": set(), "phones": set(), "business_names": set()})
            grp["emails"].update(emails)
            grp["phones"].update(phones)
            if business_name:
                grp["business_names"].add(business_name)
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
      business_names = grp.get("business_names", set())
      business_name = next(iter(business_names), "")
      if not business_name:
        business_name = fallback_business_name_from_url(url)

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
          rows.append({"url": url, "business_name": business_name, "email": email, "phone": phone_sample})
      else:
        for phone in normalized_phones:
          rows.append({"url": url, "business_name": business_name, "email": "", "phone": phone})

    app.logger.info("Crawl finished: found %d contact rows", len(rows))
    return rows


def _sanitize_text_value(value: Any, *, strip_punctuation: bool = True) -> str:
  text = str(value or "").strip()
  if not text:
    return ""
  if text.lower() in {"nan", "na", "n/a", "none", "null", "-"}:
    return ""
  if strip_punctuation:
    text = text.replace(",", "").replace(".", "")
  return text.strip()


def _normalize_report_phone(raw_phone: str) -> str:
  digits = re.sub(r"\D", "", raw_phone or "")
  if not digits:
    return ""
  if len(digits) < 9 or len(digits) > 13:
    return ""

  starts_local = digits.startswith("0")
  starts_eu_code = any(digits.startswith(code) for code in EU_COUNTRY_CODES)
  if not (starts_local or starts_eu_code):
    return ""

  return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"


def clean_contacts_with_pandas(rows: list[dict[str, str]]) -> list[dict[str, str]]:
  if not PANDAS_AVAILABLE or pd is None:
    raise ValueError("pandas is required for contact data cleaning")

  df = pd.DataFrame(rows or [])
  for col in ("url", "business_name", "email", "phone"):
    if col not in df.columns:
      df[col] = ""

  df["url"] = df["url"].astype(str).fillna("")
  df["business_name"] = df["business_name"].astype(str).fillna("")
  df["email"] = df["email"].astype(str).fillna("")
  df["phone"] = df["phone"].astype(str).fillna("")

  df["business_name"] = df["business_name"].map(_sanitize_text_value)
  df["email"] = df["email"].map(lambda value: _sanitize_text_value(value, strip_punctuation=False))
  df["phone"] = df["phone"].map(lambda value: _sanitize_text_value(value, strip_punctuation=False))

  df["phone"] = df["phone"].map(_normalize_report_phone)

  # Remove rows where both contact channels are empty.
  df = df[
    (df["email"] != "")
    | (df["phone"] != "")
  ]

  # Remove duplicate full rows first.
  df = df.drop_duplicates(subset=["business_name", "email", "phone"], keep="first")

  # Remove duplicate emails and phones (keep first non-empty value occurrence).
  duplicate_email = (df["email"] != "") & df["email"].duplicated(keep="first")
  duplicate_phone = (df["phone"] != "") & df["phone"].duplicated(keep="first")
  df = df[~(duplicate_email | duplicate_phone)]

  df = df.reset_index(drop=True)
  df.insert(0, "contact_id", range(1, len(df) + 1))

  return df[["contact_id", "business_name", "email", "phone"]].to_dict(orient="records")


def clean_contacts_without_pandas(rows: list[dict[str, str]]) -> list[dict[str, str]]:
  cleaned: list[dict[str, str]] = []
  seen_rows: set[tuple[str, str, str]] = set()
  seen_emails: set[str] = set()
  seen_phones: set[str] = set()

  for row in rows or []:
    business_name = _sanitize_text_value((row or {}).get("business_name"))
    email = _sanitize_text_value((row or {}).get("email"), strip_punctuation=False)
    phone = _normalize_report_phone(_sanitize_text_value((row or {}).get("phone"), strip_punctuation=False))

    if not email and not phone:
      continue

    row_key = (business_name, email, phone)
    if row_key in seen_rows:
      continue

    if email and email in seen_emails:
      continue
    if phone and phone in seen_phones:
      continue

    seen_rows.add(row_key)
    if email:
      seen_emails.add(email)
    if phone:
      seen_phones.add(phone)

    cleaned.append(
      {
        "contact_id": len(cleaned) + 1,
        "business_name": business_name,
        "email": email,
        "phone": phone,
      }
    )

  return cleaned


def clean_contacts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
  if PANDAS_AVAILABLE and pd is not None:
    return clean_contacts_with_pandas(rows)
  return clean_contacts_without_pandas(rows)


def _get_day_range(start: date | None = None, weeks: int = 1, days: int | None = None):
    """
    Return list of dates covering the given number of weeks or explicit days.
    If `days` is provided it overrides `weeks`. Clamped to max 12 weeks (84 days) to keep the grid manageable.
    """
    if start is None:
        start = date.today()
    if days is not None:
        total_days = max(1, min(int(days), 84))
        return [start + timedelta(days=i) for i in range(total_days)]
    weeks = max(1, min(int(weeks or 1), 12))
    total_days = weeks * 7
    monday = start - timedelta(days=start.weekday())
    return [monday + timedelta(days=i) for i in range(total_days)]


def _load_schedule_context(db, week_days):
    employees = db.query(Employee).order_by(Employee.name).all()
    sites = db.query(Site).order_by(Site.name).all()
    shifts = (
        db.query(Shift)
        .options(joinedload(Shift.site), joinedload(Shift.employee))
        .filter(Shift.day >= week_days[0], Shift.day <= week_days[-1])
        .all()
    )

    matrix = {}
    crews_by_slot = {}
    for shift in shifts:
        if shift.employee_id is None:
            continue
        slot = (shift.day, shift.site_id, shift.start_time, shift.end_time)
        person = shift.employee
        if person and all(existing['id'] != person.id for existing in crews_by_slot.get(slot, [])):
            crews_by_slot.setdefault(slot, []).append({
                'id': person.id,
                'name': person.name,
                'image': person.profile_image_path or '',
            })
    for s in shifts:
        key = (s.employee_id, s.day)
        site_name = s.site.name if s.site and s.site.name else "Site"
        site_address = s.site.address if s.site and s.site.address else "Adresse unbekannt"
        time_window = f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}"
        shift_info = {
            'id': s.id,
            'site_id': s.site_id,
            'label': f"{site_name} - {site_address} ({time_window})",
            'site_name': site_name,
            'site_address': site_address,
            'time_window': time_window,
            'day_iso': s.day.isoformat(),
            'start_time_str': s.start_time.strftime('%H:%M'),
            'end_time_str': s.end_time.strftime('%H:%M'),
            'instructions': s.instructions or '',
            'is_recurring': bool(s.is_recurring),
            'assigned_people': crews_by_slot.get((s.day, s.site_id, s.start_time, s.end_time), []),
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


def _shift_interval(day: date, start_time: time, end_time: time) -> tuple[datetime, datetime]:
  start_dt = datetime.combine(day, start_time)
  end_dt = datetime.combine(day, end_time)
  if end_dt <= start_dt:
    end_dt += timedelta(days=1)
  return start_dt, end_dt


def _find_employee_schedule_conflict(
  db,
  employee_id: int,
  day: date,
  start_time: time,
  end_time: time,
  site_id: int,
  exclude_shift_id: int | None = None,
) -> str | None:
  candidate_start, candidate_end = _shift_interval(day, start_time, end_time)

  query = db.query(Shift).filter(Shift.employee_id == employee_id)
  if exclude_shift_id is not None:
    query = query.filter(Shift.id != exclude_shift_id)

  candidate_site_name = "Site"
  candidate_site = db.get(Site, site_id)
  if candidate_site and candidate_site.name:
    candidate_site_name = candidate_site.name

  for existing in query.all():
    existing_start, existing_end = _shift_interval(existing.day, existing.start_time, existing.end_time)

    if candidate_start < existing_end and existing_start < candidate_end:
      existing_site = db.get(Site, existing.site_id)
      existing_site_name = (existing_site.name if existing_site and existing_site.name else "Site")
      return (
        "Scheduling conflict: this employee is already assigned "
        f"({existing.day.strftime('%d.%m.%Y')} {existing.start_time.strftime('%H:%M')}–{existing.end_time.strftime('%H:%M')} · {existing_site_name})."
      )

    gap = None
    if candidate_end <= existing_start:
      gap = existing_start - candidate_end
    elif existing_end <= candidate_start:
      gap = candidate_start - existing_end

    if gap is not None and gap < timedelta(minutes=30) and existing.site_id != site_id:
      existing_site = db.get(Site, existing.site_id)
      existing_site_name = (existing_site.name if existing_site and existing_site.name else "Site")
      return (
        "Warnung: Zwischen Einsätzen an unterschiedlichen Standorten müssen mindestens 30 Minuten liegen "
        f"({existing_site_name} ↔ {candidate_site_name})."
      )

  return None


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
    elements.append(PageBreak())
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
    """Build the schedule PDF with no more than seven day columns per page."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), leftMargin=32, rightMargin=32,
        topMargin=32, bottomMargin=28,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SchedulePdfTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"), fontSize=19, leading=23,
    )
    subtitle_style = ParagraphStyle(
        "SchedulePdfSubtitle", parent=styles["Heading4"], fontName="Helvetica",
        textColor=colors.HexColor("#475569"), fontSize=10, leading=13,
    )
    header_style = ParagraphStyle(
        "SchedulePdfHeader", parent=styles["Heading5"], alignment=1,
        fontSize=8, leading=10, textColor=colors.whitesmoke,
    )
    cell_style = ParagraphStyle(
        "SchedulePdfCell", parent=styles["BodyText"], fontSize=7.5,
        leading=9, spaceAfter=0,
    )
    elements = []
    logo_path = os.path.join(app.root_path, "static", "logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=.8 * inch, height=.8 * inch)
        logo.hAlign = "LEFT"
        elements.extend([logo, Spacer(1, 7)])
    elements.append(Paragraph("Employee Schedule", title_style))
    elements.append(Paragraph(
        f"{week_days[0].strftime('%d %b %Y')} &ndash; {week_days[-1].strftime('%d %b %Y')}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 12))

    date_groups = []
    for day in week_days:
        week_key = day.isocalendar()[:2]
        if not date_groups or date_groups[-1][0].isocalendar()[:2] != week_key:
            date_groups.append([])
        date_groups[-1].append(day)

    for group_index, date_group in enumerate(date_groups):
        if group_index:
            elements.append(PageBreak())
            week_number = date_group[0].isocalendar()[1]
            elements.append(Paragraph(
                f"Week {week_number}: {date_group[0].strftime('%d %b')} &ndash; {date_group[-1].strftime('%d %b %Y')}",
                subtitle_style,
            ))
            elements.append(Spacer(1, 8))

        data = [[Paragraph("<b>Employee</b>", header_style)] + [
            Paragraph(f"<b>{day.strftime('%a')}</b><br/>{day.strftime('%d %b')}", header_style)
            for day in date_group
        ]]
        for employee in employees:
            employee_label = html.escape(employee.name or "")
            if employee.role:
                employee_label += f"<br/><font color='#64748b' size='7'>{html.escape(employee.role)}</font>"
            row = [Paragraph(employee_label, cell_style)]
            for day in date_group:
                shifts = matrix.get((employee.id, day), [])
                if not shifts:
                    row.append(Paragraph("<font color='#9ca3af'>Free</font>", cell_style))
                    continue
                descriptions = []
                for shift in shifts:
                    if isinstance(shift, dict):
                        site = html.escape(str(shift.get("site_name") or "Site"))
                        time_window = html.escape(str(shift.get("time_window") or ""))
                        address = html.escape(str(shift.get("site_address") or ""))
                        notes = html.escape(str(shift.get("instructions") or ""))
                        detail = " · ".join(part for part in (time_window, address, notes) if part)
                        descriptions.append(f"<b>{site}</b>" + (f"<br/><font color='#475569'>{detail}</font>" if detail else ""))
                    else:
                        descriptions.append(html.escape(str(shift or "")))
                row.append(Paragraph("<br/><br/>".join(descriptions), cell_style))
            data.append(row)

        employee_width = 1.55 * inch
        day_width = max(doc.width - employee_width, 1) / max(len(date_group), 1)
        table = Table(
            data, repeatRows=1, hAlign="LEFT",
            colWidths=[employee_width] + [day_width] * len(date_group),
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#e2e8f0")]),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
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
    bulk_email_label_style = ParagraphStyle(
      "ContactsBulkEmailLabel",
      parent=styles["Normal"],
      fontSize=9,
      textColor=colors.HexColor("#0f172a"),
      spaceAfter=2,
    )
    bulk_email_style = ParagraphStyle(
      "ContactsBulkEmail",
      parent=styles["Normal"],
      fontSize=9,
      textColor=colors.HexColor("#0f766e"),
      spaceAfter=10,
      leading=11,
    )
    email_cell_style = ParagraphStyle(
      "ContactsEmailCell",
      parent=styles["BodyText"],
      fontSize=10,
      textColor=colors.HexColor("#0f766e"),
    )

    logo_path = os.path.join(app.root_path, "static", "logo.png")

    def _draw_logo(canvas_obj, pdf_doc):
      if not os.path.exists(logo_path):
        return
      logo_width = 0.85 * inch
      logo_height = 0.85 * inch
      x = pdf_doc.leftMargin
      y = A4[1] - logo_height - 14
      try:
        canvas_obj.drawImage(
          logo_path,
          x,
          y,
          width=logo_width,
          height=logo_height,
          preserveAspectRatio=True,
          mask="auto",
        )
      except Exception:
        app.logger.debug("Unable to draw logo on contacts PDF page", exc_info=True)

    elements: list = []
    generated_at = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    elements.append(Paragraph("Elf's Plan - Contact Crawl", title_style))
    elements.append(Paragraph(f"Generated {generated_at}", subtitle_style))

    bulk_emails = sorted({(row.get("email") or "").strip() for row in rows if (row.get("email") or "").strip()})
    if bulk_emails:
      elements.append(Paragraph("All emails (semicolon separated):", bulk_email_label_style))
      elements.append(Paragraph("; ".join(bulk_emails), bulk_email_style))

    table_data = [["ID", "Business / Customer", "Email", "Phone"]]
    for row in rows:
        contact_id = str(row.get("contact_id") or "-").strip() or "-"
        business_name = (row.get("business_name") or "").strip() or "-"
        email = (row.get("email") or "").strip() or "-"
        phone = (row.get("phone") or "").strip() or "-"
        if email != "-":
            email_cell = Paragraph(f'<link href="mailto:{email}">{email}</link>', email_cell_style)
        else:
            email_cell = "-"
        table_data.append([contact_id, business_name, email_cell, phone])
    if len(table_data) == 1:
        table_data.append(["-", "-", "-", "-"])

    table = Table(
        table_data,
        colWidths=[doc.width * 0.08, doc.width * 0.27, doc.width * 0.35, doc.width * 0.30],
        hAlign="LEFT",
    )
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
    doc.build(elements, onFirstPage=_draw_logo, onLaterPages=_draw_logo)
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


def _get_admin_lang() -> str:
  chosen = (request.args.get("lang") or session.get("admin_lang") or "en").lower()
  if chosen not in ("en", "de"):
    chosen = "en"
  session["admin_lang"] = chosen
  return chosen

ADMIN_I18N = {
  "en": {
    "language_label": "Language",
    "overview": "Overview",
    "manage_employees": "Manage employees",
    "manage_sites": "Manage sites",
    "profile": "Profile",
    "assign_coverage": "Assign coverage",
    "crawler": "Crawler",
    "invoices": "Invoices",
    "account": "Account",
    "log_out": "Log out",
    "financial_dashboard": "Financial dashboard",
    "revenue_invoice_analytics": "Revenue & invoice analytics",
    "total_invoices": "Total invoices",
    "total_billed": "Total billed",
    "collected": "Collected",
    "outstanding": "Outstanding",
    "overdue_invoices": "Overdue invoices",
    "live_revenue_charts": "Live revenue charts",
    "track_hint": "Track the last 6 billing months and export the data anytime.",
    "open_invoices": "Open invoices",
    "paid_invoices": "Paid invoices",
    "needs_attention": "Requires follow-up",
    "hours": "Hours",
    "download_csv": "Download CSV",
    "revenue_hours_performance": "Revenue & hours performance",
    "revenue_hours_hint": "Interactive trends for invoice volume, revenue, and billed hours.",
    "average_invoice": "Average invoice",
    "this_month": "This month",
    "outstanding_label": "Outstanding",
    "monthly_breakdown": "Monthly breakdown",
    "team_directory": "Team directory",
    "employee_search_label": "Search employees",
    "open_employee_profiles": "Open employee profiles",
    "total_employees": "Total employees",
    "currently_shown": "Currently shown",
    "scheduled_today": "Scheduled today",
    "unassigned_this_week": "Unassigned this week",
    "search_placeholder": "Search by name or role",
    "reset_filters": "Reset filters",
    "of": "of",
    "no_matching_employees": "No matching employees",
  },
  "de": {
    "language_label": "Sprache",
    "overview": "Übersicht",
    "manage_employees": "Mitarbeiter verwalten",
    "manage_sites": "Standorte verwalten",
    "profile": "Profile",
    "assign_coverage": "Einsatzplanung",
    "crawler": "Crawler",
    "invoices": "Rechnungen",
    "account": "Konto",
    "log_out": "Abmelden",
    "financial_dashboard": "Finanzübersicht",
    "revenue_invoice_analytics": "Umsatz- & Rechnungsanalyse",
    "total_invoices": "Rechnungen gesamt",
    "total_billed": "Gesamtbetrag",
    "collected": "Eingegangen",
    "outstanding": "Ausstehend",
    "overdue_invoices": "Überfällige Rechnungen",
    "live_revenue_charts": "Live-Umsatzdiagramme",
    "track_hint": "Verfolge die letzten 6 Abrechnungsmonate und exportiere die Daten jederzeit.",
    "open_invoices": "Rechnungen öffnen",
    "paid_invoices": "Bezahlte Rechnungen",
    "needs_attention": "Nachverfolgung erforderlich",
    "hours": "Stunden",
    "download_csv": "CSV herunterladen",
    "revenue_hours_performance": "Umsatz- & Stundenentwicklung",
    "revenue_hours_hint": "Interaktive Trends für Rechnungsanzahl, Umsatz und gebuchte Stunden.",
    "average_invoice": "Durchschnittliche Rechnung",
    "this_month": "Diesen Monat",
    "outstanding_label": "Ausstehend",
    "monthly_breakdown": "Monatliche Übersicht",
    "team_directory": "Teamverzeichnis",
    "employee_search_label": "Mitarbeiter suchen",
    "open_employee_profiles": "Mitarbeiterprofile öffnen",
    "total_employees": "Mitarbeiter gesamt",
    "currently_shown": "Aktuell angezeigt",
    "scheduled_today": "Heute eingeplant",
    "unassigned_this_week": "Diese Woche ohne Einsatz",
    "search_placeholder": "Nach Name oder Rolle suchen",
    "reset_filters": "Filter zurücksetzen",
    "of": "von",
    "no_matching_employees": "Keine passenden Mitarbeiter",
  },
}

def _get_admin_i18n(lang: str):
  return ADMIN_I18N.get(lang, ADMIN_I18N["en"])


def _build_admin_dashboard_context(db):
  lang = _get_admin_lang()
  i18n = _get_admin_i18n(lang)
  today = date.today()
  week_start = today - timedelta(days=today.weekday())
  week_end = week_start + timedelta(days=7)
  current_month = today.strftime("%Y-%m")

  total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
  total_revenue = db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0)).scalar() or 0.0
  paid_revenue = db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0)).filter(Invoice.status == "paid").scalar() or 0.0
  outstanding_revenue = db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0)).filter(Invoice.status != "paid").scalar() or 0.0
  overdue_count = db.query(func.count(Invoice.id)).filter(Invoice.status == "overdue").scalar() or 0
  invoices_this_month = db.query(func.count(Invoice.id)).filter(Invoice.billing_month == current_month).scalar() or 0
  income_this_month = db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0)).filter(Invoice.billing_month == current_month).scalar() or 0.0

  stats = {
    "total_invoices": total_invoices,
    "total_revenue": total_revenue,
    "paid_revenue": paid_revenue,
    "outstanding_revenue": outstanding_revenue,
    "overdue_invoices": overdue_count,
    "invoices_this_month": invoices_this_month,
    "income_this_month": income_this_month,
  }

  months = []
  month_year = today.month
  month_year_year = today.year
  for _ in range(6):
    months.append(f"{month_year_year:04d}-{month_year:02d}")
    month_year -= 1
    if month_year < 1:
      month_year = 12
      month_year_year -= 1

  monthly_rows = (
    db.query(
      Invoice.billing_month,
      func.count(Invoice.id).label("invoice_count"),
      func.coalesce(func.sum(Invoice.total_amount), 0.0).label("total_income"),
      func.coalesce(func.sum(Invoice.total_hours), 0.0).label("total_hours"),
    )
    .filter(Invoice.billing_month.in_(months))
    .group_by(Invoice.billing_month)
    .all()
  )

  monthly_map = {row.billing_month: row for row in monthly_rows}

  site_rows = (
    db.query(
      Invoice.billing_month,
      Site.id,
      Site.name.label("site_name"),
      func.coalesce(func.sum(Invoice.total_amount), 0.0).label("income"),
      func.coalesce(func.sum(Invoice.total_hours), 0.0).label("hours"),
      func.avg(Invoice.hourly_rate).label("hourly_rate"),
    )
    .join(Site)
    .filter(Invoice.billing_month.in_(months))
    .group_by(Invoice.billing_month, Site.id, Site.name)
    .all()
  )

  sites_by_month = {}
  for row in site_rows:
    sites_by_month.setdefault(row.billing_month, []).append(
      {
        "site_name": row.site_name,
        "income": float(row.income),
        "hours": float(row.hours),
        "hourly_rate": float(row.hourly_rate or 0.0),
      }
    )

  max_income = max((float(row.total_income) for row in monthly_rows), default=0.0) or 1.0
  monthly_summaries = []
  chart_labels = []
  chart_income = []
  chart_invoice_counts = []
  chart_hours = []

  for month in months:
    row = monthly_map.get(month)
    if row:
      total_income = float(row.total_income)
      total_hours = float(row.total_hours)
      invoice_count = int(row.invoice_count)
    else:
      total_income = 0.0
      total_hours = 0.0
      invoice_count = 0

    monthly_summaries.append(
      {
        "month_name": date(int(month[:4]), int(month[5:]), 1).strftime("%b %Y"),
        "billing_month": month,
        "total_income": total_income,
        "total_hours": total_hours,
        "invoice_count": invoice_count,
        "fill_ratio": int((total_income / max_income) * 100),
        "sites": sorted(sites_by_month.get(month, []), key=lambda item: item["income"], reverse=True),
      }
    )
    chart_labels.append(date(int(month[:4]), int(month[5:]), 1).strftime("%b %Y"))
    chart_income.append(total_income)
    chart_invoice_counts.append(invoice_count)
    chart_hours.append(total_hours)

  recent_invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(6).all()
  due_soon = (
    db.query(Invoice)
    .filter(
      Invoice.status.in_(("sent", "overdue")),
      Invoice.due_date != None,
      Invoice.due_date <= datetime.combine(today + timedelta(days=14), time.max),
    )
    .order_by(Invoice.due_date.asc())
    .limit(6)
    .all()
  )

  period_label = today.strftime("%B %Y")
  today_label = today.strftime("%A %d %b %Y")
  # admin language selection (query param or session)
  lang = (request.args.get("lang") or session.get("admin_lang") or "en").lower()
  if lang not in ("en", "de"):
    lang = "en"

  ADMIN_I18N = {
    "en": {
      "live_revenue_charts": "Live revenue charts",
      "track_hint": "Track the last 6 billing months and export the data anytime.",
      "open_invoices": "Open invoices",
      "download_csv": "Download CSV",
      "revenue_hours_performance": "Revenue & hours performance",
      "revenue_hours_hint": "Interactive trends for invoice volume, revenue, and billed hours.",
      "average_invoice": "Average invoice",
      "this_month": "This month",
      "outstanding": "Outstanding",
      "monthly_breakdown": "Monthly breakdown",
    },
    "de": {
      "live_revenue_charts": "Live-Umsatzdiagramme",
      "track_hint": "Verfolge die letzten 6 Abrechnungsmonate und exportiere die Daten jederzeit.",
      "open_invoices": "Rechnungen öffnen",
      "download_csv": "CSV herunterladen",
      "revenue_hours_performance": "Umsatz- & Stundenentwicklung",
      "revenue_hours_hint": "Interaktive Trends für Rechnungsanzahl, Umsatz und gebuchte Stunden.",
      "average_invoice": "Durchschnittliche Rechnung",
      "this_month": "Diesen Monat",
      "outstanding": "Ausstehend",
      "monthly_breakdown": "Monatliche Übersicht",
    },
  }

  return {
    "stats": stats,
    "monthly_summaries": monthly_summaries,
    "chart_labels": chart_labels,
    "chart_income": chart_income,
    "chart_hours": chart_hours,
    "recent_invoices": recent_invoices,
    "due_soon": due_soon,
    "period_label": period_label,
    "today_label": today_label,
    "lang": lang,
    "i18n": i18n,
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
  if session.get("role") == "admin":
    if not next_url:
      return url_for("admin_employees")
    try:
      parsed = urlparse(next_url)
      path = parsed.path or ""
    except Exception:
      return url_for("admin_employees")
    if path.startswith("/employee") or path == url_for("login"):
      return url_for("admin_employees")
    return f"{path}?{parsed.query}" if parsed.query else path
  # Employees may only land on employee-scoped routes to avoid redirect loops.
  if session.get("role") == "site_manager":
    if not next_url:
      return url_for("admin_employees")
    try:
      parsed = urlparse(next_url)
      path = parsed.path or ""
    except Exception:
      return url_for("admin_employees")
    safe_prefixes = ("/site-manager", "/manager/", "/employee", "/schedule", "/admin/employees", "/admin/sites")
    if path.startswith(safe_prefixes):
      return f"{path}?{parsed.query}" if parsed.query else path
    return url_for("admin_employees")
  if session.get("role") == "sales_manager":
    if not next_url:
      return url_for("admin_employees")
    try:
      parsed = urlparse(next_url)
      path = parsed.path or ""
    except Exception:
      return url_for("admin_employees")
    safe_prefixes = ("/admin/sites", "/admin/employees", "/crawler", "/gpt")
    if path.startswith(safe_prefixes):
      return f"{path}?{parsed.query}" if parsed.query else path
    return url_for("admin_employees")
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


EMPLOYEE_LANG_DEFAULT = "de"
EMPLOYEE_LANG_SUPPORTED = ("en", "de", "uk")
EMPLOYEE_LANG_LABELS = {
  "de": "Deutsch",
  "en": "English",
  "uk": "Ð£ÐºÑ€Ð°Ñ—Ð½ÑÑŒÐºÐ°",
}

EMPLOYEE_TEXTS: dict[str, dict[str, str]] = {
  "en": {
    "login_secure_access": "Secure access",
    "login_workspace_label": "COMPANY WORKSPACE",
    "login_tagline": "Welcome to Elf's Plan.",
    "login_brand_message": "Sign in to access schedules, sites, and team information.",
    "login_form_intro": "Use your company sign-in details to continue.",
    "login_show_password": "Show password",
    "login_hide_password": "Hide password",
    "login_title": "Sign in",
    "login_username": "Username, work email, or login code",
    "login_password": "Password / PIN",
    "login_button": "Login",
    "login_hint": "Admins use their username and password. Employees use their work email or login code plus PIN.",
    "login_invalid": "Invalid credentials",
    "login_required": "Username and password are required",
    "language": "Language",
    "dashboard_title": "Crew dashboard",
    "sign_out": "Sign out",
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
    "completed": "Completed ðŸŽ‰",
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
    "confetti_complete": "Mission complete! ðŸŽ‰",
  },
  "de": {
    "login_secure_access": "Sicherer Zugang",
    "login_workspace_label": "UNTERNEHMENSBEREICH",
    "login_tagline": "Willkommen bei Elf's Plan.",
    "login_brand_message": "Melden Sie sich an, um Einsatzpläne, Standorte und Teamdaten aufzurufen.",
    "login_form_intro": "Melden Sie sich mit Ihren Unternehmensdaten an.",
    "login_show_password": "Passwort anzeigen",
    "login_hide_password": "Passwort ausblenden",
    "login_title": "Anmelden",
    "login_username": "Benutzername, E-Mail oder Login-Code",
    "login_password": "Passwort / PIN",
    "login_button": "Login",
    "login_hint": "Admins nutzen Benutzername und Passwort. Mitarbeitende nutzen E-Mail oder Login-Code plus PIN.",
    "login_invalid": "Ungültige Anmeldedaten",
    "login_required": "Benutzername und Passwort sind erforderlich",
    "language": "Sprache",
    "dashboard_title": "Mitarbeiter-Dashboard",
    "sign_out": "Abmelden",
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
    "completed": "Erledigt ðŸŽ‰",
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
    "confetti_complete": "Einsatz erledigt! ðŸŽ‰",
  },
  "uk": {
    "login_secure_access": "Ð‘ÐµÐ·Ð¿ÐµÑ‡Ð½Ð¸Ð¹ Ð²Ñ…Ñ–Ð´",
    "login_workspace_label": "Ð ÐžÐ‘ÐžÐ§Ð˜Ð™ ÐŸÐ ÐžÐ¡Ð¢Ð†Ð ",
    "login_tagline": "Ð›Ð°ÑÐºÐ°Ð²Ð¾ Ð¿Ñ€Ð¾ÑÐ¸Ð¼Ð¾ Ð´Ð¾ Elf's Plan.",
    "login_brand_message": "Ð£Ð²Ñ–Ð¹Ð´Ñ–Ñ‚ÑŒ, Ñ‰Ð¾Ð± Ð¿ÐµÑ€ÐµÐ³Ð»ÑÐ½ÑƒÑ‚Ð¸ Ð³Ñ€Ð°Ñ„Ñ–ÐºÐ¸, Ð¾Ð±'Ñ”ÐºÑ‚Ð¸ Ñ‚Ð° Ñ–Ð½Ñ„Ð¾Ñ€Ð¼Ð°Ñ†Ñ–ÑŽ Ð¿Ñ€Ð¾ ÐºÐ¾Ð¼Ð°Ð½Ð´Ñƒ.",
    "login_form_intro": "Ð£Ð²Ñ–Ð¹Ð´Ñ–Ñ‚ÑŒ Ð·Ð° Ð´Ð¾Ð¿Ð¾Ð¼Ð¾Ð³Ð¾ÑŽ Ð´Ð°Ð½Ð¸Ñ… ÐºÐ¾Ð¼Ð¿Ð°Ð½Ñ–Ñ—.",
    "login_show_password": "ÐŸÐ¾ÐºÐ°Ð·Ð°Ñ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ",
    "login_hide_password": "ÐŸÑ€Ð¸Ñ…Ð¾Ð²Ð°Ñ‚Ð¸ Ð¿Ð°Ñ€Ð¾Ð»ÑŒ",
    "login_title": "Ð£Ð²Ñ–Ð¹Ñ‚Ð¸",
    "login_username": "Ð†Ð¼'Ñ ÐºÐ¾Ñ€Ð¸ÑÑ‚ÑƒÐ²Ð°Ñ‡Ð°, Ñ€Ð¾Ð±Ð¾Ñ‡Ð° Ð¿Ð¾ÑˆÑ‚Ð° Ð°Ð±Ð¾ ÐºÐ¾Ð´ Ð²Ñ…Ð¾Ð´Ñƒ",
    "login_password": "ÐŸÐ°Ñ€Ð¾Ð»ÑŒ / PIN",
    "login_button": "Ð£Ð²Ñ–Ð¹Ñ‚Ð¸",
    "login_hint": "ÐÐ´Ð¼Ñ–Ð½Ð¸ Ð²Ñ…Ð¾Ð´Ñть за логіном і паролем. Співробітники — за робочим email або кодом входу та PIN.",
    "login_invalid": "ÐÐµÐ²Ñ–Ñ€Ð½Ñ– Ð¾Ð±Ð»Ñ–ÐºÐ¾Ð²Ñ– Ð´Ð°Ð½Ñ–",
    "login_required": "ÐŸÐ¾Ñ‚Ñ€Ñ–Ð±Ð½Ñ– Ñ–Ð¼'Ñ ÐºÐ¾Ñ€Ð¸ÑÑ‚ÑƒÐ²Ð°Ñ‡Ð° Ñ‚Ð° Ð¿Ð°Ñ€Ð¾Ð»ÑŒ",
    "language": "ÐœÐ¾Ð²Ð°",
    "dashboard_title": "ÐŸÐ°Ð½ÐµÐ»ÑŒ ÑÐ¿Ñ–Ð²Ñ€Ð¾Ð±Ñ–Ñ‚Ð½Ð¸ÐºÐ°",
    "sign_out": "Ð’Ð¸Ð¹Ñ‚Ð¸",
    "welcome": "ÐŸÑ€Ð¸Ð²Ñ–Ñ‚, {name}!",
    "today": "Ð¡ÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ–",
    "next": "Ð”Ð°Ð»Ñ–",
    "history": "Ð†ÑÑ‚Ð¾Ñ€Ñ–Ñ",
    "your_missions": "Ð’Ð°ÑˆÑ– Ð·Ð¼Ñ–Ð½Ð¸",
    "upcoming_jobs": "ÐœÐ°Ð¹Ð±ÑƒÑ‚Ð½Ñ– Ð·Ð¼Ñ–Ð½Ð¸",
    "recent_missions": "ÐžÑÑ‚Ð°Ð½Ð½Ñ– Ð·Ð¼Ñ–Ð½Ð¸",
    "location": "Ð›Ð¾ÐºÐ°Ñ†Ñ–Ñ",
    "instructions": "Ð†Ð½ÑÑ‚Ñ€ÑƒÐºÑ†Ñ–Ñ—",
    "duration": "Ð¢Ñ€Ð¸Ð²Ð°Ð»Ñ–ÑÑ‚ÑŒ",
    "scheduled": "Ð—Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð¾",
    "actual": "Ð¤Ð°ÐºÑ‚Ð¸Ñ‡Ð½Ð¾",
    "checkpoints": "Ð’Ñ–Ð´Ð¼Ñ–Ñ‚ÐºÐ¸",
    "clock_in": "ÐŸÐ¾Ñ‡Ð°Ñ‚Ð¸ Ð·Ð¼Ñ–Ð½Ñƒ",
    "clocked_in": "Почато ✔",
    "clock_out": "Ð—Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾",
    "open_maps": "Ð’Ñ–Ð´ÐºÑ€Ð¸Ñ‚Ð¸ Ð² Maps",
    "mark_complete": "ÐŸÐ¾Ð·Ð½Ð°Ñ‡Ð¸Ñ‚Ð¸ Ð·Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾",
    "completed": "Ð—Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾ ðŸŽ‰",
    "upload_before": "Завантажити фото «до»",
    "replace_before": "Замінити фото «до»",
    "upload_after": "Ð—Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶Ð¸Ñ‚Ð¸ Ñ„Ð¾Ñ‚Ð¾ Â«Ð¿Ñ–ÑÐ»Ñ»",
    "replace_after": "Ð—Ð°Ð¼Ñ–Ð½Ð¸Ñ‚Ð¸ Ñ„Ð¾Ñ‚Ð¾ Â«Ð¿Ñ–ÑÐ»Ñ»",
    "before": "Ð”Ð¾",
    "after": "ÐŸÑ–ÑÐ»Ñ",
    "today_empty_title": "ÐÐ° ÑÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ– Ð²Ñе виконано ✨",
    "today_empty_message": "ÐÐ° ÑÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ– Ð·Ð¼Ñ–Ð½ Ð½ÐµÐ¼Ð°Ñ”. ÐŸÐµÑ€ÐµÐ²Ñ–Ñ€Ñ‚Ðµ Ð¿Ñ–Ð·Ð½Ñ–ÑˆÐµ Ð°Ð±Ð¾ Ð·Ð²ÐµÑ€Ð½Ñ–Ñ‚ÑŒÑÑ Ð´Ð¾ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑ€Ð°.",
    "upcoming_empty": "ÐŸÐ¾ÐºÐ¸ Ñ‰Ð¾ Ð½ÐµÐ¼Ð°Ñ” Ð¼Ð°Ð¹Ð±ÑƒÑ‚Ð½Ñ–Ñ… Ð·Ð¼Ñ–Ð½.",
    "history_empty": "Ð†ÑÑ‚Ð¾Ñ€Ñ–Ñ Ð·Ð¼Ñ–Ð½ Ð¿Ð¾Ñ€Ð¾Ð¶Ð½Ñ.",
    "friendly_none": "Ð—Ð°Ñ€Ð°Ð· Ð½ÐµÐ¼Ð°Ñ” Ð·Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð¸Ñ… Ð·Ð¼Ñ–Ð½.",
    "friendly_one": "ÐÐ° ÑÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ– Ñƒ Ð²Ð°Ñ 1 Ð·Ð¼Ñ–Ð½Ð°.",
    "friendly_many": "ÐÐ° ÑÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ– Ð·Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð¾ {count} Ð·Ð¼Ñ–Ð½.",
    "status_scheduled": "Ð—Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð¾",
    "status_in_progress": "Ð’ Ð¿Ñ€Ð¾Ñ†ÐµÑÑ–",
    "status_completed": "Ð—Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾",
    "scheduled_job": "Ð—Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð° Ð·Ð¼Ñ–Ð½Ð°",
    "address_soon": "ÐÐ´Ñ€ÐµÑÑƒ Ð±ÑƒÐ´Ðµ Ð´Ð¾Ð´Ð°Ð½Ð¾",
    "no_special_instructions": "Ð¡ÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ– Ð±ÐµÐ· Ð´Ð¾Ð´Ð°Ñ‚ÐºÐ¾Ð²Ð¸Ñ… Ñ–Ð½ÑÑ‚Ñ€ÑƒÐºÑ†Ñ–Ð¹.",
    "no_notes": "ÐÐµÐ¼Ð°Ñ” Ð¿Ñ€Ð¸Ð¼Ñ–Ñ‚Ð¾Ðº.",
    "date_tbd": "Ð”Ð°Ñ‚Ñƒ Ð±ÑƒÐ´Ðµ Ð²Ð¸Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¾",
    "time_tbd": "Ð§Ð°Ñ Ð±ÑƒÐ´Ðµ Ð²Ð¸Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¾",
    "starts": "ÐŸÐ¾Ñ‡Ð°Ñ‚Ð¾Ðº {time}",
    "ends": "Ð—Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð½Ñ {time}",
    "shift_not_found": "Ð—Ð¼Ñ–Ð½Ñƒ Ð´Ð»Ñ Ð²Ð°ÑˆÐ¾Ð³Ð¾ Ð¿Ñ€Ð¾Ñ„Ñ–Ð»ÑŽ Ð½Ðµ Ð·Ð½Ð°Ð¹Ð´ÐµÐ½Ð¾.",
    "shift_not_today": "Ð¦Ñ Ð·Ð¼Ñ–Ð½Ð° Ð½Ðµ Ð·Ð°Ð¿Ð»Ð°Ð½Ð¾Ð²Ð°Ð½Ð° Ð½Ð° ÑÑŒÐ¾Ð³Ð¾Ð´Ð½Ñ–.",
    "clocked_in_success": "Ð’Ð¸ Ð²Ñ–Ð´Ð¼Ñ–Ñ‚Ð¸Ð»Ð¸ÑÑŒ. Ð“Ð°Ñ€Ð½Ð¾Ñ— Ñ€Ð¾Ð±Ð¾Ñ‚Ð¸!",
    "photo_type_required": "Ð’ÐºÐ°Ð¶Ñ–Ñ‚ÑŒ, Ñ†Ðµ Ñ„Ð¾Ñ‚Ð¾ Â«Ð´Ð¾Â» Ñ‡Ð¸ Â«Ð¿Ñ–ÑÐ»Ñ».",
    "photo_select_first": "Ð¡Ð¿Ð¾Ñ‡Ð°Ñ‚ÐºÑƒ Ð¾Ð±ÐµÑ€Ñ–Ñ‚ÑŒ Ñ„Ð¾Ñ‚Ð¾ Ð´Ð»Ñ Ð·Ð°Ð²Ð°Ð½Ñ‚Ð°Ð¶ÐµÐ½Ð½Ñ.",
    "photo_type_invalid": "ÐÐµÐ¿Ñ–Ð´Ñ‚Ñ€Ð¸Ð¼ÑƒÐ²Ð°Ð½Ð¸Ð¹ Ñ‚Ð¸Ð¿ Ñ„Ð°Ð¹Ð»Ñƒ. Ð’Ð¸ÐºÐ¾Ñ€Ð¸ÑÑ‚Ð°Ð¹Ñ‚Ðµ PNG, JPG Ð°Ð±Ð¾ JPEG.",
    "photo_save_error": "ÐÐµ Ð²Ð´Ð°Ð»Ð¾ÑÑ Ð·Ð±ÐµÑ€ÐµÐ³Ñ‚Ð¸ Ñ„Ð¾Ñ‚Ð¾. Ð¡Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ñ‰Ðµ Ñ€Ð°Ð·.",
    "photo_saved": "Фото «{label}» збережено. Чудово!",
    "complete_success": "Ð—Ð¼Ñ–Ð½Ñƒ Ð·Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾. Ð”ÑÐºÑƒÑ”Ð¼Ð¾!",
    "confetti_complete": "Ð—Ð¼Ñ–Ð½Ñƒ Ð·Ð°Ð²ÐµÑ€ÑˆÐµÐ½Ð¾! ðŸŽ‰",
  },
}


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
    "ÑƒÐºÑ€Ð°Ñ—Ð½ÑÑŒÐºÐ°": "uk",
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


@app.route("/employee-sw.js")
def employee_service_worker():
  return send_file(
    os.path.join(APP_ROOT, "static", "employee-sw.js"),
    mimetype="application/javascript",
    max_age=0,
  )


@app.route("/manager-sw.js")
def manager_service_worker():
  return send_file(
    os.path.join(APP_ROOT, "static", "site-manager-sw.js"),
    mimetype="application/javascript",
    max_age=0,
  )


@app.route("/login", methods=["GET", "POST"])
def login():
  lang = _get_employee_lang()
  ui = EMPLOYEE_TEXTS.get(lang, EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT])
  next_url = _safe_next_url()
  if session.get("role") == "admin" and session.get("auth"):
    return redirect(next_url or url_for("admin_employees"))
  if session.get("role") == "site_manager" and session.get("employee_id"):
    return redirect(_employee_redirect_target(next_url))
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
        return redirect(next_url or url_for("admin_employees"))

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

      if employee and employee.has_platform_access and employee.is_active and employee.login_pin_hash:
        if check_password_hash(employee.login_pin_hash, password):
          session.clear()
          session["role"] = employee.access_role if employee.access_role in {"admin", "site_manager", "sales_manager"} else "employee"
          if employee.access_role == "admin":
            session["auth"] = True
          session["employee_id"] = employee.id
          session["employee_name"] = employee.name
          session["employee_code"] = employee.login_code
          session["employee_lang"] = lang
          return redirect(_employee_redirect_target(next_url))
      error = _employee_text(lang, "login_invalid")
    else:
      error = _employee_text(lang, "login_required")

  return render_template_string(
    LOGIN_TEMPLATE,
    error=error,
    next_value=next_url,
    lang=lang,
    ui=ui,
    lang_labels=EMPLOYEE_LANG_LABELS,
  )


@app.route("/employee")
@app.route("/employee/dashboard")
@employee_login_required
def employee_dashboard():
  employee_id = session.get("employee_id")
  employee_name = session.get("employee_name", "Team member")
  lang = _get_employee_lang()
  ui = EMPLOYEE_TEXTS.get(lang, EMPLOYEE_TEXTS[EMPLOYEE_LANG_DEFAULT])
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
  return render_template_string(
    EMPLOYEE_DASHBOARD_TEMPLATE,
    lang=lang,
    ui=ui,
    lang_labels=EMPLOYEE_LANG_LABELS,
    welcome_message=_employee_text(lang, "welcome", name=employee_name),
    employee_name=employee_name,
    today_label=today_label,
    friendly_message=friendly_message,
    shifts=shift_cards,
    upcoming_jobs=upcoming_cards,
    history=history_cards,
    todays_shifts_count=len(shift_cards),
    todays_shifts_for_notify=[{"site_name": s["site_name"], "time_window": s["time_window"]} for s in shift_cards],
  )


@app.route("/employee/shifts/<int:shift_id>/clock-in", methods=["POST"])
@employee_login_required
def employee_clock_in(shift_id: int):
  employee_id = session.get("employee_id")
  lang = _get_employee_lang()
  lat = _coerce_float(request.form.get("lat"))
  lng = _coerce_float(request.form.get("lng"))

  db = SessionLocal()
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


@app.route("/employee/shifts/<int:shift_id>/upload", methods=["POST"])
@employee_login_required
def employee_upload_photo(shift_id: int):
  employee_id = session.get("employee_id")
  lang = _get_employee_lang()
  photo_type = (request.form.get("photo_type") or "").strip().lower()
  file = request.files.get("photo")

  db = SessionLocal()
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

    if not _allowed_image(file.filename):
      flash(_employee_text(lang, "photo_type_invalid"))
      return redirect(url_for("employee_dashboard"))

    relative_path = _build_shift_proof_relative_path(shift, photo_type, file.filename)
    upload_subpath = relative_path[len("uploads/") :].replace("/", os.sep)
    destination = os.path.join(app.config["UPLOAD_FOLDER"], upload_subpath)
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    try:
      file.save(destination)
    except OSError:
      logging.exception("Failed to save uploaded photo for shift %s", shift_id)
      flash(_employee_text(lang, "photo_save_error"))
      return redirect(url_for("employee_dashboard"))

    photo_label = _employee_text(lang, "before") if photo_type == "before" else _employee_text(lang, "after")
    if photo_type == "before":
      _remove_photo(shift.before_photo_path)
      shift.before_photo_path = relative_path
    else:
      _remove_photo(shift.after_photo_path)
      shift.after_photo_path = relative_path

    db.commit()
    flash(_employee_text(lang, "photo_saved", label=photo_label))
  finally:
    db.close()

  return redirect(url_for("employee_dashboard"))


@app.route("/employee/shifts/<int:shift_id>/complete", methods=["POST"])
@employee_login_required
def employee_complete_shift(shift_id: int):
  employee_id = session.get("employee_id")
  lang = _get_employee_lang()
  lat = _coerce_float(request.form.get("lat"))
  lng = _coerce_float(request.form.get("lng"))

  db = SessionLocal()
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


@app.route("/shift/<int:shift_id>/edit", methods=["POST"])
@site_manager_required
def edit_shift(shift_id: int):
    db = SessionLocal()
    try:
        shift = db.get(Shift, shift_id)
        if not shift:
            flash("Shift not found.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        raw_employee_ids = request.form.getlist("employee_ids[]")
        if not raw_employee_ids:
            legacy_employee_id = (request.form.get("employee_id") or "").strip()
            raw_employee_ids = [legacy_employee_id] if legacy_employee_id else []
        employee_ids = []
        for raw_id in raw_employee_ids:
            try:
                employee_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if employee_id not in employee_ids:
                employee_ids.append(employee_id)
        if not employee_ids:
            flash("Keep at least one employee assigned to this shift.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        day_str = (request.form.get("day") or "").strip()
        start_str = (request.form.get("start_time") or "").strip()
        end_str = (request.form.get("end_time") or "").strip()
        instructions = (request.form.get("instructions") or "").strip() or None
        try:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
        except (ValueError, TypeError):
            flash("Enter a valid date and time.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        if end_time <= start_time:
            flash("End time must be after start time.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        original_crew = db.query(Shift).filter(
            Shift.site_id == shift.site_id,
            Shift.day == shift.day,
            Shift.start_time == shift.start_time,
            Shift.end_time == shift.end_time,
            Shift.employee_id.isnot(None),
        ).all()
        if shift.employee_id is not None and all(item.id != shift.id for item in original_crew):
            original_crew.append(shift)
        current_by_employee = {item.employee_id: item for item in original_crew}
        selected_employees = {employee.id: employee for employee in db.query(Employee).filter(Employee.id.in_(employee_ids)).all()}
        if len(selected_employees) != len(employee_ids):
            flash("One or more selected employees were not found.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        for employee_id, employee in selected_employees.items():
            if not employee.is_active and employee_id not in current_by_employee:
                flash(f"{employee.name} is inactive and cannot be added to a shift.", "warning")
                return redirect(request.referrer or url_for("schedule_dashboard"))

        removed = [item for employee_id, item in current_by_employee.items() if employee_id not in selected_employees]
        if any(item.clock_in_at or item.clock_out_at for item in removed):
            flash("An employee who has started this shift cannot be removed.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        conflict_messages = []
        for employee_id in employee_ids:
            existing = current_by_employee.get(employee_id)
            conflict_message = _find_employee_schedule_conflict(
                db,
                employee_id=employee_id,
                day=day,
                start_time=start_time,
                end_time=end_time,
                site_id=shift.site_id,
                exclude_shift_id=existing.id if existing else None,
            )
            if conflict_message:
                conflict_messages.append(f"{selected_employees[employee_id].name}: {conflict_message}")

        for employee_id, item in current_by_employee.items():
            if employee_id not in selected_employees:
                db.delete(item)
                continue
            item.day = day
            item.start_time = start_time
            item.end_time = end_time
            item.instructions = instructions

        reusable_open_shift = shift if shift.employee_id is None else None
        for employee_id in employee_ids:
            if employee_id in current_by_employee:
                continue
            if reusable_open_shift is not None:
                reusable_open_shift.employee_id = employee_id
                reusable_open_shift.day = day
                reusable_open_shift.start_time = start_time
                reusable_open_shift.end_time = end_time
                reusable_open_shift.instructions = instructions
                reusable_open_shift = None
                continue
            db.add(Shift(
                employee_id=employee_id,
                site_id=shift.site_id,
                day=day,
                start_time=start_time,
                end_time=end_time,
                instructions=instructions,
                is_recurring=shift.is_recurring,
            ))

        db.commit()
        flash("Shift and assigned employees updated successfully.", "success")
        if conflict_messages:
            flash(f"Shift was saved despite scheduling conflicts. Review: {conflict_messages[0]}", "warning")
    except Exception:
        db.rollback()
        app.logger.exception("Error editing shift %s", shift_id)
        flash("Error updating shift.", "warning")
    finally:
        db.close()

    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/shift/<int:shift_id>/assign-employee", methods=["POST"])
@site_manager_required
def assign_employee_to_shift(shift_id: int):
    """Add one or more employees as matching assignments to an existing shift."""
    db = SessionLocal()
    try:
        source = db.get(Shift, shift_id)
        raw_ids = request.form.getlist("employee_ids[]")
        if not raw_ids:
            single_id = request.form.get("employee_id")
            raw_ids = [single_id] if single_id else []
        employee_ids = []
        for raw_id in raw_ids:
            try:
                employee_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if employee_id not in employee_ids:
                employee_ids.append(employee_id)
        if not source or not employee_ids:
            flash("Choose at least one employee for this shift.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))

        assigned = 0
        skipped = []
        conflicts = []
        for employee_id in employee_ids:
            employee = db.get(Employee, employee_id)
            if not employee or not employee.is_active:
                skipped.append("An employee was not found or is inactive.")
                continue

            duplicate = db.query(Shift.id).filter(
                Shift.employee_id == employee.id,
                Shift.site_id == source.site_id,
                Shift.day == source.day,
                Shift.start_time == source.start_time,
                Shift.end_time == source.end_time,
            ).first()
            if duplicate:
                skipped.append(f"{employee.name} is already assigned to this shift.")
                continue

            conflict = _find_employee_schedule_conflict(
                db, employee_id=employee.id, day=source.day,
                start_time=source.start_time, end_time=source.end_time,
                site_id=source.site_id,
                exclude_shift_id=source.id if source.employee_id is None else None,
            )
            if conflict:
                conflicts.append(f"{employee.name}: {conflict}")

            if source.employee_id is None and assigned == 0:
                source.employee_id = employee.id
            else:
                db.add(Shift(
                    employee_id=employee.id, site_id=source.site_id, day=source.day,
                    start_time=source.start_time, end_time=source.end_time,
                    instructions=source.instructions, is_recurring=source.is_recurring,
                ))
            assigned += 1

        if assigned:
            db.commit()
            flash(f"{assigned} employee(s) added to the shift.", "success")
            if conflicts:
                flash(f"Employees were assigned despite scheduling conflicts. Review: {conflicts[0]}", "warning")
        elif skipped:
            db.rollback()
        for message in skipped[:3]:
            flash(message, "warning")
    except Exception:
        db.rollback()
        app.logger.exception("Could not assign employees to shift %s", shift_id)
        flash("Employees could not be added to the shift.", "warning")
    finally:
        db.close()
    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/shift/<int:shift_id>/move", methods=["POST"])
@site_manager_required
def move_shift_day(shift_id: int):
    db = SessionLocal()
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

        conflict_message = _find_employee_schedule_conflict(
          db,
          employee_id=new_employee_id,
          day=new_day,
          start_time=shift.start_time,
          end_time=shift.end_time,
          site_id=shift.site_id,
          exclude_shift_id=shift.id,
        )

        shift.day = new_day
        shift.employee_id = new_employee_id
        db.commit()
        result = {"ok": True, "conflict": bool(conflict_message)}
        if conflict_message:
          result["notification"] = f"Shift moved and saved despite a scheduling conflict: {conflict_message}"
        return jsonify(result)
    except Exception as exc:
        db.rollback()
        app.logger.error("Error moving shift %s: %s", shift_id, exc)
        return jsonify({"ok": False, "error": "Failed to move shift"}), 500
    finally:
        db.close()


@app.route("/shift/batch-edit", methods=["POST"])
@site_manager_required
def batch_edit_shifts():
  db = SessionLocal()
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
        flash("End time must be after start time.", "warning")
        return redirect(request.referrer or url_for("schedule_dashboard"))

    shifts = db.query(Shift).filter(Shift.id.in_(shift_ids)).all()
    if not shifts:
      flash("Keine gültigen Einsätze gefunden.", "warning")
      return redirect(request.referrer or url_for("schedule_dashboard"))

    updated_count = 0
    conflict_messages = []
    for shift in shifts:
      target_day = new_day if new_day is not None else shift.day
      target_start = new_start if new_start is not None else shift.start_time
      target_end = new_end if new_end is not None else shift.end_time

      conflict_message = _find_employee_schedule_conflict(
        db,
        employee_id=shift.employee_id,
        day=target_day,
        start_time=target_start,
        end_time=target_end,
        site_id=shift.site_id,
        exclude_shift_id=shift.id,
      )
      if conflict_message:
        conflict_messages.append(f"Shift #{shift.id}: {conflict_message}")

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
      if conflict_messages:
        flash(f"{len(conflict_messages)} shift(s) were saved despite scheduling conflicts. Review: {conflict_messages[0]}", "warning")
      flash(f"{updated_count} Einsatz/Einsätze erfolgreich aktualisiert.")
    else:
      flash("Es wurden keine Einsätze aktualisiert.", "warning")

    return redirect(request.referrer or url_for("schedule_dashboard"))
  except Exception as exc:
    db.rollback()
    app.logger.error("Error during batch shift edit: %s", exc)
    flash("Fehler beim Aktualisieren der ausgewählten Einsätze.", "warning")
    return redirect(request.referrer or url_for("schedule_dashboard"))
  finally:
    db.close()


@app.route("/shift/batch-delete", methods=["POST"])
@site_manager_required
def batch_delete_shifts():
    db = SessionLocal()
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


@app.route("/shift/delete/<int:shift_id>")
@site_manager_required
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


@app.route("/schedule/batch-release", methods=["POST"])
@site_manager_required
def batch_release_shifts():
    db = SessionLocal()
    try:
        ids = request.form.getlist("shift_ids[]")
        released = 0
        blocked = 0
        for raw_id in ids:
            try:
                shift = db.get(Shift, int(raw_id))
            except (TypeError, ValueError):
                continue
            if not shift or shift.employee_id is None:
                continue
            if shift.clock_in_at or shift.clock_out_at:
                blocked += 1
                continue
            shift.employee_id = None
            released += 1
        if released:
            db.commit()
            flash(f"{released} shift(s) are now open.")
        if blocked:
            flash(f"Could not release {blocked} shift(s) that have already started.", "warning")
        if not released and not blocked:
            flash("Select at least one shift first.", "warning")
    except Exception:
        db.rollback()
        app.logger.exception("Could not release selected shifts")
        flash("Could not release the selected shifts.", "warning")
    finally:
        db.close()
    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/schedule/batch-assign", methods=["POST"])
@site_manager_required
def batch_assign_shifts():
    db = SessionLocal()
    try:
        employee_id = request.form.get("employee_id", type=int)
        employee = db.get(Employee, employee_id) if employee_id else None
        if not employee or employee.is_active is False:
            flash("Select an active employee.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        ids = request.form.getlist("shift_ids[]")
        assigned = 0
        conflicts = 0
        for raw_id in ids:
            try:
                shift = db.get(Shift, int(raw_id))
            except (TypeError, ValueError):
                continue
            if not shift:
                continue
            if shift.employee_id == employee.id:
                continue
            conflict = _find_employee_schedule_conflict(
                db, employee_id=employee.id, day=shift.day,
                start_time=shift.start_time, end_time=shift.end_time,
                site_id=shift.site_id, exclude_shift_id=shift.id,
            )
            if conflict:
                conflicts += 1
            shift.employee_id = employee.id
            assigned += 1
        if assigned:
            db.commit()
            flash(f"Assigned {assigned} shift(s) to {employee.name}.")
        if conflicts:
            flash(f"{conflicts} shift(s) were assigned despite scheduling conflicts. Review the schedule.", "warning")
        if not assigned and not conflicts:
            flash("None of the selected shifts could be assigned.", "warning")
    except Exception:
        db.rollback()
        app.logger.exception("Could not assign selected shifts")
        flash("Could not assign the selected shifts.", "warning")
    finally:
        db.close()
    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/schedule/batch-duplicate", methods=["POST"])
@site_manager_required
def batch_duplicate_shifts():
    db = SessionLocal()
    try:
        ids = request.form.getlist("shift_ids[]")[:200]
        target_raw = (request.form.get("target_day") or "").strip()
        try:
            target_day = datetime.strptime(target_raw, "%Y-%m-%d").date()
        except ValueError:
            flash("Select a target date.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        shifts = db.query(Shift).filter(Shift.id.in_([int(i) for i in ids if str(i).isdigit()])).all()
        if not shifts:
            flash("Select at least one shift first.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        first_day = min(shift.day for shift in shifts)
        created = 0
        conflicts = 0
        for source in shifts:
            target = target_day + timedelta(days=(source.day - first_day).days)
            conflict = _find_employee_schedule_conflict(
                db, employee_id=source.employee_id, day=target,
                start_time=source.start_time, end_time=source.end_time,
                site_id=source.site_id,
            ) if source.employee_id is not None else None
            if conflict:
                conflicts += 1
            db.add(Shift(
                employee_id=source.employee_id, site_id=source.site_id, day=target,
                start_time=source.start_time, end_time=source.end_time,
                instructions=source.instructions,
            ))
            created += 1
        if created:
            db.commit()
            flash(f"Duplicated {created} shift(s).")
        if conflicts:
            flash(f"{conflicts} duplicate shift(s) were saved despite scheduling conflicts. Review the schedule.", "warning")
    except Exception:
        db.rollback()
        app.logger.exception("Could not duplicate selected shifts")
        flash("Could not duplicate the selected shifts.", "warning")
    finally:
        db.close()
    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/schedule/tours", methods=["POST"])
@site_manager_required
def create_schedule_tour():
    db = SessionLocal()
    try:
        name = (request.form.get("tour_name") or "").strip()[:160]
        ids = [int(i) for i in request.form.getlist("shift_ids[]") if str(i).isdigit()]
        shifts = db.query(Shift).filter(Shift.id.in_(ids)).all()
        if not name or not shifts:
            flash("Enter a tour name and select at least one shift.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        if any(shift.employee_id is None for shift in shifts):
            flash("Assign open shifts to an employee before adding them to a tour.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        days = {shift.day for shift in shifts}
        if len(days) != 1:
            flash("A tour can only contain shifts from the same day.", "warning")
            return redirect(request.referrer or url_for("schedule_dashboard"))
        tour = Tour(name=name, day=next(iter(days)))
        db.add(tour)
        for position, shift in enumerate(sorted(shifts, key=lambda item: (item.start_time, item.site.name if item.site else "")), 1):
            tour.stops.append(TourStop(shift=shift, position=position))
        db.commit()
        flash(f"Tour '{tour.name}' created with {len(shifts)} stops.")
        return redirect(url_for("schedule_dashboard", tour_id=tour.id))
    except Exception:
        db.rollback()
        app.logger.exception("Could not create schedule tour")
        flash("Could not create the tour.", "warning")
    finally:
        db.close()
    return redirect(request.referrer or url_for("schedule_dashboard"))


@app.route("/schedule/tours/<int:tour_id>", methods=["GET"])
@site_manager_required
def view_schedule_tour(tour_id: int):
    db = SessionLocal()
    try:
        tour = db.get(Tour, tour_id)
        if not tour:
            return jsonify({"error": "Tour not found"}), 404
        return jsonify({
            "id": tour.id,
            "name": tour.name,
            "day": tour.day.isoformat(),
            "stops": [{
                "position": stop.position,
                "employee": stop.shift.employee.name if stop.shift.employee else None,
                "site": stop.shift.site.name if stop.shift.site else "",
                "address": stop.shift.site.address if stop.shift.site else "",
                "start": stop.shift.start_time.strftime("%H:%M"),
                "end": stop.shift.end_time.strftime("%H:%M"),
            } for stop in tour.stops],
        })
    finally:
        db.close()


@app.route("/schedule", methods=["GET", "POST"])
@site_manager_required
def schedule_dashboard():
    db = SessionLocal()
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
            create_open_shift = request.form.get("create_open_shift") == "on"
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
            repeat_weekly = request.form.get("repeat_weekly") == "on"
            if repeat_weekly and day_values:
              repeat_until_raw = (request.form.get("repeat_until") or "").strip()
              try:
                repeat_until = datetime.strptime(repeat_until_raw, "%Y-%m-%d").date()
              except ValueError:
                repeat_until = None
              if not repeat_until:
                flash("Choose an end date for the repeating schedule.", "warning")
                return redirect(url_for("schedule_dashboard", **request.args.to_dict(flat=False)))
              recurrence_start = min(day_values)
              if repeat_until < recurrence_start or (repeat_until - recurrence_start).days > 364:
                flash("The end date must be on or after the start date and within one year.", "warning")
                return redirect(url_for("schedule_dashboard", **request.args.to_dict(flat=False)))
              try:
                repeat_interval = int(request.form.get("repeat_interval") or 1)
              except (TypeError, ValueError):
                repeat_interval = 0
              if not 1 <= repeat_interval <= 52:
                flash("Repeat interval must be between 1 and 52 weeks.", "warning")
                return redirect(url_for("schedule_dashboard", **request.args.to_dict(flat=False)))
              weekdays = set()
              for weekday_raw in request.form.getlist("repeat_weekday"):
                try:
                  weekday = int(weekday_raw)
                except (TypeError, ValueError):
                  continue
                if 0 <= weekday <= 6:
                  weekdays.add(weekday)
              if not weekdays:
                weekdays = {recurrence_start.weekday()}
              first_week = recurrence_start - timedelta(days=recurrence_start.weekday())
              recurring_days = []
              candidate = recurrence_start
              while candidate <= repeat_until:
                week_offset = (candidate - first_week).days // 7
                if week_offset % repeat_interval == 0 and candidate.weekday() in weekdays:
                  recurring_days.append(candidate)
                candidate += timedelta(days=1)
              if not recurring_days:
                flash("No shifts match the selected weekdays and recurrence dates.", "warning")
                return redirect(url_for("schedule_dashboard", **request.args.to_dict(flat=False)))
              day_values = recurring_days
            if (employee_ids or create_open_shift) and site_id and day_values and start_str and duration_hours_str:
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
                for employee_id in (employee_ids or [None]):
                  employee = db.get(Employee, employee_id) if employee_id is not None else None
                  employee_label = employee.name if employee else "Open shift"
                  for day_val in day_values:
                    end_dt = datetime.combine(day_val, start_val) + duration_delta
                    end_val = end_dt.time()

                    conflict_message = None
                    if employee_id is not None:
                      conflict_message = _find_employee_schedule_conflict(
                        db,
                        employee_id=employee_id,
                        day=day_val,
                        start_time=start_val,
                        end_time=end_val,
                        site_id=int(site_id),
                      )
                    if conflict_message:
                      blocked_messages.append(f"{employee_label} ({day_val.strftime('%d.%m.%Y')}): {conflict_message}")

                    shift = Shift(
                      employee_id=employee_id,
                      site_id=int(site_id),
                      day=day_val,
                      start_time=start_val,
                      end_time=end_val,
                      instructions=instructions_val,
                      is_recurring=repeat_weekly,
                    )
                    db.add(shift)
                    db.flush()
                    created += 1
                if created:
                  db.commit()
                  flash(f"{created} Einsatz/Einsätze wurden eingeplant.")
                if blocked_messages:
                  flash(f"{len(blocked_messages)} shift(s) were saved despite scheduling conflicts. Review: {blocked_messages[0]}", "warning")
                if not created and not blocked_messages:
                  flash("No shifts could be scheduled.", "warning")
            query_args = request.args.to_dict(flat=False)
            query_args.pop("create", None)
            if request.form.get("create_another") == "1":
              query_args["create"] = ["1"]
            return redirect(url_for("schedule_dashboard", **query_args))

        selected_employee_id = request.args.get("employee_id", type=int)
        selected_site_id = request.args.get("site_id", type=int)
        selected_schedule_split = request.args.get("split", "employees")
        if selected_schedule_split not in {"employees", "objects", "orders"}:
          selected_schedule_split = "employees"
        selected_tour_id = request.args.get("tour_id", type=int)
        current_tour = db.get(Tour, selected_tour_id) if selected_tour_id else None
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

        selected_period = request.args.get("period", "week")
        if selected_period not in {"day", "week", "fortnight", "month", "custom"}:
          legacy_days = request.args.get("days", type=int)
          selected_period = "day" if legacy_days == 1 else "week"
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

        if start_date_val is None:
          start_date_val = date.today()

        if selected_period == "custom":
          end_date_str = request.args.get("end_date", "")
          try:
            requested_end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
          except ValueError:
            requested_end = start_date_val
          if requested_end < start_date_val:
            start_date_val, requested_end = requested_end, start_date_val
          range_length = max(1, min((requested_end - start_date_val).days + 1, 84))
          week_days = _get_day_range(start=start_date_val, days=range_length)
          start_date_val = week_days[0]
        elif selected_period == "day":
          week_days = [start_date_val]
          start_date_val = week_days[0]
        elif selected_period == "month":
          month_start = start_date_val.replace(day=1)
          next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
          week_days = _get_day_range(start=month_start, days=(next_month_start - month_start).days)
          start_date_val = month_start
        else:
          weeks = 2 if selected_period == "fortnight" else 1
          week_days = _get_day_range(start=start_date_val, weeks=weeks)
          start_date_val = week_days[0]
        weeks = max(1, (len(week_days) + 6) // 7)
        display_days = week_days
        schedule_weeks = []
        for display_day in display_days:
          week_key = display_day.isocalendar()[:2]
          if not schedule_weeks or schedule_weeks[-1][0].isocalendar()[:2] != week_key:
            schedule_weeks.append([])
          schedule_weeks[-1].append(display_day)
        employees, sites, matrix = _load_schedule_context(db, week_days)

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

        # The Objects split groups employee assignments into one site/day/time card.
        # Keep every underlying shift id so bulk actions still operate on each assignment.
        site_cells = {}
        site_slot_groups = {}
        for (employee_id, shift_day), day_shifts in filtered_matrix.items():
          if selected_schedule_split == "objects" and selected_employee_id and employee_id != selected_employee_id:
            continue
          for shift_info in day_shifts:
            slot_key = (
              shift_info.get("site_id"), shift_day, shift_info.get("start_time_str"),
              shift_info.get("end_time_str"), employee_id is None,
            )
            grouped = site_slot_groups.get(slot_key)
            if grouped is None:
              grouped = dict(shift_info)
              grouped["shift_ids"] = []
              grouped["is_open"] = employee_id is None
              grouped["assigned_people"] = list(shift_info.get("assigned_people") or [])
              site_slot_groups[slot_key] = grouped
            grouped["shift_ids"].append(shift_info["id"])
            known_people = {person.get("id") for person in grouped["assigned_people"]}
            for person in shift_info.get("assigned_people") or []:
              if person.get("id") not in known_people:
                grouped["assigned_people"].append(person)
                known_people.add(person.get("id"))
        for grouped in site_slot_groups.values():
          site_cells.setdefault((grouped.get("site_id"), date.fromisoformat(grouped["day_iso"])), []).append(grouped)
        for site_day_shifts in site_cells.values():
          site_day_shifts.sort(key=lambda item: (item.get("start_time_str") or "", item.get("site_name") or ""))

        grid_employee_ids = {e.id for e in visible_employees}
        shift_days_for_grid = {day for (emp_id, day) in filtered_matrix.keys() if emp_id in grid_employee_ids or emp_id is None}
        # Keep the full selected period in the grid, even when some days are empty.
        visible_days = week_days
        has_any_shifts = bool(shift_days_for_grid)

        pdf_params = {"week": week_days[0].isoformat(), "period": selected_period}
        if selected_period == "custom":
          pdf_params["end_date"] = week_days[-1].isoformat()
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
            visible_sites=[s for s in sites if not selected_site_id or s.id == selected_site_id],
            week_days=week_days,
            visible_days=visible_days,
            display_days=display_days,
            schedule_weeks=schedule_weeks,
            schedule_period_start=week_days[0],
            schedule_period_end=week_days[-1],
            selected_period=selected_period,
            has_any_shifts=has_any_shifts,
            weeks=weeks,
            start_date=start_date_val.isoformat() if start_date_val else "",
            cells=filtered_matrix,
            site_cells=site_cells,
            selected_schedule_split=selected_schedule_split,
            reportlab_available=REPORTLAB_AVAILABLE,
            selected_employee_id=selected_employee_id,
            selected_site_id=selected_site_id,
            selected_employee=selected_employee,
            selected_site=selected_site,
            pdf_url=pdf_url,
            hours_pdf_url=hours_pdf_url,
            free_day=free_day_str,
            free_week_start=free_week_start_str,
            current_tour=current_tour,
            open_create=request.args.get("create") == "1",
            active_page="schedule",
            is_site_manager=session.get("role") == "site_manager",
        )
        return schedule_html
    finally:
        db.close()


@app.route("/schedule/preview-import-previous-month")
@site_manager_required
def schedule_preview_import_previous_month():
    db = SessionLocal()
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
        first_day, last_day = _week_range_by_offset(reference_day=date.today(), weeks_back=source_offset)
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
                td = _add_weeks(s.day, k)
                target_days.append(td.strftime("%Y-%m-%d"))
                cm = _find_employee_schedule_conflict(
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


@app.route("/schedule/import-previous-month", methods=["POST"])
@site_manager_required
def schedule_import_previous_month():
    db = SessionLocal()
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
        first_day, last_day = _week_range_by_offset(reference_day=date.today(), weeks_back=source_offset)
        query = db.query(Shift).filter(Shift.day >= first_day, Shift.day <= last_day)
        if selected_ids:
            query = query.filter(Shift.id.in_(selected_ids))
        shifts = query.order_by(Shift.day.asc()).all()
        created = 0
        conflicts = 0
        skipped_existing = 0
        skipped_inactive = 0
        for s in shifts:
          emp = s.employee if s.employee else db.get(Employee, s.employee_id)
          # for target weeks 1..target_offset, create a copy per week if no existing/conflict
          for k in range(1, target_offset + 1):
            td = _add_weeks(s.day, k)
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
            conflict_msg = _find_employee_schedule_conflict(
              db, s.employee_id, td, s.start_time, s.end_time, s.site_id
            )
            if conflict_msg:
              conflicts += 1
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
            "skipped_conflict": 0,
            "conflicts": conflicts,
            "skipped_existing": skipped_existing,
            "skipped_inactive": skipped_inactive,
        })
    finally:
        db.close()


@app.route("/schedule/free-available")
@site_manager_required
def schedule_free_available():
    """Return JSON list of active employees who are free for the given date range and time interval.

    Query params:
      - free_start_date (YYYY-MM-DD) required
      - free_end_date (YYYY-MM-DD) optional (defaults to start_date)
      - free_start_time (HH:MM) optional
      - free_end_time (HH:MM) optional
      - site_id optional to limit by site
    """
    db = SessionLocal()
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


@app.route("/admin")
@login_required
def admin_dashboard():
  db = SessionLocal()
  try:
    context = _build_admin_dashboard_context(db)
    # ensure older templates expecting `ui` still work by providing a ui bundle
    ui_bundle = context.get("i18n") if isinstance(context.get("i18n"), dict) else {}
    return render_template_string(
      ADMIN_TEMPLATE,
      active_page="dashboard",
      ui=ui_bundle,
      **context,
    )
  finally:
    db.close()


@app.route("/dashboard")
@login_required
def dashboard_redirect():
  return redirect(url_for("admin_dashboard"))


@app.route("/admin/dashboard/download-report", methods=["GET"])
@login_required
def admin_dashboard_download_report():
  db = SessionLocal()
  try:
    context = _build_admin_dashboard_context(db)
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Month", "Invoice Count", "Total Income (€)", "Total Hours"])
    for summary in context["monthly_summaries"]:
      writer.writerow([
        summary["month_name"],
        summary["invoice_count"],
        f"{summary['total_income']:.2f}",
        f"{summary['total_hours']:.2f}",
      ])
    csv_buffer.seek(0)
    return send_file(
      io.BytesIO(csv_buffer.getvalue().encode("utf-8")),
      mimetype="text/csv",
      as_attachment=True,
      download_name="dashboard_monthly_income.csv",
    )
  finally:
    db.close()


@app.route("/admin/employees", methods=["GET", "POST"])
@site_or_sales_manager_required
def admin_employees():
  db = SessionLocal()
  is_main_admin = session.get("role") == "admin"
  is_site_manager = session.get("role") == "site_manager"
  is_sales_manager = session.get("role") == "sales_manager"
  lang = _get_admin_lang()
  i18n = _get_admin_i18n(lang)
  try:
    search_q = (request.args.get("q") or "").strip()
    work_type_filter = (request.args.get("work_type") or "").strip()
    if work_type_filter == "Geringfügige":
      work_type_filter = "Intern"
    role_filter = (request.args.get("role") or "").strip()
    staff_type_filter = (request.args.get("staff_type_filter") or "").strip()
    branch_filter = (request.args.get("branch_filter") or "").strip()
    status_filter = (request.args.get("status_filter") or "all").strip().lower()
    if status_filter not in {"all", "active", "passive"}:
      status_filter = "all"
    if request.method == "POST":
      if is_sales_manager:
        abort(403)
      action = (request.form.get("action") or "create").strip().lower()
      send_credentials_requested = request.form.get("send_credentials_email") == "1"
      if send_credentials_requested and not is_main_admin:
        abort(403)
      emp_id = request.form.get("id")
      redirect_q = (request.form.get("redirect_q") or "").strip()
      redirect_page_raw = (request.form.get("redirect_page") or "").strip()
      redirect_page_val = None
      if redirect_page_raw.isdigit():
        redirect_page_val = max(int(redirect_page_raw), 1)
      redirect_params: dict[str, int | str] = {}
      if redirect_q:
        redirect_params["q"] = redirect_q
      redirect_work_type = (request.form.get("redirect_work_type") or "").strip()
      redirect_role = (request.form.get("redirect_role") or "").strip()
      redirect_staff_type = (request.form.get("redirect_staff_type") or "").strip()
      redirect_branch = (request.form.get("redirect_branch") or "").strip()
      redirect_status = (request.form.get("redirect_status") or "all").strip()
      if redirect_work_type:
        redirect_params["work_type"] = redirect_work_type
      if redirect_role:
        redirect_params["role"] = redirect_role
      if redirect_staff_type:
        redirect_params["staff_type_filter"] = redirect_staff_type
      if redirect_branch in {"Wien", "Graz"}:
        redirect_params["branch_filter"] = redirect_branch
      if redirect_status in {"all", "active", "passive"} and redirect_status != "all":
        redirect_params["status_filter"] = redirect_status
      if redirect_page_val and redirect_page_val > 1:
        redirect_params["page"] = redirect_page_val
      redirect_url = url_for("admin_employees", **redirect_params)
      return_to = (request.form.get("return_to") or "").strip()
      if return_to.startswith("/") and not return_to.startswith("//"):
        redirect_url = return_to

      if action == "create":
        name = (request.form.get("name") or "").strip()
        role = (request.form.get("role") or "").strip()
        create_has_access = request.form.get("has_platform_access") == "1" if is_main_admin else False
        create_email = (request.form.get("login_email") or "").strip()
        create_status = (request.form.get("worker_status") or "active").strip().lower()
        if send_credentials_requested and (not create_has_access or create_status != "active" or not EMAIL_REGEX.fullmatch(create_email)):
          flash("Enable platform access, set a valid email, and set the employee to Active before sending sign-in details.", "warning")
          return redirect(redirect_url)
        is_active_val = request.form.get("is_active")
        is_active_bool = True
        if is_active_val is not None:
          try:
            is_active_bool = bool(int(is_active_val))
          except Exception:
            is_active_bool = True
        if not name:
          flash("Employee name is required.", "warning")
        if name:
          staff_functions = _normalize_staff_functions(request.form.get("staff_functions"), fallback=(request.form.get("staff_type") or "Cleaner").strip())
          staff_type = staff_functions[0]
          branch = (request.form.get("branch") or "Wien").strip()
          if branch not in {"Wien", "Graz"}:
            branch = "Wien"
          has_platform_access = create_has_access if is_main_admin else False
          worker_status = (request.form.get("worker_status") or "active").strip().lower()
          if worker_status not in {"active", "passive"}:
            worker_status = "active"
          is_active_bool = worker_status == "active"
          work_type = (request.form.get("profile_work_type") or "Teilzeit").strip()
          if work_type not in {"Teilzeit", "Vollzeit", "Intern", "Geringfügige"}:
            work_type = "Teilzeit"
          group_type = (request.form.get("profile_group_type") or "Lohngruppe").strip()
          if group_type not in {"Lohngruppe", "Verwendungsgruppe"}:
            group_type = "Lohngruppe"
          employee = Employee(
            name=name, role=role or staff_type, is_active=is_active_bool, worker_status=worker_status,
          staff_type=staff_type, staff_functions=json.dumps(staff_functions), branch=branch, has_platform_access=has_platform_access,
          access_role=(request.form.get("access_role") or "employee").strip() if has_platform_access and is_main_admin and (request.form.get("access_role") or "employee").strip() in {"employee", "site_manager", "sales_manager", "admin"} else "employee",
            login_email=create_email if has_platform_access and is_main_admin else None,
            profile_phone=(request.form.get("profile_phone") or "").strip() or None,
            profile_address=(request.form.get("profile_address") or "").strip() or None,
            profile_zip_code=(request.form.get("profile_zip_code") or "").strip() or None,
            profile_city=(request.form.get("profile_city") or "").strip() or None,
            profile_contract_start_date=((request.form.get("profile_contract_start_date") or "").strip() or None) if is_main_admin else None,
            profile_contract_end_date=((request.form.get("profile_contract_end_date") or "").strip() or None) if is_main_admin else None,
            profile_employment_type=(request.form.get("profile_employment_type") or "").strip() or "Reinigungskraft",
            profile_group_type=group_type if is_main_admin else None,
            profile_group_number=(request.form.get("profile_group_number") or "").strip() or None if is_main_admin else None,
            profile_euros_per_hour=(request.form.get("profile_euros_per_hour") or "").strip() or None if is_main_admin else None,
            profile_working_hours=(request.form.get("profile_working_hours") or "").strip() or None,
            profile_work_type=work_type,
          )
          db.add(employee)
          db.commit()
          generated_pin = None
          if employee.has_platform_access:
            existing_codes = _collect_existing_codes(db, exclude_id=employee.id)
            if not (employee.login_code or "").strip():
              employee.login_code = _generate_employee_login_code(name, existing_codes)
            if not (employee.login_pin_hash or "").strip():
              generated_pin = _generate_employee_pin()
              employee.login_pin_hash = generate_password_hash(generated_pin)
              employee.login_pin_plain = generated_pin
          # handle optional profile image upload
          file_obj = request.files.get("profile_image")
          if file_obj:
            saved = _save_profile_image(file_obj, f"emp{employee.id}")
            if saved:
              employee.profile_image_path = saved
          db.commit()
          if generated_pin:
            if send_credentials_requested:
              email_sent, email_message = send_employee_credentials_email(employee, generated_pin)
              if email_sent:
                flash(email_message, "success")
              else:
                _remember_credentials_for_session(employee.id, employee.login_code, generated_pin)
                flash(email_message, "warning")
            else:
              _remember_credentials_for_session(employee.id, employee.login_code, generated_pin)
          flash("Employee added.", "success")
      elif action == "update" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp:
          requested_access = request.form.get("has_platform_access") == "1" if is_main_admin else emp.has_platform_access
          requested_email = (request.form.get("login_email") or "").strip()
          requested_status = (request.form.get("worker_status") or emp.worker_status or "active").strip().lower()
          if send_credentials_requested and (not requested_access or requested_status != "active" or not EMAIL_REGEX.fullmatch(requested_email)):
            flash("Enable platform access, set a valid email, and set the employee to Active before sending sign-in details.", "warning")
            return redirect(redirect_url)
          name = (request.form.get("name") or "").strip()
          role = (request.form.get("role") or "").strip()
          profile_zip_code = (request.form.get("profile_zip_code") or "").strip()
          profile_city = (request.form.get("profile_city") or "").strip()
          profile_contract_start_date = (request.form.get("profile_contract_start_date") or "").strip()
          profile_contract_end_date = (request.form.get("profile_contract_end_date") or "").strip()
          profile_euros_per_hour = (request.form.get("profile_euros_per_hour") or "").strip()
          profile_working_hours = (request.form.get("profile_working_hours") or "").strip()
          profile_work_type = (request.form.get("profile_work_type") or "").strip()
          if profile_work_type not in {"Teilzeit", "Vollzeit", "Intern", "Geringfügige"}:
            profile_work_type = "Teilzeit"
          profile_group_type = (request.form.get("profile_group_type") or "").strip()
          profile_group_number = (request.form.get("profile_group_number") or "").strip()
          if profile_group_type not in {"Lohngruppe", "Verwendungsgruppe"}:
            profile_group_type = "Lohngruppe"
          if name and (is_main_admin or emp.access_role == "employee"):
            generated_pin = None
            emp.name = name
            emp.role = role or None
            worker_status = (request.form.get("worker_status") or emp.worker_status or "active").strip().lower()
            if worker_status in {"active", "passive"}:
              emp.worker_status = worker_status
              emp.is_active = worker_status == "active"
            submitted_staff_functions = _normalize_staff_functions(request.form.get("staff_functions"), fallback=emp.staff_type or "Cleaner")
            submitted_staff_type = submitted_staff_functions[0]
            emp.staff_functions = json.dumps(submitted_staff_functions)
            emp.staff_type = submitted_staff_type
            submitted_branch = (request.form.get("branch") or emp.branch or "Wien").strip()
            emp.branch = submitted_branch if submitted_branch in {"Wien", "Graz"} else "Wien"
            if is_main_admin:
              emp.has_platform_access = requested_access
              if not emp.has_platform_access:
                emp.login_email = None
                emp.login_code = None
                emp.login_pin_hash = None
                emp.login_pin_plain = None
              else:
                emp.login_email = requested_email or None
                submitted_access_role = (request.form.get("access_role") or "employee").strip()
                if submitted_access_role in {"employee", "site_manager", "sales_manager", "admin"}:
                  emp.access_role = submitted_access_role
            # Non-admin editors can change job functions but cannot grant or revoke platform access.
            emp.profile_phone = (request.form.get("profile_phone") or "").strip() or None
            emp.profile_address = (request.form.get("profile_address") or "").strip() or None
            emp.profile_zip_code = profile_zip_code or None
            emp.profile_city = profile_city or None
            if is_main_admin:
              emp.profile_contract_start_date = profile_contract_start_date or None
              emp.profile_contract_end_date = profile_contract_end_date or None
            if is_main_admin:
              emp.profile_euros_per_hour = profile_euros_per_hour or None
            emp.profile_working_hours = profile_working_hours or None
            emp.profile_work_type = profile_work_type or "Teilzeit"
            if is_main_admin:
              emp.profile_group_type = profile_group_type or "Lohngruppe"
              emp.profile_group_number = profile_group_number or None
              if emp.has_platform_access:
                existing_codes = _collect_existing_codes(db, exclude_id=emp.id)
                if not (emp.login_code or "").strip():
                  emp.login_code = _generate_employee_login_code(emp.name, existing_codes)
                if send_credentials_requested or not (emp.login_pin_hash or "").strip():
                  generated_pin = _generate_employee_pin()
                  emp.login_pin_hash = generate_password_hash(generated_pin)
                  emp.login_pin_plain = generated_pin
            # handle optional profile image upload (replace existing)
            file_obj = request.files.get("profile_image")
            if file_obj:
              saved = _save_profile_image(file_obj, f"emp{emp.id}", replace_path=emp.profile_image_path)
              if saved:
                emp.profile_image_path = saved
            db.commit()
            if generated_pin:
              if send_credentials_requested:
                email_sent, email_message = send_employee_credentials_email(emp, generated_pin)
                if email_sent:
                  flash(email_message, "success")
                else:
                  _remember_credentials_for_session(emp.id, emp.login_code, generated_pin)
                  flash(email_message, "warning")
              else:
                _remember_credentials_for_session(emp.id, emp.login_code, generated_pin)
            flash("Employee updated.", "success")
      elif action == "set_status" and emp_id:
        emp = db.get(Employee, int(emp_id))
        new_status = (request.form.get("worker_status") or "").strip().lower()
        if emp and (is_main_admin or emp.access_role == "employee") and new_status in {"active", "passive"}:
          emp.worker_status = new_status
          emp.is_active = new_status == "active"
          db.commit()
          flash("Employee status updated.", "success")
      elif action == "delete" and emp_id:
        emp = db.get(Employee, int(emp_id))
        if emp and (is_main_admin or emp.access_role == "employee"):
          emp_name = emp.name
          # remove associated profile image from disk
          for employee_document in db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == emp.id).all():
            try:
              document_path = os.path.join(EMPLOYEE_DOCUMENT_FOLDER, employee_document.storage_name)
              if os.path.isfile(document_path):
                os.remove(document_path)
            except OSError:
              logging.exception("Failed removing document for deleted employee %s", emp.id)
            db.delete(employee_document)
          try:
            _remove_photo(emp.profile_image_path)
          except Exception:
            logging.exception("Failed removing profile image for deleted employee %s", emp.id)
          db.delete(emp)
          db.commit()
          flash("Employee deleted.", "success")
      elif action == "credentials_share" and emp_id:
        if not is_main_admin:
          abort(403)
        emp = db.get(Employee, int(emp_id))
        if emp and (is_main_admin or emp.access_role == "employee"):
          emp.has_platform_access = True
          existing_codes = _collect_existing_codes(db, exclude_id=emp.id)
          if not (emp.login_code or "").strip():
            emp.login_code = _generate_employee_login_code(emp.name, existing_codes)
          new_pin = (emp.login_pin_plain or "").strip()
          if not new_pin:
            new_pin = _generate_employee_pin()
            emp.login_pin_hash = generate_password_hash(new_pin)
            emp.login_pin_plain = new_pin
          db.commit()
          _remember_credentials_for_session(emp.id, emp.login_code, new_pin)
          flash("Login details are ready to share.", "success")
        else:
          flash("Could not update login details.", "warning")
        return redirect(redirect_url)
      elif action == "credentials_email" and emp_id:
        if not is_main_admin:
          abort(403)
        emp = db.get(Employee, int(emp_id))
        if not emp or not emp.has_platform_access or emp.worker_status != "active":
          flash("Enable platform access and set the employee to Active before sending sign-in details.", "warning")
          return redirect(redirect_url)
        recipient = (emp.login_email or "").strip()
        if not EMAIL_REGEX.fullmatch(recipient):
          flash("Add a valid employee email address before sending sign-in details.", "warning")
          return redirect(redirect_url)
        existing_codes = _collect_existing_codes(db, exclude_id=emp.id)
        login_code = (emp.login_code or "").strip() or _generate_employee_login_code(emp.name, existing_codes)
        new_pin = _generate_employee_pin()
        previous_code = emp.login_code
        emp.login_code = login_code
        email_sent, email_message = send_employee_credentials_email(emp, new_pin)
        if email_sent:
          emp.has_platform_access = True
          emp.login_pin_hash = generate_password_hash(new_pin)
          emp.login_pin_plain = new_pin
          db.commit()
          flash(email_message, "success")
        else:
          emp.login_code = previous_code
          db.rollback()
          flash(email_message, "warning")
        return redirect(redirect_url)
      elif action == "credentials_update" and emp_id:
        if not is_main_admin:
          abort(403)
        emp = db.get(Employee, int(emp_id))
        if emp and (is_main_admin or emp.access_role == "employee"):
          emp.has_platform_access = True
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
            emp.login_pin_plain = new_pin
            pin_snippet = new_pin
          db.commit()
          if pin_snippet:
            _remember_credentials_for_session(emp.id, emp.login_code, pin_snippet)
            flash("Login details updated.", "success")
          else:
            flash("Login details updated.", "success")
        else:
          flash("Could not update login details.", "warning")
        return redirect(redirect_url)

      return redirect(redirect_url)

    saved_credential_snippets = session.pop("credential_snippets", {})
    credential_snippets = saved_credential_snippets if is_main_admin else {}
    auto_generated = _generate_missing_employee_credentials(db) if is_main_admin else {}
    for emp_id, data in auto_generated.items():
      key = str(emp_id)
      if key not in credential_snippets:
        credential_snippets[key] = {
          "code": data.get("code"),
          "pin": data.get("pin"),
        }

    base_query = db.query(Employee)
    if is_site_manager:
      base_query = base_query.filter(Employee.access_role == "employee")
    elif is_sales_manager:
      base_query = base_query.filter(Employee.access_role == "employee")
    status_counts = {"all": 0, "active": 0, "passive": 0}
    for worker_status, count in base_query.with_entities(Employee.worker_status, func.count(Employee.id)).group_by(Employee.worker_status).all():
      normalized_status = worker_status if worker_status in {"active", "passive"} else "active"
      status_counts[normalized_status] += count
      status_counts["all"] += count
    if status_filter != "all":
      base_query = base_query.filter(Employee.worker_status == status_filter)
    if search_q:
      like = f"%{search_q}%"
      base_query = base_query.filter(
        or_(
          Employee.name.ilike(like),
          Employee.role.ilike(like),
          Employee.login_email.ilike(like),
          Employee.profile_phone.ilike(like),
          Employee.profile_address.ilike(like),
          Employee.profile_zip_code.ilike(like),
          Employee.profile_city.ilike(like),
          Employee.staff_type.ilike(like),
          Employee.staff_functions.ilike(like),
          Employee.branch.ilike(like),
        )
      )
    if work_type_filter:
      if work_type_filter == "Intern":
        base_query = base_query.filter(Employee.profile_work_type.in_(["Intern", "Geringfügige"]))
      else:
        base_query = base_query.filter(Employee.profile_work_type == work_type_filter)
    if role_filter:
      base_query = base_query.filter(Employee.role.ilike(f"%{role_filter}%"))
    if staff_type_filter:
      base_query = base_query.filter(_employee_staff_function_filter(staff_type_filter))
    if branch_filter in {"Wien", "Graz"}:
      base_query = base_query.filter(Employee.branch == branch_filter)
    employee_staff_types = list(STAFF_FUNCTION_OPTIONS)
    if staff_type_filter not in employee_staff_types:
      staff_type_filter = ""
    stored_work_types = [
      row[0] for row in db.query(Employee.profile_work_type)
      .filter(Employee.profile_work_type.isnot(None), Employee.profile_work_type != "")
      .distinct().order_by(Employee.profile_work_type.asc()).all()
    ]
    employee_work_types = sorted({"Intern" if work_type == "Geringfügige" else work_type for work_type in stored_work_types})

    free_filter = request.args.get('free', default='0') == '1'
    free_day_str = (request.args.get('free_day') or '').strip()
    free_week_start_str = (request.args.get('free_week_start') or '').strip()
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

    if free_filter:
      if free_day is not None:
        scheduled_employee_ids_subq = (
          db.query(Shift.employee_id)
          .filter(Shift.day == free_day)
          .distinct()
          .subquery()
        )
      else:
        week_start = free_week_start if free_week_start is not None else date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=7)
        scheduled_employee_ids_subq = (
          db.query(Shift.employee_id)
          .filter(Shift.day >= week_start, Shift.day < week_end)
          .distinct()
          .subquery()
        )
      base_query = base_query.filter(~Employee.id.in_(scheduled_employee_ids_subq))

    total_employee_query = db.query(func.count(Employee.id))
    if is_site_manager or is_sales_manager:
      total_employee_query = total_employee_query.filter(Employee.access_role == "employee")
    total_employees = total_employee_query.scalar() or 0
    filtered_employees = base_query.count()

    per_page = 25
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
    employee_function_map = {emp.id: _employee_staff_functions(emp) for emp in employees}
    show_shifts_column = any("Cleaner" in employee_function_map[emp.id] for emp in employees)
    employee_column_count = 3 + int(not is_site_manager and not is_sales_manager) + int(show_shifts_column) + 1 + int(not is_sales_manager)
    employee_to_edit_id = request.args.get("edit_employee", type=int)
    edit_employee = db.get(Employee, employee_to_edit_id) if employee_to_edit_id else None
    if edit_employee and not is_main_admin and edit_employee.access_role != "employee":
      edit_employee = None
    employee_to_edit_data = None
    if edit_employee:
      employee_to_edit_data = {
        "id": edit_employee.id, "name": edit_employee.name, "role": edit_employee.role or "",
        "active": "1" if edit_employee.is_active != 0 else "0", "workerStatus": edit_employee.worker_status or ("active" if edit_employee.is_active else "passive"), "phone": edit_employee.profile_phone or "",
        "address": edit_employee.profile_address or "", "zip": edit_employee.profile_zip_code or "", "city": edit_employee.profile_city or "",
        "start": edit_employee.profile_contract_start_date or "" if is_main_admin else "", "end": edit_employee.profile_contract_end_date or "" if is_main_admin else "",
        "rate": edit_employee.profile_euros_per_hour or "" if is_main_admin else "",
        "hours": edit_employee.profile_working_hours or "", "workType": "Intern" if edit_employee.profile_work_type == "Geringfügige" else edit_employee.profile_work_type or "Teilzeit",
        "groupType": edit_employee.profile_group_type or "Lohngruppe" if is_main_admin else "", "groupNumber": edit_employee.profile_group_number or "" if is_main_admin else "",
        "accessRole": edit_employee.access_role or "employee", "staffType": edit_employee.staff_type or "Cleaner",
        "staffFunctions": _employee_staff_functions(edit_employee),
        "branch": edit_employee.branch or "Wien", "platformAccess": "1" if edit_employee.has_platform_access else "0",
        "loginEmail": edit_employee.login_email or "",
        "image": edit_employee.profile_image_path or "",
      }

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
      .join(Employee, Employee.id == Shift.employee_id)
      .filter(Shift.day >= week_start, Shift.day < week_end, _employee_staff_function_filter("Cleaner"))
      .distinct()
      .all()
      if row[0] is not None
    }
    cleaner_query = db.query(func.count(Employee.id)).filter(_employee_staff_function_filter("Cleaner"))
    if is_site_manager or is_sales_manager:
      cleaner_query = cleaner_query.filter(Employee.access_role == "employee")
    unassigned_employees = max((cleaner_query.scalar() or 0) - len(scheduled_emp_ids), 0)

    return render_template_string(
      ADMIN_EMPLOYEES_TEMPLATE,
      active_page="employees",
      lang=lang,
      i18n=i18n,
      is_main_admin=is_main_admin,
      is_site_manager=is_site_manager,
      is_sales_manager=is_sales_manager,
      employees=employees,
      employee_to_edit_data=employee_to_edit_data,
      employee_function_map=employee_function_map,
      shift_counts=shift_counts,
      total_employees=total_employees,
      filtered_employees=filtered_employees,
      search_q=search_q,
      work_type_filter=work_type_filter,
      role_filter=role_filter,
      staff_type_filter=staff_type_filter,
      branch_filter=branch_filter,
      employee_staff_types=employee_staff_types,
      show_shifts_column=show_shifts_column,
      employee_column_count=employee_column_count,
      status_filter=status_filter,
      status_counts=status_counts,
      employee_work_types=employee_work_types,
      today_shifts=today_shifts,
      unassigned_employees=unassigned_employees,
      credential_snippets=credential_snippets,
      employee_shift_groups=employee_shift_groups,
      free_filter=free_filter,
      free_day=free_day_str,
      free_week_start=free_week_start_str,
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


@app.route("/admin/employees/<int:employee_id>", methods=["GET", "POST"])
@site_or_sales_manager_required
def admin_employee_detail(employee_id: int):
  db = SessionLocal()
  is_site_manager = session.get("role") == "site_manager"
  is_sales_manager = session.get("role") == "sales_manager"
  try:
    employee = db.get(Employee, employee_id)
    if not employee:
      flash("Employee not found.", "warning")
      return redirect(url_for("admin_employees"))
    if session.get("role") != "admin" and employee.access_role != "employee":
      flash("You do not have access to this employee record.", "warning")
      return redirect(url_for("admin_employees"))
    if request.method == "POST":
      if is_sales_manager:
        abort(403)
      action = (request.form.get("action") or "upload_employee_document").strip()
      if action == "update_staff_access":
        submitted_functions = _normalize_staff_functions(
          request.form.get("staff_functions"), fallback=employee.staff_type or "Cleaner"
        )
        employee.staff_functions = json.dumps(submitted_functions)
        employee.staff_type = submitted_functions[0]
        if session.get("role") == "admin":
          allowed_access_roles = {"employee", "site_manager", "sales_manager", "admin"}
          submitted_access_role = (request.form.get("access_role") or employee.access_role or "employee").strip()
          if submitted_access_role not in allowed_access_roles:
            flash("Choose a valid system access level.", "warning")
            return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#account")
          employee.access_role = submitted_access_role
          employee.has_platform_access = request.form.get("has_platform_access") == "1"
          employee.login_email = (request.form.get("login_email") or "").strip() or None
        # Non-admin editors can change functions but cannot grant or revoke platform access.
        generated_pin = None
        if employee.has_platform_access:
          existing_codes = _collect_existing_codes(db, exclude_id=employee.id)
          if not (employee.login_code or "").strip():
            employee.login_code = _generate_employee_login_code(employee.name, existing_codes)
          if not (employee.login_pin_hash or "").strip():
            generated_pin = _generate_employee_pin()
            employee.login_pin_hash = generate_password_hash(generated_pin)
            employee.login_pin_plain = generated_pin
        try:
          db.commit()
          if generated_pin:
            _remember_credentials_for_session(employee.id, employee.login_code, generated_pin)
          flash("Employee functions and platform access saved.", "success")
        except Exception:
          db.rollback()
          app.logger.exception("Could not update employee functions employee_id=%s", employee.id)
          flash("Platform access could not be saved. Please try again.", "warning")
        return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#account")
      if action == "update_profile":
        if is_sales_manager:
          abort(403)
        name = (request.form.get("name") or "").strip()
        if not name:
          flash("Employee name is required.", "warning")
          return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#general")
        employee.name = name
        employee.role = (request.form.get("role") or "").strip() or None
        employee.profile_phone = (request.form.get("profile_phone") or "").strip() or None
        employee.profile_address = (request.form.get("profile_address") or "").strip() or None
        employee.profile_zip_code = (request.form.get("profile_zip_code") or "").strip() or None
        employee.profile_city = (request.form.get("profile_city") or "").strip() or None
        staff_types = {"Cleaner", "Office administrator", "IT", "Reception", "Intern", "Graphic designer", "Other"}
        staff_type = (request.form.get("staff_type") or employee.staff_type or "Cleaner").strip()
        if staff_type in staff_types:
          employee.staff_type = staff_type
        branch = (request.form.get("branch") or employee.branch or "Wien").strip()
        employee.branch = branch if branch in {"Wien", "Graz"} else "Wien"
        work_type = (request.form.get("profile_work_type") or "Teilzeit").strip()
        employee.profile_work_type = work_type if work_type in {"Teilzeit", "Vollzeit", "Intern", "Geringfügige"} else "Teilzeit"
        employee.profile_working_hours = (request.form.get("profile_working_hours") or "").strip() or None
        worker_status = (request.form.get("worker_status") or employee.worker_status or "active").strip().lower()
        if worker_status in {"active", "passive"}:
          employee.worker_status = worker_status
          employee.is_active = worker_status == "active"
        if session.get("role") == "admin":
          employee.profile_euros_per_hour = (request.form.get("profile_euros_per_hour") or "").strip() or None
          employee.profile_group_type = (request.form.get("profile_group_type") or "Lohngruppe").strip()
          employee.profile_group_number = (request.form.get("profile_group_number") or "").strip() or None
        image = request.files.get("profile_image")
        if image and image.filename:
          saved_image = _save_profile_image(image, f"emp{employee.id}", replace_path=employee.profile_image_path)
          if saved_image:
            employee.profile_image_path = saved_image
        try:
          db.commit()
          flash("Employee profile saved.", "success")
        except Exception:
          db.rollback()
          app.logger.exception("Could not update employee profile employee_id=%s", employee.id)
          flash("The employee profile could not be saved. Please try again.", "warning")
        return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#information")
      if action == "update_contract":
        if session.get("role") != "admin":
          abort(403)
        start_value = (request.form.get("profile_contract_start_date") or "").strip()
        end_value = (request.form.get("profile_contract_end_date") or "").strip()
        try:
          for date_value in (start_value, end_value):
            if date_value:
              datetime.strptime(date_value, "%Y-%m-%d")
          employee.profile_contract_start_date = start_value or None
          employee.profile_contract_end_date = end_value or None
          db.commit()
          flash("Contract dates saved.", "success")
        except ValueError:
          db.rollback()
          flash("Enter contract dates in the correct format.", "warning")
        except Exception:
          db.rollback()
          app.logger.exception("Could not update contract dates employee_id=%s", employee.id)
          flash("Contract dates could not be saved. Please try again.", "warning")
        return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#contract")
      if action == "delete_employee_document":
        document_id = request.form.get("document_id", type=int)
        document = db.get(EmployeeDocument, document_id) if document_id else None
        if not document or document.employee_id != employee.id:
          abort(404)
        try:
          path = os.path.join(EMPLOYEE_DOCUMENT_FOLDER, document.storage_name)
          if os.path.isfile(path):
            os.remove(path)
          db.delete(document)
          db.commit()
          flash("Employee document deleted.", "success")
        except Exception:
          db.rollback()
          app.logger.exception("Could not delete employee document %s", document_id)
          flash("The document could not be deleted. Please try again.", "warning")
        return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#documents")
      upload = request.files.get("employee_document")
      raw_filename = secure_filename(upload.filename or "") if upload else ""
      extension = raw_filename.rsplit(".", 1)[-1].lower() if "." in raw_filename else ""
      allowed_extensions = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}
      if not upload or not raw_filename:
        flash("Choose a document to upload.", "warning")
      elif extension not in allowed_extensions:
        flash("Upload a PDF, Word document, or image file.", "warning")
      else:
        storage_name = f"employee_{employee.id}_{secrets.token_hex(16)}.{extension}"
        storage_path = os.path.join(EMPLOYEE_DOCUMENT_FOLDER, storage_name)
        try:
          upload.save(storage_path)
          document = EmployeeDocument(
            employee_id=employee.id,
            original_filename=raw_filename[:255],
            storage_name=storage_name,
          )
          db.add(document)
          db.commit()
          flash("Employee document uploaded.", "success")
        except Exception:
          db.rollback()
          try:
            if os.path.isfile(storage_path):
              os.remove(storage_path)
          except OSError:
            app.logger.exception("Could not remove incomplete employee document upload")
          app.logger.exception("Could not save employee document for employee_id=%s", employee.id)
          flash("The document could not be uploaded. Please try again.", "warning")
      return redirect(url_for("admin_employee_detail", employee_id=employee.id) + "#documents")
    is_cleaner = _employee_has_staff_function(employee, "Cleaner")
    shifts = []
    shift_count = 0
    schedule_week_start = date.today() - timedelta(days=date.today().weekday())
    requested_week = (request.args.get("week") or "").strip()
    if requested_week:
      try:
        requested_date = datetime.strptime(requested_week, "%Y-%m-%d").date()
        schedule_week_start = requested_date - timedelta(days=requested_date.weekday())
      except ValueError:
        pass
    schedule_week_end = schedule_week_start + timedelta(days=6)
    schedule_days = []
    schedule_hour_rows = list(range(5, 24))
    week_start_label = schedule_week_start.strftime("%d.%m.%Y")
    week_end_label = schedule_week_end.strftime("%d.%m.%Y")
    schedule_week_range = f"{week_start_label} → {week_end_label}"
    previous_week_url = url_for("admin_employee_detail", employee_id=employee.id, week=(schedule_week_start - timedelta(days=7)).isoformat()) + "#schedule"
    next_week_url = url_for("admin_employee_detail", employee_id=employee.id, week=(schedule_week_start + timedelta(days=7)).isoformat()) + "#schedule"
    current_week_url = url_for("admin_employee_detail", employee_id=employee.id, week=(date.today() - timedelta(days=date.today().weekday())).isoformat()) + "#schedule"
    if is_cleaner:
      shifts = (
        db.query(Shift)
        .filter(
          Shift.employee_id == employee.id,
          Shift.day >= schedule_week_start,
          Shift.day <= schedule_week_end,
        )
        .order_by(Shift.day.asc(), Shift.start_time.asc())
        .all()
      )
      shift_count = db.query(func.count(Shift.id)).filter(Shift.employee_id == employee.id).scalar() or 0
      day_labels = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."] if _get_current_language() == "de" else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
      for day_offset in range(7):
        schedule_day = schedule_week_start + timedelta(days=day_offset)
        schedule_days.append({
          "date": schedule_day,
          "weekday": day_labels[day_offset],
          "day_label": schedule_day.strftime("%d.%m."),
          "is_today": schedule_day == date.today(),
          "events": [],
        })
      day_index = {item["date"]: index for index, item in enumerate(schedule_days)}
      for shift in shifts:
        shift_day_index = day_index.get(shift.day)
        if shift_day_index is None:
          continue
        start_minutes = shift.start_time.hour * 60 + shift.start_time.minute
        end_minutes = shift.end_time.hour * 60 + shift.end_time.minute
        all_day = start_minutes == 0 and (end_minutes == 0 or end_minutes >= (23 * 60 + 30))
        if end_minutes <= start_minutes:
          end_minutes += 24 * 60
        if all_day:
          top_px, height_px = 4, 34
        else:
          visible_start = max(start_minutes, 5 * 60)
          visible_end = min(end_minutes, 24 * 60)
          if visible_end <= visible_start:
            continue
          top_px = 42 + (visible_start - 5 * 60) * 52 / 60
          visible_minutes = visible_end - visible_start
          height_px = max(44, visible_minutes * 52 / 60 - 3)
        schedule_days[shift_day_index]["events"].append({
          "top_px": round(top_px),
          "height_px": round(height_px),
          "all_day": all_day,
          "time_window": f"{shift.start_time.strftime('%H:%M')}–{shift.end_time.strftime('%H:%M')}",
          "site_name": (shift.site.profile_company_name or shift.site.name) if shift.site else "Scheduled shift",
          "instructions": shift.instructions or "",
        })
    documents = db.query(EmployeeDocument).filter(
      EmployeeDocument.employee_id == employee.id
    ).order_by(EmployeeDocument.uploaded_at.desc(), EmployeeDocument.id.desc()).all() if not is_sales_manager else []
    credential_email_reason = None
    employee_login_status = employee.worker_status or ("active" if employee.is_active else "passive")
    if not employee.has_platform_access:
      credential_email_reason = "Enable platform access to send sign-in details."
    elif employee_login_status != "active":
      credential_email_reason = "Set the employee to Active to send sign-in details."
    elif not EMAIL_REGEX.fullmatch((employee.login_email or "").strip()):
      credential_email_reason = "Add a valid login email to send sign-in details."
    return render_template_string(
      EMPLOYEE_DETAIL_TEMPLATE,
      employee=employee,
      employee_staff_functions=_employee_staff_functions(employee),
      employee_staff_types=list(STAFF_FUNCTION_OPTIONS),
      shifts=shifts,
      shift_count=shift_count,
      is_cleaner=is_cleaner,
      schedule_days=schedule_days,
      schedule_hour_rows=schedule_hour_rows,
      schedule_week_range=schedule_week_range,
      schedule_week_start=schedule_week_start,
      previous_week_url=previous_week_url,
      next_week_url=next_week_url,
      current_week_url=current_week_url,
      documents=documents,
      credential_email_reason=credential_email_reason,
      active_page="employees",
      is_site_manager=is_site_manager,
      is_sales_manager=is_sales_manager,
      is_main_admin=session.get("role") == "admin",
    )
  finally:
    db.close()


@app.route("/admin/employees/<int:employee_id>/documents/<int:document_id>", methods=["GET"])
@site_or_sales_manager_required
def admin_employee_document_download(employee_id: int, document_id: int):
  if session.get("role") == "sales_manager":
    abort(403)
  db = SessionLocal()
  try:
    employee = db.get(Employee, employee_id)
    document = db.get(EmployeeDocument, document_id)
    if not employee or not document or document.employee_id != employee.id:
      abort(404)
    if session.get("role") != "admin" and employee.access_role != "employee":
      abort(403)
    path = os.path.join(EMPLOYEE_DOCUMENT_FOLDER, document.storage_name)
    if not os.path.isfile(path):
      abort(404)
    return send_file(path, as_attachment=True, download_name=document.original_filename)
  finally:
    db.close()


@app.route("/admin/employees/<int:employee_id>/document", methods=["GET"])
@login_required
def admin_employee_docx(employee_id: int):
  db = SessionLocal()
  try:
    app.logger.info("Employee DOCX download requested (employee_id=%s)", employee_id)
    try:
      employee = db.get(Employee, employee_id)
    except Exception:
      app.logger.exception("Could not load employee for DOCX download (employee_id=%s)", employee_id)
      raise
    if not employee:
      app.logger.warning("Employee DOCX download stopped: employee not found (employee_id=%s)", employee_id)
      flash("Employee not found.", "warning")
      return redirect(url_for("admin_employees"))

    debug_mode = (request.args.get("debug") or "").strip() in {"1", "true", "yes"}
    try:
      template_path = _resolve_employee_template_path()
    except Exception:
      app.logger.exception("Could not resolve employee DOCX template (employee_id=%s)", employee_id)
      raise
    if not template_path:
      candidates = [
        os.path.join(APP_ROOT, "uploads", "employee_template.docx"),
        os.path.join(APP_ROOT, "static", "uploads", "employee_template.docx"),
      ]
      app.logger.error(
        "Employee DOCX download stopped: template not found (employee_id=%s app_root=%s candidates=%s configured_path_set=%s)",
        employee_id,
        APP_ROOT,
        [(path, os.path.isfile(path), os.access(path, os.R_OK)) for path in candidates],
        bool((os.getenv("EMPLOYEE_TEMPLATE_PATH") or "").strip()),
      )
      flash("Employee template not found. Place employee_template.docx in uploads/ or static/uploads/.", "warning")
      return redirect(url_for("admin_employees"))

    if debug_mode:
      import json
      from importlib import metadata as importlib_metadata

      env_template = (os.getenv("EMPLOYEE_TEMPLATE_PATH") or "").strip()
      stat_info: dict[str, str | int | None] = {
        "resolved_template_path": template_path,
        "env_EMPLOYEE_TEMPLATE_PATH": env_template or None,
      }
      try:
        st = os.stat(template_path)
        stat_info.update(
          {
            "template_size_bytes": int(st.st_size),
            "template_mtime_utc": datetime.utcfromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S UTC"),
          }
        )
      except OSError as exc:
        stat_info["template_stat_error"] = str(exc)

      try:
        docx_version = importlib_metadata.version("python-docx")
      except Exception:
        docx_version = None

      # Inspect the template content as python-docx sees it (helps diagnose textboxes vs paragraphs)
      template_probe: dict[str, str | int | None] = {
        "python_docx_version": docx_version,
        "employee_id": employee.id,
      }

      template_probe["docx_available"] = PYTHON_DOCX_AVAILABLE
      template_probe["docx_import_error"] = PYTHON_DOCX_IMPORT_ERROR
      if PYTHON_DOCX_AVAILABLE and Document is not None:
        try:
          probe_doc = Document(template_path)
          hit = None
          for p in probe_doc.paragraphs:
            if "arbeitnehmer" in (p.text or "").lower():
              hit = p.text
              break
          template_probe["template_first_arbeitnehmer_paragraph"] = hit
          template_probe["template_paragraph_count"] = len(probe_doc.paragraphs)
          template_probe["template_table_count"] = len(probe_doc.tables)
        except Exception as exc:
          template_probe["template_probe_error"] = str(exc)

      payload = {"template": stat_info, "probe": template_probe}
      return app.response_class(
        response=json.dumps(payload, ensure_ascii=False, indent=2),
        status=200,
        mimetype="application/json",
      )

    if not PYTHON_DOCX_AVAILABLE:
      app.logger.error(
        "Employee DOCX download stopped: python-docx unavailable in web process (employee_id=%s template=%s import_error=%s)",
        employee_id,
        template_path,
        PYTHON_DOCX_IMPORT_ERROR,
      )
      flash("DOCX generation is unavailable. Check the application log for the python-docx import error.", "warning")
      return redirect(url_for("admin_employees"))

    try:
      docx_buffer = _build_employee_docx(employee, template_path)
    except ValueError as exc:
      app.logger.exception(
        "Employee DOCX generation stopped with a value error (employee_id=%s template=%s)",
        employee_id,
      )
      flash(str(exc), "warning")
      return redirect(url_for("admin_employees"))
    except Exception:
      app.logger.exception(
        "Employee DOCX generation failed (employee_id=%s template=%s)",
        employee_id,
        template_path,
      )
      raise

    app.logger.info(
      "Generated employee DOCX (employee_id=%s template=%s bytes=%s)",
      employee.id,
      template_path,
      docx_buffer.getbuffer().nbytes,
    )
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", (employee.name or f"employee_{employee.id}").strip())
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return send_file(
      docx_buffer,
      mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      as_attachment=True,
      download_name=f"employee_{safe_name}_{timestamp}.docx",
    )
  finally:
    db.close()


@app.route("/admin/sites", methods=["GET", "POST"])
@site_or_sales_manager_required
def admin_sites():
  db = SessionLocal()
  is_main_admin = session.get("role") == "admin"
  is_site_manager = session.get("role") == "site_manager"
  is_sales_manager = session.get("role") == "sales_manager"
  current_manager_id = session.get("employee_id") if is_site_manager else None
  try:
    search_q = (request.args.get("q") or "").strip()
    status_filter = (request.args.get("status_filter") or "all").strip().lower()
    manager_filter = (request.args.get("manager_id") or "").strip()
    client_filter = (request.args.get("client") or "").strip()
    coverage_filter = (request.args.get("coverage") or "").strip().lower()
    if coverage_filter not in {"scheduled", "unscheduled"}:
      coverage_filter = ""
    if status_filter not in {"all", "active", "inactive"}:
      status_filter = "all"
    if request.method == "POST":
      entity = (request.form.get("entity") or "site").strip()
      action = (request.form.get("action") or "").strip().lower()
      profile_action = (request.form.get("profile_action") or "save").strip().lower()
      contract_site = None
      redirect_q = (request.form.get("redirect_q") or "").strip()
      redirect_page_raw = (request.form.get("redirect_page") or "").strip()
      redirect_status = (request.form.get("redirect_status") or "all").strip().lower()
      redirect_page_val = None
      if redirect_page_raw.isdigit():
        redirect_page_val = max(int(redirect_page_raw), 1)
      redirect_params: dict[str, int | str] = {}
      effective_q = redirect_q or search_q
      if effective_q:
        redirect_params["q"] = effective_q
      effective_manager = (request.form.get("redirect_manager") or manager_filter).strip()
      effective_client = (request.form.get("redirect_client") or client_filter).strip()
      effective_coverage = (request.form.get("redirect_coverage") or coverage_filter).strip().lower()
      if effective_manager:
        redirect_params["manager_id"] = effective_manager
      if effective_client:
        redirect_params["client"] = effective_client
      if effective_coverage in {"scheduled", "unscheduled"}:
        redirect_params["coverage"] = effective_coverage
      if redirect_status in {"active", "inactive"}:
        redirect_params["status_filter"] = redirect_status
      if redirect_page_val and redirect_page_val > 1:
        redirect_params["page"] = redirect_page_val
      redirect_url = url_for("admin_sites", **redirect_params)
      if entity == "site":
        site_id = request.form.get("id")
        if action == "set_status" and site_id:
          site = db.get(Site, int(site_id))
          if site:
            site.is_active = (request.form.get("is_active") or "1") != "0"
            db.commit()
            flash("Site status updated.", "success")
        elif action == "create":
          company_name = (request.form.get("profile_company_name") or "").strip()
          name = (request.form.get("name") or "").strip() or company_name
          address = (request.form.get("address") or "").strip() or None
          contact_name = (request.form.get("profile_contact_name") or "").strip() or None
          contact_email = (request.form.get("profile_contact_email") or "").strip() or None
          default_rate = request.form.get("profile_default_hourly_rate", type=float) if is_main_admin else None
          is_active = (request.form.get("is_active", "1") or "1").strip() != "0"
          if not name:
            flash("Client name is required.", "warning")
          else:
            if _site_exists(db, name, address or ""):
              flash("A client with the same name and service address already exists.", "warning")
            else:
              site = Site(
                name=name, address=address, hourly_rate=default_rate or 50.0,
                is_active=is_active, profile_company_name=company_name or name,
                profile_contact_name=contact_name, profile_contact_email=contact_email,
                contact_name=contact_name, contact_email=contact_email,
                profile_phone=(request.form.get("profile_phone") or "").strip() or None,
                profile_billing_address=(request.form.get("profile_billing_address") or "").strip() or None if is_main_admin else None,
                profile_vat_id=(request.form.get("profile_vat_id") or "").strip() or None if is_main_admin else None,
                profile_default_hourly_rate=default_rate,
                profile_notes=(request.form.get("profile_notes") or "").strip() or None,
                contract_partner_name=(request.form.get("contract_partner_name") or "").strip() or None if is_main_admin else None,
                contract_contact_details=(request.form.get("contract_contact_details") or "").strip() or None if is_main_admin else None,
                manager_employee_id=current_manager_id,
              )
              submitted_customer_id = (request.form.get("profile_tax_id") or "").strip() if is_main_admin else ""
              site.profile_tax_id = submitted_customer_id or None
              if is_main_admin:
                manager_id = request.form.get("manager_employee_id", type=int)
                manager = db.get(Employee, manager_id) if manager_id else None
                site.manager_employee_id = manager.id if manager and manager.access_role == "site_manager" else None
              for field_name in (("contract_start_date", "contract_end_date") if is_main_admin else ()):
                raw_date = (request.form.get(field_name) or "").strip()
                if raw_date:
                  try:
                    setattr(site, field_name, datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d-%m-%Y"))
                  except ValueError:
                    flash("Enter contract dates in a valid format.", "warning")
                    return redirect(redirect_url)
              image_file = request.files.get("site_profile_image")
              image_path = _save_profile_image(image_file, "site_new")
              if image_file and getattr(image_file, "filename", "") and not image_path:
                flash("Invalid client image. Use PNG, JPG, GIF, WEBP, or HEIC.", "warning")
                return redirect(redirect_url)
              site.profile_image_path = image_path
              db.add(site)
              db.flush()
              _ensure_site_customer_id(db, site)
              db.commit()
              flash("Client added.", "success")
              if profile_action == "generate_contract" and is_main_admin:
                contract_site = site
        elif action == "update" and site_id:
          site = db.get(Site, int(site_id))
          if site:
            company_name = (request.form.get("profile_company_name") or "").strip() or site.profile_company_name or site.name
            name = (request.form.get("name") or "").strip() or company_name
            address = (request.form.get("address") or "").strip() or None
            default_rate = request.form.get("profile_default_hourly_rate", type=float) if is_main_admin else None
            is_active = (request.form.get("is_active", "1") or "1").strip() != "0"
            if _site_exists(db, name, address or "", exclude_id=site.id):
              flash("Another client already uses that name and service address.", "warning")
            else:
              site.name = name
              site.address = address
              site.profile_company_name = company_name
              site.is_active = is_active
              if default_rate is not None:
                site.profile_default_hourly_rate = default_rate
                site.hourly_rate = default_rate
              site.profile_contact_name = (request.form.get("profile_contact_name") or "").strip() or None
              site.profile_contact_email = (request.form.get("profile_contact_email") or "").strip() or None
              site.contact_name = site.profile_contact_name
              site.contact_email = site.profile_contact_email
              site.profile_phone = (request.form.get("profile_phone") or "").strip() or None
              if is_main_admin:
                site.profile_billing_address = (request.form.get("profile_billing_address") or "").strip() or None
                site.profile_vat_id = (request.form.get("profile_vat_id") or "").strip() or None
                submitted_customer_id = (request.form.get("profile_tax_id") or "").strip()
                site.profile_tax_id = submitted_customer_id or site.profile_tax_id
                _ensure_site_customer_id(db, site)
              site.profile_notes = (request.form.get("profile_notes") or "").strip() or None
              if is_main_admin:
                site.contract_partner_name = (request.form.get("contract_partner_name") or "").strip() or None
                site.contract_contact_details = (request.form.get("contract_contact_details") or "").strip() or None
              for field_name in (("contract_start_date", "contract_end_date") if is_main_admin else ()):
                raw_date = (request.form.get(field_name) or "").strip()
                if raw_date:
                  try:
                    setattr(site, field_name, datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d-%m-%Y"))
                  except ValueError:
                    flash("Enter contract dates in a valid format.", "warning")
                    return redirect(redirect_url)
                else:
                  setattr(site, field_name, None)
              image_file = request.files.get("site_profile_image")
              image_path = _save_profile_image(image_file, f"site_{site.id}", replace_path=site.profile_image_path)
              if image_file and getattr(image_file, "filename", "") and not image_path:
                flash("Invalid client image. Use PNG, JPG, GIF, WEBP, or HEIC.", "warning")
                return redirect(redirect_url)
              if image_path:
                site.profile_image_path = image_path
              if is_main_admin:
                manager_id = request.form.get("manager_employee_id", type=int)
                manager = db.get(Employee, manager_id) if manager_id else None
                site.manager_employee_id = manager.id if manager and manager.access_role == "site_manager" else None
              db.commit()
              flash("Client updated.", "success")
              if profile_action == "generate_contract" and is_main_admin:
                contract_site = site
        elif action == "delete" and site_id:
          site = db.get(Site, int(site_id))
          if site:
            linked_invoice = db.query(Invoice.id).filter(Invoice.site_id == site.id).first()
            if linked_invoice:
              flash("This site has invoices and cannot be deleted. Set it to inactive instead.", "warning")
              return redirect(url_for("admin_site_detail", site_id=site.id))

            inspection_rows = db.query(SiteInspection).filter(SiteInspection.site_id == site.id).all()
            inspection_photo_paths = [
              item.photo_path
              for inspection in inspection_rows
              for item in inspection.items
              if item.photo_path
            ]
            site_area_rows = db.query(SiteInspectionArea).filter(SiteInspectionArea.site_id == site.id).all()
            site_image_path = site.profile_image_path
            for inspection in inspection_rows:
              db.delete(inspection)
            for site_area in site_area_rows:
              db.delete(site_area)
            db.delete(site)
            db.commit()
            for photo_path in inspection_photo_paths:
              photo_name = os.path.basename(str(photo_path).replace("\\", "/"))
              photo_file = os.path.join(INSPECTION_PHOTO_FOLDER, photo_name)
              try:
                if os.path.isfile(photo_file):
                  os.remove(photo_file)
              except OSError:
                app.logger.warning("Could not remove inspection photo while deleting site %s: %s", site_id, photo_file)
            _remove_photo(site_image_path)
            flash("Site deleted. Its shifts and inspection reports were also deleted.", "success")
            return redirect(redirect_url)
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
            if parsed_rate is not None and is_main_admin:
              site.hourly_rate = parsed_rate
            site.is_active = (active_flag or "1").strip() != "0"
        db.commit()

      if contract_site is not None and is_main_admin:
        partner_name = (contract_site.contract_partner_name or "").strip()
        company_name = (contract_site.profile_company_name or contract_site.name or "").strip()
        contact_details = (contract_site.contract_contact_details or "").strip()
        if not partner_name or not company_name or not contact_details:
          flash("Fill in the contract partner, company, and phone, fax, or email before generating the contract.", "warning")
          return redirect(url_for("admin_sites", edit_client=contract_site.id, **redirect_params))
        pdf_buffer = generate_contract_pdf(partner_name, company_name, contact_details)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return send_file(
          pdf_buffer,
          mimetype="application/pdf",
          as_attachment=True,
          download_name=f"client_contract_{contract_site.id}_{timestamp}.pdf",
        )
      return redirect(redirect_url)

    query = db.query(Site)
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=7)
    if search_q:
      like = f"%{search_q}%"
      query = query.filter(or_(
        Site.name.ilike(like), Site.address.ilike(like),
        Site.profile_company_name.ilike(like), Site.profile_contact_name.ilike(like),
        Site.profile_contact_email.ilike(like), Site.profile_phone.ilike(like),
        Site.profile_billing_address.ilike(like), Site.profile_vat_id.ilike(like),
        Site.profile_tax_id.ilike(like), Site.contact_name.ilike(like), Site.contact_email.ilike(like),
      ))
    if manager_filter == "unassigned":
      query = query.filter(Site.manager_employee_id.is_(None))
    elif manager_filter.isdigit():
      query = query.filter(Site.manager_employee_id == int(manager_filter))
    client_name_expr = func.coalesce(func.nullif(func.trim(Site.profile_company_name), ""), Site.name)
    if client_filter:
      query = query.filter(client_name_expr == client_filter)
    if coverage_filter == "scheduled":
      scheduled_site_ids = db.query(Shift.site_id).filter(
        Shift.day >= week_start, Shift.day < week_end, Shift.site_id.is_not(None)
      ).distinct()
      query = query.filter(Site.id.in_(scheduled_site_ids))
    elif coverage_filter == "unscheduled":
      scheduled_site_ids = db.query(Shift.site_id).filter(
        Shift.day >= week_start, Shift.day < week_end, Shift.site_id.is_not(None)
      ).distinct()
      query = query.filter(~Site.id.in_(scheduled_site_ids))
    if status_filter == "active":
      query = query.filter(or_(Site.is_active.is_(True), Site.is_active.is_(None)))
    elif status_filter == "inactive":
      query = query.filter(Site.is_active.is_(False))

    # Preserve the legacy profiles page behavior: make customer IDs available
    # for existing client records as they are moved into the database UI.
    missing_customer_ids = db.query(Site).filter(
      or_(Site.profile_tax_id.is_(None), func.trim(Site.profile_tax_id) == "")
    ).all()
    if missing_customer_ids:
      for site_without_id in missing_customer_ids:
        _ensure_site_customer_id(db, site_without_id)
      db.commit()

    filtered_sites = query.count()

    per_page = 25
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
    edit_client_id = request.args.get("edit_client", type=int)
    edit_client = db.get(Site, edit_client_id) if edit_client_id else None
    client_to_edit_data = None
    if edit_client:
      client_to_edit_data = {
        "id": edit_client.id, "name": edit_client.name, "address": edit_client.address or "",
        "rate": edit_client.hourly_rate or 0 if is_main_admin else "", "defaultRate": edit_client.profile_default_hourly_rate or "" if is_main_admin else "",
        "active": "1" if edit_client.is_active != 0 else "0", "company": edit_client.profile_company_name or "",
        "contact": edit_client.profile_contact_name or edit_client.contact_name or "",
        "email": edit_client.profile_contact_email or edit_client.contact_email or "",
        "phone": edit_client.profile_phone or "", "billing": edit_client.profile_billing_address or "" if is_main_admin else "",
        "vat": edit_client.profile_vat_id or "" if is_main_admin else "", "customerId": edit_client.profile_tax_id or "" if is_main_admin else "",
        "notes": edit_client.profile_notes or "", "contractStart": edit_client.contract_start_date or "" if is_main_admin else "",
        "contractEnd": edit_client.contract_end_date or "" if is_main_admin else "", "contractPartner": edit_client.contract_partner_name or "" if is_main_admin else "",
        "contractContact": edit_client.contract_contact_details or "" if is_main_admin else "", "managerId": edit_client.manager_employee_id or "" if is_main_admin else "", "logo": edit_client.profile_image_path or "",
      }
    site_managers = db.query(Employee).filter(Employee.access_role == "site_manager", Employee.is_active.is_(True)).order_by(Employee.name.asc()).all()
    site_manager_filter_options = db.query(Employee).filter(Employee.access_role == "site_manager").order_by(Employee.name.asc()).all()
    client_filter_options = [
      row[0] for row in db.query(client_name_expr)
      .filter(func.trim(client_name_expr) != "")
      .distinct().order_by(client_name_expr.asc()).all()
    ]
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
      status_filter=status_filter,
      manager_filter=manager_filter,
      client_filter=client_filter,
      coverage_filter=coverage_filter,
      is_main_admin=is_main_admin,
      is_site_manager=is_site_manager or is_sales_manager,
      is_sales_manager=is_sales_manager,
      site_managers=site_managers,
      site_manager_filter_options=site_manager_filter_options,
      client_filter_options=client_filter_options,
      shift_counts=shift_counts,
      total_sites=total_sites,
      active_sites_total=active_sites_total,
      client_to_edit_data=client_to_edit_data,
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


@app.route("/admin/sites/<int:site_id>", methods=["GET", "POST"])
@site_or_sales_manager_required
def admin_site_detail(site_id: int):
  db = SessionLocal()
  is_site_manager = session.get("role") == "site_manager"
  is_sales_manager = session.get("role") == "sales_manager"
  is_main_admin = session.get("role") == "admin"
  try:
    site = db.get(Site, site_id)
    if not site:
      flash("Client not found.", "warning")
      return redirect(url_for("admin_sites"))
    if request.method == "POST":
      if (request.form.get("action") or "") != "update_site_profile":
        abort(400)
      company_name = (request.form.get("profile_company_name") or "").strip()
      site_name = (request.form.get("name") or "").strip() or company_name
      address = (request.form.get("address") or "").strip() or None
      if not company_name or not site_name:
        flash("Company and service location names are required.", "warning")
        return redirect(url_for("admin_site_detail", site_id=site.id) + "#general")
      if _site_exists(db, site_name, address or "", exclude_id=site.id):
        flash("Another site already uses that name and service address.", "warning")
        return redirect(url_for("admin_site_detail", site_id=site.id) + "#general")
      site.profile_company_name = company_name
      site.name = site_name
      site.address = address
      site.is_active = (request.form.get("is_active") or "1") != "0"
      site.profile_contact_name = (request.form.get("profile_contact_name") or "").strip() or None
      site.profile_contact_email = (request.form.get("profile_contact_email") or "").strip() or None
      site.contact_name = site.profile_contact_name
      site.contact_email = site.profile_contact_email
      site.profile_phone = (request.form.get("profile_phone") or "").strip() or None
      site.profile_notes = (request.form.get("profile_notes") or "").strip() or None
      if is_main_admin:
        rate = request.form.get("profile_default_hourly_rate", type=float)
        if rate is not None:
          site.profile_default_hourly_rate = rate
          site.hourly_rate = rate
        site.profile_billing_address = (request.form.get("profile_billing_address") or "").strip() or None
        site.profile_vat_id = (request.form.get("profile_vat_id") or "").strip() or None
        site.profile_tax_id = (request.form.get("profile_tax_id") or "").strip() or site.profile_tax_id
        site.contract_partner_name = (request.form.get("contract_partner_name") or "").strip() or None
        site.contract_contact_details = (request.form.get("contract_contact_details") or "").strip() or None
        date_error = False
        for field_name in ("contract_start_date", "contract_end_date"):
          raw_value = (request.form.get(field_name) or "").strip()
          if not raw_value:
            setattr(site, field_name, None)
          else:
            try:
              setattr(site, field_name, datetime.strptime(raw_value, "%Y-%m-%d").strftime("%d-%m-%Y"))
            except ValueError:
              date_error = True
        if date_error:
          db.rollback()
          flash("Enter contract dates in a valid format.", "warning")
          return redirect(url_for("admin_site_detail", site_id=site.id) + "#contract")
        manager_id = request.form.get("manager_employee_id", type=int)
        manager = db.get(Employee, manager_id) if manager_id else None
        site.manager_employee_id = manager.id if manager and manager.access_role == "site_manager" else None
      image_file = request.files.get("site_profile_image")
      image_path = _save_profile_image(image_file, f"site_{site.id}", replace_path=site.profile_image_path)
      if image_file and image_file.filename and not image_path:
        db.rollback()
        flash("Invalid site image. Use PNG, JPG, GIF, WEBP, or HEIC.", "warning")
        return redirect(url_for("admin_site_detail", site_id=site.id) + "#general")
      if image_path:
        site.profile_image_path = image_path
      site_saved = False
      try:
        db.commit()
        _ensure_site_customer_id(db, site)
        db.commit()
        site_saved = True
        flash("Site profile saved.", "success")
      except Exception:
        db.rollback()
        app.logger.exception("Could not update site profile site_id=%s", site.id)
        flash("The site profile could not be saved. Please try again.", "warning")
      if site_saved and (request.form.get("profile_action") or "") == "generate_contract" and is_main_admin:
        partner_name = (site.contract_partner_name or "").strip()
        company_name = (site.profile_company_name or site.name or "").strip()
        contact_details = (site.contract_contact_details or "").strip()
        if not partner_name or not company_name or not contact_details:
          flash("Fill in the contract partner, company, and contact details before generating the contract.", "warning")
          return redirect(url_for("admin_site_detail", site_id=site.id) + "#contract")
        pdf_buffer = generate_contract_pdf(partner_name, company_name, contact_details)
        return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True, download_name=f"client_contract_{site.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf")
      return redirect(url_for("admin_site_detail", site_id=site.id) + "#information")
    shifts = (
      db.query(Shift)
      .filter(Shift.site_id == site.id)
      .order_by(Shift.day.desc(), Shift.start_time.desc())
      .limit(20)
      .all()
    )
    invoices = (
      db.query(Invoice)
      .filter(Invoice.site_id == site.id)
      .order_by(Invoice.issued_date.desc(), Invoice.id.desc())
      .limit(20)
      .all()
    ) if not is_site_manager and not is_sales_manager else []
    shift_count = db.query(func.count(Shift.id)).filter(Shift.site_id == site.id).scalar() or 0
    def site_contract_date_input(raw_value: str | None) -> str:
      if not raw_value:
        return ""
      for date_format in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
          return datetime.strptime(raw_value, date_format).strftime("%Y-%m-%d")
        except ValueError:
          continue
      return ""
    return render_template_string(
      CLIENT_DETAIL_TEMPLATE,
      active_page="sites",
      site=site,
      shifts=shifts,
      invoices=invoices,
      shift_count=shift_count,
      is_site_manager=is_site_manager or is_sales_manager,
      is_main_admin=session.get("role") == "admin",
      is_sales_manager=is_sales_manager,
      site_managers=db.query(Employee).filter(Employee.access_role == "site_manager", Employee.is_active.is_(True)).order_by(Employee.name.asc()).all(),
      contract_start_input=site_contract_date_input(site.contract_start_date),
      contract_end_input=site_contract_date_input(site.contract_end_date),
    )
  finally:
    db.close()


@app.route("/admin/profiles", methods=["GET", "POST"])
@login_required
def admin_profiles():
  """Redirect legacy profile URLs to the current employee/client databases."""
  tab = (request.args.get("tab") or request.form.get("tab") or "employees").strip().lower()
  if tab == "clients":
    params = {
      "q": (request.args.get("client_search") or request.form.get("client_search") or "").strip(),
      "page": request.args.get("clients_page", type=int) or request.form.get("clients_page", type=int),
    }
    vat = (request.args.get("client_vat") or request.form.get("client_vat") or "").strip()
    if vat:
      params["q"] = " ".join(part for part in (params["q"], vat) if part)
    return redirect(url_for("admin_sites", **{key: value for key, value in params.items() if value}))

  params = {
    "q": (request.args.get("emp_search") or request.form.get("emp_search") or "").strip(),
    "page": request.args.get("employees_page", type=int) or request.form.get("employees_page", type=int),
    "work_type": (request.args.get("emp_work_type") or request.form.get("emp_work_type") or "").strip(),
    "role": (request.args.get("emp_role") or request.form.get("emp_role") or "").strip(),
  }
  return redirect(url_for("admin_employees", **{key: value for key, value in params.items() if value}))
@app.route("/leads", methods=["GET", "POST"])
@site_or_sales_manager_required
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
@site_or_sales_manager_required
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
@site_manager_required
def schedule_pdf():
    if not REPORTLAB_AVAILABLE:
        return jsonify({"error": "reportlab not installed"}), 503

    week_param = request.args.get("week")
    employee_id = request.args.get("employee_id", type=int)
    weeks = request.args.get("weeks", default=1, type=int) or 1
    weeks = max(1, min(weeks, 12))
    period = request.args.get("period", "week")
    ref_date = None
    if week_param:
        try:
            ref_date = datetime.strptime(week_param, "%Y-%m-%d").date()
        except ValueError:
            ref_date = None
    ref_date = ref_date or date.today()
    if period == "month":
        month_start = ref_date.replace(day=1)
        next_month_start = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        week_days = _get_day_range(month_start, days=(next_month_start - month_start).days)
    elif period == "custom":
        end_date_str = request.args.get("end_date", "")
        try:
            range_end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            range_end = ref_date
        if range_end < ref_date:
            ref_date, range_end = range_end, ref_date
        range_length = max(1, min((range_end - ref_date).days + 1, 84))
        week_days = _get_day_range(ref_date, days=range_length)
    elif period == "day":
        week_days = [ref_date]
    elif period == "fortnight":
        week_days = _get_day_range(ref_date, weeks=2)
    else:
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
@sales_manager_or_admin_required
def index():
    if request.method == "GET":
        return render_template_string(
            HTML_TEMPLATE,
            gpt_enabled=bool(openai_client),
            active_page="crawler",
            is_sales_manager=session.get("role") == "sales_manager",
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
    cleaned_data = clean_contacts(data)

    pdf_buffer = _generate_contacts_pdf(cleaned_data)
    filename = f"putzelf_contacts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@app.route("/gpt", methods=["POST"])
@sales_manager_or_admin_required
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


def _generate_invoice_number(session_obj, reserved: set[str] | None = None) -> str:
  """Generate continuous invoice numbers: RE-1000, RE-1001, ...

  NOTE: When creating multiple invoices in one DB transaction, pass a mutable
  `reserved` set so invoice numbers remain unique even before commit.
  """
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
  while (
    (reserved is not None and candidate in reserved)
    or session_obj.query(Invoice.id).filter(Invoice.invoice_number == candidate).first()
  ):
    next_number += 1
    candidate = f"RE-{next_number}"

  if reserved is not None:
    reserved.add(candidate)

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


def _generate_customer_id(session_obj, reserved: set[str] | None = None) -> str:
  """Generate continuous customer IDs: UT- 0001, UT- 0002, ...

  NOTE: When creating multiple IDs in one DB transaction, pass a mutable
  `reserved` set to avoid duplicates before commit.
  """
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
    (reserved is not None and candidate in reserved)
    or
    session_obj.query(Site.id).filter(Site.profile_tax_id == candidate).first()
    or session_obj.query(Invoice.id).filter(Invoice.site_tax_id == candidate).first()
  ):
    next_sequence += 1
    candidate = _format_customer_id(next_sequence)

  if reserved is not None:
    reserved.add(candidate)

  return candidate


def _ensure_site_customer_id(session_obj, site: Site | None, reserved: set[str] | None = None) -> str:
  """Return a site's customer ID, creating one when missing."""
  if not site:
    return ""
  current_value = (site.profile_tax_id or "").strip()
  if current_value:
    return current_value
  generated = _generate_customer_id(session_obj, reserved=reserved)
  site.profile_tax_id = generated
  return generated


def _month_range_by_offset(reference_day: date | None = None, months_back: int = 1) -> tuple[date, date]:
  """Return first/last day of the month that is months_back before the reference month."""
  ref = reference_day or date.today()
  first_of_current = date(ref.year, ref.month, 1)
  source_month_first = _add_months(first_of_current, -months_back)
  if source_month_first.month == 12:
    next_month = date(source_month_first.year + 1, 1, 1)
  else:
    next_month = date(source_month_first.year, source_month_first.month + 1, 1)
  return source_month_first, next_month - timedelta(days=1)


def _week_range_by_offset(reference_day: date | None = None, weeks_back: int = 0) -> tuple[date, date]:
  """Return Monday..Sunday range for the week that is `weeks_back` before the reference week.

  weeks_back=0 -> current week, 1 -> previous week, etc.
  """
  ref = reference_day or date.today()
  # find Monday of current week
  monday = ref - timedelta(days=ref.weekday())
  source_monday = monday - timedelta(weeks=weeks_back)
  return source_monday, source_monday + timedelta(days=6)


def _previous_month_range(reference_day: date | None = None) -> tuple[date, date]:
  return _month_range_by_offset(reference_day, 1)


def _parse_optional_contract_date(value: str | None) -> date | None:
  raw = (value or "").strip()
  if not raw:
    return None
  for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y"):
    try:
      return datetime.strptime(raw, fmt).date()
    except ValueError:
      continue
  return None


def _is_employee_active(emp, reference_date: date | None = None) -> bool:
  if emp is None:
    return False
  if reference_date is None:
    reference_date = date.today()

  start_date = _parse_optional_contract_date(emp.profile_contract_start_date)
  end_date = _parse_optional_contract_date(emp.profile_contract_end_date)
  if start_date and start_date > reference_date:
    return False
  if end_date and end_date < reference_date:
    return False
  return True


def _add_months(original_date: date, months: int) -> date:
  year = original_date.year + (original_date.month - 1 + months) // 12
  month = ((original_date.month - 1 + months) % 12) + 1
  day = original_date.day
  try:
    return date(year, month, day)
  except ValueError:
    if month == 12:
      next_month = date(year + 1, 1, 1)
    else:
      next_month = date(year, month + 1, 1)
    return next_month - timedelta(days=1)


def _add_weeks(original_date: date, weeks: int) -> date:
  try:
    return original_date + timedelta(weeks=weeks)
  except Exception:
    return original_date


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

  reserved_invoice_numbers: set[str] = set()
  reserved_customer_ids: set[str] = set()

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
      invoice_number=_generate_invoice_number(session_obj, reserved=reserved_invoice_numbers),
      site_id=site.id,
      site_company_name=((site.profile_company_name or "").strip() or (site.name or "").strip()),
      site_contact_name=((site.profile_contact_name or "").strip() or (site.contact_name or "").strip()),
      site_contact_email=((site.profile_contact_email or "").strip() or (site.contact_email or "").strip()),
      site_phone=(site.profile_phone or "").strip(),
      site_billing_address=((site.profile_billing_address or "").strip() or (site.address or "").strip()),
      site_tax_id=_ensure_site_customer_id(session_obj, site, reserved=reserved_customer_ids),
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

    # Recipient block (company above contact name, plus address with country)
    recipient_company_line = (
      ((invoice.site.profile_company_name or "").strip() if invoice.site else "")
      or (invoice.site_company_name or "").strip()
      or (invoice.site.name.strip() if invoice.site and invoice.site.name else "")
      or ""
    )
    recipient_contact_line = (
      ((invoice.site.profile_contact_name or "").strip() if invoice.site else "")
      or (invoice.site_contact_name or "").strip()
      or ""
    )

    recipient_name_lines: list[str] = []
    if recipient_company_line:
      recipient_name_lines.append(recipient_company_line)
    if recipient_contact_line and recipient_contact_line != recipient_company_line:
      recipient_name_lines.append(recipient_contact_line)
    if not recipient_name_lines:
      recipient_name_lines = ["-"]

    recipient_address_raw = (
      (invoice.site_billing_address or "").strip()
      or (invoice.site.address.strip() if invoice.site and invoice.site.address else "")
    )
    recipient_address_lines: list[str] = []
    if recipient_address_raw:
      if "\n" in recipient_address_raw:
        recipient_address_lines = [line.strip() for line in recipient_address_raw.splitlines() if line.strip()]
      else:
        recipient_address_lines = [part.strip() for part in recipient_address_raw.split(",") if part.strip()]

    # Ensure "Österreich" is shown as the last line (exactly once) under the address.
    if recipient_address_lines:
      recipient_address_lines = [
        line for line in recipient_address_lines
        if line.strip().lower().strip(".") != "österreich"
      ]
      recipient_address_lines.append("Österreich")

    recipient_extra_lines: list[str] = []

    # Logo path (drawn on canvas to avoid layout shifts)
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'stafflogo.png')
    logo_flowable = None
    if os.path.exists(logo_path):
      logo_flowable = Image(logo_path, width=1.6 * inch, height=0.4 * inch)
      logo_flowable.hAlign = "LEFT"

    vat_id = ((invoice.site.profile_vat_id or "").strip() if invoice.site else "")
    contract_start = ((invoice.site.contract_start_date or "").strip() if invoice.site else "")
    contract_end = ((invoice.site.contract_end_date or "").strip() if invoice.site else "")

    leistungszeitraum_value = delivery_date
    if contract_start and contract_end:
      leistungszeitraum_value = f"{contract_start} – {contract_end}"
    elif contract_start:
      leistungszeitraum_value = contract_start
    elif contract_end:
      leistungszeitraum_value = contract_end

    # Create header table with sender and invoice info
    right_details_data = [
      [Paragraph('Rechnungs-Nr.', invoice_header_label_style), Paragraph(_format_invoice_number(invoice.invoice_number), invoice_header_value_style)],
      [Paragraph('Rechnungsdatum', invoice_header_label_style), Paragraph(invoice_date, invoice_header_value_style)],
      [Paragraph('Leistungszeitraum', invoice_header_label_style), Paragraph(leistungszeitraum_value, invoice_header_value_style)],
      [Paragraph('Ihre Kundennummer', invoice_header_label_style), Paragraph(customer_number, invoice_header_value_style)],
    ]
    if vat_id:
      right_details_data.append([Paragraph('Ihre USt-ID', invoice_header_label_style), Paragraph(vat_id, invoice_header_value_style)])
    right_details_data.append([Paragraph('Ihr Ansprechpartner', invoice_header_label_style), Paragraph('Sebastijan Kerculj', invoice_header_value_style)])
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
        Paragraph(f'<font size=10>{"<br/>".join(recipient_name_lines)}</font>', address_style),
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
            f'{unit_price:.2f} €',
            f'{original_total:.2f} €'
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
      ['', '', '', 'Gesamtbetrag netto', f'{net_total:.2f} €'],
      ['', '', '', f'zzgl. Umsatzsteuer {tax_rate_percent:.0f}%', f'{tax_amount:.2f} €'],
      ['', '', '', 'Gesamtbetrag brutto', f'{gross_total:.2f} €']
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
- Hourly Rate: €{invoice.hourly_rate:.2f}
- Total Amount: €{invoice.total_amount:.2f}
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


def send_employee_credentials_email(employee: Employee, pin: str) -> Tuple[bool, str]:
  """Email employee sign-in details using the app's configured SMTP account."""
  import smtplib
  from email.message import EmailMessage

  smtp_server = (os.getenv("SMTP_SERVER") or os.getenv("SMTP_HOST") or "smtp.gmail.com").strip()
  try:
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
  except ValueError:
    return False, "Email server configuration is invalid."
  sender_email = (os.getenv("EMPLOYEE_CREDENTIALS_FROM_EMAIL") or "office@putzelf.com").strip()
  sender_name = (os.getenv("EMPLOYEE_CREDENTIALS_FROM_NAME") or os.getenv("SMTP_FROM_NAME") or "Elf's Plan").strip()
  smtp_username = (os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or os.getenv("SENDER_EMAIL") or sender_email).strip()
  smtp_password = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS") or os.getenv("SENDER_PASSWORD") or "").strip()
  recipient = (employee.login_email or "").strip()
  if not sender_email or not smtp_password:
    return False, "Email is not configured. Set SMTP_USERNAME and SMTP_PASSWORD for office@putzelf.com first."
  if not recipient or not EMAIL_REGEX.fullmatch(recipient):
    return False, "Enter a valid employee email address first."

  tls_setting = (os.getenv("SMTP_SECURE") or "").strip().lower()
  if tls_setting:
    use_ssl = tls_setting in {"1", "true", "yes", "on"}
    use_tls = not use_ssl
  else:
    use_tls = (os.getenv("SMTP_USE_TLS", "true") or "").strip().lower() in {"1", "true", "yes", "on"}
    use_ssl = (os.getenv("SMTP_USE_SSL", "false") or "").strip().lower() in {"1", "true", "yes", "on"}

  public_url = (app.config.get("PUBLIC_APP_URL") or request.url_root.rstrip("/")).rstrip("/")
  login_url = f"{public_url}{url_for('login')}"
  message = EmailMessage()
  message["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
  message["To"] = recipient
  message["Subject"] = "Your Elf's Plan sign-in details"
  message.set_content(
    f"Hello {employee.name},\n\n"
    "Your Elf's Plan account is ready. Use these details to sign in:\n\n"
    f"Login page: {login_url}\n"
    f"Login code: {employee.login_code}\n"
    f"PIN: {pin}\n\n"
    "Please keep your PIN private.\n\n"
    "Elf's Plan"
  )
  try:
    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(smtp_server, smtp_port) as server:
      if use_tls and not use_ssl:
        server.starttls()
      server.login(smtp_username, smtp_password)
      server.send_message(message)
    app.logger.info("Employee sign-in details sent to employee_id=%s", employee.id)
    return True, f"Sign-in details sent to {recipient}."
  except Exception:
    app.logger.exception("Failed to email sign-in details to employee_id=%s", employee.id)
    return False, "Could not send the email. Check SMTP settings and try again."


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


def _resolve_employee_template_path() -> str | None:
  configured = (os.getenv("EMPLOYEE_TEMPLATE_PATH") or "").strip()
  if configured:
    candidate = configured if os.path.isabs(configured) else os.path.join(APP_ROOT, configured)
    if os.path.exists(candidate):
      return candidate

  candidates = [
    os.path.join(APP_ROOT, "uploads", "employee_template.docx"),
    os.path.join(APP_ROOT, "static", "uploads", "employee_template.docx"),
  ]
  for candidate in candidates:
    if os.path.exists(candidate):
      return candidate
  return None


def _build_employee_docx(employee: Employee, template_path: str) -> io.BytesIO:
  if not PYTHON_DOCX_AVAILABLE or Document is None:
    raise ValueError("python-docx is required for employee DOCX generation")

  doc = Document(template_path)
  employee_name = (employee.name or "").strip()
  street_line = (employee.profile_address or "").strip()
  zip_code = (employee.profile_zip_code or "").strip()
  city = (employee.profile_city or "").strip()
  city_line = " ".join([part for part in [zip_code, city] if part]).strip()
  full_line = ", ".join([part for part in [employee_name, street_line, city_line] if part])

  def _to_doc_date(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
      return ""
    try:
      return datetime.strptime(raw, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
      return raw

  start_date_value = _to_doc_date(employee.profile_contract_start_date)
  end_date_value = _to_doc_date(employee.profile_contract_end_date)
  employment_type = (employee.profile_employment_type or "").strip() or "Reinigungskraft"
  euros_per_hour_raw = (employee.profile_euros_per_hour or "").strip() or "12,37"
  euros_per_hour = euros_per_hour_raw.replace(".", ",")
  working_hours = (employee.profile_working_hours or "").strip() or "3"
  work_type = (employee.profile_work_type or "").strip()
  if work_type not in {"Teilzeit", "Vollzeit", "Geringfügige"}:
    work_type = "Teilzeit"
  group_type = (employee.profile_group_type or "").strip()
  if group_type not in {"Lohngruppe", "Verwendungsgruppe"}:
    group_type = "Lohngruppe"
  group_number = (employee.profile_group_number or "").strip() or "6"
  group_label = f"{group_type} {group_number}".strip()

  # Prefer explicit placeholders (so templates can be swapped safely)
  placeholders = {
    "{{EMPLOYEE_FULL_LINE}}": full_line,
    "{{FULL_LINE}}": full_line,
    "{{EMPLOYEE_NAME}}": employee_name,
    "{{NAME}}": employee_name,
    "{{STREET}}": street_line,
    "{{ADDRESS}}": street_line,
    "{{ZIP_CITY}}": city_line,
    "{{CITY_LINE}}": city_line,
    "{{CONTRACT_START_DATE}}": start_date_value,
    "{{START_DATE}}": start_date_value,
    "{{CONTRACT_END_DATE}}": end_date_value,
    "{{END_DATE}}": end_date_value,
    "{{EMPLOYMENT_TYPE}}": employment_type,
    "{{EUROS_PER_HOUR}}": euros_per_hour,
    "{{WORKING_HOURS}}": working_hours,
    "{{WORK_TYPE}}": work_type,
    "{{GROUP_LABEL}}": group_label,
  }

  replacements = {
    **placeholders,
    "Max Mustermann, Maxmustermanngasse 4/5/10, 1210 Wien": full_line,
    "Max Mustermann": employee_name,
    "Maxmustermanngasse 4/5/10": street_line,
    "1210 Wien": city_line,
    "09.06.2025": start_date_value or "09.06.2025",
    "30.09.2025": end_date_value or "30.09.2025",
    "Reinigungskraft": employment_type,
    "Stundenlohn von brutto € 12,37": f"Stundenlohn von brutto € {euros_per_hour}",
    "€ 12,37": f"€ {euros_per_hour}",
    "3 Stunden": f"{working_hours} Stunden",
    "geringfügige": work_type,
    "geringfugige": work_type,
    "Lohngruppe 6": group_label,
    "Verwendungsgruppe 6": group_label,
    "Verwendungsgruupe 6": group_label,
  }

  changed_any = False

  employee_block = "\n".join([part for part in [employee_name, street_line, city_line] if part]).strip()
  bold_tokens = [
    employee_name,
    street_line,
    city_line,
    employee_block,
    full_line,
    start_date_value,
    end_date_value,
    employment_type,
    euros_per_hour,
    f"€ {euros_per_hour}".strip(),
    working_hours,
    f"{working_hours} Stunden".strip(),
    work_type,
    group_label,
  ]

  def _rewrite_with_bold_tokens(paragraph, updated_text: str) -> None:
    paragraph.clear()

    tokens = [t for t in (bold_tokens or []) if isinstance(t, str) and t.strip()]
    if not tokens:
      paragraph.add_run(updated_text)
      return

    ranges: list[tuple[int, int]] = []
    seen = set()
    for token in sorted(tokens, key=lambda v: len(v), reverse=True):
      token = token.strip()
      if len(token) < 2 or token in seen:
        continue
      seen.add(token)
      start = 0
      while True:
        idx = updated_text.find(token, start)
        if idx == -1:
          break
        ranges.append((idx, idx + len(token)))
        start = idx + len(token)

    if not ranges:
      paragraph.add_run(updated_text)
      return

    # Prefer earlier ranges; if same start, prefer longer token
    ranges.sort(key=lambda r: (r[0], -(r[1] - r[0])))
    selected: list[tuple[int, int]] = []
    last_end = -1
    for start, end in ranges:
      if start >= last_end:
        selected.append((start, end))
        last_end = end

    # Merge overlaps/adjacent
    merged: list[tuple[int, int]] = []
    for start, end in selected:
      if not merged:
        merged.append((start, end))
        continue
      ps, pe = merged[-1]
      if start <= pe:
        merged[-1] = (ps, max(pe, end))
      else:
        merged.append((start, end))

    pos = 0
    for start, end in merged:
      if pos < start:
        paragraph.add_run(updated_text[pos:start])
      run = paragraph.add_run(updated_text[start:end])
      run.bold = True
      pos = end
    if pos < len(updated_text):
      paragraph.add_run(updated_text[pos:])

  def _apply_to_paragraph(paragraph) -> bool:
    if not paragraph.text:
      return False
    original_text = paragraph.text
    working_text = original_text

    # 1) Placeholder + legacy sample string replacements
    for source, target in replacements.items():
      if source and source in working_text:
        working_text = working_text.replace(source, target)

    # 2) Heuristics for typical contract templates (works even if demo names/dates differ)
    if employee_block:
      # Replace employee details after 'ArbeitnehmerIn:' (keep the rest of the paragraph)
      def _employee_repl(m: re.Match) -> str:
        return f"{m.group(1)}{employee_block}{m.group(3)}"

      working_text = re.sub(
        r"((?:und\s+)?(?:ArbeitnehmerIn|Arbeitnehmerin|Arbeitnehmer/in)\s*:\s*)(.*?)(\s*Folgende\s+Vereinbarung)",
        _employee_repl,
        working_text,
        flags=re.IGNORECASE | re.DOTALL,
      )
      working_text = re.sub(
        r"((?:und\s+)?(?:ArbeitnehmerIn|Arbeitnehmerin|Arbeitnehmer/in)\s*:\s*)(.*)$",
        lambda m: f"{m.group(1)}{employee_block}",
        working_text,
        flags=re.IGNORECASE | re.DOTALL,
      )

    if start_date_value:
      working_text = re.sub(
        r"(?i)(beginnt\s+am\s+)\d{2}\.\d{2}\.\d{4}",
        lambda m: f"{m.group(1)}{start_date_value}",
        working_text,
      )
    if end_date_value:
      working_text = re.sub(
        r"(?i)(befristet\s+bis\s+zum\s+)\d{2}\.\d{2}\.\d{4}",
        lambda m: f"{m.group(1)}{end_date_value}",
        working_text,
      )

    # 3) Broader (but still contract-related) normalization
    working_text = re.sub(
      r"Stundenlohn\s+von\s+brutto\s+€\s*\d+[\.,]\d+",
      f"Stundenlohn von brutto € {euros_per_hour}",
      working_text,
    )
    working_text = re.sub(r"\b\d+\s*Stunden\b", f"{working_hours} Stunden", working_text)
    working_text = re.sub(r"geringf[uü]gige", work_type, working_text, flags=re.IGNORECASE)
    working_text = re.sub(
      r"(Lohngruppe|Verwendungsgruppe|Verwendungsgruupe)\s*\d+",
      group_label,
      working_text,
    )

    if working_text != original_text:
      _rewrite_with_bold_tokens(paragraph, working_text)
      return True

    return False

  for paragraph in doc.paragraphs:
    if _apply_to_paragraph(paragraph):
      changed_any = True

  for table in doc.tables:
    for row in table.rows:
      for cell in row.cells:
        for paragraph in cell.paragraphs:
          if _apply_to_paragraph(paragraph):
            changed_any = True

  for section in doc.sections:
    for paragraph in section.header.paragraphs:
      if _apply_to_paragraph(paragraph):
        changed_any = True
    for table in section.header.tables:
      for row in table.rows:
        for cell in row.cells:
          for paragraph in cell.paragraphs:
            if _apply_to_paragraph(paragraph):
              changed_any = True

    for paragraph in section.footer.paragraphs:
      if _apply_to_paragraph(paragraph):
        changed_any = True
    for table in section.footer.tables:
      for row in table.rows:
        for cell in row.cells:
          for paragraph in cell.paragraphs:
            if _apply_to_paragraph(paragraph):
              changed_any = True

  if not changed_any:
    raise ValueError(
      "Employee DOCX template seems incompatible: no placeholders or known contract labels were found to replace. "
      "Use placeholders like {{EMPLOYEE_NAME}}, {{STREET}}, {{ZIP_CITY}}, {{START_DATE}}, {{END_DATE}}, {{EUROS_PER_HOUR}}, {{WORKING_HOURS}}, {{GROUP_LABEL}}."
    )

  output = io.BytesIO()
  doc.save(output)
  output.seek(0)
  return output


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
    created = int(result.get("created") or 0)
    skipped_existing = int(result.get("skipped_existing") or 0)
    skipped_zero_hours = int(result.get("skipped_zero_hours") or 0)
    msg = (
      f"Monthly invoices generated for {result['month']}: "
      f"created {created}, "
      f"skipped existing {skipped_existing}, "
      f"skipped zero-hours {skipped_zero_hours}."
    )
    flash(msg, "success" if created > 0 else "warning")
  except ValueError as exc:
    flash(str(exc), "warning")
  except Exception as exc:  # pragma: no cover - defensive
    session_obj.rollback()
    app.logger.exception("Auto-generate invoices failed")
    flash(f"Auto-generate invoices failed: {exc}", "warning")
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


# Operations pages: public document library, QR code, and monthly inspections.
from service_portal import create_service_portal_blueprint

app.register_blueprint(create_service_portal_blueprint(
    session_factory=SessionLocal,
    Employee=Employee,
    Site=Site,
    SiteInspectionArea=SiteInspectionArea,
    SiteInspection=SiteInspection,
    InspectionItem=InspectionItem,
    PublicDocument=PublicDocument,
    manager_required=site_manager_required,
    login_required=login_required,
    public_document_folder=PUBLIC_DOCUMENT_FOLDER,
    inspection_photo_folder=INSPECTION_PHOTO_FOLDER,
    public_app_url=app.config["PUBLIC_APP_URL"],
    reportlab_available=REPORTLAB_AVAILABLE,
    pdf_canvas=canvas,
    page_size=A4,
))


if __name__ == "__main__":
    if "--generate-monthly-invoices" in sys.argv:
      raise SystemExit(_run_monthly_invoice_generation_from_cli())
    app.run(host="0.0.0.0", port=5000, debug=True)
