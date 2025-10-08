"""
Email API modules - modular email system
"""
from .campaigns_api import email_campaigns_bp
from .templates_api import email_templates_bp
from .queue_api import email_queue_bp
from .monitoring_api import email_monitoring_bp

__all__ = ['email_campaigns_bp', 'email_templates_bp', 'email_queue_bp', 'email_monitoring_bp']