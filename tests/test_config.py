"""
Tests for configuration management
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from smartobd.core.config import Config


class TestConfig:
    """Test configuration management"""
    
    def test_config_loading(self):
        """Test configuration loading from file"""
        # Create temporary config file
        config_data = {
            'app': {
                'name': 'TestApp',
                'version': '1.0.0'
            },
            'database': {
                'type': 'sqlite',
                'path': 'test.db'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            assert config.get('app.name') == 'TestApp'
            assert config.get('app.version') == '1.0.0'
            assert config.get('database.type') == 'sqlite'
            assert config.get('database.path') == 'test.db'
            
        finally:
            Path(config_path).unlink()
    
    def test_config_defaults(self):
        """Test configuration default values"""
        config_data = {
            'app': {
                'name': 'TestApp'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Test default values
            assert config.get('app.version', 'default') == 'default'
            assert config.get('nonexistent.key', 'default') == 'default'
            
        finally:
            Path(config_path).unlink()
    
    def test_config_setting(self):
        """Test setting configuration values"""
        config_data = {'app': {'name': 'TestApp'}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Set new values
            config.set('app.version', '2.0.0')
            config.set('database.type', 'postgresql')
            
            assert config.get('app.version') == '2.0.0'
            assert config.get('database.type') == 'postgresql'
            
        finally:
            Path(config_path).unlink()
    
    def test_config_saving(self):
        """Test saving configuration to file"""
        config_data = {'app': {'name': 'TestApp'}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Set new value
            config.set('app.version', '2.0.0')
            
            # Save to new file
            new_config_path = config_path.replace('.yaml', '_new.yaml')
            config.save(new_config_path)
            
            # Load new config
            new_config = Config(new_config_path)
            assert new_config.get('app.version') == '2.0.0'
            
        finally:
            Path(config_path).unlink()
            if Path(new_config_path).exists():
                Path(new_config_path).unlink()
    
    def test_database_url_generation(self):
        """Test database URL generation"""
        config_data = {
            'database': {
                'type': 'sqlite',
                'path': 'test.db'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            config = Config(config_path)
            
            # Test SQLite URL
            url = config.get_database_url()
            assert 'sqlite:///test.db' in url
            
        finally:
            Path(config_path).unlink()
    
    def test_missing_config_file(self):
        """Test handling of missing config file"""
        with pytest.raises(FileNotFoundError):
            Config('nonexistent_config.yaml') 