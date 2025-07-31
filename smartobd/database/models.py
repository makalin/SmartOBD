"""
SQLAlchemy database models for SmartOBD
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class OBDData(Base):
    """OBD-II sensor data model"""
    __tablename__ = 'obd_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    
    # Engine data
    rpm = Column(Float)
    speed = Column(Float)
    engine_load = Column(Float)
    coolant_temp = Column(Float)
    intake_temp = Column(Float)
    fuel_level = Column(Float)
    throttle_position = Column(Float)
    maf = Column(Float)  # Mass Air Flow
    fuel_pressure = Column(Float)
    engine_oil_temp = Column(Float)
    engine_runtime = Column(Float)
    
    # Distance data
    distance_w_mil = Column(Float)  # Distance with MIL on
    distance_since_dtc_clear = Column(Float)  # Distance since DTC clear
    
    # Raw data storage
    raw_data = Column(Text)  # JSON string of complete data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'vehicle_id': self.vehicle_id,
            'rpm': self.rpm,
            'speed': self.speed,
            'engine_load': self.engine_load,
            'coolant_temp': self.coolant_temp,
            'intake_temp': self.intake_temp,
            'fuel_level': self.fuel_level,
            'throttle_position': self.throttle_position,
            'maf': self.maf,
            'fuel_pressure': self.fuel_pressure,
            'engine_oil_temp': self.engine_oil_temp,
            'engine_runtime': self.engine_runtime,
            'distance_w_mil': self.distance_w_mil,
            'distance_since_dtc_clear': self.distance_since_dtc_clear,
            'raw_data': self.raw_data
        }


class MaintenanceAlert(Base):
    """Maintenance alert model"""
    __tablename__ = 'maintenance_alerts'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)  # oil_change, tire_rotation, etc.
    severity = Column(String(20), default='medium')  # low, medium, high, critical
    message = Column(Text, nullable=False)
    predicted_date = Column(DateTime)
    confidence = Column(Float, default=0.0)  # ML prediction confidence
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'predicted_date': self.predicted_date.isoformat() if self.predicted_date else None,
            'confidence': self.confidence,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VehicleInfo(Base):
    """Vehicle information model"""
    __tablename__ = 'vehicle_info'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), unique=True, nullable=False, index=True)
    vin = Column(String(17))  # Vehicle Identification Number
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    engine_type = Column(String(50))
    transmission_type = Column(String(50))
    fuel_type = Column(String(50))
    mileage = Column(Float)
    last_service_date = Column(DateTime)
    service_history = Column(JSON)  # JSON array of service records
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'vin': self.vin,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'engine_type': self.engine_type,
            'transmission_type': self.transmission_type,
            'fuel_type': self.fuel_type,
            'mileage': self.mileage,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'service_history': self.service_history,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MaintenanceSchedule(Base):
    """Maintenance schedule model"""
    __tablename__ = 'maintenance_schedules'
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    maintenance_type = Column(String(100), nullable=False)  # oil_change, tire_rotation, etc.
    interval_miles = Column(Float, nullable=False)
    interval_months = Column(Integer)
    last_service_miles = Column(Float)
    last_service_date = Column(DateTime)
    next_service_miles = Column(Float)
    next_service_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'maintenance_type': self.maintenance_type,
            'interval_miles': self.interval_miles,
            'interval_months': self.interval_months,
            'last_service_miles': self.last_service_miles,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'next_service_miles': self.next_service_miles,
            'next_service_date': self.next_service_date.isoformat() if self.next_service_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MLModel(Base):
    """Machine learning model metadata"""
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # maintenance_prediction, anomaly_detection, etc.
    model_version = Column(String(20), nullable=False)
    file_path = Column(String(255), nullable=False)
    accuracy = Column(Float)
    training_date = Column(DateTime)
    features_used = Column(JSON)  # List of features used in training
    hyperparameters = Column(JSON)  # Model hyperparameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_type': self.model_type,
            'model_version': self.model_version,
            'file_path': self.file_path,
            'accuracy': self.accuracy,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'features_used': self.features_used,
            'hyperparameters': self.hyperparameters,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 