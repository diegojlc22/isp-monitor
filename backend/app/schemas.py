from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import json

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
    snmp_traffic_interface_index: Optional[int] = None
    # Mikrotik
    is_mikrotik: bool = False
    mikrotik_interface: Optional[str] = None
    api_port: int = 8728
    # Wireless
    brand: str = "generic"
    equipment_type: str = "station"  # "transmitter" or "station"
    signal_dbm: Optional[float] = None
    ccq: Optional[int] = None
    connected_clients: Optional[int] = None
    cpu_usage: Optional[int] = None
    memory_usage: Optional[int] = None
    disk_usage: Optional[int] = None
    temperature: Optional[float] = None
    voltage: Optional[float] = None
    is_priority: bool = False  # Mark for priority monitoring
    last_traffic_in: Optional[float] = None
    last_traffic_out: Optional[float] = None
    max_traffic_in: Optional[float] = None
    max_traffic_out: Optional[float] = None
    traffic_alert_interval: int = 360
    min_voltage_threshold: Optional[float] = 16.0
    voltage_alert_interval: int = 360
    voltage_multiplier: float = 1.0
    voltage_offset: float = 0.0
    whatsapp_groups: Optional[List[str]] = []

    @validator('whatsapp_groups', pre=True)
    def parse_whatsapp_groups(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        if v is None:
            return []
        return v

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
    snmp_traffic_interface_index: Optional[int] = None
    is_mikrotik: Optional[bool] = None
    mikrotik_interface: Optional[str] = None
    api_port: Optional[int] = None
    brand: Optional[str] = None
    equipment_type: Optional[str] = None
    signal_dbm: Optional[float] = None
    ccq: Optional[int] = None
    connected_clients: Optional[int] = None
    is_priority: Optional[bool] = None  # Priority monitoring flag
    max_traffic_in: Optional[float] = None
    max_traffic_out: Optional[float] = None
    traffic_alert_interval: Optional[int] = None
    min_voltage_threshold: Optional[float] = None
    voltage_alert_interval: Optional[int] = None
    voltage_multiplier: Optional[float] = None
    voltage_offset: Optional[float] = None
    whatsapp_groups: Optional[List[str]] = None

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
    template_traffic: Optional[str] = None
    # No more legacy fields
    # Config Multi-Canal
    telegram_enabled: Optional[bool] = True
    whatsapp_enabled: Optional[bool] = False
    whatsapp_target: Optional[str] = None 
    whatsapp_target_group: Optional[str] = None
    whatsapp_group_battery: Optional[str] = None # Grupo específico Bateria
    whatsapp_group_ai: Optional[str] = None # Grupo específico IA
    
    # Notification Types
    notify_equipment_status: Optional[bool] = True
    notify_backups: Optional[bool] = True
    notify_agent: Optional[bool] = True

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
    source_equipment_id: Optional[int] = None
    target_equipment_id: Optional[int] = None
    type: str = "wireless"

class NetworkLinkCreate(NetworkLinkBase):
    pass

class NetworkLink(NetworkLinkBase):
    id: int
    source_equipment_name: Optional[str] = None
    target_equipment_name: Optional[str] = None
    
    class Config:
        from_attributes = True
