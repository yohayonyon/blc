# 🕷️ Broken Links Crawler (BLC)

A multithreaded Python crawler that finds **broken links** across websites, reports them in human-readable or JSON formats, and can optionally email the results. Perfect for website audits, SEO checks, or quality assurance tasks.

---

## 🚀 Features

- 🔍 Detects broken links (`404`, no domain, HTTPS redirects, etc.)
- 🌐 Depth-controlled internal/external link crawling
- ⚙️ Multithreaded (user-defined or auto-scaled)
- 🧾 Reports in **human-readable** and **JSON** formats
- 🕒 Report timestamps use the machine's **local timezone**
- 📧 Optional email reports with SMTP config
- 📊 Live terminal display (can be silenced)
- 📄 Also extracts links from PDF files under the same domain

---

## 📦 Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/yohayonyon/blc
   cd blc
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Usage

```bash
python blc.py <url> [options]
```

### Example:

```bash
python blc.py https://example.com -t 8 -d 2 --email_to admin@example.com --email_report_mode errors
```

---

## 🛠️ CLI Options

| Option | Description |
|--------|-------------|
| `<url>` | **(Required)** Root URL to begin crawling |
| `-t`, `--threads` | Number of threads (`-1` for auto) |
| `-d`, `--depth` | Max crawl depth (`-1` = unlimited) |
| `-s`, `--silent` | Suppress live progress display |
| `--log_file` | Set log filename (default: `blc.log`) |
| `--log_verbosity` | Log level: `none`, `info`, `debug`, etc. |
| `--log_display` | Also show logs on terminal |
| `--human_report` | Filename for human report (default: `report.txt`) |
| `--json_report` | Filename for JSON report (default: `report.json`) |
| `--email_to` | Recipient email address |
| `--email_report_mode` | `always`, `errors`, or `never` (when to send report) |

---

## 🧾 Report Format

### Human-readable (`--human_report`)

```
Crawler Report
============================================================
Generated at     : 2025-04-08 17:22:12 IDT+0300
Execution Time   : 00:02:43.11
Visited URLs     : 85
Threads Used     : 4
============================================================

Discovered Links:
------------------------------------------------------------
[1] URL         : https://example.com/broken-page
     Depth       : 1
     Appeared In : https://example.com
     Status      : no_such_page
     Error       : HTTPError: 404 - Not Found
------------------------------------------------------------
```

### JSON (`--json_report`)

```json
{
  "report_generated_at": "2025-04-08T17:22:12 IDT+0300",
  "execution_time_seconds": "00:02:43.11",
  "visited_urls": 85,
  "threads_used": 4,
  "links": [
    {
      "url": "https://example.com/broken-page",
      "depth": 1,
      "appeared_in": "https://example.com",
      "status": "no_such_page",
      "error": "HTTPError: 404 - Not Found"
    }
  ]
}
```

---

## 📧 Email Reporting

### Step 1: Create `config.json`

```json
{
  "EMAIL_SENDER": "your_email@example.com",
  "EMAIL_PASSWORD": "your_app_password",
  "SMTP_ADDRESS": "smtp.gmail.com",
  "SMTP_PORT": "587"
}
```

### Step 2: Run with email options

```bash
python blc.py https://example.com --email_to your_email@example.com --email_report_mode always
```

---

## 🧠 Architecture

- `blc.py` – CLI entry point
- `broken_links_crawler.py` – Orchestrator
- `crawler.py` – Core link parser & validator
- `link.py` – Link & status definitions
- `worker_manager.py` – Thread pool with deduplication
- `human_report.py`, `json_report.py` – Reporting classes
- `email_report_sender.py` – SMTP-based email system

---

## 📌 Notes

- The crawler **normalizes and filters URLs**, and skips non-HTML content.
- Links in **PDFs under the same domain** are also crawled.
- Broken links are categorized using `LinkStatus` enums for clear reporting.
- Live progress shows execution time and counts in real time unless `--silent` is used.

---

## 🧑‍💻 License

MIT License – feel free to use and modify.

---