"""
Admin CRM Routes - Routes for admin CRM management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.utils.auth_utils import admin_required

# Create Admin CRM routes blueprint
crm_bp = Blueprint('crm', __name__)

# Import CRM controller functions
from app.blueprints.crm_controller import (
    dashboard as crm_dashboard_func,
    calls as crm_calls_func,
    contacts as crm_contacts_func,
    work as crm_work_func
)

# Admin CRM Dashboard
@crm_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin CRM Dashboard"""
    return crm_dashboard_func()

# Admin CRM Calls management
@crm_bp.route('/calls')
@login_required
@admin_required
def calls():
    """Admin CRM Calls management page"""
    return crm_calls_func()

# Admin CRM Contacts management
@crm_bp.route('/contacts')
@login_required
@admin_required
def contacts():
    """Admin CRM Contacts management page"""
    return crm_contacts_func()

# Admin CRM Work page
@crm_bp.route('/work')
@login_required
@admin_required
def work():
    """Admin CRM Work page"""
    return crm_work_func()
