# Blueprints module - only ankieter_bp remains here
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'crm', 'admin'))
from ankieter import ankieter_bp

__all__ = ['ankieter_bp']
