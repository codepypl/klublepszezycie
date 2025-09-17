"""
Blog-related models
"""
from datetime import datetime
from . import db

class BlogCategory(db.Model):
    """Blog categories"""
    __tablename__ = 'blog_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('BlogPost', secondary='blog_post_categories', back_populates='categories')
    
    def __repr__(self):
        return f'<BlogCategory {self.title}>'

class BlogTag(db.Model):
    """Blog tags"""
    __tablename__ = 'blog_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('BlogPost', secondary='blog_post_tags', back_populates='tags')
    
    def __repr__(self):
        return f'<BlogTag {self.name}>'

class BlogPost(db.Model):
    """Blog posts"""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(200))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    is_featured = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    social_facebook = db.Column(db.Boolean, default=False)
    social_twitter = db.Column(db.Boolean, default=False)
    social_linkedin = db.Column(db.Boolean, default=False)
    social_instagram = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    # Relationships
    author = db.relationship('User', backref='blog_posts')
    categories = db.relationship('BlogCategory', secondary='blog_post_categories', back_populates='posts')
    tags = db.relationship('BlogTag', secondary='blog_post_tags', back_populates='posts')
    comments = db.relationship('BlogComment', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def is_published(self):
        """Check if post is published"""
        return self.status == 'published' and self.published_at is not None
    
    @property
    def reading_time(self):
        """Estimate reading time in minutes"""
        words_per_minute = 200
        word_count = len(self.content.split())
        return max(1, word_count // words_per_minute)
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'

class BlogComment(db.Model):
    """Blog comments with threaded support"""
    __tablename__ = 'blog_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('blog_comments.id'), nullable=True)
    
    # Author information
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Additional tracking information
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    browser = db.Column(db.String(100))
    operating_system = db.Column(db.String(100))
    location_country = db.Column(db.String(100))
    location_city = db.Column(db.String(100))
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post = db.relationship('BlogPost')
    parent = db.relationship('BlogComment', remote_side=[id], backref='replies')
    
    def __repr__(self):
        return f'<BlogComment {self.author_name} on post {self.post_id}>'
