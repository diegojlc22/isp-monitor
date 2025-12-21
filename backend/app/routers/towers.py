from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app.database import get_db
from backend.app.models import Tower
from backend.app.schemas import Tower as TowerSchema, TowerCreate

router = APIRouter(prefix="/towers", tags=["towers"])

@router.get("/", response_model=List[TowerSchema])
async def read_towers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tower).offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=TowerSchema)
async def create_tower(tower: TowerCreate, db: AsyncSession = Depends(get_db)):
    db_tower = Tower(**tower.model_dump())
    db.add(db_tower)
    await db.commit()
    await db.refresh(db_tower)
    return db_tower

@router.get("/{tower_id}", response_model=TowerSchema)
async def read_tower(tower_id: int, db: AsyncSession = Depends(get_db)):
    db_tower = await db.get(Tower, tower_id)
    if db_tower is None:
        raise HTTPException(status_code=404, detail="Tower not found")
    return db_tower

@router.delete("/{tower_id}")
async def delete_tower(tower_id: int, db: AsyncSession = Depends(get_db)):
    db_tower = await db.get(Tower, tower_id)
    if not db_tower:
        raise HTTPException(status_code=404, detail="Tower not found")
    await db.delete(db_tower)
    await db.commit()
    await db.commit()
    return {"message": "Tower deleted"}

# --- Network Links Endpoints ---

from backend.app.models import NetworkLink
from backend.app.schemas import NetworkLink as NetworkLinkSchema, NetworkLinkCreate

@router.get("/links", response_model=List[NetworkLinkSchema])
async def read_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NetworkLink))
    return result.scalars().all()

@router.post("/links", response_model=NetworkLinkSchema)
async def create_link(link: NetworkLinkCreate, db: AsyncSession = Depends(get_db)):
    # Check if link exists? For now simplify
    db_link = NetworkLink(**link.model_dump())
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link

@router.delete("/links/{link_id}")
async def delete_link(link_id: int, db: AsyncSession = Depends(get_db)):
    db_link = await db.get(NetworkLink, link_id)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    await db.delete(db_link)
    await db.commit()
    return {"message": "Link deleted"}
