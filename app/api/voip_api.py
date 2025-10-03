"""
VoIP API endpoints for Twilio integration
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.auth_utils import ankieter_required
from app.services.twilio_service import twilio_service
from app.models import db
from app.models.crm_model import Call
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create blueprint
voip_api_bp = Blueprint('voip_api', __name__, url_prefix='/api/voip')

@voip_api_bp.route('/twilio/make-call', methods=['POST'])
@login_required
@ankieter_required
def make_twilio_call():
    """Make a call through Twilio"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        phone_number = data.get('phone_number')
        
        if not contact_id or not phone_number:
            return jsonify({'success': False, 'error': 'Contact ID and phone number required'}), 400
        
        # Check if Twilio is configured
        if not twilio_service.is_configured():
            return jsonify({'success': False, 'error': 'Twilio nie jest skonfigurowane'}), 500
        
        # Create call record in database
        now = datetime.utcnow()
        call = Call(
            contact_id=contact_id,
            ankieter_id=current_user.id,
            call_date=now,
            call_start_time=now,
            status='initiated',
            phone_number=phone_number
        )
        db.session.add(call)
        db.session.commit()
        
        # Make Twilio call
        result = twilio_service.make_call(
            to_number=phone_number,
            agent_id=current_user.id,
            contact_id=contact_id
        )
        
        if result['success']:
            # Update call record with Twilio SID
            call.twilio_sid = result['call_sid']
            call.status = 'ringing'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'call_id': call.id,
                'twilio_sid': result['call_sid'],
                'status': result['status'],
                'start_time': now.isoformat()
            })
        else:
            # Update call record with error
            call.status = 'failed'
            call.notes = f"Twilio error: {result['error']}"
            db.session.commit()
            
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"❌ Error making Twilio call: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@voip_api_bp.route('/twilio/end-call', methods=['POST'])
@login_required
@ankieter_required
def end_twilio_call():
    """End a Twilio call"""
    try:
        data = request.get_json()
        call_id = data.get('call_id')
        twilio_sid = data.get('twilio_sid')
        
        if not twilio_sid:
            return jsonify({'success': False, 'error': 'Twilio SID required'}), 400
        
        # End call in Twilio
        result = twilio_service.end_call(twilio_sid)
        
        if result['success']:
            # Update call record in database
            if call_id:
                call = Call.query.get(call_id)
                if call:
                    call.status = 'completed'
                    call.call_end_time = datetime.utcnow()
                    db.session.commit()
            
            return jsonify({'success': True, 'status': result['status']})
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"❌ Error ending Twilio call: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@voip_api_bp.route('/twilio/call-status', methods=['POST'])
@login_required
def get_twilio_call_status():
    """Get status of a Twilio call"""
    try:
        data = request.get_json()
        twilio_sid = data.get('twilio_sid')
        
        if not twilio_sid:
            return jsonify({'success': False, 'error': 'Twilio SID required'}), 400
        
        result = twilio_service.get_call_status(twilio_sid)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error getting call status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@voip_api_bp.route('/twilio/voice', methods=['POST'])
def twilio_voice_webhook():
    """
    Twilio webhook for voice calls
    This is called when Twilio needs TwiML instructions
    """
    try:
        # Get call direction from Twilio
        call_direction = request.form.get('Direction')
        called_number = request.form.get('Called')
        from_number = request.form.get('From')
        
        logger.info(f"📞 Twilio voice webhook - Direction: {call_direction}, From: {from_number}, To: {called_number}")
        
        if call_direction == 'outbound-api':
            # This is an outbound call we initiated
            # Generate TwiML for the customer
            twiml = twilio_service.generate_twiml_for_customer()
        else:
            # This is an inbound call
            # Generate TwiML for the agent
            twiml = twilio_service.generate_twiml_for_agent()
        
        # Return TwiML response
        from flask import Response
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"❌ Error in Twilio voice webhook: {e}")
        # Return empty TwiML on error
        from flask import Response
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', mimetype='text/xml')

@voip_api_bp.route('/twilio/status', methods=['POST'])
def twilio_status_webhook():
    """
    Twilio webhook for call status updates
    This is called when call status changes
    """
    try:
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        duration = request.form.get('Duration')
        
        logger.info(f"📞 Twilio status webhook - SID: {call_sid}, Status: {call_status}, Duration: {duration}")
        
        # Update call record in database
        call = Call.query.filter_by(twilio_sid=call_sid).first()
        if call:
            call.status = call_status.lower()
            
            if call_status == 'completed':
                call.call_end_time = datetime.utcnow()
                if duration:
                    call.duration = int(duration)
            
            db.session.commit()
            logger.info(f"✅ Updated call {call.id} status to {call_status}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"❌ Error in Twilio status webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@voip_api_bp.route('/twilio/recording', methods=['POST'])
@login_required
@ankieter_required
def get_call_recording():
    """Get recording URL for a call"""
    try:
        data = request.get_json()
        twilio_sid = data.get('twilio_sid')
        
        if not twilio_sid:
            return jsonify({'success': False, 'error': 'Twilio SID required'}), 400
        
        result = twilio_service.get_call_recording(twilio_sid)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error getting recording: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
