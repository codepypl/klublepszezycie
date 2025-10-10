"""
Image utility functions for processing and resizing images
"""
import os
import logging
from PIL import Image
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def create_thumbnail(image_path, thumbnail_path, size=(300, 300), quality=85):
    """
    Create a thumbnail from an image file
    
    Args:
        image_path (str): Path to the original image
        thumbnail_path (str): Path where thumbnail should be saved
        size (tuple): Thumbnail size (width, height)
        quality (int): JPEG quality (1-100)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Open the original image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Ensure the thumbnail directory exists
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"✅ Created thumbnail: {thumbnail_path}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error creating thumbnail: {e}")
        return False

def generate_thumbnail_path(original_path, suffix='_thumb'):
    """
    Generate thumbnail path from original image path
    
    Args:
        original_path (str): Original image path
        suffix (str): Suffix to add before extension
    
    Returns:
        str: Thumbnail path
    """
    path_parts = os.path.splitext(original_path)
    return f"{path_parts[0]}{suffix}.jpg"

def create_gallery_thumbnails(post_id, image_filename, upload_folder):
    """
    Create thumbnails for gallery images
    
    Args:
        post_id (int): Blog post ID
        image_filename (str): Original image filename
        upload_folder (str): Base upload folder path
    
    Returns:
        dict: Result with thumbnail info
    """
    try:
        # Original image path
        original_path = os.path.join(upload_folder, 'blog', str(post_id), 'gallery', image_filename)
        
        if not os.path.exists(original_path):
            logger.error(f"❌ Original image not found: {original_path}")
            return {'success': False, 'error': 'Original image not found'}
        
        # Generate thumbnail path
        thumbnail_filename = generate_thumbnail_path(image_filename)
        thumbnail_path = os.path.join(upload_folder, 'blog', str(post_id), 'gallery', thumbnail_filename)
        
        # Create thumbnail
        success = create_thumbnail(original_path, thumbnail_path, size=(400, 300))
        
        if success:
            # Return thumbnail URL (relative to static folder)
            thumbnail_url = f'/static/uploads/blog/{post_id}/gallery/{thumbnail_filename}'
            original_url = f'/static/uploads/blog/{post_id}/gallery/{image_filename}'
            
            return {
                'success': True,
                'original_url': original_url,
                'thumbnail_url': thumbnail_url,
                'thumbnail_filename': thumbnail_filename
            }
        else:
            return {'success': False, 'error': 'Failed to create thumbnail'}
            
    except Exception as e:
        logger.error(f"❌ Error in create_gallery_thumbnails: {e}")
        return {'success': False, 'error': str(e)}

def create_featured_thumbnail(post_id, image_filename, upload_folder):
    """
    Create thumbnail for featured image
    
    Args:
        post_id (int): Blog post ID
        image_filename (str): Original image filename
        upload_folder (str): Base upload folder path
    
    Returns:
        dict: Result with thumbnail info
    """
    try:
        # Original image path
        original_path = os.path.join(upload_folder, 'blog', str(post_id), 'featured', image_filename)
        
        if not os.path.exists(original_path):
            logger.error(f"❌ Original featured image not found: {original_path}")
            return {'success': False, 'error': 'Original image not found'}
        
        # Generate thumbnail path
        thumbnail_filename = generate_thumbnail_path(image_filename)
        thumbnail_path = os.path.join(upload_folder, 'blog', str(post_id), 'featured', thumbnail_filename)
        
        # Create thumbnail (larger size for featured images)
        success = create_thumbnail(original_path, thumbnail_path, size=(800, 600))
        
        if success:
            # Return thumbnail URL (relative to static folder)
            thumbnail_url = f'/static/uploads/blog/{post_id}/featured/{thumbnail_filename}'
            original_url = f'/static/uploads/blog/{post_id}/featured/{image_filename}'
            
            return {
                'success': True,
                'original_url': original_url,
                'thumbnail_url': thumbnail_url,
                'thumbnail_filename': thumbnail_filename
            }
        else:
            return {'success': False, 'error': 'Failed to create thumbnail'}
            
    except Exception as e:
        logger.error(f"❌ Error in create_featured_thumbnail: {e}")
        return {'success': False, 'error': str(e)}




