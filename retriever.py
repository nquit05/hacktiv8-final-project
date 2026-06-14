from google import genai
from google.genai import types
from qdrant_rest import QdrantRest

COLLECTION = "portfolio"

def get_retriever(google_api_key: str, qdrant_url: str, qdrant_api_key: str):
    client_google = genai.Client(api_key=google_api_key, http_options={"api_version": "v1"})
    qdrant        = QdrantRest(url=qdrant_url, api_key=qdrant_api_key)

    def retrieve(query: str, top_k: int = 4) -> str:
        result = client_google.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        vec = result.embeddings[0].values

        results = qdrant.search(
            collection=COLLECTION,
            vector=vec,
            top_k=top_k,
            score_threshold=0.45
        )
        chunks = [r["payload"]["content"] for r in results]
        return "\n\n---\n\n".join(chunks) if chunks else ""

    return retrieve