"""
File utilities for handling file operations
"""
import os
import logging
from pathlib import Path
from flask import current_app

def delete_file(file_path):
    """
    Delete a file from the filesystem
    
    Args:
        file_path (str): Path to the file to delete (relative to uploads folder)
    
    Returns:
        bool: True if file was deleted successfully, False otherwise
    """
    try:
        # Get the full path to the uploads folder
        uploads_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        full_path = os.path.join(uploads_folder, file_path)
        
        # Check if file exists
        if os.path.exists(full_path):
            os.remove(full_path)
            logging.info(f"File deleted successfully: {full_path}")
            return True
        else:
            logging.warning(f"File not found for deletion: {full_path}")
            return False
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {str(e)}")
        return False

def delete_file_if_exists(file_path):
    """
    Delete a file if it exists, without raising errors
    
    Args:
        file_path (str): Path to the file to delete (relative to uploads folder)
    
    Returns:
        bool: True if file was deleted or didn't exist, False if error occurred
    """
    try:
        if not file_path:
            return True
            
        # Get the full path to the uploads folder
        uploads_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
        full_path = os.path.join(uploads_folder, file_path)
        
        # Check if file exists and delete
        if os.path.exists(full_path):
            os.remove(full_path)
            logging.info(f"File deleted successfully: {full_path}")
        else:
            logging.info(f"File not found (already deleted or never existed): {full_path}")
        
        return True
    except Exception as e:
        logging.error(f"Error deleting file {file_path}: {str(e)}")
        return False

def extract_filename_from_url(url):
    """
    Extract filename from a URL path
    
    Args:
        url (str): URL path (e.g., '/static/uploads/filename.jpg')
    
    Returns:
        str: Filename or None if not found
    """
    try:
        if not url:
            return None
            
        # Remove leading slash and static/uploads prefix
        if url.startswith('/static/uploads/'):
            return url[16:]  # Remove '/static/uploads/'
        elif url.startswith('static/uploads/'):
            return url[15:]  # Remove 'static/uploads/'
        else:
            # Try to extract filename from path
            return os.path.basename(url)
    except Exception as e:
        logging.error(f"Error extracting filename from URL {url}: {str(e)}")
        return None

def cleanup_blog_post_files(post):
    """
    Clean up all files associated with a blog post
    
    Args:
        post: BlogPost instance
    
    Returns:
        dict: Summary of deleted files
    """
    deleted_files = {
        'featured_image': False,
        'gallery_images': []
    }
    
    try:
        # Delete featured image
        if post.featured_image:
            filename = extract_filename_from_url(post.featured_image)
            if filename:
                deleted_files['featured_image'] = delete_file_if_exists(filename)
        
        # Delete gallery images
        if hasattr(post, 'images') and post.images:
            for image in post.images:
                if image.image_url:
                    filename = extract_filename_from_url(image.image_url)
                    if filename:
                        success = delete_file_if_exists(filename)
                        deleted_files['gallery_images'].append({
                            'filename': filename,
                            'deleted': success
                        })
        
        logging.info(f"Blog post files cleanup completed for post {post.id}: {deleted_files}")
        return deleted_files
        
    except Exception as e:
        logging.error(f"Error cleaning up blog post files for post {post.id}: {str(e)}")
        return deleted_files
