# Florida School Surtax Oversight Dashboard - Complete Playbook

A comprehensive guide to understanding and using the K-12 school construction oversight platform.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Quick Start](#2-quick-start)
3. [Architecture](#3-architecture)
4. [Module Reference](#4-module-reference)
5. [AI/ML Capabilities](#5-aiml-capabilities)
6. [Data Flow](#6-data-flow)
7. [Web Application](#7-web-application)
8. [Configuration](#8-configuration)
9. [Common Workflows](#9-common-workflows)
10. [Deployment & Operations](#10-deployment--operations)

---

## 1. System Overview

### What This System Does

This is an **AI-powered oversight dashboard** for Florida school district surtax-funded construction projects. It enables citizen oversight committees to monitor $45M+ in annual school construction spending with:

| Feature | Purpose |
|---------|---------|
| Executive Dashboard | One-screen summary for committee meetings |
| Natural Language Q&A | Ask questions in plain English, get instant answers |
| Risk Monitoring | Automatic flagging of delayed and over-budget projects |
| Vendor Analytics | Performance tracking and recommendation engine |
| Document Management | Store contracts, invoices, progress reports |
| Public Transparency | Citizen-facing portal for taxpayer accountability |

### Key Capabilities

- **Real-Time Project Tracking** - 45 surtax-funded projects monitored
- **AI-Powered Q&A** - Executive-friendly natural language interface
- **Automated Alerts** - Email notifications for delays and budget overruns
- **Earned Value Analysis** - CPI/SPI metrics for project health
- **Multi-County Support** - Template-based system scales to any Florida county
- **Compliance Monitoring** - Capital vs. operating classification, audit trails
- **Vendor Scorecard** - Performance rating with ideal vendor matching

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.8+, Flask 2.3+ |
| Database | SQLite (production-ready file-based) |
| Frontend | Jinja2 templates, Tailwind CSS |
| Configuration | YAML with environment variable interpolation |
| AI/ML | Rule-based NLP, pattern recognition, predictive analytics |
| Deployment | Windows auto-start, Gunicorn-ready for Linux |

### Business Impact

| Metric | Value |
|--------|-------|
| Budget Under Oversight | $45M annually (~$450M over 10-year surtax) |
| Projects Tracked | 45 active surtax-funded projects |
| Schools Covered | 40+ Marion County schools |
| Data Quality | 100% school name mapping (auto-classified) |
| Alert Coverage | 30-day delay threshold, 10% budget variance |

---

## 2. Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Texasdada13/florida-school-surtax-oversight.git
cd florida-school-surtax-oversight

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your settings (optional)
```

### Run the Dashboard

**Option 1: PowerShell Script**
```powershell
.\start_dashboard.ps1
# Opens http://127.0.0.1:5847
```

**Option 2: Direct Python**
```bash
python app.py
# Dashboard at http://127.0.0.1:5847
```

**Option 3: Specify County**
```bash
python run.py --county marion --port 5847
```

### First Steps for New Users

1. **Overview Page** (`/`) - See total budget, projects, and spending by category
2. **Ask AI** (`/ask`) - Try "What projects are delayed?"
3. **Executive View** (`/executive`) - Clean view for committee meetings
4. **Concerns** (`/concerns`) - Review flagged projects needing attention
5. **Documents** (`/documents`) - Upload contracts and reports

---

## 3. Architecture

### Directory Structure

```
florida-school-surtax-oversight/
├── app/                        # Flask application
│   ├── __init__.py            # App factory
│   ├── config.py              # Configuration loader
│   ├── database.py            # SQLite utilities
│   ├── routes/                # Route blueprints
│   │   ├── main.py           # Overview, projects, schools, ask AI
│   │   ├── monitoring.py     # Concerns, watchlist, risk, audit
│   │   ├── financials.py     # Vendors, analytics, budget
│   │   ├── documents.py      # Document library, reports
│   │   ├── tools.py          # Executive view, compliance, map
│   │   └── api.py            # JSON API endpoints
│   ├── services/              # Business logic layer
│   │   ├── stats.py          # Statistical calculations
│   │   ├── ai_chat.py        # Natural language Q&A
│   │   ├── ai_insights.py    # ML-based insights
│   │   ├── vendor_matching.py # Vendor recommendations
│   │   ├── school_mapping.py  # School name extraction
│   │   ├── email_alerts.py    # Alert notifications
│   │   └── document_manager.py # File management
│   ├── templates/             # Jinja2 HTML templates
│   └── static/                # CSS, JavaScript assets
│
├── config/                    # Configuration files
│   ├── default.yaml          # Global defaults
│   └── counties/
│       └── marion.yaml       # Marion County config
│
├── data/                      # Data storage
│   ├── surtax.db             # SQLite database
│   ├── schemas/
│   │   └── schema.sql        # Database schema
│   └── uploads/              # Document storage
│
├── scripts/                   # Utility scripts
│   ├── map_school_projects.py
│   ├── migrate_email_alerts.py
│   └── migrate_documents.py
│
├── run.py                     # Application entry point
├── app.py                     # Simple runner
└── start_dashboard.ps1        # Windows startup script
```

### Component Relationships

```
                    ┌─────────────────────────┐
                    │      Entry Points       │
                    │   run.py / app.py       │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │   Flask App Factory     │
                    │   app/__init__.py       │
                    └───────────┬─────────────┘
                                │
     ┌──────────────────────────┼──────────────────────────┐
     │                          │                          │
┌────▼────┐              ┌──────▼──────┐            ┌──────▼──────┐
│ Routes  │              │  Services   │            │  Database   │
│ (6 BP)  │◄────────────►│  (7 svc)    │◄──────────►│  SQLite     │
└────┬────┘              └──────┬──────┘            └─────────────┘
     │                          │
     │    ┌─────────────────────┼─────────────────────┐
     │    │                     │                     │
     ▼    ▼                     ▼                     ▼
┌─────────────┐         ┌─────────────┐       ┌─────────────┐
│  Templates  │         │   AI/ML     │       │   Config    │
│  (Jinja2)   │         │  Services   │       │   (YAML)    │
└─────────────┘         └─────────────┘       └─────────────┘
```

### Blueprint Organization

| Blueprint | URL Prefix | Purpose |
|-----------|------------|---------|
| `main_bp` | `/` | Overview, projects, schools, AI chat |
| `monitoring_bp` | `/` | Concerns, watchlist, risk dashboard, audit |
| `financials_bp` | `/` | Vendors, analytics, budget performance |
| `documents_bp` | `/` | Document library, meeting minutes, reports |
| `tools_bp` | `/` | Executive view, compliance, map, public portal |
| `api_bp` | `/api` | JSON endpoints for AJAX calls |

---

## 4. Module Reference

### Routes (app/routes/)

#### main.py - Core Dashboard Views

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Dashboard overview with stats and spending breakdown |
| `/projects` | GET | Projects list with filtering and sorting |
| `/project/<id>` | GET | Individual project detail page |
| `/schools` | GET | Schools listing with project counts |
| `/ask` | GET | AI-powered question interface |

**Example - Overview Data:**
```python
# Returns:
{
    'total_projects': 45,
    'total_budget': 156000000,  # $156M
    'total_spent': 89000000,    # $89M
    'active_projects': 28,
    'completed_projects': 12,
    'delayed_projects': 6,
    'over_budget_projects': 4,
    'avg_completion': 57.3      # percent
}
```

#### monitoring.py - Risk & Issue Tracking

| Route | Method | Purpose |
|-------|--------|---------|
| `/concerns` | GET | All delayed + over-budget projects |
| `/watchlist` | GET | User's personal project watchlist |
| `/risk` | GET | Risk dashboard by severity level |
| `/audit` | GET | Audit trail of database changes |

**Risk Classification:**
- **High Risk:** Delayed AND over-budget
- **Medium Risk:** Delayed OR over-budget (not both)
- **Low Risk:** On time and on budget

#### financials.py - Budget & Vendor Analysis

| Route | Method | Purpose |
|-------|--------|---------|
| `/vendors` | GET | Vendor performance tracking |
| `/vendor-profile` | GET | Ideal vendor recommendation tool |
| `/change-orders` | GET | Contract modification tracking |
| `/analytics` | GET | Spending by category and status |
| `/budget-performance` | GET | Earned Value Analysis (EV/AC, CPI, SPI) |
| `/county-comparison` | GET | Multi-county benchmarking |

#### documents.py - Document Management

| Route | Method | Purpose |
|-------|--------|---------|
| `/documents` | GET | Document library with filtering |
| `/documents/upload` | POST | Upload new document |
| `/documents/download/<id>` | GET | Download file |
| `/documents/view/<id>` | GET | View inline (PDF/images) |
| `/documents/delete/<id>` | POST | Soft delete document |
| `/minutes` | GET | Meeting minutes archive |
| `/report` | GET | Annual report generator |

**Supported File Types:**
- Documents: PDF, DOC, DOCX, XLS, XLSX, TXT, CSV
- Images: JPG, PNG, GIF
- Archives: ZIP
- Max size: 50 MB

#### tools.py - Special Views

| Route | Method | Purpose |
|-------|--------|---------|
| `/executive` | GET | Simplified view for committee meetings |
| `/compliance` | GET | Capital vs. operating classification |
| `/map` | GET | Geographic map of school projects |
| `/public` | GET | Public transparency portal |
| `/alerts` | GET | Alert configuration and history |

#### api.py - JSON API Endpoints

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/ask` | POST | Process natural language question |
| `/api/projects` | GET | Get all projects as JSON |
| `/api/stats` | GET | Dashboard statistics |
| `/api/watchlist` | GET | Current watchlist |
| `/api/watchlist/toggle/<id>` | POST | Add/remove from watchlist |
| `/api/alerts/status` | GET | Email alert configuration status |
| `/api/alerts/test` | POST | Send test alert email |

---

### Services (app/services/)

#### stats.py - Statistical Calculations

```python
from app.services.stats import (
    get_overview_stats,
    get_spending_by_category,
    get_spending_by_school,
    get_budget_vs_actual
)

# Get overview statistics
stats = get_overview_stats(cursor)
# Returns: total_projects, total_budget, delayed_projects, etc.

# Get spending breakdown
spending = get_spending_by_category(cursor)
# Returns: category, project_count, total_budget, total_spent
```

#### ai_chat.py - Natural Language Q&A

**Purpose:** Executive-friendly interface that answers questions in plain English.

```python
from app.services.ai_chat import process_question

result = process_question("What projects are behind schedule?", cursor)
# Returns:
{
    'answer': '**6 projects** are 30+ days behind schedule...',
    'data': [list of delayed projects],
    'suggestions': ['Which vendors are involved?', 'What are the delay reasons?'],
    'ask_staff': True,  # Flag for action items
    'next_step': 'Request status updates from contractors',
    'data_note': 'Delay days calculated from original completion date'
}
```

**Question Categories:**

| Category | Example Questions | Handler |
|----------|-------------------|---------|
| Schedule Risks | "What's delayed?", "Schedule problems?" | `_handle_schedule_risks()` |
| Budget Issues | "Over budget?", "Cost overruns?" | `_handle_over_budget()` |
| Remaining Budget | "How much left?", "Remaining funds?" | `_handle_remaining_budget()` |
| Largest Projects | "Top projects?", "Biggest contracts?" | `_handle_largest_projects()` |
| Vendor Analysis | "Top vendor?", "Contractor performance?" | `_handle_top_vendor()` |
| Category Split | "Spending by category?", "How is money allocated?" | `_handle_category_split()` |

#### ai_insights.py - ML-Based Insights

**Purpose:** Automated pattern detection and recommendations.

```python
from app.services.ai_insights import generate_insights

insights = generate_insights(cursor)
# Returns list of insights:
[
    {
        'type': 'trend',
        'icon': 'trending-up',
        'title': 'Budget Trend Alert',
        'description': 'Projects consistently exceed initial budgets by 12%',
        'severity': 'warning'
    },
    ...
]
```

**Insight Types:**
- Budget trend analysis
- Delay pattern detection
- Vendor performance alerts
- Category efficiency metrics
- Spending vs. progress analysis

#### vendor_matching.py - Vendor Recommendation Engine

```python
from app.services.vendor_matching import (
    get_ideal_vendor_profile,
    evaluate_vendor_fit
)

# Get recommendations for a project type
profile = get_ideal_vendor_profile('new_construction', budget_tier='large')
# Returns: recommended certifications, experience, bonding capacity

# Score how well a vendor fits a project
score = evaluate_vendor_fit(vendor_id, project_category, cursor)
# Returns: 0-100 fit score with breakdown
```

**Vendor Fit Scoring (0-100):**
- Base score: 50
- Category experience: +/- 20 points
- On-time performance: +/- 15 points
- On-budget performance: +/- 15 points
- Project capacity: +/- 10 points

#### school_mapping.py - School Name Extraction

**Purpose:** Automatically identify schools from contract titles.

```python
from app.services.school_mapping import (
    extract_school_from_title,
    auto_map_schools,
    get_school_list
)

# Extract school from title
school = extract_school_from_title("HVAC Upgrades - West Port High")
# Returns: "West Port High"

# Bulk update unmapped projects
stats = auto_map_schools(cursor)
# Returns: {'mapped_high': 20, 'mapped_medium': 5, 'still_unmapped': 3}
```

**Matching Strategy:**
1. Exact name matches (40+ Marion County schools)
2. Aliases ("Dunnellon Senior High" → "Dunnellon High")
3. New school patterns ("New Elementary W" → "New Elementary 'W' (Planned)")
4. District-wide detection ("All schools" → "District-Wide")

#### email_alerts.py - Alert Notifications

```python
from app.services.email_alerts import (
    EmailAlertService,
    check_and_send_alerts
)

# Check configuration
service = EmailAlertService()
if service.is_enabled():
    # Send delay alert
    service.send_delay_alert(
        project_title="HVAC Upgrade - West Port High",
        school_name="West Port High",
        delay_days=45,
        original_date="2024-06-01",
        current_date="2024-07-15"
    )

# Automated check for all projects
stats = check_and_send_alerts(cursor)
# Returns: {'delay_alerts': 3, 'budget_alerts': 1}
```

**Alert Types:**
- Delay alerts (30+ days behind schedule)
- Budget alerts (10%+ over original)
- Weekly digest summary

#### document_manager.py - File Management

```python
from app.services.document_manager import (
    save_document,
    get_document,
    get_documents_for_contract
)

# Upload document
success, message, doc_id = save_document(
    cursor=cursor,
    file=uploaded_file,
    filename="contract.pdf",
    contract_id="CTR-2024-001",
    document_type="contract",
    description="Original signed contract"
)

# Get documents for a project
docs = get_documents_for_contract(cursor, "CTR-2024-001")
```

---

## 5. AI/ML Capabilities

### Natural Language Processing

The system uses **rule-based NLP** optimized for executive personas:

**Design Principles:**
1. Lead with numbers - dollar amounts and percentages first
2. Plain English - no jargon or technical terms
3. Name names - specific vendors, projects, schools
4. One screen max - concise answers
5. Flag follow-up items - mark things needing staff attention
6. Include next steps when actionable

**Question Routing:**
```
User Question → Keyword Matching → Handler Selection → Database Query → Response Formatting
```

**Example Flow:**
```
"What projects are over budget?"
    ↓
Keywords: "over budget", "cost", "budget"
    ↓
Handler: _handle_over_budget()
    ↓
Query: SELECT * FROM contracts WHERE is_over_budget = 1
    ↓
Response: "**4 projects** are currently over their original budget..."
```

### Machine Learning Features

| Feature | Method | Purpose |
|---------|--------|---------|
| Cost Performance Index | Historical analysis | Predict cost overruns |
| Delay Pattern Detection | Category-level trends | Identify problematic project types |
| Vendor Performance Score | Multi-factor scoring | Evaluate contractor reliability |
| Budget Variance Detection | Anomaly identification | Flag unusual spending |
| Efficiency Metrics | Spending vs. progress | Alert on cost overrun risk |

### Earned Value Analysis

The system calculates project health using industry-standard metrics:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| CPI (Cost Performance Index) | EV / AC | >1.0 = under budget |
| SPI (Schedule Performance Index) | EV / PV | >1.0 = ahead of schedule |
| Cost Variance | EV - AC | Positive = savings |
| Schedule Variance | EV - PV | Positive = ahead |

---

## 6. Data Flow

### Request Flow - Dashboard Overview

```
User Request: GET /
    ↓
main_bp.index() route
    ↓
get_db() → SQLite connection
    ↓
get_overview_stats(cursor)
    ├─ COUNT(*) projects
    ├─ SUM(current_amount) total budget
    ├─ SUM(total_paid) spent amount
    ├─ COUNT WHERE is_delayed=1
    └─ COUNT WHERE is_over_budget=1
    ↓
get_spending_by_category(cursor)
    ├─ GROUP BY surtax_category
    └─ SUM budgets per category
    ↓
render_template('main/overview.html')
    ├─ Apply currency filters ($45.2M)
    └─ Render with Tailwind CSS
    ↓
Response to browser
    ↓
close_db()
```

### AI Chat Data Flow

```
User: "What projects are delayed?"
    ↓
POST /api/ask
    ↓
process_question(question, cursor)
    ├─ Keyword matching → _handle_schedule_risks()
    ├─ Query: SELECT * FROM contracts WHERE is_delayed=1
    ├─ Format response with metrics
    ├─ Generate follow-up suggestions
    └─ Set ask_staff flag if action needed
    ↓
Return JSON:
{
    'answer': '**6 projects** are 30+ days behind...',
    'data': [project1, project2, ...],
    'suggestions': ['What vendors?', 'Delay reasons?'],
    'ask_staff': true,
    'next_step': 'Request status updates'
}
    ↓
Frontend renders with:
    ├─ Markdown answer
    ├─ Data table (if applicable)
    ├─ Quick suggestion buttons
    └─ Staff alert indicator
```

### Document Upload Flow

```
User: Upload contract PDF
    ↓
POST /documents/upload
    ↓
Validation:
    ├─ Check file extension (whitelist)
    ├─ Check file size (<50MB)
    └─ Get MIME type
    ↓
Storage:
    ├─ Generate UUID filename
    ├─ Save to data/uploads/2026/01/{uuid}.pdf
    └─ Insert database record
    ↓
Return: { success: true, document_id: 123 }
```

---

## 7. Web Application

### Page Overview

| Page | URL | Purpose |
|------|-----|---------|
| Overview | `/` | Dashboard with stats and spending |
| Projects | `/projects` | Filterable project list |
| Ask AI | `/ask` | Natural language interface |
| Concerns | `/concerns` | Delayed and over-budget projects |
| Watchlist | `/watchlist` | Personal project tracking |
| Vendors | `/vendors` | Vendor performance |
| Analytics | `/analytics` | Spending analysis |
| Budget | `/budget-performance` | Earned Value metrics |
| Documents | `/documents` | File library |
| Executive | `/executive` | Meeting-ready view |
| Compliance | `/compliance` | Capital vs. operating |
| Public | `/public` | Citizen portal |

### Executive View Features

The `/executive` endpoint provides a clean interface for committee meetings:

- **No sidebar navigation** - Full-screen focus
- **Large numbers** - Easy to read from projector
- **Status indicators** - Green/yellow/red health signals
- **Print-friendly** - Optimized for handouts
- **Real-time data** - Always current

### Public Portal Features

The `/public` endpoint provides taxpayer transparency:

- **Read-only access** - No login required
- **Project status** - All surtax projects visible
- **Spending breakdown** - Where tax dollars go
- **Progress tracking** - Completion percentages
- **No sensitive data** - Filtered for public consumption

---

## 8. Configuration

### Environment Variables (.env)

```bash
# Application
SECRET_KEY=your-secret-key-change-in-production
SURTAX_COUNTY=marion

# Database (optional - defaults to data/surtax.db)
DATABASE_PATH=/path/to/database.db

# Email Alerts (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=app-specific-password
ALERT_EMAIL_TO=committee@example.com,admin@example.com

# Document Storage (optional)
UPLOAD_FOLDER=/path/to/uploads
```

### YAML Configuration (config/default.yaml)

```yaml
app:
  name: "School Surtax Oversight"
  version: "1.0.0"
  debug: false

server:
  host: "127.0.0.1"
  port: 5847

database:
  type: "sqlite"
  path: "data/surtax.db"

features:
  ai_chat: true
  ai_insights: true
  vendor_matching: true
  county_comparison: true
  public_portal: true
  document_upload: true
  email_alerts: false  # Requires SMTP config

compliance:
  budget_variance_alert_threshold: 10  # percent
  schedule_delay_alert_threshold: 30   # days
```

### County Configuration (config/counties/marion.yaml)

```yaml
county:
  name: "Marion County"
  fips_code: "12083"
  state: "Florida"

school_district:
  name: "Marion County Public Schools"
  superintendent: "Dr. Diane Gullett"
  board_members: 5

surtax:
  rate: 0.005  # 0.5%
  start_year: 2025
  end_year: 2035
  estimated_annual_revenue: 45000000  # $45M

spending_categories:
  - name: "New Construction"
    code: "new_construction"
  - name: "Renovation"
    code: "renovation"
  - name: "HVAC"
    code: "hvac"
  - name: "Safety & Security"
    code: "safety_security"
  # ... more categories

comparison_counties:
  - citrus
  - alachua
  - lake
  - sumter
```

---

## 9. Common Workflows

### Workflow 1: Committee Meeting Preparation

```bash
# 1. Start dashboard
python app.py

# 2. Open executive view
# Navigate to http://127.0.0.1:5847/executive

# 3. Review concerns
# Navigate to /concerns for delayed/over-budget projects

# 4. Generate report (optional)
# Navigate to /report for annual report
```

### Workflow 2: Answering Committee Questions

```python
# Use the Ask AI interface at /ask
# Or programmatically:

from app.services.ai_chat import process_question
from app.database import get_db

conn = get_db()
cursor = conn.cursor()

# Example questions
questions = [
    "What projects are behind schedule?",
    "How much budget remains?",
    "Who is our largest contractor?",
    "Which schools have the most projects?"
]

for q in questions:
    result = process_question(q, cursor)
    print(f"Q: {q}")
    print(f"A: {result['answer']}\n")
```

### Workflow 3: Adding a New Project

```sql
-- Insert via SQL (or future admin interface)
INSERT INTO contracts (
    contract_id, title, school_name, vendor_name,
    surtax_category, original_amount, current_amount,
    status, percent_complete
) VALUES (
    'CTR-2026-001',
    'Roof Replacement - Forest High School',
    'Forest High',
    'ABC Roofing Inc',
    'renovation',
    1500000,
    1500000,
    'Active',
    0
);
```

### Workflow 4: Uploading Documents

```python
# Via web interface at /documents
# Or via API:

import requests

files = {'file': open('contract.pdf', 'rb')}
data = {
    'contract_id': 'CTR-2026-001',
    'document_type': 'contract',
    'description': 'Original signed contract'
}

response = requests.post(
    'http://127.0.0.1:5847/documents/upload',
    files=files,
    data=data
)
print(response.json())
```

### Workflow 5: Configuring Email Alerts

```bash
# 1. Edit .env file
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=committee@example.com

# 2. Test alert configuration
curl -X POST http://127.0.0.1:5847/api/alerts/test

# 3. Check alert status
curl http://127.0.0.1:5847/api/alerts/status
```

### Workflow 6: Adding a New County

```bash
# 1. Create county config
cp config/counties/marion.yaml config/counties/newcounty.yaml

# 2. Edit with county-specific data
# - County name, FIPS code
# - School district info
# - Surtax details
# - Spending categories
# - Comparison counties

# 3. Start with new county
python run.py --county newcounty --port 5848
```

---

## 10. Deployment & Operations

### Windows Auto-Start

The system includes auto-start capability for Windows:

```
Location: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SurtaxDashboard.vbs
```

**To disable:**
1. Press `Win+R`
2. Type `shell:startup`
3. Delete `SurtaxDashboard.vbs`

### Production Deployment (Linux)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5847 "app:create_app('marion')"

# Or with systemd service
# See deployment/surtax-dashboard.service
```

### Database Backup

```bash
# Simple backup
cp data/surtax.db data/backups/surtax_$(date +%Y%m%d).db

# Scheduled backup (Windows Task Scheduler or cron)
# Runs daily at midnight
```

### Monitoring

The system logs to standard output. For production:

```bash
# Redirect logs
python app.py >> logs/dashboard.log 2>&1

# Or use logging configuration
# See config/logging.yaml
```

---

## Appendix A: Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `contracts` | Main projects table (45+ columns) |
| `concerns` | Issue tracking |
| `change_orders` | Contract modifications |
| `vendors` | Vendor master |
| `documents` | File metadata |
| `meeting_minutes` | Committee records |
| `audit_log` | Change tracking |

### Key Fields - contracts

| Field | Type | Purpose |
|-------|------|---------|
| `contract_id` | TEXT PK | Unique identifier |
| `title` | TEXT | Project name |
| `school_name` | TEXT | Associated school |
| `vendor_name` | TEXT | Contractor |
| `surtax_category` | TEXT | Project type |
| `original_amount` | REAL | Original budget |
| `current_amount` | REAL | Current budget |
| `total_paid` | REAL | Amount spent |
| `percent_complete` | REAL | 0-100 |
| `is_delayed` | INTEGER | Flag |
| `delay_days` | INTEGER | Days behind |
| `is_over_budget` | INTEGER | Flag |
| `budget_variance_pct` | REAL | % over/under |

---

## Appendix B: Troubleshooting

### Common Issues

**Issue: "No module named 'app'"**
```bash
# Run from project root
cd florida-school-surtax-oversight
python app.py  # Should work
```

**Issue: Database locked**
```bash
# Only one writer at a time with SQLite
# Restart the application
# Or check for stuck processes
```

**Issue: Email alerts not sending**
```bash
# Check configuration
curl http://127.0.0.1:5847/api/alerts/status

# Verify SMTP settings in .env
# Test with Gmail app-specific password
```

**Issue: Documents not uploading**
```bash
# Check file size (<50MB)
# Check file type (see allowed list)
# Verify uploads directory exists: data/uploads/
```

---

## Appendix C: API Reference

### GET /api/stats
```json
{
    "total_projects": 45,
    "total_budget": 156000000,
    "total_spent": 89000000,
    "active_projects": 28,
    "completed_projects": 12,
    "delayed_projects": 6,
    "over_budget_projects": 4
}
```

### POST /api/ask
```json
// Request
{ "question": "What projects are delayed?" }

// Response
{
    "answer": "**6 projects** are 30+ days behind schedule...",
    "data": [...],
    "suggestions": ["Which vendors?", "Delay reasons?"],
    "ask_staff": true,
    "next_step": "Request status updates"
}
```

### GET /api/alerts/status
```json
{
    "enabled": true,
    "configured": true,
    "recipients": 2
}
```

---

## Appendix D: Key Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Simple application runner |
| `run.py` | Full CLI with county selection |
| `app/__init__.py` | Flask app factory |
| `app/config.py` | Configuration loader |
| `app/database.py` | SQLite utilities |
| `app/routes/main.py` | Core dashboard routes |
| `app/routes/api.py` | JSON API endpoints |
| `app/services/ai_chat.py` | Natural language Q&A |
| `app/services/stats.py` | Statistical calculations |
| `config/default.yaml` | Default configuration |
| `config/counties/marion.yaml` | Marion County config |
| `data/surtax.db` | SQLite database |

---

*Last Updated: January 2026*
*Version: 1.0.0*
*County: Marion County, Florida*
