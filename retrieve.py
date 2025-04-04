import sys
from backend.llm.vector_db import VectorDB

def main():
    # Create a VectorDB instance
    db = VectorDB()
    
    # Load the saved index and metadata (adjust paths as needed)
    index_path = "faiss_index.bin"
    metadata_path = "metadata_list.pkl"
    db.load_index(index_path, metadata_path)
    
    # Ask the user for a query
    query = input("Enter your query: ")
    
    # Perform a semantic search for the top 3 documents
    results = db.search(query, top_k=3)
    
    if not results:
        print("No results found.")
    else:
        for i, res in enumerate(results, start=1):
            description = res["metadata"].get("description", "No description")
            asc_code = res["asc_code"]
            score = res["score"]
            print(f"\nResult {i}:")
            print(f"Description: {description}")
            print("ASC Code:")
            print(asc_code)
            print(f"Similarity Score: {score:.4f}")

if __name__ == "__main__":
    main()
