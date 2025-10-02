"""
Bazowa klasa dla dostawców e-maili
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

class BaseEmailProvider(ABC):
    """Bazowa klasa dla wszystkich dostawców e-maili"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = None  # Będzie ustawiony przez EmailManager
    
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str = None, 
                   text_content: str = None, from_email: str = None, 
                   from_name: str = None) -> Tuple[bool, str]:
        """
        Wysyła pojedynczy e-mail
        
        Args:
            to_email: Adres e-mail odbiorcy
            subject: Temat e-maila
            html_content: Treść HTML
            text_content: Treść tekstowa
            from_email: Adres nadawcy
            from_name: Nazwa nadawcy
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        pass
    
    @abstractmethod
    def send_batch(self, emails: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, int]]:
        """
        Wysyła e-maile w batchu
        
        Args:
            emails: Lista e-maili do wysłania
            
        Returns:
            Tuple[bool, str, Dict[str, int]]: (sukces, komunikat, statystyki)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Sprawdza czy provider jest dostępny
        
        Returns:
            bool: True jeśli dostępny
        """
        pass
    
    def set_logger(self, logger):
        """Ustawia logger"""
        self.logger = logger




