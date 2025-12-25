from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app.database import get_db
from backend.app.models import Tower, NetworkLink
from backend.app.schemas import Tower as TowerSchema, TowerCreate
from backend.app.schemas import NetworkLink as NetworkLinkSchema, NetworkLinkCreate
from backend.app.services.cache import cache  # Cache para performance

router = APIRouter(prefix="/towers", tags=["towers"])

@router.get("/", response_model=List[TowerSchema])
async def read_towers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    # Tenta buscar do cache
    cache_key = f"towers_list_{skip}_{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Se não está no cache, busca do banco
    result = await db.execute(select(Tower).offset(skip).limit(limit))
    towers = result.scalars().all()
    
    # Salva no cache por 30 segundos
    await cache.set(cache_key, towers, ttl_seconds=30)
    
    return towers

@router.post("/", response_model=TowerSchema)
async def create_tower(tower: TowerCreate, db: AsyncSession = Depends(get_db)):
    db_tower = Tower(**tower.model_dump())
    db.add(db_tower)
    await db.commit()
    await db.refresh(db_tower)
    
    # Invalida o cache de torres
    await cache.delete("towers_list_0_100")
    
    return db_tower

# --- Network Links Endpoints (MUST come before /{tower_id} to avoid route conflict) ---

@router.get("/links", response_model=List[NetworkLinkSchema])
async def read_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NetworkLink))
    return result.scalars().all()

@router.post("/links", response_model=NetworkLinkSchema)
async def create_link(link: NetworkLinkCreate, db: AsyncSession = Depends(get_db)):
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

# --- Tower-specific endpoints (generic /{tower_id} must come AFTER specific routes) ---

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
    
    # Invalida o cache de torres
    await cache.delete("towers_list_0_100")
    
    return {"message": "Tower deleted"}
