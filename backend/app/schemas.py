from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TowerBase(BaseModel):
    name: str
    ip: Optional[str] = None
    latitude: float
    longitude: float
    observations: Optional[str] = None
    parent_id: Optional[int] = None

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
    parent_id: Optional[int] = None
    ssh_user: str = "admin"
    ssh_port: int = 22
    snmp_community: str = "public"
    snmp_version: int = 1  # Default to v1 for Ubiquiti compatibility
    snmp_port: int = 161
    snmp_interface_index: int = 1
    # Mikrotik
    is_mikrotik: bool = False
    mikrotik_interface: Optional[str] = None
    api_port: int = 8728
    # Wireless
    brand: str = "generic"
    equipment_type: str = "station"  # "transmitter" or "station"
    signal_dbm: Optional[int] = None
    ccq: Optional[int] = None

class EquipmentCreate(EquipmentBase):
    ssh_password: Optional[str] = None

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    tower_id: Optional[int] = None
    parent_id: Optional[int] = None
    ssh_user: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_port: Optional[int] = None
    snmp_community: Optional[str] = None
    snmp_version: Optional[int] = None
    snmp_port: Optional[int] = None
    snmp_interface_index: Optional[int] = None
    is_mikrotik: Optional[bool] = None
    mikrotik_interface: Optional[str] = None
    api_port: Optional[int] = None
    brand: Optional[str] = None
    equipment_type: Optional[str] = None
    signal_dbm: Optional[int] = None
    ccq: Optional[int] = None

class Equipment(EquipmentBase):
    id: int
    is_online: bool
    last_checked: Optional[datetime]
    # We do NOT return ssh_password for security, only user/port
    
    class Config:
        from_attributes = True

class TelegramConfig(BaseModel):
    bot_token: str
    chat_id: str
    backup_chat_id: Optional[str] = None
    template_down: Optional[str] = None
    template_up: Optional[str] = None

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
    last_latitude: Optional[float] = None
    last_longitude: Optional[float] = None
    last_location_update: Optional[datetime] = None
    
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

class LatencyThresholds(BaseModel):
    good: int # ms, e.g. 50
    critical: int # ms, e.g. 200

class NetworkLinkBase(BaseModel):
    source_tower_id: int
    target_tower_id: int
    type: str = "wireless"

class NetworkLinkCreate(NetworkLinkBase):
    pass

class NetworkLink(NetworkLinkBase):
    id: int
    
    class Config:
        from_attributes = True
