"""
Import service for CRM system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from datetime import datetime
from models import db
from crm.models import Contact, ImportLog
from crm.config import CSV_COLUMNS, DEFAULT_MAX_CALL_ATTEMPTS

class ImportService:
    """Service for importing contacts from XLSX files"""
    
    @staticmethod
    def import_xlsx_file(file_path, ankieter_id, filename):
        """Import contacts from XLSX file"""
        try:
            # Read XLSX file
            df = pd.read_excel(file_path)
            
            # Create import log
            import_log = ImportLog(
                filename=filename,
                file_size=os.path.getsize(file_path),
                imported_by=ankieter_id,
                import_status='processing'
            )
            db.session.add(import_log)
            db.session.commit()
            
            # Map columns
            column_mapping = ImportService._map_columns(df.columns)
            
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Extract contact data
                    contact_data = ImportService._extract_contact_data(row, column_mapping)
                    
                    if not contact_data.get('name') or not contact_data.get('phone'):
                        skipped_count += 1
                        continue
                    
                    # Check if contact already exists
                    existing_contact = Contact.query.filter_by(
                        phone=contact_data['phone']
                    ).first()
                    
                    if existing_contact:
                        skipped_count += 1
                        continue
                    
                    # Create contact
                    contact = Contact(
                        name=contact_data['name'],
                        phone=contact_data['phone'],
                        email=contact_data.get('email'),
                        company=contact_data.get('company'),
                        notes=contact_data.get('notes'),
                        source_file=filename,
                        assigned_ankieter_id=ankieter_id,
                        max_call_attempts=DEFAULT_MAX_CALL_ATTEMPTS
                    )
                    
                    # Add tags if provided
                    if contact_data.get('tags'):
                        contact.set_tags(contact_data['tags'])
                    
                    db.session.add(contact)
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    skipped_count += 1
                    continue
            
            # Update import log
            import_log.rows_imported = imported_count
            import_log.rows_skipped = skipped_count
            import_log.import_status = 'completed'
            
            db.session.commit()
            
            return {
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count,
                'import_log_id': import_log.id
            }
            
        except Exception as e:
            # Update import log with error
            if 'import_log' in locals():
                import_log.import_status = 'failed'
                import_log.error_message = str(e)
                db.session.commit()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _map_columns(columns):
        """Map file columns to contact fields"""
        mapping = {}
        
        for field, possible_names in CSV_COLUMNS.items():
            for col in columns:
                col_lower = col.lower().strip()
                for possible_name in possible_names:
                    if possible_name.lower() in col_lower:
                        mapping[field] = col
                        break
                if field in mapping:
                    break
        
        return mapping
    
    @staticmethod
    def _extract_contact_data(row, column_mapping):
        """Extract contact data from row"""
        data = {}
        
        # Required fields
        if 'name' in column_mapping:
            data['name'] = str(row[column_mapping['name']]).strip()
        
        if 'phone' in column_mapping:
            phone = str(row[column_mapping['phone']]).strip()
            # Clean phone number
            phone = ImportService._clean_phone_number(phone)
            data['phone'] = phone
        
        # Optional fields
        if 'email' in column_mapping:
            email = str(row[column_mapping['email']]).strip()
            if email and email != 'nan':
                data['email'] = email
        
        if 'company' in column_mapping:
            company = str(row[column_mapping['company']]).strip()
            if company and company != 'nan':
                data['company'] = company
        
        if 'notes' in column_mapping:
            notes = str(row[column_mapping['notes']]).strip()
            if notes and notes != 'nan':
                data['notes'] = notes
        
        return data
    
    @staticmethod
    def _clean_phone_number(phone):
        """Clean and format phone number"""
        # Remove all non-digit characters except +
        import re
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Add +48 if no country code
        if not cleaned.startswith('+'):
            if cleaned.startswith('48'):
                cleaned = '+' + cleaned
            elif cleaned.startswith('0'):
                cleaned = '+48' + cleaned[1:]
            else:
                cleaned = '+48' + cleaned
        
        return cleaned
    
    @staticmethod
    def get_import_history(ankieter_id=None):
        """Get import history"""
        query = ImportLog.query
        
        if ankieter_id:
            query = query.filter_by(imported_by=ankieter_id)
        
        imports = query.order_by(ImportLog.created_at.desc()).all()
        
        return imports
    
    @staticmethod
    def validate_xlsx_file(file_path):
        """Validate XLSX file before import"""
        try:
            # Try to read the file
            df = pd.read_excel(file_path)
            
            # Check if file has data
            if df.empty:
                return False, "Plik jest pusty"
            
            # Check for required columns (name and phone)
            columns = [col.lower().strip() for col in df.columns]
            
            has_name = any('imię' in col or 'nazwisko' in col or 'name' in col for col in columns)
            has_phone = any('telefon' in col or 'phone' in col or 'numer' in col for col in columns)
            
            if not has_name:
                return False, "Brak kolumny z imieniem/nazwiskiem"
            
            if not has_phone:
                return False, "Brak kolumny z numerem telefonu"
            
            return True, "Plik jest poprawny"
            
        except Exception as e:
            return False, f"Błąd odczytu pliku: {str(e)}"
