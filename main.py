from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_core import create_rag_chain

app = FastAPI(
    title="Campus RAG API",
    description="Query college information via a RAG pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    rag_chain = create_rag_chain()
    print("RAG chain created successfully.")
except Exception as e:
    print(f"FATAL: Error creating RAG chain: {e}")
    rag_chain = None

class Query(BaseModel):
    text: str

@app.post("/chat")
def chat_with_rag(query: Query):
    if not rag_chain:
        raise HTTPException(status_code=500, detail="RAG chain is not available due to startup error.")
    try:
        response = rag_chain.invoke(query.text)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during query: {e}")

@app.get("/")
def read_root():
    return {"status": "API is up and running."}
