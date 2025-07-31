#!/usr/bin/env python3
"""
SmartOBD - Predictive Vehicle Maintenance Powered by OBD-II & AI
Main entry point for the application
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from smartobd.core.app import SmartOBDApp
from smartobd.core.config import Config
from smartobd.core.logger import setup_logging
from smartobd.utils.cli import CLIInterface


def main():
    """Main entry point for SmartOBD application"""
    parser = argparse.ArgumentParser(
        description="SmartOBD - Predictive Vehicle Maintenance Powered by OBD-II & AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smartobd.py --connect                    # Connect to OBD-II device
  python smartobd.py --dashboard                  # Start web dashboard
  python smartobd.py --monitor                    # Start monitoring mode
  python smartobd.py --config config_local.yaml   # Use custom config
  python smartobd.py --debug                      # Enable debug mode
        """
    )
    
    parser.add_argument(
        "--connect", 
        action="store_true", 
        help="Connect to OBD-II device and start data collection"
    )
    
    parser.add_argument(
        "--dashboard", 
        action="store_true", 
        help="Start web dashboard server"
    )
    
    parser.add_argument(
        "--monitor", 
        action="store_true", 
        help="Start monitoring mode (background data collection)"
    )
    
    parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=5000,
        help="Port for web dashboard (default: 5000)"
    )
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host for web dashboard (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="SmartOBD v1.0.0"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Setup logging
        setup_logging(
            level=args.log_level,
            log_file=config.get("logging.file_path"),
            log_format=config.get("logging.format")
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Starting SmartOBD application...")
        
        # Create application instance
        app = SmartOBDApp(config)
        
        # Handle different modes
        if args.connect:
            logger.info("Starting OBD-II connection mode...")
            app.connect_obd()
            app.start_data_collection()
            
        elif args.dashboard:
            logger.info("Starting web dashboard...")
            app.start_dashboard(host=args.host, port=args.port)
            
        elif args.monitor:
            logger.info("Starting monitoring mode...")
            app.start_monitoring()
            
        else:
            # Interactive CLI mode
            logger.info("Starting interactive CLI mode...")
            cli = CLIInterface(app)
            cli.run()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 