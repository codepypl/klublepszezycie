"""
Ankieter Routes - Routes for ankieter functionality
Note: CRM functionality has been removed
"""
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.auth_utils import ankieter_required

# Create Ankieter routes blueprint
ankieter_bp = Blueprint('ankieter', __name__)

# Ankieter Dashboard
@ankieter_bp.route('/')
@login_required
@ankieter_required
def dashboard():
    """Ankieter Dashboard"""
    flash('Moduł ankietera jest obecnie niedostępny. Funkcjonalność CRM została usunięta.', 'info')
    return redirect(url_for('public.index'))

# Work page
@ankieter_bp.route('/work')
@login_required
@ankieter_required
def work():
    """Work page for ankieter"""
    flash('Moduł ankietera jest obecnie niedostępny. Funkcjonalność CRM została usunięta.', 'info')
    return redirect(url_for('public.index'))
