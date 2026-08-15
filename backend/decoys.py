import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models

router = APIRouter(prefix="/api/decoys", tags=["Decoy Management"])

# Default list of system decoy traps
DEFAULT_DECOYS = [
    {"name": "Honey Credential File (/etc/passwd)", "type": "file", "status": "active"},
    {"name": "Decoy Database Cluster (10.0.4.18:3306)", "type": "database", "status": "active"},
    {"name": "Decoy Routing Network (10.0.4.25)", "type": "network", "status": "active"},
    {"name": "Honey Production API Keys (/etc/cloud/secrets.env)", "type": "file", "status": "inactive"}
]

def seed_default_decoys(db: Session):
    """Ensure default decoy configurations exist in the database."""
    count = db.query(models.DecoyModel).count()
    if count == 0:
        for d in DEFAULT_DECOYS:
            decoy = models.DecoyModel(
                name=d["name"],
                type=d["type"],
                status=d["status"]
            )
            db.add(decoy)
        db.commit()

@router.get("")
def list_decoys(db: Session = Depends(database.get_db)):
    """List all registered adaptive decoy traps and their current activation status."""
    seed_default_decoys(db)
    return db.query(models.DecoyModel).all()

@router.post("/trigger/{decoy_id}")
def trigger_decoy(decoy_id: int, session_id: str = None, db: Session = Depends(database.get_db)):
    """Manually activate or trigger a decoy trap for testing / live demo purposes."""
    seed_default_decoys(db)
    decoy = db.query(models.DecoyModel).filter(models.DecoyModel.id == decoy_id).first()
    if not decoy:
        raise HTTPException(status_code=404, detail=f"Decoy trap '{decoy_id}' not found")

    decoy.status = "active"
    decoy.activated_at = datetime.datetime.utcnow()
    if session_id:
        decoy.triggered_by_session = session_id
    db.commit()
    db.refresh(decoy)

    return {"status": "success", "message": f"Decoy '{decoy.name}' activated", "decoy": decoy}

@router.post("/reset/{decoy_id}")
def reset_decoy(decoy_id: int, db: Session = Depends(database.get_db)):
    """Reset a decoy trap status back to inactive."""
    seed_default_decoys(db)
    decoy = db.query(models.DecoyModel).filter(models.DecoyModel.id == decoy_id).first()
    if not decoy:
        raise HTTPException(status_code=404, detail=f"Decoy trap '{decoy_id}' not found")

    decoy.status = "inactive"
    decoy.triggered_by_session = None
    db.commit()

    return {"status": "success", "message": f"Decoy '{decoy.name}' reset to inactive"}
