from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import csv
import io
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

@router.post("/import_csv")
async def import_towers_csv_route(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Importa torres via arquivo CSV (formato Excel/BR suportado)"""
    try:
        content = await file.read()
        # Decode UTF-8 e remove BOM se existir
        decoded = content.decode('utf-8-sig')
        
        # Tenta detectar dialeto
        try:
            dialect = csv.Sniffer().sniff(decoded[:1024], delimiters=',;\t')
        except:
            class Dialect(csv.Dialect):
                delimiter = '\t'
                quotechar = '"'
                doublequote = True
                skipinitialspace = True
                lineterminator = '\n'
                quoting = csv.QUOTE_MINIMAL
            dialect = Dialect

        f = io.StringIO(decoded)
        reader = csv.DictReader(f, dialect=dialect)
        
        # Normalizar Colunas
        if reader.fieldnames:
            norm_names = []
            for field in reader.fieldnames:
                fname = field.lower().strip()
                if fname in ['descrição', 'descricao', 'obs']: fname = 'observacoes'
                if fname in ['lat']: fname = 'latitude'
                if fname in ['lon', 'long']: fname = 'longitude'
                norm_names.append(fname)
            reader.fieldnames = norm_names
        
        if 'nome' not in reader.fieldnames:
             raise HTTPException(status_code=400, detail="CSV deve conter coluna 'Nome'")

        imported_count = 0
        skipped_count = 0
        
        for row in reader:
            name = row.get('nome', '').strip()
            if not name: continue
            
            # Checar duplicidade (por nome)
            stmt = select(Tower).where(Tower.name == name)
            res = await db.execute(stmt)
            if res.scalars().first():
                skipped_count += 1
                continue

            lat = row.get('latitude')
            lon = row.get('longitude')
            obs = row.get('observacoes') or row.get('descricao')
            ip = row.get('ip')
            
            # Limpar Floats
            def clean_float(v):
                if not v: return None
                try: return float(str(v).replace(',', '.'))
                except: return None
            
            new_tower = Tower(
                name=name,
                latitude=clean_float(lat),
                longitude=clean_float(lon),
                ip=ip.strip() if ip else None,
                observations=obs,
                is_online=True
            )
            db.add(new_tower)
            imported_count += 1
        
        await db.commit()
        
        # Invalida cache
        await cache.delete("towers_list_0_100")
        
        return {"message": "Importação concluída", "imported": imported_count, "skipped": skipped_count}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro na importação: {str(e)}")

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
