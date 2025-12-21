from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TowerBase(BaseModel):
    name: str
    ip: Optional[str] = None
    latitude: float
    longitude: float
    observations: Optional[str] = None

class TowerCreate(TowerBase):
    pass

class Tower(TowerBase):
    id: int
    is_online: bool
    last_checked: Optional[datetime]
    
    class Config:
        from_attributes = True

class EquipmentBase(BaseModel):
    name: str
    ip: str
    tower_id: Optional[int] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    tower_id: Optional[int] = None

class Equipment(EquipmentBase):
    id: int
    is_online: bool
    last_checked: Optional[datetime]

    class Config:
        from_attributes = True

class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str

# Auth Schemas
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    password: str
    role: str = "tech"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class SystemNameUpdate(BaseModel):
    name: str
