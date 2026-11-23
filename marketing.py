"""Contact crawler and AI assistant routes."""

from __future__ import annotations

import json
import logging
import os
import re
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urldefrag, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify, render_template, request, send_file

logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)

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
        logger.debug("Playwright not available: %s", e)
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
        logger.warning("Playwright fetch failed for %s: %s", url, e)
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
        logger.warning("requests.get failed for %s: %s", url, e)
        return "", 0

def crawl(
    start_url: str,
    max_pages: int = 100,
    render_js: bool = False,
    *,
    default_phone_region: str,
    infer_region_from_netloc,
    normalize_phone_fn,
    find_labelled_phones_fn,
):
    """
    Crawl collecting emails and phones with stricter phone extraction rules.
    """
    visited = set()
    queue = deque([start_url])
    url_map = {}

    parsed_start = urlparse(start_url)
    base_domain = _normalize_netloc(parsed_start.netloc)
    start_segments = [s for s in parsed_start.path.split("/") if s]
    phone_region = infer_region_from_netloc(parsed_start.netloc) or default_phone_region

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
            logger.debug("Skipping external host: %s", url)
            continue

        visited.add(url)
        logger.info("Crawling: %s", url)

        html, status = fetch_html(url, render_js=False)
        logger.debug("Fetched %s status=%s len=%d (requests)", url, status, len(html or ""))
        try:
            status_num = int(status)
        except Exception:
            status_num = 0
        if not (200 <= status_num < 300):
            logger.debug("Skipping non-2xx: %s (%s)", url, status)
            continue

        soup = BeautifulSoup(html or "", "html.parser")

        business_name = extract_business_name_from_soup(soup)

        emails = set(EMAIL_REGEX.findall(html or ""))
        phones = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("tel:"):
                num = href.split("tel:")[1].split("?")[0].strip()
                n = normalize_phone_fn(num, region=phone_region)
                if n:
                    phones.add(n)

        for tag_name in VISIBLE_TAGS:
            for tag in soup.find_all(tag_name):
                text = tag.get_text(" ", strip=True)
                if not text:
                    continue
                if len(text) > 300:
                    continue
                for n in find_labelled_phones_fn(text, region=phone_region):
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
                        n = normalize_phone_fn(val, region=phone_region)
                        if n:
                            phones.add(n)
                    else:
                        for n in find_labelled_phones_fn(val, region=phone_region):
                            phones.add(n)
                elif isinstance(val, (list, tuple)):
                    for part in val:
                        for n in find_labelled_phones_fn(str(part), region=phone_region):
                            phones.add(n)

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                addr = href.split("mailto:")[1].split("?")[0].strip()
                if EMAIL_REGEX.match(addr):
                    emails.add(addr)

        if not emails and is_probable_detail_path(parsed.path) and render_js:
            logger.debug("No emails via requests on probable detail %s — retrying with Playwright", url)
            html_js, status_js = fetch_html(url, render_js=True)
            logger.debug("Fetched %s status=%s len=%d (playwright)", url, status_js, len(html_js or ""))
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
                        n = normalize_phone_fn(num, region=phone_region)
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
                        for n in find_labelled_phones_fn(t, region=phone_region):
                            phones.add(n)

        if emails or phones:
            grp = url_map.setdefault(url, {"emails": set(), "phones": set(), "business_names": set()})
            grp["emails"].update(emails)
            grp["phones"].update(phones)
            if business_name:
                grp["business_names"].add(business_name)
            for e in emails:
                logger.info("Found email %s on %s", e, url)
            for p in phones:
                logger.info("Found phone %s on %s", p, url)

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
                logger.debug("Prioritizing single-segment detail link: %s", link)
                enqueue(link, left=True)
                continue

            if len(path_segments) >= 1 and path_segments[0] == "firmen" and len(path_segments) == 2:
                if path_segments != start_segments:
                    logger.debug("Skipping region index link: %s", link)
                    continue

            if len(path_segments) > 2 and path_segments[0] == "firmen":
                logger.debug("Prioritizing probable detail link: %s", link)
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
        p = normalize_phone_fn(phone, region=phone_region)
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

    logger.info("Crawl finished: found %d contact rows", len(rows))
    return rows


def create_marketing_blueprint(
    *,
    login_required,
    openai_client,
    clean_contacts,
    generate_contacts_pdf,
    reportlab_available: bool,
    default_phone_region: str,
    infer_region_from_netloc,
    normalize_phone_fn,
    find_labelled_phones_fn,
):
    blueprint = Blueprint("marketing", __name__)

    @blueprint.route("/crawler", methods=["GET", "POST"])
    @login_required
    def crawler():
        if request.method == "GET":
            return render_template(
                "crawler.html",
                gpt_enabled=bool(openai_client),
                active_page="crawler",
            )

        if not reportlab_available:
            return jsonify({"error": "reportlab not installed; cannot generate PDF output."}), 503
        start_url = (request.form.get("start_url") or "").strip()
        if not start_url:
            return jsonify({"error": "Missing start URL"}), 400
        try:
            max_pages = int(request.form.get("max_pages", "100"))
        except (TypeError, ValueError):
            max_pages = 100
        max_pages = max(1, min(max_pages, 200))
        render_js = bool(request.form.get("render_js"))
        data = crawl(
            start_url,
            max_pages=max_pages,
            render_js=render_js,
            default_phone_region=default_phone_region,
            infer_region_from_netloc=infer_region_from_netloc,
            normalize_phone_fn=normalize_phone_fn,
            find_labelled_phones_fn=find_labelled_phones_fn,
        )
        cleaned_data = clean_contacts(data)
        pdf_buffer = generate_contacts_pdf(cleaned_data)
        filename = f"putzelf_contacts_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    @blueprint.route("/gpt", methods=["POST"])
    @login_required
    def gpt():
        if openai_client is None:
            return jsonify({
                "error": "GPT integration is not configured. Set OPENAI_API_KEY and install the 'openai' package."
            }), 503
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
            user_content += "\n\nContext:\n" + context
        try:
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
        except Exception as exc:
            logger.warning("GPT endpoint error: %s", exc)
            return jsonify({"error": "Failed to contact GPT backend."}), 500

    return blueprint
