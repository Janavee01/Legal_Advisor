# Legal Advisor

A retrieval-augmented generation (RAG) system that answers questions about Indian law by retrieving the most relevant statutory provisions (Acts, Codes, and Sanhitas) and reranking them with a fine-tuned cross-encoder. It lets ordinary people ask legal questions in plain language and get precise, citable answers backed by the exact section of the correct Act.

The system ingests a corpus of Indian statutes, chunks them into sections, indexes them with a hybrid dense + lexical search, and reranks candidates with a model fine-tuned to distinguish between confusable sibling sections of the same Act.

## Highlights

- **37 Indian statutes** across 11 legal domains, parsed from India Code PDFs into structured, section-aware JSON.
- **Hybrid retrieval** that combines dense (semantic) and lexical (BM25) recall, with section-title matching and query expansion.
- **Fine-tuned cross-encoder reranker** (`BAAI/bge-reranker-v2-m3`) trained specifically to separate near-identical sections within the same Act (e.g. `BNS 101` vs `BNS 103`).
- **Semantic intent routing** that maps a plain-language query to a legal intent and a legal domain before retrieval.
- **Retrieval quality harness** reporting Hit@1/3/5 and MRR over a labeled test set of 150+ query → citation cases.

> ⚠️ **Not legal advice.** This tool surfaces the text of statutes for informational purposes. It does not substitute for a licensed legal professional.

## Architecture

### Whole-project block diagram

```
                        ┌──────────────────────────────────────────────────────┐
                        │                        USER                          │
                        │                    plain-language                     │
                        │                    legal question                     │
                        └──────────────────────────┬───────────────────────────┘
                                                   │ query
                                                   ▼
          ┌────────────────────────────────────────────────────────────────────┐
          │                      FRONTEND  (React + Vite, WIP)                │
          │                          src/App.tsx, main.tsx                     │
          └──────────────────────────────────┬─────────────────────────────────┘
                                             │ HTTP
                                             ▼
          ┌────────────────────────────────────────────────────────────────────┐
          │                       BACKEND  (Node/TS, WIP)                     │
          └──────────────────────────────────┬─────────────────────────────────┘
                                             │ query
                                             ▼
 ╔═══════════════════════════════════════════╧══════════════════════════════════════════════╗
 ║                              AI_SERVICE — Python RAG pipeline                            ║
 ╠═════════════════════════════════════════ QUERY PATH ═════════════════════════════════════╣
 ║                                                                                          ║
 ║    ┌─────────────────────┐      ┌──────────────────────┐     ┌─────────────────────────┐  ║
 ║    │   semantic_router    │      │    intent_expander   │     │ query_context_builder  │  ║
 ║    │   (query→category)   │─────▶│   (query→legal       │────▶│  builds expanded query │  ║
 ║    │ retrieval/query_ro   │      │    intents)          │     │   + category + intents │  ║
 ║    └─────────────────────┘      └──────────────────────┘     └───────────┬─────────────┘  ║
 ║                                                                          │ expanded query ║
 ║                                                                          ▼                ║
 ║    ┌───────────────────────────────────────────  RECALL  ─────────────────────────────┐  ║
 ║    │                     retrieve.py  (hybrid, multi-view)                            │  ║
 ║    │   ┌────────────────────┐      ┌────────────────────┐      ┌───────────────────┐  │  ║
 ║    │   │  DENSE  (ChromaDB) │      │  LEXICAL  (BM25)   │      │ SECTION-TITLE BM25 │  │  ║
 ║    │   │  embedder bge-m3   │      │   retriever        │      │   (precise title   │  │  ║
 ║    │   └─────────┬──────────┘      └─────────┬──────────┘      │    discrimination) │  │  ║
 ║    └─────────────┼───────────────────────────┼─────────────────┼─────────────────────┘  │  ║
 ║                  ▼                           ▼                 ▼                        ║
 ║         candidate chunks (deduped, 50 max)                                             ║
 ║                  │                                                                     ║
 ║                  ▼                                                                     ║
 ║    ┌──────────────────────────────────────────┐                                        ║
 ║    │   reranker.py  (fine-tuned CrossEncoder) │                                        ║
 ║    │  retrieval score(0.55) + rerank(0.40)    │   ──▶  top-k citations                ║
 ║    │  + title match(0.05)                     │        (Act › Section › Title)        ║
 ║    └──────────────────────────────────────────┘                                        ║
 ╠════════════════════════════════════════ INGEST PATH ═══════════════════════════════════╣
 ║                                                                                          ║
 ║    ┌────────────────┐      ┌───────────────┐      ┌────────────────┐      ┌──────────┐   ║
 ║    │  parser.py      │      │  chunker.py    │      │  ingest.py     │      │ vectordb │   ║
 ║    │  PDF → sections │─────▶│  section-aware │─────▶│  build stores   │─────▶│  Chroma  │   ║
 ║    │  (ACT_REGISTRY) │      │  chunks        │      │  + BM25 + cache │      │  + pickl │   ║
 ║    └────────┬───────┘      └───────────────┘      └────────┬─────────┘      └──────────┘   ║
 ║             │                                              │                               ║
 ╚═════════════╪══════════════════════════════════════════════╪═══════════════════════════════╝
               │ raw PDFs                                     │ generated stores
               ▼                                              ▼
   ┌────────────────────────────┐            ┌───────────────────────────────────────────────┐
   │  DATASETS                  │            │  DATA (generated, gitignored)                 │
   │  raw_pdfs/<category>/*.pdf │            │  chroma/, vector_store.pkl,                   │
   │  parsed/<category>/*.json  │            │  bm25.pkl, embedding_cache.pkl                │
   └────────────────────────────┘            └───────────────────────────────────────────────┘

                  ┌──────────────────────────────────────────────────────────────────┐
                  │  TRAINING — reranker_finetune/                                   │
                  │  00_merge_corpus → 01_mine_hard_negatives → 02_generate_queries  │
                  │  → 03_build_training_pairs → 04_finetune_reranker                │
                  │  output: finetuned_reranker  ──▶  loaded by reranker.py          │
                  └──────────────────────────────────────────────────────────────────┘
```

### Directory layout

```
legal_advisor/
├── ai_service/            # Python RAG pipeline
│   └── app/
│       ├── config.py      # Paths for parsed data and stores
│       ├── retrieval/     # Semantic routing (query → category/intent)
│       │   ├── semantic_router.py
│       │   ├── query_router.py
│       │   └── bm25_retriever.py
│       └── rag/           # Ingestion + retrieval core
│           ├── parser.py            # PDF → structured sections
│           ├── chunker.py           # section-aware chunking
│           ├── embedder.py          # BAAI/bge-m3 embeddings
│           ├── vectordb.py          # ChromaDB vector store
│           ├── ingest.py            # build vector store + BM25 index
│           ├── retrieve.py          # hybrid retrieval + scoring
│           ├── reranker.py          # fine-tuned cross-encoder rerank
│           ├── intent_expander.py   # query → legal intents
│           ├── query_context_builder.py
│           ├── retrieval_context.py
│           ├── category_prototypes.py
│           ├── intent_index.json
│           └── eval.py              # Hit@1/3/5, MRR harness
├── datasets/
│   ├── raw_pdfs/<category>/      # source statute PDFs (gitignored)
│   └── parsed/<category>/        # structured section JSON per Act
├── training/
│   └── reranker_finetune/        # reranker fine-tuning pipeline
├── backend/                      # Node/TypeScript API (in progress)
├── frontend/                     # React + Vite UI (in progress)
└── data/                         # embeddings, vector store, BM25 (generated)
```

### Retrieval pipeline (per query)

1. **Route** — `semantic_router` maps the raw query to a legal domain (criminal, family, labour, consumer, ...) with a confidence score.
2. **Expand** — `intent_expander` matches the query to known legal intents (from `intent_index.json`) and builds an expanded query with curated legal vocabulary.
3. **Recall** — `retrieve.py` fetches candidates via multiple query views through a single Chroma query plus BM25 candidates, with category filtering and fallback widening.
4. **Score** — a blend of semantic similarity, BM25 relevance, section-title overlap, category match, and Act-name match.
5. **Rerank** — the fine-tuned cross-encoder reranks the top-50 candidates; the top-k are returned with full citation metadata (Act, section number, title, chapter).

### Covering Acts by category

| Category | Acts |
|----------|------|
| criminal | BNSS 2023, BNS 2023, BSA 2023, NDPS 1985, Arms Act 1959 |
| women_child | PWDVA 2005, POCSO 2012, POSH 2013, Dowry Prohibition 1961, JJ Act 2015 |
| family | Hindu Marriage 1955, Special Marriage 1954, Hindu Succession 1956, Indian Succession 1925, Guardians & Wards 1890 |
| labour | Code on Wages 2019, OSH Code 2020, Industrial Disputes 1947, Maternity Benefit 1961, EPF 1952, Payment of Wages 1936, Employees Compensation 1923, Social Security Code 2020, Factories Act 1948 |
| consumer | Consumer Protection 2019, Legal Metrology 2009 |
| property | Transfer of Property 1882, Registration 1908 |
| cyber | IT Act 2000 |
| transport | Motor Vehicles 1988 |
| rights | RTI 2005, Legal Services Authorities 1987 |
| social_justice | RPWD 2016, SC/ST (POA) 1989, Senior Citizens 2007 |
| administrative | Passports Act 1967 |
| constitution | Constitution of India |

## Getting started

### Prerequisites

- Python 3.10+
- PyTorch with a CUDA-capable GPU (recommended; CPU works but is slow)
- Node.js 18+ and npm (for the frontend/backend)

### Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
pip install -r ai_service/requirements.txt

# 3. Configure the environment
cp .env.example .env    # set OPENROUTER_API_KEY for query generation
```

### Source PDFs

Place India Code statute PDFs under `datasets/raw_pdfs/<category>/`. Example:

```
datasets/raw_pdfs/
├── criminal/bharatiya_nyaya_sanhita_2023.pdf
├── family/hindu_marriage_act_1955.pdf
└── ...
```

Acts are recognized by `ACT_REGISTRY` in `ai_service/app/rag/parser.py` (keyed by filename stem). See `parser.py --show-unregistered` to find PDFs lacking registry metadata.

## Usage

### 1. Parse PDFs into structured JSON

```bash
python -m ai_service.app.rag.parser                    # parse all PDFs
python -m ai_service.app.rag.parser --act the_arms_act_1959   # one Act
python -m ai_service.app.rag.parser --verbose
```

Output is written to `datasets/parsed/<category>/<stem>.json`.

### 2. Ingest into the vector store + BM25 index

```bash
python -m ai_service.app.rag.ingest
python -m ai_service.app.rag.ingest --reset    # rebuild from scratch
```

This builds:
- `ai_service/app/data/chroma/` — the ChromaDB vector store
- `ai_service/app/data/vector_store.pkl` — document metadata store
- `ai_service/app/data/bm25.pkl` — lexical index
- `ai_service/app/data/embedding_cache.pkl` — cached embeddings

### 3. Run retrieval

```python
from ai_service.app.rag.retrieve import retrieve

result = retrieve(
    "Can a minor be tried as an adult in serious cases?",
    top_k=5,
)
for r in result["results"]:
    print(r["citation"], r["final_score"])
```

### 4. Evaluate retrieval quality

```bash
python -m ai_service.app.rag.eval            # full harness, Hit@1/3/5 + MRR
python -m ai_service.app.rag.eval --top-k 5 --verbose
```

Test cases live in `ai_service/app/rag/retrieval_test_cases.py` (each has a query and expected preferred/acceptable citations).

## Reranker training

The reranker is fine-tuned from `BAAI/bge-reranker-v2-m3` to separate confusable sibling sections of the same Act. Pipeline (in `training/reranker_finetune/`):

```bash
# 1. Flatten the parsed corpus into one file
python 00_merge_corpus.py ../../datasets/parsed corpus.json

# 2. Mine hard negatives (adjacent sections + similar titles)
python 01_mine_hard_negatives.py corpus.json hard_negatives.json

# 3. Generate natural-language queries per section (needs .env OPENROUTER_API_KEY)
python 02_generate_queries.py hard_negatives.json section_queries.json

# 4. Build (query, doc, label) training pairs
python 03_build_training_pairs.py hard_negatives.json section_queries.json training_pairs.json

# 5. Fine-tune the cross-encoder
python 04_finetune_reranker.py training_pairs.json ./finetuned_reranker
```

After training, `reranker.py` loads the fine-tuned model from `training/reranker_finetune/finetuned_reranker` automatically. Validate against `eval.py` before adopting a new model — only keep it if strict Hit@1/3/5 improve without regressing the previously-passing cases.

## Frontend (in progress)

React + Vite + TypeScript app in `frontend/`. Currently the default Vite scaffold while the UI is being built.

```bash
cd frontend
npm install
npm run dev
```

## Configuration

- `ai_service/app/config.py` — base data and parsed-directory paths.
- `ai_service/app/rag/parser.py` — `ACT_REGISTRY`: each Act's full name, short name, year, ministry, and category.
- `ai_service/app/rag/category_prototypes.py` — domain descriptions used by the semantic router.
- `ai_service/app/rag/intent_index.json` — legal intents with example queries and prototypes used for query expansion.
- `ai_service/app/rag/reranker.py` — reranker model path and score-blend weights.

## Project layout notes

- `frontend/`, `backend/`, and `ai_service/` are the three main subsystems; only the Python RAG core is fully implemented so far.
- `datasets/raw_pdfs/` and generated artifacts (`ai_service/app/data/`, `chroma_db/`) are gitignored — they are built from source documents.

## License

TBD.
