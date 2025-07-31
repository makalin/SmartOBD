"""
Database management for SmartOBD
"""

import os
import sqlite3
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..core.logger import LoggerMixin
from ..core.config import Config
from .models import Base, OBDData, MaintenanceAlert, VehicleInfo


class DatabaseManager(LoggerMixin):
    """Database management class for SmartOBD"""
    
    def __init__(self, config: Config):
        """
        Initialize database manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self.db_path = config.get('database.path', 'data/smartobd.db')
        
        self.logger.info(f"Database manager initialized - Path: {self.db_path}")
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Create database directory if it doesn't exist
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Create database engine
            database_url = self.config.get_database_url()
            self.engine = create_engine(database_url, echo=False)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except:
            return False
    
    def save_obd_data(self, data_list: List[Dict[str, Any]]):
        """
        Save OBD data to database
        
        Args:
            data_list: List of OBD data dictionaries
        """
        if not data_list:
            return
        
        session = self.get_session()
        try:
            for data_dict in data_list:
                # Create OBDData object
                obd_data = OBDData(
                    timestamp=datetime.fromisoformat(data_dict.get('collection_timestamp', datetime.now().isoformat())),
                    vehicle_id=data_dict.get('vehicle_id', 'unknown'),
                    rpm=data_dict.get('sensors', {}).get('rpm'),
                    speed=data_dict.get('sensors', {}).get('speed'),
                    engine_load=data_dict.get('sensors', {}).get('engine_load'),
                    coolant_temp=data_dict.get('sensors', {}).get('coolant_temp'),
                    intake_temp=data_dict.get('sensors', {}).get('intake_temp'),
                    fuel_level=data_dict.get('sensors', {}).get('fuel_level'),
                    throttle_position=data_dict.get('sensors', {}).get('throttle_position'),
                    maf=data_dict.get('sensors', {}).get('maf'),
                    fuel_pressure=data_dict.get('sensors', {}).get('fuel_pressure'),
                    engine_oil_temp=data_dict.get('sensors', {}).get('engine_oil_temp'),
                    engine_runtime=data_dict.get('sensors', {}).get('engine_runtime'),
                    distance_w_mil=data_dict.get('sensors', {}).get('distance_w_mil'),
                    distance_since_dtc_clear=data_dict.get('sensors', {}).get('distance_since_dtc_clear'),
                    raw_data=json.dumps(data_dict)
                )
                
                session.add(obd_data)
            
            session.commit()
            self.logger.debug(f"Saved {len(data_list)} OBD data records")
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error saving OBD data: {e}")
            raise
        finally:
            session.close()
    
    def get_recent_obd_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent OBD data from database
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of OBD data dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(OBDData).order_by(OBDData.timestamp.desc()).limit(limit)
            records = query.all()
            
            return [record.to_dict() for record in records]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting recent OBD data: {e}")
            return []
        finally:
            session.close()
    
    def get_obd_data_range(self, start_date: datetime, end_date: datetime, vehicle_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get OBD data for date range
        
        Args:
            start_date: Start date
            end_date: End date
            vehicle_id: Optional vehicle ID filter
            
        Returns:
            List of OBD data dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(OBDData).filter(
                OBDData.timestamp >= start_date,
                OBDData.timestamp <= end_date
            )
            
            if vehicle_id:
                query = query.filter(OBDData.vehicle_id == vehicle_id)
            
            records = query.order_by(OBDData.timestamp.asc()).all()
            return [record.to_dict() for record in records]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting OBD data range: {e}")
            return []
        finally:
            session.close()
    
    def save_maintenance_alert(self, alert_data: Dict[str, Any]):
        """
        Save maintenance alert to database
        
        Args:
            alert_data: Maintenance alert data
        """
        session = self.get_session()
        try:
            alert = MaintenanceAlert(
                vehicle_id=alert_data.get('vehicle_id', 'unknown'),
                alert_type=alert_data.get('type'),
                severity=alert_data.get('severity', 'medium'),
                message=alert_data.get('message'),
                predicted_date=datetime.fromisoformat(alert_data.get('predicted_date')) if alert_data.get('predicted_date') else None,
                confidence=alert_data.get('confidence', 0.0),
                is_resolved=alert_data.get('is_resolved', False),
                created_at=datetime.now()
            )
            
            session.add(alert)
            session.commit()
            
            self.logger.info(f"Saved maintenance alert: {alert_data.get('type')}")
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error saving maintenance alert: {e}")
            raise
        finally:
            session.close()
    
    def get_maintenance_alerts(self, vehicle_id: Optional[str] = None, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get maintenance alerts from database
        
        Args:
            vehicle_id: Optional vehicle ID filter
            resolved: Optional resolved status filter
            
        Returns:
            List of maintenance alert dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(MaintenanceAlert)
            
            if vehicle_id:
                query = query.filter(MaintenanceAlert.vehicle_id == vehicle_id)
            
            if resolved is not None:
                query = query.filter(MaintenanceAlert.is_resolved == resolved)
            
            records = query.order_by(MaintenanceAlert.created_at.desc()).all()
            return [record.to_dict() for record in records]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting maintenance alerts: {e}")
            return []
        finally:
            session.close()
    
    def export_obd_data(self, start_date: str, end_date: str, format: str = 'csv') -> str:
        """
        Export OBD data to file
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            format: Export format (csv, json)
            
        Returns:
            Path to exported file
        """
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            data = self.get_obd_data_range(start_dt, end_dt)
            
            if not data:
                self.logger.warning("No data found for export")
                return None
            
            # Create export directory
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"obd_data_{start_date[:10]}_{end_date[:10]}_{timestamp}.{format}"
            filepath = export_dir / filename
            
            if format == 'csv':
                self._export_to_csv(data, filepath)
            elif format == 'json':
                self._export_to_json(data, filepath)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(data)} records to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return None
    
    def _export_to_csv(self, data: List[Dict[str, Any]], filepath: Path):
        """Export data to CSV file"""
        if not data:
            return
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def _export_to_json(self, data: List[Dict[str, Any]], filepath: Path):
        """Export data to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, default=str)
    
    def clear_old_obd_data(self, days: int = 365) -> int:
        """
        Clear old OBD data from database
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = session.query(OBDData).filter(OBDData.timestamp < cutoff_date).delete()
            session.commit()
            
            self.logger.info(f"Deleted {deleted_count} old OBD data records")
            return deleted_count
            
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error clearing old data: {e}")
            return 0
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        try:
            obd_count = session.query(OBDData).count()
            alert_count = session.query(MaintenanceAlert).count()
            unresolved_alerts = session.query(MaintenanceAlert).filter(MaintenanceAlert.is_resolved == False).count()
            
            # Get date range
            first_record = session.query(OBDData).order_by(OBDData.timestamp.asc()).first()
            last_record = session.query(OBDData).order_by(OBDData.timestamp.desc()).first()
            
            return {
                'total_obd_records': obd_count,
                'total_alerts': alert_count,
                'unresolved_alerts': unresolved_alerts,
                'first_record_date': first_record.timestamp.isoformat() if first_record else None,
                'last_record_date': last_record.timestamp.isoformat() if last_record else None,
                'database_size_mb': self._get_database_size()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            session.close()
    
    def _get_database_size(self) -> float:
        """Get database file size in MB"""
        try:
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except:
            return 0.0
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed") 