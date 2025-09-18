"""
User information collection utilities
"""
import re
import requests
from flask import request
from user_agents import parse
from .user_agent_parser import UserAgentParser
from .ip_geolocation import IPGeolocation

def get_user_info():
    """Extract user information from request"""
    user_agent_string = request.headers.get('User-Agent', '')
    ip_address = get_client_ip()
    
    # Parse user agent with our custom parser
    ua_parser = UserAgentParser()
    parsed_ua = ua_parser.parse(user_agent_string)
    
    # Get location from IP
    location_info = IPGeolocation.get_location(ip_address)
    
    return {
        'ip_address': ip_address,
        'user_agent': user_agent_string,
        'browser': ua_parser.get_browser_display_name(parsed_ua['browser'], parsed_ua['browser_version']),
        'operating_system': ua_parser.get_os_display_name(parsed_ua['os'], parsed_ua['os_version']),
        'location_country': location_info.get('country', ''),
        'location_city': location_info.get('city', '')
    }

def get_client_ip():
    """Get client IP address"""
    # Check for forwarded headers first (for reverse proxies)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        if ip and not is_private_ip(ip):
            return ip
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
        if ip and not is_private_ip(ip):
            return ip
    elif request.headers.get('CF-Connecting-IP'):  # Cloudflare
        ip = request.headers.get('CF-Connecting-IP')
        if ip and not is_private_ip(ip):
            return ip
    elif request.headers.get('X-Forwarded'):
        ip = request.headers.get('X-Forwarded')
        if ip and not is_private_ip(ip):
            return ip
    
    # Fallback to remote_addr
    ip = request.remote_addr
    if ip and not is_private_ip(ip):
        return ip
    
    # If all else fails and we have a private IP, try to get external IP
    if ip and is_private_ip(ip):
        try:
            import requests
            response = requests.get('https://api.ipify.org', timeout=3)
            if response.status_code == 200:
                external_ip = response.text.strip()
                if external_ip and not is_private_ip(external_ip):
                    return external_ip
        except:
            pass
    
    return ip or 'Nieznany'

# Location function moved to ip_geolocation.py

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
