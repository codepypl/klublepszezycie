from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, FooterSettings, LegalDocument, SocialLink
from datetime import datetime

footer_bp = Blueprint('footer', __name__)

@footer_bp.route('/footer')
@login_required
def index():
    """Footer management page"""
    # Get or create footer settings
    footer_settings = FooterSettings.query.first()
    if not footer_settings:
        footer_settings = FooterSettings()
        db.session.add(footer_settings)
        db.session.commit()
    
    # Get legal documents
    privacy_policy = LegalDocument.query.filter_by(document_type='privacy_policy', is_active=True).first()
    terms = LegalDocument.query.filter_by(document_type='terms', is_active=True).first()
    
    return render_template('admin/footer.html', 
                         footer_settings=footer_settings,
                         privacy_policy=privacy_policy,
                         terms=terms)

@footer_bp.route('/footer/update', methods=['POST'])
@login_required
def update_footer():
    """Update footer settings"""
    try:
        footer_settings = FooterSettings.query.first()
        if not footer_settings:
            footer_settings = FooterSettings()
            db.session.add(footer_settings)
        
        # Update footer settings
        footer_settings.company_title = request.form.get('company_title', footer_settings.company_title)
        footer_settings.company_description = request.form.get('company_description', footer_settings.company_description)
        footer_settings.contact_title = request.form.get('contact_title', footer_settings.contact_title)
        footer_settings.contact_email = request.form.get('contact_email', footer_settings.contact_email)
        footer_settings.contact_phone = request.form.get('contact_phone', footer_settings.contact_phone)
        footer_settings.social_title = request.form.get('social_title', footer_settings.social_title)
        footer_settings.company_name = request.form.get('company_name', footer_settings.company_name)
        footer_settings.show_privacy_policy = 'show_privacy_policy' in request.form
        footer_settings.show_terms = 'show_terms' in request.form
        footer_settings.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Ustawienia stopki zostały zaktualizowane pomyślnie!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas aktualizacji ustawień stopki: {str(e)}', 'error')
    
    return redirect(url_for('footer.index'))

@footer_bp.route('/footer/legal/<document_type>')
@login_required
def edit_legal(document_type):
    """Edit legal document page"""
    if document_type not in ['privacy_policy', 'terms']:
        flash('Nieprawidłowy typ dokumentu', 'error')
        return redirect(url_for('footer.index'))
    
    document = LegalDocument.query.filter_by(document_type=document_type, is_active=True).first()
    if not document:
        # Create new document
        document = LegalDocument(
            document_type=document_type,
            title='Polityka prywatności' if document_type == 'privacy_policy' else 'Regulamin',
            content='' if document_type == 'privacy_policy' else ''
        )
        db.session.add(document)
        db.session.commit()
    
    return render_template('admin/legal_edit.html', document=document)

@footer_bp.route('/footer/legal/<document_type>/update', methods=['POST'])
@login_required
def update_legal(document_type):
    """Update legal document"""
    if document_type not in ['privacy_policy', 'terms']:
        flash('Nieprawidłowy typ dokumentu', 'error')
        return redirect(url_for('footer.index'))
    
    try:
        document = LegalDocument.query.filter_by(document_type=document_type, is_active=True).first()
        if not document:
            document = LegalDocument(document_type=document_type)
            db.session.add(document)
        
        document.title = request.form.get('title', document.title)
        document.content = request.form.get('content', document.content)
        document.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'{document.title} został zaktualizowany pomyślnie!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd podczas aktualizacji dokumentu: {str(e)}', 'error')
    
    return redirect(url_for('footer.edit_legal', document_type=document_type))

# Public routes moved to public.py blueprint
