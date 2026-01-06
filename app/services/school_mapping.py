"""
School Name Mapping Service

Automatically maps projects to schools based on title patterns,
location data, and known school names in Marion County.
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple

# Known Marion County Schools - ordered by specificity (more specific first)
MARION_COUNTY_SCHOOLS = [
    # High Schools (check these FIRST to avoid matching elementary)
    "Belleview Senior High",
    "Belleview High",
    "Dunnellon Senior High",
    "Dunnellon High",
    "Forest High",
    "Lake Weir High",
    "North Marion High",
    "Vanguard High",
    "West Port High",

    # Middle Schools
    "Belleview Middle",
    "Dunnellon Middle",
    "Fort King Middle",
    "Horizon Academy at Marion Oaks",
    "Howard Middle",
    "Lake Weir Middle",
    "Liberty Middle",
    "North Marion Middle",
    "Osceola Middle",
    "West Port Middle",

    # Elementary Schools
    "Anthony Elementary",
    "Belleview Elementary",
    "Belleview-Santos Elementary",
    "College Park Elementary",
    "Dr. N.H. Jones Elementary",
    "Dunnellon Elementary",
    "East Marion Elementary",
    "Emerald Shores Elementary",
    "Evergreen Elementary",
    "Fessenden Elementary",
    "Fort McCoy School",
    "Greenway Elementary",
    "Hammett Bowen Jr. Elementary",
    "Harbour View Elementary",
    "Hillcrest School",
    "Maplewood Elementary",
    "Marion Oaks Elementary",
    "Oakcrest Elementary",
    "Ocala Springs Elementary",
    "Reddick-Collier Elementary",
    "Romeo Elementary",
    "Shady Hill Elementary",
    "Sparr Elementary",
    "Stanton-Weirsdale Elementary",
    "Sunrise Elementary",
    "Ward-Highlands Elementary",
    "Wyomina Park Elementary",

    # Other Facilities
    "Marion Technical College",
    "Marion County School District",
]

# Alternate names/aliases for schools
SCHOOL_ALIASES = {
    "dunnellon senior high": "Dunnellon High",
    "belleview senior high": "Belleview High",
    "lake weir senior high": "Lake Weir High",
    "west port senior high": "West Port High",
    "north marion senior high": "North Marion High",
    "forest senior high": "Forest High",
    "vanguard senior high": "Vanguard High",
    "hammett bowen": "Hammett Bowen Jr. Elementary",
    "lake weir sr high": "Lake Weir High",
    "north marion sr high": "North Marion High",
    "public safety": "District-Wide",
    "cop debt service": "District-Wide",
}

# Patterns that indicate district-wide projects
DISTRICT_WIDE_PATTERNS = [
    r"district[- ]?wide",
    r"all schools",
    r"all marion county schools",
    r"county[- ]?wide",
    r"multiple schools",
    r"various schools",
    r"school bus",
    r"transportation",
    r"fleet",
    r"district technology",
    r"central office",
]

# Patterns for new construction (unnamed schools)
NEW_CONSTRUCTION_PATTERNS = [
    r"new (?:elementary|middle|high) school [\"']?([A-Z]{1,3})[\"']?",
    r"school [\"']?([A-Z]{1,3})[\"']?",
    r"elementary [\"']?([A-Z])[\"']?",
]


def extract_school_from_title(title: str) -> Optional[str]:
    """
    Extract school name from contract title using pattern matching.

    Returns:
        School name if found, None otherwise
    """
    if not title:
        return None

    title_lower = title.lower()

    # Check for district-wide patterns first
    for pattern in DISTRICT_WIDE_PATTERNS:
        if re.search(pattern, title_lower):
            return "District-Wide"

    # Check for aliases first (e.g., "Dunnellon Senior High" -> "Dunnellon High")
    for alias, canonical in SCHOOL_ALIASES.items():
        if alias in title_lower:
            return canonical

    # Check for known school names (list is ordered by specificity)
    for school in MARION_COUNTY_SCHOOLS:
        # Create pattern that matches school name with optional suffixes
        school_pattern = re.escape(school.lower())
        if re.search(school_pattern, title_lower):
            return school

    # Check for new construction patterns - improved regex
    new_school_patterns = [
        # "New Southwest Elementary W" or "New SW Elementary 'W'"
        r"new\s+(?:sw\s+|southwest\s+)?(?:elementary|middle|high)\s+(?:school\s+)?[\"']?([A-Z]{1,3})[\"']?",
        # "New High School CCC" or "New Middle School DD"
        r"new\s+(?:high|middle|elementary)\s+school\s+[\"']?([A-Z]{1,4})[\"']?",
        # "School DD" or "Elementary X"
        r"(?:school|elementary|middle|high)\s+[\"']([A-Z]{1,3})[\"']",
    ]

    for pattern in new_school_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
            # Determine type from title
            if "elementary" in title_lower:
                school_type = "Elementary"
            elif "middle" in title_lower:
                school_type = "Middle School"
            elif "high" in title_lower:
                school_type = "High School"
            else:
                school_type = "School"
            return f"New {school_type} \"{letter}\" (Planned)"

    # Check for partial matches (just the main part of school name)
    # Only if the name part is sufficiently unique
    for school in MARION_COUNTY_SCHOOLS:
        parts = school.split()
        # Get the main identifier (e.g., "Hammett Bowen" from "Hammett Bowen Jr. Elementary")
        main_part = parts[0].lower()
        # Only match if it's a distinctive name (not generic like "North" or "West")
        if len(main_part) > 5 and main_part not in ["north", "south", "east", "west", "lake"]:
            if main_part in title_lower:
                return school

    return None


def extract_school_from_location(location: str) -> Optional[str]:
    """
    Extract school information from location field.
    """
    if not location:
        return None

    location_lower = location.lower()

    # Check for district-wide patterns
    for pattern in DISTRICT_WIDE_PATTERNS:
        if re.search(pattern, location_lower):
            return "District-Wide"

    # Check for known school names
    for school in MARION_COUNTY_SCHOOLS:
        if school.lower() in location_lower:
            return school

    return None


def map_school_for_contract(
    title: str,
    location: Optional[str],
    surtax_category: Optional[str]
) -> Tuple[Optional[str], str]:
    """
    Determine school name for a contract.

    Returns:
        Tuple of (school_name, confidence) where confidence is 'high', 'medium', or 'low'
    """
    # Try title first
    school = extract_school_from_title(title)
    if school:
        return school, "high"

    # Try location
    if location:
        school = extract_school_from_location(location)
        if school:
            return school, "medium"

    # Category-based defaults
    if surtax_category in ("safety_security", "technology"):
        # These are often district-wide
        if location and "all" in location.lower():
            return "District-Wide", "medium"

    return None, "low"


def auto_map_schools(cursor: sqlite3.Cursor) -> Dict[str, int]:
    """
    Automatically map school names for contracts missing them.

    Returns:
        Dictionary with mapping statistics
    """
    stats = {
        "total_unmapped": 0,
        "mapped_high": 0,
        "mapped_medium": 0,
        "still_unmapped": 0,
    }

    # Get contracts without school names
    cursor.execute('''
        SELECT contract_id, title, project_location, surtax_category
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND (school_name IS NULL OR school_name = '')
    ''')

    unmapped = cursor.fetchall()
    stats["total_unmapped"] = len(unmapped)

    for row in unmapped:
        contract_id, title, location, category = row
        school, confidence = map_school_for_contract(title, location, category)

        if school:
            cursor.execute('''
                UPDATE contracts
                SET school_name = ?
                WHERE contract_id = ?
            ''', (school, contract_id))

            if confidence == "high":
                stats["mapped_high"] += 1
            else:
                stats["mapped_medium"] += 1
        else:
            stats["still_unmapped"] += 1

    return stats


def get_unmapped_contracts(cursor: sqlite3.Cursor) -> List[Dict]:
    """
    Get list of contracts that still need manual school mapping.
    """
    cursor.execute('''
        SELECT contract_id, title, project_location, surtax_category, current_amount
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND (school_name IS NULL OR school_name = '')
        ORDER BY current_amount DESC
    ''')

    return [
        {
            "contract_id": row[0],
            "title": row[1],
            "location": row[2],
            "category": row[3],
            "amount": row[4],
        }
        for row in cursor.fetchall()
    ]


def get_school_list() -> List[str]:
    """Return list of all known schools for dropdown selection."""
    return ["District-Wide"] + sorted(MARION_COUNTY_SCHOOLS)
