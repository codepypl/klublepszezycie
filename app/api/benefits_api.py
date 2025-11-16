"""
Benefits API endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models import BenefitItem, db
from app.utils.auth_utils import admin_required_api, login_required_api
import logging
import os
import time

benefits_api_bp = Blueprint('benefits_api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@benefits_api_bp.route('/benefits', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required_api
def api_benefits():
    """Benefits API"""
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            pagination = BenefitItem.query.order_by(BenefitItem.order.asc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'success': True,
                'benefits': [{
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'image': benefit.image,
                    'order': benefit.order,
                    'is_active': benefit.is_active,
                    'created_at': benefit.created_at.isoformat() if benefit.created_at else None
                } for benefit in pagination.items],
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'total': pagination.total,
                    'per_page': pagination.per_page
                }
            })
        except Exception as e:
            logging.error(f"Error getting benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Handle both JSON and FormData
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            logging.info(f"Creating benefit with data: {data}")
            
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            if not data.get('title'):
                return jsonify({'success': False, 'message': 'Title is required'}), 400
            
            # Handle image upload
            image_path = None
            if 'image' in request.files and request.files['image'].filename:
                file = request.files['image']
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid conflicts
                    filename = f"{int(time.time())}_{filename}"
                    
                    # Create benefits-specific upload folder
                    benefits_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'benefits')
                    os.makedirs(benefits_upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(benefits_upload_folder, filename)
                    file.save(file_path)
                    
                    # Automatically resize image to optimal size (max 800x600)
                    try:
                        from app.utils.image_utils import resize_benefit_image
                        resize_success, resized_path = resize_benefit_image(file_path, max_width=800, max_height=600, quality=85)
                        if resize_success:
                            # Update filename if path changed (e.g., extension changed to .jpg)
                            if resized_path != file_path:
                                filename = os.path.basename(resized_path)
                                file_path = resized_path
                            logging.info(f"✅ Image resized successfully: {filename}")
                        else:
                            logging.warning(f"⚠️ Failed to resize image, but keeping original: {filename}")
                    except Exception as e:
                        logging.warning(f"⚠️ Error during image resize: {e}, keeping original image")
                    
                    image_path = f'/static/uploads/benefits/{filename}'
                    logging.info(f"Image saved to: {image_path}")
                else:
                    return jsonify({'success': False, 'message': 'Nieprawidłowy typ pliku obrazu'}), 400
            
            benefit = BenefitItem(
                title=data['title'],
                description=data.get('description', ''),
                icon=data.get('icon', ''),
                image=image_path,
                order=data.get('order', 0),
                is_active=data.get('is_active', True) if isinstance(data.get('is_active'), bool) else (data.get('is_active') == 'true' or data.get('is_active') == 'on')
            )
            
            db.session.add(benefit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit created successfully',
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'image': benefit.image,
                    'order': benefit.order,
                    'is_active': benefit.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating benefit: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            benefit_ids = data.get('benefit_ids', data.get('ids', []))
            
            if not benefit_ids:
                return jsonify({'success': False, 'message': 'No benefits selected'}), 400
            
            updated_count = 0
            for benefit_id in benefit_ids:
                benefit = BenefitItem.query.get(benefit_id)
                if benefit:
                    if 'title' in data:
                        benefit.title = data['title']
                    if 'description' in data:
                        benefit.description = data['description']
                    if 'icon' in data:
                        benefit.icon = data['icon']
                    if 'order' in data:
                        benefit.order = data['order']
                    if 'is_active' in data:
                        benefit.is_active = data['is_active']
                    updated_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully updated {updated_count} benefits'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk updating benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            benefit_ids = data.get('benefit_ids', data.get('ids', []))
            
            if not benefit_ids:
                return jsonify({'success': False, 'message': 'No benefits selected'}), 400
            
            deleted_count = 0
            for benefit_id in benefit_ids:
                benefit = BenefitItem.query.get(benefit_id)
                if benefit:
                    db.session.delete(benefit)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} benefits'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting benefits: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@benefits_api_bp.route('/benefits/<int:benefit_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required_api
def api_benefit(benefit_id):
    """Individual benefit API"""
    benefit = BenefitItem.query.get(benefit_id)
    
    if not benefit:
        return jsonify({
            'success': False,
            'error': f'Benefit with ID {benefit_id} not found'
        }), 404
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'image': benefit.image,
                    'order': benefit.order,
                    'is_active': benefit.is_active,
                    'created_at': benefit.created_at.isoformat() if benefit.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            # Handle both JSON and FormData
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            if 'title' in data:
                benefit.title = data['title']
            if 'description' in data:
                benefit.description = data['description']
            if 'icon' in data:
                benefit.icon = data['icon']
            if 'order' in data:
                benefit.order = data['order']
            if 'is_active' in data:
                benefit.is_active = data['is_active'] if isinstance(data['is_active'], bool) else (data['is_active'] == 'true' or data['is_active'] == 'on')
            
            # Check if remove_image flag is set (from FormData or JSON)
            remove_image = False
            if 'remove_image' in data:
                remove_image = data['remove_image'] == 'true' or data['remove_image'] == True
            elif 'remove_image' in request.form:
                remove_image = request.form.get('remove_image') == 'true'
            
            if remove_image:
                # Remove image if flag is set
                if benefit.image:
                    benefits_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'benefits')
                    old_image_path = benefit.image.replace('/static/uploads/benefits/', '')
                    old_full_path = os.path.join(benefits_upload_folder, old_image_path)
                    if os.path.exists(old_full_path):
                        try:
                            os.remove(old_full_path)
                            logging.info(f"✅ Deleted image file: {old_full_path}")
                        except Exception as e:
                            logging.warning(f"Could not delete old image: {e}")
                    benefit.image = None
                    logging.info(f"Image removed from benefit {benefit.id}")
            # Handle image upload if provided
            elif 'image' in request.files and request.files['image'].filename:
                file = request.files['image']
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Add timestamp to avoid conflicts
                    filename = f"{int(time.time())}_{filename}"
                    
                    # Create benefits-specific upload folder
                    benefits_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'benefits')
                    os.makedirs(benefits_upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(benefits_upload_folder, filename)
                    file.save(file_path)
                    
                    # Automatically resize image to optimal size (max 800x600)
                    try:
                        from app.utils.image_utils import resize_benefit_image
                        resize_success, resized_path = resize_benefit_image(file_path, max_width=800, max_height=600, quality=85)
                        if resize_success:
                            # Update filename if path changed (e.g., extension changed to .jpg)
                            if resized_path != file_path:
                                filename = os.path.basename(resized_path)
                                file_path = resized_path
                            logging.info(f"✅ Image resized successfully: {filename}")
                        else:
                            logging.warning(f"⚠️ Failed to resize image, but keeping original: {filename}")
                    except Exception as e:
                        logging.warning(f"⚠️ Error during image resize: {e}, keeping original image")
                    
                    # Delete old image if exists
                    if benefit.image:
                        old_image_path = benefit.image.replace('/static/uploads/benefits/', '')
                        old_full_path = os.path.join(benefits_upload_folder, old_image_path)
                        if os.path.exists(old_full_path):
                            try:
                                os.remove(old_full_path)
                            except Exception as e:
                                logging.warning(f"Could not delete old image: {e}")
                    
                    benefit.image = f'/static/uploads/benefits/{filename}'
                    logging.info(f"Image updated to: {benefit.image}")
                else:
                    return jsonify({'success': False, 'message': 'Nieprawidłowy typ pliku obrazu'}), 400
            elif 'image' in data and data['image'] == '':
                # Clear image if empty string is sent
                if benefit.image:
                    benefits_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'benefits')
                    old_image_path = benefit.image.replace('/static/uploads/benefits/', '')
                    old_full_path = os.path.join(benefits_upload_folder, old_image_path)
                    if os.path.exists(old_full_path):
                        try:
                            os.remove(old_full_path)
                        except Exception as e:
                            logging.warning(f"Could not delete old image: {e}")
                benefit.image = None
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit updated successfully',
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'image': benefit.image,
                    'order': benefit.order,
                    'is_active': benefit.is_active
                }
            })
        
        elif request.method == 'DELETE':
            db.session.delete(benefit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Benefit deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with benefit {benefit_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@benefits_api_bp.route('/bulk-delete/benefits', methods=['POST'])
@login_required_api
@admin_required_api
def api_bulk_delete_benefits():
    """Bulk delete benefits"""
    try:
        data = request.get_json()
        benefit_ids = data.get('benefit_ids', data.get('ids', []))
        
        if not benefit_ids:
            return jsonify({'success': False, 'message': 'No benefits selected'}), 400
        
        deleted_count = 0
        for benefit_id in benefit_ids:
            benefit = BenefitItem.query.get(benefit_id)
            if benefit:
                db.session.delete(benefit)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} benefits'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting benefits: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
