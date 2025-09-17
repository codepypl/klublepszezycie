"""
SEO routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.seo_controller import SEOController

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/seo')
@login_required
def index():
    """SEO management page"""
    data = SEOController.get_seo_settings()
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/seo.html', seo_settings=data['settings'])

@seo_bp.route('/seo/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new SEO settings"""
    if request.method == 'POST':
        page_type = request.form.get('page_type', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        keywords = request.form.get('keywords', '').strip()
        og_title = request.form.get('og_title', '').strip()
        og_description = request.form.get('og_description', '').strip()
        og_image = request.form.get('og_image', '').strip()
        
        result = SEOController.create_seo_setting(
            page_type, title, description, keywords, og_title, og_description, og_image
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('seo.index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('admin/seo_create.html')

@seo_bp.route('/seo/edit/<int:setting_id>', methods=['GET', 'POST'])
@login_required
def edit(setting_id):
    """Edit SEO settings"""
    data = SEOController.get_seo_setting(setting_id)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('seo.index'))
    
    setting = data['setting']
    
    if request.method == 'POST':
        page_type = request.form.get('page_type', '').strip()
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        keywords = request.form.get('keywords', '').strip()
        og_title = request.form.get('og_title', '').strip()
        og_description = request.form.get('og_description', '').strip()
        og_image = request.form.get('og_image', '').strip()
        
        result = SEOController.update_seo_setting(
            setting_id, page_type, title, description, keywords, og_title, og_description, og_image
        )
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('seo.index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('admin/seo_edit.html', setting=setting)

@seo_bp.route('/seo/delete/<int:setting_id>', methods=['POST'])
@login_required
def delete(setting_id):
    """Delete SEO settings"""
    result = SEOController.delete_seo_setting(setting_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('seo.index'))