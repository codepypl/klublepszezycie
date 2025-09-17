"""
Benefits API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import BenefitItem, db
from app.utils.auth import admin_required
import logging

benefits_api_bp = Blueprint('benefits_api', __name__)

@benefits_api_bp.route('/benefits', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_benefits():
    """Benefits API"""
    if request.method == 'GET':
        try:
            benefits = BenefitItem.query.order_by(BenefitItem.order.asc()).all()
            return jsonify({
                'success': True,
                'benefits': [{
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'order': benefit.order,
                    'is_active': benefit.is_active,
                    'created_at': benefit.created_at.isoformat() if benefit.created_at else None
                } for benefit in benefits]
            })
        except Exception as e:
            logging.error(f"Error getting benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            benefit = BenefitItem(
                title=data['title'],
                description=data.get('description', ''),
                icon=data.get('icon', ''),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(benefit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit created successfully',
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'order': benefit.order,
                    'is_active': benefit.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating benefit: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            benefit_ids = data.get('benefit_ids', [])
            
            if not benefit_ids:
                return jsonify({'success': False, 'message': 'No benefits selected'}), 400
            
            updated_count = 0
            for benefit_id in benefit_ids:
                benefit = BenefitItem.query.get(benefit_id)
                if benefit:
                    if 'title' in data:
                        benefit.title = data['title']
                    if 'description' in data:
                        benefit.description = data['description']
                    if 'icon' in data:
                        benefit.icon = data['icon']
                    if 'order' in data:
                        benefit.order = data['order']
                    if 'is_active' in data:
                        benefit.is_active = data['is_active']
                    updated_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated {updated_count} benefits'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk updating benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            benefit_ids = data.get('benefit_ids', [])
            
            if not benefit_ids:
                return jsonify({'success': False, 'message': 'No benefits selected'}), 400
            
            deleted_count = 0
            for benefit_id in benefit_ids:
                benefit = BenefitItem.query.get(benefit_id)
                if benefit:
                    db.session.delete(benefit)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} benefits'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@benefits_api_bp.route('/benefits/<int:benefit_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_benefit(benefit_id):
    """Individual benefit API"""
    benefit = BenefitItem.query.get_or_404(benefit_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'order': benefit.order,
                    'is_active': benefit.is_active,
                    'created_at': benefit.created_at.isoformat() if benefit.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'title' in data:
                benefit.title = data['title']
            if 'description' in data:
                benefit.description = data['description']
            if 'icon' in data:
                benefit.icon = data['icon']
            if 'order' in data:
                benefit.order = data['order']
            if 'is_active' in data:
                benefit.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(benefit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with benefit {benefit_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@benefits_api_bp.route('/bulk-delete/benefits', methods=['POST'])
@login_required
@admin_required
def api_bulk_delete_benefits():
    """Bulk delete benefits"""
    try:
        data = request.get_json()
        benefit_ids = data.get('benefit_ids', [])
        
        if not benefit_ids:
            return jsonify({'success': False, 'message': 'No benefits selected'}), 400
        
        deleted_count = 0
        for benefit_id in benefit_ids:
            benefit = BenefitItem.query.get(benefit_id)
            if benefit:
                db.session.delete(benefit)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} benefits'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting benefits: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
