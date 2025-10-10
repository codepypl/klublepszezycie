"""
Events API Module - modularized events functionality
"""

from .events_api import events_api_bp
from .schedules_api import schedules_api_bp
from .registrations_api import registrations_api_bp

# Export all blueprints
__all__ = [
    'events_api_bp',
    'schedules_api_bp',
    'registrations_api_bp'
]




