#!/usr/bin/env python3
"""
Uproszczony skrypt do uruchomienia harmonogramu e-maili
"""

from app import app, db
from models import EventEmailSchedule, User, EmailTemplate
from services.email_service import EmailService
from datetime import datetime

def run_schedule_5min():
    """Uruchom harmonogram 5min przed wydarzeniem"""
    
    with app.app_context():
        try:
            print("🚀 URUCHAMIANIE HARMONOGRAMU 5MIN...")
            
            # 1. Znajdź harmonogram (używając nowoczesnej składni SQLAlchemy)
            schedule = db.session.get(EventEmailSchedule, 48)
            if not schedule:
                print("❌ Harmonogram ID 48 nie znaleziony")
                return
            
            print(f"✅ Harmonogram znaleziony: {schedule.notification_type}")
            
            # 2. Znajdź członków klubu
            club_members = User.query.filter_by(club_member=True, is_active=True).all()
            emails = [member.email for member in club_members if member.email]
            
            print(f"👥 Członkowie klubu: {len(emails)}")
            
            # 3. Inicjalizuj EmailService z aplikacją Flask
            email_service = EmailService()
            email_service.init_app(app)
            
            print("📧 Wysyłam e-maile...")
            success = 0
            
            for email in emails:
                try:
                    result = email_service.send_template_email(
                        to_email=email,
                        template_name='event_reminder_5min_before',
                        variables={
                            'event_title': 'Wydarzenie Klubu',
                            'event_date': datetime.now().strftime('%d.%m.%Y %H:%M')
                        }
                    )
                    
                    if result:
                        success += 1
                        print(f"   ✅ {email}")
                    else:
                        print(f"   ❌ {email}")
                        
                except Exception as e:
                    print(f"   ❌ {email} - {e}")
            
            # 4. Zaktualizuj status harmonogramu
            schedule.status = 'sent'
            schedule.sent_at = datetime.utcnow()
            db.session.commit()
            
            print(f"\n🎉 GOTOWE! Wysłano: {success}/{len(emails)}")
            
        except Exception as e:
            print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    run_schedule_5min()
