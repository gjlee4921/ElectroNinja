# vector_store.py

import os
import numpy as np
import logging
import pickle
import json
import openai
from typing import List, Dict, Any, Optional
from electroninja.config.settings import Config
from electroninja.utils.error_handler import ModelError, FileError

logger = logging.getLogger('electroninja')

class VectorStore:
    """Vector database for storing and retrieving circuit examples using semantic search"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.embedding_model = "text-embedding-3-small"
        self.vector_size = 1536
        self.metadata_list = []
        self.index = None
        
        # Set OpenAI API key
        openai.api_key = self.config.OPENAI_API_KEY
        
        # Import FAISS
        try:
            import faiss
            self.faiss = faiss
            self.index = faiss.IndexFlatL2(self.vector_size)
            logger.info("FAISS index initialized")
        except ImportError:
            logger.error("Failed to import FAISS. Vector search will not be available.")
            self.faiss = None
            
    def load(self):
        """
        Load the index and metadata from disk, or build from metadata.json if not found
        
        Returns:
            bool: True if successfully loaded or built, False otherwise
        """
        try:
            if self.faiss is None:
                logger.error("FAISS is not available. Cannot load index.")
                return False
                
            index_path = self.config.VECTOR_DB_INDEX
            metadata_path = self.config.VECTOR_DB_METADATA
            
            # Try to load existing index and metadata
            if os.path.exists(index_path) and os.path.exists(metadata_path):
                self.index = self.faiss.read_index(index_path)
                
                with open(metadata_path, "rb") as f:
                    self.metadata_list = pickle.load(f)
                    
                logger.info(f"Loaded index with {len(self.metadata_list)} documents")
                return True
            else:
                # If index doesn't exist, try to build from metadata.json
                logger.warning("Saved index or metadata file not found. Attempting to build from metadata.json")
                return self._build_index_from_metadata()
                
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            return False
    
    def _build_index_from_metadata(self):
        """
        Build the index from metadata.json file
        
        Returns:
            bool: True if successfully built, False otherwise
        """
        try:
            metadata_json_path = os.path.join(self.config.EXAMPLES_DIR, "metadata.json")
            
            if not os.path.exists(metadata_json_path):
                logger.error(f"Metadata file not found: {metadata_json_path}")
                return False
                
            with open(metadata_json_path, "r", encoding="utf-8") as f:
                examples = json.load(f)
                
            logger.info(f"Found {len(examples)} examples in metadata.json")
            
            # Process each example
            successful_count = 0
            for i, example in enumerate(examples, 1):
                asc_path = example.get("asc_path")
                description = example.get("description", "No description")
                
                # Check if path is valid
                if not asc_path:
                    logger.warning(f"Example {i}: Missing asc_path")
                    continue
                
                # Convert relative path if needed
                if not os.path.isabs(asc_path):
                    asc_path = os.path.join(self.config.BASE_DIR, asc_path)
                
                if os.path.exists(asc_path):
                    try:
                        with open(asc_path, "r", encoding="utf-8") as asc_file:
                            asc_code = asc_file.read()
                        
                        # Combine description and ASC code for embedding
                        combined_text = f"{description}\n\nASC CODE:\n{asc_code}"
                        
                        # Add to index
                        if self.add_document(combined_text, metadata={"asc_path": asc_path, "description": description}):
                            successful_count += 1
                            logger.info(f"Added example {i}: {os.path.basename(asc_path)}")
                    except Exception as e:
                        logger.warning(f"Failed to process {asc_path}: {str(e)}")
                else:
                    logger.warning(f"File not found: {asc_path}")
            
            # Save the built index
            if successful_count > 0:
                self.save()
                logger.info(f"Built and saved index with {successful_count} documents")
                return True
            else:
                logger.error("Failed to build index: No valid examples found")
                return False
                
        except Exception as e:
            logger.error(f"Failed to build index from metadata: {str(e)}")
            return False
            
    def save(self):
        """
        Save the index and metadata to disk
        
        Returns:
            bool: True if successfully saved, False otherwise
        """
        try:
            if self.faiss is None or self.index is None:
                logger.error("FAISS is not available or index is not initialized.")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config.VECTOR_DB_INDEX), exist_ok=True)
            
            # Save FAISS index
            self.faiss.write_index(self.index, self.config.VECTOR_DB_INDEX)
            
            # Save metadata
            with open(self.config.VECTOR_DB_METADATA, "wb") as f:
                pickle.dump(self.metadata_list, f)
                
            logger.info(f"Saved index with {len(self.metadata_list)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            return False
            
    def add_document(self, asc_code: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add a document to the vector store
        
        Args:
            asc_code (str): ASC code or combined text to embed
            metadata (dict, optional): Additional metadata
            
        Returns:
            bool: True if successfully added, False otherwise
        """
        try:
            if self.faiss is None or self.index is None:
                logger.error("FAISS is not available or index is not initialized.")
                return False
                
            # Embed the text
            vector = self.embed_text(asc_code)
            vector = np.expand_dims(vector, axis=0)  # shape: (1, vector_size)
            
            # Add to FAISS index
            self.index.add(vector)
            
            # Add to metadata list
            doc = {"asc_code": asc_code}
            if metadata:
                doc.update(metadata)
            self.metadata_list.append(doc)
            
            logger.info(f"Document added. Total documents: {len(self.metadata_list)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return False
            
    def search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_text (str): Query text to search for
            top_k (int): Number of results to return
            
        Returns:
            list: List of matching documents with metadata and scores
        """
        try:
            if self.faiss is None or self.index is None:
                logger.error("FAISS is not available or index is not initialized.")
                return []
                
            # Check if database is empty
            if len(self.metadata_list) == 0:
                # Try to build index from metadata if empty
                logger.warning("No documents in the database. Attempting to build from metadata.json")
                if not self._build_index_from_metadata():
                    return []
            
            # Adjust top_k to not exceed number of documents
            effective_top_k = min(top_k, len(self.metadata_list))
            
            # Embed the query
            query_vector = self.embed_text(query_text)
            query_vector = np.expand_dims(query_vector, axis=0)
            
            # Search
            distances, indices = self.index.search(query_vector, effective_top_k)
            
            # Build results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1 or idx >= len(self.metadata_list):
                    continue
                
                # Get the metadata and full stored text
                metadata = {k: v for k, v in self.metadata_list[idx].items() if k != "asc_code"}
                full_text = self.metadata_list[idx].get("asc_code", "")
                
                # Extract just the ASC code portion to avoid duplication
                # If the format is consistent with "ASC CODE:" marker
                asc_code = full_text
                if "\nASC CODE:\n" in full_text:
                    asc_code = full_text.split("\nASC CODE:\n", 1)[1]
                
                results.append({
                    "asc_code": asc_code,
                    "metadata": metadata,
                    "score": float(distances[0][i])
                })
                
            logger.info(f"Found {len(results)} similar documents for query: '{query_text[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
            
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate an embedding for text
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Embedding vector
            
        Raises:
            ModelError: If embedding fails
        """
        try:
            # Clean text
            text = text.replace("\n", " ")
            
            # Get embedding from OpenAI
            response = openai.Embedding.create(
                input=[text],
                model=self.embedding_model
            )
            
            # Extract embedding
            embedding = response["data"][0]["embedding"]
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            raise ModelError(f"Failed to generate embedding: {str(e)}")
            
    def get_document_count(self):
        """Get the number of documents in the index"""
        return len(self.metadata_list)
        
    def clear(self):
        """Clear the index and metadata"""
        if self.faiss is not None:
            self.index = self.faiss.IndexFlatL2(self.vector_size)
            self.metadata_list = []
            logger.info("Index and metadata cleared")
            return True
        return False