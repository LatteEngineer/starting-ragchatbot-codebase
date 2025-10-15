# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Course Materials RAG (Retrieval-Augmented Generation) system that enables semantic search and AI-powered Q&A over educational course content. The system uses ChromaDB for vector storage, Anthropic's Claude API with tool calling for AI generation, and provides a web-based chat interface.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Create .env file with required variables
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start from root
cd backend && uv run uvicorn app:app --reload --port 8000

# The app serves both API and frontend at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Python Version
- Requires Python 3.13+
- Uses `uv` package manager (not pip)

## Architecture Overview

### Core Design Pattern: Tool-Based RAG with Dual Claude API Calls

The system implements a sophisticated RAG pattern where Claude uses tools to search the knowledge base:

1. **First Claude API call**: Claude analyzes the query and decides whether to use the `search_course_content` tool
2. **Tool execution**: If needed, semantic search runs against ChromaDB
3. **Second Claude API call**: Claude synthesizes search results into a natural language answer

This dual-call pattern is implemented in `ai_generator.py:generate_response()` → `_handle_tool_execution()`.

### Data Flow Architecture

```
User Query → FastAPI → RAG System → AI Generator → Claude (1st call)
                ↓                                        ↓
         Session Manager                          Tool Decision
                                                         ↓
                                            Tool Manager → Vector Store
                                                         ↓
                                                  ChromaDB Search
                                                         ↓
                                            Claude (2nd call) → Response
```

### Component Responsibilities

**RAG System (`rag_system.py`)**: Central orchestrator that coordinates all components. Owns the document ingestion pipeline and query processing flow.

**AI Generator (`ai_generator.py`)**: Manages Claude API interactions. Implements the dual-call pattern for tool use. Contains the system prompt that instructs Claude on tool usage.

**Tool Manager (`search_tools.py`)**: Implements the tool abstraction layer. `CourseSearchTool` handles search execution and result formatting. Tracks sources for UI display.

**Vector Store (`vector_store.py`)**: ChromaDB wrapper with two collections:
- `course_catalog`: Course metadata for semantic course name resolution
- `course_content`: Chunked course content for semantic search

Three-stage search process: (1) resolve fuzzy course name via semantic search, (2) build metadata filters, (3) search content with filters.

**Document Processor (`document_processor.py`)**: Parses course documents with expected structure (Course Title/Link/Instructor headers, Lesson markers). Implements sentence-based chunking with overlap. Enriches chunks with contextual prefixes.

**Session Manager (`session_manager.py`)**: Manages conversation history. Stores last `MAX_HISTORY * 2` messages per session (default: 4 messages = 2 exchanges). History is injected into Claude's system prompt for context.

### Key Configuration (`backend/config.py`)

- `ANTHROPIC_MODEL`: `"claude-sonnet-4-20250514"` - The Claude model used
- `EMBEDDING_MODEL`: `"all-MiniLM-L6-v2"` - SentenceTransformer model for embeddings
- `CHUNK_SIZE`: 800 characters - Size of text chunks
- `CHUNK_OVERLAP`: 100 characters - Overlap between chunks
- `MAX_RESULTS`: 5 - Number of search results returned
- `MAX_HISTORY`: 2 - Number of conversation exchanges to remember (4 messages total)
- `CHROMA_PATH`: `"./chroma_db"` - Vector database location (in backend/)

### Document Format Requirements

Course documents must follow this structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [lesson url]
[lesson content...]

Lesson 1: [next lesson]
...
```

Documents are placed in `docs/` folder. The system automatically loads them on startup (`app.py:on_event("startup")`).

### Frontend Integration

The frontend (`frontend/`) is served as static files by FastAPI (`app.py:119`). It's a vanilla JavaScript SPA that:
- Maintains session state via `currentSessionId`
- Sends queries to `/api/query` with session ID
- Renders markdown responses using `marked.js`
- Displays collapsible sources returned from search

## Important Implementation Details

### Session Management
- Sessions are created on first query if no `session_id` provided
- Session IDs follow format: `session_N` where N is incrementing counter
- History is formatted as "User: ...\nAssistant: ..." and prepended to system prompt

### Tool Calling Flow
- Tool definitions are registered in `RAGSystem.__init__()` via `ToolManager`
- Claude receives tool schema in first API call
- On `stop_reason="tool_use"`, `_handle_tool_execution()` processes tool calls
- Tool results are added to message history as `role="user"` with `type="tool_result"`
- Second API call omits tools to force synthesis (no tool loop)

### Vector Search Behavior
- Fuzzy course name matching: "Prompt Caching" finds "Introduction to Prompt Caching with Anthropic"
- Course name resolution uses semantic search on `course_catalog` collection
- Content search applies filters for `course_title` and optionally `lesson_number`
- Returns top `MAX_RESULTS` chunks with metadata

### Chunk Context Enrichment
- First chunk of each lesson: `"Lesson {N} content: {chunk}"`
- Last lesson's chunks: `"Course {title} Lesson {N} content: {chunk}"`
- This improves retrieval accuracy by adding explicit context

### Incremental Document Loading
- `add_course_folder()` checks `get_existing_course_titles()` to avoid duplicates
- Course title is used as unique identifier
- Set `clear_existing=True` to force rebuild of vector store

## Modifying the System

### Adding New Tools
1. Create a class implementing `Tool` protocol in `search_tools.py`
2. Implement `get_tool_definition()` returning Anthropic tool schema
3. Implement `execute(**kwargs)` with tool logic
4. Register in `RAGSystem.__init__()`: `self.tool_manager.register_tool(YourTool(...))`

### Changing Search Behavior
- Modify `VectorStore.search()` for query logic changes
- Adjust `CourseSearchTool._format_results()` for output format
- Update `MAX_RESULTS` in `config.py` for more/fewer results

### Adjusting AI Behavior
- Edit `AIGenerator.SYSTEM_PROMPT` for instruction changes
- Modify `temperature` or `max_tokens` in `ai_generator.py:base_params`
- Change `MAX_HISTORY` in `config.py` for longer/shorter conversation memory

### Supporting New Document Formats
- Extend `DocumentProcessor.process_course_document()` with new parsing logic
- Modify regex patterns for different header formats
- Update `chunk_text()` for different chunking strategies
- always use uv to run the server do not use pip directly
- make sure to use uv to manage all dependencies
- use uv to run Python files