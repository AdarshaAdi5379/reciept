"""
Receipt Models - Enterprise Grade with Versioning
"""
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

User = get_user_model()


class UploadBatch(models.Model):
    """Tracks Excel upload batches for audit purposes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='upload_batches'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    records_inserted = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success'),
        ],
        default='pending'
    )
    error_log = models.JSONField(default=list, blank=True)
    file_path = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'upload_batches'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Batch {self.file_name} ({self.status})"


class Receipt(models.Model):
    """
    Master receipt record.
    Always points to the latest version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_number = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique receipt identifier"
    )
    current_version = models.ForeignKey(
        'ReceiptVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_receipts'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('voided', 'Voided'),
        ],
        default='active',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'receipts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def get_latest_version(self):
        """Get the most recent version of this receipt."""
        return self.versions.order_by('-version_number').first()

    @property
    def student_name(self):
        """Get student name from current version."""
        return self.current_version.student_name if self.current_version else None

    @property
    def total_amount(self):
        """Get total amount from current version."""
        return self.current_version.total_amount if self.current_version else None


class ReceiptVersion(models.Model):
    """
    Immutable receipt version history.
    Every change creates a new version - never update existing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.PositiveIntegerField(
        help_text="Sequential version number (1, 2, 3...)"
    )

    # Receipt Data Fields
    student_name = models.CharField(max_length=200, db_index=True)
    class_name = models.CharField(max_length=100, db_index=True)
    payment_mode = models.CharField(
        max_length=50,
        choices=[
            ('cash', 'Cash'),
            ('cheque', 'Cheque'),
            ('bank_transfer', 'Bank Transfer'),
            ('upi', 'UPI'),
            ('card', 'Card'),
            ('other', 'Other'),
        ],
        db_index=True
    )
    date = models.DateField(db_index=True)

    # Fee Breakdown
    annual_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    kit_books_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    activity_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    uniform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Source tracking
    source = models.CharField(
        max_length=20,
        choices=[
            ('upload', 'Excel Upload'),
            ('manual_edit', 'Manual Edit'),
            ('api', 'API'),
        ],
        default='upload'
    )
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receipt_versions'
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'receipt_versions'
        ordering = ['-version_number']
        unique_together = ['receipt', 'version_number']
        indexes = [
            models.Index(fields=['receipt', 'version_number']),
            models.Index(fields=['student_name']),
            models.Index(fields=['class_name']),
            models.Index(fields=['date']),
            models.Index(fields=['payment_mode']),
            models.Index(fields=['changed_at']),
        ]

    def __str__(self):
        return f"{self.receipt.receipt_number} v{self.version_number}"

    @property
    def total_amount(self):
        """Calculate total from all fee components."""
        return (
            self.annual_fee +
            self.tuition_fee +
            self.kit_books_fee +
            self.activity_fee +
            self.uniform_fee
        )

    def get_field_values(self):
        """Return dict of all field values for comparison."""
        return {
            'student_name': self.student_name,
            'class_name': self.class_name,
            'payment_mode': self.payment_mode,
            'date': self.date.isoformat() if self.date else None,
            'annual_fee': str(self.annual_fee),
            'tuition_fee': str(self.tuition_fee),
            'kit_books_fee': str(self.kit_books_fee),
            'activity_fee': str(self.activity_fee),
            'uniform_fee': str(self.uniform_fee),
        }


class AuditLog(models.Model):
    """
    Field-level audit logging for manual edits.
    Tracks exactly what changed and when.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    version = models.ForeignKey(
        ReceiptVersion,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reason = models.TextField(blank=True, help_text="Reason for the change")

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['receipt', 'changed_at']),
            models.Index(fields=['field_name']),
            models.Index(fields=['changed_at']),
        ]

    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.field_name} changed"


class ShareLink(models.Model):
    """
    Secure signed URLs for sharing receipts.
    Links expire after a set time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='share_links'
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    access_count = models.PositiveIntegerField(default=0)
    max_access = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'share_links'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Share link for {self.receipt.receipt_number}"

    def is_valid(self):
        """Check if link is still valid."""
        from django.utils import timezone
        return (
            self.is_active and
            self.expires_at > timezone.now() and
            self.access_count < self.max_access
        )
