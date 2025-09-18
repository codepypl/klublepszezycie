"""
FAQ API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import FAQ, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging

faq_api_bp = Blueprint('faq_api', __name__)

@faq_api_bp.route('/faq', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_faq():
    """FAQ API"""
    if request.method == 'GET':
        try:
            faqs = FAQ.query.order_by(FAQ.order.asc()).all()
            return jsonify({
                'success': True,
                'faqs': [{
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'order': faq.order,
                    'is_active': faq.is_active,
                    'created_at': faq.created_at.isoformat() if faq.created_at else None
                } for faq in faqs]
            })
        except Exception as e:
            logging.error(f"Error getting FAQs: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            faq = FAQ(
                question=data['question'],
                answer=data['answer'],
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(faq)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'FAQ created successfully',
                'faq': {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'order': faq.order,
                    'is_active': faq.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating FAQ: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            faq_ids = data.get('faq_ids', data.get('ids', []))
            
            if not faq_ids:
                return jsonify({'success': False, 'message': 'No FAQs selected'}), 400
            
            deleted_count = 0
            for faq_id in faq_ids:
                faq = FAQ.query.get(faq_id)
                if faq:
                    db.session.delete(faq)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} FAQs'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting FAQs: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@faq_api_bp.route('/faq/<int:faq_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_faq_item(faq_id):
    """Individual FAQ API"""
    faq = FAQ.query.get_or_404(faq_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'faq': {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'order': faq.order,
                    'is_active': faq.is_active,
                    'created_at': faq.created_at.isoformat() if faq.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'question' in data:
                faq.question = data['question']
            if 'answer' in data:
                faq.answer = data['answer']
            if 'order' in data:
                faq.order = data['order']
            if 'is_active' in data:
                faq.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'FAQ updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(faq)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'FAQ deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with FAQ {faq_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@faq_api_bp.route('/bulk-delete/faq', methods=['POST'])
@login_required
@admin_required_api
def api_bulk_delete_faq():
    """Bulk delete FAQs"""
    try:
        data = request.get_json()
        faq_ids = data.get('faq_ids', data.get('ids', []))
        
        if not faq_ids:
            return jsonify({'success': False, 'message': 'No FAQs selected'}), 400
        
        deleted_count = 0
        for faq_id in faq_ids:
            faq = FAQ.query.get(faq_id)
            if faq:
                db.session.delete(faq)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} FAQs'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting FAQs: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
