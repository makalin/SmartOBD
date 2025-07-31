"""
Web dashboard server for SmartOBD
"""

import threading
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from ..core.logger import LoggerMixin
from ..core.config import Config


class DashboardServer(LoggerMixin):
    """Web dashboard server for SmartOBD"""
    
    def __init__(self, config: Config, db_manager):
        """
        Initialize dashboard server
        
        Args:
            config: Application configuration
            db_manager: Database manager instance
        """
        self.config = config
        self.db_manager = db_manager
        
        # Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = config.get('app.secret_key', 'smartobd-secret-key')
        
        # Enable CORS
        CORS(self.app)
        
        # SocketIO for real-time updates
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Server state
        self.server_thread = None
        self.is_running = False
        self.host = config.get('app.host', '0.0.0.0')
        self.port = config.get('app.port', 5000)
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("Dashboard server initialized")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return self._render_dashboard()
        
        @self.app.route('/api/status')
        def api_status():
            """Get application status"""
            return jsonify(self._get_status())
        
        @self.app.route('/api/current-data')
        def api_current_data():
            """Get current OBD data"""
            return jsonify(self._get_current_data())
        
        @self.app.route('/api/recent-data')
        def api_recent_data():
            """Get recent OBD data"""
            limit = request.args.get('limit', 100, type=int)
            data = self.db_manager.get_recent_obd_data(limit)
            return jsonify(data)
        
        @self.app.route('/api/maintenance-alerts')
        def api_maintenance_alerts():
            """Get maintenance alerts"""
            resolved = request.args.get('resolved', 'false').lower() == 'true'
            alerts = self.db_manager.get_maintenance_alerts(resolved=resolved)
            return jsonify(alerts)
        
        @self.app.route('/api/database-stats')
        def api_database_stats():
            """Get database statistics"""
            stats = self.db_manager.get_database_stats()
            return jsonify(stats)
        
        @self.app.route('/api/export-data')
        def api_export_data():
            """Export data"""
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            format = request.args.get('format', 'csv')
            
            if not start_date or not end_date:
                return jsonify({'error': 'start_date and end_date required'}), 400
            
            filepath = self.db_manager.export_obd_data(start_date, end_date, format)
            if filepath:
                return jsonify({'filepath': filepath})
            else:
                return jsonify({'error': 'Export failed'}), 500
        
        @self.app.route('/api/test-notifications')
        def api_test_notifications():
            """Test notifications"""
            # This would require access to notification manager
            return jsonify({'message': 'Notification test endpoint'})
        
        @self.app.route('/api/clear-old-data')
        def api_clear_old_data():
            """Clear old data"""
            days = request.args.get('days', 365, type=int)
            deleted_count = self.db_manager.clear_old_obd_data(days)
            return jsonify({'deleted_count': deleted_count})
        
        # Static files
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files"""
            return send_from_directory('static', filename)
        
        # WebSocket events
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info("Client connected to dashboard")
            emit('status', self._get_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info("Client disconnected from dashboard")
        
        @self.socketio.on('request_data')
        def handle_data_request():
            """Handle data request from client"""
            data = self._get_current_data()
            emit('current_data', data)
    
    def _render_dashboard(self) -> str:
        """Render dashboard HTML"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SmartOBD Dashboard</title>
            <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .header h1 { margin: 0; }
                .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
                .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .card h3 { margin-bottom: 15px; color: #2c3e50; }
                .status-item { display: flex; justify-content: space-between; margin-bottom: 10px; }
                .status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 10px; }
                .status-online { background: #27ae60; }
                .status-offline { background: #e74c3c; }
                .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .alerts-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .alert-item { padding: 10px; margin-bottom: 10px; border-left: 4px solid #e74c3c; background: #fdf2f2; }
                .alert-item.resolved { border-left-color: #27ae60; background: #f0f9f0; }
                .button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
                .button:hover { background: #2980b9; }
                .button.danger { background: #e74c3c; }
                .button.danger:hover { background: #c0392b; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 SmartOBD Dashboard</h1>
                    <p>Real-time vehicle monitoring and predictive maintenance</p>
                </div>
                
                <div class="status-grid">
                    <div class="card">
                        <h3>System Status</h3>
                        <div id="system-status">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <h3>Current Data</h3>
                        <div id="current-data">Loading...</div>
                    </div>
                    
                    <div class="card">
                        <h3>Database Stats</h3>
                        <div id="database-stats">Loading...</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h3>Real-time Engine Data</h3>
                    <canvas id="engineChart" width="400" height="200"></canvas>
                </div>
                
                <div class="alerts-container">
                    <h3>Maintenance Alerts</h3>
                    <div id="alerts-list">Loading...</div>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="button" onclick="exportData()">Export Data</button>
                    <button class="button" onclick="clearOldData()">Clear Old Data</button>
                    <button class="button" onclick="testNotifications()">Test Notifications</button>
                </div>
            </div>
            
            <script>
                const socket = io();
                let engineChart;
                
                // Initialize chart
                function initChart() {
                    const ctx = document.getElementById('engineChart').getContext('2d');
                    engineChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: [],
                            datasets: [{
                                label: 'RPM',
                                data: [],
                                borderColor: '#3498db',
                                tension: 0.1
                            }, {
                                label: 'Speed (km/h)',
                                data: [],
                                borderColor: '#e74c3c',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true }
                            }
                        }
                    });
                }
                
                // Update system status
                function updateStatus() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            const statusDiv = document.getElementById('system-status');
                            statusDiv.innerHTML = `
                                <div class="status-item">
                                    <span>Application Running: <span class="status-indicator ${data.is_running ? 'status-online' : 'status-offline'}"></span></span>
                                    <span>${data.is_running ? 'Yes' : 'No'}</span>
                                </div>
                                <div class="status-item">
                                    <span>OBD Connected: <span class="status-indicator ${data.obd_connected ? 'status-online' : 'status-offline'}"></span></span>
                                    <span>${data.obd_connected ? 'Yes' : 'No'}</span>
                                </div>
                                <div class="status-item">
                                    <span>Data Collection: <span class="status-indicator ${data.data_collection_active ? 'status-online' : 'status-offline'}"></span></span>
                                    <span>${data.data_collection_active ? 'Active' : 'Inactive'}</span>
                                </div>
                                <div class="status-item">
                                    <span>Pending Alerts: <span class="status-indicator ${data.pending_alerts > 0 ? 'status-offline' : 'status-online'}"></span></span>
                                    <span>${data.pending_alerts}</span>
                                </div>
                            `;
                        });
                }
                
                // Update current data
                function updateCurrentData() {
                    fetch('/api/current-data')
                        .then(response => response.json())
                        .then(data => {
                            const dataDiv = document.getElementById('current-data');
                            if (data) {
                                dataDiv.innerHTML = `
                                    <div class="status-item">
                                        <span>RPM:</span>
                                        <span>${data.rpm || 'N/A'}</span>
                                    </div>
                                    <div class="status-item">
                                        <span>Speed:</span>
                                        <span>${data.speed || 'N/A'} km/h</span>
                                    </div>
                                    <div class="status-item">
                                        <span>Engine Load:</span>
                                        <span>${data.engine_load || 'N/A'}%</span>
                                    </div>
                                    <div class="status-item">
                                        <span>Coolant Temp:</span>
                                        <span>${data.coolant_temp || 'N/A'}°C</span>
                                    </div>
                                    <div class="status-item">
                                        <span>Fuel Level:</span>
                                        <span>${data.fuel_level || 'N/A'}%</span>
                                    </div>
                                `;
                                
                                // Update chart
                                if (engineChart && data.rpm !== null && data.speed !== null) {
                                    const now = new Date().toLocaleTimeString();
                                    engineChart.data.labels.push(now);
                                    engineChart.data.datasets[0].data.push(data.rpm);
                                    engineChart.data.datasets[1].data.push(data.speed);
                                    
                                    // Keep only last 20 points
                                    if (engineChart.data.labels.length > 20) {
                                        engineChart.data.labels.shift();
                                        engineChart.data.datasets[0].data.shift();
                                        engineChart.data.datasets[1].data.shift();
                                    }
                                    
                                    engineChart.update();
                                }
                            } else {
                                dataDiv.innerHTML = '<p>No data available</p>';
                            }
                        });
                }
                
                // Update database stats
                function updateDatabaseStats() {
                    fetch('/api/database-stats')
                        .then(response => response.json())
                        .then(data => {
                            const statsDiv = document.getElementById('database-stats');
                            statsDiv.innerHTML = `
                                <div class="status-item">
                                    <span>Total Records:</span>
                                    <span>${data.total_obd_records || 0}</span>
                                </div>
                                <div class="status-item">
                                    <span>Total Alerts:</span>
                                    <span>${data.total_alerts || 0}</span>
                                </div>
                                <div class="status-item">
                                    <span>Unresolved Alerts:</span>
                                    <span>${data.unresolved_alerts || 0}</span>
                                </div>
                                <div class="status-item">
                                    <span>Database Size:</span>
                                    <span>${data.database_size_mb || 0} MB</span>
                                </div>
                            `;
                        });
                }
                
                // Update alerts
                function updateAlerts() {
                    fetch('/api/maintenance-alerts')
                        .then(response => response.json())
                        .then(alerts => {
                            const alertsDiv = document.getElementById('alerts-list');
                            if (alerts.length > 0) {
                                alertsDiv.innerHTML = alerts.map(alert => `
                                    <div class="alert-item ${alert.is_resolved ? 'resolved' : ''}">
                                        <strong>${alert.alert_type.replace('_', ' ').toUpperCase()}</strong><br>
                                        ${alert.message}<br>
                                        <small>Severity: ${alert.severity} | Confidence: ${(alert.confidence * 100).toFixed(1)}%</small>
                                    </div>
                                `).join('');
                            } else {
                                alertsDiv.innerHTML = '<p>No active alerts</p>';
                            }
                        });
                }
                
                // Export data
                function exportData() {
                    const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
                    const endDate = new Date().toISOString().split('T')[0];
                    
                    fetch(`/api/export-data?start_date=${startDate}&end_date=${endDate}&format=csv`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.filepath) {
                                alert('Data exported successfully!');
                            } else {
                                alert('Export failed: ' + data.error);
                            }
                        });
                }
                
                // Clear old data
                function clearOldData() {
                    if (confirm('Are you sure you want to clear old data?')) {
                        fetch('/api/clear-old-data?days=365')
                            .then(response => response.json())
                            .then(data => {
                                alert(`Cleared ${data.deleted_count} old records`);
                                updateDatabaseStats();
                            });
                    }
                }
                
                // Test notifications
                function testNotifications() {
                    fetch('/api/test-notifications')
                        .then(response => response.json())
                        .then(data => {
                            alert(data.message);
                        });
                }
                
                // Socket events
                socket.on('status', function(data) {
                    console.log('Status update:', data);
                });
                
                socket.on('current_data', function(data) {
                    console.log('Current data update:', data);
                });
                
                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', function() {
                    initChart();
                    updateStatus();
                    updateCurrentData();
                    updateDatabaseStats();
                    updateAlerts();
                    
                    // Update every 5 seconds
                    setInterval(updateStatus, 5000);
                    setInterval(updateCurrentData, 5000);
                    setInterval(updateDatabaseStats, 30000);
                    setInterval(updateAlerts, 10000);
                });
            </script>
        </body>
        </html>
        """
    
    def _get_status(self) -> Dict[str, Any]:
        """Get application status"""
        # This would need access to the main app instance
        return {
            'is_running': True,
            'obd_connected': False,
            'data_collection_active': False,
            'dashboard_running': self.is_running,
            'database_connected': self.db_manager.is_connected(),
            'last_prediction': None,
            'pending_alerts': 0
        }
    
    def _get_current_data(self) -> Optional[Dict[str, Any]]:
        """Get current OBD data"""
        try:
            recent_data = self.db_manager.get_recent_obd_data(limit=1)
            if recent_data:
                return recent_data[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting current data: {e}")
            return None
    
    def start(self, host: Optional[str] = None, port: Optional[int] = None):
        """Start dashboard server"""
        if self.is_running:
            self.logger.warning("Dashboard server is already running")
            return
        
        try:
            self.host = host or self.host
            self.port = port or self.port
            
            self.logger.info(f"Starting dashboard server on {self.host}:{self.port}")
            
            self.is_running = True
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            self.logger.info("Dashboard server started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting dashboard server: {e}")
            self.is_running = False
    
    def _run_server(self):
        """Run Flask server"""
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            self.logger.error(f"Error running dashboard server: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop dashboard server"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("Stopping dashboard server...")
            self.is_running = False
            
            # Flask-SocketIO doesn't have a clean shutdown method
            # In practice, you'd need to implement proper shutdown
            
            self.logger.info("Dashboard server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping dashboard server: {e}")
    
    def is_running(self) -> bool:
        """Check if dashboard server is running"""
        return self.is_running 