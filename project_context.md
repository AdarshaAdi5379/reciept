# Project Context: Enterprise Receipt Management System (ERMS)

## 📋 Project Overview

**Project Name:** Enterprise Receipt Management System (ERMS)  
**Type:** Internal College Financial Receipt Infrastructure  
**Version:** 1.0.0  
**Status:** MVP Complete

### Purpose
A secure, versioned receipt management system designed for educational institutions to:
- Upload and process receipt data from Excel files
- Maintain complete audit history of all changes
- Generate professional, enterprise-level PDF receipts with:
  - A4 formatted, print-ready layout
  - Two-column information sections
  - Dynamic fee tables with rupees/paise columns
  - Amount-in-words conversion (Indian English format)
  - Multi-signature support (Student/Parent, Received By, Accountant)
  - Watermark support for voided receipts
- Share receipts via secure links (WhatsApp/Email)
- Provide instant search and filtering capabilities

---

## 🏗 Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Primary backend language |
| Django | 4.2 LTS | Web framework |
| Django REST Framework | 3.14+ | API framework |
| PostgreSQL | 14+ | Primary database |
| WeasyPrint | 60+ | PDF generation |
| openpyxl | 3.1+ | Excel file processing |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| python-dotenv | 1.0+ | Environment management |
| django-cors-headers | 4.3+ | CORS handling |
| gunicorn | 21.0+ | WSGI HTTP Server |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15.x | React framework (App Router) |
| React | 19.x | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Styling |
| ESLint | 9.x | Code linting |

### Development Tools
- Git (Version Control)
- pip (Python Package Manager)
- npm (Node Package Manager)

---

## 🎯 Design Principles & Practices

### Architecture Patterns

1. **Service Layer Pattern**
   - Business logic separated from views
   - Services: `ExcelParserService`, `ReceiptService`, `VersionService`, `PDFService`
   - Promotes testability and reusability

2. **Repository Pattern (Django ORM)**
   - Models as data access layer
   - QuerySets for complex queries
   - Managers for custom query logic

3. **API-First Design**
   - RESTful API endpoints
   - JSON responses
   - Stateless authentication (future)

4. **Immutable Versioning**
   - Never update existing version records
   - Every change creates a new version
   - Complete audit trail

### Coding Standards

**Backend (Python/Django):**
- PEP 8 style guide
- Type hints where applicable
- Docstrings for all classes and functions
- Service classes with static methods
- Atomic database transactions
- Explicit error handling with logging

**Frontend (TypeScript/React):**
- Functional components with hooks
- Strict TypeScript configuration
- Component-based architecture
- Custom API client with typed responses
- Client-side state management with useState/useEffect

### Security Practices

1. **Input Validation**
   - Serializer validation on all inputs
   - File type and size validation
   - SQL injection prevention via ORM

2. **Data Integrity**
   - Atomic transactions for multi-step operations
   - Database constraints (unique, foreign keys)
   - UUID primary keys (non-sequential)

3. **Access Control**
   - CSRF protection
   - CORS configuration
   - File size limits (5MB)
   - Signed URLs for sharing (with expiration)

---

## 📁 Project Structure

```
reciept/
├── README.md                    # Project documentation
├── TODO.md                      # Task tracking
├── project_context.md           # This file
│
├── backend/                     # Django Backend
│   ├── manage.py                # Django management script
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment template
│   │
│   ├── erms/                    # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py          # Django settings
│   │   ├── urls.py              # Root URL configuration
│   │   ├── wsgi.py              # WSGI application
│   │   └── asgi.py              # ASGI application
│   │
│   ├── core/                    # Core app (placeholder)
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   └── views.py
│   │
│   ├── receipts/                # Main receipts app
│   │   ├── __init__.py
│   │   ├── admin.py             # Admin configuration
│   │   ├── apps.py
│   │   ├── models.py            # Data models
│   │   ├── serializers.py       # DRF serializers
│   │   ├── urls.py              # URL routing
│   │   ├── views.py             # API views
│   │   │
│   │   ├── migrations/          # Database migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   │
│   │   ├── services/            # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── excel_parser.py  # Excel validation & parsing
│   │   │   ├── receipt_service.py # Receipt operations
│   │   │   ├── version_service.py # Versioning logic
│   │   │   └── pdf_service.py   # PDF generation
│   │   │
│   │   └── tests/               # Test files (future)
│   │
│   ├── templates/               # Django templates
│   │   └── receipts/
│   │       └── receipt_pdf.html # PDF template
│   │
│   └── logs/                    # Application logs
│       └── erms.log
│
└── frontend/                    # Next.js Frontend
    ├── package.json             # Node dependencies
    ├── tsconfig.json            # TypeScript config
    ├── next.config.ts           # Next.js config
    ├── postcss.config.mjs       # PostCSS config
    ├── eslint.config.mjs        # ESLint config
    ├── .env.local               # Environment variables
    │
    ├── public/                  # Static assets
    │   ├── favicon.ico
    │   └── *.svg
    │
    └── src/
        ├── app/                 # App Router pages
        │   ├── layout.tsx       # Root layout
        │   ├── page.tsx         # Dashboard
        │   ├── globals.css      # Global styles
        │   │
        │   ├── receipts/
        │   │   ├── page.tsx     # Receipt list/search
        │   │   └── [receiptNumber]/
        │   │       └── page.tsx # Receipt detail
        │   │
        │   ├── upload/
        │   │   └── page.tsx     # Excel upload
        │   │
        │   └── batches/
        │       └── page.tsx     # Upload history
        │
        └── lib/
            └── api.ts           # API client & types
```

---

## 🗄 Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌──────────────────────┐
│   Receipt       │       │   ReceiptVersion     │
├─────────────────┤       ├──────────────────────┤
│ id (UUID)       │──┐    │ id (UUID)            │
│ receipt_number  │  │    │ receipt_id (FK)──────│─┐
│ current_version │──│──┼─▶│ version_number      │ │
│ status          │  │    │ student_name         │ │
│ created_at      │  │    │ class_name           │ │
│ updated_at      │  │    │ payment_mode         │ │
└─────────────────┘  │    │ date                 │ │
                     │    │ annual_fee           │ │
                     │    │ tuition_fee          │ │
                     │    │ kit_books_fee        │ │
                     │    │ activity_fee         │ │
                     │    │ uniform_fee          │ │
                     │    │ source               │ │
                     │    │ batch_id (FK)        │ │
                     │    │ changed_by (FK)      │ │
                     │    │ changed_at           │ │
                     │    └──────────────────────┘ │
                     │                             │
                     │    ┌──────────────────────┐ │
                     │    │   UploadBatch        │ │
                     │    ├──────────────────────┤ │
                     │    │ id (UUID)            │ │
                     └───▶│ file_name            │ │
                          │ uploaded_by (FK)     │ │
                          │ uploaded_at          │ │
                          │ records_inserted     │ │
                          │ records_updated      │ │
                          │ records_failed       │ │
                          │ status               │ │
                          └──────────────────────┘ │
                                                   │
┌─────────────────┐       ┌──────────────────────┐ │
│   AuditLog      │       │   ShareLink          │ │
├─────────────────┤       ├──────────────────────┤ │
│ id (UUID)       │       │ id (UUID)            │ │
│ receipt_id (FK) │───────│ receipt_id (FK)      │─┘
│ version_id (FK) │       │ token                │
│ field_name      │       │ created_at           │
│ old_value       │       │ expires_at           │
│ new_value       │       │ access_count         │
│ changed_by (FK) │       │ max_access           │
│ changed_at      │       │ is_active            │
│ reason          │       └──────────────────────┘
└─────────────────┘
```

### Model Details

#### Receipt (Master Record)
- Primary entity for each unique receipt
- `receipt_number` is unique and indexed for fast lookups
- `current_version` points to the latest version data
- `status` can be 'active' or 'voided'

#### ReceiptVersion (Immutable History)
- Stores all receipt data fields
- `version_number` increments sequentially per receipt
- `source` tracks origin: 'upload', 'manual_edit', 'api'
- Never updated - only new records inserted

#### UploadBatch
- Tracks each Excel upload operation
- Stores statistics: inserted, updated, failed counts
- `error_log` contains JSON array of errors

#### AuditLog
- Field-level change tracking
- Links to both receipt and version
- Stores old and new values for each field change

#### ShareLink
- Secure token-based sharing
- Configurable expiration and access limits
- Tracks access count

---

## 🔌 API Reference

### Base URL
- Development: `http://localhost:8000/api`
- Production: Configured via environment

### Endpoints

#### Receipts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/receipts/` | Search receipts with filters |
| GET | `/receipts/{receipt_number}/` | Get receipt details |
| PUT | `/receipts/{receipt_number}/` | Update receipt (creates new version) |
| DELETE | `/receipts/{receipt_number}/` | Void receipt (soft delete) |
| GET | `/receipts/{receipt_number}/versions/` | Get version history |
| GET | `/receipts/{receipt_number}/audit/` | Get field-level audit log |
| GET | `/receipts/{receipt_number}/pdf/` | Download PDF |
| POST | `/receipts/{receipt_number}/share/` | Generate share link |

#### Upload

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/receipts/upload/` | Upload Excel file |
| GET | `/receipts/batches/` | List upload history |
| GET | `/receipts/batches/{batch_id}/` | Get batch details |

#### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/receipts/stats/` | Get dashboard statistics |

### Query Parameters (Search)

| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | Search by receipt number or student name |
| student_name | string | Filter by student name (partial match) |
| class_name | string | Filter by class |
| payment_mode | string | Filter by payment mode |
| date_from | date | Filter from date (YYYY-MM-DD) |
| date_to | date | Filter until date (YYYY-MM-DD) |
| status | string | Filter by status (active/voided) |
| page | int | Page number (default: 1) |
| page_size | int | Items per page (default: 50, max: 100) |

### Response Formats

**Success Response:**
```json
{
  "id": "uuid",
  "receipt_number": "RCP001",
  "student_name": "John Doe",
  ...
}
```

**Error Response:**
```json
{
  "error": "Error message description"
}
```

**Upload Response:**
```json
{
  "success": true,
  "batch_id": "uuid",
  "inserted": 100,
  "updated": 20,
  "failed": 3,
  "errors": [
    {"receipt_number": "RCP050", "error": "Invalid date format"}
  ]
}
```

---

## 📊 Business Logic

### Excel Upload Flow

```
1. File Validation
   ├── Check file extension (.xlsx, .xls)
   ├── Check file size (max 5MB)
   └── Parse with openpyxl

2. Header Validation
   ├── Normalize header names
   ├── Check required headers present
   └── Map to internal field names

3. Row Processing (Atomic Transaction)
   ├── For each valid row:
   │   ├── Check if receipt_number exists
   │   ├── If exists:
   │   │   ├── Compare with current version
   │   │   └── If different → Create new version
   │   └── If new:
   │       ├── Create Receipt record
   │       └── Create Version 1
   └── Rollback on any error

4. Response
   └── Return insert/update/fail counts
```

### Version Creation Flow

```
1. Fetch current version
2. Compare all tracked fields
3. If no changes → Return existing version
4. If changes exist:
   ├── Increment version_number
   ├── Create new ReceiptVersion
   ├── Update Receipt.current_version
   └── Create AuditLog entries for each changed field
```

### PDF Generation Flow

```
1. Fetch receipt with current version
2. Render HTML template with context
3. Apply print-optimized CSS
4. Convert to PDF via WeasyPrint
5. Return as downloadable response
```

---

## 🔧 Configuration

### Environment Variables (Backend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DEBUG | No | True | Enable debug mode |
| SECRET_KEY | Yes | - | Django secret key |
| DB_NAME | Yes | erms_db | Database name |
| DB_USER | Yes | postgres | Database user |
| DB_PASSWORD | Yes | - | Database password |
| DB_HOST | Yes | localhost | Database host |
| DB_PORT | No | 5432 | Database port |
| ALLOWED_HOSTS | No | localhost | Comma-separated hosts |
| CORS_ALLOWED_ORIGINS | No | http://localhost:3000 | Comma-separated origins |
| INSTITUTION_NAME | No | - | For PDF header |
| BASE_URL | No | http://localhost:8000 | For share links |

### Environment Variables (Frontend)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| NEXT_PUBLIC_API_URL | Yes | http://localhost:8000/api | Backend API URL |

---

## 🧪 Testing Strategy

### Backend Tests (Future)
- Unit tests for services
- Integration tests for API endpoints
- Model tests for constraints

### Frontend Tests (Future)
- Component tests
- Integration tests for pages
- API client tests

---

## 🚀 Deployment

### Backend (Production)

1. **Environment Setup:**
   ```bash
   DEBUG=False
   SECRET_KEY=<secure-key>
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

2. **Database:**
   - Use managed PostgreSQL (AWS RDS, Railway, etc.)
   - Enable SSL connections
   - Configure daily backups

3. **Server:**
   - Gunicorn WSGI server
   - Nginx reverse proxy
   - HTTPS via Let's Encrypt

### Frontend (Production)

1. **Build:**
   ```bash
   npm run build
   ```

2. **Deploy Options:**
   - Vercel (recommended)
   - Self-hosted with Node.js
   - Docker container

---

## 📈 Performance Considerations

### Database Indexing
- `receipt_number` - unique index for lookups
- `student_name` - index for search
- `class_name` - index for filtering
- `date` - index for date range queries
- `status` + `created_at` - composite index for list views

### Query Optimization
- `select_related` for foreign keys
- `prefetch_related` for reverse relations
- Pagination for all list endpoints

### Caching (Future)
- Redis for frequently accessed data
- Cache dashboard statistics
- Cache PDF generation results

---

## 🔐 Security Checklist

- [x] CSRF protection enabled
- [x] CORS configured
- [x] Input validation via serializers
- [x] File type validation
- [x] File size limits
- [x] SQL injection prevention (ORM)
- [x] UUID primary keys
- [x] Atomic transactions
- [x] Signed share URLs
- [ ] Rate limiting (future)
- [ ] Authentication (future)
- [ ] RBAC (future)

---

## 📝 Future Enhancements

### Phase 2 Features
- User authentication (JWT)
- Role-based access control
- Rate limiting
- Audit log UI
- Bulk operations
- Export to Excel

### Phase 3 Features
- Student portal (read-only)
- Payment integration
- Email notifications
- Dashboard analytics
- Custom receipt templates

---

## 👥 Development Team

This is an internal project for educational institution use.

---

## 📞 Support

For issues or questions, contact the development team or refer to the project documentation in README.md.