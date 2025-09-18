"""
IP geolocation utilities
"""
import requests
import logging
from typing import Dict, Optional

class IPGeolocation:
    """Simple IP geolocation service"""
    
    @classmethod
    def get_location(cls, ip_address: str) -> Dict[str, Optional[str]]:
        """
        Get location information for IP address
        
        Args:
            ip_address: IP address to lookup
            
        Returns:
            Dict with country, city, region
        """
        if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
            return {
                'country': 'Polska',
                'city': 'Lokalne',
                'region': 'Lokalne'
            }
        
        try:
            # Use free IP geolocation service
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country', 'Nieznany'),
                        'city': data.get('city', 'Nieznane'),
                        'region': data.get('regionName', 'Nieznany')
                    }
        except Exception as e:
            logging.warning(f"IP geolocation failed for {ip_address}: {str(e)}")
        
        return {
            'country': 'Nieznany',
            'city': 'Nieznane',
            'region': 'Nieznany'
        }
    
    @classmethod
    def get_location_display_name(cls, country: str, city: str, region: str = None) -> str:
        """Get formatted location name"""
        if country == 'Nieznany' and city == 'Nieznane':
            return 'Nieznana lokalizacja'
        
        if city and city != 'Nieznane':
            if region and region != 'Nieznany':
                return f'{city}, {region}, {country}'
            return f'{city}, {country}'
        
        return country
