"""
Testimonials API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import Testimonial, db
from app.utils.auth import admin_required
import logging

testimonials_api_bp = Blueprint('testimonials_api', __name__)

@testimonials_api_bp.route('/testimonials', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_testimonials():
    """Testimonials API"""
    if request.method == 'GET':
        try:
            testimonials = Testimonial.query.order_by(Testimonial.order.asc()).all()
            return jsonify({
                'success': True,
                'testimonials': [{
                    'id': testimonial.id,
                    'author_name': testimonial.author_name,
                    'content': testimonial.content,
                    'member_since': testimonial.member_since,
                    'order': testimonial.order,
                    'is_active': testimonial.is_active,
                    'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None
                } for testimonial in testimonials]
            })
        except Exception as e:
            logging.error(f"Error getting testimonials: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            testimonial = Testimonial(
                author_name=data['author_name'],
                content=data['content'],
                member_since=data.get('member_since', ''),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(testimonial)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Testimonial created successfully',
                'testimonial': {
                    'id': testimonial.id,
                    'author_name': testimonial.author_name,
                    'content': testimonial.content,
                    'member_since': testimonial.member_since,
                    'order': testimonial.order,
                    'is_active': testimonial.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating testimonial: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            testimonial_ids = data.get('testimonial_ids', [])
            
            if not testimonial_ids:
                return jsonify({'success': False, 'message': 'No testimonials selected'}), 400
            
            deleted_count = 0
            for testimonial_id in testimonial_ids:
                testimonial = Testimonial.query.get(testimonial_id)
                if testimonial:
                    db.session.delete(testimonial)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} testimonials'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting testimonials: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@testimonials_api_bp.route('/testimonials/<int:testimonial_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_testimonial(testimonial_id):
    """Individual testimonial API"""
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'testimonial': {
                    'id': testimonial.id,
                    'author_name': testimonial.author_name,
                    'content': testimonial.content,
                    'member_since': testimonial.member_since,
                    'order': testimonial.order,
                    'is_active': testimonial.is_active,
                    'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'author_name' in data:
                testimonial.author_name = data['author_name']
            if 'content' in data:
                testimonial.content = data['content']
            if 'member_since' in data:
                testimonial.member_since = data['member_since']
            if 'order' in data:
                testimonial.order = data['order']
            if 'is_active' in data:
                testimonial.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Testimonial updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(testimonial)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Testimonial deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with testimonial {testimonial_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@testimonials_api_bp.route('/bulk-delete/testimonials', methods=['POST'])
@login_required
@admin_required
def api_bulk_delete_testimonials():
    """Bulk delete testimonials"""
    try:
        data = request.get_json()
        testimonial_ids = data.get('testimonial_ids', [])
        
        if not testimonial_ids:
            return jsonify({'success': False, 'message': 'No testimonials selected'}), 400
        
        deleted_count = 0
        for testimonial_id in testimonial_ids:
            testimonial = Testimonial.query.get(testimonial_id)
            if testimonial:
                db.session.delete(testimonial)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} testimonials'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting testimonials: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
