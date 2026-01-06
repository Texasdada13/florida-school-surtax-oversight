-- Florida School Surtax Oversight Dashboard
-- Database Schema

-- Main contracts/projects table
CREATE TABLE IF NOT EXISTS contracts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,

    -- School/Location
    school_name TEXT,
    school_id TEXT,

    -- Vendor Information
    vendor_name TEXT,
    vendor_type TEXT,           -- Local, Regional, National, Publicly Traded
    vendor_size TEXT,           -- Small, Medium, Large, Enterprise
    vendor_headquarters TEXT,

    -- Classification
    surtax_category TEXT,       -- New Construction, HVAC, Safety & Security, etc.
    expenditure_type TEXT,      -- Capital, Operating

    -- Financial
    original_amount REAL,
    current_amount REAL,
    amount_paid REAL DEFAULT 0,
    budget_variance_amount REAL DEFAULT 0,
    budget_variance_pct REAL DEFAULT 0,

    -- Schedule
    original_start_date TEXT,
    original_end_date TEXT,
    current_start_date TEXT,
    current_end_date TEXT,

    -- Status
    status TEXT DEFAULT 'Planned',  -- Planned, Active, Complete, On Hold
    percent_complete REAL DEFAULT 0,

    -- Flags
    is_delayed INTEGER DEFAULT 0,
    delay_days INTEGER DEFAULT 0,
    delay_reason TEXT,
    is_over_budget INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,

    -- Metadata
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Concerns/Issues tracking
CREATE TABLE IF NOT EXISTS concerns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,              -- Budget, Schedule, Quality, Compliance, Other
    severity TEXT,              -- Low, Medium, High, Critical
    status TEXT DEFAULT 'Open', -- Open, Under Review, Resolved, Closed
    resolution TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    resolved_date TEXT,
    created_by TEXT,
    resolved_by TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- Change orders / contract modifications
CREATE TABLE IF NOT EXISTS change_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT NOT NULL,
    change_order_number TEXT,
    description TEXT,
    reason TEXT,
    original_value REAL,
    change_value REAL,
    new_value REAL,
    schedule_impact_days INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected
    requested_date TEXT,
    approved_date TEXT,
    approved_by TEXT,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- Vendors master table (for enhanced vendor tracking)
CREATE TABLE IF NOT EXISTS vendors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    dba_name TEXT,
    vendor_type TEXT,           -- Local, Regional, National, Publicly Traded
    vendor_size TEXT,           -- Small (<$1M), Medium, Large, Enterprise
    headquarters_city TEXT,
    headquarters_state TEXT,
    years_in_business INTEGER,
    bonding_capacity REAL,
    certifications TEXT,        -- JSON array: MBE, WBE, DBE, etc.
    license_number TEXT,
    insurance_expiry TEXT,
    performance_rating REAL,    -- Calculated 0-100
    notes TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for tracking changes
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,       -- INSERT, UPDATE, DELETE
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,
    changed_date TEXT DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT
);

-- Meeting minutes
CREATE TABLE IF NOT EXISTS meeting_minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_date TEXT NOT NULL,
    meeting_type TEXT,          -- Regular, Special, Emergency
    location TEXT,
    attendees TEXT,             -- JSON array
    agenda TEXT,
    minutes TEXT,
    decisions TEXT,             -- JSON array of decisions made
    action_items TEXT,          -- JSON array of action items
    status TEXT DEFAULT 'Draft', -- Draft, Approved
    approved_date TEXT,
    document_path TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id TEXT,
    title TEXT NOT NULL,
    document_type TEXT,         -- Contract, Invoice, Inspection, Report, Other
    file_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    description TEXT,
    uploaded_by TEXT,
    uploaded_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contracts_school ON contracts(school_name);
CREATE INDEX IF NOT EXISTS idx_contracts_vendor ON contracts(vendor_name);
CREATE INDEX IF NOT EXISTS idx_contracts_category ON contracts(surtax_category);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_delayed ON contracts(is_delayed);
CREATE INDEX IF NOT EXISTS idx_concerns_contract ON concerns(contract_id);
CREATE INDEX IF NOT EXISTS idx_concerns_status ON concerns(status);
CREATE INDEX IF NOT EXISTS idx_change_orders_contract ON change_orders(contract_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name, record_id);
