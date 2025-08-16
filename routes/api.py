from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.api_key import APIKey
from models.user import User
from auth_deps import get_current_user
from utils import generate_api_key

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/keys")
def get_api_keys(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    keys = db.query(APIKey).filter(APIKey.owner_id == user.id).all()
    return {"api_keys": keys}

@router.post("/keys")
def create_api_key(name: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    key_value = generate_api_key()

    new_key = APIKey(
        name=name,
        key=key_value,
        owner_id=user.id
    )

    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return {
        "message": "API key created",
        "api_key": {
            "id": new_key.id,
            "name": new_key.name,
            "key": new_key.key
        }
    }


@router.delete("/keys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key)
    db.commit()
    return {"message": "API key deleted"}

@router.get("/analytics")
def get_api_analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_calls = db.query(APIKey.total_calls).filter(APIKey.owner_id == user.id).all()
    total_errors = db.query(APIKey.total_errors).filter(APIKey.owner_id == user.id).all()
    total_success = db.query(APIKey.total_success).filter(APIKey.owner_id == user.id).all()

    return {
        "total_calls": sum(x[0] for x in total_calls),
        "total_errors": sum(x[0] for x in total_errors),
        "total_success": sum(x[0] for x in total_success),
    }

@router.get("/analytics/{key_id}")
def get_api_analytics_individual(key_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    key = db.query(APIKey).filter(APIKey.id == key_id, APIKey.owner_id == user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {
        "key_id": key.id,
        "name": key.name,
        "total_calls": key.total_calls,
        "total_errors": key.total_errors,
        "total_success": key.total_success,
    }
