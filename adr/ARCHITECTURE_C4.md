# C4 Architecture Documentation

This document describes the Course Materials RAG System architecture using the C4 model (Context, Container, Component, and Code diagrams).

## Level 1: System Context Diagram

Shows how the system fits into the world around it.

```mermaid
C4Context
    title System Context Diagram - Course Materials RAG System

    Person(user, "Course Student", "A person learning from online courses who needs to find information in course materials")

    System(rag_system, "Course Materials RAG System", "Enables semantic search and AI-powered Q&A over educational course content using RAG")

    System_Ext(anthropic, "Anthropic API", "Claude AI service for natural language understanding and generation with tool calling")
    System_Ext(chromadb, "ChromaDB", "Vector database for semantic search over course content embeddings")

    Rel(user, rag_system, "Asks questions about courses", "HTTPS")
    Rel(rag_system, anthropic, "Requests AI responses with tool use", "HTTPS/JSON")
    Rel(rag_system, chromadb, "Stores and retrieves course embeddings", "Local/Python API")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Key Context Elements

- **User**: Course students who need quick answers about course content
- **RAG System**: The main application providing intelligent search and Q&A
- **Anthropic API**: External Claude AI service for natural language processing
- **ChromaDB**: Embedded vector database for semantic search

---

## Level 2: Container Diagram

Shows the high-level technical building blocks.

```mermaid
C4Container
    title Container Diagram - Course Materials RAG System

    Person(user, "Course Student", "A person learning from online courses")

    Container_Boundary(rag_boundary, "Course Materials RAG System") {
        Container(spa, "Web Application", "HTML/CSS/JavaScript", "Provides chat interface for querying course materials. Uses marked.js for markdown rendering")
        Container(api, "API Application", "Python/FastAPI", "Handles HTTP requests, orchestrates RAG pipeline, manages sessions")
        Container(vector_store, "Vector Store", "ChromaDB + SentenceTransformers", "Stores course embeddings in two collections: course_catalog and course_content")
    }

    System_Ext(anthropic, "Anthropic Claude API", "AI service for response generation with tool calling")
    ContainerDb(filesystem, "File System", "docs/", "Stores course documents (TXT, PDF, DOCX)")

    Rel(user, spa, "Interacts with", "HTTPS")
    Rel(spa, api, "Makes API calls to", "JSON/HTTPS")
    Rel(api, anthropic, "Sends queries and tool definitions", "HTTPS/JSON")
    Rel(api, vector_store, "Queries embeddings", "Python API")
    Rel(api, filesystem, "Loads course documents", "File I/O")
    Rel(vector_store, filesystem, "Persists vector data", "File I/O")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Container Descriptions

**Web Application (Frontend)**
- Technology: Vanilla JavaScript, HTML5, CSS3
- Purpose: Single-page chat interface
- Key Features: Session management, markdown rendering, source display

**API Application (Backend)**
- Technology: Python 3.13, FastAPI, Uvicorn
- Purpose: HTTP API and RAG orchestration
- Key Features: Query processing, document ingestion, session tracking

**Vector Store**
- Technology: ChromaDB 1.0.15, SentenceTransformers (all-MiniLM-L6-v2)
- Purpose: Semantic search over course embeddings
- Key Features: Dual collections, filtered search, fuzzy course matching

---

## Level 3: Component Diagram

Shows the internal components of the API Application container.

```mermaid
C4Component
    title Component Diagram - API Application (Backend)

    Container_Boundary(api_boundary, "API Application") {
        Component(fastapi, "FastAPI Router", "FastAPI", "HTTP endpoints: /api/query, /api/courses. Serves static frontend files")
        Component(rag_system, "RAG System", "Python Class", "Central orchestrator: coordinates document processing, query flow, and all components")
        Component(ai_generator, "AI Generator", "Python Class", "Manages Claude API interactions. Implements dual-call pattern for tool use")
        Component(tool_manager, "Tool Manager", "Python Class", "Manages available tools. Routes tool execution requests")
        Component(search_tool, "Course Search Tool", "Python Class", "Executes semantic search. Formats results with context. Tracks sources")
        Component(vector_store, "Vector Store", "Python Class", "ChromaDB wrapper. Two collections: course_catalog (metadata), course_content (chunks)")
        Component(doc_processor, "Document Processor", "Python Class", "Parses course documents. Implements sentence-based chunking with overlap")
        Component(session_mgr, "Session Manager", "Python Class", "Manages conversation history. Stores last N exchanges per session")
        Component(models, "Data Models", "Pydantic", "Course, Lesson, CourseChunk, QueryRequest, QueryResponse")
        Component(config, "Configuration", "Python Dataclass", "System settings: API keys, chunk size, model names, limits")
    }

    System_Ext(anthropic, "Anthropic Claude API")
    ContainerDb(chromadb, "ChromaDB")
    ContainerDb(filesystem, "File System")

    Rel(fastapi, rag_system, "Routes queries to")
    Rel(rag_system, session_mgr, "Gets/updates conversation history")
    Rel(rag_system, ai_generator, "Sends query with history and tools")
    Rel(rag_system, doc_processor, "Uses for document ingestion")
    Rel(rag_system, tool_manager, "Gets tool definitions from")

    Rel(ai_generator, anthropic, "Makes dual API calls", "HTTPS")
    Rel(ai_generator, tool_manager, "Executes tools via")

    Rel(tool_manager, search_tool, "Routes search requests to")
    Rel(search_tool, vector_store, "Queries via")

    Rel(vector_store, chromadb, "Reads/writes embeddings", "Python API")
    Rel(doc_processor, vector_store, "Adds processed chunks to")
    Rel(doc_processor, filesystem, "Reads course files from")

    Rel(fastapi, config, "Reads settings")
    Rel(rag_system, config, "Uses for initialization")
    Rel_Back(models, fastapi, "Used by")
    Rel_Back(models, rag_system, "Used by")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Component Responsibilities

**FastAPI Router** (`app.py`)
- Exposes REST endpoints
- Validates requests with Pydantic models
- Serves static frontend files
- Loads initial documents on startup

**RAG System** (`rag_system.py`)
- Central orchestrator for all operations
- Manages document ingestion pipeline
- Coordinates query processing flow
- Owns component lifecycle

**AI Generator** (`ai_generator.py`)
- Implements dual Claude API call pattern
- First call: Claude decides to use tools
- Second call: Claude synthesizes results
- Manages system prompt and conversation history

**Tool Manager** (`search_tools.py`)
- Abstract tool registration system
- Routes tool execution by name
- Collects and resets sources for UI

**Course Search Tool** (`search_tools.py`)
- Implements semantic search logic
- Formats results with course/lesson context
- Tracks sources for frontend display

**Vector Store** (`vector_store.py`)
- Wraps ChromaDB with two collections
- Three-stage search: resolve course → build filter → search content
- Supports fuzzy course name matching
- Manages embeddings lifecycle

**Document Processor** (`document_processor.py`)
- Parses structured course documents
- Extracts metadata (title, instructor, lessons)
- Implements sentence-based chunking
- Enriches chunks with contextual prefixes

**Session Manager** (`session_manager.py`)
- Creates and tracks conversation sessions
- Stores message history (max N exchanges)
- Formats history for system prompt injection

---

## Level 4: Code Diagram - Query Processing Flow

Shows the detailed interaction for processing a user query.

```mermaid
sequenceDiagram
    autonumber

    participant Client as Frontend<br/>(script.js)
    participant API as FastAPI<br/>(app.py)
    participant RAG as RAGSystem<br/>(rag_system.py)
    participant Session as SessionManager<br/>(session_manager.py)
    participant AI as AIGenerator<br/>(ai_generator.py)
    participant Claude as Anthropic API
    participant Tools as ToolManager<br/>(search_tools.py)
    participant Search as CourseSearchTool<br/>(search_tools.py)
    participant Vector as VectorStore<br/>(vector_store.py)
    participant DB as ChromaDB

    Client->>API: POST /api/query<br/>{query, session_id}
    API->>API: Validate QueryRequest
    API->>RAG: query(query, session_id)

    RAG->>Session: get_conversation_history(session_id)
    Session-->>RAG: formatted_history or None

    RAG->>Tools: get_tool_definitions()
    Tools-->>RAG: [search_course_content schema]

    RAG->>AI: generate_response(query, history, tools, tool_manager)

    Note over AI: Build system prompt + history
    AI->>Claude: messages.create()<br/>messages: [{role: "user", content: query}]<br/>system: SYSTEM_PROMPT + history<br/>tools: [search_course_content]<br/>temperature: 0, max_tokens: 800

    Note over Claude: Analyzes query,<br/>decides to use tool
    Claude-->>AI: Response<br/>stop_reason: "tool_use"<br/>content: [{type: "tool_use", name: "search_course_content",<br/>input: {query, course_name, lesson_number}}]

    AI->>AI: _handle_tool_execution(response, params, tool_manager)

    loop For each tool_use in response.content
        AI->>Tools: execute_tool(name, **input)
        Tools->>Search: execute(query, course_name, lesson_number)

        Search->>Vector: search(query, course_name, lesson_number)

        Note over Vector: Stage 1: Resolve Course Name
        Vector->>DB: course_catalog.query(course_name, n_results=1)
        DB-->>Vector: Best matching course title

        Note over Vector: Stage 2: Build Filter
        Vector->>Vector: _build_filter(course_title, lesson_number)<br/>Returns: {"$and": [{"course_title": ...}, {"lesson_number": ...}]}

        Note over Vector: Stage 3: Content Search
        Vector->>DB: course_content.query(query_texts=[query],<br/>n_results=MAX_RESULTS, where=filter_dict)
        DB-->>Vector: {documents: [...], metadatas: [...], distances: [...]}

        Vector-->>Search: SearchResults(documents, metadata, distances)

        Search->>Search: _format_results(results)<br/>Add [Course - Lesson N] headers<br/>Track sources in last_sources
        Search-->>Tools: formatted_string

        Tools-->>AI: tool_result_content

        AI->>AI: Build tool_results list<br/>[{type: "tool_result", tool_use_id, content}]
    end

    AI->>AI: Append messages:<br/>[assistant: tool_use response, user: tool_results]

    Note over AI: Second Claude call (synthesis)
    AI->>Claude: messages.create()<br/>messages: [user query, assistant tool_use, user tool_results]<br/>system: same prompt<br/>NO TOOLS

    Note over Claude: Synthesizes final answer<br/>from search results
    Claude-->>AI: Response<br/>stop_reason: "end_turn"<br/>content: [{type: "text", text: "Natural language answer"}]

    AI-->>RAG: response_text

    RAG->>Tools: get_last_sources()
    Tools->>Search: return last_sources
    Search-->>Tools: ["Course - Lesson 2", "Course - Lesson 3", ...]
    Tools-->>RAG: sources list

    RAG->>Tools: reset_sources()

    RAG->>Session: add_exchange(session_id, query, response)
    Session->>Session: Append messages, trim to max_history * 2

    RAG-->>API: (response, sources)

    API->>API: Build QueryResponse<br/>{answer, sources, session_id}
    API-->>Client: 200 OK<br/>JSON response

    Client->>Client: Remove loading spinner<br/>Render markdown answer<br/>Display collapsible sources
```

### Key Code-Level Patterns

**Dual Claude API Call Pattern**
1. First call includes tools → Claude returns `stop_reason="tool_use"`
2. Tool execution → Results added to message history
3. Second call without tools → Forces synthesis → Returns `stop_reason="end_turn"`

**Three-Stage Vector Search**
1. Fuzzy course name resolution via semantic search on `course_catalog`
2. Filter construction from resolved course title and lesson number
3. Content search on `course_content` with filters and embeddings

**Message History Management**
1. History retrieved before each query
2. Formatted as "User: ...\nAssistant: ..." string
3. Appended to system prompt
4. Updated after response with new exchange
5. Trimmed to `max_history * 2` messages

**Source Tracking**
1. Sources captured during `_format_results()` in `CourseSearchTool`
2. Stored in instance variable `last_sources`
3. Retrieved by RAG system via `ToolManager.get_last_sources()`
4. Reset after retrieval to avoid contamination

---

## Level 4: Code Diagram - Document Ingestion Flow

Shows the detailed process of adding course documents to the system.

```mermaid
sequenceDiagram
    autonumber

    participant Startup as app.py<br/>startup_event()
    participant RAG as RAGSystem<br/>(rag_system.py)
    participant DocProc as DocumentProcessor<br/>(document_processor.py)
    participant Vector as VectorStore<br/>(vector_store.py)
    participant DB as ChromaDB
    participant FS as File System

    Startup->>Startup: Check if docs/ exists
    Startup->>RAG: add_course_folder("../docs", clear_existing=False)

    RAG->>Vector: get_existing_course_titles()
    Vector->>DB: course_catalog.get()<br/>Returns all IDs
    DB-->>Vector: {ids: ["Course A", "Course B", ...]}
    Vector-->>RAG: existing_titles set

    RAG->>FS: os.listdir("../docs")
    FS-->>RAG: [course1_script.txt, course2_script.txt, ...]

    loop For each file in docs/
        RAG->>RAG: Check extension (.pdf, .docx, .txt)

        RAG->>DocProc: process_course_document(file_path)

        DocProc->>FS: read_file(file_path)
        FS-->>DocProc: file_content (UTF-8)

        Note over DocProc: Parse metadata (lines 1-3)
        DocProc->>DocProc: Extract:<br/>- Course Title: ...<br/>- Course Link: ...<br/>- Course Instructor: ...

        DocProc->>DocProc: Create Course object<br/>(title, course_link, instructor)

        Note over DocProc: Parse lessons (line 4+)
        loop For each line in content
            alt Line matches "Lesson N: Title"
                DocProc->>DocProc: Process previous lesson if exists:<br/>- chunk_text(lesson_content)<br/>- Create CourseChunk objects<br/>- Add context prefix
                DocProc->>DocProc: Start new lesson:<br/>- Extract lesson_number, title<br/>- Check next line for "Lesson Link:"
            else Regular content line
                DocProc->>DocProc: Append to lesson_content
            end
        end

        Note over DocProc: Process final lesson
        DocProc->>DocProc: chunk_text(lesson_content)

        Note over DocProc: Sentence-based chunking
        DocProc->>DocProc: Split into sentences (regex)<br/>Build chunks up to CHUNK_SIZE<br/>Add CHUNK_OVERLAP sentences

        DocProc->>DocProc: Create CourseChunk objects:<br/>- content (with context prefix)<br/>- course_title<br/>- lesson_number<br/>- chunk_index

        DocProc-->>RAG: (course, course_chunks)

        alt Course title not in existing_titles
            RAG->>Vector: add_course_metadata(course)

            Vector->>Vector: Build metadata:<br/>{title, instructor, course_link,<br/>lessons_json, lesson_count}
            Vector->>DB: course_catalog.add(<br/>documents=[course.title],<br/>metadatas=[metadata],<br/>ids=[course.title])

            RAG->>Vector: add_course_content(course_chunks)

            Vector->>Vector: Extract:<br/>- documents: [chunk.content]<br/>- metadatas: [{course_title, lesson_number, chunk_index}]<br/>- ids: ["{course_title}_{chunk_index}"]

            Vector->>DB: course_content.add(<br/>documents, metadatas, ids)
            DB->>DB: Generate embeddings<br/>(SentenceTransformer)
            DB->>DB: Store vectors

            RAG->>RAG: Increment total_courses, total_chunks<br/>Add to existing_titles
        else Course already exists
            RAG->>RAG: Log: "Course already exists - skipping"
        end
    end

    RAG-->>Startup: (total_courses_added, total_chunks_created)
    Startup->>Startup: Log: "Loaded N courses with M chunks"
```

### Document Processing Details

**File Format Parsing**
- Line 1: `Course Title: [title]`
- Line 2: `Course Link: [url]`
- Line 3: `Course Instructor: [name]`
- Line 4+: `Lesson N: [title]` markers followed by content

**Chunking Strategy**
- Sentence-based splitting using regex: `(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])`
- Builds chunks up to `CHUNK_SIZE` (800 chars) without breaking sentences
- Adds `CHUNK_OVERLAP` (100 chars) by including sentences from previous chunk
- Ensures smooth semantic continuity between chunks

**Context Enrichment**
- First chunk of lesson: `"Lesson {N} content: {chunk}"`
- Last lesson chunks: `"Course {title} Lesson {N} content: {chunk}"`
- Improves retrieval by adding explicit context markers

**Duplicate Prevention**
- Queries existing course titles before processing
- Compares parsed course title against existing set
- Skips processing if match found
- Uses course title as unique identifier

---

## Data Model

```mermaid
classDiagram
    class Course {
        +string title
        +string course_link
        +string instructor
        +List~Lesson~ lessons
    }

    class Lesson {
        +int lesson_number
        +string title
        +string lesson_link
    }

    class CourseChunk {
        +string content
        +string course_title
        +int lesson_number
        +int chunk_index
    }

    class QueryRequest {
        +string query
        +string session_id
    }

    class QueryResponse {
        +string answer
        +List~string~ sources
        +string session_id
    }

    class SearchResults {
        +List~string~ documents
        +List~Dict~ metadata
        +List~float~ distances
        +string error
        +is_empty() bool
    }

    class Message {
        +string role
        +string content
    }

    Course "1" --> "*" Lesson : contains
    Course "1" --> "*" CourseChunk : generates
    Lesson "1" --> "*" CourseChunk : source of

    QueryRequest ..> QueryResponse : produces
    SearchResults ..> QueryResponse : influences
```

---

## Key Architectural Decisions

### ADR-001: Tool-Based RAG with Dual Claude API Calls

**Context**: Need to leverage Claude's reasoning to decide when to search vs. answer directly.

**Decision**: Use Claude's tool calling feature with a two-call pattern:
1. First call: Claude analyzes query and decides whether to use search tool
2. Second call: Claude synthesizes search results into natural language

**Consequences**:
- **Positive**: Claude can answer general questions without search, reducing unnecessary vector queries
- **Positive**: Claude's reasoning improves search query formulation
- **Negative**: Increased latency (two API calls)
- **Negative**: Higher API costs (two Claude invocations per query)

### ADR-002: Dual ChromaDB Collections

**Context**: Need to support both course-level discovery and content-level search.

**Decision**: Maintain two separate collections:
- `course_catalog`: Course metadata for fuzzy course name matching
- `course_content`: Chunked content for semantic search

**Consequences**:
- **Positive**: Fuzzy course name matching ("Prompt Caching" → "Intro to Prompt Caching with Anthropic")
- **Positive**: Efficient filtering by resolved course name
- **Negative**: Two separate indexing operations during ingestion
- **Negative**: Increased storage overhead

### ADR-003: Sentence-Based Chunking with Overlap

**Context**: Need to balance chunk size for embedding quality vs. context preservation.

**Decision**: Use sentence-aware chunking with 800 character chunks and 100 character overlap.

**Consequences**:
- **Positive**: Chunks don't break mid-sentence, preserving semantic meaning
- **Positive**: Overlap ensures important information at chunk boundaries isn't lost
- **Negative**: More chunks than fixed-size chunking (increased storage)
- **Negative**: Complex chunking logic with sentence detection

### ADR-004: Context Enrichment for Chunks

**Context**: Vector search may return chunks without sufficient context about their source.

**Decision**: Prepend contextual information to chunks:
- `"Lesson {N} content: {chunk}"` for lesson starts
- `"Course {title} Lesson {N} content: {chunk}"` for later chunks

**Consequences**:
- **Positive**: Improved retrieval accuracy (embeddings include course/lesson context)
- **Positive**: Claude receives explicit source context in search results
- **Negative**: Increased chunk size and embedding computation
- **Negative**: Potential bias toward chunks with rich prefixes

### ADR-005: Session-Based Conversation History

**Context**: Users may ask follow-up questions requiring previous context.

**Decision**: Store last `MAX_HISTORY` exchanges per session, inject into system prompt.

**Consequences**:
- **Positive**: Supports multi-turn conversations
- **Positive**: Claude can reference previous answers
- **Negative**: Increased prompt size (context window usage)
- **Negative**: Session state must be managed (memory overhead)

---

## Deployment View

```mermaid
C4Deployment
    title Deployment Diagram - Local Development

    Deployment_Node(dev_machine, "Developer Machine", "macOS/Linux/Windows") {
        Deployment_Node(browser, "Web Browser", "Chrome/Firefox/Safari") {
            Container(spa, "Web Application", "JavaScript/HTML/CSS", "Chat interface")
        }

        Deployment_Node(python_runtime, "Python Runtime", "Python 3.13 + uv") {
            Container(fastapi, "FastAPI Application", "Uvicorn", "API server on port 8000")
        }

        Deployment_Node(storage, "Local Storage", "File System") {
            ContainerDb(chromadb, "ChromaDB", "chroma_db/", "Vector database files")
            ContainerDb(docs, "Course Documents", "docs/", "TXT/PDF/DOCX files")
            ContainerDb(env, "Environment Config", ".env", "API keys and settings")
        }
    }

    Deployment_Node(cloud, "Anthropic Cloud", "AWS") {
        Container(claude_api, "Claude API", "claude-sonnet-4", "AI service")
    }

    Rel(spa, fastapi, "HTTPS requests", "localhost:8000")
    Rel(fastapi, chromadb, "Python API calls")
    Rel(fastapi, docs, "File I/O")
    Rel(fastapi, env, "Reads config")
    Rel(fastapi, claude_api, "HTTPS/JSON", "api.anthropic.com")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Deployment Notes

**Local Development**:
- Single machine deployment
- Frontend served as static files by FastAPI
- ChromaDB runs embedded (no separate server)
- Environment variables in `.env` file

**Production Considerations** (not implemented):
- Separate frontend hosting (CDN)
- Persistent vector database (external ChromaDB server)
- API key management (secrets manager)
- Horizontal scaling requires session state externalization
- Rate limiting and authentication not implemented

---

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Vanilla JavaScript | ES6+ | UI logic and API client |
| | HTML5/CSS3 | - | Page structure and styling |
| | marked.js | - | Markdown rendering |
| **Backend** | Python | 3.13+ | Application runtime |
| | FastAPI | 0.116.1 | Web framework and API |
| | Uvicorn | 0.35.0 | ASGI server |
| | Pydantic | - | Data validation |
| **AI/ML** | Anthropic API | 0.58.2 | Claude AI integration |
| | SentenceTransformers | 5.0.0 | Embedding generation |
| | Model: all-MiniLM-L6-v2 | - | 384-dim embeddings |
| **Database** | ChromaDB | 1.0.15 | Vector database |
| **Build** | uv | - | Python package manager |
| **Config** | python-dotenv | 1.1.1 | Environment variables |

---

## Glossary

**RAG (Retrieval-Augmented Generation)**: Pattern where LLM responses are enhanced with retrieved context from a knowledge base.

**Tool Calling**: Claude API feature allowing the model to request execution of predefined functions.

**Embedding**: Vector representation of text that captures semantic meaning (384 dimensions in this system).

**Semantic Search**: Finding similar content based on meaning rather than keyword matching.

**Chunk**: Fixed-size text segment created from larger documents for vector storage.

**Session**: Conversation context tracked across multiple query-response exchanges.

**Course Catalog**: ChromaDB collection storing course metadata for fuzzy name matching.

**Course Content**: ChromaDB collection storing chunked course text with embeddings.

**System Prompt**: Instructions given to Claude defining its behavior and capabilities.

**Stop Reason**: Claude API response field indicating why generation stopped (e.g., "tool_use", "end_turn").
