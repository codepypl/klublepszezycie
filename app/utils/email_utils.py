"""
Email utilities for proper encoding and formatting
"""
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
import re

def create_proper_from_header(from_name: str, from_email: str) -> str:
    """
    Create properly encoded From header for emails
    
    Args:
        from_name: Sender name (can contain Unicode characters)
        from_email: Sender email address
        
    Returns:
        Properly encoded From header string
    """
    try:
        # Convert Polish characters to ASCII to avoid RFC 2047 encoding
        from unidecode import unidecode
        ascii_name = unidecode(from_name)
        
        # Use simple format to avoid encoding issues
        return f"{ascii_name} <{from_email}>"
    except Exception:
        # Fallback to simple format
        return f"{from_name} <{from_email}>"

def create_proper_subject(subject: str) -> str:
    """
    Create properly encoded Subject header for emails
    
    Args:
        subject: Email subject (can contain Unicode characters)
        
    Returns:
        Properly encoded Subject header string
    """
    try:
        # Convert Polish characters to ASCII to avoid RFC 2047 encoding
        from unidecode import unidecode
        ascii_subject = unidecode(subject)
        return ascii_subject
    except Exception:
        # Fallback to original subject
        return subject

def create_email_message(to_email: str, subject: str, html_content: str, 
                        text_content: str = None, from_name: str = None, 
                        from_email: str = None) -> MIMEMultipart:
    """
    Create properly formatted email message with correct encoding
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content (optional)
        from_name: Sender name (optional)
        from_email: Sender email address (optional)
        
    Returns:
        Properly formatted MIMEMultipart message
    """
    # Create message
    msg = MIMEMultipart('alternative')
    
    # Set headers with proper encoding
    if from_name and from_email:
        msg['From'] = create_proper_from_header(from_name, from_email)
    else:
        msg['From'] = from_email or 'noreply@klublepszezycie.pl'
    
    msg['To'] = to_email
    msg['Subject'] = create_proper_subject(subject)
    
    # Add text content
    if text_content:
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
    
    # Add HTML content
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    return msg

def test_email_encoding():
    """Test function to verify email encoding works correctly"""
    
    # Test cases
    test_cases = [
        ("Klub Lepsze Życie", "noreply@klublepszezycie.pl"),
        ("Test Name", "test@example.com"),
        ("Müller", "mueller@example.com"),
        ("José", "jose@example.com"),
    ]
    
    print("=== EMAIL ENCODING TEST ===")
    
    for name, email in test_cases:
        from_header = create_proper_from_header(name, email)
        subject = create_proper_subject(f"Test email from {name}")
        
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"From header: {from_header}")
        print(f"Subject: {subject}")
        print()

if __name__ == "__main__":
    test_email_encoding()
