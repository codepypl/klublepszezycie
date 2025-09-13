"""
SEO Management Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, SEOSettings
from datetime import datetime

seo_bp = Blueprint('seo', __name__)

@seo_bp.route('/seo')
@login_required
def index():
    """SEO management page"""
    seo_settings = SEOSettings.query.order_by(SEOSettings.page_type.asc()).all()
    return render_template('admin/seo.html', seo_settings=seo_settings)

@seo_bp.route('/seo/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new SEO settings"""
    if request.method == 'POST':
        try:
            # Check if page_type already exists
            existing = SEOSettings.query.filter_by(page_type=request.form.get('page_type')).first()
            if existing:
                flash('Ustawienia SEO dla tego typu strony już istnieją', 'error')
                return redirect(url_for('seo.create'))
            
            seo = SEOSettings(
                page_type=request.form.get('page_type'),
                page_title=request.form.get('page_title', ''),
                meta_description=request.form.get('meta_description', ''),
                meta_keywords=request.form.get('meta_keywords', ''),
                og_title=request.form.get('og_title', ''),
                og_description=request.form.get('og_description', ''),
                og_image=request.form.get('og_image', ''),
                og_type=request.form.get('og_type', 'website'),
                twitter_card=request.form.get('twitter_card', ''),
                twitter_title=request.form.get('twitter_title', ''),
                twitter_description=request.form.get('twitter_description', ''),
                twitter_image=request.form.get('twitter_image', ''),
                canonical_url=request.form.get('canonical_url', ''),
                structured_data=request.form.get('structured_data', ''),
                is_active=bool(request.form.get('is_active'))
            )
            
            db.session.add(seo)
            db.session.commit()
            
            flash('Ustawienia SEO zostały utworzone pomyślnie', 'success')
            return redirect(url_for('seo.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas tworzenia ustawień SEO: {str(e)}', 'error')
            return redirect(url_for('seo.create'))
    
    return render_template('admin/seo.html')

@seo_bp.route('/seo/<int:seo_id>')
@login_required
def edit_seo(seo_id):
    """Edit SEO settings - HTML form"""
    seo = SEOSettings.query.get_or_404(seo_id)
    return render_template('admin/seo.html', edit_seo=seo)


