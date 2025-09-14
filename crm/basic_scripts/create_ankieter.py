#!/usr/bin/env python3
"""
Script to create an ankieter user
"""
import os
import sys
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_ankieter():
    """Create an ankieter user"""
    try:
        from app import create_app
        from models import User, db
        
        # Create app
        app = create_app()
        
        with app.app_context():
            # Check if ankieter already exists
            existing_ankieter = User.query.filter_by(email='ankieter@lepszezycie.pl').first()
            if existing_ankieter:
                print("✅ Ankieter already exists!")
                print(f"   Email: {existing_ankieter.email}")
                print(f"   Role: {existing_ankieter.role}")
                return
            
            # Create ankieter user
            ankieter = User(
                email='ankieter@lepszezycie.pl',
                password_hash=generate_password_hash('ankieter123'),
                name='Ankieter Testowy',
                phone='+48 123 456 789',
                role='ankieter',
                is_active=True,
                is_temporary_password=True
            )
            
            db.session.add(ankieter)
            db.session.commit()
            
            print("✅ Ankieter user created successfully!")
            print(f"   Email: {ankieter.email}")
            print(f"   Password: ankieter123")
            print(f"   Role: {ankieter.role}")
            print(f"   Name: {ankieter.name}")
            print(f"   Phone: {ankieter.phone}")
            print("\n🔐 Login credentials:")
            print("   Email: ankieter@lepszezycie.pl")
            print("   Password: ankieter123")
            print("\n🌐 Access the ankieter dashboard at: http://localhost:5000/ankieter/")
            
    except Exception as e:
        print(f"❌ Error creating ankieter: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_ankieter()
