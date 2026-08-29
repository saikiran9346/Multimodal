# Multimodal Multi-PDF RAG for Technical Manuals

> Production-grade Multimodal Retrieval-Augmented Generation (RAG) system for querying complex technical PDF manuals containing dense prose, multi-column layouts, Markdown tables, and engineering schematics.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?style=flat&logo=react)](https://reactjs.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC2626.svg?style=flat&logo=qdrant)](https://qdrant.tech)
[![Docling](https://img.shields.io/badge/Docling-IBM%20Document%20Parser-4F46E5.svg?style=flat)](https://github.com/DS4SD/docling)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F97316.svg?style=flat)](https://groq.com)

---

## 1. Overview & Problem Statement

Technical equipment manuals (e.g., Grundfos industrial pump documentation, machinery service guides) present fundamental challenges for standard text-only RAG pipelines:

- **Complex Visuals & Schematics**: Critical installation, electrical wiring, and lifting guidelines exist only inside diagrams and figures.
- **Structured Data in Tables**: Maximum operating pressures, permissible liquid temperatures, and shaft seal limits are stored in tabular matrices that standard parsers destroy.
- **Cross-Document Keyword Collisions**: In multi-manual indexes, different products share identical vocabularies (*"pump"*, *"motor stool"*, *"pressure rating"*, *"installation"*), causing cross-document distraction and retrieval pollution.
- **Strict Citation Requirements**: Field engineers require verifiable document names and page numbers for every technical claim.

This project implements an end-to-end multimodal, multi-document RAG system with structure-aware PDF chunking, automated vision model classification, hybrid dense-sparse vector search, cross-encoder reranking, and document-aware routing.

---

## 2. Key Features

- **Structure-Aware Document Parsing**: Powered by IBM's **Docling** engine to parse multi-column PDF layouts, hierarchical headings, and Markdown tables with high fidelity.
- **Multimodal Visual Understanding**: Automatically extracts diagrams at 2.0x DPI, filters out decorative logos/branding, and generates detailed technical summaries via **Groq Vision** (`qwen/qwen3.6-27b`).
- **Hybrid Dense + Sparse Retrieval**: Combines 768-dimensional dense semantic vectors (**BAAI/bge-base-en-v1.5**) with sparse BM25 vectors (**Qdrant/bm25**) using **Reciprocal Rank Fusion (RRF)**.
- **Cross-Encoder Reranking**: Re-scores candidate pools with **BAAI/bge-reranker-base** (`TextCrossEncoder`) to place the most relevant evidence chunks at Rank 1.
- **Multi-Document Disambiguation**: Employs document title prefixing (`[Manual: <Name>]`) and query-aware metadata routing to eliminate cross-manual distraction without evaluation data leakage.
- **Grounded Answers with Strict Citations**: Uses Groq LLM inference with low temperature (`0.1`) and inline citations `[1]`, `[2]` directly tied to document filenames and page numbers.
- **Production FastAPI Backend**: Async REST API with validation, health checks, and error handling.
- **Modern React Interface**: Single-page application with source inspection, image chunk badges, document filter dropdowns, and live citation jump links.

---

## 3. Architecture

```mermaid
graph TD
    subgraph Ingestion Pipeline
        A[Upload PDF Manual] --> B[Docling Structure Parser]
        B --> C[HybridChunker: Text & Tables]
        B --> D[Picture Extractor: 2.0x DPI]
        D --> E[Groq Vision: Classify & Describe]
        E -- Technical Diagrams --> F[Image Chunks]
        E -- Branding / Logos --> G[Discard]
        C --> H[Prepend Document Identifier]
        F --> H
        H --> I[FastEmbed: Dense BGE-Base 768d]
        H --> J[FastEmbed: Sparse BM25 IDF]
        I --> K[(Qdrant Vector DB)]
        J --> K
    end

    subgraph Query & Generation Pipeline
        L[User Query] --> M[Document Query Router]
        M --> N[Hybrid Search: Dense + BM25 Prefetch]
        K --> N
        N --> O[Reciprocal Rank Fusion RRF]
        O --> P[Candidate Pool: Top-15 Chunks]
        P --> Q[BGE-Reranker-Base Cross-Encoder]
        Q --> R[Top-5 Re-Ranked Evidence Chunks]
        R --> S[Groq LLM: Grounded Generation]
        S --> T[FastAPI JSON Response + Citations]
        T --> U[React UI / Chat Interface]
    end
```

---

## 4. End-to-End RAG Workflow

```
[ PDF Document Upload ]
          │
          ▼
[ Docling Structural Parsing ] ───► Preserves Markdown tables & reading order
          │
          ├──► Text / Table Chunks ──┐
          │                          ▼
          └──► Technical Figures ────► [ Groq Vision Model ] ──► Visual Summaries
                                                                       │
                                                                       ▼
[ Chunk Title Prefixing ] ◄────────────────────────────────────────────┘
  e.g. "[Manual: Grundfos CM, CME] \n 11.4 Operating Limits..."
          │
          ▼
[ Dual Vector Embedding ]
  ├── Dense: BAAI/bge-base-en-v1.5 (Cosine, 768d)
  └── Sparse: Qdrant/bm25 (IDF modified)
          │
          ▼
[ Qdrant Hybrid Storage ] (Payload: doc_name, page_no, headings, content_types)
          │
          ▼
[ Query Routing & Hybrid Search ] ──► Dense Prefetch + BM25 Prefetch via RRF
          │
          ▼
[ Cross-Encoder Reranking ] ──► BAAI/bge-reranker-base (Pool: 15 -> Top 5)
          │
          ▼
[ Groq LLM Generation ] ──► Grounded response with [1], [2] bracket citations
```

---

## 5. Multi-PDF Support

Real-world technical repositories store multiple manuals simultaneously. This system handles cross-document coexistence through:

1. **Payload Metadata Isolation**: Every indexed point in Qdrant retains `doc_name`, `page_no`, `content_types`, `headings`, and `captions`.
2. **Document Title Prefixing**: Chunks are prefixed with their human-readable manual title (`[Manual: Grundfos CM, CME]` or `[Manual: Grundfos TP, TPD]`). This ensures semantic encoders and cross-encoders preserve manual context even for generic sub-sections.
3. **Query-Aware Metadata Filtering**: If a user's prompt explicitly mentions a specific series (e.g. *"TP Series 300"* or *"CM manual"*), Qdrant payload filters dynamically isolate candidates to that document. Generic queries search across all indexed manuals simultaneously.
4. **Per-Source Document & Page Citations**: Every cited source displays both the source PDF filename and the exact target page number.

---

## 6. Retrieval Architectures

The benchmark evaluates four distinct retrieval pipeline architectures:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Baseline Dense                                                           │
│    Query ──► BGE-Base Embed ──► Qdrant Cosine Similarity ──► Top-5 Chunks   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Hybrid Search (Dense + BM25 RRF)                                         │
│    Query ──► Dense Vector + Sparse BM25 ──► Qdrant RRF Fusion ──► Top-5     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Hybrid + Cross-Encoder Reranker                                          │
│    Query ──► Hybrid Search (Top-15 Pool) ──► BGE-Reranker-Base ──► Top-5    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Multimodal (Text + Tables + Vision Chunks)                               │
│    Query ──► Multimodal Index (Text+Tables+Vision) ──► Hybrid RRF ──►       │
│              BGE-Reranker-Base Cross-Encoder ──► Top-5 Evidence             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tech Stack

| Layer | Technology | Details / Model |
| :--- | :--- | :--- |
| **Document Parser** | IBM Docling | `HybridChunker` (Supports PDF, DOCX, PPTX, XLSX, HTML, Markdown, CSV) |
| **Vision Model** | Groq API | `qwen/qwen3.6-27b` (Classification & diagram description) |
| **Dense Embeddings** | FastEmbed | `BAAI/bge-base-en-v1.5` (768 dimensions) |
| **Sparse Embeddings** | FastEmbed | `Qdrant/bm25` (Learned sparse token weights) |
| **Vector Database** | Qdrant | Local embedded storage (`./qdrant_storage`) or Docker (`:6333`) |
| **Reranker** | FastEmbed | `BAAI/bge-reranker-base` (`TextCrossEncoder`) |
| **LLM Generation** | Groq API | `qwen/qwen3.6-27b` (`temperature=0.1`) |
| **Backend API** | FastAPI / Uvicorn | Python 3.12, Pydantic v2, CORS, Starlette |
| **Frontend UI** | React 18 / Vite | Vanilla CSS, Lucide Icons, Fetch API |

---

## 8. Evaluation Methodology

The system is evaluated against ground-truth test datasets using standard Information Retrieval (IR) metrics at $k=5$:

$$\text{Recall@k} = \frac{|\text{Retrieved}_k \cap \text{Relevant}|}{|\text{Relevant}|}$$

$$\text{Precision@k} = \frac{|\text{Retrieved}_k \cap \text{Relevant}|}{k}$$

$$\text{MRR} = \frac{1}{\text{rank}_{\text{first relevant}}}$$

$$\text{NDCG@k} = \frac{\text{DCG}_k}{\text{IDCG}_k} \quad \text{where} \quad \text{DCG}_k = \sum_{i=1}^k \frac{2^{\text{rel}_i} - 1}{\log_2(i + 1)}$$

### Benchmark Query Categories (25 Questions):
1. **TABLE**: Exact threshold queries requiring structured multi-column table data (e.g. pressure ratings for seal types).
2. **IMAGE**: Technical queries whose answers exist solely inside engineering figures and schematics.
3. **EXACT_FACT**: Highly specific numeric or operational constraints located in specific paragraphs.
4. **MULTI_PAGE**: Questions requiring cross-referencing information scattered across multiple pages.
5. **SECTION_STRUCTURE**: Structural manual questions (e.g. section overview and maintenance scope).

---

## 9. Experimental Results

### A. Single-PDF Benchmark (135 Chunks — `grundfos_cm_pump_manual.pdf`)

*Source data: `experiments/results/baseline_dense.json`, `hybrid_rrf.json`, `hybrid_reranked.json`, `multimodal.json`*

| Pipeline Architecture | Recall@5 | Precision@5 | MRR | NDCG@5 |
| :--- | :---: | :---: | :---: | :---: |
| **1. Baseline Dense (BGE)** | 0.9200 | 0.4240 | 0.8600 | 0.8528 |
| **2. Hybrid Search (Dense + BM25 RRF)** | 0.9200 | 0.4240 | 0.9200 | 0.8871 |
| **3. Hybrid + Cross-Encoder Reranker** | 0.9400 | 0.4000 | 0.9400 | 0.9115 |
| **4. Multimodal (Text + Tables + Vision)** | **0.9600** | **0.4240** | **0.9733** | **0.9395** |

---

### B. Multi-PDF Benchmark Results (422 Chunks — 2 Pump Manuals)

*Source data: `experiments/results/multi_pdf_evaluation.json`*

Evaluated on the full 25-question multi-document ground-truth set (422 chunks across both manuals). Results show clean, monotonic improvement in MRR and NDCG across every added pipeline stage.

| Pipeline Architecture | Recall@5 | Precision@5 | MRR | NDCG@5 |
| :--- | :---: | :---: | :---: | :---: |
| **1. Baseline Dense (BGE)** | 0.7800 | 0.1920 | 0.6967 | 0.6891 |
| **2. Hybrid Search (Dense + BM25 RRF)** | 0.9000 | 0.2240 | 0.7767 | 0.7813 |
| **3. Hybrid + Cross-Encoder Reranker** | 0.9000 | 0.2160 | 0.8267 | 0.8216 |
| **4. Multimodal (Text + Tables + Vision)** | **0.9200** | 0.2240 | **0.8747** | **0.8578** |

---

## 10. Robustness & Error Handling

The FastAPI backend includes defensive validation verified via explicit integration tests (`backend/test_error_handling.py`):

| Test Case | Request Input | Expected & Actual HTTP Status | Response Body / Behavior |
| :--- | :--- | :---: | :--- |
| **Corrupted / Fake PDF** | `.txt` file renamed to `invalid.pdf` | `400 Bad Request` | `{"detail": "Failed to parse 'invalid.pdf'. Please ensure it is a valid, uncorrupted PDF document."}` |
| **Zero-Byte File** | Genuinely empty file (0 bytes) | `400 Bad Request` | `{"detail": "Uploaded file is empty (0 bytes)."}` |
| **Non-PDF Extension** | `.png` image sent to upload | `400 Bad Request` | `{"detail": "Only PDF files (.pdf) are supported."}` |
| **Missing Upload Field** | Multipart request without file | `422 Unprocessable Entity` | Pydantic validation error (`Field required`) |
| **Empty Query** | `{"query": "   "}` | `400 Bad Request` | `{"detail": "Query cannot be empty."}` |
| **Missing Query Field** | `{}` | `422 Unprocessable Entity` | Pydantic validation error (`Field required`) |
| **Nonexistent Document Filter** | `{"query": "...", "doc_name": "missing.pdf"}` | `404 Not Found` | `{"detail": "Document 'missing.pdf' was not found in the indexed collection."}` |
| **Long Query Stress Test** | 2,000+ character prompt | `200 OK` | Handled gracefully without buffer overflow or model crash |

---

## 11. API Endpoints

### 1. Health Check
```http
GET /api/health
```
```json
{
  "status": "healthy",
  "qdrant": "connected",
  "indexed_chunks": 844
}
```

### 2. Document Query
```http
POST /api/query
Content-Type: application/json

{
  "query": "What is shaft seal type AQQx rated for?",
  "top_k": 5,
  "exclude_images": false,
  "doc_name": null
}
```
```json
{
  "query": "What is shaft seal type AQQx rated for?",
  "answer": "Based on the provided excerpts, the shaft seal type AQQx has the following ratings:\n- For Stainless Steel: liquid temperature -20 to 90 °C at 16 bar [1].\n- For Cast Iron: liquid temperature -20 to 90 °C at 10 bar [2].",
  "sources": [
    {
      "index": 1,
      "doc_name": "grundfos_cm_pump_manual.pdf",
      "page_no": 11,
      "headings": ["11.4 Maximum system pressure and permissible liquid temperature"],
      "content_types": ["table"],
      "text": "[Manual: Grundfos CM, CME]\n11.4 Maximum system pressure...",
      "score": 5.168
    }
  ]
}
```

### 3. PDF Ingestion
```http
POST /api/ingest
Content-Type: multipart/form-data

file=@grundfos_cm_pump_manual.pdf
```
```json
{
  "status": "success",
  "filename": "grundfos_cm_pump_manual.pdf",
  "total_chunks": 135,
  "text_chunks": 113,
  "image_chunks": 22,
  "message": "Successfully indexed 135 chunks for 'grundfos_cm_pump_manual.pdf' into Qdrant."
}
```

---

## 12. Project Structure

```
Multimodal-Rag/
├── README.md
├── docker-compose.yml             # Optional Docker Compose for Qdrant service
├── requirements.txt               # Root Python dependencies
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── ingest.py      # POST /api/ingest endpoint
│   │   │       └── query.py       # POST /api/query endpoint
│   │   ├── generation/
│   │   │   └── llm.py             # Groq LLM grounded generation & citation prompt
│   │   ├── ingestion/
│   │   │   ├── parser.py          # Docling document conversion
│   │   │   ├── chunker.py         # Structure-aware HybridChunker
│   │   │   └── image_processor.py # Groq Vision image classification & description
│   │   ├── models/
│   │   │   ├── chunk.py           # SourceChunk model
│   │   │   ├── document.py        # IngestResponse model
│   │   │   └── response.py        # QueryRequest & QueryResponse models
│   │   ├── retrieval/
│   │   │   ├── embeddings.py      # BGE-base dense embeddings via FastEmbed
│   │   │   ├── reranker.py        # BGE-reranker-base cross-encoder
│   │   │   └── vector_store.py    # Qdrant client, hybrid RRF, routing, and filters
│   │   ├── config.py              # Pydantic Settings & environment variables
│   │   └── main.py                # FastAPI application entrypoint
│   │
│   ├── build_multi_index.py       # Rebuilds multi-document Qdrant index
│   ├── evaluate_multi_pdf.py      # 4-arm multi-PDF benchmark evaluation suite
│   ├── test_api.py                # Live FastAPI endpoint test client
│   └── test_error_handling.py     # 8-scenario error and edge-case test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnswerCard.jsx     # Markdown response renderer with citation pill clicks
│   │   │   ├── ChatView.jsx       # Chat thread and prompt input
│   │   │   ├── Header.jsx         # App bar with Qdrant connectivity badge
│   │   │   └── Sidebar.jsx        # Document upload, filter controls, and stats
│   │   ├── api.js                 # Frontend API client
│   │   ├── App.jsx                # Main application state and layout
│   │   └── index.css              # Custom styling
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── evaluation/
│   │   ├── multi_pdf_questions.json # 25 Multi-document ground-truth benchmark questions
│   │   └── questions.json           # 25 Single-document benchmark questions
│   └── sample_manuals/
│       ├── grundfos_cm_pump_manual.pdf
│       └── 1_TP.pdf
│
└── experiments/
    ├── baseline_dense.py          # Arm 1 evaluation script
    ├── hybrid_rrf.py              # Arm 2 evaluation script
    ├── hybrid_reranked.py         # Arm 3 evaluation script
    ├── multimodal.py              # Arm 4 evaluation script
    └── results/
        ├── baseline_dense.json
        ├── hybrid_rrf.json
        ├── hybrid_reranked.json
        ├── multimodal.json
        └── multi_pdf_evaluation.json
```

---

## 13. Installation & Setup

### Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: v18+ and `npm`
- **Groq API Key**: Obtain from [console.groq.com](https://console.groq.com)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/Multimodal-Rag.git
cd Multimodal-Rag
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

pip install -r ../requirements.txt
```

Create a `.env` file in the `backend/` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
QDRANT_URL=http://localhost:6333
```
*(Note: If no external Qdrant server is running, the backend automatically falls back to local embedded storage in `qdrant_storage/` without requiring Docker).*

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

Create a `.env` file in the `frontend/` directory:
```env
VITE_API_URL=http://localhost:8000
```

---

## 14. How to Run

### 1. Start Qdrant (Optional Docker)
```bash
docker compose up -d
```

### 2. Start FastAPI Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at `http://localhost:8000/docs`.

### 3. Start React Frontend
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

### 4. Run Multi-PDF Benchmark Evaluation
```bash
cd backend
python evaluate_multi_pdf.py
```

### 5. Run Error Handling & Endpoint Verification Tests
```bash
cd backend
python test_error_handling.py
python test_api.py
```

---

## 15. User Interface & Demonstration

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  MULTIMODAL TECHNICAL MANUAL RAG                          ● Qdrant Connected (844 Chunks)│
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│  DOCUMENT REPOSITORY     │  CHAT & QUESTION ANSWERING                                  │
│                          │                                                             │
│  [ Upload PDF Manual ]   │  User: What is shaft seal type AQQx rated for?              │
│                          │                                                             │
│  Indexed Documents:      │  Assistant:                                                 │
│  • grundfos_cm_pump.pdf  │  Based on the technical manual excerpts, shaft seal         │
│  • 1_TP.pdf              │  type AQQx has the following permissible ratings:           │
│                          │                                                             │
│  Filter By Document:     │  • Stainless Steel (AISI 316): -20 to 90 °C at 16 bar [1]   │
│  [ All Documents ▾ ]     │  • Cast Iron (EN-GJL-200): -20 to 90 °C at 10 bar [2]       │
│                          │                                                             │
│  Retrieval Settings:     │  ────────────────────────────────────────────────────────── │
│  [x] Include Visuals     │  Sources & Evidence:                                        │
│  Top K: [ 5 ]            │  [1] grundfos_cm_pump_manual.pdf (p.11) [TABLE] Score: 5.168│
│                          │  [2] grundfos_cm_pump_manual.pdf (p.11) [TABLE] Score: 4.151│
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 16. Limitations

1. **Local Cross-Encoder Latency on CPU**: Running the `BAAI/bge-reranker-base` cross-encoder over 15–25 candidates on CPU adds ~80–120ms per query. (Mitigated by candidate pooling).
2. **Groq Daily Token Quotas on Batch Image Extraction**: Extracting dozens of high-res figures in large 100+ page manuals can hit transient rate limits without retry backoff. (Mitigated by exponential backoff with state caching in `*_image_progress.json`).
3. **Structural/Table-of-Contents Questions**: Queries asking about a section's own subsections (e.g. 'what does section 6 cover') have a ceiling on Recall@5 of ~0.50 across every retrieval architecture tested, including multimodal. Root cause: subsection enumeration only exists in the document's own Table of Contents chunk; body-content chunks split by heading never restate it, and verbose image-description chunks can outrank the short ToC chunk in the candidate pool. Reproduced identically across three separate questions on two different manuals -- a structural property of chunk-based RAG, not a fixable retrieval bug.

---

## 17. Future Improvements

- **ColPali / Vision-Language Late Interaction**: Experiment with ColPali embeddings to index raw page screenshots alongside textual chunks.
- **Hierarchical Parent-Document Retrieval**: Return entire section contexts to the LLM when small table fragments match.
- **Agentic Multi-Step Reasoning**: Allow the agent to query multiple manuals sequentially for comparative pump sizing workflows.

---

## 18. Why This Project Is Technically Interesting

1. **Overcomes the Text-Only Blindspot**: Standard RAG fails on equipment manuals where answers exist in wiring schematics or mechanical drawings. This system bridges text and visual modalities.
2. **Document Structure Preservation**: Rather than naive fixed-size chunking (e.g. 500 characters with 50 overlap), Docling chunking respects table borders, subsection boundaries, and prov page links.
3. **Honest Multi-Document Evaluation**: Demonstrates the real-world challenge of multi-document retrieval degradation when scaling chunk corpus size, proving why document prefixing and routing are necessary for production scale.
4. **Resilient Production API**: Comprehensive error handling catching malformed, empty, and non-PDF files as structured 4xx responses without unhandled server crashes.

---

## 19. Resume & Technical Interview Highlights

- **Designed & Implemented Multimodal RAG**: Built an end-to-end ingestion and retrieval engine utilizing Docling structure parsing, Groq Vision image classification, and hybrid retrieval over 800+ indexed vector representations.
- **Improved Retrieval Performance with Hybrid RRF & Reranking**: Evaluated 4 retrieval architectures across 25 ground-truth technical queries, demonstrating an increase from **0.6967 MRR (Dense baseline)** to **0.8747 MRR (Multimodal + Reranker)** on a multi-document index.
- **Multi-Document Disambiguation**: Solved cross-manual keyword collisions across hundreds of technical chunks by engineering document title prefixing and query-aware metadata filtering in Qdrant.
- **Full-Stack Production System**: Built and integrated a FastAPI backend with Pydantic validation, CORS middleware, and an interactive React interface featuring dynamic citation previews.
