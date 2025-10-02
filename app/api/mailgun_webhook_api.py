"""
Mailgun Webhook API - śledzenie dostarczenia emaili
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import EmailLog
import logging
import hashlib
import hmac
import json
import os
from datetime import datetime
from app.utils.timezone_utils import get_local_now

mailgun_webhook_bp = Blueprint('mailgun_webhook', __name__)

def verify_mailgun_signature(timestamp, token, signature):
    """Weryfikuje podpis webhooka Mailgun"""
    try:
        api_key = os.getenv('MAILGUN_API_KEY', '')
        if not api_key:
            return False
        
        # Mailgun używa HMAC-SHA256
        signing_string = f"{timestamp}{token}"
        expected_signature = hmac.new(
            api_key.encode('utf-8'),
            signing_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logging.error(f"Error verifying Mailgun signature: {e}")
        return False

@mailgun_webhook_bp.route('/webhook/mailgun/delivered', methods=['POST'])
def mailgun_delivered():
    """Webhook dla dostarczonych emaili"""
    try:
        # Pobierz dane z webhooka
        data = request.form.to_dict()
        
        # Weryfikuj podpis (opcjonalne w trybie testowym)
        if os.getenv('MAILGUN_VERIFY_WEBHOOKS', 'true').lower() == 'true':
            timestamp = request.headers.get('X-Mailgun-Timestamp')
            token = request.headers.get('X-Mailgun-Token')
            signature = request.headers.get('X-Mailgun-Signature')
            
            if not verify_mailgun_signature(timestamp, token, signature):
                logging.warning("Invalid Mailgun webhook signature")
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 401
        
        # Pobierz dane z webhooka
        recipient = data.get('recipient')
        message_id = data.get('Message-Id')
        event = data.get('event', 'delivered')
        
        if not recipient or not message_id:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Znajdź email w logach po message_id
        email_log = EmailLog.query.filter_by(
            message_id=message_id
        ).first()
        
        if not email_log:
            # Jeśli nie znajdziemy po message_id, spróbuj po adresie i czasie
            # Mailgun czasami nie przekazuje message_id
            logging.warning(f"Email log not found for message_id: {message_id}")
            return jsonify({'status': 'ok', 'message': 'Email log not found'})
        
        # Aktualizuj status
        if event == 'delivered':
            email_log.status = 'delivered'
        elif event == 'opened':
            email_log.status = 'opened'
        elif event == 'clicked':
            email_log.status = 'clicked'
        elif event == 'bounced':
            email_log.status = 'bounced'
        elif event == 'complained':
            email_log.status = 'complained'
        
        # Dodaj informacje o webhooku
        webhook_data = {
            'event': event,
            'timestamp': get_local_now().isoformat(),
            'recipient': recipient,
            'message_id': message_id,
            'raw_data': data
        }
        
        # Zapisz dane webhooka w recipient_data
        if email_log.recipient_data:
            try:
                existing_data = json.loads(email_log.recipient_data)
                if 'webhooks' not in existing_data:
                    existing_data['webhooks'] = []
                existing_data['webhooks'].append(webhook_data)
                email_log.recipient_data = json.dumps(existing_data)
            except (json.JSONDecodeError, TypeError):
                email_log.recipient_data = json.dumps({'webhooks': [webhook_data]})
        else:
            email_log.recipient_data = json.dumps({'webhooks': [webhook_data]})
        
        db.session.commit()
        
        logging.info(f"✅ Email status updated: {recipient} -> {event}")
        
        return jsonify({'status': 'ok', 'message': 'Status updated'})
        
    except Exception as e:
        logging.error(f"Error processing Mailgun webhook: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@mailgun_webhook_bp.route('/webhook/mailgun/opened', methods=['POST'])
def mailgun_opened():
    """Webhook dla otwartych emaili"""
    return mailgun_delivered()  # Użyj tej samej logiki

@mailgun_webhook_bp.route('/webhook/mailgun/clicked', methods=['POST'])
def mailgun_clicked():
    """Webhook dla klikniętych emaili"""
    return mailgun_delivered()  # Użyj tej samej logiki

@mailgun_webhook_bp.route('/webhook/mailgun/bounced', methods=['POST'])
def mailgun_bounced():
    """Webhook dla odrzuconych emaili"""
    return mailgun_delivered()  # Użyj tej samej logiki

@mailgun_webhook_bp.route('/webhook/mailgun/complained', methods=['POST'])
def mailgun_complained():
    """Webhook dla skarg na emaile"""
    return mailgun_delivered()  # Użyj tej samej logiki

@mailgun_webhook_bp.route('/webhook/mailgun/failed', methods=['POST'])
def mailgun_failed():
    """Webhook dla nieudanych emaili"""
    try:
        data = request.form.to_dict()
        
        recipient = data.get('recipient')
        message_id = data.get('Message-Id')
        error_message = data.get('delivery-status', 'Unknown error')
        
        if not recipient or not message_id:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Znajdź email w logach
        email_log = EmailLog.query.filter_by(
            message_id=message_id
        ).first()
        
        if not email_log:
            logging.warning(f"Email log not found for failed message_id: {message_id}")
            return jsonify({'status': 'ok', 'message': 'Email log not found'})
        
        # Aktualizuj status na failed
        email_log.status = 'failed'
        email_log.error_message = error_message
        
        # Dodaj informacje o błędzie
        webhook_data = {
            'event': 'failed',
            'timestamp': get_local_now().isoformat(),
            'recipient': recipient,
            'message_id': message_id,
            'error_message': error_message,
            'raw_data': data
        }
        
        if email_log.recipient_data:
            try:
                existing_data = json.loads(email_log.recipient_data)
                if 'webhooks' not in existing_data:
                    existing_data['webhooks'] = []
                existing_data['webhooks'].append(webhook_data)
                email_log.recipient_data = json.dumps(existing_data)
            except (json.JSONDecodeError, TypeError):
                email_log.recipient_data = json.dumps({'webhooks': [webhook_data]})
        else:
            email_log.recipient_data = json.dumps({'webhooks': [webhook_data]})
        
        db.session.commit()
        
        logging.error(f"❌ Email failed: {recipient} - {error_message}")
        
        return jsonify({'status': 'ok', 'message': 'Status updated'})
        
    except Exception as e:
        logging.error(f"Error processing Mailgun failed webhook: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@mailgun_webhook_bp.route('/webhook/mailgun/test', methods=['GET', 'POST'])
def mailgun_webhook_test():
    """Test endpoint dla webhooków Mailgun"""
    if request.method == 'GET':
        return jsonify({
            'status': 'ok',
            'message': 'Mailgun webhook endpoint is working',
            'endpoints': {
                'delivered': '/webhook/mailgun/delivered',
                'opened': '/webhook/mailgun/opened',
                'clicked': '/webhook/mailgun/clicked',
                'bounced': '/webhook/mailgun/bounced',
                'complained': '/webhook/mailgun/complained',
                'failed': '/webhook/mailgun/failed'
            }
        })
    
    # POST - symulacja webhooka
    data = request.get_json() or request.form.to_dict()
    
    return jsonify({
        'status': 'ok',
        'message': 'Test webhook received',
        'data': data
    })
