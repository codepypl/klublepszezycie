"""
File import service for extracting and processing XLSX files line by line
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import json
from datetime import datetime
from app.models import db
from app.models.crm_model import ImportFile, ImportRecord, Contact
from app.config.crm_config import DEFAULT_MAX_CALL_ATTEMPTS

class FileImportService:
    """Service for importing and processing XLSX files line by line"""
    
    @staticmethod
    def extract_file_to_database(file_path, filename, file_type, ankieter_id, csv_separator=','):
        """
        Extract XLSX file line by line and store in database
        Returns ImportFile object with all raw records
        """
        try:
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Create ImportFile record
            import_file = ImportFile(
                filename=filename,
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                file_type=file_type.lower(),
                csv_separator=csv_separator,
                imported_by=ankieter_id,
                import_status='processing',
                total_rows=len(df)
            )
            db.session.add(import_file)
            db.session.flush()  # Get the ID
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        # Handle NaN values
                        if pd.isna(value):
                            row_data[col] = None
                        else:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            # Handle special values
                            if str_value in ['nan', 'None', '']:
                                row_data[col] = None
                            else:
                                row_data[col] = str_value
                    
                    # Validate row_data before JSON serialization
                    try:
                        json_data = json.dumps(row_data, ensure_ascii=False)
                    except (TypeError, ValueError) as json_error:
                        print(f"JSON serialization error for row {index + 1}: {json_error}")
                        print(f"Problematic row_data: {row_data}")
                        continue
                    
                    # Create ImportRecord
                    import_record = ImportRecord(
                        import_file_id=import_file.id,
                        row_number=index + 1,  # 1-based row numbering
                        processed=False
                    )
                    import_record.set_raw_data(row_data)
                    db.session.add(import_record)
                    
                except Exception as e:
                    print(f"Error processing row {index + 1}: {e}")
                    print(f"Row data: {row_data if 'row_data' in locals() else 'Not available'}")
                    continue
            
            # Update import file status
            import_file.import_status = 'completed'
            import_file.processed_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'import_file': import_file,
                'total_rows': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_import_records_from_file(import_file_id, file_path, file_type, csv_separator=','):
        """Create ImportRecord entries from file for existing ImportFile"""
        try:
            import_file = ImportFile.query.get(import_file_id)
            if not import_file:
                return {'success': False, 'error': 'Import file not found'}
            
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Create ImportRecord for each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        # Handle NaN values
                        if pd.isna(value):
                            row_data[col] = None
                        else:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            # Handle special values
                            if str_value in ['nan', 'None', '']:
                                row_data[col] = None
                            else:
                                row_data[col] = str_value
                    
                    # Create ImportRecord
                    import_record = ImportRecord(
                        import_file_id=import_file_id,
                        row_number=index + 1,
                        processed=False
                    )
                    import_record.set_raw_data(row_data)
                    db.session.add(import_record)
                    
                except Exception as e:
                    print(f"Error processing row {index + 1}: {e}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'total_records': len(df)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def analyze_file(file_path, file_type, csv_separator=','):
        """
        Analyze file and return column information and sample data
        """
        try:
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Get sample data (first 5 rows)
            sample_data = []
            for index, row in df.head(5).iterrows():
                row_data = {}
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        row_data[col] = None
                    else:
                        row_data[col] = str(value).strip()
                sample_data.append(row_data)
            
            return {
                'success': True,
                'columns': list(df.columns),
                'total_rows': len(df),
                'sample_data': sample_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_import_records_from_file(import_file_id, file_path, file_type, csv_separator=','):
        """Create ImportRecord entries from file for existing ImportFile"""
        try:
            import_file = ImportFile.query.get(import_file_id)
            if not import_file:
                return {'success': False, 'error': 'Import file not found'}
            
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Create ImportRecord for each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        # Handle NaN values
                        if pd.isna(value):
                            row_data[col] = None
                        else:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            # Handle special values
                            if str_value in ['nan', 'None', '']:
                                row_data[col] = None
                            else:
                                row_data[col] = str_value
                    
                    # Create ImportRecord
                    import_record = ImportRecord(
                        import_file_id=import_file_id,
                        row_number=index + 1,
                        processed=False
                    )
                    import_record.set_raw_data(row_data)
                    db.session.add(import_record)
                    
                except Exception as e:
                    print(f"Error processing row {index + 1}: {e}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'total_records': len(df)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def process_records_to_contacts(import_file_id, column_mapping, ankieter_id):
        """
        Process raw records into Contact objects based on column mapping
        """
        try:
            import_file = ImportFile.query.get(import_file_id)
            if not import_file:
                return {'success': False, 'error': 'Import file not found'}
            
            # Get unprocessed records
            records = ImportRecord.query.filter_by(
                import_file_id=import_file_id,
                processed=False
            ).all()
            
            processed_count = 0
            skipped_count = 0
            
            for record in records:
                try:
                    raw_data = record.get_raw_data()
                    
                    # Validate raw_data
                    if not raw_data or not isinstance(raw_data, dict):
                        record.error_message = 'Invalid raw data format'
                        record.processed = True
                        skipped_count += 1
                        continue
                    
                    # Extract data based on mapping
                    contact_data = FileImportService._extract_contact_data(raw_data, column_mapping)
                    
                    # Validate required fields - only phone is required
                    if not contact_data.get('phone'):
                        record.error_message = 'Missing required field (phone)'
                        record.processed = True
                        skipped_count += 1
                        continue
                    
                    # Check if contact already exists
                    existing_contact = Contact.query.filter_by(
                        phone=contact_data['phone']
                    ).first()
                    
                    if existing_contact:
                        record.contact_id = existing_contact.id
                        record.processed = True
                        record.error_message = 'Contact already exists'
                        skipped_count += 1
                        continue
                    
                    # Create contact
                    contact = Contact(
                        name=contact_data.get('name', 'Brak nazwy'),  # Default name if not provided
                        phone=contact_data['phone'],
                        email=contact_data.get('email'),
                        company=contact_data.get('company'),
                        notes=contact_data.get('notes'),
                        source_file=import_file.filename or f'import_{import_file.id}',  # Use filename or fallback
                        assigned_ankieter_id=ankieter_id,
                        max_call_attempts=DEFAULT_MAX_CALL_ATTEMPTS
                    )
                    
                    # Add tags if provided
                    if contact_data.get('tags'):
                        contact.set_tags(contact_data['tags'])
                    
                    db.session.add(contact)
                    db.session.flush()  # Get the ID
                    
                    # Link record to contact
                    record.contact_id = contact.id
                    record.processed = True
                    processed_count += 1
                    
                except Exception as e:
                    record.error_message = str(e)
                    record.processed = True
                    skipped_count += 1
                    continue
            
            # Update import file with final stats
            import_file.import_status = 'completed'
            import_file.processed_rows = processed_count  # This is the count of successfully imported contacts
            
            db.session.commit()
            
            return {
                'success': True,
                'imported': processed_count,
                'skipped': skipped_count,
                'import_file_id': import_file.id
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_import_records_from_file(import_file_id, file_path, file_type, csv_separator=','):
        """Create ImportRecord entries from file for existing ImportFile"""
        try:
            import_file = ImportFile.query.get(import_file_id)
            if not import_file:
                return {'success': False, 'error': 'Import file not found'}
            
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Create ImportRecord for each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        # Handle NaN values
                        if pd.isna(value):
                            row_data[col] = None
                        else:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            # Handle special values
                            if str_value in ['nan', 'None', '']:
                                row_data[col] = None
                            else:
                                row_data[col] = str_value
                    
                    # Create ImportRecord
                    import_record = ImportRecord(
                        import_file_id=import_file_id,
                        row_number=index + 1,
                        processed=False
                    )
                    import_record.set_raw_data(row_data)
                    db.session.add(import_record)
                    
                except Exception as e:
                    print(f"Error processing row {index + 1}: {e}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'total_records': len(df)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _extract_contact_data(raw_data, column_mapping):
        """Extract contact data from raw data based on column mapping"""
        data = {}
        
        try:
            # Required fields
            if 'name' in column_mapping and column_mapping['name'] and column_mapping['name'] in raw_data:
                name_value = raw_data[column_mapping['name']]
                if name_value is not None:
                    data['name'] = str(name_value).strip()
            
            if 'phone' in column_mapping and column_mapping['phone'] and column_mapping['phone'] in raw_data:
                phone_value = raw_data[column_mapping['phone']]
                if phone_value is not None:
                    phone = str(phone_value).strip()
                    data['phone'] = FileImportService._clean_phone_number(phone)
        except Exception as e:
            print(f"Error extracting contact data: {e}")
            print(f"Raw data: {raw_data}")
            print(f"Column mapping: {column_mapping}")
            return {}
        
        # Optional fields
        try:
            if 'email' in column_mapping and column_mapping['email'] and column_mapping['email'] in raw_data:
                email_value = raw_data[column_mapping['email']]
                if email_value is not None:
                    email = str(email_value).strip()
                    if email and email != 'None' and email != 'nan':
                        data['email'] = email
            
            if 'company' in column_mapping and column_mapping['company'] and column_mapping['company'] in raw_data:
                company_value = raw_data[column_mapping['company']]
                if company_value is not None:
                    company = str(company_value).strip()
                    if company and company != 'None' and company != 'nan':
                        data['company'] = company
            
            if 'notes' in column_mapping and column_mapping['notes'] and column_mapping['notes'] in raw_data:
                notes_value = raw_data[column_mapping['notes']]
                if notes_value is not None:
                    notes = str(notes_value).strip()
                    if notes and notes != 'None' and notes != 'nan':
                        data['notes'] = notes
            
            if 'tags' in column_mapping and column_mapping['tags'] and column_mapping['tags'] in raw_data:
                tags_value = raw_data[column_mapping['tags']]
                if tags_value is not None:
                    tags = str(tags_value).strip()
                    if tags and tags != 'None' and tags != 'nan':
                        # Split tags by comma and clean them
                        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        data['tags'] = tags_list
        except Exception as e:
            print(f"Error extracting optional fields: {e}")
            print(f"Raw data: {raw_data}")
            print(f"Column mapping: {column_mapping}")
        
        return data
    
    @staticmethod
    def _clean_phone_number(phone):
        """Clean and format phone number"""
        import re
        # Remove all non-digit characters except +
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
    def get_import_files(ankieter_id=None):
        """Get list of import files"""
        query = ImportFile.query
        
        if ankieter_id:
            query = query.filter_by(imported_by=ankieter_id)
        
        return query.order_by(ImportFile.created_at.desc()).all()
    
    @staticmethod
    def get_import_records(import_file_id, page=1, per_page=20):
        """Get import records for a specific file with pagination"""
        records = ImportRecord.query.filter_by(import_file_id=import_file_id)\
            .order_by(ImportRecord.row_number)\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return records
    
    @staticmethod
    def preview_mapping(file_path, file_type, csv_separator, mapping, rows_count=20):
        """Preview mapping results with sample data"""
        try:
            # Read file
            if file_type == 'xlsx':
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, sep=csv_separator, encoding='utf-8')
            
            # Apply mapping
            preview_data = []
            for index, row in df.head(rows_count).iterrows():
                mapped_row = {}
                for field, column in mapping.items():
                    if column and column in df.columns:
                        mapped_row[field] = str(row[column])
                    else:
                        mapped_row[field] = ''
                preview_data.append(mapped_row)
            
            return {
                'success': True,
                'preview_data': preview_data,
                'total_rows': len(df)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def create_import_records_from_file(import_file_id, file_path, file_type, csv_separator=','):
        """Create ImportRecord entries from file for existing ImportFile"""
        try:
            import_file = ImportFile.query.get(import_file_id)
            if not import_file:
                return {'success': False, 'error': 'Import file not found'}
            
            # Read file based on type
            if file_type.lower() == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8', sep=csv_separator)
            else:  # xlsx, xls
                df = pd.read_excel(file_path)
            
            # Create ImportRecord for each row
            for index, row in df.iterrows():
                try:
                    # Convert row to dictionary
                    row_data = {}
                    for col in df.columns:
                        value = row[col]
                        # Handle NaN values
                        if pd.isna(value):
                            row_data[col] = None
                        else:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            # Handle special values
                            if str_value in ['nan', 'None', '']:
                                row_data[col] = None
                            else:
                                row_data[col] = str_value
                    
                    # Create ImportRecord
                    import_record = ImportRecord(
                        import_file_id=import_file_id,
                        row_number=index + 1,
                        processed=False
                    )
                    import_record.set_raw_data(row_data)
                    db.session.add(import_record)
                    
                except Exception as e:
                    print(f"Error processing row {index + 1}: {e}")
                    continue
            
            db.session.commit()
            
            return {
                'success': True,
                'total_records': len(df)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

