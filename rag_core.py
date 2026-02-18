import os
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings  # pip install -U langchain-huggingface
from langchain_chroma import Chroma  # pip install -U langchain-chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers import ContextualCompressionRetriever

load_dotenv()

CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "meta-llama/llama-3-8b-instruct"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"

def create_rag_chain():
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
    )

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})

    cross_encoder = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL_NAME)
    reranker = CrossEncoderReranker(model=cross_encoder, top_n=5)
    retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=base_retriever,
    )

    llm = ChatOpenAI(
        model=GENERATION_MODEL_NAME,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2,
        max_tokens=512,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",
             "You are a helpful campus assistant. Answer only from the provided context. "
             "If the answer is not in the context, say you do not know.\n\nContext:\n{context}"),
            ("human", "{question}"),
        ]
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain
