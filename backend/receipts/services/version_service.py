"""
Version Service - Handles receipt versioning and audit logging.
"""
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from receipts.models import Receipt, ReceiptVersion, AuditLog, UploadBatch

User = get_user_model()
logger = logging.getLogger('receipts')


class VersionService:
    """
    Service for managing receipt versions.
    
    Key principles:
    - Never update existing version records
    - Every change creates a new version
    - Field-level changes are logged in audit_logs
    - Receipt.current_version always points to latest
    """
    
    FEE_FIELDS = [
        'annual_fee',
        'tuition_fee', 
        'kit_books_fee',
        'activity_fee',
        'uniform_fee',
    ]
    
    TRACKED_FIELDS = [
        'student_name',
        'class_name',
        'payment_mode',
        'date',
    ] + FEE_FIELDS
    
    @staticmethod
    def create_initial_version(
        receipt: Receipt,
        data: Dict[str, Any],
        batch: UploadBatch = None,
        user: User = None
    ) -> ReceiptVersion:
        """
        Create the first version of a receipt.
        
        Args:
            receipt: The receipt instance
            data: Dictionary with receipt data
            batch: Optional upload batch
            user: User who made the change
            
        Returns:
            Created ReceiptVersion instance
        """
        version = ReceiptVersion.objects.create(
            receipt=receipt,
            version_number=1,
            student_name=data.get('student_name', ''),
            class_name=data.get('class_name', ''),
            payment_mode=data.get('payment_mode', 'cash'),
            date=data.get('date'),
            annual_fee=data.get('annual_fee', Decimal('0.00')),
            tuition_fee=data.get('tuition_fee', Decimal('0.00')),
            kit_books_fee=data.get('kit_books_fee', Decimal('0.00')),
            activity_fee=data.get('activity_fee', Decimal('0.00')),
            uniform_fee=data.get('uniform_fee', Decimal('0.00')),
            source='upload' if batch else 'manual_edit',
            batch=batch,
            changed_by=user
        )
        
        # Update receipt to point to current version
        receipt.current_version = version
        receipt.save(update_fields=['current_version', 'updated_at'])
        
        logger.info(f"Created version 1 for receipt {receipt.receipt_number}")
        
        return version
    
    @staticmethod
    def compare_versions(
        old_version: ReceiptVersion,
        new_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare old version with new data to find changes.
        
        Args:
            old_version: Current version
            new_data: New data dictionary
            
        Returns:
            Dictionary of changed fields: {field_name: {'old': value, 'new': value}}
        """
        changes = {}
        
        for field in VersionService.TRACKED_FIELDS:
            old_value = getattr(old_version, field)
            new_value = new_data.get(field)
            
            # Handle date comparison
            if field == 'date' and new_value:
                if hasattr(new_value, 'isoformat'):
                    new_value_str = new_value.isoformat()
                else:
                    new_value_str = str(new_value)
                old_value_str = old_value.isoformat() if old_value else None
                
                if old_value_str != new_value_str:
                    changes[field] = {'old': old_value_str, 'new': new_value_str}
                continue
            
            # Handle decimal comparison
            if field in VersionService.FEE_FIELDS:
                if new_value is not None:
                    new_decimal = Decimal(str(new_value)) if not isinstance(new_value, Decimal) else new_value
                    if old_value != new_decimal:
                        changes[field] = {'old': str(old_value), 'new': str(new_decimal)}
                continue
            
            # Handle string fields
            if new_value is not None and str(old_value) != str(new_value):
                changes[field] = {'old': str(old_value), 'new': str(new_value)}
        
        return changes
    
    @staticmethod
    @transaction.atomic
    def create_new_version(
        receipt: Receipt,
        new_data: Dict[str, Any],
        user: User = None,
        reason: str = '',
        source: str = 'manual_edit'
    ) -> ReceiptVersion:
        """
        Create a new version of a receipt with field-level audit logging.
        
        Args:
            receipt: The receipt to update
            new_data: Dictionary with new receipt data
            user: User making the change
            reason: Reason for the change
            source: Source of change ('manual_edit', 'upload', 'api')
            
        Returns:
            New ReceiptVersion instance
        """
        old_version = receipt.current_version
        
        if not old_version:
            # No existing version, create initial
            return VersionService.create_initial_version(receipt, new_data, user=user)
        
        # Compare and find changes
        changes = VersionService.compare_versions(old_version, new_data)
        
        if not changes:
            logger.info(f"No changes detected for receipt {receipt.receipt_number}")
            return old_version
        
        # Create new version
        new_version_number = old_version.version_number + 1
        
        new_version = ReceiptVersion.objects.create(
            receipt=receipt,
            version_number=new_version_number,
            student_name=new_data.get('student_name', old_version.student_name),
            class_name=new_data.get('class_name', old_version.class_name),
            payment_mode=new_data.get('payment_mode', old_version.payment_mode),
            date=new_data.get('date', old_version.date),
            annual_fee=new_data.get('annual_fee', old_version.annual_fee),
            tuition_fee=new_data.get('tuition_fee', old_version.tuition_fee),
            kit_books_fee=new_data.get('kit_books_fee', old_version.kit_books_fee),
            activity_fee=new_data.get('activity_fee', old_version.activity_fee),
            uniform_fee=new_data.get('uniform_fee', old_version.uniform_fee),
            source=source,
            changed_by=user
        )
        
        # Update receipt's current version
        receipt.current_version = new_version
        receipt.save(update_fields=['current_version', 'updated_at'])
        
        # Create audit logs for each changed field
        audit_logs = []
        for field_name, change in changes.items():
            audit_log = AuditLog.objects.create(
                receipt=receipt,
                version=new_version,
                field_name=field_name,
                old_value=change['old'],
                new_value=change['new'],
                changed_by=user,
                reason=reason
            )
            audit_logs.append(audit_log)
        
        logger.info(
            f"Created version {new_version_number} for receipt {receipt.receipt_number} "
            f"with {len(changes)} field changes"
        )
        
        return new_version
    
    @staticmethod
    def get_version_history(receipt: Receipt) -> List[Dict[str, Any]]:
        """
        Get complete version history for a receipt.
        
        Args:
            receipt: Receipt instance
            
        Returns:
            List of version dictionaries
        """
        versions = receipt.versions.all().select_related('changed_by')
        
        history = []
        for version in versions:
            version_data = {
                'id': str(version.id),
                'version_number': version.version_number,
                'student_name': version.student_name,
                'class_name': version.class_name,
                'payment_mode': version.payment_mode,
                'date': version.date.isoformat() if version.date else None,
                'annual_fee': str(version.annual_fee),
                'tuition_fee': str(version.tuition_fee),
                'kit_books_fee': str(version.kit_books_fee),
                'activity_fee': str(version.activity_fee),
                'uniform_fee': str(version.uniform_fee),
                'total_amount': str(version.total_amount),
                'source': version.source,
                'changed_by': version.changed_by.email if version.changed_by else None,
                'changed_at': version.changed_at.isoformat(),
            }
            history.append(version_data)
        
        return history
    
    @staticmethod
    def get_field_changes(receipt: Receipt) -> List[Dict[str, Any]]:
        """
        Get all field-level changes for a receipt.
        
        Args:
            receipt: Receipt instance
            
        Returns:
            List of change dictionaries
        """
        audit_logs = AuditLog.objects.filter(
            receipt=receipt
        ).select_related('version', 'changed_by').order_by('-changed_at')
        
        changes = []
        for log in audit_logs:
            change_data = {
                'id': str(log.id),
                'version_number': log.version.version_number,
                'field_name': log.field_name,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'changed_by': log.changed_by.email if log.changed_by else None,
                'changed_at': log.changed_at.isoformat(),
                'reason': log.reason,
            }
            changes.append(change_data)
        
        return changes
    
    @staticmethod
    def get_version_at_date(receipt: Receipt, date) -> Optional[ReceiptVersion]:
        """
        Get the version of a receipt that was active at a specific date.
        
        Args:
            receipt: Receipt instance
            date: Target date
            
        Returns:
            ReceiptVersion active at that date, or None
        """
        return receipt.versions.filter(
            changed_at__date__lte=date
        ).order_by('-version_number').first()