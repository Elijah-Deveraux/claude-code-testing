# PDF Summarizer Project Context

## Current Stage
**Stage:** Stage 2 Complete - Ready for Stage 3 (Database & ETL Pipeline)
**Last Updated:** 2025-10-29

## Project Overview
2-agent architecture PDF summarization system
- **Agent 1 (Retrieval):** PDF ingestion → Text extraction → Vector storage (Qdrant)
- **Agent 2 (Summarizer):** Context retrieval → LLM summarization → Output
- **Backend:** FastAPI with RESTful endpoints
- **Frontend:** Streamlit with session state management
- **Vector Database:** Qdrant (local)
- **Metadata Storage:** local in memory storage

## Technology Stack
- **Python:** 3.12
- **Virtual Environment:** venv
- **Embeddings:** Google Text-Embedding-004 (free, 768 dimensions)
- **LLM:** Google Gemini (free tier) OR Ollama llama3.2 (local)
- **Framework:** LangChain/LangGraph
- **Vector DB:** Qdrant with cosine similarity
- **Philosophy:** Simple, practical, no overengineering

## Key Technical Decisions
- **Using LangChain/LangGraph framework** (decided in Stage 1.5)
  - Removed sentence-transformers dependency
  - Adopted industry-standard LLM orchestration patterns
  - 40-50% code reduction expected
  - Better error handling, retry logic, async support built-in
- **Google Text-Embedding-004** for cost-free embeddings via LangChain GoogleGenerativeAIEmbeddings
- **LangChain document processing**: PyPDFLoader, RecursiveCharacterTextSplitter
- **LangChain LLM integration**: ChatGoogleGenerativeAI or Ollama via LangChain wrappers
- Simple in-memory caching (no Redis needed)
- Basic authentication (header-based API key)
- local in memory storage for simplicity (no complex DB needed)

## Stage Completion Status
- [x] **Stage 1:** Foundation & Architecture ✅ (Completed 2025-10-29)
- [x] **Stage 1.5:** Framework Refactoring (LangChain migration) ✅ (Completed 2025-10-29)
- [x] **Stage 2:** Backend API Development ✅ (Completed 2025-10-29)
- [ ] **Stage 3:** Database & ETL Pipeline
- [ ] **Stage 4:** Summarization Agent & LLM
- [ ] **Stage 5:** Frontend Development
- [ ] **Stage 6:** Testing & QA
- [ ] **Stage 7:** Documentation & Deployment

## Critical Files Created

### Stage 1 & 1.5:
- **ARCHITECTURE.md** - Complete system architecture with LangChain integration details
- **requirements.txt** - Dependencies with LangChain (sentence-transformers removed)
- **.env.example** - Environment configuration with LangChain variable mapping
- **src/agents/retrieval_agent.py** - Skeleton with LangChain imports and components
- **src/agents/summarizer_agent.py** - Skeleton with LangChain LLM components
- **src/config/logging_config.py** - Logging configuration
- **VENV_SETUP.md** - Virtual environment setup guide
- **.claude/decisions/stage-1.5-langchain-migration.md** - Migration decision document

### Stage 2:
- **src/api/main.py** - FastAPI application entry point with CORS, middleware, lifecycle
- **src/api/models.py** - Comprehensive Pydantic models for all requests/responses
- **src/api/middleware/auth.py** - API key authentication middleware
- **src/api/middleware/rate_limit.py** - In-memory rate limiting middleware
- **src/api/middleware/error_handler.py** - Global error handling with custom exceptions
- **src/api/routes/health.py** - Health check and metrics endpoints
- **src/api/routes/documents.py** - Document upload, list, detail, delete endpoints
- **src/api/routes/summarize.py** - Summarization endpoint with caching

## Known Issues / Blockers
None - Stages 1, 1.5, and 2 completed successfully

## Next Immediate Task
**Execute Stage 3: Database & ETL Pipeline**
- Set up Qdrant vector database
- Set up in-memory metadata storage
- Implement Retrieval Agent with LangChain (PyPDFLoader, embeddings, vector store)
- Implement CRUD operations
- Add retry logic and error handling
