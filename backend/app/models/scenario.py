from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text
from app.database import Base


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    apply_to_next_only = Column(Boolean, default=False, nullable=False)
    route_id = Column(String(36), nullable=True)  # Optional target route
    parameters = Column(Text, nullable=True)  # JSON string of options
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
