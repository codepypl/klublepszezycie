"""
Content-related models (sections, benefits, testimonials, etc.)
"""
from datetime import datetime
from . import db

class MenuItem(db.Model):
    """Navigation menu items"""
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    blog_url = db.Column(db.String(200))  # Alternative URL for blog pages
    blog = db.Column(db.Boolean, default=False)  # Show only on blog pages
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuItem {self.title}>'

class Section(db.Model):
    """Website sections"""
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.Text)
    content = db.Column(db.Text)
    background_image = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Pillars configuration
    enable_pillars = db.Column(db.Boolean, default=False)
    pillars_count = db.Column(db.Integer, default=4)
    pillars_data = db.Column(db.Text)  # JSON data for pillars
    
    # Floating cards configuration
    enable_floating_cards = db.Column(db.Boolean, default=False)
    floating_cards_count = db.Column(db.Integer, default=3)
    floating_cards_data = db.Column(db.Text)  # JSON data for floating cards
    
    # Final text
    final_text = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Section {self.name}>'

class BenefitItem(db.Model):
    """Benefits items"""
    __tablename__ = 'benefit_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BenefitItem {self.title}>'

class Testimonial(db.Model):
    """Customer testimonials"""
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100), nullable=False)
    member_since = db.Column(db.String(100))  # Changed from author_title to member_since
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Testimonial {self.author_name}>'

class SocialLink(db.Model):
    """Social media links"""
    __tablename__ = 'social_links'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SocialLink {self.platform}>'

class FAQ(db.Model):
    """Frequently Asked Questions"""
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FAQ {self.question[:50]}...>'
