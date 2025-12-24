from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

class Tower(Base):
    __tablename__ = "towers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip = Column(String, unique=True, index=True, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    observations = Column(Text, nullable=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc))
    
    # Hierarchy (If this tower depends on a router)
    parent_id = Column(Integer, nullable=True)

    equipments = relationship("Equipment", back_populates="tower")

class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip = Column(String, unique=True, index=True)
    tower_id = Column(Integer, ForeignKey("towers.id"), nullable=True)
    
    # Hierarchy (If this device depends on another device)
    parent_id = Column(Integer, nullable=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc))
    last_latency = Column(Integer, nullable=True) # ms
    
    # SSH Credentials
    ssh_user = Column(String, nullable=True, default="admin")
    ssh_password = Column(String, nullable=True)
    ssh_port = Column(Integer, default=22)
    
    # SNMP
    snmp_community = Column(String, default="public")
    snmp_version = Column(Integer, default=1)  # v1 for Ubiquiti compatibility
    snmp_port = Column(Integer, default=161)
    snmp_interface_index = Column(Integer, default=1) # OID index
    
    # Mikrotik API (The Dude style)
    is_mikrotik = Column(Boolean, default=False)
    mikrotik_interface = Column(String, nullable=True) # e.g. "ether1"
    api_port = Column(Integer, default=8728)
    
    # Wireless Stats (Ubiquiti/Intelbras)
    brand = Column(String, default="generic") # mikrotik, ubiquiti, intelbras, generic
    equipment_type = Column(String, default="station")  # "transmitter" or "station"
    signal_dbm = Column(Integer, nullable=True)
    ccq = Column(Integer, nullable=True)
    connected_clients = Column(Integer, nullable=True, default=0)  # For APs/Transmitters
    
    last_traffic_in = Column(Float, default=0.0) # Mbps
    last_traffic_out = Column(Float, default=0.0) # Mbps
    
    tower = relationship("Tower", back_populates="equipments")

class PingLog(Base):
    __tablename__ = "ping_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String) # 'tower' or 'equipment'
    device_id = Column(Integer)
    status = Column(Boolean) # True=Online, False=Offline
    latency_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), index=True)
    in_mbps = Column(Float)
    out_mbps = Column(Float)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), index=True)


class Parameters(Base):
    __tablename__ = "parameters"
    
    key = Column(String, primary_key=True)
    value = Column(String)

# Initial Parameters: telegram_bot_token, telegram_chat_id

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="tech") # 'admin' or 'tech'
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class NetworkLink(Base):
    __tablename__ = "network_links"

    id = Column(Integer, primary_key=True, index=True)
    source_tower_id = Column(Integer, ForeignKey("towers.id"))
    target_tower_id = Column(Integer, ForeignKey("towers.id"))
    type = Column(String, default="wireless") # wireless, fiber

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String) # 'tower' or 'equipment'
    device_name = Column(String)
    device_ip = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
