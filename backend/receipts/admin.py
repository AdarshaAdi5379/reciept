"""
Admin configuration for Receipt models.
"""
from django.contrib import admin
from django.utils.html import format_html
from receipts.models import Receipt, ReceiptVersion, UploadBatch, AuditLog, ShareLink


class ReceiptVersionInline(admin.TabularInline):
    """Inline admin for receipt versions."""
    model = ReceiptVersion
    extra = 0
    readonly_fields = [
        'version_number', 'student_name', 'class_name', 'payment_mode',
        'date', 'annual_fee', 'tuition_fee', 'kit_books_fee',
        'activity_fee', 'uniform_fee', 'source', 'changed_by', 'changed_at'
    ]
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


class AuditLogInline(admin.TabularInline):
    """Inline admin for audit logs."""
    model = AuditLog
    extra = 0
    readonly_fields = [
        'version', 'field_name', 'old_value', 'new_value',
        'changed_by', 'changed_at', 'reason'
    ]
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin for Receipt model."""
    list_display = [
        'receipt_number', 'student_name_display', 'class_name_display',
        'total_amount_display', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['receipt_number', 'current_version__student_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ReceiptVersionInline, AuditLogInline]
    
    def student_name_display(self, obj):
        return obj.student_name or '-'
    student_name_display.short_description = 'Student Name'
    student_name_display.admin_order_field = 'current_version__student_name'
    
    def class_name_display(self, obj):
        version = obj.current_version
        return version.class_name if version else '-'
    class_name_display.short_description = 'Class'
    
    def total_amount_display(self, obj):
        version = obj.current_version
        if version:
            return f'₹{version.total_amount:,.2f}'
        return '-'
    total_amount_display.short_description = 'Total Amount'
    
    def status_badge(self, obj):
        if obj.status == 'active':
            return format_html(
                '<span style="background: #dcfce7; color: #166534; '
                'padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background: #fee2e2; color: #991b1b; '
            'padding: 3px 10px; border-radius: 3px;">Voided</span>'
        )
    status_badge.short_description = 'Status'


@admin.register(ReceiptVersion)
class ReceiptVersionAdmin(admin.ModelAdmin):
    """Admin for ReceiptVersion model."""
    list_display = [
        'receipt_number', 'version_number', 'student_name',
        'class_name', 'total_amount_display', 'source', 'changed_at'
    ]
    list_filter = ['source', 'payment_mode', 'changed_at']
    search_fields = ['receipt__receipt_number', 'student_name']
    readonly_fields = [
        'id', 'receipt', 'version_number', 'student_name', 'class_name',
        'payment_mode', 'date', 'annual_fee', 'tuition_fee', 'kit_books_fee',
        'activity_fee', 'uniform_fee', 'source', 'batch', 'changed_by', 'changed_at'
    ]
    
    def receipt_number(self, obj):
        return obj.receipt.receipt_number
    receipt_number.short_description = 'Receipt No.'
    
    def total_amount_display(self, obj):
        return f'₹{obj.total_amount:,.2f}'
    total_amount_display.short_description = 'Total Amount'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    """Admin for UploadBatch model."""
    list_display = [
        'file_name', 'uploaded_by', 'uploaded_at', 'records_inserted',
        'records_updated', 'records_failed', 'status_badge'
    ]
    list_filter = ['status', 'uploaded_at']
    search_fields = ['file_name', 'uploaded_by__email']
    readonly_fields = [
        'id', 'file_name', 'uploaded_by', 'uploaded_at',
        'records_inserted', 'records_updated', 'records_failed',
        'status', 'error_log', 'file_path'
    ]
    
    def status_badge(self, obj):
        colors = {
            'success': ('#dcfce7', '#166534'),
            'failed': ('#fee2e2', '#991b1b'),
            'partial': ('#fef3c7', '#92400e'),
            'processing': ('#dbeafe', '#1e40af'),
            'pending': ('#f1f5f9', '#475569'),
        }
        bg, fg = colors.get(obj.status, ('#f1f5f9', '#475569'))
        return format_html(
            '<span style="background: {}; color: {}; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            bg, fg, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin for AuditLog model."""
    list_display = [
        'receipt_number', 'version_number', 'field_name',
        'old_value_truncated', 'new_value_truncated', 'changed_by', 'changed_at'
    ]
    list_filter = ['field_name', 'changed_at']
    search_fields = ['receipt__receipt_number', 'field_name']
    readonly_fields = [
        'id', 'receipt', 'version', 'field_name', 'old_value',
        'new_value', 'changed_by', 'changed_at', 'reason'
    ]
    
    def receipt_number(self, obj):
        return obj.receipt.receipt_number
    receipt_number.short_description = 'Receipt No.'
    
    def version_number(self, obj):
        return obj.version.version_number
    version_number.short_description = 'Version'
    
    def old_value_truncated(self, obj):
        if len(obj.old_value) > 30:
            return obj.old_value[:30] + '...'
        return obj.old_value
    old_value_truncated.short_description = 'Old Value'
    
    def new_value_truncated(self, obj):
        if len(obj.new_value) > 30:
            return obj.new_value[:30] + '...'
        return obj.new_value
    new_value_truncated.short_description = 'New Value'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    """Admin for ShareLink model."""
    list_display = [
        'receipt_number', 'token_truncated', 'created_at',
        'expires_at', 'access_count', 'is_valid_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['receipt__receipt_number', 'token']
    readonly_fields = [
        'id', 'receipt', 'token', 'created_at', 'expires_at',
        'access_count', 'max_access', 'is_active'
    ]
    
    def receipt_number(self, obj):
        return obj.receipt.receipt_number
    receipt_number.short_description = 'Receipt No.'
    
    def token_truncated(self, obj):
        return obj.token[:20] + '...'
    token_truncated.short_description = 'Token'
    
    def is_valid_display(self, obj):
        if obj.is_valid():
            return format_html(
                '<span style="color: #166534;">Valid</span>'
            )
        return format_html(
            '<span style="color: #991b1b;">Expired/Invalid</span>'
        )
    is_valid_display.short_description = 'Status'