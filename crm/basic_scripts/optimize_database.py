"""
Database optimization script: indexes and cleanup

Run with: FLASK_APP=app.py flask shell -c 'import crm.basic_scripts.optimize_database as s; s.run()'
Or: python -m crm.basic_scripts.optimize_database
"""
import os
from contextlib import contextmanager

from flask import Flask
from sqlalchemy import text

# Reuse the app factory to get SQLAlchemy engine
from app import create_app
from app.models import db


@contextmanager
def app_context():
    app = create_app()
    with app.app_context():
        yield app


def run():
    with app_context():
        engine = db.engine
        conn = engine.connect()
        trans = conn.begin()
        try:
            statements = [
                # Drop unused tables if they exist
                "DROP TABLE IF EXISTS event_notifications CASCADE;",
                "DROP TABLE IF EXISTS event_recipient_groups CASCADE;",
                # Useful indexes
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);",
                "CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_active);",
                "CREATE INDEX IF NOT EXISTS idx_event_schedule_date ON event_schedule (event_date);",
                "CREATE INDEX IF NOT EXISTS idx_event_schedule_published ON event_schedule (is_published);",
                "CREATE INDEX IF NOT EXISTS idx_event_schedule_active ON event_schedule (is_active);",
                "CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue (status);",
                "CREATE INDEX IF NOT EXISTS idx_email_queue_scheduled ON email_queue (scheduled_at);",
                "CREATE INDEX IF NOT EXISTS idx_crm_contacts_phone ON crm_contacts (phone);",
                "CREATE INDEX IF NOT EXISTS idx_crm_contacts_ankieter ON crm_contacts (assigned_ankieter_id);",
                "CREATE INDEX IF NOT EXISTS idx_crm_calls_status ON crm_calls (status);",
                "CREATE INDEX IF NOT EXISTS idx_crm_calls_date ON crm_calls (call_date);",
            ]

            for stmt in statements:
                conn.execute(text(stmt))
            trans.commit()
            print("✅ Optimization completed: tables cleaned and indexes ensured.")
        except Exception as e:
            trans.rollback()
            print(f"❌ Optimization failed: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    run()
