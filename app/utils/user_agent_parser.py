"""
User-Agent parser for extracting browser and OS information
"""
import re
from typing import Dict, Optional

class UserAgentParser:
    """Simple User-Agent parser for browser and OS detection"""
    
    # Browser patterns
    BROWSER_PATTERNS = {
        'Chrome': r'Chrome/(\d+\.\d+)',
        'Firefox': r'Firefox/(\d+\.\d+)',
        'Safari': r'Safari/(\d+\.\d+)',
        'Edge': r'Edg/(\d+\.\d+)',
        'Opera': r'Opera/(\d+\.\d+)',
        'Internet Explorer': r'MSIE (\d+\.\d+)',
        'Internet Explorer': r'Trident/.*rv:(\d+\.\d+)'
    }
    
    # OS patterns
    OS_PATTERNS = {
        'Windows 10': r'Windows NT 10\.0',
        'Windows 8.1': r'Windows NT 6\.3',
        'Windows 8': r'Windows NT 6\.2',
        'Windows 7': r'Windows NT 6\.1',
        'Windows Vista': r'Windows NT 6\.0',
        'Windows XP': r'Windows NT 5\.1',
        'macOS': r'Mac OS X (\d+[._]\d+)',
        'iOS': r'iPhone OS (\d+[._]\d+)',
        'iOS': r'iPad.*OS (\d+[._]\d+)',
        'Android': r'Android (\d+\.\d+)',
        'Linux': r'Linux',
        'Ubuntu': r'Ubuntu',
        'Debian': r'Debian',
        'CentOS': r'CentOS',
        'Red Hat': r'Red Hat'
    }
    
    @classmethod
    def parse(cls, user_agent: str) -> Dict[str, Optional[str]]:
        """
        Parse User-Agent string and extract browser and OS information
        
        Args:
            user_agent: User-Agent string from request
            
        Returns:
            Dict with browser, browser_version, os, os_version
        """
        if not user_agent:
            return {
                'browser': None,
                'browser_version': None,
                'os': None,
                'os_version': None
            }
        
        user_agent = user_agent.strip()
        
        # Parse browser
        browser = None
        browser_version = None
        for browser_name, pattern in cls.BROWSER_PATTERNS.items():
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                browser = browser_name
                browser_version = match.group(1)
                break
        
        # Parse OS
        os = None
        os_version = None
        for os_name, pattern in cls.OS_PATTERNS.items():
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                os = os_name
                if match.groups():
                    os_version = match.group(1).replace('_', '.')
                break
        
        return {
            'browser': browser,
            'browser_version': browser_version,
            'os': os,
            'os_version': os_version
        }
    
    @classmethod
    def get_browser_display_name(cls, browser: str, version: str = None) -> str:
        """Get formatted browser name with version"""
        if not browser:
            return 'Nieznana przeglądarka'
        
        if version:
            return f'{browser} {version}'
        return browser
    
    @classmethod
    def get_os_display_name(cls, os: str, version: str = None) -> str:
        """Get formatted OS name with version"""
        if not os:
            return 'Nieznany system'
        
        if version:
            return f'{os} {version}'
        return os
