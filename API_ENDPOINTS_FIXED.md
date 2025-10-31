# API Endpoints - Fixed

## Issue Found
The frontend was calling incorrect API endpoints, causing 400 errors.

## Fixed Endpoints

### Before → After

1. **Upload PDF**
   - ❌ Before: `/upload-pdf`
   - ✅ After: `/documents/upload-pdf`

2. **Delete Document**
   - ❌ Before: `/document/{document_id}`
   - ✅ After: `/documents/{document_id}`

3. **Already Correct:**
   - ✅ `/documents` - List documents
   - ✅ `/summarize` - Generate summary
   - ✅ `/health` - Health check
   - ✅ `/metrics` - System metrics

## Complete API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| GET | `/metrics` | System metrics (requires API key) |
| POST | `/documents/upload-pdf` | Upload PDF document |
| GET | `/documents` | List all documents |
| GET | `/documents/{doc_id}` | Get document details |
| DELETE | `/documents/{doc_id}` | Delete document |
| POST | `/summarize` | Generate summary |

## Backend Route Structure

The backend uses router prefixes:

```python
# Health router (no prefix)
app.include_router(health.router)
# Endpoints: /health, /metrics

# Documents router (prefix: /documents)
app.include_router(documents.router)
# Endpoints: /documents/upload-pdf, /documents, /documents/{doc_id}

# Summarize router (prefix: /summarize)
app.include_router(summarize.router)
# Endpoints: /summarize
```

## Changes Made

### File: `frontend/app.py`

1. Line 414: Changed `/upload-pdf` → `/documents/upload-pdf`
2. Line 496: Changed `/document/{document_id}` → `/documents/{document_id}`

## Testing

After these fixes, the application should work correctly:

1. ✅ Upload PDF files
2. ✅ View document list
3. ✅ Generate summaries
4. ✅ Delete documents

## How to Test

1. Start backend: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`
2. Start frontend: `streamlit run frontend/app.py`
3. Upload a PDF through the UI
4. Verify it appears in the document list
5. Generate a summary
6. Delete the document

All endpoints should now work correctly!
