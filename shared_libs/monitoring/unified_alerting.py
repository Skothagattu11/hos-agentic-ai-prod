"""
Unified Alerting System for HolisticOS
Primary: Email alerts with Slack fallback when email fails
"""

import asyncio
import aiohttp
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

class UnifiedAlertManager:
    """Unified alert manager with email primary and Slack fallback"""
    
    def __init__(self):
        # Email configuration (primary)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("ALERT_EMAIL_USER")
        self.email_password = os.getenv("ALERT_EMAIL_PASSWORD")
        self.alert_recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
        self.alert_recipients = [email.strip() for email in self.alert_recipients if email.strip()]
        
        # Slack configuration (fallback)
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        # Alert cooldown settings
        self.alert_cooldown = {}
        self.cooldown_minutes = {
            AlertSeverity.CRITICAL: 5,   # 5 minutes for critical
            AlertSeverity.ERROR: 10,     # 10 minutes for errors
            AlertSeverity.WARNING: 15,   # 15 minutes for warnings
            AlertSeverity.INFO: 30       # 30 minutes for info
        }
        self.alert_history = []
        self.max_history = 100
        
        # Track delivery methods
        self.delivery_stats = {
            "email_success": 0,
            "email_failures": 0,
            "slack_fallback": 0,
            "total_failures": 0
        }
        
        # Email templates
        self.email_templates = {
            AlertSeverity.CRITICAL: {"subject_prefix": "🚨 CRITICAL", "color": "#990000"},
            AlertSeverity.ERROR: {"subject_prefix": "❌ ERROR", "color": "#ff0000"},
            AlertSeverity.WARNING: {"subject_prefix": "⚠️ WARNING", "color": "#ff9900"},
            AlertSeverity.INFO: {"subject_prefix": "ℹ️ INFO", "color": "#36a64f"}
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
        """Send alert with email primary and Slack fallback"""
        alert_key = f"{service}:{title}"
        
        if not self.should_send_alert(alert_key, severity):
            logger.debug(f"Alert cooldown active for: {alert_key}")
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
        
        # Try email first, fallback to Slack if email fails
        email_success = await self._try_send_email(alert)
        
        if not email_success:
            logger.warning(f"Email delivery failed for alert: {title}, trying Slack fallback")
            slack_success = await self._try_send_slack(alert)
            
            if slack_success:
                self.delivery_stats["slack_fallback"] += 1
                logger.info(f"Alert delivered via Slack fallback: {title}")
            else:
                self.delivery_stats["total_failures"] += 1
                logger.error(f"Both email and Slack delivery failed for alert: {title}")
    
    async def _try_send_email(self, alert: Alert) -> bool:
        """Try to send email alert, return True if successful"""
        try:
            if not self.email_user or not self.email_password or not self.alert_recipients:
                logger.debug("Email configuration incomplete, skipping email delivery")
                return False
            
            template = self.email_templates[alert.severity]
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{template['subject_prefix']} - HolisticOS: {alert.title}"
            msg["From"] = self.email_user
            msg["To"] = ", ".join(self.alert_recipients)
            msg["X-Priority"] = "1" if alert.severity == AlertSeverity.CRITICAL else "3"
            
            # Create HTML and text versions
            html_body = self._create_html_email(alert, template)
            text_body = self._create_text_email(alert)
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email using asyncio to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, self._send_smtp_email, msg)
            
            self.delivery_stats["email_success"] += 1
            logger.info(f"Alert email sent successfully: {alert.severity.value} - {alert.title}")
            return True
            
        except Exception as e:
            self.delivery_stats["email_failures"] += 1
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    async def _try_send_slack(self, alert: Alert) -> bool:
        """Try to send Slack alert as fallback, return True if successful"""
        try:
            if not self.slack_webhook_url:
                logger.debug("Slack webhook URL not configured, skipping Slack fallback")
                return False
            
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900", 
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#990000"
            }
            
            payload = {
                "text": f"🚨 HolisticOS Alert (Email delivery failed - Slack fallback)",
                "attachments": [{
                    "color": color_map[alert.severity],
                    "title": f"[{alert.severity.value.upper()}] {alert.title}",
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in alert.details.items()
                    ],
                    "footer": "HolisticOS Monitoring (Slack Fallback)",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack fallback alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Slack fallback failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Slack fallback error: {e}")
            return False
    
    def _send_smtp_email(self, msg: MIMEMultipart):
        """Send email via SMTP (blocking operation)"""
        context = ssl.create_default_context()
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls(context=context)
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
    
    def _create_html_email(self, alert: Alert, template: Dict[str, str]) -> str:
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
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_text_email(self, alert: Alert) -> str:
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
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get alert delivery statistics"""
        total_attempts = sum(self.delivery_stats.values())
        
        return {
            **self.delivery_stats,
            "total_attempts": total_attempts,
            "email_success_rate": (
                self.delivery_stats["email_success"] / total_attempts * 100 
                if total_attempts > 0 else 0
            ),
            "overall_success_rate": (
                (self.delivery_stats["email_success"] + self.delivery_stats["slack_fallback"]) / total_attempts * 100
                if total_attempts > 0 else 0
            )
        }
    
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

# Global unified alert manager instance
alert_manager = UnifiedAlertManager()

# Background monitoring task
async def monitor_health_continuously():
    """Background task to monitor health and send alerts"""
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
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
        
        # Check every 2 minutes
        await asyncio.sleep(120)