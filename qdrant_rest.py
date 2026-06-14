import requests

class QdrantRest:
    def __init__(self, url: str, api_key: str):
        self.base = url.rstrip("/")
        self.headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }

    def get_collections(self):
        r = requests.get(f"{self.base}/collections", headers=self.headers)
        return r.json()

    def create_collection(self, name: str, size: int):
        r = requests.put(
            f"{self.base}/collections/{name}",
            headers=self.headers,
            json={"vectors": {"size": size, "distance": "Cosine"}}
        )
        return r.json()

    def delete_collection(self, name: str):
        r = requests.delete(f"{self.base}/collections/{name}", headers=self.headers)
        return r.json()

    def upsert(self, collection: str, points: list):
        r = requests.put(
            f"{self.base}/collections/{collection}/points",
            headers=self.headers,
            json={"points": points}
        )
        return r.json()

    def search(self, collection: str, vector: list, top_k: int = 4, score_threshold: float = 0.45):
        r = requests.post(
            f"{self.base}/collections/{collection}/points/search",
            headers=self.headers,
            json={
                "vector": vector,
                "limit": top_k,
                "score_threshold": score_threshold,
                "with_payload": True
            }
        )
        return r.json().get("result", [])