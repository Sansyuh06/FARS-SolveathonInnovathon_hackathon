"""
FARSverse Natural Language Command Parser
Integrates local Ollama LLM (phi3:mini) on RTX GPU with deterministic fallback.
Converts human instructions into structured simulation actions.
"""
from __future__ import annotations
import json
import os
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")


INTENT_PATTERNS = [
    (['assist', 'take care', 'help', 'attend', 'support', 'treat', 'patient'], 'assist_patient', 4),
    (['deliver', 'medicine', 'medication', 'meds', 'pills', 'supplies', 'send medicine', 'courier'], 'deliver_medicine', 4),
    (['guide', 'escort', 'lead', 'show', 'take to', 'bring to', 'visitor'], 'guide_patient', 4),
    (['check', 'inspect', 'visit', 'monitor', 'patrol', 'survey', 'look at'], 'check_room', 4),
    (['urgent', 'stat', 'emergency', 'critical', 'immediately'], 'assist_patient', 4),
    (['charge', 'recharge', 'dock', 'return to dock', 'plug in'], 'return_to_charge', 4),
    (['go to', 'send', 'move to', 'navigate to', 'dispatch'], 'assist_patient', 4),
]

LOCATION_PATTERNS = [
    (r'\broom\s*(\d+)\b', lambda m: f"Room{m.group(1)}"),
    (r'\bicu\s*(\d)\b', lambda m: f"ICU{m.group(1)}"),
    (r'\bicu\b', lambda m: "ICU1"),
    (r'\bpharmacy\b', lambda m: "Pharmacy"),
    (r'\breception\b', lambda m: "Reception"),
    (r'\bwaiting\s*hall\b', lambda m: "WaitingHall"),
    (r'\bwaiting\b', lambda m: "WaitingHall"),
    (r'\bemergency\s*(room|dept|department)?\b', lambda m: "EmergencyRoom"),
    (r'\ber\b', lambda m: "EmergencyRoom"),
    (r'\bstaff\s*(office)?\b', lambda m: "StaffOffice"),
    (r'\bcharging\s*(dock|station)?\b', lambda m: "ChargingDock"),
    (r'\bdock\b', lambda m: "ChargingDock"),
    (r'\bmain\s*hall\b', lambda m: "MainHall"),
    (r'\bentrance\b', lambda m: "Entrance"),
]


def normalize_location(loc_str: str) -> str:
    """Normalize arbitrary LLM output like 'Room 19' to 'Room19'."""
    if not loc_str:
        return "MainHall"
    loc_clean = loc_str.strip().lower()
    for pattern, extractor in LOCATION_PATTERNS:
        m = re.search(pattern, loc_clean)
        if m:
            return extractor(m)
    # Check digits
    digits = re.findall(r'\d+', loc_str)
    if digits:
        return f"Room{digits[0]}"
    return "MainHall"


def _try_ollama(command: str) -> Optional[Dict[str, Any]]:
    """Attempt parsing via local Ollama LLM endpoint."""
    try:
        url = f"{OLLAMA_HOST}/api/generate"
        system_prompt = (
            "You are the FARSverse robotics command parser. "
            "Convert the user's natural language command into a JSON object with: "
            "action ('create_task', 'pause', 'play', 'reset', 'block_corridor', 'unblock_corridor'), "
            "task_type ('assist_patient', 'deliver_medicine', 'guide_patient', 'check_room', 'return_to_charge'), "
            "location (e.g. 'Room19', 'Pharmacy', 'EmergencyRoom', 'MainHall', 'ICU1', 'Reception'), "
            "priority (always 4 for user commands), "
            "description (summary). "
            "Output RAW VALID JSON ONLY. No markdown, no prose."
        )
        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "prompt": f"{system_prompt}\nUser: {command}\nJSON:",
            "stream": False,
            "format": "json"
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5.0) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode('utf-8'))
                raw_json = res_body.get('response', '')
                parsed = json.loads(raw_json)
                raw_action = str(parsed.get('action', 'create_task')).lower()
                raw_task_type = str(parsed.get('task_type', '')).lower()
                raw_loc = parsed.get('location', '')

                # Determine simulation control action vs task creation
                if any(k in raw_action for k in ['pause', 'freeze']):
                    action = 'pause'
                elif any(k in raw_action for k in ['play', 'start', 'resume']):
                    action = 'play'
                elif any(k in raw_action for k in ['reset', 'restart']):
                    action = 'reset'
                elif 'unblock' in raw_action:
                    action = 'unblock_corridor'
                elif 'block' in raw_action:
                    action = 'block_corridor'
                else:
                    action = 'create_task'

                # Match valid task type
                task_type = 'assist_patient'
                for t in ['deliver_medicine', 'assist_patient', 'guide_patient', 'check_room', 'return_to_charge']:
                    if t in raw_action or t in raw_task_type:
                        task_type = t
                        break

                normalized_loc = normalize_location(raw_loc or raw_task_type or command)

                target_robot = parsed.get('target_robot')
                if not target_robot:
                    m_rob = re.search(r'\b(rob(?:ot)?[- ]?(\d+))\b', command, re.IGNORECASE)
                    if m_rob:
                        target_robot = f"Rob-{m_rob.group(2)}"

                return {
                    'status': 'ok',
                    'parsed_by': 'ollama',
                    'action': action,
                    'task_type': task_type,
                    'location': normalized_loc,
                    'target_robot': target_robot,
                    'priority': 4,
                    'description': parsed.get('description', command),
                    'message': f"Ollama ({OLLAMA_MODEL}) dispatched: {command}"
                }
    except Exception as e:
        # Fall back gracefully
        pass
    return None


def parse_natural_language_command(text: str) -> Dict[str, Any]:
    """Parse text command using local Ollama if online, or deterministic fallback parser."""
    text_clean = text.strip()
    if not text_clean:
        return {'status': 'error', 'message': 'Empty command provided.'}

    # 1. Instant deterministic simulation controls
    cmd_lower = text_clean.lower()
    if any(k in cmd_lower for k in ['pause', 'freeze', 'halt all', 'stop robots']):
        return {
            'status': 'ok',
            'parsed_by': 'fallback',
            'action': 'pause',
            'message': 'Simulation paused.'
        }
    if any(k in cmd_lower for k in ['resume', 'play', 'unpause', 'start simulation']):
        return {
            'status': 'ok',
            'parsed_by': 'fallback',
            'action': 'play',
            'message': 'Simulation running.'
        }
    if any(k in cmd_lower for k in ['reset world', 'restart simulation', 'reset all', 'reboot']):
        return {
            'status': 'ok',
            'parsed_by': 'fallback',
            'action': 'reset',
            'message': 'Simulation reset to scenario initial state.'
        }
    if 'block' in cmd_lower and any(w in cmd_lower for w in ['corridor', 'west', 'east', 'hall']):
        return {
            'status': 'ok',
            'parsed_by': 'fallback',
            'action': 'block_corridor',
            'message': 'Corridor obstacle blockage enabled.'
        }
    if 'unblock' in cmd_lower or 'clear obstacle' in cmd_lower:
        return {
            'status': 'ok',
            'parsed_by': 'fallback',
            'action': 'unblock_corridor',
            'message': 'Corridor obstacle blockage cleared.'
        }

    # 2. Try Ollama (phi3:mini / GPU)
    ollama_res = _try_ollama(text_clean)
    if ollama_res:
        return {'status': 'ok', **ollama_res}

    # 3. Deterministic rule-based extraction
    detected_type = 'assist_patient'
    for keywords, task_type, prio in INTENT_PATTERNS:
        if any(kw in cmd_lower for kw in keywords):
            detected_type = task_type
            break

    detected_loc = normalize_location(cmd_lower)
    target_robot = None
    m_rob = re.search(r'\b(rob(?:ot)?[- ]?(\d+))\b', cmd_lower)
    if m_rob:
        target_robot = f"Rob-{m_rob.group(2)}"

    return {
        'status': 'ok',
        'parsed_by': 'fallback',
        'action': 'create_task',
        'task_type': detected_type,
        'location': detected_loc,
        'target_robot': target_robot,
        'priority': 4,  # User commands get Critical Priority P4 to assign immediately!
        'description': f"Command: {text_clean}",
        'message': f"Interpreted action: {detected_type.replace('_', ' ').title()} at {detected_loc} (P4)"
    }
