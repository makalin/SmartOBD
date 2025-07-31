"""
Command Line Interface for SmartOBD
"""

import cmd
import sys
from typing import Dict, Any
from colorama import init, Fore, Style

from ..core.logger import LoggerMixin


class CLIInterface(LoggerMixin):
    """Interactive CLI interface for SmartOBD"""
    
    def __init__(self, app):
        """
        Initialize CLI interface
        
        Args:
            app: SmartOBD application instance
        """
        self.app = app
        init()  # Initialize colorama
        
        self.logger.info("CLI interface initialized")
    
    def run(self):
        """Start interactive CLI"""
        print(f"{Fore.CYAN}🚗 SmartOBD - Predictive Vehicle Maintenance{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Type 'help' for available commands{Style.RESET_ALL}")
        print()
        
        try:
            while True:
                try:
                    command = input(f"{Fore.GREEN}SmartOBD> {Style.RESET_ALL}").strip()
                    
                    if not command:
                        continue
                    
                    if command.lower() in ['quit', 'exit', 'q']:
                        print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                        break
                    
                    self._process_command(command)
                    
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Use 'quit' to exit{Style.RESET_ALL}")
                except EOFError:
                    break
                    
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
        finally:
            self.app.shutdown()
    
    def _process_command(self, command: str):
        """Process CLI command"""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == 'help':
            self._show_help()
        elif cmd == 'status':
            self._show_status()
        elif cmd == 'connect':
            self._connect_obd()
        elif cmd == 'disconnect':
            self._disconnect_obd()
        elif cmd == 'start':
            self._start_monitoring()
        elif cmd == 'stop':
            self._stop_monitoring()
        elif cmd == 'dashboard':
            self._start_dashboard(args)
        elif cmd == 'data':
            self._show_data(args)
        elif cmd == 'alerts':
            self._show_alerts(args)
        elif cmd == 'predictions':
            self._show_predictions()
        elif cmd == 'train':
            self._train_models(args)
        elif cmd == 'export':
            self._export_data(args)
        elif cmd == 'clear':
            self._clear_data(args)
        elif cmd == 'test':
            self._test_notifications()
        elif cmd == 'config':
            self._show_config()
        else:
            print(f"{Fore.RED}Unknown command: {cmd}{Style.RESET_ALL}")
            print(f"Type 'help' for available commands")
    
    def _show_help(self):
        """Show help information"""
        help_text = f"""
{Fore.CYAN}Available Commands:{Style.RESET_ALL}

{Fore.GREEN}System Commands:{Style.RESET_ALL}
  status                    - Show system status
  connect                   - Connect to OBD-II device
  disconnect                - Disconnect from OBD-II device
  start                     - Start monitoring mode
  stop                      - Stop monitoring mode
  dashboard [port]          - Start web dashboard (default port: 5000)

{Fore.GREEN}Data Commands:{Style.RESET_ALL}
  data [limit]              - Show recent OBD data (default: 10 records)
  alerts [resolved]         - Show maintenance alerts (add 'resolved' for resolved alerts)
  predictions               - Show maintenance predictions
  export [start_date] [end_date] [format] - Export data (format: csv/json)

{Fore.GREEN}ML Commands:{Style.RESET_ALL}
  train [vehicle_id]        - Train maintenance prediction models

{Fore.GREEN}Utility Commands:{Style.RESET_ALL}
  clear [days]              - Clear old data (default: 365 days)
  test                      - Test notification systems
  config                    - Show configuration
  help                      - Show this help
  quit/exit/q               - Exit application

{Fore.YELLOW}Examples:{Style.RESET_ALL}
  SmartOBD> connect
  SmartOBD> start
  SmartOBD> dashboard 8080
  SmartOBD> data 50
  SmartOBD> export 2023-01-01 2023-12-31 csv
"""
        print(help_text)
    
    def _show_status(self):
        """Show system status"""
        try:
            status = self.app.get_status()
            
            print(f"\n{Fore.CYAN}System Status:{Style.RESET_ALL}")
            print(f"  Application Running: {self._format_status(status['is_running'])}")
            print(f"  OBD Connected: {self._format_status(status['obd_connected'])}")
            print(f"  Data Collection: {self._format_status(status['data_collection_active'])}")
            print(f"  Dashboard Running: {self._format_status(status['dashboard_running'])}")
            print(f"  Database Connected: {self._format_status(status['database_connected'])}")
            print(f"  Pending Alerts: {status['pending_alerts']}")
            
            if status['last_prediction']:
                print(f"  Last Prediction: {status['last_prediction']}")
            
        except Exception as e:
            print(f"{Fore.RED}Error getting status: {e}{Style.RESET_ALL}")
    
    def _connect_obd(self):
        """Connect to OBD-II device"""
        print(f"{Fore.YELLOW}Connecting to OBD-II device...{Style.RESET_ALL}")
        
        try:
            success = self.app.connect_obd()
            if success:
                print(f"{Fore.GREEN}Successfully connected to OBD-II device{Style.RESET_ALL}")
                
                # Show vehicle info
                vehicle_info = self.app.get_vehicle_info()
                if vehicle_info:
                    print(f"{Fore.CYAN}Vehicle Information:{Style.RESET_ALL}")
                    if vehicle_info.get('vin'):
                        print(f"  VIN: {vehicle_info['vin']}")
                    if vehicle_info.get('supported_commands'):
                        print(f"  Supported Commands: {len(vehicle_info['supported_commands'])}")
            else:
                print(f"{Fore.RED}Failed to connect to OBD-II device{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Error connecting: {e}{Style.RESET_ALL}")
    
    def _disconnect_obd(self):
        """Disconnect from OBD-II device"""
        print(f"{Fore.YELLOW}Disconnecting from OBD-II device...{Style.RESET_ALL}")
        
        try:
            self.app.disconnect_obd()
            print(f"{Fore.GREEN}Disconnected from OBD-II device{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error disconnecting: {e}{Style.RESET_ALL}")
    
    def _start_monitoring(self):
        """Start monitoring mode"""
        print(f"{Fore.YELLOW}Starting monitoring mode...{Style.RESET_ALL}")
        
        try:
            self.app.start_monitoring()
            print(f"{Fore.GREEN}Monitoring mode started{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error starting monitoring: {e}{Style.RESET_ALL}")
    
    def _stop_monitoring(self):
        """Stop monitoring mode"""
        print(f"{Fore.YELLOW}Stopping monitoring mode...{Style.RESET_ALL}")
        
        try:
            self.app.stop_monitoring()
            print(f"{Fore.GREEN}Monitoring mode stopped{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error stopping monitoring: {e}{Style.RESET_ALL}")
    
    def _start_dashboard(self, args):
        """Start web dashboard"""
        port = int(args[0]) if args else 5000
        
        print(f"{Fore.YELLOW}Starting web dashboard on port {port}...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Open your browser to: http://localhost:{port}{Style.RESET_ALL}")
        
        try:
            self.app.start_dashboard(port=port)
            print(f"{Fore.GREEN}Dashboard started successfully{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error starting dashboard: {e}{Style.RESET_ALL}")
    
    def _show_data(self, args):
        """Show recent OBD data"""
        limit = int(args[0]) if args else 10
        
        try:
            data = self.app.data_collector.get_recent_data(limit)
            
            if not data:
                print(f"{Fore.YELLOW}No data available{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}Recent OBD Data (Last {len(data)} records):{Style.RESET_ALL}")
            
            for i, record in enumerate(data[:5]):  # Show first 5 records
                print(f"\n{Fore.GREEN}Record {i+1}:{Style.RESET_ALL}")
                print(f"  Timestamp: {record.get('timestamp', 'N/A')}")
                print(f"  RPM: {record.get('rpm', 'N/A')}")
                print(f"  Speed: {record.get('speed', 'N/A')} km/h")
                print(f"  Engine Load: {record.get('engine_load', 'N/A')}%")
                print(f"  Coolant Temp: {record.get('coolant_temp', 'N/A')}°C")
                print(f"  Fuel Level: {record.get('fuel_level', 'N/A')}%")
            
            if len(data) > 5:
                print(f"\n{Fore.YELLOW}... and {len(data) - 5} more records{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Error getting data: {e}{Style.RESET_ALL}")
    
    def _show_alerts(self, args):
        """Show maintenance alerts"""
        show_resolved = 'resolved' in args
        
        try:
            alerts = self.app.predictor.get_maintenance_alerts()
            
            if not alerts:
                status = "resolved" if show_resolved else "active"
                print(f"{Fore.YELLOW}No {status} alerts{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}Maintenance Alerts:{Style.RESET_ALL}")
            
            for alert in alerts:
                if show_resolved == alert.get('is_resolved', False):
                    continue
                
                severity_color = {
                    'low': Fore.GREEN,
                    'medium': Fore.YELLOW,
                    'high': Fore.RED,
                    'critical': Fore.MAGENTA
                }.get(alert.get('severity', 'medium'), Fore.YELLOW)
                
                print(f"\n{severity_color}{alert['alert_type'].replace('_', ' ').title()}{Style.RESET_ALL}")
                print(f"  Message: {alert.get('message', 'N/A')}")
                print(f"  Severity: {alert.get('severity', 'N/A')}")
                print(f"  Confidence: {alert.get('confidence', 0):.1%}")
                print(f"  Created: {alert.get('created_at', 'N/A')}")
                
        except Exception as e:
            print(f"{Fore.RED}Error getting alerts: {e}{Style.RESET_ALL}")
    
    def _show_predictions(self):
        """Show maintenance predictions"""
        try:
            predictions = self.app.get_maintenance_predictions()
            
            if not predictions:
                print(f"{Fore.YELLOW}No predictions available{Style.RESET_ALL}")
                return
            
            print(f"\n{Fore.CYAN}Maintenance Predictions:{Style.RESET_ALL}")
            
            for maintenance_type, prediction in predictions.items():
                status = "Loaded" if prediction.get('model_loaded') else "Not Loaded"
                color = Fore.GREEN if prediction.get('model_loaded') else Fore.RED
                
                print(f"  {maintenance_type.replace('_', ' ').title()}: {color}{status}{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Error getting predictions: {e}{Style.RESET_ALL}")
    
    def _train_models(self, args):
        """Train maintenance prediction models"""
        vehicle_id = args[0] if args else None
        
        print(f"{Fore.YELLOW}Training maintenance prediction models...{Style.RESET_ALL}")
        
        try:
            self.app.predictor.train_models(vehicle_id)
            print(f"{Fore.GREEN}Model training completed{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error training models: {e}{Style.RESET_ALL}")
    
    def _export_data(self, args):
        """Export data"""
        if len(args) < 2:
            print(f"{Fore.RED}Usage: export <start_date> <end_date> [format]{Style.RESET_ALL}")
            print(f"Example: export 2023-01-01 2023-12-31 csv")
            return
        
        start_date = args[0]
        end_date = args[1]
        format = args[2] if len(args) > 2 else 'csv'
        
        print(f"{Fore.YELLOW}Exporting data from {start_date} to {end_date}...{Style.RESET_ALL}")
        
        try:
            filepath = self.app.data_collector.export_data(start_date, end_date, format)
            if filepath:
                print(f"{Fore.GREEN}Data exported to: {filepath}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Export failed{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error exporting data: {e}{Style.RESET_ALL}")
    
    def _clear_data(self, args):
        """Clear old data"""
        days = int(args[0]) if args else 365
        
        print(f"{Fore.YELLOW}Clearing data older than {days} days...{Style.RESET_ALL}")
        
        try:
            deleted_count = self.app.data_collector.clear_old_data(days)
            print(f"{Fore.GREEN}Cleared {deleted_count} old records{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error clearing data: {e}{Style.RESET_ALL}")
    
    def _test_notifications(self):
        """Test notification systems"""
        print(f"{Fore.YELLOW}Testing notification systems...{Style.RESET_ALL}")
        
        try:
            results = self.app.notification_manager.test_notifications()
            
            print(f"\n{Fore.CYAN}Notification Test Results:{Style.RESET_ALL}")
            for method, success in results.items():
                color = Fore.GREEN if success else Fore.RED
                status = "PASS" if success else "FAIL"
                print(f"  {method.title()}: {color}{status}{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}Error testing notifications: {e}{Style.RESET_ALL}")
    
    def _show_config(self):
        """Show configuration"""
        try:
            config = self.app.config.get_all()
            
            print(f"\n{Fore.CYAN}Configuration:{Style.RESET_ALL}")
            print(f"  App Name: {config.get('app', {}).get('name', 'N/A')}")
            print(f"  Version: {config.get('app', {}).get('version', 'N/A')}")
            print(f"  Database: {config.get('database', {}).get('type', 'N/A')}")
            print(f"  OBD Connection: {config.get('obd', {}).get('connection_type', 'N/A')}")
            print(f"  Log Level: {config.get('logging', {}).get('level', 'N/A')}")
            
        except Exception as e:
            print(f"{Fore.RED}Error getting configuration: {e}{Style.RESET_ALL}")
    
    def _format_status(self, status: bool) -> str:
        """Format status for display"""
        if status:
            return f"{Fore.GREEN}✓{Style.RESET_ALL}"
        else:
            return f"{Fore.RED}✗{Style.RESET_ALL}" 