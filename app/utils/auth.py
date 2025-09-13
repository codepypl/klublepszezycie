"""
Authentication utility functions
"""
from models import User

def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

