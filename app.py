import re
import io
import csv
from collections import deque
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, send_file, render_template_string

app = Flask(__name__)

# Email regex only
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}")

# Modern, mobile-friendly HTML interface for "Putzelf Marketing"
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Putzelf Marketing — URL Contact Crawler</title>

  <!-- Bootstrap 5 (CDN) -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    :root { --bs-primary: #0097b2; }
    body { background: linear-gradient(180deg,#f7fbff 0%, #ffffff 100%); min-height:100vh; }
    .brand { font-weight:700; letter-spacing:0.2px; color: #0b5560; }
    .card { border-radius:12px; box-shadow:0 6px 20px rgba(20,30,60,0.08); }
    .small-note { font-size:0.85rem; color:#6b7280; }
    .brand-row { display:flex; align-items:center; justify-content:center; gap:0.6rem; }
    .logo { height:70px; width:auto; }
    @media (max-width:800px){
      .container { padding:1rem; }
    }
  </style>
</head>
<body>
  <div class="container py-5 d-flex align-items-center justify-content-center">
    <div class="w-100" style="max-width:760px;">
      <div class="text-center mb-4">
       <div class="brand-row">
          <!-- logo served from Flask 'static' folder -->
          <img src="/static/logo.png" alt="Putzelf Marketing" class="logo"> 
          <h1 class="h3 mb-0 brand">Putzelf Marketing</h1>
        </div>
      </div>

      <div class="card p-4">
        <form id="crawl-form" class="needs-validation" novalidate>
          <div class="mb-3">
            <label for="start_url" class="form-label">Start URL</label>
            <input type="url" class="form-control form-control-lg" id="start_url" name="start_url" placeholder="https://example.com" required>
            <div class="invalid-feedback">Please enter a valid URL to start crawling.</div>
          </div>

          <div class="mb-3">
            <label for="max_pages" class="form-label">Max pages to crawl</label>
            <input type="number" class="form-control" id="max_pages" name="max_pages" min="1" max="200" value="30" required>
            <div class="form-text small-note">Limit pages to avoid long running crawls. (1–200)</div>
          </div>

          <div class="d-flex align-items-center gap-2">
            <button id="submit-btn" type="submit" class="btn btn-primary btn-lg" style="background-color:#0097b2; border-color:#0097b2;">
              <span id="btn-spinner" class="spinner-border spinner-border-sm me-2 d-none" role="status" aria-hidden="true"></span>
              Crawl & Download CSV
            </button>

            <button id="reset-btn" type="button" class="btn btn-outline-secondary" onclick="document.getElementById('crawl-form').reset()">
              Reset
            </button>

            <div id="status" class="ms-3 text-muted small-note" aria-live="polite"></div>
          </div>

          <hr class="my-4">
        </form>
      </div>

      <footer class="text-center mt-3 text-muted small-note">
        Putzelf Marketing &copy; <span id="year"></span>
      </footer>
    </div>
  </div>

  <script>
    // set year
    document.getElementById('year').textContent = new Date().getFullYear();

    // bootstrap validation
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

          // get filename from content-disposition if present
          let filename = 'emails.csv';
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
  </script>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def extract_emails(html: str):
    """Extract unique emails from HTML."""
    return list(set(EMAIL_REGEX.findall(html)))

def crawl(start_url: str, max_pages: int = 30):
    visited = set()
    queue = deque([start_url])
    results = []

    base_domain = urlparse(start_url).netloc

    while queue and len(visited) < max_pages:
        url = urldefrag(queue.popleft()).url

        if url in visited:
            continue
        if urlparse(url).netloc != base_domain:
            continue

        visited.add(url)
        app.logger.info("Crawling: %s", url)

        try:
            resp = requests.get(url, timeout=10, headers={"User-Agent": "PutzelfMarketing/1.0"})
        except Exception:
            continue

        if not (200 <= resp.status_code < 300):
            continue

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract emails on this page
        for email in extract_emails(html):
            results.append({"url": url, "email": email})

        # Add new internal links to queue
        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            if link.startswith("mailto:"):
                continue
            queue.append(link)

    # Deduplicate by email only
    unique = {}
    for item in results:
        email = item["email"].lower().strip()
        if email and email not in unique:
            unique[email] = item

    return list(unique.values())

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_TEMPLATE)

    start_url = request.form.get("start_url")
    try:
        max_pages = int(request.form.get("max_pages", "30"))
    except Exception:
        max_pages = 30
    max_pages = max(1, min(max_pages, 200))

    data = crawl(start_url, max_pages)

    # Build CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["url", "email"])
    writer.writeheader()
    for row in data:
        writer.writerow(row)

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="putzelf_emails.csv",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)