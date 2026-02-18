# README.md — Campus RAG Chatbot (FastAPI + Streamlit + Chroma + Reranker + OpenRouter)

A campus chatbot built with a Retrieval-Augmented Generation (RAG) pipeline.  
It scrapes selected campus web pages and downloads PDFs, indexes them into a local Chroma vector database, retrieves and reranks relevant chunks, and generates grounded answers using an OpenRouter-hosted LLM.

## Features
- Scrapes HTML pages and downloads same-domain PDFs into a local data folder.
- Detects HTML updates using SHA-1 hash comparison and updates only changed pages.
- Chunks content, creates embeddings locally, and persists vectors in Chroma.
- Query-time retrieval with cross-encoder reranking for better relevance.
- FastAPI backend endpoint for chat and a Streamlit chat UI.

## Project Structure
- ingest.py: Scrape + parse + chunk + embed + store in vector DB
- rag_core.py: Builds RAG chain (retriever + reranker + LLM)
- main.py: FastAPI server exposing chat API
- app.py: Streamlit UI client
- requirements.txt: Python dependencies

## Requirements
- Python 3.10 or newer recommended
- Internet access for scraping and LLM calls
- Enough disk space for model downloads (first run may download embedding/reranker models)

## Setup
1) Create and activate a virtual environment (recommended)
- Linux/WSL
  - python3 -m venv virenv
  - source virenv/bin/activate

2) Install dependencies
- pip install -r requirements.txt

## Configuration
Create a file named .env in the project root and add:
- OPENROUTER_API_KEY=your_key_here

Important: If you change the key later, restart the backend server so it reads the updated value.

## Step 1 — Ingest Data (build/update vector database)
Run:
- python ingest.py

What happens:
- Saves each scraped page as an HTML file using a unique filename derived from domain + path + query string.
- Updates an existing HTML file only if the content hash changes.
- Downloads PDFs only if the filename does not already exist locally.
- Extracts text from HTML and PDFs, splits into chunks, embeds chunks, and persists the vector index in the chroma_db directory.

If you want a clean rebuild:
- Delete the data folder and chroma_db folder, then run python ingest.py again.

## Step 2 — Start the Backend (FastAPI)
Run:
- uvicorn main:app --reload --host 0.0.0.0 --port 8000

API endpoints:
- GET / returns a simple status JSON
- POST /chat accepts JSON like {"text":"your question"} and returns {"answer":"..."}

Quick test:
- curl -s http://127.0.0.1:8000/
- curl -s -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"text":"Hello"}'

## Step 3 — Start the Frontend (Streamlit)
In a new terminal (same venv):
- streamlit run app.py

In the Streamlit sidebar:
- Set API base URL to http://127.0.0.1:8000
- Click Recheck API
- Ask questions in the chat input

## Common Issues
1) 401 Unauthorized from the LLM
- The OpenRouter key is missing or invalid.
- Confirm .env contains OPENROUTER_API_KEY and restart the backend.
- You can also export it in the same terminal before running uvicorn:
  - export OPENROUTER_API_KEY=your_key_here

2) Streamlit says backend is not reachable
- Confirm the backend is running and GET / returns status JSON.
- Ensure API base URL is only the base (http://127.0.0.1:8000) and not a longer path.
- If running in WSL, keep both backend and frontend in the same environment and bind backend to 0.0.0.0 as shown above.

3) Model downloads on first run
- Embedding and reranker models may download the first time and then be cached.
- Wait for downloads to complete and retry.

4) The chatbot answers “I don’t know”
- This is expected when the retrieved context does not contain the answer.
- Try asking a more specific question or re-run ingestion to ensure the latest pages are indexed.
- You can also tune retrieval parameters in rag_core.py (top-k and top_n).

## Notes
- HTML update detection is implemented via hashing old vs new HTML content.
- PDF update detection is not implemented; PDFs are skipped if a file with the same name already exists.
- The embedding model is all-MiniLM-L6-v2 and reranker is bge-reranker-base by default.

