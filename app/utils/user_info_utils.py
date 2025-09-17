"""
User information collection utilities
"""
import re
import requests
from flask import request
from user_agents import parse

def get_user_info():
    """Extract user information from request"""
    user_agent_string = request.headers.get('User-Agent', '')
    ip_address = get_client_ip()
    
    # Parse user agent
    user_agent = parse(user_agent_string)
    
    # Get location from IP
    location_info = get_location_from_ip(ip_address)
    
    return {
        'ip_address': ip_address,
        'user_agent': user_agent_string,
        'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}".strip(),
        'operating_system': f"{user_agent.os.family} {user_agent.os.version_string}".strip(),
        'location_country': location_info.get('country', ''),
        'location_city': location_info.get('city', '')
    }

def get_client_ip():
    """Get client IP address"""
    # Check for forwarded headers first
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_location_from_ip(ip_address):
    """Get location information from IP address"""
    try:
        # Skip private IPs
        if is_private_ip(ip_address):
            return {'country': '', 'city': ''}
        
        # Use ipapi.co service (free, no API key required)
        response = requests.get(f'http://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'country': data.get('country_name', ''),
                'city': data.get('city', '')
            }
    except Exception as e:
        print(f"Error getting location for IP {ip_address}: {e}")
    
    return {'country': '', 'city': ''}

def is_private_ip(ip):
    """Check if IP is private/local"""
    private_patterns = [
        r'^127\.',  # 127.0.0.0/8
        r'^10\.',   # 10.0.0.0/8
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # 172.16.0.0/12
        r'^192\.168\.',  # 192.168.0.0/16
        r'^::1$',   # IPv6 localhost
        r'^fe80:',  # IPv6 link-local
        r'^fc00:',  # IPv6 unique local
    ]
    
    for pattern in private_patterns:
        if re.match(pattern, ip):
            return True
    return False
