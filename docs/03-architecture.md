# System Architecture Document

> **Role**: Architect
> **Created**: 2025-12-04
> **Updated**: 2025-12-04
> **Version**: 1.1

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```mermaid
flowchart TB
    subgraph Presentation["🖥️ Presentation Layer"]
        UI[Streamlit Web UI]
    end

    subgraph Application["⚙️ Application Layer"]
        SS[Search Service]
        IS[Ingestion Service]
        HR[Hybrid Ranker]
    end

    subgraph Data["💾 Data Layer"]
        Chroma[(Chroma DB<br/>Vector Storage)]
        BM25[(BM25 Index<br/>Keyword Search)]
    end

    subgraph External["🌐 External Services"]
        Storm[Storm Parse API<br/>Document Parsing]
        OpenAI[OpenAI API<br/>Embeddings]
    end

    UI --> SS
    SS --> HR
    HR --> Chroma
    HR --> BM25

    IS --> Storm
    Storm --> IS
    IS --> OpenAI
    OpenAI --> IS
    IS --> Chroma
    IS --> BM25
```

### 1.2 Deployment Architecture

```mermaid
flowchart TB
    subgraph Internet["🌐 Internet"]
        Browser[Browser Client]
    end

    subgraph OCI["☁️ Oracle Cloud Infrastructure<br/>ARM Free Tier"]
        subgraph Docker["🐳 Docker Compose"]
            Nginx[Nginx<br/>Reverse Proxy<br/>SSL + Auth]
            App[bookbrain-app<br/>Python 3.12<br/>Streamlit]
            ChromaDB[bookbrain-chroma<br/>Chroma Server]
        end

        subgraph Storage["📦 Volumes"]
            Vol1[(chroma_data)]
            Vol2[(app_data)]
        end
    end

    Browser -->|HTTPS:443| Nginx
    Nginx -->|:8501| App
    App -->|:8000| ChromaDB
    ChromaDB --> Vol1
    App --> Vol2
```

### 1.3 Security Architecture

```mermaid
flowchart LR
    subgraph Security["🔒 Security Layers"]
        L1[Layer 1<br/>Oracle Security Group<br/>Port Whitelist]
        L2[Layer 2<br/>Nginx Basic Auth<br/>Username/Password]
        L3[Layer 3<br/>HTTPS/TLS 1.3<br/>Let's Encrypt]
    end

    User[User] --> L3 --> L2 --> L1 --> App[Application]
```

---

## 2. Component Design

### 2.1 Ingestion Pipeline

```mermaid
flowchart LR
    subgraph Input["📁 Input"]
        PDF[PDF Files]
    end

    subgraph Parsing["📄 Document Parsing"]
        Upload[Upload to<br/>Storm Parse API]
        Poll[Poll for<br/>Result]
        Parse[Parsed<br/>Markdown]
    end

    subgraph Processing["⚙️ Processing"]
        Chunk[Text Chunker<br/>800 tokens]
        Embed[Embedding<br/>Generator]
    end

    subgraph Storage["💾 Storage"]
        Chroma[(Chroma DB)]
        BM25[(BM25 Index)]
    end

    PDF --> Upload --> Poll --> Parse
    Parse --> Chunk --> Embed
    Embed --> Chroma
    Chunk --> BM25
```

#### Storm Parse API Integration

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Storm Parse API

    C->>S: POST /api/v2/parse/by-file<br/>(PDF + language=ko)
    S-->>C: { jobId, state: "REQUESTED" }

    loop Poll until COMPLETED
        C->>S: GET /api/v2/parse/job/{jobId}
        S-->>C: { state, pages? }
    end

    Note over C,S: state: REQUESTED → ACCEPTED → PROCESSED → COMPLETED

    S-->>C: { state: "COMPLETED", pages: [...] }
```

#### Process Flow Detail

1. **PDF Upload**
   - Input: PDF 파일 경로
   - API: Storm Parse `/api/v2/parse/by-file`
   - Output: jobId

2. **Result Polling**
   - API: Storm Parse `/api/v2/parse/job/{jobId}`
   - States: REQUESTED → ACCEPTED → PROCESSED → COMPLETED
   - Output: Structured markdown per page

3. **Metadata Extraction**
   ```python
   metadata = {
       "book_title": "파일명에서 추출",
       "book_file": "원본 파일명",
       "page_number": "API 응답에서 추출",
       "chapter": "### 패턴으로 추출"
   }
   ```

4. **Text Chunking**
   - Strategy: `RecursiveCharacterTextSplitter`
   - Chunk Size: 800 tokens (약 1600자 한글)
   - Chunk Overlap: 200 tokens (약 400자)
   - Separators: `["\n\n", "\n", "```", ". ", " "]`

5. **Embedding Generation**
   - Model: `text-embedding-3-small` (OpenAI)
   - Dimension: 1536
   - Batch Size: 100 chunks per request

6. **Storage**
   - Chroma: Vector + Metadata
   - BM25 Index: pickle 파일로 저장

### 2.2 Search Engine

```mermaid
flowchart TB
    Query[User Query] --> QE[Query Embedding<br/>OpenAI]
    Query --> QT[Query Tokenizer]

    QE --> VS[Vector Search<br/>Chroma]
    QT --> BS[BM25 Search]

    VS --> |Top-K Results| RRF[RRF Fusion<br/>Reciprocal Rank Fusion]
    BS --> |Top-K Results| RRF

    RRF --> Results[Final Ranked Results]
```

#### Hybrid Scoring: Reciprocal Rank Fusion

```mermaid
flowchart LR
    subgraph Vector["Vector Results"]
        V1["#1: Doc A (0.95)"]
        V2["#2: Doc C (0.87)"]
        V3["#3: Doc B (0.82)"]
    end

    subgraph BM25["BM25 Results"]
        B1["#1: Doc B (12.5)"]
        B2["#2: Doc A (10.2)"]
        B3["#3: Doc D (8.1)"]
    end

    subgraph RRF["RRF Calculation"]
        direction TB
        R1["Doc A: 1/(60+1) + 1/(60+2) = 0.0327"]
        R2["Doc B: 1/(60+3) + 1/(60+1) = 0.0323"]
        R3["Doc C: 1/(60+2) = 0.0161"]
        R4["Doc D: 1/(60+3) = 0.0159"]
    end

    subgraph Final["Final Ranking"]
        F1["#1: Doc A ✓"]
        F2["#2: Doc B"]
        F3["#3: Doc C"]
    end

    Vector --> RRF
    BM25 --> RRF
    RRF --> Final
```

**RRF 공식**:
```
score(d) = Σ 1 / (k + rank(d))
```
- k = 60 (기본 상수)
- 스케일이 다른 점수를 랭킹 기반으로 통합

### 2.3 UI Components

```mermaid
flowchart TB
    subgraph App["Streamlit App"]
        Main[app.py<br/>Main Entry]

        subgraph Components["Components"]
            SB[SearchBar]
            SO[SearchOptions]
            RC[ResultCard]
            SD[Sidebar]
        end

        subgraph State["Session State"]
            History[search_history]
            Results[current_results]
            Settings[settings]
        end
    end

    Main --> Components
    Components --> State
```

---

## 3. Data Flow

### 3.1 Ingestion Data Flow

```mermaid
sequenceDiagram
    participant PDF as PDF Files
    participant Ing as Ingestion Service
    participant Storm as Storm Parse API
    participant OAI as OpenAI API
    participant DB as Chroma + BM25

    PDF->>Ing: Read PDF files

    loop For each PDF
        Ing->>Storm: Upload PDF
        Storm-->>Ing: jobId

        loop Poll
            Ing->>Storm: Get job status
            Storm-->>Ing: status + pages
        end

        Ing->>Ing: Extract metadata
        Ing->>Ing: Chunk text (800 tokens)

        Ing->>OAI: Embed chunks (batch)
        OAI-->>Ing: Vectors

        Ing->>DB: Store vectors + metadata
    end

    Ing->>Ing: Build BM25 index
    Ing->>DB: Save BM25 index
```

### 3.2 Search Data Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant Search as Search Service
    participant OAI as OpenAI API
    participant Chroma as Chroma DB
    participant BM25 as BM25 Index

    User->>UI: Enter query
    UI->>Search: Search request

    par Vector Search
        Search->>OAI: Embed query
        OAI-->>Search: Query vector
        Search->>Chroma: Similarity search
        Chroma-->>Search: Top-K results
    and BM25 Search
        Search->>BM25: Keyword search
        BM25-->>Search: Top-K results
    end

    Search->>Search: RRF Fusion
    Search->>Search: Highlight text
    Search-->>UI: Ranked results
    UI-->>User: Display results
```

---

## 4. Technical Decisions

### 4.1 Document Parsing: Storm Parse API

| 고려 옵션 | 장점 | 단점 | 선택 |
|----------|------|------|------|
| **Storm Parse API** | VLM 기반, 구조 인식 우수, 한글 지원 | API 비용 | ✅ |
| PyMuPDF/pdfplumber | 무료, 로컬 처리 | 레이아웃 인식 약함 | - |
| Upstage Document AI | 한국 기업, 한글 최적화 | Storm 대비 검증 필요 | 백업 |

### 4.2 Embedding Model Selection

| Model | Dimension | 한글 성능 | 코드 성능 | 비용 | 선택 |
|-------|-----------|----------|----------|------|------|
| text-embedding-3-small | 1536 | Good | Good | $0.02/1M | ✅ |
| text-embedding-3-large | 3072 | Better | Better | $0.13/1M | - |
| multilingual-e5-large | 1024 | Good | Medium | Free | 백업 |

**결정**: `text-embedding-3-small`
- 이유: 비용 효율, 충분한 품질, 한글+코드 혼합 지원

### 4.3 Chunking Strategy

```python
CHUNK_CONFIG = {
    "chunk_size": 800,        # 토큰 (약 1600자 한글)
    "chunk_overlap": 200,     # 토큰 (약 400자)
    "separators": [
        "\n\n",               # 단락 구분
        "\n",                 # 줄바꿈
        "```",                # 코드 블록
        ". ",                 # 문장 끝
        " ",                  # 단어
    ],
    "length_function": "tiktoken",
}
```

### 4.4 BM25 vs Elasticsearch

| Aspect | rank_bm25 | Elasticsearch |
|--------|-----------|---------------|
| 설치 | pip install | 별도 서버 |
| 리소스 | 낮음 (인메모리) | 높음 |
| 확장성 | 낮음 | 높음 |
| 복잡도 | 낮음 | 높음 |

**결정**: `rank_bm25`
- 이유: 개인 프로젝트 규모에 적합, Oracle Free Tier 리소스 고려

---

## 5. Scalability & Future

### 5.1 Current Scale (v1.0)

```mermaid
pie title 예상 데이터 규모
    "청크 수 (~10,000)" : 40
    "벡터 데이터 (~100MB)" : 30
    "BM25 인덱스 (~20MB)" : 15
    "메타데이터 (~5MB)" : 15
```

- 50권+ (증가 예정)
- 1 사용자
- ~100-200MB 총 데이터

### 5.2 Extension Points

```mermaid
flowchart TB
    subgraph Current["v1.0 현재"]
        Search[Hybrid Search]
    end

    subgraph Future["v2.0 확장"]
        RAG[RAG + LLM<br/>AI 요약]
        Agent[LangGraph<br/>에이전트]
        Multi[다중 사용자]
    end

    Search --> RAG
    RAG --> Agent
    Search --> Multi
```

### 5.3 RAG Extension Architecture (v2.0)

```mermaid
flowchart LR
    Query[User Query] --> Search[Hybrid Search]
    Search --> Chunks[Retrieved Chunks]
    Chunks --> Context[Context Builder]
    Context --> LLM[LLM<br/>GPT-4 등]
    LLM --> Answer[Summarized Answer<br/>+ Source Citations]
```

---

## 6. Monitoring & Operations

### 6.1 Logging Strategy

```mermaid
flowchart LR
    App[Application] --> |structured logs| File[Log Files]
    File --> |rotation| Archive[Archived Logs]

    subgraph Events["Logged Events"]
        E1[search_query]
        E2[search_results]
        E3[ingestion_progress]
        E4[errors]
    end
```

### 6.2 Backup Strategy

```mermaid
flowchart TB
    subgraph Weekly["Weekly Backup"]
        B1[Chroma DB]
        B2[BM25 Index]
        B3[Config]
    end

    Weekly --> Compress[tar.gz]
    Compress --> Store[/backup/]
    Store --> Rotate[Keep Last 4]
```

---

## 7. API Specifications

### 7.1 Storm Parse API

#### Upload Request
```http
POST https://storm-apis.sionic.im/parse-router/api/v2/parse/by-file
Authorization: Bearer {JWT_TOKEN}
Content-Type: multipart/form-data

file: {binary}
language: "ko"
deleteOriginFile: true
```

#### Upload Response
```json
{
  "jobId": "defa_be5e9d960e8a45e39cf33069f1fae8d2",
  "state": "REQUESTED",
  "requestedAt": "2025-12-04T00:00:00Z"
}
```

#### Result Query
```http
GET https://storm-apis.sionic.im/parse-router/api/v2/parse/job/{jobId}
Authorization: Bearer {JWT_TOKEN}
```

#### Result Response (Completed)
```json
{
  "jobId": "...",
  "state": "COMPLETED",
  "requestedAt": "...",
  "completedAt": "...",
  "pages": [
    {
      "pageNumber": 1,
      "content": "### Chapter 1\n\n본문 내용..."
    }
  ]
}
```

