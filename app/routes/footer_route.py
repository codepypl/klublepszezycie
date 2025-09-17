"""
Footer routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.footer_controller import FooterController

footer_bp = Blueprint('footer', __name__)

@footer_bp.route('/footer')
@login_required
def index():
    """Footer management page"""
    # Get footer settings
    settings_data = FooterController.get_footer_settings()
    
    if not settings_data['success']:
        flash(f'Błąd: {settings_data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Get legal documents
    legal_data = FooterController.get_legal_documents()
    
    if not legal_data['success']:
        flash(f'Błąd: {legal_data["error"]}', 'error')
    
    return render_template('admin/footer.html', 
                         footer_settings=settings_data['footer_settings'],
                         privacy_policy=legal_data['privacy_policy'],
                         terms=legal_data['terms'])

@footer_bp.route('/footer/update', methods=['POST'])
@login_required
def update_footer():
    """Update footer settings"""
    company_title = request.form.get('company_title', '')
    company_description = request.form.get('company_description', '')
    contact_title = request.form.get('contact_title', '')
    contact_email = request.form.get('contact_email', '')
    contact_phone = request.form.get('contact_phone', '')
    social_title = request.form.get('social_title', '')
    company_name = request.form.get('company_name', '')
    show_privacy_policy = 'show_privacy_policy' in request.form
    show_terms = 'show_terms' in request.form
    
    result = FooterController.update_footer_settings(
        company_title, company_description, contact_title, 
        contact_email, contact_phone, social_title, 
        company_name, show_privacy_policy, show_terms
    )
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f'Błąd: {result["error"]}', 'error')
    
    return redirect(url_for('footer.index'))

@footer_bp.route('/footer/legal/<document_type>')
@login_required
def edit_legal(document_type):
    """Edit legal document page"""
    if document_type not in ['privacy_policy', 'terms']:
        flash('Nieprawidłowy typ dokumentu', 'error')
        return redirect(url_for('footer.index'))
    
    data = FooterController.get_legal_document(document_type)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('footer.index'))
    
    return render_template('admin/legal_edit.html', document=data['document'])

@footer_bp.route('/footer/legal/<document_type>/update', methods=['POST'])
@login_required
def update_legal(document_type):
    """Update legal document"""
    if document_type not in ['privacy_policy', 'terms']:
        flash('Nieprawidłowy typ dokumentu', 'error')
        return redirect(url_for('footer.index'))
    
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    
    result = FooterController.update_legal_document(document_type, title, content)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f'Błąd: {result["error"]}', 'error')
    
    return redirect(url_for('footer.edit_legal', document_type=document_type))

# Public routes moved to public.py blueprint
