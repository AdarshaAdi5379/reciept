"""
DRF Views for Receipt API.
"""
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, parser_classes, action, permission_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from receipts.models import Receipt, ReceiptVersion, UploadBatch, AuditLog, ShareLink
from receipts.serializers import (
    ReceiptListSerializer,
    ReceiptDetailSerializer,
    ReceiptUpdateSerializer,
    ReceiptVersionSerializer,
    UploadBatchSerializer,
    UploadBatchDetailSerializer,
    AuditLogSerializer,
    ShareLinkSerializer,
    SearchQuerySerializer,
)
from receipts.services import (
    ReceiptService,
    VersionService,
    PDFService,
)

logger = logging.getLogger('receipts')


# Simple Django view for file upload (no DRF, no auth checks)
@csrf_exempt
def simple_upload_handler(request):
    """
    Simple upload handler that bypasses all DRF authentication/permission checks.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    file_obj = request.FILES.get('file')
    
    if not file_obj:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    # Validate file type
    if not file_obj.name.endswith(('.xlsx', '.xls')):
        return JsonResponse({'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'}, status=400)
    
    # Validate file size (5MB limit)
    if file_obj.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'File size exceeds 5MB limit'}, status=400)
    
    try:
        result = ReceiptService.process_excel_upload(
            file_object=file_obj,
            user=request.user if request.user.is_authenticated else None,
            file_name=file_obj.name
        )
        
        if result['success']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JsonResponse({'error': f'Upload failed: {str(e)}'}, status=500)


class ReceiptListView(APIView):
    """
    List and search receipts.
    
    GET /api/receipts/
    Query params:
    - query: General search (receipt_number or student_name)
    - student_name: Filter by student name
    - class_name: Filter by class
    - payment_mode: Filter by payment mode
    - date_from: Filter from date
    - date_to: Filter until date
    - status: Filter by status (active/voided)
    - page: Page number
    - page_size: Items per page
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Validate query parameters
        query_serializer = SearchQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                query_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get search parameters
        params = query_serializer.validated_data
        
        # Perform search
        result = ReceiptService.search_receipts(
            query=params.get('query'),
            student_name=params.get('student_name'),
            class_name=params.get('class_name'),
            payment_mode=params.get('payment_mode'),
            date_from=params.get('date_from'),
            date_to=params.get('date_to'),
            status=params.get('status'),
            page=params.get('page', 1),
            page_size=params.get('page_size', 50)
        )
        
        return Response(result)


class ReceiptDetailView(APIView):
    """
    Get, update, or void a specific receipt.
    
    GET /api/receipts/{receipt_number}/
    PUT /api/receipts/{receipt_number}/
    DELETE /api/receipts/{receipt_number}/ (void)
    """
    
    def get(self, request, receipt_number):
        receipt_data = ReceiptService.get_receipt_detail(receipt_number)
        
        if not receipt_data:
            return Response(
                {'error': f'Receipt {receipt_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(receipt_data)
    
    def put(self, request, receipt_number):
        serializer = ReceiptUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, result = ReceiptService.update_receipt(
            receipt_number=receipt_number,
            data=serializer.validated_data,
            user=request.user if request.user.is_authenticated else None,
            reason=serializer.validated_data.get('reason', '')
        )
        
        if success:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, receipt_number):
        success, result = ReceiptService.void_receipt(
            receipt_number=receipt_number,
            user=request.user if request.user.is_authenticated else None
        )
        
        if success:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class ReceiptVersionsView(APIView):
    """
    Get version history for a receipt.
    
    GET /api/receipts/{receipt_number}/versions/
    """
    
    def get(self, request, receipt_number):
        try:
            receipt = Receipt.objects.get(receipt_number=receipt_number)
        except Receipt.DoesNotExist:
            return Response(
                {'error': f'Receipt {receipt_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        versions = VersionService.get_version_history(receipt)
        return Response({'versions': versions})


class ReceiptAuditLogView(APIView):
    """
    Get field-level audit log for a receipt.
    
    GET /api/receipts/{receipt_number}/audit/
    """
    
    def get(self, request, receipt_number):
        try:
            receipt = Receipt.objects.get(receipt_number=receipt_number)
        except Receipt.DoesNotExist:
            return Response(
                {'error': f'Receipt {receipt_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        changes = VersionService.get_field_changes(receipt)
        return Response({'changes': changes})


class ReceiptPDFView(APIView):
    """
    Download receipt as PDF.
    
    GET /api/receipts/{receipt_number}/pdf/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, receipt_number):
        try:
            receipt = Receipt.objects.select_related('current_version').get(
                receipt_number=receipt_number
            )
        except Receipt.DoesNotExist:
            return Response(
                {'error': f'Receipt {receipt_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            pdf_content = PDFService.generate_receipt_pdf(receipt)
            
            response = HttpResponse(
                pdf_content,
                content_type='application/pdf'
            )
            response['Content-Disposition'] = (
                f'attachment; filename="receipt_{receipt_number}.pdf"'
            )
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {str(e)}")
            return Response(
                {'error': 'Failed to generate PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReceiptShareView(APIView):
    """
    Generate share link for a receipt.
    
    POST /api/receipts/{receipt_number}/share/
    Body: {
        "expiry_hours": 72,  // optional
        "max_access": 5      // optional
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request, receipt_number):
        try:
            receipt = Receipt.objects.get(receipt_number=receipt_number)
        except Receipt.DoesNotExist:
            return Response(
                {'error': f'Receipt {receipt_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        expiry_hours = request.data.get('expiry_hours', 72)
        max_access = request.data.get('max_access', 5)
        
        share_link = PDFService.generate_share_link(
            receipt=receipt,
            expiry_hours=expiry_hours,
            max_access=max_access
        )
        
        serializer = ShareLinkSerializer(share_link)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SharedReceiptPDFView(APIView):
    """
    Download receipt PDF via share link.
    
    GET /api/receipts/share/{token}/pdf/
    """
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        receipt = PDFService.validate_share_link(token)
        
        if not receipt:
            return Response(
                {'error': 'Invalid or expired share link'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            pdf_content = PDFService.generate_receipt_pdf(receipt)
            
            response = HttpResponse(
                pdf_content,
                content_type='application/pdf'
            )
            response['Content-Disposition'] = (
                f'attachment; filename="receipt_{receipt.receipt_number}.pdf"'
            )
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate shared PDF: {str(e)}")
            return Response(
                {'error': 'Failed to generate PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
def upload_excel_view(request):
    """
    Upload Excel file with receipts.
    
    POST /api/receipts/upload/
    Body: multipart/form-data with 'file' field
    """
    if request.method != 'POST':
        return Response(
            {'error': 'Only POST requests are allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    file_obj = request.FILES.get('file')
    
    if not file_obj:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file type
    if not file_obj.name.endswith(('.xlsx', '.xls')):
        return Response(
            {'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size (5MB limit)
    if file_obj.size > 5 * 1024 * 1024:
        return Response(
            {'error': 'File size exceeds 5MB limit'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    result = ReceiptService.process_excel_upload(
        file_object=file_obj,
        user=request.user if request.user.is_authenticated else None,
        file_name=file_obj.name
    )
    
    if result['success']:
        return JsonResponse(result, status=200)
    else:
        return JsonResponse(result, status=400)



# Keep the old class for reference but don't use it
@method_decorator(csrf_exempt, name='dispatch')
class UploadExcelView(APIView):
    """
    DEPRECATED - Use upload_excel_view function instead.
    Upload Excel file with receipts.
    
    POST /api/receipts/upload/
    Body: multipart/form-data with 'file' field
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [AllowAny]
    
    def post(self, request):
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        if not file_obj.name.endswith(('.xlsx', '.xls')):
            return Response(
                {'error': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (5MB limit)
        if file_obj.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'File size exceeds 5MB limit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = ReceiptService.process_excel_upload(
            file_object=file_obj,
            user=request.user if request.user.is_authenticated else None,
            file_name=file_obj.name
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


class UploadBatchListView(APIView):
    """
    List upload batch history.
    
    GET /api/receipts/batches/
    Query params:
    - page: Page number
    - page_size: Items per page
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        result = ReceiptService.get_upload_history(
            page=page,
            page_size=page_size
        )
        
        return Response(result)


class UploadBatchDetailView(APIView):
    """
    Get details of a specific upload batch.
    
    GET /api/receipts/batches/{batch_id}/
    """
    
    def get(self, request, batch_id):
        try:
            batch = UploadBatch.objects.get(id=batch_id)
            serializer = UploadBatchDetailSerializer(batch)
            return Response(serializer.data)
        except UploadBatch.DoesNotExist:
            return Response(
                {'error': 'Batch not found'},
                status=status.HTTP_404_NOT_FOUND
            )


@csrf_exempt
def stats_handler(request):
    """
    Simple stats endpoint without DRF overhead.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Total receipts count
        total_receipts = Receipt.objects.filter(status='active').count()
        
        # Return simple stats
        return JsonResponse({
            'total_receipts': total_receipts,
            'total_amount': '0.00',
            'by_payment_mode': [],
            'by_class': [],
            'recent_uploads': [],
        }, status=200)
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return JsonResponse({
            'total_receipts': 0,
            'total_amount': '0.00',
            'by_payment_mode': [],
            'by_class': [],
            'recent_uploads': [],
            'error': str(e)
        }, status=200)


