"""
Alerting System with Slack Integration for HolisticOS
Manages alerts, notifications, and escalation policies
"""

import asyncio
import aiohttp
import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass

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

class AlertManager:
    """Manage alerts, notifications, and cooldown logic"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.alert_cooldown = {}  # Prevent spam alerts
        self.cooldown_minutes = {
            AlertSeverity.CRITICAL: 5,   # 5 minutes for critical
            AlertSeverity.ERROR: 10,     # 10 minutes for errors
            AlertSeverity.WARNING: 15,   # 15 minutes for warnings
            AlertSeverity.INFO: 30       # 30 minutes for info
        }
        self.alert_history = []  # Keep track of recent alerts
        self.max_history = 100   # Keep last 100 alerts
    
    def should_send_alert(self, alert_key: str, severity: AlertSeverity) -> bool:
        """Check if alert should be sent based on cooldown logic"""
        now = datetime.now()
        last_sent = self.alert_cooldown.get(alert_key)
        
        if not last_sent:
            self.alert_cooldown[alert_key] = now
            return True
        
        cooldown_period = self.cooldown_minutes[severity]
        minutes_since = (now - last_sent).total_seconds() / 60
        
        if minutes_since >= cooldown_period:
            self.alert_cooldown[alert_key] = now
            return True
        
        logger.debug(f"Alert cooldown active for: {alert_key} ({minutes_since:.1f}m < {cooldown_period}m)")
        return False
    
    async def send_alert(self, severity: AlertSeverity, title: str, details: Dict[str, Any], service: str = "system"):
        """Send alert to configured channels"""
        alert_key = f"{severity.value}:{service}:{title}"
        
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
        self._add_to_history(alert)
        
        # Check cooldown
        if not self.should_send_alert(alert_key, severity):
            logger.debug(f"Alert suppressed due to cooldown: {alert_key}")
            return False
        
        # Send to configured channels
        success = False
        
        if self.webhook_url:
            success = await self._send_slack_alert(alert)
        else:
            logger.debug(f"No Slack webhook configured. Alert: {title}")
            # Log the alert even if no webhook is configured
            self._log_alert(alert)
            success = True
        
        if success:
            logger.debug(f"Alert sent successfully: [{severity.value.upper()}] {title}")
        
        return success
    
    async def _send_slack_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            color_map = {
                AlertSeverity.INFO: "#36a64f",      # Green
                AlertSeverity.WARNING: "#ff9900",   # Orange  
                AlertSeverity.ERROR: "#ff0000",     # Red
                AlertSeverity.CRITICAL: "#990000"   # Dark Red
            }
            
            emoji_map = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.ERROR: "❌",
                AlertSeverity.CRITICAL: "🚨"
            }
            
            # Format details for Slack
            fields = []
            for key, value in alert.details.items():
                # Limit field value length for readability
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                
                fields.append({
                    "title": key.replace("_", " ").title(),
                    "value": str_value,
                    "short": len(str_value) < 50
                })
            
            # Add timestamp and service info
            fields.extend([
                {
                    "title": "Service",
                    "value": alert.service,
                    "short": True
                },
                {
                    "title": "Environment",
                    "value": os.getenv("ENVIRONMENT", "production"),
                    "short": True
                }
            ])
            
            payload = {
                "text": f"{emoji_map[alert.severity]} HolisticOS Alert",
                "attachments": [{
                    "color": color_map[alert.severity],
                    "title": f"[{alert.severity.value.upper()}] {alert.title}",
                    "fields": fields,
                    "footer": "HolisticOS Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            # Send to Slack
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"Slack webhook failed with status: {response.status}")
                        response_text = await response.text()
                        logger.error(f"Slack response: {response_text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("Timeout sending Slack alert")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def _log_alert(self, alert: Alert):
        """Log alert to application logs"""
        log_level = {
            AlertSeverity.INFO: logging.DEBUG,  # Changed to DEBUG for quiet mode
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }
        
        details_str = ", ".join([f"{k}={v}" for k, v in alert.details.items()])
        message = f"ALERT [{alert.severity.value.upper()}] {alert.service}: {alert.title} | {details_str}"
        
        logger.log(log_level[alert.severity], message)
    
    def _add_to_history(self, alert: Alert):
        """Add alert to history and maintain size limit"""
        self.alert_history.append(alert)
        
        # Trim history if it gets too long
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp > cutoff]
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of alerts in the last N hours"""
        recent_alerts = self.get_alert_history(hours)
        
        summary = {
            "total_alerts": len(recent_alerts),
            "by_severity": {},
            "by_service": {},
            "active_cooldowns": len(self.alert_cooldown),
            "period_hours": hours
        }
        
        for severity in AlertSeverity:
            summary["by_severity"][severity.value] = len([
                a for a in recent_alerts if a.severity == severity
            ])
        
        services = set(alert.service for alert in recent_alerts)
        for service in services:
            summary["by_service"][service] = len([
                a for a in recent_alerts if a.service == service
            ])
        
        return summary
    
    def clear_cooldowns(self):
        """Clear all alert cooldowns (for testing or manual reset)"""
        self.alert_cooldown.clear()
        logger.debug("All alert cooldowns cleared")

# Global alert manager instance
alert_manager = AlertManager()

# Health monitoring task that runs in background
async def monitor_health_continuously():
    """Background task to continuously monitor health and send alerts"""
    from .health_checker import health_checker
    
    logger.debug("Starting continuous health monitoring...")
    check_interval = 120  # Check every 2 minutes
    
    while True:
        try:
            health_status = await health_checker.run_comprehensive_health_check()
            
            # Track health check metrics
            from .metrics import metrics
            for service, data in health_status["services"].items():
                is_healthy = data["status"] == "healthy"
                response_time = data.get("response_time_ms", 0) / 1000  # Convert to seconds
                metrics.update_health_check_metrics(service, is_healthy, response_time)
            
            # Check for critical issues
            if health_status["overall_status"] == "critical":
                await alert_manager.send_alert(
                    AlertSeverity.CRITICAL,
                    "System Critical Issues Detected",
                    {
                        "critical_issues": health_status["summary"]["critical_issues"],
                        "environment": os.getenv("ENVIRONMENT", "production"),
                        "timestamp": health_status["timestamp"],
                        "affected_services": len(health_status["summary"]["critical_issues"])
                    },
                    service="system"
                )
            
            # Check for degraded performance
            elif health_status["overall_status"] == "degraded":
                await alert_manager.send_alert(
                    AlertSeverity.WARNING,
                    "System Performance Degraded", 
                    {
                        "warnings": health_status["summary"]["warnings"],
                        "healthy_services": health_status["summary"]["healthy_services"],
                        "degraded_services": len(health_status["summary"]["warnings"])
                    },
                    service="system"
                )
            
            # Check individual service issues
            for service, data in health_status["services"].items():
                if data["status"] == "critical":
                    await alert_manager.send_alert(
                        AlertSeverity.ERROR,
                        f"{service.title()} Service Critical",
                        {
                            "service": service,
                            "error_message": data["message"], 
                            "response_time_ms": data.get("response_time_ms", -1),
                            "details": data.get("details", {})
                        },
                        service=service
                    )
                elif data["status"] == "degraded" and data.get("response_time_ms", 0) > 5000:
                    # Alert on very slow responses
                    await alert_manager.send_alert(
                        AlertSeverity.WARNING,
                        f"{service.title()} Service Slow",
                        {
                            "service": service,
                            "response_time_ms": data.get("response_time_ms", 0),
                            "message": data["message"]
                        },
                        service=service
                    )
        
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            # Send alert about monitoring failure
            await alert_manager.send_alert(
                AlertSeverity.ERROR,
                "Health Monitoring Failed",
                {
                    "error": str(e),
                    "monitoring_check": "failed"
                },
                service="monitoring"
            )
        
        # Wait for next check
        await asyncio.sleep(check_interval)

# Convenience functions for sending alerts
async def send_critical_alert(title: str, details: Dict[str, Any], service: str = "system"):
    """Send a critical alert"""
    return await alert_manager.send_alert(AlertSeverity.CRITICAL, title, details, service)

async def send_error_alert(title: str, details: Dict[str, Any], service: str = "system"):
    """Send an error alert"""
    return await alert_manager.send_alert(AlertSeverity.ERROR, title, details, service)

async def send_warning_alert(title: str, details: Dict[str, Any], service: str = "system"):
    """Send a warning alert"""
    return await alert_manager.send_alert(AlertSeverity.WARNING, title, details, service)

async def send_info_alert(title: str, details: Dict[str, Any], service: str = "system"):
    """Send an info alert"""
    return await alert_manager.send_alert(AlertSeverity.INFO, title, details, service)