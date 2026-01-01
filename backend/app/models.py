from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.database import Base

class Tower(Base):
    __tablename__ = "towers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip = Column(String, unique=True, index=True, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    observations = Column(Text, nullable=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    
    # Hierarchy (If this tower depends on a router)
    parent_id = Column(Integer, nullable=True)

    # Maintenance Mode
    maintenance_until = Column(DateTime, nullable=True)

    equipments = relationship("Equipment", back_populates="tower", cascade="all, delete-orphan")

class TowerRequest(Base):
    """Solicitações de cadastro de torre vindas do APK"""
    __tablename__ = "tower_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    ip = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    requested_by = Column(String, nullable=True) # ID técnico
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending") # pending, approved

class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    ip = Column(String, unique=True, index=True)
    mac_address = Column(String, unique=True, index=True, nullable=True) # Para topologia auto
    tower_id = Column(Integer, ForeignKey("towers.id"), nullable=True)
    
    # Contexto para APK
    is_panel = Column(Boolean, default=False) # É um painel/AP?
    associated_clients = Column(Integer, default=0) # Total clientes
    
    # Hierarchy (If this device depends on another device)
    parent_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    
    # Status
    is_online = Column(Boolean, default=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    last_ping = Column(Float, nullable=True) # Unix timestamp float
    last_latency = Column(Integer, nullable=True) # ms
    
    # Maintenance Mode
    maintenance_until = Column(DateTime, nullable=True)
    
    # SSH Credentials
    ssh_user = Column(String, nullable=True, default="admin")
    ssh_password = Column(String, nullable=True)
    ssh_port = Column(Integer, default=22)
    
    # SNMP
    snmp_community = Column(String, default="public")
    snmp_version = Column(Integer, default=1)  # v1 for Ubiquiti compatibility
    snmp_port = Column(Integer, default=161)
    snmp_interface_index = Column(Integer, default=1) 
    snmp_traffic_interface_index = Column(Integer, nullable=True) 

    # Mikrotik API (The Dude style)
    is_mikrotik = Column(Boolean, default=False)
    mikrotik_interface = Column(String, nullable=True) # e.g. "ether1"
    api_port = Column(Integer, default=8728)
    
    # Wireless Stats (Ubiquiti/Intelbras)
    brand = Column(String, default="generic") # mikrotik, ubiquiti, intelbras, generic
    equipment_type = Column(String, default="station")  # "transmitter" or "station"
    signal_dbm = Column(Float, nullable=True)
    ccq = Column(Integer, nullable=True)
    connected_clients = Column(Integer, nullable=True, default=0)  # For APs/Transmitters
    whatsapp_groups = Column(JSON, nullable=True, default=[]) # List of Group IDs

    last_traffic_in = Column(Float, default=0.0) # Mbps
    last_traffic_out = Column(Float, default=0.0) # Mbps
    
    tower = relationship("Tower", back_populates="equipments")
    # Removido relationships de logs para evitar erro de FK e overload de memória
    # Logs devem ser acessados via query direta (select)
    
    # Adjacency List Pattern (Auto-relacionamento)
    # parent: aponta para o pai (remote_side=id diz que parent_id se liga ao id da outra ponta)
    parent = relationship("Equipment", remote_side=[id], back_populates="children")
    
    # children: lista de filhos (não precisa remote_side aqui)
    children = relationship("Equipment", back_populates="parent")

class PingLog(Base):
    __tablename__ = "ping_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String) # 'tower' or 'equipment'
    device_id = Column(Integer)
    status = Column(Boolean) # True=Online, False=Offline
    latency_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), index=True)
    interface_index = Column(Integer, default=1, index=True)
    in_mbps = Column(Float)
    out_mbps = Column(Float)
    signal_dbm = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class LatencyHistory(Base):
    __tablename__ = "latency_history"
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, index=True)
    latency = Column(Float)
    packet_loss = Column(Float)
    timestamp = Column(Float, index=True)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Rastreamento do Técnico
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)

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
    timestamp = Column(DateTime, default=datetime.utcnow)

class PingStatsHourly(Base):
    """
    Rollup table for efficient historical graphs.
    Stores hourly averages instead of raw logs.
    """
    __tablename__ = "ping_stats_hourly"

    id = Column(Integer, primary_key=True, index=True)
    device_type = Column(String, index=True) # 'tower' or 'equipment'
    device_id = Column(Integer, index=True)
    avg_latency_ms = Column(Float)
    pkt_loss_percent = Column(Float) # 0.0 to 100.0
    availability_percent = Column(Float) # 0.0 to 100.0 (Uptime)
    timestamp = Column(DateTime, index=True) # The hour start time (e.g., 14:00:00)

class SyntheticLog(Base):
    """
    Logs for synthetic monitoring (DNS, HTTP, VoIP simulation).
    """
    __tablename__ = "synthetic_logs"

    id = Column(Integer, primary_key=True, index=True)
    target = Column(String) # e.g., "google.com", "8.8.8.8"
    test_type = Column(String) # "dns", "http", "voip_sim"
    
    # Metrics
    latency_ms = Column(Integer, nullable=True) # DNS resolve or HTTP TTFB
    jitter_ms = Column(Integer, nullable=True) # For VoIP
    status_code = Column(Integer, nullable=True) # For HTTP
    success = Column(Boolean, default=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class Baseline(Base):
    """
    Stores learned behavior patterns (Machine Learning/Statistics).
    Example: Correct latency for Tower X at 14:00 is 15ms +/- 5ms.
    """
    __tablename__ = "baselines"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, index=True) # Null for global tests
    metric_type = Column(String) # "ping_latency", "dns_time", "http_time"
    
    # Time bucket
    hour_of_day = Column(Integer) # 0-23
    day_of_week = Column(Integer) # 0-6 (0=Monday)
    
    # Stats
    avg_value = Column(Float)
    std_dev = Column(Float) # Standard Deviation
    sample_count = Column(Integer)
    
    last_updated = Column(DateTime, default=datetime.utcnow)

class MonitorTarget(Base):
    """
    User-defined targets for the Synthetic Agent.
    """
    __tablename__ = "monitor_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # Friendly Name (e.g. "Google DNS")
    target = Column(String, unique=True, index=True) # IP or Domain (e.g. "8.8.8.8")
    type = Column(String) # "icmp" (ping), "http", "dns"
    enabled = Column(Boolean, default=True)
