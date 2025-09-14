#!/usr/bin/env python3
"""
Skrypt do tworzenia szablonu kampanii emailowej
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, EmailTemplate

def create_campaign_template():
    """Tworzy szablon kampanii emailowej"""
    app = create_app()
    
    with app.app_context():
        template_name = 'campaign_newsletter'
        existing_template = EmailTemplate.query.filter_by(name=template_name).first()
        
        if not existing_template:
            template = EmailTemplate(
                name=template_name,
                subject='{{newsletter_title}} - Newsletter Klubu Lepsze Życie',
                html_content='''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
                    <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Klub Lepsze Życie</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">{{newsletter_title}}</p>
                    </div>
                    
                    <div style="padding: 30px; background-color: white;">
                        <h2 style="color: #2c3e50; margin-bottom: 20px;">{{main_heading}}</h2>
                        
                        <div style="margin-bottom: 25px;">
                            {{main_content}}
                        </div>
                        
                        <div style="background-color: #e9ecef; padding: 20px; border-radius: 8px; margin: 25px 0;">
                            <h3 style="color: #2c3e50; margin-top: 0;">{{highlight_title}}</h3>
                            <p style="margin-bottom: 0;">{{highlight_content}}</p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{{cta_url}}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                {{cta_text}}
                            </a>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                        
                        <div style="text-align: center; color: #6c757d; font-size: 14px;">
                            <p>Dziękujemy za bycie częścią naszej społeczności!</p>
                            <p>Zespół Klubu Lepsze Życie</p>
                        </div>
                    </div>
                </div>
                ''',
                text_content='''
                {{newsletter_title}} - Newsletter Klubu Lepsze Życie
                
                {{main_heading}}
                
                {{main_content}}
                
                {{highlight_title}}
                {{highlight_content}}
                
                {{cta_text}}: {{cta_url}}
                
                Dziękujemy za bycie częścią naszej społeczności!
                Zespół Klubu Lepsze Życie
                ''',
                template_type='campaign',
                variables='["newsletter_title", "main_heading", "main_content", "highlight_title", "highlight_content", "cta_text", "cta_url"]'
            )
            
            db.session.add(template)
            db.session.commit()
            print(f"✅ Szablon {template_name} został utworzony pomyślnie!")
        else:
            print(f"❌ Szablon {template_name} już istnieje.")

if __name__ == '__main__':
    create_campaign_template()


