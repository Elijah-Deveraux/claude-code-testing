# Debug Fix Applied

## Changes Made

### 1. Backend (`src/api/routes/documents.py`)
- Added more detailed logging to show filename and content_type
- Added explicit check for null/empty filename
- Made PDF extension check case-insensitive (`.pdf` or `.PDF`)
- Improved error messages to show what filename was received

### 2. Frontend (`frontend/app.py`)
- Updated error handling to show both `error` and `detail` fields from response
- Added status code to error message
- Added debug info display to see full error response

## Next Steps

1. **If backend is running with `--reload`**: Changes should auto-reload
2. **If not**: Restart the backend:
   ```bash
   # Press Ctrl+C to stop
   source venv/bin/activate
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Restart frontend** (to load the new error handling):
   ```bash
   # Press Ctrl+C to stop
   source venv/bin/activate
   streamlit run frontend/app.py
   ```

4. **Try uploading again** and check:
   - The detailed error message in the UI
   - The backend logs for the filename and content_type

## What to Look For

### In the Frontend UI:
- You should now see: `❌ Upload failed (Status 400): [detailed error message]`
- Plus a "Debug info" line showing the full error response

### In the Backend Logs:
Look for a line like:
```
INFO: PDF upload requested: filename=sample_2.pdf, content_type=application/pdf
```

This will tell us:
- Is the filename being sent correctly?
- Is the content type correct?
- What's the actual error?

## Possible Issues

1. **Filename is None/empty**: Frontend not sending filename correctly
2. **Extension not .pdf**: Case sensitivity or encoding issue
3. **Different error**: Size limit, authentication, etc.

The debug output will show us exactly what's happening!
