"""
Email Alerting System for HolisticOS
Manages alerts, notifications, and escalation policies via email
"""

import asyncio
import smtplib
import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Alert data structure"""
    severity: AlertSeverity
    title: str
    details: Dict[str, Any]
    timestamp: datetime
    service: str
    alert_key: str

class EmailAlertManager:
    """Manage alerts, notifications, and cooldown logic via email"""
    
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("ALERT_EMAIL_USER")
        self.email_password = os.getenv("ALERT_EMAIL_PASSWORD")
        self.alert_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
        self.alert_recipients = [email.strip() for email in self.alert_recipients if email.strip()]
        
        # Alert cooldown settings
        self.alert_cooldown = {}  # Prevent spam alerts
        self.cooldown_minutes = {
            AlertSeverity.CRITICAL: 5,   # 5 minutes for critical
            AlertSeverity.ERROR: 10,     # 10 minutes for errors
            AlertSeverity.WARNING: 15,   # 15 minutes for warnings
            AlertSeverity.INFO: 30       # 30 minutes for info
        }
        self.alert_history = []  # Keep track of recent alerts
        self.max_history = 100   # Keep last 100 alerts
        
        # Email templates
        self.email_templates = {
            AlertSeverity.CRITICAL: {
                "subject_prefix": "🚨 CRITICAL",
                "color": "#990000",
                "priority": "high"
            },
            AlertSeverity.ERROR: {
                "subject_prefix": "❌ ERROR",
                "color": "#ff0000", 
                "priority": "normal"
            },
            AlertSeverity.WARNING: {
                "subject_prefix": "⚠️ WARNING",
                "color": "#ff9900",
                "priority": "normal"
            },
            AlertSeverity.INFO: {
                "subject_prefix": "ℹ️ INFO",
                "color": "#36a64f",
                "priority": "low"
            }
        }
    
    def should_send_alert(self, alert_key: str, severity: AlertSeverity) -> bool:
        """Check if alert should be sent based on cooldown logic"""
        now = datetime.now()
        cooldown_key = f"{alert_key}:{severity.value}"
        
        if cooldown_key not in self.alert_cooldown:
            self.alert_cooldown[cooldown_key] = now
            return True
        
        last_sent = self.alert_cooldown[cooldown_key]
        minutes_since = (now - last_sent).total_seconds() / 60
        cooldown_period = self.cooldown_minutes[severity]
        
        if minutes_since >= cooldown_period:
            self.alert_cooldown[cooldown_key] = now
            return True
        
        return False
    
    async def send_alert(self, severity: AlertSeverity, title: str, details: Dict[str, Any], 
                        service: str = "holisticos"):
        """Send alert via email"""
        alert_key = f"{service}:{title}"
        
        if not self.should_send_alert(alert_key, severity):
            logger.debug(f"Alert cooldown active for: {alert_key}")
            return
        
        if not self.email_user or not self.email_password or not self.alert_recipients:
            logger.warning(f"Email configuration incomplete. Alert: {title}")
            return
        
        # Create alert object
        alert = Alert(
            severity=severity,
            title=title,
            details=details,
            timestamp=datetime.now(),
            service=service,
            alert_key=alert_key
        )
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        # Send email in background
        asyncio.create_task(self._send_email_alert(alert))
    
    async def _send_email_alert(self, alert: Alert):
        """Send the actual email alert"""
        try:
            template = self.email_templates[alert.severity]
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{template['subject_prefix']} - HolisticOS: {alert.title}"
            msg["From"] = self.email_user
            msg["To"] = ", ".join(self.alert_recipients)
            msg["X-Priority"] = "1" if alert.severity == AlertSeverity.CRITICAL else "3"
            
            # Create HTML and text versions
            html_body = self._create_html_alert(alert, template)
            text_body = self._create_text_alert(alert)
            
            # Attach both versions
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email using asyncio to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None, 
                self._send_smtp_email, 
                msg
            )
            
            logger.info(f"Alert email sent: {alert.severity.value} - {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_smtp_email(self, msg: MIMEMultipart):
        """Send email via SMTP (blocking operation)"""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
    
    def _create_html_alert(self, alert: Alert, template: Dict[str, str]) -> str:
        """Create HTML email body"""
        details_html = ""
        for key, value in alert.details.items():
            details_html += f"<tr><td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>{key}</td><td style='padding: 5px; border: 1px solid #ddd;'>{value}</td></tr>"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {template['color']}; color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🔔 HolisticOS Alert</h1>
                    <h2 style="margin: 10px 0 0 0; font-size: 18px; font-weight: normal;">{alert.title}</h2>
                </div>
                
                <div style="padding: 20px;">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                        <tr><td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>Severity</td><td style='padding: 5px; border: 1px solid #ddd;'>{alert.severity.value.upper()}</td></tr>
                        <tr><td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>Service</td><td style='padding: 5px; border: 1px solid #ddd;'>{alert.service}</td></tr>
                        <tr><td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>Timestamp</td><td style='padding: 5px; border: 1px solid #ddd;'>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                        {details_html}
                    </table>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid {template['color']};">
                        <h3 style="margin: 0 0 10px 0; color: #333;">Recommended Actions:</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Check the HolisticOS health dashboard</li>
                            <li>Review recent deployment logs</li>
                            <li>Verify external service availability</li>
                            <li>Monitor system resources and performance</li>
                        </ul>
                    </div>
                    
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px;">
                        <p>This alert was generated by HolisticOS Monitoring System</p>
                        <p>To modify alert preferences, contact your system administrator</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_text_alert(self, alert: Alert) -> str:
        """Create plain text email body"""
        details_text = "\n".join([f"  {key}: {value}" for key, value in alert.details.items()])
        
        return f"""
HolisticOS Alert - {alert.severity.value.upper()}

Title: {alert.title}
Service: {alert.service}
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Details:
{details_text}

Recommended Actions:
- Check the HolisticOS health dashboard
- Review recent deployment logs  
- Verify external service availability
- Monitor system resources and performance

---
This alert was generated by HolisticOS Monitoring System
        """
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history"""
        recent_alerts = self.alert_history[-limit:]
        return [
            {
                "severity": alert.severity.value,
                "title": alert.title,
                "service": alert.service,
                "timestamp": alert.timestamp.isoformat(),
                "details": alert.details
            }
            for alert in recent_alerts
        ]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {
                "total_alerts": 0,
                "alerts_by_severity": {},
                "alerts_by_service": {},
                "recent_alert_rate": 0
            }
        
        # Count by severity
        severity_counts = {}
        service_counts = {}
        
        for alert in self.alert_history:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            service_counts[alert.service] = service_counts.get(alert.service, 0) + 1
        
        # Calculate recent alert rate (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_alerts = [a for a in self.alert_history if a.timestamp > one_hour_ago]
        
        return {
            "total_alerts": len(self.alert_history),
            "alerts_by_severity": severity_counts,
            "alerts_by_service": service_counts,
            "recent_alert_rate": len(recent_alerts),
            "last_alert": self.alert_history[-1].timestamp.isoformat() if self.alert_history else None
        }

# Global alert manager instance
alert_manager = EmailAlertManager()

# Background monitoring task
async def monitor_health_continuously():
    """Background task to monitor health and send email alerts"""
    from shared_libs.monitoring.health_checker import health_checker
    
    while True:
        try:
            health_status = await health_checker.run_comprehensive_health_check()
            
            # Check for critical issues
            if health_status["overall_status"] == "critical":
                await alert_manager.send_alert(
                    AlertSeverity.CRITICAL,
                    "System Critical Issues Detected",
                    {
                        "Critical Issues": ", ".join(health_status["summary"]["critical_issues"]),
                        "Environment": os.getenv("ENVIRONMENT", "production"),
                        "Timestamp": health_status["timestamp"],
                        "Health URL": "https://your-app.onrender.com/api/health"
                    }
                )
            
            # Check for degraded performance
            elif health_status["overall_status"] == "degraded":
                await alert_manager.send_alert(
                    AlertSeverity.WARNING,
                    "System Performance Degraded",
                    {
                        "Warnings": ", ".join(health_status["summary"]["warnings"]),
                        "Healthy Services": ", ".join(health_status["summary"]["healthy_services"]),
                        "Health URL": "https://your-app.onrender.com/api/health"
                    }
                )
            
            # Check specific service issues
            for service, data in health_status["services"].items():
                if data["status"] == "critical":
                    await alert_manager.send_alert(
                        AlertSeverity.ERROR,
                        f"{service.title()} Service Down",
                        {
                            "Service": service,
                            "Error": data["message"],
                            "Response Time": f"{data['response_time_ms']}ms",
                            "Health URL": "https://your-app.onrender.com/api/health"
                        }
                    )
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
        
        # Check every 2 minutes
        await asyncio.sleep(120)