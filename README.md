# Singing Bowl Export Desk 🎵

**Singing Bowl Export Desk** is a complete, production-ready B2B Lead Generation and Cold Outreach SaaS dashboard specifically tailored for Singing Bowl Export businesses. It enables exporters to discover real buyer business emails across target countries, manage lead databases, compose personalized HTML email catalogs, send bulk outreach campaigns with delivery rate-limiting and retry logic, track performance analytics, and export databases.

---

## 🌟 Features

- **Automated Lead Search & Extraction**: Discover singing bowl importers, wellness shops, sound therapy centers, and holistic stores via SerpApi or built-in search simulation.
- **Web Scraping Pipeline**: Extracts business name, owner/contact person, email, phone number, website, and country directly from target websites using BeautifulSoup4.
- **Email Validation & Automatic Deduplication**: Validates email format, filters out generic placeholder/disposable domains, and prevents duplicate records in SQLite based on unique email addresses.
- **Lead Scoring System**: Computes relevance scores (0–100) based on data completeness (presence of owner name, direct email, phone, website, and country).
- **Personalized Email Outreach**: Dynamic placeholder replacement (`{{ownerName}}`, `{{businessName}}`, `{{country}}`, `{{website}}`, `{{productCatalogPDF}}`, `{{whatsAppNumber}}`, `{{unsubscribeUrl}}`).
- **Rate-Limited Bulk Sending**: Sends emails with configurable delays (2–5 seconds) to maintain high inbox deliverability, with automatic retry for failed transmissions and live progress reporting.
- **Analytics & Reporting Dashboard**: Visualizes email performance, daily sending statistics, top buyer countries via Chart.js, and campaign history log.
- **Database Management & Safe Reset**: Search, filter by country/status, paginate leads (25 rows/page), edit/delete individually or in bulk, and safely reset the database with confirmation modal.
- **Data Export**: Export complete lead data to CSV and Microsoft Excel (`.xlsx`) with custom formatted columns.

---

## 📁 Folder Structure

```text
SingingBowlExportDesk/
├── app.py                     # Main Flask application with Blueprints & API routes
├── requirements.txt           # Python package dependencies
├── README.md                  # Comprehensive project documentation
├── .env.example               # Template for environment variables
├── instance/
│   └── database.db            # SQLite database instance (auto-created)
├── services/
│   ├── database.py            # SQLAlchemy database initialization & default seeder
│   ├── models.py              # Lead, Campaign, and Settings ORM models
│   ├── search_service.py      # SerpApi integration & search simulation engine
│   ├── scraper.py             # BeautifulSoup web scraper & contact extractor
│   ├── email_sender.py        # SMTP manager, bulk sender & email personalizer
│   └── utils.py               # Utilities for text cleaning, scoring & email validation
├── static/
│   ├── css/
│   │   └── style.css          # Design system & custom UI animations
│   └── js/
│       ├── dashboard.js       # Auto-refreshing dashboard metrics
│       ├── search.js          # Lead search state machine & progress polling
│       ├── leads.js           # Lead table controls, pagination & email composer
│       ├── reports.js         # Analytics graphs & Chart.js renderer
│       └── settings.js        # Settings form handlers & SMTP testing
├── templates/
│   ├── base.html              # Layout shell with sidebar, top nav & modals
│   ├── dashboard.html         # Overview dashboard & KPI cards
│   ├── search.html            # Search form, progress indicator & pipeline steps
│   ├── leads.html             # Lead database table & HTML email composer
│   ├── campaigns.html         # Campaign history & delivery logs
│   ├── reports.html           # Graphical reports & top countries analytics
│   ├── settings.html          # SMTP, SerpApi, and outreach configuration
│   ├── 404.html               # Custom 404 error page
│   └── 500.html               # Custom 500 error page
└── uploads/
    └── exports/               # Generated export files directory
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.9+ installed on your system.
- Git (optional).

### 2. Clone / Set Up Project Directory
Navigate to the root project folder:
```bash
cd SingingBowlExportDesk
```

### 3. Create Virtual Environment
Create and activate a virtual environment:

- **Windows**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` (optional, settings can also be updated directly in the UI):
```bash
cp .env.example .env
```

---

## 🏃 Running the Application

Execute the Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## ⚙️ Configuration

### SMTP Email Settings
Navigate to **Settings** in the dashboard to set up your email sending service:
- **Email Address**: Your sender email (e.g. `export@yourdomain.com` or `yourgmail@gmail.com`).
- **App Password**: App-specific password generated from Google Account Settings (for Gmail) or standard SMTP password.
- **SMTP Host**: Default `smtp.gmail.com` (or `smtp.office365.com`, `mail.yourdomain.com`).
- **Port**: `587` (STARTTLS) or `465` (SSL).
- Use the **Test Connection** button to verify setup before launching campaigns.

### SerpApi Key Configuration
- Sign up for a free key at [SerpApi.com](https://serpapi.com).
- Enter the key under **Settings > Search Settings**.
- If no key is provided, the application operates in **Simulation Mode**, utilizing a curated pool of singing bowl business data for demonstration and testing.

---

## 🛠️ How It Works

### 1. Web Scraping & Contact Extraction
- **Discovery**: Queries search engines for keywords such as `"singing bowls wholesale"`, `"tibetan bowls supplier"`, `"sound healing store"` filtered by target countries.
- **Scraping**: Visits target domain landing pages and contact pages. Parses HTML with BeautifulSoup to locate email addresses, phone numbers, owner/founder names from Schema.org metadata or text patterns (`"Founded by..."`, `"Contact: ..."`), and business titles.
- **Scoring**: Calculates relevance scores based on data completeness:
  - Valid Email: +30 points
  - Owner Name: +20 points
  - Business Name: +15 points
  - Phone Number: +15 points
  - Website URL: +10 points
  - Country Identified: +10 points

### 2. Email Validation & Duplicate Removal
- **Regex & Domain Checks**: Filters out invalid syntax and non-business domains (`example.com`, `sentry.io`, etc.) alongside `noreply@` prefixes.
- **Database Deduplication**: Prior to insertion, checks the SQLite database for existing email addresses (`Lead.email`). Duplicates are skipped automatically and logged in the search summary.

### 3. Personalization Engine
Outreach email templates support HTML and automatically substitute variables:
- `{{ownerName}}`: Extracted contact person or business fallback.
- `{{businessName}}`: Target business name.
- `{{country}}`: Country of the lead.
- `{{website}}`: Business website URL.
- `{{productCatalogPDF}}`: Configured downloadable PDF catalog link.
- `{{whatsAppNumber}}`: Export manager's WhatsApp number.
- `{{unsubscribeUrl}}`: Compliance unsubscribe link.

---

## 📊 License & Author

Designed for **Singing Bowl Exporters** to streamline international B2B buyer lead generation and outreach.
