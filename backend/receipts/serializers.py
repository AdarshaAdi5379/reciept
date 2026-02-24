"""
DRF Serializers for Receipt API.
"""
from decimal import Decimal
from datetime import datetime
from rest_framework import serializers
from receipts.models import Receipt, ReceiptVersion, UploadBatch, AuditLog, ShareLink


class ReceiptVersionSerializer(serializers.ModelSerializer):
    """Serializer for receipt versions."""
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    date = serializers.DateField()
    changed_at = serializers.DateTimeField(read_only=True)
    changed_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ReceiptVersion
        fields = [
            'id',
            'version_number',
            'student_name',
            'class_name',
            'payment_mode',
            'date',
            'annual_fee',
            'tuition_fee',
            'kit_books_fee',
            'activity_fee',
            'uniform_fee',
            'total_amount',
            'source',
            'changed_by',
            'changed_at',
        ]
        read_only_fields = ['id', 'version_number', 'source', 'changed_by', 'changed_at']


class ReceiptListSerializer(serializers.ModelSerializer):
    """Serializer for receipt list view."""
    student_name = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    date = serializers.DateField(read_only=True)
    payment_mode = serializers.CharField(read_only=True)
    class_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'receipt_number',
            'student_name',
            'class_name',
            'payment_mode',
            'date',
            'total_amount',
            'status',
            'created_at',
            'updated_at',
        ]


class ReceiptDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed receipt view."""
    version_number = serializers.IntegerField(read_only=True)
    student_name = serializers.CharField(read_only=True)
    class_name = serializers.CharField(read_only=True)
    payment_mode = serializers.CharField(read_only=True)
    date = serializers.DateField(read_only=True)
    annual_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    tuition_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    kit_books_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    activity_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    uniform_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Receipt
        fields = [
            'id',
            'receipt_number',
            'status',
            'student_name',
            'class_name',
            'payment_mode',
            'date',
            'annual_fee',
            'tuition_fee',
            'kit_books_fee',
            'activity_fee',
            'uniform_fee',
            'total_amount',
            'version_number',
            'created_at',
            'updated_at',
        ]


class ReceiptUpdateSerializer(serializers.Serializer):
    """Serializer for receipt updates."""
    student_name = serializers.CharField(max_length=200, required=False)
    class_name = serializers.CharField(max_length=100, required=False)
    payment_mode = serializers.ChoiceField(
        choices=['cash', 'cheque', 'bank_transfer', 'upi', 'card', 'other'],
        required=False
    )
    date = serializers.DateField(required=False)
    annual_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    tuition_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    kit_books_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    activity_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    uniform_fee = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for the change"
    )
    
    def validate(self, data):
        """Ensure at least one field is being updated."""
        updateable_fields = [
            'student_name', 'class_name', 'payment_mode', 'date',
            'annual_fee', 'tuition_fee', 'kit_books_fee',
            'activity_fee', 'uniform_fee'
        ]
        
        has_changes = any(
            field in data and data[field] is not None
            for field in updateable_fields
        )
        
        if not has_changes:
            raise serializers.ValidationError(
                "At least one field must be provided for update"
            )
        
        return data


class UploadBatchSerializer(serializers.ModelSerializer):
    """Serializer for upload batch history."""
    uploaded_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UploadBatch
        fields = [
            'id',
            'file_name',
            'uploaded_by',
            'uploaded_at',
            'records_inserted',
            'records_updated',
            'records_failed',
            'status',
        ]


class UploadBatchDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for upload batch."""
    uploaded_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UploadBatch
        fields = [
            'id',
            'file_name',
            'uploaded_by',
            'uploaded_at',
            'records_inserted',
            'records_updated',
            'records_failed',
            'status',
            'error_log',
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""
    version_number = serializers.IntegerField(source='version.version_number', read_only=True)
    changed_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'version_number',
            'field_name',
            'old_value',
            'new_value',
            'changed_by',
            'changed_at',
            'reason',
        ]


class ShareLinkSerializer(serializers.ModelSerializer):
    """Serializer for share links."""
    receipt_number = serializers.CharField(source='receipt.receipt_number', read_only=True)
    share_url = serializers.SerializerMethodField()
    whatsapp_url = serializers.SerializerMethodField()
    email_link = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ShareLink
        fields = [
            'id',
            'receipt_number',
            'token',
            'share_url',
            'whatsapp_url',
            'email_link',
            'created_at',
            'expires_at',
            'access_count',
            'max_access',
            'is_valid',
        ]
        read_only_fields = ['token', 'created_at', 'expires_at', 'access_count']
    
    def get_share_url(self, obj):
        from receipts.services import PDFService
        return PDFService.get_share_url(obj)
    
    def get_whatsapp_url(self, obj):
        from receipts.services import PDFService
        return PDFService.get_whatsapp_share_url(obj)
    
    def get_email_link(self, obj):
        from receipts.services import PDFService
        email_data = PDFService.get_email_share_data(obj)
        return email_data.get('mailto_link')


class UploadResponseSerializer(serializers.Serializer):
    """Serializer for upload response."""
    success = serializers.BooleanField()
    batch_id = serializers.UUIDField()
    inserted = serializers.IntegerField()
    updated = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    total_rows = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)
    details = serializers.DictField(required=False)


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search query parameters."""
    query = serializers.CharField(required=False, allow_blank=True)
    student_name = serializers.CharField(required=False, allow_blank=True)
    class_name = serializers.CharField(required=False, allow_blank=True)
    payment_mode = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False, allow_null=True)
    date_to = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['active', 'voided'],
        required=False,
        allow_null=True
    )
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=50)