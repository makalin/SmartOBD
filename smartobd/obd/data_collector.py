"""
OBD-II data collection module
"""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.logger import LoggerMixin
from ..core.config import Config
from .connection import OBDConnection


class DataCollector(LoggerMixin):
    """OBD-II data collection class"""
    
    def __init__(self, config: Config, db_manager):
        """
        Initialize data collector
        
        Args:
            config: Application configuration
            db_manager: Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        self.obd_connection = OBDConnection(config)
        
        # Collection settings
        self.interval_seconds = config.get('data_collection.interval_seconds', 5)
        self.batch_size = config.get('data_collection.batch_size', 100)
        self.storage_format = config.get('data_collection.storage_format', 'sqlite')
        
        # Collection state
        self.is_running = False
        self.collection_thread = None
        self.data_buffer = []
        self.buffer_lock = threading.Lock()
        
        self.logger.info(f"Data collector initialized - Interval: {self.interval_seconds}s, Batch size: {self.batch_size}")
    
    def start(self):
        """Start data collection"""
        if self.is_running:
            self.logger.warning("Data collection is already running")
            return
        
        if not self.obd_connection.is_connected():
            self.logger.error("Cannot start data collection: OBD-II device not connected")
            return
        
        try:
            self.logger.info("Starting data collection...")
            self.is_running = True
            self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
            self.collection_thread.start()
            self.logger.info("Data collection started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting data collection: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop data collection"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("Stopping data collection...")
            self.is_running = False
            
            # Wait for collection thread to finish
            if self.collection_thread and self.collection_thread.is_alive():
                self.collection_thread.join(timeout=10)
            
            # Flush remaining data
            self._flush_buffer()
            
            self.logger.info("Data collection stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping data collection: {e}")
    
    def is_running(self) -> bool:
        """Check if data collection is running"""
        return self.is_running
    
    def _collection_loop(self):
        """Main data collection loop"""
        self.logger.info("Data collection loop started")
        
        while self.is_running:
            try:
                # Get current OBD data
                data = self.obd_connection.get_current_data()
                
                if data:
                    # Add metadata
                    data['collection_timestamp'] = datetime.now().isoformat()
                    data['vehicle_id'] = self._get_vehicle_id()
                    
                    # Add to buffer
                    with self.buffer_lock:
                        self.data_buffer.append(data)
                        
                        # Flush buffer if it's full
                        if len(self.data_buffer) >= self.batch_size:
                            self._flush_buffer()
                
                # Sleep for collection interval
                time.sleep(self.interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Error in data collection loop: {e}")
                time.sleep(self.interval_seconds)  # Continue after error
        
        self.logger.info("Data collection loop stopped")
    
    def _flush_buffer(self):
        """Flush data buffer to storage"""
        with self.buffer_lock:
            if not self.data_buffer:
                return
            
            try:
                data_to_save = self.data_buffer.copy()
                self.data_buffer.clear()
                
                # Save to database
                self.db_manager.save_obd_data(data_to_save)
                
                self.logger.debug(f"Flushed {len(data_to_save)} data points to storage")
                
            except Exception as e:
                self.logger.error(f"Error flushing data buffer: {e}")
                # Put data back in buffer to retry later
                with self.buffer_lock:
                    self.data_buffer.extend(data_to_save)
    
    def _get_vehicle_id(self) -> str:
        """Get vehicle identifier"""
        try:
            vehicle_info = self.obd_connection.get_vehicle_info()
            if vehicle_info and vehicle_info.get('vin'):
                return vehicle_info['vin']
            else:
                return "unknown_vehicle"
        except:
            return "unknown_vehicle"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get data collection statistics"""
        with self.buffer_lock:
            return {
                'is_running': self.is_running,
                'buffer_size': len(self.data_buffer),
                'interval_seconds': self.interval_seconds,
                'batch_size': self.batch_size,
                'storage_format': self.storage_format
            }
    
    def get_recent_data(self, limit: int = 100) -> list:
        """Get recent OBD data from database"""
        try:
            return self.db_manager.get_recent_obd_data(limit)
        except Exception as e:
            self.logger.error(f"Error getting recent data: {e}")
            return []
    
    def export_data(self, start_date: str, end_date: str, format: str = 'csv') -> str:
        """
        Export data for specified date range
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            format: Export format (csv, json)
            
        Returns:
            Path to exported file
        """
        try:
            return self.db_manager.export_obd_data(start_date, end_date, format)
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return None
    
    def clear_old_data(self, days: int = 365) -> int:
        """
        Clear old data from database
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        try:
            return self.db_manager.clear_old_obd_data(days)
        except Exception as e:
            self.logger.error(f"Error clearing old data: {e}")
            return 0 