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
    calls as crm_calls_func,
    contacts as crm_contacts_func,
    work as crm_work_func
)

# Ankieter Dashboard
@ankieter_bp.route('/')
@login_required
@ankieter_required
def dashboard():
    """Ankieter Dashboard"""
    return crm_dashboard_func()

# Calls management
@ankieter_bp.route('/calls')
@login_required
@ankieter_required
def calls():
    """Calls management page"""
    return crm_calls_func()

# Contacts management
@ankieter_bp.route('/contacts')
@login_required
@ankieter_required
def contacts():
    """Contacts management page"""
    return crm_contacts_func()

# Work page
@ankieter_bp.route('/work')
@login_required
@ankieter_required
def work():
    """Work page for ankieter"""
    return crm_work_func()
