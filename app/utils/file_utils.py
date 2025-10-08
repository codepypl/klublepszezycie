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
        url (str): URL path (e.g., '/static/uploads/blog/article/123/featured/filename.jpg')
    
    Returns:
        str: Filename or None if not found
    """
    try:
        if not url:
            return None
            
        # Remove leading slash and extract filename
        if url.startswith('/static/uploads/blog/article/'):
            return url.split('/')[-1]  # Get filename from end of path
        elif url.startswith('static/uploads/blog/article/'):
            return url.split('/')[-1]  # Get filename from end of path
        elif url.startswith('/static/uploads/blog/'):
            return url[22:]  # Remove '/static/uploads/blog/'
        elif url.startswith('static/uploads/blog/'):
            return url[21:]  # Remove 'static/uploads/blog/'
        elif url.startswith('/static/images/blog/'):
            return url[20:]  # Remove '/static/images/blog/' (legacy)
        elif url.startswith('static/images/blog/'):
            return url[19:]  # Remove 'static/images/blog/' (legacy)
        elif url.startswith('/static/uploads/'):
            return url[16:]  # Remove '/static/uploads/' (legacy)
        elif url.startswith('static/uploads/'):
            return url[15:]  # Remove 'static/uploads/' (legacy)
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
            if post.featured_image.startswith('/static/uploads/blog/') and '/featured/' in post.featured_image:
                # New structure: /static/uploads/blog/<id>/featured/filename
                url_path = post.featured_image.replace('/static/uploads/', '')
                featured_path = os.path.join(current_app.config['UPLOAD_FOLDER'], url_path)
                if os.path.exists(featured_path):
                    os.remove(featured_path)
                    deleted_files['featured_image'] = True
                    logging.info(f"Deleted featured image: {featured_path}")
            elif post.featured_image.startswith('/static/uploads/blog/article/'):
                # Old structure: /static/uploads/blog/article/<id>/featured/filename
                filename = post.featured_image.split('/')[-1]  # Get filename
                featured_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id), 'featured', filename)
                if os.path.exists(featured_path):
                    os.remove(featured_path)
                    deleted_files['featured_image'] = True
                    logging.info(f"Deleted featured image: {featured_path}")
            else:
                # Legacy structure: /static/uploads/filename or /static/images/blog/featured/filename
                filename = extract_filename_from_url(post.featured_image)
                if filename:
                    deleted_files['featured_image'] = delete_file_if_exists(filename)
        
        # Delete gallery images
        if hasattr(post, 'images') and post.images:
            for image in post.images:
                if image.image_url:
                    if image.image_url.startswith('/static/uploads/blog/') and '/gallery/' in image.image_url:
                        # New structure: /static/uploads/blog/<id>/gallery/filename
                        url_path = image.image_url.replace('/static/uploads/', '')
                        gallery_path = os.path.join(current_app.config['UPLOAD_FOLDER'], url_path)
                        if os.path.exists(gallery_path):
                            os.remove(gallery_path)
                            deleted_files['gallery_images'].append({
                                'filename': os.path.basename(gallery_path),
                                'deleted': True
                            })
                            logging.info(f"Deleted gallery image: {gallery_path}")
                    elif image.image_url.startswith(f'/static/uploads/blog/article/{post.id}/gallery/'):
                        # Old structure: /static/uploads/blog/article/<id>/gallery/filename
                        filename = image.image_url.split('/')[-1]  # Get filename
                        gallery_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id), 'gallery', filename)
                        if os.path.exists(gallery_path):
                            os.remove(gallery_path)
                            deleted_files['gallery_images'].append({
                                'filename': filename,
                                'deleted': True
                            })
                            logging.info(f"Deleted gallery image: {gallery_path}")
                    else:
                        # Legacy structure: /static/uploads/filename or /static/images/blog/article/<id>/gallery/filename
                        filename = extract_filename_from_url(image.image_url)
                        if filename:
                            success = delete_file_if_exists(filename)
                            deleted_files['gallery_images'].append({
                                'filename': filename,
                                'deleted': success
                            })
        
        # Clean up empty directories
        try:
            # Remove new structure directories if empty
            gallery_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post.id), 'gallery')
            if os.path.exists(gallery_dir) and not os.listdir(gallery_dir):
                os.rmdir(gallery_dir)
                logging.info(f"Removed empty gallery directory: {gallery_dir}")
            
            featured_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post.id), 'featured')
            if os.path.exists(featured_dir) and not os.listdir(featured_dir):
                os.rmdir(featured_dir)
                logging.info(f"Removed empty featured directory: {featured_dir}")
            
            post_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post.id))
            if os.path.exists(post_dir) and not os.listdir(post_dir):
                os.rmdir(post_dir)
                logging.info(f"Removed empty post directory: {post_dir}")
            
            # Remove old structure directories if empty
            old_gallery_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id), 'gallery')
            if os.path.exists(old_gallery_dir) and not os.listdir(old_gallery_dir):
                os.rmdir(old_gallery_dir)
                logging.info(f"Removed empty old gallery directory: {old_gallery_dir}")
            
            old_featured_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id), 'featured')
            if os.path.exists(old_featured_dir) and not os.listdir(old_featured_dir):
                os.rmdir(old_featured_dir)
                logging.info(f"Removed empty old featured directory: {old_featured_dir}")
            
            old_article_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id))
            if os.path.exists(old_article_dir) and not os.listdir(old_article_dir):
                os.rmdir(old_article_dir)
                logging.info(f"Removed empty old article directory: {old_article_dir}")
        except Exception as e:
            logging.warning(f"Could not remove empty directories: {str(e)}")
        
        logging.info(f"Blog post files cleanup completed for post {post.id}: {deleted_files}")
        return deleted_files
        
    except Exception as e:
        logging.error(f"Error cleaning up blog post files for post {post.id}: {str(e)}")
        return deleted_files
