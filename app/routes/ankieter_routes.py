"""
Ankieter Routes - Routes for ankieter CRM functionality
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.blueprints.crm_controller import ankieter_required

# Create Ankieter routes blueprint
ankieter_bp = Blueprint('ankieter', __name__)

# Import CRM controller functions
from app.blueprints.crm_controller import (
    dashboard as crm_dashboard_func,
    work as crm_work_func
)

# Ankieter Dashboard
@ankieter_bp.route('/')
@login_required
@ankieter_required
def dashboard():
    """Ankieter Dashboard"""
    return crm_dashboard_func()

# Calls and contacts are only for administrators
# Ankieter doesn't need these routes

# Work page
@ankieter_bp.route('/work')
@login_required
@ankieter_required
def work():
    """Work page for ankieter"""
    return crm_work_func()
