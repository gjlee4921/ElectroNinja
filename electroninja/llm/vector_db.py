import os
import openai
import numpy as np
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import pickle

# Load environment variables (including OPENAI_API_KEY)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

class VectorDB:
    """
    A simple vector database handler for storing circuit examples and performing semantic searches using FAISS.
    
    This implementation:
      - Uses OpenAI's embedding API (e.g., "text-embedding-3-small") to embed text.
      - Stores embeddings in a FAISS index (in-memory).
      - Maintains metadata in a list parallel to the FAISS index.
      
    Each document should include:
      - The ASC code (or combined text: description + ASC code)
      - Metadata with keys:
            "asc_path": file path to the .asc file,
            "description": a short description of the circuit.
    """
    def __init__(self, embedding_model: str = "text-embedding-3-small", vector_size: int = 1536):
        self.embedding_model = embedding_model
        self.vector_size = vector_size
        
        # Import and create a FAISS index
        import faiss
        self.index = faiss.IndexFlatL2(vector_size)  # Using L2 distance
        
        # List to store metadata for each document (in the same order as vectors added)
        self.metadata_list = []

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generates an embedding vector for the given text using OpenAI.
        
        :param text: The text to embed (e.g., combined description and ASC code).
        :return: A numpy array (dtype=np.float32) representing the embedding.
        """
        text = text.replace("\n", " ")
        response = openai.Embedding.create(
            input=[text],
            model=self.embedding_model
        )
        embedding = response["data"][0]["embedding"]
        return np.array(embedding, dtype=np.float32)

    def add_document(self, asc_code: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Embeds the given ASC text (or combined text) and inserts it into the FAISS index.
        
        :param asc_code: The text of the ASC code (or combination of description and ASC code) to store.
        :param metadata: Additional metadata, e.g. {"asc_path": "...", "description": "..."}
        """
        vector = self.embed_text(asc_code)
        vector = np.expand_dims(vector, axis=0)  # shape: (1, vector_size)
        self.index.add(vector)
        
        doc = {"asc_code": asc_code}
        if metadata:
            doc.update(metadata)
        self.metadata_list.append(doc)
        
        print(f"Document added. Total documents: {len(self.metadata_list)}")

    def search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs a semantic search over the ASC code examples.
        
        :param query_text: The text to search with (e.g., user query).
        :param top_k: Number of most similar results to return.
        :return: A list of dictionaries, each containing the stored 'asc_code', metadata, and similarity 'score'.
        """
        if len(self.metadata_list) == 0:
            print("No documents in the database.")
            return []
        
        query_vector = self.embed_text(query_text)
        query_vector = np.expand_dims(query_vector, axis=0)
        distances, indices = self.index.search(query_vector, top_k)
        
        print("FAISS search results:")
        print("Indices:", indices)
        print("Distances:", distances)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(self.metadata_list):
                continue
            results.append({
                "asc_code": self.metadata_list[idx].get("asc_code", ""),
                "metadata": {k: v for k, v in self.metadata_list[idx].items() if k != "asc_code"},
                "score": distances[0][i]
            })
        return results

    def save_index(self, index_path: str, metadata_path: str):
        """
        Saves the FAISS index and metadata list to disk.
        
        :param index_path: File path to save the FAISS index.
        :param metadata_path: File path to save the metadata list.
        """
        import faiss
        faiss.write_index(self.index, index_path)
        with open(metadata_path, "wb") as f:
            pickle.dump(self.metadata_list, f)
        print(f"Index and metadata saved to {index_path} and {metadata_path}.")

    def load_index(self, index_path: str, metadata_path: str):
        """
        Loads the FAISS index and metadata list from disk.
        
        :param index_path: File path from which to load the FAISS index.
        :param metadata_path: File path from which to load the metadata list.
        """
        import faiss
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, "rb") as f:
                self.metadata_list = pickle.load(f)
            print(f"Loaded index with {len(self.metadata_list)} documents from {index_path} and {metadata_path}.")
        else:
            print("Saved index or metadata file not found.")
