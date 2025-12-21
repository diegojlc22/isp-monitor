from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app import models, schemas, auth_utils
from backend.app.database import get_db
from backend.app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.Token)
async def login(request: schemas.LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not auth_utils.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = auth_utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
async def update_user_me(user_update: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user_update.name:
        current_user.name = user_update.name
    if user_update.email:
        # Check uniqueness if changing email
        if user_update.email != current_user.email:
            existing_res = await db.execute(select(models.User).where(models.User.email == user_update.email))
            existing = existing_res.scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            current_user.email = user_update.email
    if user_update.password:
        current_user.hashed_password = auth_utils.get_password_hash(user_update.password)
        
    await db.commit()
    await db.refresh(current_user)
    return current_user
