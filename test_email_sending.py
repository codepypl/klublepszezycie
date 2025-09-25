#!/usr/bin/env python3
"""
Test wysyłania emaili - wysyła 100 emaili na testowy adres
"""
import requests
import json
import time

def test_email_sending():
    """Test wysyłania emaili przez API"""
    
    # Konfiguracja
    base_url = "http://localhost:8000"  # Port serwera produkcyjnego
    test_email = "codeitpy@gmail.com"
    count = 100
    batch_size = 10
    
    print(f"🧪 Rozpoczynam test wysyłania {count} emaili na {test_email}")
    print(f"📦 Rozmiar paczki: {batch_size}")
    print(f"🌐 URL: {base_url}")
    
    # Dane do wysłania
    data = {
        "test_email": test_email,
        "count": count,
        "batch_size": batch_size
    }
    
    try:
        # Wyślij żądanie
        response = requests.post(
            f"{base_url}/api/email/test-sending",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Status HTTP: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        print(f"📄 Raw response: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ Test uruchomiony pomyślnie!")
                print(f"📋 Task ID: {result.get('task_id')}")
                print(f"📧 Test email: {result.get('test_email')}")
                print(f"🔢 Liczba emaili: {result.get('count')}")
                print(f"📦 Rozmiar paczki: {result.get('batch_size')}")
                print(f"💬 Wiadomość: {result.get('message')}")
                
                # Sprawdź status zadania
                print(f"\n⏳ Sprawdzanie statusu zadania...")
                time.sleep(5)
                
                # Tutaj można dodać sprawdzanie statusu zadania przez Celery API
                print(f"📊 Sprawdź status w Flower: http://localhost:5555")
                print(f"📊 Lub sprawdź logi Celery Worker")
                
            except ValueError as e:
                print(f"❌ Błąd parsowania JSON: {e}")
                print(f"📄 Raw response: {response.text}")
        else:
            print(f"❌ Błąd HTTP: {response.status_code}")
            print(f"📄 Odpowiedź: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Błąd połączenia z {base_url}")
        print(f"💡 Upewnij się, że aplikacja Flask jest uruchomiona")
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")

if __name__ == "__main__":
    test_email_sending()
