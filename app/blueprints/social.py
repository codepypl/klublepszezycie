"""
Social Media Management Blueprint
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SocialLink
import re

social_bp = Blueprint('social', __name__)

@social_bp.route('/social')
@login_required
def index():
    """Social media management page"""
    social_links = SocialLink.query.order_by(SocialLink.order.asc()).all()
    return render_template('admin/social.html', social_links=social_links)

@social_bp.route('/social/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new social media link"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate URL format
            url = data.get('url', '').strip()
            if not url:
                return jsonify({'error': 'URL jest wymagany'}), 400
            
            # Basic URL validation
            if not re.match(r'^https?://', url):
                return jsonify({'error': 'URL musi zaczynać się od http:// lub https://'}), 400
            
            social_link = SocialLink(
                platform=data.get('platform', '').strip(),
                url=url,
                icon=data.get('icon', ''),
                target=data.get('target', '_blank'),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(social_link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został utworzony pomyślnie',
                'id': social_link.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    return render_template('admin/social.html')

@social_bp.route('/social/<int:link_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_link(link_id):
    """Get, update or delete specific social media link"""
    link = SocialLink.query.get_or_404(link_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': link.id,
            'platform': link.platform,
            'url': link.url,
            'icon': link.icon,
            'target': link.target,
            'order': link.order,
            'is_active': link.is_active,
            'created_at': link.created_at.isoformat() if link.created_at else None
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Validate URL format if provided
            url = data.get('url', link.url).strip()
            if url and not re.match(r'^https?://', url):
                return jsonify({'error': 'URL musi zaczynać się od http:// lub https://'}), 400
            
            # Update fields
            link.platform = data.get('platform', link.platform)
            link.url = url if url else link.url
            link.icon = data.get('icon', link.icon)
            link.target = data.get('target', link.target)
            link.order = data.get('order', link.order)
            link.is_active = data.get('is_active', link.is_active)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został zaktualizowany pomyślnie'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został usunięty pomyślnie'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@social_bp.route('/social/public')
def get_public_links():
    """Get active social media links (public endpoint)"""
    try:
        links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
        
        return jsonify([{
            'id': link.id,
            'platform': link.platform,
            'url': link.url,
            'icon': link.icon,
            'target': link.target,
            'order': link.order
        } for link in links])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@social_bp.route('/social/platforms')
def get_platforms():
    """Get available social media platforms"""
    platforms = [
        {'value': 'Facebook', 'icon': 'facebook'},
        {'value': 'Instagram', 'icon': 'instagram'},
        {'value': 'Twitter', 'icon': 'twitter'},
        {'value': 'LinkedIn', 'icon': 'linkedin'},
        {'value': 'YouTube', 'icon': 'youtube'},
        {'value': 'TikTok', 'icon': 'tiktok'},
        {'value': 'WhatsApp', 'icon': 'whatsapp'},
        {'value': 'Telegram', 'icon': 'telegram'},
        {'value': 'Pinterest', 'icon': 'pinterest'},
        {'value': 'Snapchat', 'icon': 'snapchat'},
        {'value': 'Discord', 'icon': 'discord'},
        {'value': 'Twitch', 'icon': 'twitch'}
    ]
    
    return jsonify(platforms)
