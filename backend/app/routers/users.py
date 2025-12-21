from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from backend.app import models, schemas, auth_utils
from backend.app.database import get_db
from backend.app.dependencies import get_current_admin_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    res = await db.execute(select(models.User).where(models.User.email == user.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth_utils.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role if user.role else "tech"
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[schemas.User])
async def list_users(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    res = await db.execute(select(models.User))
    return res.scalars().all()

@router.put("/{user_id}", response_model=schemas.User)
async def update_user(user_id: int, user_update: schemas.UserUpdate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    res = await db.execute(select(models.User).where(models.User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.name:
        user.name = user_update.name
    if user_update.email and user_update.email != user.email:
         res_email = await db.execute(select(models.User).where(models.User.email == user_update.email))
         if res_email.scalar_one_or_none():
             raise HTTPException(status_code=400, detail="Email already taken")
         user.email = user_update.email
    if user_update.password:
        user.hashed_password = auth_utils.get_password_hash(user_update.password)
        
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_admin_user)):
    res = await db.execute(select(models.User).where(models.User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}
