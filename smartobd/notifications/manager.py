"""
Notification management for SmartOBD
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.logger import LoggerMixin
from ..core.config import Config


class NotificationManager(LoggerMixin):
    """Notification management class for SmartOBD"""
    
    def __init__(self, config: Config):
        """
        Initialize notification manager
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.notification_config = config.get_notification_config()
        
        self.logger.info("Notification manager initialized")
    
    def send_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Send maintenance alerts via configured notification methods
        
        Args:
            alerts: List of maintenance alert dictionaries
        """
        if not alerts:
            return
        
        try:
            self.logger.info(f"Sending {len(alerts)} maintenance alerts")
            
            for alert in alerts:
                # Send email notification
                if self.notification_config['email']['enabled']:
                    self._send_email_alert(alert)
                
                # Send SMS notification
                if self.notification_config['sms']['enabled']:
                    self._send_sms_alert(alert)
                
                # Send push notification
                if self.notification_config['push']['enabled']:
                    self._send_push_alert(alert)
                
                # Send webhook notification
                if self.notification_config['webhook']['enabled']:
                    self._send_webhook_alert(alert)
            
            self.logger.info("All alerts sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email notification"""
        try:
            email_config = self.notification_config['email']
            
            if not email_config.get('username') or not email_config.get('password'):
                self.logger.warning("Email credentials not configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(email_config.get('to_addresses', []))
            msg['Subject'] = f"SmartOBD Maintenance Alert: {alert['type'].replace('_', ' ').title()}"
            
            # Create email body
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            text = msg.as_string()
            server.sendmail(email_config['from_address'], email_config['to_addresses'], text)
            server.quit()
            
            self.logger.info(f"Email alert sent for {alert['type']}")
            
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")
    
    def _create_email_body(self, alert: Dict[str, Any]) -> str:
        """Create HTML email body"""
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        
        color = severity_colors.get(alert.get('severity', 'medium'), '#ffc107')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .alert {{ border: 2px solid {color}; border-radius: 5px; padding: 15px; margin: 10px 0; }}
                .severity {{ color: {color}; font-weight: bold; }}
                .timestamp {{ color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h2>🚗 SmartOBD Maintenance Alert</h2>
            <div class="alert">
                <h3 class="severity">{alert['type'].replace('_', ' ').title()}</h3>
                <p><strong>Message:</strong> {alert.get('message', 'Maintenance required')}</p>
                <p><strong>Severity:</strong> {alert.get('severity', 'medium').title()}</p>
                <p><strong>Confidence:</strong> {alert.get('confidence', 0):.1%}</p>
                <p class="timestamp">Alert generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <p>Please schedule maintenance for your vehicle as soon as possible.</p>
            <p>Best regards,<br>SmartOBD Team</p>
        </body>
        </html>
        """
        
        return html
    
    def _send_sms_alert(self, alert: Dict[str, Any]):
        """Send SMS notification using Twilio"""
        try:
            sms_config = self.notification_config['sms']
            
            if not sms_config.get('twilio_account_sid') or not sms_config.get('twilio_auth_token'):
                self.logger.warning("Twilio credentials not configured")
                return
            
            # Create message
            message = f"SmartOBD Alert: {alert['type'].replace('_', ' ').title()} needed. {alert.get('message', 'Maintenance required')}"
            
            # Send SMS via Twilio
            url = f"https://api.twilio.com/2010-04-01/Accounts/{sms_config['twilio_account_sid']}/Messages.json"
            
            data = {
                'From': sms_config['twilio_phone_number'],
                'To': sms_config['recipient_numbers'][0],  # Send to first number
                'Body': message
            }
            
            response = requests.post(
                url,
                data=data,
                auth=(sms_config['twilio_account_sid'], sms_config['twilio_auth_token'])
            )
            
            if response.status_code == 201:
                self.logger.info(f"SMS alert sent for {alert['type']}")
            else:
                self.logger.error(f"Failed to send SMS: {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error sending SMS alert: {e}")
    
    def _send_push_alert(self, alert: Dict[str, Any]):
        """Send push notification using Pushbullet"""
        try:
            push_config = self.notification_config['push']
            
            if not push_config.get('pushbullet_api_key'):
                self.logger.warning("Pushbullet API key not configured")
                return
            
            # Create notification
            title = f"SmartOBD: {alert['type'].replace('_', ' ').title()}"
            body = alert.get('message', 'Maintenance required')
            
            # Send push notification
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                'Access-Token': push_config['pushbullet_api_key'],
                'Content-Type': 'application/json'
            }
            
            data = {
                'type': 'note',
                'title': title,
                'body': body
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                self.logger.info(f"Push alert sent for {alert['type']}")
            else:
                self.logger.error(f"Failed to send push notification: {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error sending push alert: {e}")
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_config = self.notification_config['webhook']
            
            if not webhook_config.get('webhook_url'):
                self.logger.warning("Webhook URL not configured")
                return
            
            # Prepare webhook payload
            payload = {
                'timestamp': datetime.now().isoformat(),
                'alert_type': alert['type'],
                'severity': alert.get('severity', 'medium'),
                'message': alert.get('message', 'Maintenance required'),
                'confidence': alert.get('confidence', 0),
                'source': 'SmartOBD'
            }
            
            # Send webhook
            response = requests.post(
                webhook_config['webhook_url'],
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                self.logger.info(f"Webhook alert sent for {alert['type']}")
            else:
                self.logger.error(f"Failed to send webhook: {response.status_code} - {response.text}")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook alert: {e}")
    
    def test_notifications(self) -> Dict[str, bool]:
        """Test all notification methods"""
        test_alert = {
            'type': 'test_alert',
            'severity': 'medium',
            'message': 'This is a test notification from SmartOBD',
            'confidence': 0.95
        }
        
        results = {}
        
        try:
            # Test email
            if self.notification_config['email']['enabled']:
                try:
                    self._send_email_alert(test_alert)
                    results['email'] = True
                except Exception as e:
                    self.logger.error(f"Email test failed: {e}")
                    results['email'] = False
            
            # Test SMS
            if self.notification_config['sms']['enabled']:
                try:
                    self._send_sms_alert(test_alert)
                    results['sms'] = True
                except Exception as e:
                    self.logger.error(f"SMS test failed: {e}")
                    results['sms'] = False
            
            # Test push
            if self.notification_config['push']['enabled']:
                try:
                    self._send_push_alert(test_alert)
                    results['push'] = True
                except Exception as e:
                    self.logger.error(f"Push test failed: {e}")
                    results['push'] = False
            
            # Test webhook
            if self.notification_config['webhook']['enabled']:
                try:
                    self._send_webhook_alert(test_alert)
                    results['webhook'] = True
                except Exception as e:
                    self.logger.error(f"Webhook test failed: {e}")
                    results['webhook'] = False
            
            self.logger.info(f"Notification tests completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error testing notifications: {e}")
            return {}
    
    def get_notification_status(self) -> Dict[str, Any]:
        """Get notification configuration status"""
        return {
            'email': {
                'enabled': self.notification_config['email']['enabled'],
                'configured': bool(self.notification_config['email'].get('username') and 
                                 self.notification_config['email'].get('password'))
            },
            'sms': {
                'enabled': self.notification_config['sms']['enabled'],
                'configured': bool(self.notification_config['sms'].get('twilio_account_sid') and 
                                 self.notification_config['sms'].get('twilio_auth_token'))
            },
            'push': {
                'enabled': self.notification_config['push']['enabled'],
                'configured': bool(self.notification_config['push'].get('pushbullet_api_key'))
            },
            'webhook': {
                'enabled': self.notification_config['webhook']['enabled'],
                'configured': bool(self.notification_config['webhook'].get('webhook_url'))
            }
        } 