import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from receipts.models import Receipt, ReceiptVersion
from receipts.services.pdf_service import PDFService
from decimal import Decimal
from datetime import date

# Find an existing receipt or create a new one
receipt = Receipt.objects.first()
if not receipt:
    receipt = Receipt.objects.create(receipt_number='082')
    version = ReceiptVersion.objects.create(
        receipt=receipt,
        version_number=1,
        student_name='JEFFRIN NIXON',
        class_name='Nursery',
        payment_mode='cash',
        date=date(2026, 2, 9),
        kit_books_fee=Decimal('15000.00'),
        uniform_fee=Decimal('5000.00')
    )
    receipt.current_version = version
    receipt.save()

# Generate PDF
pdf_bytes = PDFService.generate_receipt_pdf(receipt)

with open('test_receipt.pdf', 'wb') as f:
    f.write(pdf_bytes)

print(f"Generated PDF for receipt {receipt.receipt_number}")
