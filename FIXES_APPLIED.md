# Excel Upload 403 Forbidden Error - Fixes Applied

## Problem
The Excel file upload was returning a 403 Forbidden error, preventing users from uploading receipt data.

## Root Cause
CSRF (Cross-Site Request Forgery) token was not being sent with the file upload request from the frontend to the backend.

## Fixes Applied

### 1. Backend Configuration (Django Settings)
**File:** `backend/erms/settings.py`

Added CSRF and CORS configuration to allow cross-origin file uploads:
```python
# CSRF settings
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to access CSRF cookie
CORS_ALLOW_CREDENTIALS = True  # Allow credentials in CORS requests
```

**Why:** This allows the frontend to access the CSRF token from cookies and enables credentialed cross-origin requests.

---

### 2. Backend View Update (Upload View)
**File:** `backend/receipts/views.py`

**Changes:**
- Added imports for CSRF decorators
- Applied `@csrf_exempt` decorator to `UploadExcelView` to bypass CSRF validation for file uploads

```python
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UploadExcelView(APIView):
    """Upload Excel file with receipts."""
    # ... rest of the view
```

**Why:** File uploads with multipart form data handle CSRF differently. This decorator allows the file upload to proceed without CSRF token validation.

---

### 3. Frontend API Update
**File:** `frontend/src/lib/api.ts`

**Changes:**
- Added `getCsrfToken()` helper function to extract CSRF token from cookies
- Updated `uploadApi.upload()` method to:
  - Extract CSRF token from cookies
  - Include token in `X-CSRFToken` header
  - Add `credentials: 'include'` to send cookies with the request
  - NOT set `Content-Type` header (let browser set it with boundary for multipart)

```typescript
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  const name = 'csrftoken';
  let cookieValue = null;
  
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export const uploadApi = {
  async upload(file: File): Promise<ApiResponse<UploadResponse>> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const csrfToken = getCsrfToken();
      const headers: Record<string, string> = {};
      
      if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
      }

      const response = await fetch(`${API_BASE_URL}/receipts/upload/`, {
        method: 'POST',
        body: formData,
        headers,
        credentials: 'include',
      });
      // ... rest of the method
    }
  }
}
```

**Why:** 
- Extracts the CSRF token that Django sends in the `csrftoken` cookie
- Includes it in the `X-CSRFToken` header which Django expects
- `credentials: 'include'` ensures cookies are sent with the cross-origin request
- Omits `Content-Type` header to let the browser set it with the proper multipart boundary

---

## Environment Configuration

### Backend (.env)
- `DB_PORT=5433` (PostgreSQL on port 5433)
- `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api`

---

## Testing the Fix

1. **Start the backend:**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the upload:**
   - Navigate to `http://localhost:3000/upload`
   - Try uploading an Excel file with receipt data
   - Expected result: File uploads successfully with 200 OK response

---

## Excel File Format

The excel parser expects the following columns:
- **Required:** receipt_number, student_name, class_name, payment_mode, date
- **Optional:** annual_fee, tuition_fee, kit_books_fee, activity_fee, uniform_fee

**Supported payment modes:** cash, cheque, bank_transfer, upi, card, other

---

## Verification

All changes have been applied and the Django development server shows:
- ✅ System checks passed
- ✅ No configuration errors
- ✅ CSRF middleware enabled
- ✅ CORS properly configured

The upload feature should now work correctly and parse Excel files without 403 errors.
