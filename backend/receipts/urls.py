"""
URL configuration for Receipt API.
"""
from django.urls import path
from receipts import views
from receipts.views import simple_upload_handler, stats_handler

app_name = 'receipts'

urlpatterns = [
    # Simple upload (no DRF, no auth)
    path('upload/', simple_upload_handler, name='simple-upload'),
    
    # Stats endpoint
    path('stats/', stats_handler, name='stats'),
    
    # Receipt CRUD
    path('', views.ReceiptListView.as_view(), name='receipt-list'),
    path('<str:receipt_number>/', views.ReceiptDetailView.as_view(), name='receipt-detail'),
    path('<str:receipt_number>/versions/', views.ReceiptVersionsView.as_view(), name='receipt-versions'),
    path('<str:receipt_number>/audit/', views.ReceiptAuditLogView.as_view(), name='receipt-audit'),
    
    # PDF and Share
    path('<str:receipt_number>/pdf/', views.ReceiptPDFView.as_view(), name='receipt-pdf'),
    path('<str:receipt_number>/share/', views.ReceiptShareView.as_view(), name='receipt-share'),
    
    # Shared receipt access
    path('share/<str:token>/pdf/', views.SharedReceiptPDFView.as_view(), name='shared-pdf'),
    
    # Batch history
    path('batches/', views.UploadBatchListView.as_view(), name='batch-list'),
    path('batches/<uuid:batch_id>/', views.UploadBatchDetailView.as_view(), name='batch-detail'),
]