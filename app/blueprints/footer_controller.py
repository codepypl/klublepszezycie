"""
Footer business logic controller
"""
from flask import request
from flask_login import login_required, current_user
from app.models import db, FooterSettings, LegalDocument, SocialLink
from datetime import datetime

class FooterController:
    """Footer business logic controller"""
    
    @staticmethod
    def get_footer_settings():
        """Get footer settings"""
        try:
            footer_settings = FooterSettings.query.first()
            if not footer_settings:
                footer_settings = FooterSettings()
                db.session.add(footer_settings)
                db.session.commit()
            
            return {
                'success': True,
                'footer_settings': footer_settings
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'footer_settings': None
            }
    
    @staticmethod
    def get_legal_documents():
        """Get legal documents"""
        try:
            privacy_policy = LegalDocument.query.filter_by(
                document_type='privacy_policy', is_active=True
            ).first()
            terms = LegalDocument.query.filter_by(
                document_type='terms', is_active=True
            ).first()
            
            return {
                'success': True,
                'privacy_policy': privacy_policy,
                'terms': terms
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'privacy_policy': None,
                'terms': None
            }
    
    @staticmethod
    def update_footer_settings(company_title, company_description, contact_title, 
                              contact_email, contact_phone, social_title, 
                              company_name, show_privacy_policy, show_terms):
        """Update footer settings"""
        try:
            footer_settings = FooterSettings.query.first()
            if not footer_settings:
                footer_settings = FooterSettings()
                db.session.add(footer_settings)
            
            footer_settings.company_title = company_title
            footer_settings.company_description = company_description
            footer_settings.contact_title = contact_title
            footer_settings.contact_email = contact_email
            footer_settings.contact_phone = contact_phone
            footer_settings.social_title = social_title
            footer_settings.company_name = company_name
            footer_settings.show_privacy_policy = show_privacy_policy
            footer_settings.show_terms = show_terms
            footer_settings.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'footer_settings': footer_settings,
                'message': 'Ustawienia stopki zostały zaktualizowane pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_legal_document(document_type):
        """Get legal document by type"""
        try:
            if document_type not in ['privacy_policy', 'terms']:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy typ dokumentu',
                    'document': None
                }
            
            document = LegalDocument.query.filter_by(
                document_type=document_type, is_active=True
            ).first()
            
            if not document:
                # Create new document
                title = 'Polityka prywatności' if document_type == 'privacy_policy' else 'Regulamin'
                document = LegalDocument(
                    document_type=document_type,
                    title=title,
                    content=''
                )
                db.session.add(document)
                db.session.commit()
            
            return {
                'success': True,
                'document': document
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'document': None
            }
    
    @staticmethod
    def update_legal_document(document_type, title, content):
        """Update legal document"""
        try:
            if document_type not in ['privacy_policy', 'terms']:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy typ dokumentu'
                }
            
            document = LegalDocument.query.filter_by(
                document_type=document_type, is_active=True
            ).first()
            
            if not document:
                document = LegalDocument(document_type=document_type)
                db.session.add(document)
            
            document.title = title
            document.content = content
            document.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'document': document,
                'message': f'{document.title} został zaktualizowany pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_public_footer_data():
        """Get public footer data"""
        try:
            # Get footer settings
            footer_settings = FooterSettings.query.first()
            if not footer_settings:
                footer_settings = FooterSettings()
                db.session.add(footer_settings)
                db.session.commit()
            
            # Get social links
            social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
            
            # Get legal documents if enabled
            privacy_policy = None
            terms = None
            
            if footer_settings.show_privacy_policy:
                privacy_policy = LegalDocument.query.filter_by(
                    document_type='privacy_policy', is_active=True
                ).first()
            
            if footer_settings.show_terms:
                terms = LegalDocument.query.filter_by(
                    document_type='terms', is_active=True
                ).first()
            
            return {
                'success': True,
                'footer_settings': footer_settings,
                'social_links': social_links,
                'privacy_policy': privacy_policy,
                'terms': terms
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'footer_settings': None,
                'social_links': [],
                'privacy_policy': None,
                'terms': None
            }
