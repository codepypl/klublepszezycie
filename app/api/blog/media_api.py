"""
Blog Media API - image and media management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import BlogPost, BlogPostImage, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
import os
import time
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Create Media API blueprint
media_api_bp = Blueprint('blog_media_api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@media_api_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    """Upload image for blog posts"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Brak pliku obrazu'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nie wybrano pliku obrazu'
            }), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            filename = f"{int(time.time())}_{filename}"
            
            # Create blog-specific upload folder structure
            blog_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
            os.makedirs(blog_upload_folder, exist_ok=True)
            
            file_path = os.path.join(blog_upload_folder, filename)
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'message': 'Obraz został przesłany pomyślnie',
                'filename': filename,
                'url': f'/static/uploads/blog/{filename}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nieprawidłowy typ pliku'
            }), 400
    
    except Exception as e:
        logger.error(f"❌ Błąd przesyłania obrazu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/admin/posts/<int:post_id>/images', methods=['GET'])
@login_required
@admin_required_api
def get_post_images(post_id):
    """Get images for a blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        images = BlogPostImage.query.filter_by(post_id=post_id).order_by(BlogPostImage.created_at.desc()).all()
        
        logger.info(f"🔍 Found {len(images)} images for post {post_id}")
        for image in images:
            logger.info(f"🔍 Image {image.id}: {image.image_url}")
        
        return jsonify({
            'success': True,
            'images': [{
                'id': image.id,
                'filename': os.path.basename(image.image_url),  # Extract filename from URL
                'url': image.image_url,
                'image_url': image.image_url,  # Add both for compatibility
                'alt_text': image.alt_text,
                'caption': image.caption,
                'order': image.order,
                'is_featured': False,  # BlogPostImage doesn't have is_featured field
                'created_at': image.created_at.isoformat() if image.created_at else None
            } for image in images]
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania obrazów postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/posts/<int:post_id>/gallery', methods=['GET'])
def get_post_gallery(post_id):
    """Get gallery images for a blog post (public endpoint)"""
    try:
        from app.models import BlogPost
        
        post = BlogPost.query.filter_by(id=post_id, status='published').first()
        if not post:
            return jsonify({'success': False, 'message': 'Post nie został znaleziony'}), 404
        
        images = BlogPostImage.query.filter_by(post_id=post_id, is_active=True).order_by(BlogPostImage.order.asc(), BlogPostImage.created_at.asc()).all()
        
        # Generate thumbnail URLs
        image_list = []
        for image in images:
            # Extract filename from URL
            filename = os.path.basename(image.image_url)
            
            # Generate thumbnail filename
            from app.utils.image_utils import generate_thumbnail_path
            thumbnail_filename = generate_thumbnail_path(filename)
            
            # Check if thumbnail exists
            thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'gallery', thumbnail_filename)
            thumbnail_url = image.image_url  # Fallback to original
            
            if os.path.exists(thumbnail_path):
                # Use thumbnail URL
                thumbnail_url = f'/static/uploads/blog/{post_id}/gallery/{thumbnail_filename}'
            
            image_list.append({
                'id': image.id,
                'url': image.image_url,
                'thumbnail_url': thumbnail_url,
                'alt_text': image.alt_text or post.title,
                'caption': image.caption,
                'order': image.order,
                'title': image.caption or image.alt_text or post.title
            })
        
        return jsonify({
            'success': True,
            'images': image_list
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania galerii postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/admin/posts/<int:post_id>/images', methods=['POST'])
@login_required
@admin_required_api
def add_post_image(post_id):
    """Add image to blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        logger.info(f"🔍 Adding image to post {post_id}")
        logger.info(f"🔍 Request content type: {request.content_type}")
        logger.info(f"🔍 Request is JSON: {request.is_json}")
        logger.info(f"🔍 Files in request: {list(request.files.keys())}")
        logger.info(f"🔍 Form data: {dict(request.form)}")
        
        # Log each file in detail
        for key, file in request.files.items():
            logger.info(f"🔍 File '{key}': filename='{file.filename}', size={file.content_length if hasattr(file, 'content_length') else 'unknown'}")
        
        # Handle both JSON (URL only) and FormData (file upload)
        if request.is_json:
            # Frontend sends JSON with image_url
            data = request.get_json()
            image_url = data.get('image_url', '')
            alt_text = data.get('alt_text', '')
            caption = data.get('caption', '')
            order = data.get('order', 0)
            
            if not image_url:
                return jsonify({
                    'success': False,
                    'message': 'Brak URL obrazu'
                }), 400
            
            # Create database record with URL
            image = BlogPostImage(
                post_id=post_id,
                image_url=image_url,
                alt_text=alt_text,
                caption=caption,
                order=order
            )
            
        else:
            # Frontend sends FormData with file
            logger.info(f"🔍 Processing FormData upload")
            # Check for both 'image' and 'image_file' (frontend sends 'image_file')
            file = None
            if 'image' in request.files:
                file = request.files['image']
                logger.info(f"🔍 Found 'image' file: {file.filename}")
            elif 'image_file' in request.files:
                file = request.files['image_file']
                logger.info(f"🔍 Found 'image_file' file: {file.filename}")
            else:
                logger.info(f"🔍 No file found in request.files")
            
            if not file or file.filename == '':
                logger.error(f"❌ No file provided: file={file}, filename={file.filename if file else 'None'}")
                return jsonify({
                    'success': False,
                    'message': 'Brak pliku obrazu'
                }), 400
            
            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'message': 'Nieprawidłowy typ pliku'
                }), 400
            
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            filename = f"{int(time.time())}_{filename}"
            
            # Create post-specific upload folder structure: media/blog/{post_id}/gallery/
            post_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'gallery')
            os.makedirs(post_folder, exist_ok=True)
            
            file_path = os.path.join(post_folder, filename)
            file.save(file_path)
            logger.info(f"✅ File saved to: {file_path}")
            
            # Create thumbnail
            from app.utils.image_utils import create_gallery_thumbnails
            thumbnail_result = create_gallery_thumbnails(post_id, filename, current_app.config['UPLOAD_FOLDER'])
            
            if thumbnail_result['success']:
                logger.info(f"✅ Thumbnail created: {thumbnail_result['thumbnail_url']}")
            else:
                logger.warning(f"⚠️ Failed to create thumbnail: {thumbnail_result.get('error', 'Unknown error')}")
            
            # Create database record with uploaded file
            image = BlogPostImage(
                post_id=post_id,
                image_url=f'/static/uploads/blog/{post_id}/gallery/{filename}',
                alt_text=request.form.get('alt_text', ''),
                caption=request.form.get('caption', ''),
                order=int(request.form.get('order', 0))
            )
            logger.info(f"✅ Created BlogPostImage record: {image.image_url}")
        
        db.session.add(image)
        db.session.commit()
        
        response_data = {
            'success': True,
            'message': 'Obraz został dodany do postu',
            'image': {
                'id': image.id,
                'filename': os.path.basename(image.image_url),
                'url': image.image_url,
                'alt_text': image.alt_text,
                'caption': image.caption,
                'order': image.order,
                'created_at': image.created_at.isoformat() if image.created_at else None
            }
        }
        
        logger.info(f"✅ Successfully added image to post {post_id}: {response_data}")
        return jsonify(response_data)
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd dodawania obrazu do postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/admin/posts/<int:post_id>/images/<int:image_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_post_image(post_id, image_id):
    """Update blog post image"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        image = BlogPostImage.query.filter_by(id=image_id, post_id=post_id).first_or_404()
        
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Handle file upload if provided
        file = None
        if 'image' in request.files:
            file = request.files['image']
        elif 'image_file' in request.files:
            file = request.files['image_file']
        
        if file and file.filename != '':
            # Update file
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                
                # Create post-specific upload folder structure: media/blog/{post_id}/gallery/
                post_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'gallery')
                os.makedirs(post_folder, exist_ok=True)
                
                file_path = os.path.join(post_folder, filename)
                file.save(file_path)
                
                # Update image URL
                image.image_url = f'/static/uploads/blog/{post_id}/gallery/{filename}'
        
        # Update fields
        if 'alt_text' in data:
            image.alt_text = data['alt_text']
        if 'caption' in data:
            image.caption = data['caption']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Obraz został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji obrazu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/admin/posts/<int:post_id>/images/<int:image_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_post_image(post_id, image_id):
    """Delete blog post image"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        image = BlogPostImage.query.filter_by(id=image_id, post_id=post_id).first_or_404()
        
        # Delete physical file
        try:
            # Extract file path from image_url
            # URL format: /static/uploads/blog/{post_id}/gallery/filename
            url_path = image.image_url.replace('/static/uploads/', '')
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], url_path)
            
            logger.info(f"🔍 Deleting file: {file_path}")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"✅ File deleted: {file_path}")
            else:
                logger.warning(f"⚠️ File not found: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️ Nie udało się usunąć pliku: {e}")
        
        # Delete database record
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Obraz został usunięty'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania obrazu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@media_api_bp.route('/blog/admin/posts/<int:post_id>/featured-image', methods=['DELETE'])
@login_required
@admin_required_api
def delete_featured_image(post_id):
    """Delete featured image from blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        if post.featured_image:
            # Try to delete the physical file
            try:
                filename = os.path.basename(post.featured_image)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"⚠️ Nie udało się usunąć pliku featured image: {e}")
            
            # Clear the featured image reference
            post.featured_image = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Główny obraz postu został usunięty'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Post nie ma głównego obrazu'
            }), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania głównego obrazu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
