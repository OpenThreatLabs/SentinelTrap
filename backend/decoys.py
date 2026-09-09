from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/decoys", tags=["Decoy Management"])

# Adaptive Server Persona Presets
# Solves supervisor's feedback: "Hackers will know if all ports are open"
PERSONAS = {
    "web_app": {
        "id": "web_app",
        "name": "Cloud Web Application Server (LAMP/Nginx)",
        "description": "Exposes standard public web tiers while masking all database and backend ports.",
        "active_ports": [8080, 2222],
        "active_decoys": ["SSH Honeypot", "Web Application Trap"],
        "simulated_os": "Debian 11 / Apache 2.4.56"
    },
    "database_cluster": {
        "id": "database_cluster",
        "name": "Internal Enterprise Database Node",
        "description": "Simulates an internal backend database cluster. Conceals web and mail services.",
        "active_ports": [3306, 6379, 2222],
        "active_decoys": ["SSH Honeypot", "MySQL Decoy", "Redis Decoy"],
        "simulated_os": "Ubuntu 22.04 LTS / MySQL 8.0 & Redis 7.0"
    },
    "mail_gateway": {
        "id": "mail_gateway",
        "name": "Edge Mail & DNS Gateway",
        "description": "Presents an authoritative perimeter mail router. Exposes strictly SMTP and DNS.",
        "active_ports": [2525, 5353, 2222],
        "active_decoys": ["SSH Honeypot", "SMTP Honeypot", "DNS Honeypot"],
        "simulated_os": "CentOS 7 / Postfix 3.5.8"
    },
    "iot_router": {
        "id": "iot_router",
        "name": "IoT Edge Router & Gateway (Cisco/BusyBox)",
        "description": "Simulates an embedded IoT gateway running BusyBox. Traps automated Mirai/Mozi botnet brute-forcing on Telnet.",
        "active_ports": [2223, 8080],
        "active_decoys": ["Telnet Trap", "Web Application Trap"],
        "simulated_os": "Embedded Linux / BusyBox v1.33 (MIPS/ARM)"
    },
    "all_mesh": {
        "id": "all_mesh",
        "name": "Full Deception Mesh (Global Research Trap)",
        "description": "Simulates all 9 protocol services simultaneously for wide-spectrum threat intelligence collection.",
        "active_ports": [2222, 2223, 8080, 2121, 2525, 3306, 6379, 5353, 3389],
        "active_decoys": [
            "SSH Honeypot", "Telnet Trap", "Web Application Trap",
            "FTP Honeypot", "SMTP Honeypot", "MySQL Decoy",
            "Redis Decoy", "DNS Honeypot", "Port Scanner / RDP"
        ],
        "simulated_os": "Unified Multi-Layer Deception Matrix"
    }
}

# Current in-memory active persona (Defaults to all_mesh)
current_persona_id = "all_mesh"

@router.get("/personas")
def get_personas():
    """Returns available adaptive server personas and the currently active profile."""
    return {
        "current_persona": current_persona_id,
        "personas": list(PERSONAS.values())
    }

@router.post("/personas/{persona_id}")
def set_active_persona(persona_id: str):
    """Dynamically switch the active deception persona on the fly."""
    global current_persona_id
    if persona_id not in PERSONAS:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found")
    
    current_persona_id = persona_id
    return {
        "status": "success",
        "message": f"Active persona switched to {PERSONAS[persona_id]['name']}",
        "active_persona": PERSONAS[persona_id]
    }

