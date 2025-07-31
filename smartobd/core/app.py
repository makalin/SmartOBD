"""
Main SmartOBD application class
"""

import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path

from .config import Config
from .logger import LoggerMixin
from ..obd.connection import OBDConnection
from ..obd.data_collector import DataCollector
from ..ml.predictor import MaintenancePredictor
from ..database.manager import DatabaseManager
from ..notifications.manager import NotificationManager
from ..web.dashboard import DashboardServer


class SmartOBDApp(LoggerMixin):
    """Main SmartOBD application class"""
    
    def __init__(self, config: Config):
        """
        Initialize SmartOBD application
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.logger.info("Initializing SmartOBD application...")
        
        # Initialize components
        self.db_manager = DatabaseManager(config)
        self.obd_connection = OBDConnection(config)
        self.data_collector = DataCollector(config, self.db_manager)
        self.predictor = MaintenancePredictor(config, self.db_manager)
        self.notification_manager = NotificationManager(config)
        self.dashboard_server = DashboardServer(config, self.db_manager)
        
        # Application state
        self.is_running = False
        self.monitoring_thread = None
        self.collection_thread = None
        
        self.logger.info("SmartOBD application initialized successfully")
    
    def connect_obd(self) -> bool:
        """
        Connect to OBD-II device
        
        Returns:
            True if connection successful
        """
        try:
            self.logger.info("Attempting to connect to OBD-II device...")
            success = self.obd_connection.connect()
            
            if success:
                self.logger.info("Successfully connected to OBD-II device")
                return True
            else:
                self.logger.error("Failed to connect to OBD-II device")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to OBD-II device: {e}")
            return False
    
    def disconnect_obd(self):
        """Disconnect from OBD-II device"""
        try:
            self.logger.info("Disconnecting from OBD-II device...")
            self.obd_connection.disconnect()
            self.logger.info("Disconnected from OBD-II device")
        except Exception as e:
            self.logger.error(f"Error disconnecting from OBD-II device: {e}")
    
    def start_data_collection(self):
        """Start data collection from OBD-II device"""
        if not self.obd_connection.is_connected():
            self.logger.error("Cannot start data collection: OBD-II device not connected")
            return
        
        try:
            self.logger.info("Starting data collection...")
            self.data_collector.start()
            self.logger.info("Data collection started successfully")
        except Exception as e:
            self.logger.error(f"Error starting data collection: {e}")
    
    def stop_data_collection(self):
        """Stop data collection"""
        try:
            self.logger.info("Stopping data collection...")
            self.data_collector.stop()
            self.logger.info("Data collection stopped")
        except Exception as e:
            self.logger.error(f"Error stopping data collection: {e}")
    
    def start_monitoring(self):
        """Start monitoring mode (background data collection and prediction)"""
        if self.is_running:
            self.logger.warning("Monitoring is already running")
            return
        
        try:
            self.logger.info("Starting monitoring mode...")
            
            # Connect to OBD-II device
            if not self.connect_obd():
                raise RuntimeError("Failed to connect to OBD-II device")
            
            # Start data collection
            self.start_data_collection()
            
            # Start monitoring thread
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            self.logger.info("Monitoring mode started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring mode: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring mode"""
        try:
            self.logger.info("Stopping monitoring mode...")
            
            self.is_running = False
            
            # Stop data collection
            self.stop_data_collection()
            
            # Disconnect from OBD-II device
            self.disconnect_obd()
            
            # Wait for monitoring thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.logger.info("Monitoring mode stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring mode: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Monitoring loop started")
        
        while self.is_running:
            try:
                # Run predictions
                self.predictor.run_predictions()
                
                # Check for maintenance alerts
                alerts = self.predictor.get_maintenance_alerts()
                if alerts:
                    self.notification_manager.send_alerts(alerts)
                
                # Sleep for prediction interval
                interval_hours = self.config.get('ml.prediction_interval_hours', 1)
                time.sleep(interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        self.logger.info("Monitoring loop stopped")
    
    def start_dashboard(self, host: str = "0.0.0.0", port: int = 5000):
        """Start web dashboard server"""
        try:
            self.logger.info(f"Starting web dashboard on {host}:{port}...")
            self.dashboard_server.start(host=host, port=port)
        except Exception as e:
            self.logger.error(f"Error starting web dashboard: {e}")
    
    def stop_dashboard(self):
        """Stop web dashboard server"""
        try:
            self.logger.info("Stopping web dashboard...")
            self.dashboard_server.stop()
            self.logger.info("Web dashboard stopped")
        except Exception as e:
            self.logger.error(f"Error stopping web dashboard: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get application status"""
        return {
            'is_running': self.is_running,
            'obd_connected': self.obd_connection.is_connected(),
            'data_collection_active': self.data_collector.is_running(),
            'dashboard_running': self.dashboard_server.is_running(),
            'database_connected': self.db_manager.is_connected(),
            'last_prediction': self.predictor.get_last_prediction_time(),
            'pending_alerts': len(self.predictor.get_maintenance_alerts())
        }
    
    def get_vehicle_info(self) -> Optional[Dict[str, Any]]:
        """Get vehicle information from OBD-II device"""
        if not self.obd_connection.is_connected():
            return None
        
        try:
            return self.obd_connection.get_vehicle_info()
        except Exception as e:
            self.logger.error(f"Error getting vehicle info: {e}")
            return None
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get current OBD-II data"""
        if not self.obd_connection.is_connected():
            return None
        
        try:
            return self.obd_connection.get_current_data()
        except Exception as e:
            self.logger.error(f"Error getting current data: {e}")
            return None
    
    def get_maintenance_predictions(self) -> Dict[str, Any]:
        """Get maintenance predictions"""
        try:
            return self.predictor.get_predictions()
        except Exception as e:
            self.logger.error(f"Error getting maintenance predictions: {e}")
            return {}
    
    def shutdown(self):
        """Shutdown application gracefully"""
        self.logger.info("Shutting down SmartOBD application...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Stop dashboard
        self.stop_dashboard()
        
        # Close database connection
        self.db_manager.close()
        
        self.logger.info("SmartOBD application shutdown complete") 