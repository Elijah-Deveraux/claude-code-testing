# Quick Start Guide

## Prerequisites

1. Python 3.9+ installed
2. Virtual environment activated
3. All dependencies installed from `requirements.txt`

## Configuration Steps

### 1. Get Your Google API Key (REQUIRED)

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

### 2. Configure Environment Variables

Open the `.env` file and replace the following:

```bash
# Replace this line:
GOOGLE_API_KEY=your_google_api_key_here_REPLACE_THIS

# With your actual key:
GOOGLE_API_KEY=AIzaSyD...your_actual_key_here
```

**Optional but Recommended**: Replace the API_KEY with a secure value:
```bash
# Generate a secure key:
openssl rand -hex 32

# Then replace in .env:
API_KEY=your_generated_secure_key_here
```

### 3. Install Qdrant (Vector Database)

**Option A: In-Memory Mode (Quick Start - No Installation)**
- Works out of the box
- Data is lost when application stops
- Good for testing

**Option B: Persistent Mode (Recommended for Production)**
Using Docker:
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

Or download standalone: https://qdrant.tech/documentation/quick-start/

### 4. Ensure Dependencies Are Installed

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Starting the Application

### Terminal 1: Start Backend API

```bash
cd /home/ec2-user/workspace/coding_agents_eval
source venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Test backend: http://localhost:8000/docs

### Terminal 2: Start Frontend

```bash
cd /home/ec2-user/workspace/coding_agents_eval
source venv/bin/activate
streamlit run frontend/app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Access the Application

1. Open your browser to: http://localhost:8501
2. Upload a PDF document
3. Generate summaries (brief or detailed)

## Verification Checklist

- [ ] `.env` file exists with `GOOGLE_API_KEY` configured
- [ ] Virtual environment is activated
- [ ] Dependencies are installed (`pip install -r requirements.txt`)
- [ ] Qdrant is running (or using in-memory mode)
- [ ] Backend starts without errors on port 8000
- [ ] Frontend starts without errors on port 8501
- [ ] Can access Streamlit UI in browser
- [ ] Backend API docs accessible at http://localhost:8000/docs

## Common Issues

### "GOOGLE_API_KEY not found"
- Make sure you've replaced the placeholder in `.env`
- Ensure the `.env` file is in the project root directory

### "Connection refused" on frontend
- Make sure backend is running first on port 8000
- Check `API_BASE_URL` in `.env` is set to `http://localhost:8000`

### "Qdrant connection error"
- If using persistent mode, ensure Qdrant is running: `docker ps`
- For quick testing, the app will work with in-memory mode

### Import errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## What You Can Do

1. **Upload PDFs**: Use the sidebar to upload PDF documents
2. **View Documents**: See all uploaded documents with metadata
3. **Generate Summaries**: Create brief (3-5 sentences) or detailed (300-500 words) summaries
4. **Search Content**: Semantic search through document content
5. **Delete Documents**: Remove documents and their data

## API Endpoints

- `GET /health` - Health check
- `GET /metrics` - System metrics (requires API key)
- `POST /upload-pdf` - Upload PDF document
- `GET /documents` - List all documents
- `GET /document/{doc_id}` - Get document details
- `DELETE /document/{doc_id}` - Delete document
- `POST /summarize` - Generate summary

Full API documentation: http://localhost:8000/docs

## Need Help?

Check the full documentation:
- `README.md` - Comprehensive documentation
- `ARCHITECTURE.md` - System architecture and design
- `.claude/STAGE_TRACKER.md` - Development progress and features
