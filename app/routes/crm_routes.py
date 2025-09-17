"""
CRM Routes - Routes for CRM functionality
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.blueprints.crm_controller import ankieter_required

# Create CRM routes blueprint
crm_bp = Blueprint('crm', __name__)

# Import CRM controller functions
from app.blueprints.crm_controller import (
    dashboard,
    calls,
    contacts,
    work
)

# CRM Dashboard
@crm_bp.route('/')
@login_required
@ankieter_required
def crm_dashboard():
    """CRM Dashboard"""
    return dashboard()

# Calls management
@crm_bp.route('/calls')
@login_required
@ankieter_required
def crm_calls():
    """Calls management page"""
    return calls()

# Contacts management
@crm_bp.route('/contacts')
@login_required
@ankieter_required
def crm_contacts():
    """Contacts management page"""
    return contacts()

# Work page
@crm_bp.route('/work')
@login_required
@ankieter_required
def crm_work():
    """Work page for ankieter"""
    return work()
