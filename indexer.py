import os, uuid
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_rest import QdrantRest

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
QDRANT_URL     = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION     = "portfolio"

client_google = genai.Client(api_key=GOOGLE_API_KEY, http_options={"api_version": "v1"})
qdrant        = QdrantRest(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def embed(text: str) -> list:
    result = client_google.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return result.embeddings[0].values

def init_collection():
    existing = [c["name"] for c in qdrant.get_collections()["result"]["collections"]]
    if COLLECTION in existing:
        qdrant.delete_collection(COLLECTION)
    result = qdrant.create_collection(COLLECTION, size=3072)
    print(f"Create collection result: {result}")

def index_from_file(html_path: str):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "head"]):
        tag.decompose()

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
    sections = soup.find_all(["section", "article", "main", "div"], id=True)

    # Fallback ke semua text jika tidak ada section dengan id
    if not sections:
        text = soup.get_text(separator=" ", strip=True)
        sections_text = splitter.split_text(text)
        init_collection()
        points = []
        for chunk in sections_text:
            if len(chunk) < 60:
                continue
            points.append({
                "id": str(uuid.uuid4()),
                "vector": embed(chunk),
                "payload": {"content": chunk, "section": "general"}
            })
        qdrant.upsert(COLLECTION, points)
        print(f"✅ Indexed {len(points)} chunks.")
        return

    init_collection()
    points = []
    for sec in sections:
        text = sec.get_text(separator=" ", strip=True)
        if len(text) < 60:
            continue
        for chunk in splitter.split_text(text):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": embed(chunk),
                "payload": {
                    "content": chunk,
                    "section": sec.get("id", "general")
                }
            })

    result = qdrant.upsert(COLLECTION, points)
    print(f"Upsert result: {result}")
    print(f"✅ Indexed {len(points)} chunks.")
    
if __name__ == "__main__":
    index_from_file("portfolio.html")