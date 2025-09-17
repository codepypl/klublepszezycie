#!/usr/bin/env python3
"""
Test script to verify application works after removing settings tables
"""

import os
import sys
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test main models import
        from app.models import User, EventSchedule, EventRegistration, BlogPost, BlogCategory
        print("✅ Main models import successful")
        
        # Test CRM models import
        from crm.models import Contact, Call, BlacklistEntry, ImportFile, ImportRecord
        print("✅ CRM models import successful")
        
        # Test that removed models are not accessible
        try:
            from app.models import SEOSettings
            print("❌ SEOSettings should not be importable")
            return False
        except ImportError:
            print("✅ SEOSettings correctly removed")
        
        try:
            from app.models import FooterSettings
            print("❌ FooterSettings should not be importable")
            return False
        except ImportError:
            print("✅ FooterSettings correctly removed")
        
        try:
            from crm.models import CallQueue
            print("❌ CallQueue should not be importable")
            return False
        except ImportError:
            print("✅ CallQueue correctly removed")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection and basic queries"""
    print("\n🧪 Testing database connection...")
    
    try:
        from app import create_app
        from app.models import db, User
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Test basic query
            user_count = db.session.query(User).count()
            print(f"✅ Database connection successful (Users: {user_count})")
            
            # Test that removed tables don't exist
            try:
                result = db.session.execute("SELECT COUNT(*) FROM seo_settings")
                print("❌ seo_settings table should not exist")
                return False
            except Exception:
                print("✅ seo_settings table correctly removed")
            
            try:
                result = db.session.execute("SELECT COUNT(*) FROM footer_settings")
                print("❌ footer_settings table should not exist")
                return False
            except Exception:
                print("✅ footer_settings table correctly removed")
            
            try:
                result = db.session.execute("SELECT COUNT(*) FROM crm_call_queue")
                print("❌ crm_call_queue table should not exist")
                return False
            except Exception:
                print("✅ crm_call_queue table correctly removed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_blueprint_imports():
    """Test that blueprints can be imported without errors"""
    print("\n🧪 Testing blueprint imports...")
    
    try:
        from app.blueprints import public_bp, admin_bp, api_bp, auth_bp, blog_bp
        print("✅ Main blueprints import successful")
        
        from app.blueprints import seo_bp, footer_bp
        print("✅ Settings blueprints import successful")
        
        from crm.crm_api import crm_api_bp
        print("✅ CRM API blueprint import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Blueprint import test failed: {e}")
        traceback.print_exc()
        return False

def test_application_startup():
    """Test if application can start without errors"""
    print("\n🧪 Testing application startup...")
    
    try:
        from app import create_app
        
        # Create app
        app = create_app()
        
        # Test app context
        with app.app_context():
            print("✅ Application context created successfully")
            
            # Test basic route registration
            rules = [rule.rule for rule in app.url_map.iter_rules()]
            print(f"✅ Routes registered successfully ({len(rules)} routes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting post-migration tests...")
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Connection Tests", test_database_connection),
        ("Blueprint Import Tests", test_blueprint_imports),
        ("Application Startup Tests", test_application_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Application is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
