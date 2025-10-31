# Instructions for Claude Code

## Your Mission
You are building a production-ready PDF summarization system with a 2-agent architecture. This is a multi-stage project (7 stages total + 1 refactoring stage).

## How You Work

### 1. Before Starting ANY Stage
**ALWAYS read these files first (in order):**
1. `.claude/PROJECT_CONTEXT.md` - Understand the overall project state
2. `.claude/STAGE_TRACKER.md` - Know what's been done and what's next
3. `.claude/PROMPT_SEQUENCE.md` - Read the specific prompt for current stage

### 2. While Working on a Stage
**Track your progress:**
- As you complete each deliverable, update the checkbox in `.claude/STAGE_TRACKER.md`
- If you make important architectural decisions, document them in `.claude/decisions/stage-X-decisions.md`
- If you encounter issues, note them in both STAGE_TRACKER.md and PROJECT_CONTEXT.md

### 3. After Completing a Stage
**Create a summary:**
- Create `.claude/progress/stage-X-summary.md` with:
  - What was built
  - Key decisions made
  - Files created/modified
  - Any issues encountered
  - What's ready for the next stage
- Update `.claude/PROJECT_CONTEXT.md`:
  - Mark the stage as complete (change ❌ to ✅)
  - Update "Current Stage" to next stage
  - Add key files to "Critical Files Created"
- Update `.claude/STAGE_TRACKER.md`:
  - Mark stage as complete with date
  - Ensure all checkboxes are ticked

### 4. Before Moving to Next Stage
**Verify your work:**
- Confirm all deliverables are complete
- Check that files actually exist and contain proper code
- Ensure documentation is updated
- Ask the user if they want to review before proceeding

## Core Principles (Follow These Always)

### Technical Philosophy
1. **Keep it SIMPLE** - No overengineering, no unnecessary complexity
2. **Function over form** - Working code beats perfect code
3. **Practical solutions** - Use straightforward approaches
4. **Clear code** - Readable and maintainable is better than clever

### Code Quality Standards
1. **Always use Python 3.12 type hints** (including return types)
2. **Add detailed docstrings** to all classes, functions, methods (Google/NumPy style)
3. **Follow PEP 8 strictly** 
4. **Use meaningful names** for variables and functions
5. **Keep functions small** (<50 lines)
6. **No hard-coded values** - use constants or config
7. **Proper error handling** - specific exceptions with context
8. **Comprehensive logging** - DEBUG, INFO, WARNING, ERROR levels

### Technology Stack (Do NOT deviate)
- **Python:** 3.12
- **Virtual Environment:** venv (always)
- **Embeddings:** Google Text-Embedding-004 (free, 768 dimensions)
- **LLM:** Google Gemini (free tier) OR Ollama llama3.2
- **Framework:** LangChain/LangGraph
- **Vector DB:** Qdrant with cosine similarity
- **Metadata:** local in memory storage
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Testing:** pytest

### Agent Architecture
**Agent 1 (Retrieval):**
- PDF loading with LangChain PyPDFLoader
- Text chunking with RecursiveCharacterTextSplitter (1000/200)
- Embeddings via Google Text-Embedding-004
- Vector storage in Qdrant
- Metadata in local in memory storage
- Semantic search returning top 3-5 chunks

**Agent 2 (Summarizer):**
- Context retrieval from Agent 1
- LLM summarization via LangChain
- Two modes: Brief (3-5 sentences) and Detailed (300-500 words)
- Token tracking and caching
- Page number citations

## Communication Style

### When Starting a Stage
Say something like:
"Starting Stage X. I've read the context files. Here's what I'll build: [brief summary]. I'll update the tracker as I progress."

### During Work
Provide periodic updates:
"Completed: [deliverable]. Moving to: [next deliverable]."

### When Completing a Stage
Say something like:
"Stage X complete! Summary created at .claude/progress/stage-X-summary.md. All deliverables checked off. Ready for Stage [X+1] or would you like to review first?"

### When You Need Clarification
Ask specific questions:
"Before implementing [X], I need clarification on: [specific question]"

### When You Encounter Issues
Be transparent:
"Encountered issue: [description]. Trying approach: [solution]. Will document in tracker."

## Special Instructions

### For Stage 1
- Create a clean, industry-standard directory structure
- Justify your structure choices in ARCHITECTURE.md

### For Stage 1.5 (Refactoring)
- Explain WHAT you're changing and WHY
- Show understanding of architectural impact
- Don't break existing structure

### For All Stages
- Update the tracker as you go (real-time)
- Keep the context files current
- Write clean, documented code
- Test as you build (when applicable)

## Files You Must Maintain

**Never modify these unless instructed:**
- `.claude/INSTRUCTIONS.md` (this file)
- `.claude/PROMPT_SEQUENCE.md` (the prompts)

**Update these regularly:**
- `.claude/PROJECT_CONTEXT.md` (after each stage)
- `.claude/STAGE_TRACKER.md` (during each stage)

**Create these as you work:**
- `.claude/progress/stage-X-summary.md` (after each stage)
- `.claude/decisions/stage-X-decisions.md` (when making key decisions)

## Remember
- You are autonomous but transparent
- You work systematically through stages
- You document everything you do
- You ask when uncertain
- You verify before moving on
- You keep it simple
