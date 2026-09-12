# Legal Advisor

A retrieval-augmented generation (RAG) web application that answers questions about Indian law. It retrieves the most relevant statutory provisions (Acts, Codes, and Sanhitas), reranks them with a cross-encoder, and generates a grounded, cited answer via Google Gemini — all exposed through a full-stack web app.

The system ingests a corpus of Indian statutes, chunks them into sections, indexes them with a hybrid dense + lexical search, reranks candidates with a cross-encoder, and passes the top sections as context to Gemini to produce a plain-language answer with Act · Section citations.

## Highlights

- **37 Indian statutes** across 12 legal domains, parsed from India Code PDFs into structured, section-aware JSON.
- **Hybrid retrieval** combining dense (semantic) and lexical (BM25) recall, with section-title matching, anchor boost, and query expansion.
- **Cross-encoder reranker** (`BAAI/bge-reranker-v2-m3`) that separates near-identical sections within the same Act (e.g. `BNS 101` vs `BNS 103`).
- **Grounded generation** via Google Gemini (`gemini-3.6-flash`) with automatic retry and fallback models; every claim cites Act · Section from the retrieved text.
- **SSE streaming** from the API server to the frontend with real-time stage updates (retrieval → generation) and live elapsed-time display.
- **Retrieval quality harness** reporting Hit@1/3/5 and MRR over a labeled test set of 192 query → citation cases (Hit@5 = 100%, MRR = 0.752).

> **Not legal advice.** This tool surfaces the text of statutes for informational purposes. It does not substitute for a licensed legal professional.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              USER (browser)                                         │
│                        plain-language legal question                                │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ HTTP / SSE stream
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND  (React + Vite + Tailwind)                         │
│     App.tsx — ask form, sample queries, markdown renderer (react-markdown)          │
│     api.ts  — typed fetch + askStream() SSE parser                                  │
│                                                                                     │
│     • POST /api/ask       (non-streaming)                                           │
│     • POST /api/ask/stream (SSE: retrieval_started → retrieval_done                 │
│                                    → generation_started → generation_done)          │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ :5173  →  proxy  →  :3001
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND  (Node/TypeScript + Express)                       │
│            src/routes/ — health, ask (sync + SSE), retrieve                         │
│            src/services/ai.ts — axios client → FastAPI                              │
│                                                                                     │
│     Non-streaming:  POST /api/ask        →  POST :8000/answer                      │
│     Streaming:      POST /api/ask/stream →  POST :8000/answer/stream  (pipe SSE)   │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                        │ :3001  →  :8000
                                        ▼
╔═════════════════════════════════════════════════════════════════════════════════════╗
║                     AI SERVICE  (Python FastAPI + RAG pipeline)                     ║
╠═════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                     ║
║  POST /answer      — retrieve (under GPU lock) + generate (off-lock)                ║
║  POST /answer/stream — same, but streams SSE stage events to the client             ║
║  POST /retrieve    — retrieval only (no LLM)                                        ║
║                                                                                     ║
║  ┌──────────────────────┐    ┌───────────────────────┐    ┌──────────────────────┐ ║
║  │   semantic_router    │    │   intent_expander     │    │ query_context_builder│ ║
║  │  query → category    │───▶│  query → legal intents│───▶│  expanded query      │ ║
║  └──────────────────────┘    └───────────────────────┘    └──────────┬───────────┘ ║
║                                                                      │              ║
║    ┌────────────────────────────── RECALL (retrieve.py) ──────────────┤              ║
║    │  Dense (ChromaDB + bge-m3)  │  Lexical (BM25)  │  Title BM25   │              ║
║    └──────────────┬───────────────┴──────────┬────────┴──────┬────────┘              ║
║                   ▼                          ▼               ▼                       ║
║              candidate chunks (deduped, max 80)                                    ║
║                   │                                                                 ║
║                   ▼                                                                 ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║    │   reranker.py — BAAI/bge-reranker-v2-m3 (cross-encoder)                   │  ║
║    │   score = retrieval(0.55) + rerank(0.40) + title_match(0.05)              │  ║
║    │   + anchor_boost(+0.12 if section appears in top-5)                       │  ║
║    └──────────────────────────┬────────────────────────────────────────────────┘  ║
║                               │                                                     ║
║                    top-8 sections (Act › Section › Title + text)                   ║
║                               │                                                     ║
║                               ▼                                                     ║
║    ┌─────────────────────────────────────────────────────────────────────────────┐  ║
║    │   answer.py — Google Gemini (gemini-3.6-flash)                             │  ║
║    │   system prompt: summary → legal provisions → practical steps              │  ║
║    │   every claim cites "Act, Section X"; flags outdated figures               │  ║
║    │   retry (3×, exponential backoff) + fallback model chain                   │  ║
║    └─────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                     ║
╠═══════════════════════════════════════ INGEST PATH ═════════════════════════════════╣
║                                                                                     ║
║    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐    ┌────────────┐  ║
║    │  parser.py       │    │  chunker.py     │    │  ingest.py  │    │ vectordb   │  ║
║    │  PDF → sections  │───▶│  section-aware  │───▶│ build stores│───▶│  ChromaDB  │  ║
║    │  (ACT_REGISTRY)  │    │  chunks         │    │  + BM25     │    │  + pickle  │  ║
║    └─────────────────┘    └─────────────────┘    └─────────────┘    └────────────┘  ║
╚═════════════════════════════════════════════════════════════════════════════════════╝

Raw PDFs                Generated stores (all gitignored)
datasets/raw_pdfs/      ai_service/app/data/chroma/
datasets/parsed/        ai_service/app/data/vector_store.pkl
                        ai_service/app/data/bm25.pkl
                        ai_service/app/data/embedding_cache.pkl
```

### Directory layout

```
legal_advisor/
├── ai_service/                     # Python RAG pipeline + FastAPI server
│   ├── venv/                       # virtualenv (ai_service/venv, gitignored)
│   └── app/
│       ├── main.py                 # FastAPI app: /health, /retrieve, /answer, /answer/stream
│       ├── rag/
│       │   ├── parser.py           # PDF → structured sections (ACT_REGISTRY)
│       │   ├── chunker.py          # section-aware chunking
│       │   ├── ingest.py           # build vector store + BM25 index
│       │   ├── retrieve.py         # hybrid retrieval + multi-view scoring
│       │   ├── reranker.py         # BAAI/bge-reranker-v2-m3 cross-encoder
│       │   ├── answer.py           # Gemini generation (answer_from_results)
│       │   ├── faithfulness.py     # citation-grounding eval script
│       │   ├── eval.py             # retrieval harness: Hit@1/3/5, MRR
│       │   ├── retrieval_test_cases.py   # 192 gold query→citation cases
│       │   ├── semantic_router.py  # query → legal domain classification
│       │   ├── intent_expander.py  # query → legal intents
│       │   ├── query_context_builder.py
│       │   ├── category_prototypes.py
│       │   └── intent_index.json
│       └── data/                   # generated stores (gitignored)
│           ├── chroma/
│           ├── vector_store.pkl
│           ├── bm25.pkl
│           └── embedding_cache.pkl
├── backend/                        # Node/TypeScript Express server (:3001)
│   ├── src/
│   │   ├── index.ts                # app entry: CORS, JSON, routes, error handler
│   │   ├── config/index.ts         # env: PORT, AI_SERVICE_URL
│   │   ├── routes/
│   │   │   ├── ask.ts              # POST /api/ask (sync) + /api/ask/stream (SSE)
│   │   │   ├── retrieve.ts         # POST /api/retrieve
│   │   │   └── health.ts           # GET  /api/health
│   │   └── services/ai.ts          # axios client → FastAPI
│   ├── package.json
│   ├── tsconfig.json
│   └── .env                        # PORT=3001, AI_SERVICE_URL=http://localhost:8000
├── frontend/                       # React + Vite + Tailwind (:5173)
│   ├── src/
│   │   ├── App.tsx                 # UI: ask form, sample queries, streaming loader, results
│   │   ├── api.ts                  # ask() + askStream() SSE parser
│   │   └── index.css               # Tailwind import + .markdown typography
│   ├── vite.config.ts              # Tailwind plugin + /api proxy → :3001
│   └── package.json
├── datasets/
│   ├── raw_pdfs/<category>/        # source statute PDFs (gitignored)
│   └── parsed/<category>/          # structured section JSON per Act
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10+ (with a CUDA GPU recommended for fast retrieval)
- Node.js 18+ and npm
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Python virtualenv and dependencies

```bash
cd ai_service
python -m venv venv
source venv/bin/activate
pip install torch sentence-transformers chromadb pdfplumber requests numpy fastapi uvicorn pydantic
```

### 2. Gemini API key

Create `~/.config/legal_advisor/.env` (or export the env var):

```bash
mkdir -p ~/.config/legal_advisor
cat > ~/.config/legal_advisor/.env << 'EOF'
GEMINI_API_KEY=your_key_here
EOF
```

The server reads this file at startup. You can also set `GEMINI_API_KEY` (or `API_KEY`) as an environment variable. Override the default model with `GEMINI_MODEL`.

### 3. Parse PDFs into structured JSON

Place India Code PDFs under `datasets/raw_pdfs/<category>/`:

```bash
datasets/raw_pdfs/
├── criminal/bharatiya_nyaya_sanhita_2023.pdf
├── family/hindu_marriage_act_1955.pdf
└── ...
```

Acts are recognized by `ACT_REGISTRY` in `ai_service/app/rag/parser.py`. Run:

```bash
python -m ai_service.app.rag.parser                    # all PDFs
python -m ai_service.app.rag.parser --act the_arms_act_1959   # one Act
python -m ai_service.app.rag.parser --show-unregistered       # find missing entries
```

### 4. Ingest into vector store + BM25 index

```bash
python -m ai_service.app.rag.ingest           # build
python -m ai_service.app.rag.ingest --reset   # rebuild from scratch
```

### 5. Run the full stack

Open **three terminals** and start all three services:

```bash
# Terminal 1 — AI service (FastAPI, port 8000)
# First-time startup loads all models: ~20-30s warmup
cd /path/to/legal_advisor
ai_service/venv/bin/uvicorn ai_service.app.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Express backend (port 3001)
cd /path/to/legal_advisor/backend
npm install          # first time only
npm run dev

# Terminal 3 — React frontend (port 5173)
cd /path/to/legal_advisor/frontend
npm install          # first time only
npm run dev
```

Open **http://localhost:5173** — click a sample query or type your own.

### Retrieve only (no LLM)

```python
from ai_service.app.rag.retrieve import retrieve

result = retrieve("Can a minor be tried as an adult?", top_k=8)
for r in result["results"]:
    print(r["citation"], r["final_score"])
```

Or via the API:

```bash
curl -s -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "Can a minor be tried as an adult?", "top_k": 8}' | jq
```

### Generate an answer (one-shot)

```bash
curl -s -X POST http://localhost:8000/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Can police arrest me without a warrant?", "top_k": 8}' | jq
```

### Generate via the Express proxy (what the frontend uses)

```bash
curl -s -X POST http://localhost:3001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "My employer is not paying my salary"}' | jq
```

## Evaluation

### Retrieval quality

```bash
python -m ai_service.app.rag.eval                          # full harness
python -m ai_service.app.rag.eval --top-k 5 --verbose
python -m ai_service.app.rag.eval --cases ai_service/app/rag/retrieval_test_cases_focus.py  # subset
```

Reported on 192 test cases (reranker + anchor boost enabled):

| Metric | Value |
|--------|-------|
| Hit@3  | 89.6% |
| Hit@5  | 100%  |
| MRR    | 0.752 |

Test cases live in `ai_service/app/rag/retrieval_test_cases.py` (each has a query and expected preferred/acceptable citations).

### Generation grounding

```bash
python -m ai_service.app.rag.faithfulness   # runs 5-query pilot
```

Checks citation precision (strict + lenient), source coverage, and flags ungrounded claims against the retrieved sections.

## Configuration

| File | Purpose |
|------|---------|
| `ai_service/app/rag/parser.py` | `ACT_REGISTRY`: Act metadata (name, year, category) keyed by PDF stem |
| `ai_service/app/rag/retrieve.py` | Score weights, anchor boost, fallback widening thresholds |
| `ai_service/app/rag/reranker.py` | Reranker model path, score-blend weights |
| `ai_service/app/rag/category_prototypes.py` | Domain descriptions for the semantic router |
| `ai_service/app/rag/intent_index.json` | Legal intents with example queries |
| `ai_service/app/rag/answer.py` | `SYSTEM_PROMPT`, `DEFAULT_MODEL`, retry/backoff config |
| `~/.config/legal_advisor/.env` | `GEMINI_API_KEY` (or `API_KEY`), `GEMINI_MODEL` override |
| `backend/.env` | `PORT`, `AI_SERVICE_URL` |

## Performance notes

- **First request after startup**: ~20s model warmup (reranker + embedder loading to GPU) + ~40-70s generation.
- **Subsequent requests**: ~3-5s retrieval + ~30-40s generation.
- Retrieval runs under a mutex lock (GPU serialization); Gemini generation runs outside the lock so concurrent requests can overlap generation.
- The default model is `gemini-3.6-flash` with automatic fallback to `gemini-3.5-flash` and `gemini-flash-latest`.

## License

TBD.
