import threading, json, urllib.request
from sim_navigation import get_all_nodes

VALID_TASKS = {'assist_patient', 'deliver_medicine', 'guide_patient', 'security_check'}
_ollama_model = None
_valid_locs = None
pending_results = []

def _locs():
    global _valid_locs
    if _valid_locs is None:
        _valid_locs = set(get_all_nodes().keys())
    return _valid_locs

def detect_model():
    global _ollama_model
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        d = json.loads(r.read().decode())
        names = [m['name'] for m in d.get('models', [])]
        for pref in ['llama3.2','llama3.1','llama3','mistral','gemma2','phi3','qwen2']:
            for n in names:
                if pref in n.lower():
                    _ollama_model = n
                    return n
        if names:
            _ollama_model = names[0]
            return names[0]
    except Exception:
        pass
    _ollama_model = None
    return None

def get_model_name():
    return _ollama_model or 'FALLBACK'

def _fallback(text):
    tl = text.lower()
    tn = tl.replace(' ', '')
    r = {'task_type':'security_check','location_node':'MainHall','priority':2,'description':text}
    if any(w in tl for w in ['medicine','deliver','pill','drug']):
        r['task_type']='deliver_medicine'
        r['priority']=3
    elif any(w in tl for w in ['guide','escort','show','take']):
        r['task_type']='guide_patient'
        r['priority']=1
    elif any(w in tl for w in ['emergency','urgent','stat','help']):
        r['task_type']='assist_patient'
        r['priority']=4
    for node in _locs():
        if node.lower() in tn:
            r['location_node'] = node
            break
    else:
        aliases = {'er':'EmergencyRoom','emergency':'EmergencyRoom','reception':'Reception',
                   'waiting':'WaitingHall','hall':'MainHall','dock':'ChargingDock','pharmacy':'Pharmacy'}
        for a, v in aliases.items():
            if a in tl:
                r['location_node'] = v
                break
    r['_src'] = 'fallback'
    return r

def _validate(p, text):
    if p.get('task_type') not in VALID_TASKS:
        p['task_type']='security_check'
    loc = str(p.get('location_node','')).replace(' ','')
    if loc not in _locs():
        fb = _fallback(text)
        loc = fb['location_node']
    p['location_node'] = loc
    pri = p.get('priority', 2)
    if not isinstance(pri, int) or pri < 1 or pri > 4:
        pri = 2
    p['priority'] = pri
    if not p.get('description'):
        p['description'] = text
    return p

def _query_thread(text):
    prompt = f"""You are the AI brain of a hospital digital twin. Parse the user command into JSON.
FORMAT: {{"task_type":"assist_patient"|"deliver_medicine"|"guide_patient"|"security_check","location_node":"<node>","priority":<1-4>,"description":"<summary>"}}
LOCATIONS: Room1-Room20, ICU1-ICU4, Pharmacy, EmergencyRoom, Reception, WaitingHall, MainHall, ChargingDock, StaffOffice, Entrance
RULES: "go to room 5"->Room5, "room 12"->Room12 (no space). "go to X"->security_check.
COMMAND: "{text}"
Reply ONLY valid JSON."""
    data = json.dumps({"model":_ollama_model,"prompt":prompt,"stream":False,"format":"json"}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=data,
                                 headers={'Content-Type':'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        rj = json.loads(resp.read().decode())
        parsed = json.loads(rj.get("response","{}"))
        parsed = _validate(parsed, text)
        parsed['_src'] = 'ollama'
        pending_results.append(parsed)
    except Exception:
        pending_results.append(_fallback(text))

def submit_command(text):
    if _ollama_model:
        threading.Thread(target=_query_thread, args=(text,), daemon=True).start()
    else:
        pending_results.append(_fallback(text))

def poll_results():
    out = list(pending_results)
    pending_results.clear()
    return out

detect_model()
