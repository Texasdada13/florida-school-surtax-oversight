# Florida School Surtax Oversight Dashboard

A template-based oversight dashboard for Florida school district surtax monitoring. Built to help Citizen Oversight Committees track how half-cent sales tax funds are being spent on school capital projects.

## Features

### Core Functionality
- **Project Tracking** - Monitor all surtax-funded projects with budget, schedule, and completion status
- **Vendor Performance** - Track contractor performance with on-time and on-budget metrics
- **Risk Dashboard** - Identify critical and high-risk projects requiring attention
- **AI-Powered Q&A** - Ask natural language questions about project data
- **Budget Performance** - Compare proposed vs actual spending against project progress

### Monitoring Tools
- **Concerns Tracking** - Log and resolve issues identified during oversight
- **Watchlist** - Personal list of projects to monitor closely
- **Alerts & Notifications** - Automated alerts for delays and budget overruns
- **Audit Trail** - Track all changes for compliance

### Financial Analysis
- **Change Orders** - Track contract modifications and their impact
- **Analytics** - Spending trends, forecasts, and category breakdowns
- **Capital vs Operating** - Ensure surtax funds are used only for capital expenditures

### Documents & Reports
- **Document Library** - Centralized storage for contracts, invoices, reports
- **Meeting Minutes** - Archive of oversight committee meetings
- **Annual Report** - Generate required annual reports

### Public Tools
- **Public Portal** - Citizen-facing transparency view
- **Map View** - Geographic visualization of project locations
- **Meeting Mode** - Presentation-ready view for committee meetings

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/florida-school-surtax-oversight.git
cd florida-school-surtax-oversight

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the application
python run.py
```

The dashboard will be available at http://127.0.0.1:5847

### Configuration

1. Copy `config/counties/_template.yaml` to `config/counties/yourcounty.yaml`
2. Customize the configuration for your county
3. Run with `python run.py --county yourcounty`

## Multi-County Support

This dashboard is designed as a template that can be deployed for any Florida county with a school surtax. Each county has its own configuration file in `config/counties/`.

### Creating a New County Configuration

```yaml
# config/counties/citrus.yaml
county:
  name: "Citrus"
  full_name: "Citrus County"
  state: "FL"

school_district:
  name: "Citrus County Schools"

surtax:
  rate: 0.5
  start_year: 2025
  end_year: 2035
  estimated_annual_revenue: 25000000
```

## Project Structure

```
florida-school-surtax-oversight/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration loader
│   ├── database.py          # Database utilities
│   ├── routes/              # Route blueprints
│   │   ├── main.py          # Overview, projects, schools
│   │   ├── monitoring.py    # Concerns, watchlist, risk
│   │   ├── financials.py    # Vendors, change orders, analytics
│   │   ├── documents.py     # Document library, minutes
│   │   ├── tools.py         # Meeting mode, compliance, map
│   │   └── api.py           # JSON API endpoints
│   ├── services/            # Business logic
│   │   ├── stats.py         # Statistical calculations
│   │   ├── ai_chat.py       # Natural language Q&A
│   │   ├── ai_insights.py   # ML-based insights
│   │   └── vendor_matching.py
│   └── templates/           # Jinja2 templates
├── config/
│   ├── default.yaml         # Default configuration
│   └── counties/            # County-specific configs
├── data/
│   └── schemas/             # Database schemas
├── docs/                    # Documentation
├── run.py                   # Application entry point
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ask` | POST | Natural language question processing |
| `/api/projects` | GET | List all projects |
| `/api/stats` | GET | Dashboard statistics |
| `/api/watchlist` | GET | Get user's watchlist |
| `/api/watchlist/toggle/<id>` | POST | Toggle project in watchlist |

## Compliance

This dashboard helps oversight committees meet Florida statutory requirements:
- Track that surtax funds are used only for capital expenditures
- Monitor budget and schedule adherence
- Maintain audit trail of all changes
- Generate required annual reports

## License

MIT License - See LICENSE file for details.

## Support

For questions or issues, please open a GitHub issue or contact your county's IT department.
