"""
OBD-II connection management
"""

import time
import threading
from typing import Dict, Any, Optional, List
import obd
from obd import OBDStatus

from ..core.logger import LoggerMixin
from ..core.config import Config


class OBDConnection(LoggerMixin):
    """OBD-II connection management class"""
    
    def __init__(self, config: Config):
        """
        Initialize OBD connection
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.connection = None
        self.is_connected_flag = False
        self.connection_lock = threading.Lock()
        
        # Get connection parameters
        params = config.get_obd_connection_params()
        self.connection_type = params['connection_type']
        self.timeout = params['timeout']
        self.retry_attempts = params['retry_attempts']
        self.supported_commands = params['supported_commands']
        
        self.logger.info(f"OBD connection initialized - Type: {self.connection_type}")
    
    def connect(self) -> bool:
        """
        Connect to OBD-II device
        
        Returns:
            True if connection successful
        """
        with self.connection_lock:
            if self.is_connected_flag:
                self.logger.info("Already connected to OBD-II device")
                return True
            
            for attempt in range(self.retry_attempts):
                try:
                    self.logger.info(f"Attempting to connect to OBD-II device (attempt {attempt + 1}/{self.retry_attempts})...")
                    
                    # Create OBD connection
                    self.connection = obd.OBD(
                        portstr=self._get_port_string(),
                        timeout=self.timeout,
                        fast=False
                    )
                    
                    # Check connection status
                    if self.connection.status() == OBDStatus.CAR_CONNECTED:
                        self.is_connected_flag = True
                        self.logger.info("Successfully connected to OBD-II device")
                        
                        # Log vehicle information
                        vehicle_info = self.get_vehicle_info()
                        if vehicle_info:
                            self.logger.info(f"Vehicle: {vehicle_info.get('make', 'Unknown')} {vehicle_info.get('model', 'Unknown')}")
                        
                        return True
                    else:
                        self.logger.warning(f"OBD connection failed - Status: {self.connection.status()}")
                        self.connection.close()
                        self.connection = None
                        
                except Exception as e:
                    self.logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                    if self.connection:
                        self.connection.close()
                        self.connection = None
                    
                    if attempt < self.retry_attempts - 1:
                        time.sleep(2)  # Wait before retry
            
            self.logger.error("Failed to connect to OBD-II device after all attempts")
            return False
    
    def disconnect(self):
        """Disconnect from OBD-II device"""
        with self.connection_lock:
            if self.connection:
                try:
                    self.connection.close()
                    self.logger.info("Disconnected from OBD-II device")
                except Exception as e:
                    self.logger.error(f"Error disconnecting: {e}")
                finally:
                    self.connection = None
                    self.is_connected_flag = False
    
    def is_connected(self) -> bool:
        """Check if connected to OBD-II device"""
        with self.connection_lock:
            return self.is_connected_flag and self.connection and self.connection.status() == OBDStatus.CAR_CONNECTED
    
    def _get_port_string(self) -> str:
        """Get port string based on connection type"""
        if self.connection_type == "auto":
            return None  # Let python-OBD auto-detect
        elif self.connection_type == "bluetooth":
            # Common Bluetooth OBD-II adapter names
            bt_names = ["OBDII", "OBD2", "ELM327", "Vgate", "iCar", "Carista"]
            for name in bt_names:
                try:
                    # This is a simplified approach - in practice you'd need proper Bluetooth discovery
                    return f"/dev/rfcomm0"  # Linux Bluetooth device
                except:
                    continue
            return None
        elif self.connection_type == "wifi":
            return "192.168.0.10:35000"  # Default WiFi OBD-II IP
        elif self.connection_type == "usb":
            return "/dev/ttyUSB0"  # Linux USB device
        else:
            return None
    
    def get_vehicle_info(self) -> Optional[Dict[str, Any]]:
        """
        Get vehicle information from OBD-II device
        
        Returns:
            Dictionary with vehicle information
        """
        if not self.is_connected():
            return None
        
        try:
            info = {}
            
            # Get VIN
            vin_response = self.connection.query(obd.commands.VIN)
            if vin_response.is_null():
                info['vin'] = None
            else:
                info['vin'] = vin_response.value
            
            # Get supported PIDs
            supported_pids = []
            for cmd in self.supported_commands:
                if hasattr(obd.commands, cmd):
                    supported_pids.append(cmd)
            
            info['supported_commands'] = supported_pids
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting vehicle info: {e}")
            return None
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current OBD-II data
        
        Returns:
            Dictionary with current sensor data
        """
        if not self.is_connected():
            return None
        
        try:
            data = {
                'timestamp': time.time(),
                'sensors': {}
            }
            
            # Query supported commands
            commands = {
                'rpm': obd.commands.RPM,
                'speed': obd.commands.SPEED,
                'engine_load': obd.commands.ENGINE_LOAD,
                'coolant_temp': obd.commands.COOLANT_TEMP,
                'intake_temp': obd.commands.INTAKE_TEMP,
                'fuel_level': obd.commands.FUEL_LEVEL,
                'throttle_position': obd.commands.THROTTLE_POS,
                'maf': obd.commands.MAF,
                'fuel_pressure': obd.commands.FUEL_PRESSURE,
                'engine_oil_temp': obd.commands.ENGINE_OIL_TEMP,
                'engine_runtime': obd.commands.ENGINE_RUNTIME,
                'distance_w_mil': obd.commands.DISTANCE_W_MIL,
                'distance_since_dtc_clear': obd.commands.DISTANCE_SINCE_DTC_CLEAR
            }
            
            for name, command in commands.items():
                try:
                    response = self.connection.query(command)
                    if not response.is_null():
                        data['sensors'][name] = response.value
                    else:
                        data['sensors'][name] = None
                except Exception as e:
                    self.logger.debug(f"Error querying {name}: {e}")
                    data['sensors'][name] = None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting current data: {e}")
            return None
    
    def get_dtc_codes(self) -> List[Dict[str, Any]]:
        """
        Get diagnostic trouble codes
        
        Returns:
            List of DTC codes
        """
        if not self.is_connected():
            return []
        
        try:
            dtc_response = self.connection.query(obd.commands.GET_DTC)
            if dtc_response.is_null():
                return []
            
            dtc_codes = []
            for code in dtc_response.value:
                dtc_codes.append({
                    'code': code.code,
                    'description': code.description,
                    'severity': code.severity
                })
            
            return dtc_codes
            
        except Exception as e:
            self.logger.error(f"Error getting DTC codes: {e}")
            return []
    
    def clear_dtc_codes(self) -> bool:
        """
        Clear diagnostic trouble codes
        
        Returns:
            True if successful
        """
        if not self.is_connected():
            return False
        
        try:
            response = self.connection.query(obd.commands.CLEAR_DTC)
            return not response.is_null()
        except Exception as e:
            self.logger.error(f"Error clearing DTC codes: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test OBD-II connection
        
        Returns:
            True if connection is working
        """
        if not self.is_connected():
            return False
        
        try:
            # Try to query a simple command
            response = self.connection.query(obd.commands.RPM)
            return not response.is_null()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False 