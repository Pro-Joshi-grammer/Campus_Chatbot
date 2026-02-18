import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from dotenv import load_dotenv

from langchain_community.document_loaders import PyMuPDFLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Prefer new packages to avoid deprecations; fallback to community if missing
try:
    from langchain_chroma import Chroma  # pip install -U langchain-chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings  # pip install -U langchain-huggingface
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# --- CONFIGURATION ---

load_dotenv()

URLS_TO_SCRAPE = [
    "https://www.iare.ac.in/?q=pages/cse-artificial-intelligence-and-machine-learning",
    "https://www.iare.ac.in/?q=pages/btech-course-syllabi-bt23-cseaiml",
    "https://www.iare.ac.in/?q=basicpage/student-start-and-innovation",
    "https://www.iare.ac.in/?q=departmentlist/113",
    "https://www.iare.ac.in/?q=pages/cse-ai-ml-contact-hod",
    "https://www.iare.ac.in/?q=pages/placement-branch-statistics",
    "https://www.iare.ac.in/?q=pages/rd-paper-publications",
]

DATA_DIR = "data"
CHROMA_DB_DIR = "./chroma_db"

# Local embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

HTML_WRITE_STRATEGY = "if_changed"  # "always" or "if_changed"
DOWNLOAD_TIMEOUT = 30
REQUEST_TIMEOUT = 20
SAME_DOMAIN_ONLY = True
PDF_SLEEP_SEC = 0.5


def _sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _should_write_html(path: str, new_content: str) -> bool:
    if HTML_WRITE_STRATEGY == "always":
        return True
    if not os.path.exists(path):
        return True
    try:
        with open(path, "r", encoding="utf-8") as f:
            old = f.read()
        return _sha1_text(old) != _sha1_text(new_content)
    except Exception:
        return True


def _safe_name_from_url(url: str, max_len: int = 180) -> str:
    u = urlparse(url)
    # Include domain, path and query to ensure uniqueness across ?q=... pages
    raw = f"{u.netloc}{u.path}?{u.query}" if u.query else f"{u.netloc}{u.path}"
    normalized = raw.replace("/", "_").replace("\\", "_").strip("_")
    safe = quote(normalized, safe="._-")
    return safe[:max_len] or "homepage"


def scrape_websites(urls, data_dir):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    for url in urls:
        if not url or not url.strip() or not url.startswith("http"):
            print(f"Skipping invalid URL: '{url}'")
            continue

        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            page_name = _safe_name_from_url(url)
            html_path = os.path.join(data_dir, f"{page_name}.html")

            pretty_html = soup.prettify()
            if _should_write_html(html_path, pretty_html):
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(pretty_html)
                print(f"Saved HTML: {html_path}")
            else:
                print(f"Skipped unchanged HTML: {html_path}")

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if not href:
                    continue
                if href.lower().endswith(".pdf"):
                    pdf_url = urljoin(url, href)
                    if SAME_DOMAIN_ONLY and urlparse(pdf_url).netloc != urlparse(url).netloc:
                        continue

                    pdf_name = os.path.basename(urlparse(pdf_url).path) or "file.pdf"
                    pdf_path = os.path.join(data_dir, pdf_name)
                    if os.path.exists(pdf_path):
                        print(f" -> Skipping existing: {pdf_name}")
                        continue

                    try:
                        print(f" -> Downloading: {pdf_name}")
                        pdf_response = requests.get(pdf_url, timeout=DOWNLOAD_TIMEOUT)
                        pdf_response.raise_for_status()
                        with open(pdf_path, "wb") as pf:
                            pf.write(pdf_response.content)
                        time.sleep(PDF_SLEEP_SEC)
                    except requests.RequestException as pe:
                        print(f"Failed to download {pdf_url}: {pe}")

        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")


def _extract_visible_text_from_html_file(path: str) -> str:
    """Fallback extractor to ensure useful text if loader under-extracts."""
    try:
        from bs4 import BeautifulSoup
        with open(path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text
    except Exception:
        return ""


def ingest_data():
    print("\n--- Ingestion Start ---")
    docs = []

    if not os.path.exists(DATA_DIR):
        print(f"No data directory '{DATA_DIR}'. Run scraper first.")
        return

    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)

        if filename.lower().endswith(".pdf"):
            try:
                loader = PyMuPDFLoader(file_path)
                docs.extend(loader.load())
                print(f"Loaded PDF: {filename}")
            except Exception as e:
                print(f"Failed to load PDF {filename}: {e}")

        elif filename.lower().endswith(".html"):
            try:
                # Try a direct visible-text extraction first
                text = _extract_visible_text_from_html_file(file_path)
                if text and len(text) > 200:
                    from langchain.schema import Document
                    docs.append(Document(page_content=text, metadata={"source": file_path}))
                    print(f"Loaded HTML (visible text): {filename} ({len(text)} chars)")
                else:
                    loader = WebBaseLoader(f"file://{os.path.abspath(file_path)}")
                    loaded = loader.load()
                    docs.extend(loaded)
                    print(f"Loaded HTML via loader: {filename} ({len(loaded)} docs)")
            except Exception as e:
                print(f"Failed to load HTML {filename}: {e}")

    if not docs:
        print("No documents found in data/. Exiting.")
        return

    print(f"Total documents: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    splits = splitter.split_documents(docs)
    print(f"Total chunks: {len(splits)}")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    print("Persisting Chroma index...")
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
    )
    print(f"Chroma DB ready at: {CHROMA_DB_DIR}\n--- Ingestion Done ---")


if __name__ == "__main__":
    scrape_websites(URLS_TO_SCRAPE, DATA_DIR)
    ingest_data()
