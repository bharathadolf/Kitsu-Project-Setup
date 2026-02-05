import re

def slugify_name(name):
    """
    Convert text to lowercase snake_case (e.g., "My Project" -> "my_project").
    """
    if not name:
        return ""
    # Replace non-alphanumeric with underscore
    s = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Collapse multiple underscores
    s = re.sub(r'_+', '_', s)
    return s.strip('_').lower()

def generate_project_code(name):
    """
    Generate a project code based on name length rules:
    - < 10 chars -> 3-letter uppercase code
    - >= 10 chars -> 5-letter uppercase code (acronym based logic)
    """
    if not name:
        return "PRJ"
        
    sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', name) # Keep spaces for word splitting
    if not sanitized:
        return "PRJ"
        
    length = len(name)
    
    if length < 10:
        # First 3 alphanum chars (ignoring spaces)
        code = re.sub(r'\s', '', sanitized)[:3]
        return code.upper() if len(code) > 0 else "PRJ"
    else:
        # Acronym based (First letters of words)
        words = sanitized.split()
        acronym = "".join([w[0] for w in words if w])
        
        # If acronym is enough (>=5 chars), take first 5
        if len(acronym) >= 5:
            return acronym[:5].upper()
            
        # If acronym is short (e.g. "My Project" -> "MP"), fill with remaining letters from first word
        # Or simplistic fallback: First 5 chars of sanitized name (no spaces)
        no_spaces = re.sub(r'\s', '', sanitized)
        return no_spaces[:5].upper()

def generate_incremental_code(prefix, existing_codes, current_count=0):
    """
    Find the next available number.
    prefix: "seq", "ep"
    existing_codes: list of strings like ["seq01", "seq02"]
    current_count: how many we have already planned to create in this session
    
    Returns: string code (e.g. "seq03")
    """
    max_num = 0
    # Match prefix followed by digits (case insensitive)
    # e.g. prefix="seq", match "seq01", "SEQ03"
    pattern = re.compile(rf"^{prefix}(\d+)", re.IGNORECASE)
    
    safe_existing = existing_codes or []
    
    for code in safe_existing:
        if not code: continue
        match = pattern.search(code)
        if match:
            try:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
                
    next_num = max_num + 1 + current_count
    return f"{prefix}{next_num:02d}"

def generate_shot_code(sequence_code, shot_number):
    """
    Format: {sequence_code}_sh{n:02}
    e.g. seq01_sh01
    """
    if not sequence_code:
        sequence_code = "seqXX"
        
    return f"{sequence_code}_sh{shot_number:02d}".lower()

def generate_asset_code(asset_type_name, asset_name):
    """
    Format: {asset_type}_{asset_name}
    """
    t = slugify_name(asset_type_name)
    n = slugify_name(asset_name)
    return f"{t}_{n}"
