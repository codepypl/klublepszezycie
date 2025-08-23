#!/usr/bin/env python3
"""
Database migration script for Better Life Club
Adds new columns and tables as needed
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Section, Page
import json

def migrate_database():
    """Add new columns to sections table and update existing data"""
    with app.app_context():
        print("Starting database migration...")
        
        # Check if pages table exists
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT 1 FROM pages LIMIT 1"))
                conn.commit()
            print("✓ Pages table already exists")
        except:
            print("Creating pages table...")
            db.create_all()
            print("✓ Pages table created")
        
        # Check if new columns exist in sections table
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("SELECT enable_pillars FROM sections LIMIT 1"))
                conn.commit()
            print("✓ New columns already exist in sections table")
        except:
            print("Adding new columns to sections table...")
            
            # Add new columns
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN enable_pillars BOOLEAN DEFAULT FALSE"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN enable_floating_cards BOOLEAN DEFAULT FALSE"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN pillars_count INTEGER DEFAULT 4"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN floating_cards_count INTEGER DEFAULT 3"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN pillars_data TEXT"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN floating_cards_data TEXT"))
                conn.execute(db.text("ALTER TABLE sections ADD COLUMN final_text TEXT"))
                conn.commit()
            
            print("✓ New columns added to sections table")
        
        # Update existing pillars and floating cards data to include links
        print("\nUpdating existing data with links...")
        about_section = Section.query.filter_by(name='about').first()
        if about_section:
            # Update pillars data
            if about_section.pillars_data:
                try:
                    pillars = json.loads(about_section.pillars_data)
                    updated_pillars = []
                    default_links = ['/finanse', '/zdrowie', '/spolecznosc', '/ai-technologia']
                    
                    for i, pillar in enumerate(pillars):
                        if 'link' not in pillar:
                            pillar['link'] = default_links[i] if i < len(default_links) else ''
                        updated_pillars.append(pillar)
                    
                    about_section.pillars_data = json.dumps(updated_pillars)
                    print("✓ Updated pillars data with links")
                except json.JSONDecodeError:
                    print("⚠ Could not parse existing pillars data")
            
            # Update floating cards data
            if about_section.floating_cards_data:
                try:
                    floating_cards = json.loads(about_section.floating_cards_data)
                    updated_floating_cards = []
                    default_links = ['/inspiracja', '/wiedza', '/rozwoj']
                    
                    for i, card in enumerate(floating_cards):
                        if 'link' not in card:
                            card['link'] = default_links[i] if i < len(default_links) else ''
                        updated_floating_cards.append(card)
                    
                    about_section.floating_cards_data = json.dumps(updated_floating_cards)
                    print("✓ Updated floating cards data with links")
                except json.JSONDecodeError:
                    print("⚠ Could not parse existing floating cards data")
            
            # Enable pillars and floating cards for about section
            about_section.enable_pillars = True
            about_section.enable_floating_cards = True
            about_section.pillars_count = 4
            about_section.floating_cards_count = 3
            
            db.session.commit()
            print("✓ Database updated successfully")
        else:
            print("⚠ About section not found")
        
        # Create sample pages if none exist
        if Page.query.count() == 0:
            print("\nCreating sample pages...")
            
            sample_pages = [
                {
                    'title': 'O Nas',
                    'slug': 'o-nas',
                    'content': '<h2>O Nas</h2><p>Jesteśmy klubem dla osób 50+, który pomaga w osiąganiu lepszego życia.</p>',
                    'meta_description': 'Poznaj nasz klub i dowiedz się jak pomagamy osobom 50+ w osiąganiu lepszego życia.',
                    'meta_keywords': 'klub, 50+, lepsze życie, seniorzy',
                    'is_active': True,
                    'is_published': True
                },
                {
                    'title': 'Kontakt',
                    'slug': 'kontakt',
                    'content': '<h2>Kontakt</h2><p>Skontaktuj się z nami w dowolny sposób.</p><p><strong>Email:</strong> kontakt@lepszezycie.pl</p><p><strong>Telefon:</strong> +48 123 456 789</p>',
                    'meta_description': 'Skontaktuj się z nami. Jesteśmy dostępni przez email, telefon i formularz kontaktowy.',
                    'meta_keywords': 'kontakt, email, telefon, formularz',
                    'is_active': True,
                    'is_published': True
                }
            ]
            
            for page_data in sample_pages:
                page = Page(**page_data)
                db.session.add(page)
            
            db.session.commit()
            print("✓ Sample pages created")
        
        print("\n🎉 Migration completed successfully!")
        print("You can now use the new Pages feature with WYSIWYG editor!")

if __name__ == '__main__':
    migrate_database()
