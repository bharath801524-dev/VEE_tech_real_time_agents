"""Clients management API router."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database.session import get_db
from app.database.models import Client

router = APIRouter()


class ClientCreate(BaseModel):
    name: str
    tier: str = "Tier-1"
    keywords: List[str] = []
    competitors: List[str] = []


def serialize_client(c: Client) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "tier": c.tier,
        "keywords": json.loads(c.keywords or "[]"),
        "competitors": json.loads(c.competitors or "[]"),
        "is_active": c.is_active,
    }


@router.get("/clients")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).filter(Client.is_active == True).all()
    return [serialize_client(c) for c in clients]


@router.post("/clients")
def create_client(body: ClientCreate, db: Session = Depends(get_db)):
    existing = db.query(Client).filter(Client.name == body.name).first()
    if existing:
        raise HTTPException(400, "Client already exists")
    client = Client(
        name=body.name,
        tier=body.tier,
        keywords=json.dumps(body.keywords),
        competitors=json.dumps(body.competitors),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return serialize_client(client)


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    client.is_active = False
    db.commit()
    return {"ok": True}
