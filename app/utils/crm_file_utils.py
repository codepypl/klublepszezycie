"""
File utilities for CRM import management
"""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename


def create_import_directory_structure(base_upload_folder):
    """
    Create directory structure for CRM imports: uploads/crm/imports/YYYY/MM/DD/
    Returns the path to today's directory
    """
    today = datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    day = today.strftime('%d')
    
    # Create path: uploads/crm/imports/YYYY/MM/DD/
    import_dir = os.path.join(base_upload_folder, 'crm', 'imports', year, month, day)
    
    # Create directory if it doesn't exist
    os.makedirs(import_dir, exist_ok=True)
    
    return import_dir


def generate_import_file_path(original_filename, base_upload_folder, import_id=None):
    """
    Generate a unique file path for import file
    Structure: uploads/crm/imports/YYYY/MM/DD/import_id_original_filename
    """
    # Create directory structure
    import_dir = create_import_directory_structure(base_upload_folder)
    
    # Generate unique filename
    if import_id is None:
        import_id = str(uuid.uuid4())
    
    # Secure the original filename
    secure_name = secure_filename(original_filename)
    
    # Create unique filename: import_id_original_filename
    unique_filename = f"{import_id}_{secure_name}"
    
    # Full path
    file_path = os.path.join(import_dir, unique_filename)
    
    return file_path


def delete_import_file(file_path):
    """
    Safely delete import file from disk
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False
    
    return False


def get_relative_path_from_upload_folder(full_path, upload_folder):
    """
    Get relative path from upload folder
    """
    if full_path.startswith(upload_folder):
        return full_path[len(upload_folder):].lstrip(os.sep)
    return full_path
