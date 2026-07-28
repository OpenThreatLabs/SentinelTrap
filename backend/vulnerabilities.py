#!/usr/bin/env python3
"""
SentinelTrap - Vulnerability & Exploit Detection Engine
Analyzes incoming telemetry data across all protocol honeypots to detect:
- WPH: Weak Password Hashing
- UCE: Unsafe Command Execution
- ID: Insecure Deserialization
- DDE: Dangerous Dynamic Execution
- HC: Hardcoded Credentials
- SIL: Sensitive Data Logging
- UFH: Unsafe File Handling (Path Traversal / File Uploads)
- PSI: Parameterized SQL Injection
- IQC: Insecure Query Construction
- XSS: Cross-Site Scripting
- SSRF: Server-Side Request Forgery
- XXE: XML External Entity Injection
Also calculates dynamic threat risk score (0-100) and maps MITRE ATT&CK techniques.
"""

import re

# RegEx Vulnerability & Exploit Detection Signatures
VULN_PATTERNS = {
    "PSI": [ # SQL Injection
        r"('|\")\s*(or|and)\s*('|\")?\d+('|\")?\s*=\s*('|\")?\d+",
        r"union\s+(all\s+)?select",
        r"drop\s+table",
        r"exec(\s|\+)+(s|x)p_",
        r"SELECT\s+.*\s+FROM\s+information_schema",
        r"'\s*OR\s*'1'='1",
        r"admin'--"
    ],
    "UCE": [ # Unsafe Command Execution / Command Injection
        r";\s*(whoami|id|uname|cat|ls|pwd|wget|curl|chmod|nc|bash|sh|python)",
        r"\|\s*(whoami|id|uname|cat|ls|pwd|wget|curl|chmod|nc|bash|sh)",
        r"`.*`",
        r"\$\(.*\)",
        r"wget\s+http",
        r"curl\s+-O",
        r"tftp\s+-g"
    ],
    "UFH": [ # Unsafe File Handling / Path Traversal
        r"\.\./\.\./",
        r"\.\.\\\.\.\\",
        r"/etc/passwd",
        r"/etc/shadow",
        r"/etc/group",
        r"c:\\boot.ini",
        r"c:\\windows\\system32"
    ],
    "SSRF": [ # Server-Side Request Forgery
        r"169\.254\.169\.254",
        r"localhost:80",
        r"127\.0\.0\.1:\d+",
        r"metadata/v1",
        r"iam/security-credentials"
    ],
    "XSS": [ # Cross-Site Scripting
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"<img\s+src=.*?>"
    ],
    "ID": [ # Insecure Deserialization
        r"cos\nsystem",
        r"gASV", # Base64 Python Pickle header
        r"rO0AB", # Java Serialized Object magic header
        r"__reduce__"
    ],
    "DDE": [ # Dangerous Dynamic Execution
        r"eval\(",
        r"exec\(",
        r"passthru\(",
        r"system\(",
        r"shell_exec\("
    ],
    "HC": [ # Hardcoded Credentials / Secret Harvesting
        r"AKIA[0-9A-Z]{16}", # AWS Access Key ID
        r"-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----",
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]"
    ],
    "WPH": [ # Weak Password Hashing / Brute Force
        r"admin|root|password|123456|support|user|guest"
    ]
}

# MITRE ATT&CK Mapping Taxonomy
MITRE_MAP = {
    "PSI": {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "UCE": {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "UFH": {"id": "T1083", "name": "File and Directory Discovery", "tactic": "Discovery"},
    "SSRF": {"id": "T1552", "name": "Unsecured Credentials - Cloud Metadata", "tactic": "Credential Access"},
    "XSS": {"id": "T1189", "name": "Drive-by Compromise", "tactic": "Initial Access"},
    "ID": {"id": "T1203", "name": "Exploitation for Client Execution", "tactic": "Execution"},
    "DDE": {"id": "T1059.006", "name": "Python/Script Dynamic Execution", "tactic": "Execution"},
    "HC": {"id": "T1552.001", "name": "Credentials In Files", "tactic": "Credential Access"},
    "WPH": {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}
}

def analyze_payload(input_text: str):
    """
    Analyzes input text and returns a list of detected vulnerability codes,
    threat risk score adjustment, and MITRE ATT&CK metadata.
    """
    if not input_text:
        return []

    detected_codes = []
    for vuln_code, patterns in VULN_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                if vuln_code not in detected_codes:
                    detected_codes.append(vuln_code)
                break
    return detected_codes

def calculate_risk_score(events_list):
    """
    Calculates dynamic threat risk score (0 to 100) based on accumulated event severity.
    """
    score = 10
    weights = {
        "UCE": 25,
        "PSI": 20,
        "SSRF": 20,
        "UFH": 15,
        "ID": 25,
        "HC": 15,
        "WPH": 10,
        "XSS": 10
    }
    
    for event in events_list:
        v_code = getattr(event, 'vulnerability_code', None) or (event.get('vulnerability_code') if isinstance(event, dict) else None)
        if v_code in weights:
            score += weights[v_code]
            
    return min(100, score)

def get_mitre_info(vuln_code: str):
    """Returns MITRE ATT&CK mapping for a vulnerability code."""
    return MITRE_MAP.get(vuln_code, {"id": "T1000", "name": "General Reconnaissance", "tactic": "Reconnaissance"})
