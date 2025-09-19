#!/usr/bin/env python3
"""
Script to initialize all statistics in the Stats table
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import Stats

def main():
    """Initialize all statistics"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Initializing all statistics...")
        
        try:
            # Update all statistics
            results = Stats.update_all_stats()
            
            print("✅ Statistics initialized successfully!")
            print("\n📊 Statistics Summary:")
            print("=" * 50)
            
            # Users
            print(f"👥 Users:")
            print(f"  Total: {results.get('total_users', 0)}")
            print(f"  Active: {results.get('active_users', 0)}")
            print(f"  Admin: {results.get('admin_users', 0)}")
            print(f"  New (30 days): {results.get('new_users_30_days', 0)}")
            print(f"  Event Registrations: {results.get('total_registrations', 0)}")
            
            # Events
            print(f"\n📅 Events:")
            print(f"  Total: {results.get('total_events', 0)}")
            
            # Blog
            print(f"\n📝 Blog:")
            print(f"  Posts: {results.get('blog_posts', 0)}")
            print(f"  Categories: {results.get('blog_categories', 0)}")
            print(f"  Comments: {results.get('blog_comments', 0)}")
            
            # CRM
            print(f"\n📞 CRM:")
            print(f"  Contacts: {results.get('total_contacts', 0)}")
            print(f"  Calls: {results.get('total_calls', 0)}")
            print(f"  Imports: {results.get('total_imports', 0)}")
            print(f"  Blacklist: {results.get('total_blacklist', 0)}")
            print(f"  Daily Calls: {results.get('daily_calls', 0)}")
            print(f"  Daily Leads: {results.get('daily_leads', 0)}")
            
            # Email
            print(f"\n📧 Email:")
            print(f"  Total Queue: {results.get('total_emails', 0)}")
            print(f"  Pending: {results.get('pending_emails', 0)}")
            print(f"  Sent: {results.get('sent_emails', 0)}")
            print(f"  Failed: {results.get('failed_emails', 0)}")
            print(f"  Logs: {results.get('total_email_logs', 0)}")
            print(f"  Bounced: {results.get('bounced_emails', 0)}")
            
            # Other
            print(f"\n💬 Other:")
            print(f"  Testimonials: {results.get('total_testimonials', 0)}")
            
            print("\n" + "=" * 50)
            print("🎉 All statistics have been successfully initialized!")
            
        except Exception as e:
            print(f"❌ Error initializing statistics: {str(e)}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
