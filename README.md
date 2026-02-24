# Enterprise Receipt Management System (ERMS)

A secure, versioned receipt management system for internal college financial infrastructure.

## 🏗 Architecture

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL
- **PDF Generation**: WeasyPrint

## ✨ Features

### Core Features
- ✅ Excel upload with validation and duplicate detection
- ✅ Automatic versioning for all receipt changes
- ✅ Field-level audit logging
- ✅ Instant receipt search with filters
- ✅ PDF generation and download
- ✅ Print support
- ✅ Share via WhatsApp and Email (signed URLs)
- ✅ Upload batch history tracking

### Enterprise Features
- ✅ Immutable version history
- ✅ Field-level change tracking
- ✅ Atomic database transactions
- ✅ Secure share links with expiration

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Create PostgreSQL database
createdb erms_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin

## 📁 Project Structure

```
reciept/
├── backend/
│   ├── erms/                 # Django project settings
│   ├── receipts/             # Main app
│   │   ├── models.py         # Data models
│   │   ├── serializers.py    # DRF serializers
│   │   ├── views.py          # API views
│   │   ├── urls.py           # URL routing
│   │   └── services/         # Business logic
│   │       ├── excel_parser.py
│   │       ├── receipt_service.py
│   │       ├── version_service.py
│   │       └── pdf_service.py
│   ├── templates/
│   │   └── receipts/
│   │       └── receipt_pdf.html
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Dashboard
│   │   │   ├── receipts/
│   │   │   │   ├── page.tsx          # Receipt list
│   │   │   │   └── [receiptNumber]/
│   │   │   │       └── page.tsx      # Receipt detail
│   │   │   ├── upload/
│   │   │   │   └── page.tsx          # Excel upload
│   │   │   └── batches/
│   │   │       └── page.tsx          # Upload history
│   │   └── lib/
│   │       └── api.ts                # API client
│   └── .env.local
│
└── README.md
```

## 📊 Database Schema

### receipts (Master Record)
- `id` (UUID PK)
- `receipt_number` (unique, indexed)
- `current_version_id` (FK to receipt_versions)
- `status` (active/voided)
- `created_at`, `updated_at`

### receipt_versions (Immutable History)
- `id` (UUID PK)
- `receipt_id` (FK)
- `version_number` (sequential)
- All receipt data fields
- `source` (upload/manual_edit)
- `batch_id`, `changed_by`, `changed_at`

### upload_batches
- Upload tracking with insert/update/failed counts

### audit_logs
- Field-level change tracking with old/new values

### share_links
- Secure signed URLs with expiration

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/receipts/` | Search receipts |
| GET | `/api/receipts/{receipt_number}/` | Get receipt detail |
| PUT | `/api/receipts/{receipt_number}/` | Update receipt |
| DELETE | `/api/receipts/{receipt_number}/` | Void receipt |
| GET | `/api/receipts/{receipt_number}/versions/` | Version history |
| GET | `/api/receipts/{receipt_number}/audit/` | Audit log |
| GET | `/api/receipts/{receipt_number}/pdf/` | Download PDF |
| POST | `/api/receipts/{receipt_number}/share/` | Generate share link |
| POST | `/api/receipts/upload/` | Upload Excel |
| GET | `/api/receipts/batches/` | Upload history |
| GET | `/api/receipts/stats/` | Dashboard stats |

## 📋 Excel Format

Required columns:
- `receipt_number` (unique)
- `student_name`
- `class_name`
- `payment_mode` (cash/cheque/bank_transfer/upi/card/other)
- `date` (YYYY-MM-DD or DD/MM/YYYY)

Optional fee columns:
- `annual_fee`, `tuition_fee`, `kit_books_fee`, `activity_fee`, `uniform_fee`

## 🔒 Security Features

- CSRF protection
- Input validation via serializers
- File size limits (5MB)
- Signed share URLs with expiration
- Atomic database transactions

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📦 Production Deployment

### Backend
1. Set `DEBUG=False` in `.env`
2. Configure proper `SECRET_KEY`
3. Set up HTTPS
4. Use Gunicorn + Nginx
5. Configure PostgreSQL backups

### Frontend
1. Build: `npm run build`
2. Start: `npm start`
3. Or deploy to Vercel

## 📝 License

Internal use only - Educational Institution

## 🤝 Contributing

This is an internal project. Contact the development team for contribution guidelines.