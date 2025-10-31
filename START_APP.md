# Start Application - Ready to Run!

## Configuration Status ✅

Your `.env` file is now fully configured and ready to use:

- ✅ **GOOGLE_API_KEY**: Configured with your API key
- ✅ **LLM Model**: Gemini 2.0 Flash (gemini-2.0-flash-exp) - Latest and fastest
- ✅ **Embedding Model**: text-embedding-004 (768 dimensions)
- ✅ **Vector Database**: In-memory mode (no external installation needed)
- ✅ **API Key**: dev-key-12345 (for local development)
- ✅ **Logs Directory**: Created

## Start Commands

### Step 1: Start Backend API

Open **Terminal 1** and run:

```bash
cd /home/ec2-user/workspace/coding_agents_eval
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

### Step 2: Start Frontend

Open **Terminal 2** and run:

```bash
cd /home/ec2-user/workspace/coding_agents_eval
source venv/bin/activate
streamlit run frontend/app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://xxx.xxx.xxx.xxx:8501
```

**Access Application:**
- Open browser: http://localhost:8501

---

## Quick Test

1. **Upload a PDF**: Click "Upload PDF" in sidebar, select a PDF file
2. **View Documents**: Check that your document appears in the list
3. **Generate Summary**: Select "Generate Summary", choose "Brief" or "Detailed"
4. **View Results**: Summary will appear with page references

---

## Configuration Details

### Current Settings:

| Setting | Value | Description |
|---------|-------|-------------|
| LLM Provider | Gemini | Google's Gemini AI |
| LLM Model | gemini-2.0-flash-exp | Latest Gemini 2.0 Flash |
| Embedding Model | text-embedding-004 | Google's embedding model |
| Vector Database | In-memory | No external DB needed |
| API Port | 8000 | Backend API port |
| Frontend Port | 8501 | Streamlit UI port |

### Why In-Memory Mode?

- ✅ **No installation required**: Start immediately
- ✅ **Perfect for testing**: Quick setup
- ✅ **No configuration needed**: Works out of the box
- ⚠️ **Data is temporary**: Lost when app restarts

**For Production**: Set `QDRANT_URL=http://localhost:6333` and run Qdrant Docker container.

---

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process if needed
kill -9 <PID>
```

### Frontend won't start
```bash
# Check if port 8501 is in use
lsof -i :8501

# Kill existing process if needed
kill -9 <PID>
```

### "Invalid API Key" error
Check that `.env` has:
```
GOOGLE_API_KEY=AIzaSyDeF8RSQ3JK2aZIVF5Lq77LfiVEu5zdRys
```
(No quotes around the value)

### Import errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## What You Can Do Now

1. **Upload PDFs**: Any PDF document (max 50MB)
2. **Generate Summaries**:
   - Brief: 3-5 sentences
   - Detailed: 300-500 words with structure
3. **View Documents**: See all uploaded documents with metadata
4. **Delete Documents**: Remove documents and their embeddings
5. **API Access**: Use REST API at http://localhost:8000/docs

---

## API Examples (Optional)

### Upload PDF via curl:
```bash
curl -X POST "http://localhost:8000/upload-pdf" \
  -H "X-API-Key: dev-key-12345" \
  -F "file=@/path/to/your/document.pdf"
```

### Get All Documents:
```bash
curl -X GET "http://localhost:8000/documents" \
  -H "X-API-Key: dev-key-12345"
```

### Generate Summary:
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "X-API-Key: dev-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-doc-id",
    "summary_type": "brief"
  }'
```

---

## Ready to Start!

Your application is fully configured and ready to run. Just execute the two commands above in separate terminals and start using the PDF summarization system!

**Next Steps:**
1. Start backend (Terminal 1)
2. Start frontend (Terminal 2)
3. Open http://localhost:8501 in browser
4. Upload your first PDF!

---

**Note**: The application uses in-memory storage, so all data will be lost when you restart the backend. For persistent storage, see `QUICK_START.md` for Qdrant Docker setup.
