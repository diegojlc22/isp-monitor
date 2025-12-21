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
    
    equipments = relationship("Equipment", back_populates="tower")

class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip = Column(String, unique=True, index=True)
    tower_id = Column(Integer, ForeignKey("towers.id"), nullable=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc))
    
    tower = relationship("Tower", back_populates="equipments")

class PingLog(Base):
    __tablename__ = "ping_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String) # 'tower' or 'equipment'
    device_id = Column(Integer)
    status = Column(Boolean) # True=Online, False=Offline
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))

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
