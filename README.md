
# URL Contact Crawler (Python + Flask)

This is a small web application that:

- Takes a **starting URL** (e.g. a business website or directory page).
- Crawls that site (same domain only, BFS, limited pages).
- Extracts **email addresses** and **phone numbers** using regex.
- Generates a **CSV file** (Excel compatible) for direct download.

There is a minimal web page with:

- A text field for the starting URL
- A numeric field for max pages to crawl
- A **"Crawl & Download CSV"** button

---

## 1. Requirements

- Python 3.8+ recommended

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 2. Run the application

From the project folder:

```bash
python app.py
```

You should see:

```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Open that address in your browser.

---

## 3. How to use

1. Go to `http://127.0.0.1:5000/`
2. Enter a **start URL** (for example, a business listing or company site).
3. Optionally adjust `Max pages to crawl` (default 30, max 200).
4. Click **"Crawl & Download CSV"**.

Your browser will download `contacts.csv` which contains:

- `url`  — page where the contact was found
- `email`
- `phone`

Open it with Excel, Google Sheets, or any spreadsheet tool.

---

## 4. Notes / Limitations

- This is a **very simple** crawler:
  - No JavaScript rendering.
  - No robots.txt parsing or rate limiting.
  - Only stays on the same domain as the starting URL.
- It may **miss** some contacts, especially those loaded dynamically via JS.
- It may still pick up some noise / non-contact numbers; you can clean the data in Excel.
- You are fully responsible for using this tool in a way that follows:
  - Your company policies
  - Website terms of service
  - Local regulations (e.g. GDPR, anti-spam laws)

If you want to make it more compliant, you can:

- Add robots.txt checks.
- Add per-domain rate limiting.
- Restrict which URLs are allowed (whitelist domains).

---

## 5. Quick summary for your boss

- Input: **one URL**
- Output: **CSV of emails + phone numbers** found on that domain
- Tech: **Python + Flask**, single file app, can be extended easily
