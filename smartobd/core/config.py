"""
Configuration management for SmartOBD
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration management class for SmartOBD"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from YAML file
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file)
            else:
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'app.name', 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Set configuration value using dot notation
        
        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """
        Save configuration to file
        
        Args:
            path: Optional path to save to (defaults to original path)
        """
        save_path = Path(path) if path else self.config_path
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(self._config, file, default_flow_style=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return self._config.copy()
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update configuration with dictionary
        
        Args:
            config_dict: Dictionary with configuration updates
        """
        self._config.update(config_dict)
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        """
        required_keys = [
            'app.name',
            'app.version',
            'database.type',
            'database.path',
            'obd.connection_type',
            'ml.model_path',
            'logging.level'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ValueError(f"Missing required configuration key: {key}")
        
        return True
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        db_type = self.get('database.type', 'sqlite')
        db_path = self.get('database.path', 'data/smartobd.db')
        
        if db_type == 'sqlite':
            return f"sqlite:///{db_path}"
        elif db_type == 'postgresql':
            host = self.get('database.host', 'localhost')
            port = self.get('database.port', 5432)
            name = self.get('database.name', 'smartobd')
            user = self.get('database.user', '')
            password = self.get('database.password', '')
            
            if user and password:
                return f"postgresql://{user}:{password}@{host}:{port}/{name}"
            else:
                return f"postgresql://{host}:{port}/{name}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def get_obd_connection_params(self) -> Dict[str, Any]:
        """Get OBD connection parameters"""
        return {
            'connection_type': self.get('obd.connection_type', 'auto'),
            'timeout': self.get('obd.timeout', 10),
            'retry_attempts': self.get('obd.retry_attempts', 3),
            'supported_commands': self.get('obd.supported_commands', [])
        }
    
    def get_ml_params(self) -> Dict[str, Any]:
        """Get machine learning parameters"""
        return {
            'model_path': self.get('ml.model_path', 'models/'),
            'training_data_path': self.get('ml.training_data_path', 'data/training/'),
            'prediction_interval_hours': self.get('ml.prediction_interval_hours', 1),
            'confidence_threshold': self.get('ml.confidence_threshold', 0.8),
            'features': self.get('ml.features', [])
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return {
            'email': self.get('notifications.email', {}),
            'sms': self.get('notifications.sms', {}),
            'push': self.get('notifications.push', {}),
            'webhook': self.get('notifications.webhook', {})
        } 