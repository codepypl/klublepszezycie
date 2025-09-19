"""
Stats Model - statystyki systemu
"""
from datetime import datetime
from . import db

class Stats(db.Model):
    __tablename__ = 'stats'
    
    id = db.Column(db.Integer, primary_key=True)
    stat_type = db.Column(db.String(50), nullable=False, index=True)  # 'total_users', 'total_events', 'event_registrations', etc.
    stat_value = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.String(255), nullable=True)  # Human readable description
    related_id = db.Column(db.Integer, nullable=True)  # ID of related entity (event_id, user_id, etc.)
    related_type = db.Column(db.String(50), nullable=True)  # Type of related entity ('event', 'user', 'group')
    date_period = db.Column(db.Date, nullable=True, index=True)  # For time-based stats
    extra_data = db.Column(db.JSON, nullable=True)  # Additional data as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate stats
    __table_args__ = (
        db.UniqueConstraint('stat_type', 'related_id', 'related_type', 'date_period', name='unique_stat'),
    )
    
    def __repr__(self):
        return f'<Stats {self.stat_type}: {self.stat_value}>'
    
    @classmethod
    def get_or_create(cls, stat_type, related_id=None, related_type=None, date_period=None):
        """Get existing stat or create new one"""
        stat = cls.query.filter_by(
            stat_type=stat_type,
            related_id=related_id,
            related_type=related_type,
            date_period=date_period
        ).first()
        
        if not stat:
            stat = cls(
                stat_type=stat_type,
                related_id=related_id,
                related_type=related_type,
                date_period=date_period,
                stat_value=0
            )
            db.session.add(stat)
        
        return stat
    
    @classmethod
    def increment(cls, stat_type, related_id=None, related_type=None, date_period=None, amount=1):
        """Increment stat value"""
        stat = cls.get_or_create(stat_type, related_id, related_type, date_period)
        stat.stat_value += amount
        stat.updated_at = datetime.utcnow()
        db.session.commit()
        return stat
    
    @classmethod
    def decrement(cls, stat_type, related_id=None, related_type=None, date_period=None, amount=1):
        """Decrement stat value"""
        stat = cls.get_or_create(stat_type, related_id, related_type, date_period)
        stat.stat_value = max(0, stat.stat_value - amount)
        stat.updated_at = datetime.utcnow()
        db.session.commit()
        return stat
    
    @classmethod
    def set_value(cls, stat_type, value, related_id=None, related_type=None, date_period=None):
        """Set stat value"""
        stat = cls.get_or_create(stat_type, related_id, related_type, date_period)
        stat.stat_value = value
        stat.updated_at = datetime.utcnow()
        db.session.commit()
        return stat
    
    @classmethod
    def get_value(cls, stat_type, related_id=None, related_type=None, date_period=None):
        """Get stat value"""
        stat = cls.query.filter_by(
            stat_type=stat_type,
            related_id=related_id,
            related_type=related_type,
            date_period=date_period
        ).first()
        
        return stat.stat_value if stat else 0
    
    @classmethod
    def get_total_users(cls):
        """Get total users count"""
        return cls.get_value('total_users')
    
    @classmethod
    def get_total_events(cls):
        """Get total events count"""
        return cls.get_value('total_events')
    
    @classmethod
    def get_total_registrations(cls):
        """Get total registrations count"""
        return cls.get_value('total_registrations')
    
    @classmethod
    def get_event_registrations(cls, event_id):
        """Get registrations count for specific event"""
        return cls.get_value('event_registrations', related_id=event_id, related_type='event')
    
    @classmethod
    def get_daily_registrations(cls, date):
        """Get registrations count for specific date"""
        return cls.get_value('daily_registrations', date_period=date)
    
    @classmethod
    def update_total_users(cls):
        """Update total users count from database"""
        from .user_model import User
        count = User.query.count()
        cls.set_value('total_users', count)
        return count
    
    @classmethod
    def update_total_events(cls):
        """Update total events count from database"""
        from .events_model import EventSchedule
        count = EventSchedule.query.count()
        cls.set_value('total_events', count)
        return count
    
    @classmethod
    def update_total_registrations(cls):
        """Update total registrations count from database"""
        from .user_model import User
        count = User.query.filter_by(account_type='event_registration').count()
        cls.set_value('total_registrations', count)
        return count
    
    @classmethod
    def update_event_registrations(cls, event_id):
        """Update registrations count for specific event"""
        from .user_model import User
        count = User.query.filter_by(
            event_id=event_id,
            account_type='event_registration'
        ).count()
        cls.set_value('event_registrations', count, related_id=event_id, related_type='event')
        return count
    
    # Blog Statistics
    @classmethod
    def get_total_blog_posts(cls):
        """Get total blog posts count"""
        return cls.get_value('total_blog_posts')
    
    @classmethod
    def get_total_blog_categories(cls):
        """Get total blog categories count"""
        return cls.get_value('total_blog_categories')
    
    @classmethod
    def get_total_blog_comments(cls):
        """Get total blog comments count"""
        return cls.get_value('total_blog_comments')
    
    @classmethod
    def update_blog_stats(cls):
        """Update blog statistics from database"""
        from .blog_model import BlogPost, BlogCategory, BlogComment
        blog_posts = BlogPost.query.count()
        blog_categories = BlogCategory.query.count()
        blog_comments = BlogComment.query.count()
        
        cls.set_value('total_blog_posts', blog_posts)
        cls.set_value('total_blog_categories', blog_categories)
        cls.set_value('total_blog_comments', blog_comments)
        
        return {'blog_posts': blog_posts, 'blog_categories': blog_categories, 'blog_comments': blog_comments}
    
    # CRM Statistics
    @classmethod
    def get_total_contacts(cls):
        """Get total contacts count"""
        return cls.get_value('total_contacts')
    
    @classmethod
    def get_total_calls(cls):
        """Get total calls count"""
        return cls.get_value('total_calls')
    
    @classmethod
    def get_total_imports(cls):
        """Get total imports count"""
        return cls.get_value('total_imports')
    
    @classmethod
    def get_total_blacklist(cls):
        """Get total blacklist entries count"""
        return cls.get_value('total_blacklist')
    
    @classmethod
    def get_daily_calls(cls, date=None):
        """Get daily calls count"""
        if date is None:
            from datetime import date
            date = date.today()
        return cls.get_value('daily_calls', date_period=date)
    
    @classmethod
    def get_daily_leads(cls, date=None):
        """Get daily leads count"""
        if date is None:
            from datetime import date
            date = date.today()
        return cls.get_value('daily_leads', date_period=date)
    
    @classmethod
    def update_crm_stats(cls):
        """Update CRM statistics from database"""
        from .crm_model import Contact, Call, ImportFile, BlacklistEntry
        from datetime import date, datetime
        
        total_contacts = Contact.query.count()
        total_calls = Call.query.count()
        total_imports = ImportFile.query.count()
        total_blacklist = BlacklistEntry.query.count()
        
        today = date.today()
        daily_calls = Call.query.filter(Call.created_at >= today).count()
        daily_leads = Call.query.filter(
            Call.created_at >= today,
            Call.status == 'lead'
        ).count()
        
        cls.set_value('total_contacts', total_contacts)
        cls.set_value('total_calls', total_calls)
        cls.set_value('total_imports', total_imports)
        cls.set_value('total_blacklist', total_blacklist)
        cls.set_value('daily_calls', daily_calls, date_period=today)
        cls.set_value('daily_leads', daily_leads, date_period=today)
        
        return {
            'total_contacts': total_contacts,
            'total_calls': total_calls,
            'total_imports': total_imports,
            'total_blacklist': total_blacklist,
            'daily_calls': daily_calls,
            'daily_leads': daily_leads
        }
    
    # Email Statistics
    @classmethod
    def get_total_emails(cls):
        """Get total emails in queue count"""
        return cls.get_value('total_emails')
    
    @classmethod
    def get_pending_emails(cls):
        """Get pending emails count"""
        return cls.get_value('pending_emails')
    
    @classmethod
    def get_sent_emails(cls):
        """Get sent emails count"""
        return cls.get_value('sent_emails')
    
    @classmethod
    def get_failed_emails(cls):
        """Get failed emails count"""
        return cls.get_value('failed_emails')
    
    @classmethod
    def get_bounced_emails(cls):
        """Get bounced emails count"""
        return cls.get_value('bounced_emails')
    
    @classmethod
    def get_total_email_logs(cls):
        """Get total email logs count"""
        return cls.get_value('total_email_logs')
    
    @classmethod
    def update_email_stats(cls):
        """Update email statistics from database"""
        from .email_model import EmailQueue, EmailLog
        
        # Queue stats
        total_emails = EmailQueue.query.count()
        pending_emails = EmailQueue.query.filter_by(status='pending').count()
        sent_emails = EmailQueue.query.filter_by(status='sent').count()
        failed_emails = EmailQueue.query.filter_by(status='failed').count()
        
        # Log stats
        total_email_logs = EmailLog.query.count()
        bounced_emails = EmailLog.query.filter_by(status='bounced').count()
        
        cls.set_value('total_emails', total_emails)
        cls.set_value('pending_emails', pending_emails)
        cls.set_value('sent_emails', sent_emails)
        cls.set_value('failed_emails', failed_emails)
        cls.set_value('total_email_logs', total_email_logs)
        cls.set_value('bounced_emails', bounced_emails)
        
        return {
            'total_emails': total_emails,
            'pending_emails': pending_emails,
            'sent_emails': sent_emails,
            'failed_emails': failed_emails,
            'total_email_logs': total_email_logs,
            'bounced_emails': bounced_emails
        }
    
    # User Statistics
    @classmethod
    def get_active_users(cls):
        """Get active users count"""
        return cls.get_value('active_users')
    
    @classmethod
    def get_admin_users(cls):
        """Get admin users count"""
        return cls.get_value('admin_users')
    
    @classmethod
    def get_new_users_30_days(cls):
        """Get new users from last 30 days count"""
        return cls.get_value('new_users_30_days')
    
    @classmethod
    def update_user_stats(cls):
        """Update user statistics from database"""
        from .user_model import User
        from datetime import datetime, timedelta
        
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(account_type='admin').count()
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30_days = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        cls.set_value('total_users', total_users)
        cls.set_value('active_users', active_users)
        cls.set_value('admin_users', admin_users)
        cls.set_value('new_users_30_days', new_users_30_days)
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'new_users_30_days': new_users_30_days
        }
    
    # Other Statistics
    @classmethod
    def get_total_testimonials(cls):
        """Get total testimonials count"""
        return cls.get_value('total_testimonials')
    
    @classmethod
    def update_testimonials_stats(cls):
        """Update testimonials statistics from database"""
        from .content_model import Testimonial
        count = Testimonial.query.count()
        cls.set_value('total_testimonials', count)
        return count
    
    # Bulk update method
    @classmethod
    def update_all_stats(cls):
        """Update all statistics from database"""
        results = {}
        results.update(cls.update_user_stats())
        
        # Update individual stats that return single values
        results['total_events'] = cls.update_total_events()
        results['total_registrations'] = cls.update_total_registrations()
        results['total_testimonials'] = cls.update_testimonials_stats()
        
        # Update stats that return dictionaries
        results.update(cls.update_blog_stats())
        results.update(cls.update_crm_stats())
        results.update(cls.update_email_stats())
        
        return results
