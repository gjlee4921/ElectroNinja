# electroninja/llm/vector_db.py

import os
import openai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Qdrant client
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

# Load environment variables (OPENAI_API_KEY, etc.)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI with your API key
openai.api_key = OPENAI_API_KEY

class VectorDB:
    """
    A simple vector database handler for storing .asc code examples (plus optional metadata)
    and performing semantic searches.

    Internally uses Qdrant as the vector store, and OpenAI for text embeddings.
    """

    def __init__(
        self,
        collection_name: str = "asc_code_examples",
        host: str = "localhost",
        port: int = 6333,
        embedding_model: str = "text-embedding-3-small",
        vector_size: int = 1536
    ):
        """
        :param collection_name: Name of the Qdrant collection.
        :param host: Host where Qdrant is running.
        :param port: Port for Qdrant.
        :param embedding_model: Which OpenAI embedding model to use.
        :param vector_size: Dimension of the embedding vector (e.g. 1536 for text-embedding-3-small).
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.embedding_model = embedding_model
        self.vector_size = vector_size

        # Connect to Qdrant
        self.client = QdrantClient(
            url=f"http://{self.host}:{self.port}",
            prefer_grpc=False  # or True if you want gRPC
        )

        # Ensure the collection is created
        self._create_collection()

    def _create_collection(self):
        """
        Creates the Qdrant collection if it doesn't already exist.
        """
        try:
            self.client.get_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' already exists.")
        except:
            print(f"Creating collection '{self.collection_name}'...")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self.vector_size,
                    distance=qdrant_models.Distance.COSINE
                )
            )

    def embed_text(self, text: str) -> List[float]:
        """
        Uses OpenAI to generate an embedding vector for the given text.
        :param text: The text to embed (e.g. .asc code or description).
        :return: List of floats representing the embedding.
        """
        text = text.replace("\n", " ")
        response = openai.Embedding.create(
            input=text,
            model=self.embedding_model
        )
        embedding = response["data"][0]["embedding"]
        return embedding

    def add_document(
        self,
        asc_code: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Embeds the given .asc code (or combined text) and inserts it into the Qdrant collection.
        :param asc_code: The text of the .asc code (or a combination of code + description).
        :param metadata: Additional info, e.g. {"asc_path": "...", "description": "..."}
        """
        # Generate embedding
        vector = self.embed_text(asc_code)

        # Build Qdrant payload
        payload = {
            "asc_code": asc_code
        }
        if metadata:
            payload.update(metadata)

        # Generate a unique ID (short random integer from UUID)
        import uuid
        point_id = uuid.uuid4().int >> 96

        # Upsert the point into Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qdrant_models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print(f"Inserted document with ID={point_id}")

    def search(
        self,
        query_text: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Given a query text, embed it and find the most similar .asc code docs.
        :param query_text: The text to search with (e.g. user prompt).
        :param top_k: Number of most similar results to return.
        :return: A list of results, each containing 'asc_code' and any other stored metadata.
        """
        # Embed the query
        query_vector = self.embed_text(query_text)

        # Perform similarity search in Qdrant
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )

        # Qdrant returns a list of ScoredPoint objects
        results = []
        for point in search_result:
            results.append({
                "asc_code": point.payload.get("asc_code", ""),
                "metadata": {
                    k: v for k, v in point.payload.items() if k != "asc_code"
                },
                "score": point.score
            })

        return results
