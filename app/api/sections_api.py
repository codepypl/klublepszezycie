"""
Sections API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import Section, db
from app.utils.auth import admin_required
import logging
import json

sections_api_bp = Blueprint('sections_api', __name__)

@sections_api_bp.route('/sections', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_sections():
    """Sections API"""
    if request.method == 'GET':
        try:
            sections = Section.query.order_by(Section.order.asc()).all()
            return jsonify({
                'success': True,
                'sections': [{
                    'id': section.id,
                    'name': section.name,
                    'title': section.title,
                    'subtitle': section.subtitle,
                    'content': section.content,
                    'background_image': section.background_image,
                    'order': section.order,
                    'is_active': section.is_active,
                    'enable_pillars': section.enable_pillars,
                    'enable_floating_cards': section.enable_floating_cards,
                    'pillars_count': section.pillars_count,
                    'floating_cards_count': section.floating_cards_count,
                    'pillars_data': section.pillars_data,
                    'floating_cards_data': section.floating_cards_data,
                    'final_text': section.final_text,
                    'created_at': section.created_at.isoformat() if section.created_at else None
                } for section in sections]
            })
        except Exception as e:
            logging.error(f"Error getting sections: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            section = Section(
                name=data['name'],
                title=data.get('title', ''),
                subtitle=data.get('subtitle', ''),
                content=data.get('content', ''),
                background_image=data.get('background_image', ''),
                order=data.get('order', 0),
                is_active=data.get('is_active', True),
                enable_pillars=data.get('enable_pillars', False),
                enable_floating_cards=data.get('enable_floating_cards', False),
                pillars_count=data.get('pillars_count', 4),
                floating_cards_count=data.get('floating_cards_count', 3),
                pillars_data=data.get('pillars_data', ''),
                floating_cards_data=data.get('floating_cards_data', ''),
                final_text=data.get('final_text', '')
            )
            
            db.session.add(section)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section created successfully',
                'section': {
                    'id': section.id,
                    'name': section.name,
                    'title': section.title,
                    'subtitle': section.subtitle,
                    'content': section.content,
                    'background_image': section.background_image,
                    'order': section.order,
                    'is_active': section.is_active,
                    'enable_pillars': section.enable_pillars,
                    'enable_floating_cards': section.enable_floating_cards,
                    'pillars_count': section.pillars_count,
                    'floating_cards_count': section.floating_cards_count,
                    'pillars_data': section.pillars_data,
                    'floating_cards_data': section.floating_cards_data,
                    'final_text': section.final_text
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating section: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            section_ids = data.get('section_ids', [])
            
            if not section_ids:
                return jsonify({'success': False, 'message': 'No sections selected'}), 400
            
            deleted_count = 0
            for section_id in section_ids:
                section = Section.query.get(section_id)
                if section:
                    db.session.delete(section)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} sections'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting sections: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@sections_api_bp.route('/sections/<int:section_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_section(section_id):
    """Individual section API"""
    section = Section.query.get_or_404(section_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'section': {
                    'id': section.id,
                    'name': section.name,
                    'title': section.title,
                    'subtitle': section.subtitle,
                    'content': section.content,
                    'background_image': section.background_image,
                    'order': section.order,
                    'is_active': section.is_active,
                    'enable_pillars': section.enable_pillars,
                    'enable_floating_cards': section.enable_floating_cards,
                    'pillars_count': section.pillars_count,
                    'floating_cards_count': section.floating_cards_count,
                    'pillars_data': section.pillars_data,
                    'floating_cards_data': section.floating_cards_data,
                    'final_text': section.final_text,
                    'created_at': section.created_at.isoformat() if section.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'name' in data:
                section.name = data['name']
            if 'title' in data:
                section.title = data['title']
            if 'subtitle' in data:
                section.subtitle = data['subtitle']
            if 'content' in data:
                section.content = data['content']
            if 'background_image' in data:
                section.background_image = data['background_image']
            if 'order' in data:
                section.order = data['order']
            if 'is_active' in data:
                section.is_active = data['is_active']
            if 'enable_pillars' in data:
                section.enable_pillars = data['enable_pillars']
            if 'enable_floating_cards' in data:
                section.enable_floating_cards = data['enable_floating_cards']
            if 'pillars_count' in data:
                section.pillars_count = data['pillars_count']
            if 'floating_cards_count' in data:
                section.floating_cards_count = data['floating_cards_count']
            if 'pillars_data' in data:
                section.pillars_data = data['pillars_data']
            if 'floating_cards_data' in data:
                section.floating_cards_data = data['floating_cards_data']
            if 'final_text' in data:
                section.final_text = data['final_text']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(section)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with section {section_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sections_api_bp.route('/sections/<int:section_id>/pillars', methods=['PUT'])
@login_required
def api_section_pillars(section_id):
    """Update section pillars"""
    section = Section.query.get_or_404(section_id)
    
    try:
        data = request.get_json()
        pillars = data.get('pillars', [])
        
        # Update pillars data (assuming it's stored as JSON in content field)
        section.content = json.dumps({'pillars': pillars})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Section pillars updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating section pillars: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sections_api_bp.route('/sections/<int:section_id>/floating-cards', methods=['PUT'])
@login_required
def api_section_floating_cards(section_id):
    """Update section floating cards"""
    section = Section.query.get_or_404(section_id)
    
    try:
        data = request.get_json()
        floating_cards = data.get('floating_cards', [])
        
        # Update floating cards data (assuming it's stored as JSON in content field)
        section.content = json.dumps({'floating_cards': floating_cards})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Section floating cards updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating section floating cards: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@sections_api_bp.route('/bulk-delete/sections', methods=['POST'])
@login_required
@admin_required
def api_bulk_delete_sections():
    """Bulk delete sections"""
    try:
        data = request.get_json()
        section_ids = data.get('section_ids', [])
        
        if not section_ids:
            return jsonify({'success': False, 'message': 'No sections selected'}), 400
        
        deleted_count = 0
        for section_id in section_ids:
            section = Section.query.get(section_id)
            if section:
                db.session.delete(section)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} sections'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting sections: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
