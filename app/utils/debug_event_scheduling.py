"""
Skrypt diagnostyczny do debugowania planowania emaili dla wydarzeń

Użycie:
    python app/utils/debug_event_scheduling.py <event_id>
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app, db
from app.models import EventSchedule, EmailQueue, EmailReminder, EmailTemplate, User, UserGroup, UserGroupMember
from app.utils.timezone_utils import get_local_now


def debug_event(event_id: int):
    """Debugowanie wydarzenia"""
    
    app = create_app()
    
    with app.app_context():
        print(f"\n{'='*80}")
        print(f"DIAGNOSTYKA WYDARZENIA ID: {event_id}")
        print(f"{'='*80}\n")
        
        # 1. Sprawdź czy wydarzenie istnieje
        event = EventSchedule.query.get(event_id)
        
        if not event:
            print(f"❌ PROBLEM: Wydarzenie o ID {event_id} nie zostało znalezione w bazie")
            return False
        
        print(f"✅ Wydarzenie znalezione: {event.title}")
        print(f"   Data wydarzenia: {event.event_date}")
        print(f"   is_active: {event.is_active}")
        print(f"   is_published: {event.is_published}")
        print(f"   reminders_scheduled: {event.reminders_scheduled}")
        print()
        
        # 2. Sprawdź czas do wydarzenia
        now = get_local_now()
        now_naive = now.replace(tzinfo=None) if hasattr(now, 'tzinfo') and now.tzinfo else now
        event_date_naive = event.event_date.replace(tzinfo=None) if hasattr(event.event_date, 'tzinfo') and event.event_date.tzinfo else event.event_date
        
        time_until_event = event_date_naive - now_naive
        hours_until = time_until_event.total_seconds() / 3600
        
        print(f"⏰ Czas do wydarzenia:")
        print(f"   Teraz: {now_naive}")
        print(f"   Data wydarzenia: {event_date_naive}")
        print(f"   Pozostało: {time_until_event} ({hours_until:.2f} godzin)")
        
        if time_until_event < timedelta(minutes=5):
            print(f"   ❌ PROBLEM: Za mało czasu do wydarzenia (< 5 minut)")
            print(f"      System nie planuje przypomnień dla wydarzeń za < 5 minut")
        elif time_until_event < timedelta(hours=1):
            print(f"   ⚠️ UWAGA: Zostanie zaplanowane tylko 1 przypomnienie (5min)")
        elif time_until_event < timedelta(hours=24):
            print(f"   ✅ OK: Zostaną zaplanowane 2 przypomnienia (1h, 5min)")
        else:
            print(f"   ✅ OK: Zostaną zaplanowane 3 przypomnienia (24h, 1h, 5min)")
        print()
        
        # 3. Sprawdź uczestników
        print(f"👥 Sprawdzanie uczestników:")
        
        # Członkowie klubu
        club_members = User.query.filter_by(
            club_member=True,
            is_active=True
        ).all()
        club_members_with_email = [u for u in club_members if u.email]
        print(f"   Członkowie klubu: {len(club_members_with_email)}")
        
        # Członkowie grupy wydarzenia
        event_group = UserGroup.query.filter_by(
            group_type='event_based',
            event_id=event_id
        ).first()
        
        if event_group:
            group_members = UserGroupMember.query.filter_by(
                group_id=event_group.id,
                is_active=True
            ).all()
            
            group_users = []
            for member in group_members:
                user = User.query.get(member.user_id)
                if user and user.is_active and user.email:
                    group_users.append(user)
            
            print(f"   Członkowie grupy wydarzenia: {len(group_users)}")
        else:
            print(f"   Grupa wydarzenia: Brak")
        
        # Unikalni uczestnicy
        all_participants = set()
        for user in club_members_with_email:
            all_participants.add(user.id)
        
        if event_group:
            for user in group_users:
                all_participants.add(user.id)
        
        total_participants = len(all_participants)
        print(f"   ŁĄCZNIE unikalnych uczestników: {total_participants}")
        
        if total_participants == 0:
            print(f"   ❌ PROBLEM: Brak uczestników!")
            print(f"      Sprawdź czy są członkowie klubu lub grupa wydarzenia")
        else:
            print(f"   ✅ OK: Znaleziono uczestników")
        print()
        
        # 4. Sprawdź szablony
        print(f"📧 Sprawdzanie szablonów:")
        templates_needed = []
        
        if hours_until >= 24:
            templates_needed = ['24h', '1h', '5min']
        elif hours_until >= 1:
            templates_needed = ['1h', '5min']
        elif hours_until >= 0.083:  # 5 minut
            templates_needed = ['5min']
        
        templates_ok = True
        for reminder_type in templates_needed:
            template_name = f'event_reminder_{reminder_type}'
            template = EmailTemplate.query.filter_by(
                name=template_name,
                is_active=True
            ).first()
            
            if template:
                print(f"   ✅ {template_name} (ID: {template.id})")
            else:
                print(f"   ❌ PROBLEM: {template_name} NIE ZNALEZIONY!")
                templates_ok = False
        
        if not templates_ok:
            print(f"   ❌ PROBLEM: Brakuje szablonów emaili!")
        print()
        
        # 5. Sprawdź kolejkę emaili
        print(f"📬 Sprawdzanie kolejki emaili:")
        queue_items = EmailQueue.query.filter_by(
            event_id=event_id,
            status='pending'
        ).all()
        
        print(f"   Emaile w kolejce (pending): {len(queue_items)}")
        
        if queue_items:
            print(f"   Szczegóły:")
            for item in queue_items[:10]:  # Pokaż max 10
                print(f"      - {item.template_name} -> {item.recipient_email}")
                print(f"        scheduled_at: {item.scheduled_at}")
                print(f"        priority: {item.priority}")
        else:
            print(f"   ⚠️ BRAK emaili w kolejce")
        print()
        
        # 6. Sprawdź EmailReminder
        print(f"📋 Sprawdzanie EmailReminder:")
        reminders = EmailReminder.query.filter_by(event_id=event_id).all()
        print(f"   Wpisów w EmailReminder: {len(reminders)}")
        
        if reminders:
            reminder_types = {}
            for reminder in reminders:
                reminder_types[reminder.reminder_type] = reminder_types.get(reminder.reminder_type, 0) + 1
            
            print(f"   Podział:")
            for rtype, count in reminder_types.items():
                print(f"      - {rtype}: {count}")
        print()
        
        # 7. Podsumowanie i sugestie
        print(f"\n{'='*80}")
        print(f"PODSUMOWANIE I SUGESTIE")
        print(f"{'='*80}\n")
        
        problems = []
        
        if event.reminders_scheduled:
            problems.append("Flaga reminders_scheduled=True (system pomija to wydarzenie)")
        
        if time_until_event < timedelta(minutes=5):
            problems.append("Za mało czasu do wydarzenia (< 5 minut)")
        
        if total_participants == 0:
            problems.append("Brak uczestników (członkowie klubu + grupa wydarzenia)")
        
        if not templates_ok:
            problems.append("Brakuje szablonów emaili")
        
        if not event.is_active:
            problems.append("Wydarzenie nieaktywne (is_active=False)")
        
        if problems:
            print("❌ ZNALEZIONE PROBLEMY:")
            for i, problem in enumerate(problems, 1):
                print(f"   {i}. {problem}")
            print()
            
            print("🔧 ROZWIĄZANIA:")
            
            if "reminders_scheduled=True" in str(problems):
                print(f"\n   1. Zresetuj flagę i zaplanuj ponownie:")
                print(f"      python app/utils/reschedule_event.py {event_id}")
                print(f"   LUB")
                print(f"      curl -X POST http://localhost:5000/api/events/schedules/{event_id}/reschedule-reminders")
            
            if "Brak uczestników" in str(problems):
                print(f"\n   2. Dodaj członków klubu lub utwórz grupę wydarzenia")
            
            if "Brakuje szablonów" in str(problems):
                print(f"\n   3. Utwórz brakujące szablony emaili w panelu admina")
            
            if "nieaktywne" in str(problems):
                print(f"\n   4. Aktywuj wydarzenie (is_active=True)")
        else:
            print("✅ Nie znaleziono problemów!")
            print()
            print("🔧 Możliwe rozwiązania:")
            print(f"\n   1. Zaplanuj przypomnienia:")
            print(f"      python app/utils/reschedule_event.py {event_id}")
            print(f"\n   2. Czekaj na automatyczny task (co 5 minut):")
            print(f"      process_event_reminders_task sprawdzi wydarzenia")
            print(f"\n   3. Sprawdź logi Celery:")
            print(f"      tail -f app/logs/app_console.log")


def main():
    if len(sys.argv) < 2:
        print("""
Użycie:
    python app/utils/debug_event_scheduling.py <event_id>
    
Przykład:
    python app/utils/debug_event_scheduling.py 123
        """)
        sys.exit(1)
    
    try:
        event_id = int(sys.argv[1])
        debug_event(event_id)
    except ValueError:
        print(f"❌ Nieprawidłowe ID wydarzenia: {sys.argv[1]}")
        sys.exit(1)


if __name__ == '__main__':
    main()

