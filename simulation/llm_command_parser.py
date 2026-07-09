"""
llm_command_parser.py -- Offline Natural Language Command Parser
Converts user commands like "deliver medicine to room 7" into structured tasks.
Fully offline -- uses keyword pattern matching (no LLM server required).
"""

import re
from navigation import get_location_node


# ---------------------------------------------------------------------------
#  Intent patterns (verb -> task_type)
# ---------------------------------------------------------------------------
INTENT_PATTERNS = [
    # (keywords, task_type, default_priority)
    (['take care', 'assist', 'help', 'attend', 'support'],       'assist_patient',   2),
    (['guide', 'escort', 'lead', 'take to', 'bring to', 'show'], 'guide_patient',    2),
    (['deliver', 'medicine', 'bring medicine', 'send medicine',
      'medication', 'meds', 'drug'],                              'deliver_medicine', 3),
    (['check', 'inspect', 'visit', 'look at', 'monitor'],        'check_room',       1),
    (['emergency', 'urgent', 'hurry', 'critical', 'stat'],       'assist_patient',   4),
    (['patrol', 'security', 'surveillance', 'monitor entrance'], 'check_room',       2),
    (['deny', 'block', 'lockdown', 'unauthorized'],              'check_room',       4),
]

# Location extraction patterns
LOCATION_PATTERNS = [
    (r'room\s*(\d+)',                     lambda m: f'Room{m.group(1)}'),
    (r'icu\s*(\d)',                        lambda m: f'ICU{m.group(1)}'),
    (r'\bicu\b',                           lambda m: 'ICU_Corr'),
    (r'\bpharmacy\b',                      lambda m: 'Pharmacy'),
    (r'\breception\b',                     lambda m: 'Reception'),
    (r'\bwaiting\s*hall\b',                lambda m: 'WaitingHall'),
    (r'\bemergency\s*(room)?\b',           lambda m: 'EmergencyRoom'),
    (r'\bstaff\s*office\b',               lambda m: 'StaffOffice'),
    (r'\bcharging\s*(dock|station)?\b',    lambda m: 'ChargingDock'),
    (r'\bmain\s*hall\b',                   lambda m: 'MainHall'),
    (r'\bentrance\b',                      lambda m: 'Entrance'),
    (r'\ber\b',                            lambda m: 'EmergencyRoom'),
]


def parse_command(text):
    """
    Parse a natural language command into a structured task dict.

    Returns:
        dict with keys: task_type, location_node, priority, description
        or None if parsing fails.
    """
    text_lower = text.strip().lower()

    if not text_lower:
        return None

    # --- Detect intent ---
    detected_type = None
    detected_priority = 1

    for keywords, task_type, priority in INTENT_PATTERNS:
        for kw in keywords:
            if kw in text_lower:
                detected_type = task_type
                detected_priority = priority
                break
        if detected_type:
            break

    # Default to check_room if no intent matched
    if not detected_type:
        detected_type = 'check_room'
        detected_priority = 1

    # --- Extract location ---
    detected_location = None

    for pattern, extractor in LOCATION_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            detected_location = extractor(m)
            break

    # If no location found, try the navigation module's fuzzy matcher
    if not detected_location:
        # Try to find any location words
        words = text_lower.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = ' '.join(words[i:j])
                node = get_location_node(phrase)
                if node:
                    detected_location = node
                    break
            if detected_location:
                break

    # Default location if nothing found
    if not detected_location:
        detected_location = 'MainHall'

    # Validate room number
    room_match = re.search(r'Room(\d+)', detected_location)
    if room_match:
        num = int(room_match.group(1))
        if num < 1 or num > 20:
            detected_location = 'MainHall'

    # If "visitor" is mentioned, change to escort_visitor
    if 'visitor' in text_lower and detected_type in ('guide_patient',):
        detected_type = 'escort_visitor'

    return {
        'task_type': detected_type,
        'location_node': detected_location,
        'priority': detected_priority,
        'description': text.strip(),
    }


def format_parse_result(result):
    """Pretty-print a parse result for debugging."""
    if not result:
        return "Could not parse command."
    return (
        f"Task: {result['task_type']}\n"
        f"Location: {result['location_node']}\n"
        f"Priority: {result['priority']}\n"
        f"Original: {result['description']}"
    )
