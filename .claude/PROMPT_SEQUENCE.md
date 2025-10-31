# Complete Prompt Sequence

Copy the prompt for the current stage and execute it. Always read PROJECT_CONTEXT.md and STAGE_TRACKER.md before starting.

---

## PROMPT 1: Project Foundation & Architecture

Initialize a PDF summarization system with 2-agent architecture (Retrieval Agent and Summarizer Agent).

Requirements:
1. Design and create an industry-standard Python project directory structure suitable for this application
2. Set up virtual environment using venv
3. Create requirements.txt with pinned versions for: FastAPI, Streamlit, Qdrant, PyPDF2/pdfplumber, langchain, langchain-community, google-generativeai
4. Create .env.example with all necessary configuration variables (including GOOGLE_API_KEY for embeddings)
5. Set up basic logging configuration (DEBUG, INFO, WARNING, ERROR levels)
6. Create skeleton files for both agents with proper class structure and docstrings
7. Document the architecture in ARCHITECTURE.md including:
   - System design overview
   - Component interaction flow
   - Technology choices and rationale
   - Directory structure justification

Deliverables:
- Complete project structure
- Virtual environment setup instructions
- Configuration files
- Agent skeleton code with interfaces
- ARCHITECTURE.md

---

## PROMPT 1.5: Framework Refactoring (Adaptability Test)

IMPORTANT CHANGE REQUEST: Framework Migration

After reviewing the initial setup, the team has decided to use LangChain/LangGraph framework instead of sentence-transformers for embeddings and LLM operations.

Requirements:
1. Refactor the project to use LangChain/LangGraph:
   - Replace sentence-transformers with LangChain embeddings (OpenAIEmbeddings or HuggingFaceEmbeddings)
   - Update the Retrieval Agent skeleton to use LangChain components
   - Prepare for LangChain LLM integration in the Summarizer Agent

2. Update requirements.txt:
   - Remove sentence-transformers
   - Add langchain, langchain-community, and langgraph with pinned versions
   - Add any necessary LangChain-specific dependencies

3. Update ARCHITECTURE.md:
   - Document why LangChain/LangGraph was chosen
   - Explain how it will be integrated
   - Update the technology stack section

4. Update agent skeleton code:
   - Modify Retrieval Agent to use LangChain's document loaders and embeddings
   - Modify Summarizer Agent to prepare for LangChain LLM chains
   - Maintain the same interface/API contracts

5. Update .env.example:
   - Add any new environment variables needed for LangChain (API keys, model names)

6. Ensure backward compatibility:
   - Don't break any existing structure
   - Maintain the same project organization
   - Keep all existing documentation structure

CRITICAL: Explain what you're changing and why in your response. Show understanding of the architectural impact.

Deliverables:
- Updated requirements.txt
- Refactored agent skeleton code using LangChain
- Updated ARCHITECTURE.md
- Updated .env.example
- Brief migration summary documenting changes made

---

## PROMPT 2: Backend API Development

Develop the FastAPI backend with complete API functionality.

Requirements:
1. Implement all required endpoints:
   - POST /upload-pdf (file upload, return document ID)
   - GET /documents (list all processed documents)
   - POST /summarize (generate summaries)
   - GET /document/{doc_id} (retrieve document details)
   - DELETE /document/{doc_id} (remove document)
   - GET /health (health check with dependencies status)
   - GET /metrics (processing statistics, cache hit rate)

2. Use Pydantic models for all request/response validation
3. Implement proper error handling with appropriate status codes (200, 201, 400, 404, 500)
4. Enable CORS for frontend integration
5. Add comprehensive logging for all operations
6. Implement API key authentication for all endpoints (simple header-based auth)
7. Add basic rate limiting to prevent abuse (no need for Redis, use in-memory)
8. Ensure all endpoints have detailed docstrings and auto-generate OpenAPI documentation

Keep it simple - no overengineering. Focus on clean, working code.

Deliverables:
- Complete FastAPI application
- Pydantic models
- Error handling middleware
- API documentation accessible at /docs

---

## PROMPT 3: Database & ETL Pipeline

Implement the complete database layer and ETL pipeline using LangChain framework.

Requirements:
1. Set up Qdrant vector database:
   - Initialize collection on first run
   - Configure embedding dimensions for Google Text-Embedding-004 (768 dimensions)
   - Use cosine similarity as distance metric
   - Keep connection setup simple

2. Set up local in memory storage for metadata storage:
   - Simple schema: document_id, filename, upload_date, num_pages, file_size, processing_status
   - Basic table structure, no complex relations

3. Implement Retrieval Agent using LangChain and Google Text-Embedding-004:
   - Use LangChain's PyPDFLoader for PDF text extraction
   - Use RecursiveCharacterTextSplitter with chunk_size=1000, chunk_overlap=200
   - Generate embeddings using Google Text-Embedding-004 (free via Google AI API)
   - Store vectors in Qdrant using LangChain's Qdrant integration
   - Store metadata in local in memory storage
   - Implement simple semantic search that returns top 3-5 relevant chunks
   - Basic query caching (in-memory dictionary is fine)
   - Handle errors gracefully for corrupted PDFs

4. Implement basic CRUD operations:
   - Create: add document
   - Read: retrieve document chunks
   - Delete: remove from both databases
   - Keep it simple, no complex update logic needed

5. Add simple database reset function
6. Basic retry logic (3 attempts with 1 second delay)
7. Input validation using Pydantic

IMPORTANT: Use Google Text-Embedding-004 (free, no billing required for reasonable usage). Keep everything simple and straightforward.

Deliverables:
- Functional Retrieval Agent using LangChain + Google embeddings
- Database initialization code
- Basic CRUD operations
- Simple error handling

---

## PROMPT 4: Summarization Agent & LLM Integration

Implement the Summarizer Agent using LangChain framework with free/open-source LLM.

Requirements:
1. Implement Summarizer Agent using LangChain:
   - Use Google Gemini (free tier via google-generativeai) OR Ollama with llama3.2 (completely free, local)
   - Retrieve relevant context from Retrieval Agent (top 3-5 chunks)
   - Create simple prompt templates for:
     * Brief summary: "Summarize in 3-5 sentences: {context}"
     * Detailed summary: "Provide detailed 300-500 word summary: {context}"
   - Use basic LangChain LLMChain (keep it simple)
   - Include page numbers in output
   - Basic length validation (count words/sentences)

2. Simple token/cost tracking:
   - Count input/output tokens using tiktoken or similar
   - Log to file with timestamp
   - Store in local in memory storage: summary_id, doc_id, tokens_used, timestamp
   - No need for complex cost calculations

3. Basic optimization:
   - Use async for LLM calls
   - Simple caching: store summary in local in memory storage, return if same doc requested
   - Keep context window under 4000 tokens

4. Add docstrings and type hints

Keep it simple - a working summarizer is better than a complex one.

Deliverables:
- Functional Summarizer Agent using free LLM
- Basic token tracking
- Simple caching
- Async implementation

---

## PROMPT 5: Frontend Development

Develop a clean Streamlit frontend with all functionality.

Requirements:
1. Create a simple, functional UI with:
   - Page title and description
   - Sidebar for navigation/settings
   - PDF upload widget (file_uploader)
   - Upload progress (use st.progress)
   - Document info display (filename, pages, size)
   - List of uploaded documents in sidebar (use st.selectbox)
   - Radio buttons to toggle summary type (Brief/Detailed)
   - Summary display area with st.markdown
   - Error messages using st.error
   - Success messages using st.success
   - Loading spinners with st.spinner

2. Session state management:
   - Store uploaded documents in st.session_state
   - Remember selected document
   - Keep summary results
   - Persist across reruns

3. Connect to FastAPI backend:
   - Use requests library for API calls
   - Handle all endpoints properly
   - Show user-friendly error messages if backend is down
   - Display API errors clearly

4. Keep design clean and simple - function over form

Deliverables:
- Working Streamlit application
- Session state working properly
- Full backend integration
- Clean, usable interface

---

## PROMPT 6: Testing & Quality Assurance

Implement a straightforward testing suite.

Requirements:
1. Create unit tests:
   - Test Retrieval Agent methods (chunking, embedding, search)
   - Test Summarizer Agent methods (summary generation)
   - Mock LangChain components (embeddings, LLMs) using unittest.mock
   - Use pytest fixtures for sample data
   - Include a small sample PDF in tests/fixtures/

2. Create API tests:
   - Test all endpoints using FastAPI TestClient
   - Test happy paths (valid inputs)
   - Test error cases (invalid file, missing doc_id)
   - Test authentication (valid/invalid API key)

3. Create one integration test:
   - Upload PDF → Extract → Store → Summarize (full workflow)
   - Use a real small PDF

4. Achieve >70% code coverage:
   - Run: pytest --cov=. --cov-report=html
   - Focus on critical paths, don't stress about 100%

5. Basic code quality:
   - Run: flake8 . --max-line-length=120 --ignore=E501
   - Fix critical issues only

6. Create simple test runner script: run_tests.sh

Keep tests simple and practical - they should catch real bugs, not be perfect.

Deliverables:
- Working test suite (unit + API + integration)
- Sample PDF fixture
- Coverage report >70%
- Most flake8 issues resolved

---

## PROMPT 7: Documentation & Deployment

Complete all documentation and basic deployment setup.

Requirements:
1. Create comprehensive README.md with these sections (in order):
   A. Project title and one-line description
   B. Table of contents (linked)
   C. Overview (200-300 words: what it does, why, key features)
   D. Architecture diagram (simple ASCII art or description)
   E. Project structure (directory tree with brief explanations)
   F. Prerequisites (Python 3.12, any system dependencies)
   G. Installation:
      - Clone repo
      - Create venv: python -m venv venv
      - Activate: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)
      - Install: pip install -r requirements.txt
      - Setup .env file (copy from .env.example, add GOOGLE_API_KEY)
   H. Configuration (table of environment variables)
   I. Usage:
      - Start backend: uvicorn main:app --reload
      - Start frontend: streamlit run frontend/app.py
      - Include cURL examples for 2-3 key endpoints
   J. API Documentation (brief overview, link to /docs)
   K. Testing (how to run: pytest)
   L. Workflow diagram (simple: Upload → Extract → Store → Retrieve → Summarize)
   M. Troubleshooting (5 common issues with solutions)
   N. Future improvements (3-5 ideas)
   O. License (MIT)

2. Create SETUP.md:
   - Detailed setup for Windows/Mac/Linux
   - Troubleshooting installation issues

3. Basic CI/CD with GitHub Actions:
   - Simple workflow: install dependencies → run tests → report coverage
   - Trigger on push to main branch
   - Keep it simple, no deployment

4. Simple Docker setup:
   - Dockerfile for the application
   - docker-compose.yml with: app, qdrant
   - Basic environment variable handling
   - Simple instructions in README

5. Optional: Simple Jupyter notebook showing vector search example

Keep documentation clear and practical. Focus on getting someone up and running quickly.

Deliverables:
- Complete README.md with all sections
- SETUP.md
- GitHub Actions workflow file
- Dockerfile and docker-compose.yml
- All docs clear and accurate

---

# End of Prompts

Remember: Read context files before each stage, update tracker during work, create summaries after completion.
