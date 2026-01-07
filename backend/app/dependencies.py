from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app import models, schemas, auth_utils
from backend.app.config import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("Token validation failed: 'sub' claim missing")
            raise HTTPException(status_code=401, detail="Could not validate credentials: sub missing")
        token_data = schemas.TokenData(email=email)
    except JWTError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {str(e)}")
        
    try:
        result = await db.execute(select(models.User).where(models.User.email == token_data.email))
        user = result.scalar_one_or_none()
        
        if user is None:
            logger.warning(f"Token valid but user not found in DB: {token_data.email}")
            raise HTTPException(status_code=401, detail="Session invalid: user not found")
        return user
    except Exception as e:
        logger.error(f"Database error during user validation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")

async def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
