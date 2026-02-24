"""
PDF Service - Generates PDF receipts using WeasyPrint.
"""
import logging
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from weasyprint import HTML, CSS

from receipts.models import Receipt, ShareLink
from receipts.services.number_utils import NumberToWords

logger = logging.getLogger('receipts')


class PDFService:
    """
    Service for generating PDF receipts.
    
    Uses WeasyPrint to convert HTML templates to PDF.
    Templates are designed for both screen and print.
    """
    
    @staticmethod
    def generate_receipt_pdf(receipt: Receipt) -> bytes:
        """
        Generate PDF for a receipt (Professional Layout).
        
        Args:
            receipt: Receipt instance with current_version
            
        Returns:
            PDF content as bytes
        """
        version = receipt.current_version
        
        if not version:
            raise ValueError(f"No version found for receipt {receipt.receipt_number}")
        
        # Calculate total from all fee components
        total_amount = (
            (version.annual_fee or Decimal('0')) +
            (version.tuition_fee or Decimal('0')) +
            (version.kit_books_fee or Decimal('0')) +
            (version.activity_fee or Decimal('0')) +
            (version.uniform_fee or Decimal('0'))
        )
        
        # Split total into rupees and paise
        total_rupees = int(total_amount)
        total_paise = int(round((total_amount - total_rupees) * 100))
        
        # Build fee items dynamically from version data
        fee_items = []
        fees = [
            ('Annual Fee', version.annual_fee or Decimal('0')),
            ('Tuition Fee', version.tuition_fee or Decimal('0')),
            ('Kit & Books', version.kit_books_fee or Decimal('0')),
            ('Uniforms', version.uniform_fee or Decimal('0')),
            ('Activity fee', version.activity_fee or Decimal('0')),
        ]
        
        sl_no = 1
        for label, amount in fees:
            rupees = int(amount)
            paise = int(round((amount - rupees) * 100))
            fee_items.append({
                'sl': sl_no,
                'label': label,
                'amount': amount,
                'rupees': rupees,
                'paise': paise,
            })
            if amount > 0:
                sl_no += 1
        
        # Convert amount to words
        amount_in_words = NumberToWords.to_words(float(total_amount))
        
        # Prepare context for template
        context = {
            'receipt': receipt,
            'version': version,
            'total_amount': total_amount,
            'total_rupees': total_rupees,
            'total_paise': total_paise,
            'amount_in_words': amount_in_words,
            'fee_items': fee_items,
            'show_zero_fees': False,  # Hide zero-value fees
            'generated_at': timezone.now(),
            'institution_name': getattr(settings, 'INSTITUTION_NAME', 'Educational Institution'),
            'institution_address': getattr(settings, 'INSTITUTION_ADDRESS', ''),
            'institution_phone': getattr(settings, 'INSTITUTION_PHONE', ''),
            'institution_email': getattr(settings, 'INSTITUTION_EMAIL', ''),
        }
        
        # Render professional HTML template
        html_content = render_to_string('receipts/receipt_professional.html', context)
        
        # Generate PDF with print CSS
        try:
            pdf_file = HTML(string=html_content).write_pdf()
            logger.info(f"Generated professional PDF for receipt {receipt.receipt_number}")
            return pdf_file
        except Exception as e:
            logger.error(f"PDF generation error for {receipt.receipt_number}: {str(e)}")
            raise
    
    
    @staticmethod
    def get_print_css() -> str:
        """
        Get CSS for PDF generation and printing.
        
        Returns:
            CSS string
        """
        return """
            @page {
                size: A4;
                margin: 1.5cm;
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12pt;
                line-height: 1.5;
                color: #1a1a1a;
                margin: 0;
                padding: 0;
            }
            
            .receipt-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                text-align: center;
                border-bottom: 3px double #2563eb;
                padding-bottom: 15px;
                margin-bottom: 20px;
            }
            
            .institution-name {
                font-size: 24pt;
                font-weight: bold;
                color: #1e40af;
                margin: 0;
            }
            
            .institution-address {
                font-size: 10pt;
                color: #64748b;
                margin: 5px 0;
            }
            
            .receipt-title {
                font-size: 18pt;
                font-weight: bold;
                text-align: center;
                color: #1e40af;
                margin: 20px 0;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            .receipt-meta {
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
                padding: 10px;
                background: #f8fafc;
                border-radius: 5px;
            }
            
            .meta-item {
                text-align: left;
            }
            
            .meta-label {
                font-size: 9pt;
                color: #64748b;
                text-transform: uppercase;
            }
            
            .meta-value {
                font-size: 12pt;
                font-weight: 600;
                color: #1a1a1a;
            }
            
            .student-info {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
            }
            
            .student-name {
                font-size: 16pt;
                font-weight: bold;
                color: #1e40af;
                margin-bottom: 5px;
            }
            
            .student-class {
                font-size: 12pt;
                color: #475569;
            }
            
            .fee-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            
            .fee-table th,
            .fee-table td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .fee-table th {
                background: #1e40af;
                color: white;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 10pt;
            }
            
            .fee-table tr:nth-child(even) {
                background: #f8fafc;
            }
            
            .fee-table .amount {
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            
            .total-row {
                background: #1e40af !important;
                color: white;
                font-weight: bold;
                font-size: 14pt;
            }
            
            .total-row td {
                border-bottom: none;
            }
            
            .payment-info {
                margin: 20px 0;
                padding: 15px;
                background: #f0fdf4;
                border-left: 4px solid #22c55e;
                border-radius: 0 5px 5px 0;
            }
            
            .payment-mode {
                font-weight: 600;
                color: #166534;
            }
            
            .footer {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                text-align: center;
            }
            
            .signature-section {
                display: flex;
                justify-content: space-between;
                margin-top: 50px;
            }
            
            .signature-box {
                text-align: center;
                width: 200px;
            }
            
            .signature-line {
                border-top: 1px solid #1a1a1a;
                margin-top: 50px;
                padding-top: 5px;
            }
            
            .terms {
                font-size: 9pt;
                color: #64748b;
                margin-top: 30px;
                padding: 10px;
                background: #f8fafc;
                border-radius: 5px;
            }
            
            .terms-title {
                font-weight: 600;
                margin-bottom: 5px;
            }
            
            .watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 60pt;
                color: rgba(30, 64, 175, 0.1);
                font-weight: bold;
                pointer-events: none;
                z-index: -1;
            }
            
            .status-badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 10pt;
                font-weight: 600;
            }
            
            .status-active {
                background: #dcfce7;
                color: #166534;
            }
            
            .status-voided {
                background: #fee2e2;
                color: #991b1b;
            }
            
            @media print {
                body {
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }
                
                .no-print {
                    display: none !important;
                }
            }
        """
    
    @staticmethod
    def generate_share_link(
        receipt: Receipt,
        expiry_hours: int = 72,
        max_access: int = 5
    ) -> ShareLink:
        """
        Generate a secure share link for a receipt.
        
        Args:
            receipt: Receipt instance
            expiry_hours: Hours until link expires
            max_access: Maximum number of accesses
            
        Returns:
            ShareLink instance
        """
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Create share link
        share_link = ShareLink.objects.create(
            receipt=receipt,
            token=token,
            expires_at=timezone.now() + timedelta(hours=expiry_hours),
            max_access=max_access
        )
        
        logger.info(f"Generated share link for receipt {receipt.receipt_number}")
        
        return share_link
    
    @staticmethod
    def get_share_url(share_link: ShareLink) -> str:
        """
        Get full share URL for a share link.
        
        Args:
            share_link: ShareLink instance
            
        Returns:
            Full URL string
        """
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}/api/receipts/share/{share_link.token}/pdf"
    
    @staticmethod
    def validate_share_link(token: str) -> Optional[Receipt]:
        """
        Validate a share link and return the receipt if valid.
        
        Args:
            token: Share link token
            
        Returns:
            Receipt instance if valid, None otherwise
        """
        try:
            share_link = ShareLink.objects.get(token=token)
            
            if not share_link.is_valid():
                return None
            
            # Increment access count
            share_link.access_count += 1
            share_link.save(update_fields=['access_count'])
            
            return share_link.receipt
            
        except ShareLink.DoesNotExist:
            return None
    
    @staticmethod
    def get_whatsapp_share_url(share_link: ShareLink) -> str:
        """
        Generate WhatsApp share URL.
        
        Args:
            share_link: ShareLink instance
            
        Returns:
            WhatsApp share URL
        """
        share_url = PDFService.get_share_url(share_link)
        receipt = share_link.receipt
        
        message = (
            f"Receipt #{receipt.receipt_number}\n"
            f"Student: {receipt.student_name}\n"
            f"Download: {share_url}"
        )
        
        return f"https://wa.me/?text={message}"
    
    @staticmethod
    def get_email_share_data(share_link: ShareLink) -> Dict[str, str]:
        """
        Generate email share data.
        
        Args:
            share_link: ShareLink instance
            
        Returns:
            Dictionary with subject and body
        """
        share_url = PDFService.get_share_url(share_link)
        receipt = share_link.receipt
        
        return {
            'subject': f"Receipt #{receipt.receipt_number}",
            'body': (
                f"Dear {receipt.student_name},\n\n"
                f"Please find your receipt #{receipt.receipt_number} at:\n"
                f"{share_url}\n\n"
                f"This link will expire in 72 hours.\n\n"
                f"Regards,\n"
                f"Institution Name"
            ),
            'mailto_link': (
                f"mailto:?subject=Receipt%20{receipt.receipt_number}&"
                f"body=Download%20your%20receipt%3A%20{share_url}"
            )
        }