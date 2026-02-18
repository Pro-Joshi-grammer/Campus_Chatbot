# README.md — Campus RAG Chatbot (FastAPI + Streamlit + Chroma + Reranker + OpenRouter)

A campus chatbot built with a Retrieval-Augmented Generation (RAG) pipeline.  
It scrapes selected campus web pages + downloads PDFs, indexes them into a local Chroma vector DB, retrieves and reranks relevant chunks, and generates grounded answers using an OpenRouter-hosted LLM.

***

## Features
- Scrapes **HTML pages** and downloads **same-domain PDFs** into `data/` [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Detects HTML updates using **SHA-1 hash comparison** (updates only changed pages) [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Splits content into chunks and stores embeddings in **Chroma** (`./chroma_db`) [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Query-time retrieval + **cross-encoder reranking** (`BAAI/bge-reranker-base`) [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)
- FastAPI backend (`/chat`) + Streamlit chat UI [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)

***

## Project Structure
- `ingest.py` — scrape + parse + chunk + embed + persist to Chroma [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- `rag_core.py` — RAG chain: Chroma retriever + reranker + OpenRouter LLM [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)
- `main.py` — FastAPI server exposing `/chat` and `/` [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a2b06faa-a727-47e5-86ca-7d4106a66464/main.py)
- `app.py` — Streamlit UI client [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)
- `requirements.txt` — dependencies [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a5ccb29e-8db2-4650-93f9-afd10d575428/requirements.txt)

***

## Requirements
- Python 3.10+ recommended (works in Linux/WSL)
- Internet access (for scraping + OpenRouter LLM + first-time model downloads)

Install dependencies: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a5ccb29e-8db2-4650-93f9-afd10d575428/requirements.txt)
```bash
pip install -r requirements.txt
```

***

## Configuration (OpenRouter)
Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
```

`rag_core.py` loads `.env` using `load_dotenv()` and reads `OPENROUTER_API_KEY` at runtime. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)

***

## Step 1 — Ingest Data (build/update vector DB)
Run the ingestion script to scrape pages/PDFs and build `./chroma_db`: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)

```bash
python ingest.py
```

What it does:
- Saves HTML snapshots with unique filenames based on domain/path/query (prevents overwrites). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Updates an HTML file only when its hash changes. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Downloads PDFs only if the file does not already exist (PDF hash checking is not implemented). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Parses HTML/PDF, chunks, embeds (MiniLM), and persists to Chroma. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)

***

## Step 2 — Start Backend (FastAPI)
Run:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a2b06faa-a727-47e5-86ca-7d4106a66464/main.py)
- `GET /` → health/status
- `POST /chat` → ask a question

Quick test:
```bash
curl -s http://127.0.0.1:8000/
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello"}'
```
The second call returns: `{"answer": "..."}` [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a2b06faa-a727-47e5-86ca-7d4106a66464/main.py)

***

## Step 3 — Start Frontend (Streamlit)
In a new terminal:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)

In the sidebar:
- Set **API base URL** to `http://127.0.0.1:8000` (base only, no `/chat`). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)
- Click **Recheck API**. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)

***

## Common Issues & Fixes

### 1) 401 from OpenRouter
If `/chat` returns 401, your OpenRouter key is missing/invalid.
- Ensure `.env` exists and contains `OPENROUTER_API_KEY=...`
- Restart uvicorn after changing `.env` (env changes require restart). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)

### 2) “Backend API not reachable” in Streamlit
- Verify `GET http://127.0.0.1:8000/` returns status JSON. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/a2b06faa-a727-47e5-86ca-7d4106a66464/main.py)
- Ensure Streamlit sidebar URL is exactly `http://127.0.0.1:8000` (no markdown brackets, no `/chat`). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/244ac1b7-5fa1-43a9-a800-41c95dd633fc/app.py)

### 3) First run downloads models
- Embedding and reranker models may download on first run (cached afterward). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)

***

## Notes
- HTML change detection is implemented via SHA-1 hash comparison of old vs new page content. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- PDFs are currently skipped if the filename already exists; PDF content updates with same name are not detected. [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/f729d627-6b84-4756-9502-6b0900924074/ingest.py)
- Retrieval defaults: top-k=20 and reranker top_n=5 (tunable in `rag_core.py`). [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/7139889/475e50ff-cc54-453d-8bf3-8cfd9e31ae72/rag_core.py)

***
