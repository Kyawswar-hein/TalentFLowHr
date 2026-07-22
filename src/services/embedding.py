import ollama
from src.core.config import settings

class EmbeddingService:
    def __init__(self):
        # nomic-embed-text matches your current 768-dimension schema layout
        self.model = "nomic-embed-text"
        self._client = None

    @property
    def client(self) -> ollama.AsyncClient:
        """Lazily instantiates the asynchronous Ollama client."""
        if self._client is None:
            # Connects to your local instance (default: http://localhost:11434)
            self._client = ollama.AsyncClient()
        return self._client

    async def get_embedding(self, text: str, is_query: bool = False) -> list[float]:
        """
        Generates a local 768-dimensional embedding vector for a single string.
        Applies Nomic task prefixes based on usage (query vs document storage).
        """
        prefix = "search_query: " if is_query else "search_document: "
        cleaned_text = f"{prefix}{text.replace('\n', ' ')}"
        
        response = await self.client.embed(
            model=self.model,
            input=cleaned_text
        )
        
        # Ollama returns a list of vectors inside the 'embeddings' key
        return response['embeddings'][0]

    async def get_embeddings_batch(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        """
        Generates local embeddings for a list of strings in a batch request.
        """
        prefix = "search_query: " if is_query else "search_document: "
        cleaned_texts = [f"{prefix}{text.replace('\n', ' ')}" for text in texts]
        
        response = await self.client.embed(
            model=self.model,
            input=cleaned_texts
        )
        
        return response['embeddings']

# Singleton instance
embedding_service = EmbeddingService()