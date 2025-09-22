#!/usr/bin/env python3
"""
Prosty skrypt do wyczyszczenia kolejki emaili
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, EmailQueue

def main():
    app = create_app()
    with app.app_context():
        # Usuń wszystkie emaile oprócz wysłanych
        deleted = EmailQueue.query.filter(
            EmailQueue.status.in_(['pending', 'failed', 'processing'])
        ).delete(synchronize_session=False)
        
        db.session.commit()
        print(f"✅ Usunięto {deleted} emaili z kolejki")

if __name__ == "__main__":
    main()
