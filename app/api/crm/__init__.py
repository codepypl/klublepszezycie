"""
CRM API modules - modular CRM system
"""
from .contacts_api import contacts_api_bp
from .imports_api import imports_api_bp
from .campaigns_api import campaigns_api_bp
from .blacklist_api import blacklist_api_bp
from .queue_api import queue_api_bp
from .agent_api import agent_api_bp
from .export_api import export_api_bp
from .voip_api import voip_api_bp
from .stats_api import crm_stats_api_bp
from .dashboard_stats_api import dashboard_stats_api_bp

__all__ = [
    'contacts_api_bp',
    'imports_api_bp', 
    'campaigns_api_bp',
    'blacklist_api_bp',
    'queue_api_bp',
    'agent_api_bp',
    'export_api_bp',
    'voip_api_bp',
    'crm_stats_api_bp',
    'dashboard_stats_api_bp'
]
