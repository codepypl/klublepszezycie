#!/usr/bin/env python3
"""
User Group Service for Lepsze Życie Club
Handles user groups, members, and group operations
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_

from models import db, UserGroup, UserGroupMember, EventRegistration, Registration, EmailSubscription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserGroupService:
    """Service for handling user group operations"""
    
    def __init__(self):
        pass
    
    def create_group(self, name: str, description: str = None, 
                    group_type: str = 'manual', criteria: Dict = None) -> UserGroup:
        """
        Create a new user group
        
        Args:
            name: Group name
            description: Group description
            group_type: Type of group (manual, event_based, dynamic)
            criteria: Group criteria as dictionary
            
        Returns:
            UserGroup: Created group
        """
        try:
            group = UserGroup(
                name=name,
                description=description,
                group_type=group_type,
                criteria=json.dumps(criteria) if criteria else None
            )
            
            db.session.add(group)
            db.session.commit()
            
            logger.info(f"Created user group: {name}")
            return group
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create user group {name}: {str(e)}")
            raise
    
    def create_event_group(self, event_id: int, event_title: str) -> UserGroup:
        """
        Create a group for event registrations
        
        Args:
            event_id: Event ID
            event_title: Event title
            
        Returns:
            UserGroup: Created group
        """
        name = f"Uczestnicy: {event_title}"
        description = f"Wszyscy uczestnicy wydarzenia: {event_title}"
        
        criteria = {
            'event_id': event_id,
            'type': 'event_registrations'
        }
        
        return self.create_group(name, description, 'event_based', criteria)
    
    def add_member_to_group(self, group_id: int, email: str, name: str = None,
                           member_type: str = 'email', metadata: Dict = None) -> UserGroupMember:
        """
        Add a member to a group
        
        Args:
            group_id: Group ID
            email: Member email
            name: Member name
            member_type: Type of member
            metadata: Additional metadata
            
        Returns:
            UserGroupMember: Created member
        """
        try:
            # Check if member already exists
            existing_member = UserGroupMember.query.filter_by(
                group_id=group_id,
                email=email
            ).first()
            
            if existing_member:
                # Update existing member
                existing_member.name = name or existing_member.name
                existing_member.member_type = member_type
                existing_member.member_metadata = json.dumps(metadata) if metadata else existing_member.member_metadata
                existing_member.is_active = True
                existing_member.updated_at = datetime.utcnow()
                
                member = existing_member
            else:
                # Create new member
                member = UserGroupMember(
                    group_id=group_id,
                    email=email,
                    name=name,
                    member_type=member_type,
                    member_metadata=json.dumps(metadata) if metadata else None
                )
                db.session.add(member)
            
            db.session.commit()
            
            # Update group member count
            group = UserGroup.query.get(group_id)
            if group:
                group.update_member_count()
                db.session.commit()
            
            logger.info(f"Added member {email} to group {group_id}")
            return member
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add member {email} to group {group_id}: {str(e)}")
            raise
    
    def remove_member_from_group(self, group_id: int, email: str) -> bool:
        """
        Remove a member from a group
        
        Args:
            group_id: Group ID
            email: Member email
            
        Returns:
            bool: True if removed successfully
        """
        try:
            member = UserGroupMember.query.filter_by(
                group_id=group_id,
                email=email
            ).first()
            
            if member:
                member.is_active = False
                member.updated_at = datetime.utcnow()
                db.session.commit()
                
                # Update group member count
                group = UserGroup.query.get(group_id)
                if group:
                    group.update_member_count()
                    db.session.commit()
                
                logger.info(f"Removed member {email} from group {group_id}")
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to remove member {email} from group {group_id}: {str(e)}")
            raise
    
    def get_group_members(self, group_id: int, active_only: bool = True) -> List[UserGroupMember]:
        """
        Get all members of a group
        
        Args:
            group_id: Group ID
            active_only: Return only active members
            
        Returns:
            List[UserGroupMember]: List of members
        """
        try:
            query = UserGroupMember.query.filter_by(group_id=group_id)
            
            if active_only:
                query = query.filter_by(is_active=True)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Failed to get members for group {group_id}: {str(e)}")
            return []
    
    def get_group_by_event(self, event_id: int) -> Optional[UserGroup]:
        """
        Get group for a specific event
        
        Args:
            event_id: Event ID
            
        Returns:
            UserGroup: Event group or None
        """
        try:
            return UserGroup.query.filter(
                and_(
                    UserGroup.group_type == 'event_based',
                    UserGroup.criteria.contains(f'"event_id": {event_id}')
                )
            ).first()
            
        except Exception as e:
            logger.error(f"Failed to get group for event {event_id}: {str(e)}")
            return None
    
    def sync_event_group_members(self, event_id: int) -> Tuple[int, int]:
        """
        Synchronize event group members with current registrations
        
        Args:
            event_id: Event ID
            
        Returns:
            Tuple[int, int]: (added_count, removed_count)
        """
        try:
            # Get or create event group
            group = self.get_group_by_event(event_id)
            if not group:
                # This should be handled by event registration
                logger.warning(f"No group found for event {event_id}")
                return 0, 0
            
            # Get current registrations
            current_registrations = EventRegistration.query.filter_by(
                event_id=event_id,
                status='confirmed'
            ).all()
            
            current_emails = {reg.email for reg in current_registrations}
            
            # Get current group members
            current_members = self.get_group_members(group.id)
            current_member_emails = {member.email for member in current_members}
            
            # Add new members
            added_count = 0
            for reg in current_registrations:
                if reg.email not in current_member_emails:
                    self.add_member_to_group(
                        group.id,
                        reg.email,
                        reg.name,
                        'event_registration',
                        {'event_id': event_id, 'registration_id': reg.id}
                    )
                    added_count += 1
            
            # Remove members no longer registered
            removed_count = 0
            for member in current_members:
                if member.email not in current_emails:
                    self.remove_member_from_group(group.id, member.email)
                    removed_count += 1
            
            logger.info(f"Synced event group {group.id}: {added_count} added, {removed_count} removed")
            return added_count, removed_count
            
        except Exception as e:
            logger.error(f"Failed to sync event group members for event {event_id}: {str(e)}")
            raise
    
    def create_manual_group(self, name: str, description: str = None, 
                           emails: List[str] = None) -> UserGroup:
        """
        Create a manual group with specific emails
        
        Args:
            name: Group name
            description: Group description
            emails: List of email addresses
            
        Returns:
            UserGroup: Created group
        """
        try:
            group = self.create_group(name, description, 'manual')
            
            if emails:
                for email in emails:
                    self.add_member_to_group(group.id, email, member_type='email')
            
            return group
            
        except Exception as e:
            logger.error(f"Failed to create manual group {name}: {str(e)}")
            raise
    
    def get_groups_by_type(self, group_type: str) -> List[UserGroup]:
        """
        Get groups by type
        
        Args:
            group_type: Type of groups to return
            
        Returns:
            List[UserGroup]: List of groups
        """
        try:
            return UserGroup.query.filter_by(
                group_type=group_type,
                is_active=True
            ).all()
            
        except Exception as e:
            logger.error(f"Failed to get groups by type {group_type}: {str(e)}")
            return []
    
    def search_groups(self, query: str) -> List[UserGroup]:
        """
        Search groups by name or description
        
        Args:
            query: Search query
            
        Returns:
            List[UserGroup]: List of matching groups
        """
        try:
            return UserGroup.query.filter(
                and_(
                    UserGroup.is_active == True,
                    or_(
                        UserGroup.name.ilike(f'%{query}%'),
                        UserGroup.description.ilike(f'%{query}%')
                    )
                )
            ).all()
            
        except Exception as e:
            logger.error(f"Failed to search groups with query '{query}': {str(e)}")
            return []
    
    def delete_group(self, group_id: int) -> bool:
        """
        Delete a group and all its members
        
        Args:
            group_id: Group ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                return False
            
            # Delete all members (cascade will handle this)
            db.session.delete(group)
            db.session.commit()
            
            logger.info(f"Deleted group {group_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete group {group_id}: {str(e)}")
            raise
    
    def get_group_statistics(self, group_id: int) -> Dict:
        """
        Get statistics for a group
        
        Args:
            group_id: Group ID
            
        Returns:
            Dict: Group statistics
        """
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                return {}
            
            members = self.get_group_members(group.id)
            
            # Count by member type
            type_counts = {}
            for member in members:
                member_type = member.member_type
                type_counts[member_type] = type_counts.get(member_type, 0) + 1
            
            return {
                'total_members': len(members),
                'active_members': len([m for m in members if m.is_active]),
                'member_types': type_counts,
                'created_at': group.created_at.isoformat(),
                'last_updated': group.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics for group {group_id}: {str(e)}")
            return {}


# Global service instance
user_group_service = UserGroupService()
