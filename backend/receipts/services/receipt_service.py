"""
Receipt Service - Core business logic for receipt operations.
"""
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from receipts.models import Receipt, ReceiptVersion, UploadBatch
from .excel_parser import ExcelParserService
from .version_service import VersionService

User = get_user_model()
logger = logging.getLogger('receipts')


class ReceiptService:
    """
    Service for receipt operations.
    
    Handles:
    - Excel upload with batch tracking
    - Duplicate detection and update
    - Receipt search and filtering
    - Share link generation
    """
    
    @staticmethod
    @transaction.atomic
    def process_excel_upload(
        file_object,
        user: User = None,
        file_name: str = 'upload.xlsx'
    ) -> Dict[str, Any]:
        """
        Process an Excel file upload.
        
        Creates/updates receipts with versioning.
        All operations are atomic - no partial writes.
        
        Args:
            file_object: Django UploadedFile
            user: User performing the upload
            file_name: Original file name
            
        Returns:
            Dictionary with upload results
        """
        # Create batch record
        batch = UploadBatch.objects.create(
            file_name=file_name,
            uploaded_by=user,
            status='processing'
        )
        
        try:
            # Parse Excel file
            parser = ExcelParserService(file_object=file_object)
            success, parsed_rows, summary = parser.parse()
            parser.close()
            
            if not success:
                batch.status = 'failed'
                batch.error_log = [summary]
                batch.save()
                return {
                    'success': False,
                    'batch_id': str(batch.id),
                    'error': summary.get('error', 'Failed to parse Excel file'),
                    'details': summary
                }
            
            # Process each row
            inserted = 0
            updated = 0
            failed = 0
            errors = []
            
            for row_data in parsed_rows:
                try:
                    receipt_number = row_data['receipt_number']
                    
                    # Check if receipt exists
                    receipt = Receipt.objects.filter(
                        receipt_number=receipt_number
                    ).first()
                    
                    if receipt:
                        # Update existing receipt
                        old_version = receipt.current_version
                        if old_version:
                            # Check if there are actual changes
                            changes = VersionService.compare_versions(old_version, row_data)
                            if changes:
                                VersionService.create_new_version(
                                    receipt=receipt,
                                    new_data=row_data,
                                    user=user,
                                    source='upload'
                                )
                                updated += 1
                            else:
                                # No changes, skip
                                pass
                        else:
                            # Receipt without version (shouldn't happen)
                            VersionService.create_initial_version(
                                receipt=receipt,
                                data=row_data,
                                batch=batch,
                                user=user
                            )
                            updated += 1
                    else:
                        # Create new receipt
                        receipt = Receipt.objects.create(
                            receipt_number=receipt_number
                        )
                        VersionService.create_initial_version(
                            receipt=receipt,
                            data=row_data,
                            batch=batch,
                            user=user
                        )
                        inserted += 1
                        
                except Exception as e:
                    failed += 1
                    errors.append({
                        'receipt_number': row_data.get('receipt_number', 'Unknown'),
                        'error': str(e)
                    })
                    logger.error(f"Error processing row: {str(e)}")
            
            # Update batch status
            batch.records_inserted = inserted
            batch.records_updated = updated
            batch.records_failed = failed
            batch.error_log = errors
            
            if failed == 0:
                batch.status = 'success'
            elif inserted > 0 or updated > 0:
                batch.status = 'partial'
            else:
                batch.status = 'failed'
            
            batch.save()
            
            logger.info(
                f"Excel upload complete: {inserted} inserted, {updated} updated, {failed} failed"
            )
            
            return {
                'success': True,
                'batch_id': str(batch.id),
                'inserted': inserted,
                'updated': updated,
                'failed': failed,
                'errors': errors[:50],  # Limit errors
                'total_rows': len(parsed_rows)
            }
            
        except Exception as e:
            logger.exception(f"Excel upload failed: {str(e)}")
            batch.status = 'failed'
            batch.error_log = [{'error': str(e)}]
            batch.save()
            
            return {
                'success': False,
                'batch_id': str(batch.id),
                'error': str(e)
            }
    
    @staticmethod
    def search_receipts(
        query: str = None,
        student_name: str = None,
        class_name: str = None,
        payment_mode: str = None,
        date_from: str = None,
        date_to: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Search receipts with filters.
        
        Args:
            query: General search query (receipt_number or student_name)
            student_name: Filter by student name (partial match)
            class_name: Filter by class
            payment_mode: Filter by payment mode
            date_from: Filter receipts from this date
            date_to: Filter receipts until this date
            status: Filter by status (active/voided)
            page: Page number
            page_size: Items per page
            
        Returns:
            Dictionary with results and pagination info
        """
        from django.db.models import Q
        
        # Start with all active receipts
        queryset = Receipt.objects.filter(
            status__in=['active', 'voided']
        ).select_related('current_version')
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(receipt_number__icontains=query) |
                Q(current_version__student_name__icontains=query)
            )
        
        if student_name:
            queryset = queryset.filter(
                current_version__student_name__icontains=student_name
            )
        
        if class_name:
            queryset = queryset.filter(
                current_version__class_name__icontains=class_name
            )
        
        if payment_mode:
            queryset = queryset.filter(
                current_version__payment_mode=payment_mode
            )
        
        if date_from:
            queryset = queryset.filter(
                current_version__date__gte=date_from
            )
        
        if date_to:
            queryset = queryset.filter(
                current_version__date__lte=date_to
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        # Order by most recent
        queryset = queryset.order_by('-created_at')
        
        # Paginate
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        receipts = queryset[offset:offset + page_size]
        
        # Serialize results
        results = []
        for receipt in receipts:
            version = receipt.current_version
            if version:
                results.append({
                    'id': str(receipt.id),
                    'receipt_number': receipt.receipt_number,
                    'student_name': version.student_name,
                    'class_name': version.class_name,
                    'payment_mode': version.payment_mode,
                    'date': version.date.isoformat() if version.date else None,
                    'total_amount': str(version.total_amount),
                    'status': receipt.status,
                    'created_at': receipt.created_at.isoformat(),
                    'updated_at': receipt.updated_at.isoformat(),
                })
        
        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
            }
        }
    
    @staticmethod
    def get_receipt_detail(receipt_number: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed receipt information.
        
        Args:
            receipt_number: Receipt number to look up
            
        Returns:
            Receipt detail dictionary or None
        """
        try:
            receipt = Receipt.objects.select_related(
                'current_version'
            ).prefetch_related(
                'versions'
            ).get(receipt_number=receipt_number)
            
            version = receipt.current_version
            
            if not version:
                return None
            
            return {
                'id': str(receipt.id),
                'receipt_number': receipt.receipt_number,
                'status': receipt.status,
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
                'version_number': version.version_number,
                'created_at': receipt.created_at.isoformat(),
                'updated_at': receipt.updated_at.isoformat(),
            }
            
        except Receipt.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def update_receipt(
        receipt_number: str,
        data: Dict[str, Any],
        user: User = None,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Update a receipt with versioning.
        
        Args:
            receipt_number: Receipt to update
            data: New data dictionary
            user: User making the change
            reason: Reason for the change
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            receipt = Receipt.objects.get(receipt_number=receipt_number)
            
            if receipt.status == 'voided':
                return False, {'error': 'Cannot update a voided receipt'}
            
            new_version = VersionService.create_new_version(
                receipt=receipt,
                new_data=data,
                user=user,
                reason=reason,
                source='manual_edit'
            )
            
            return True, {
                'receipt_number': receipt_number,
                'version_number': new_version.version_number,
                'message': 'Receipt updated successfully'
            }
            
        except Receipt.DoesNotExist:
            return False, {'error': f'Receipt {receipt_number} not found'}
    
    @staticmethod
    @transaction.atomic
    def void_receipt(
        receipt_number: str,
        user: User = None,
        reason: str = ''
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Void a receipt (soft delete).
        
        Args:
            receipt_number: Receipt to void
            user: User performing the action
            reason: Reason for voiding
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            receipt = Receipt.objects.get(receipt_number=receipt_number)
            
            if receipt.status == 'voided':
                return False, {'error': 'Receipt is already voided'}
            
            receipt.status = 'voided'
            receipt.save(update_fields=['status', 'updated_at'])
            
            logger.info(f"Receipt {receipt_number} voided by {user}")
            
            return True, {
                'receipt_number': receipt_number,
                'status': 'voided',
                'message': 'Receipt voided successfully'
            }
            
        except Receipt.DoesNotExist:
            return False, {'error': f'Receipt {receipt_number} not found'}
    
    @staticmethod
    def get_upload_history(
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get upload batch history.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Dictionary with batch history
        """
        queryset = UploadBatch.objects.all().select_related('uploaded_by')
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        batches = queryset[offset:offset + page_size]
        
        results = []
        for batch in batches:
            results.append({
                'id': str(batch.id),
                'file_name': batch.file_name,
                'uploaded_by': batch.uploaded_by.email if batch.uploaded_by else None,
                'uploaded_at': batch.uploaded_at.isoformat(),
                'records_inserted': batch.records_inserted,
                'records_updated': batch.records_updated,
                'records_failed': batch.records_failed,
                'status': batch.status,
            })
        
        return {
            'results': results,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
            }
        }