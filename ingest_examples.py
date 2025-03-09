import os
import json
from electroninja.llm.vector_db import VectorDB

def ingest_examples():
    db = VectorDB()
    metadata_path = "data/examples_asc/metadata.json"
    if not os.path.exists(metadata_path):
        print(f"Metadata file not found: {metadata_path}")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        examples = json.load(f)
    
    for example in examples:
        asc_path = example.get("asc_path")
        description = example.get("description", "No description")
        if asc_path and os.path.exists(asc_path):
            with open(asc_path, "r", encoding="utf-8") as asc_file:
                asc_code = asc_file.read()
            combined_text = f"{description}\n\nASC CODE:\n{asc_code}"
            db.add_document(combined_text, metadata={"asc_path": asc_path, "description": description})
        else:
            print(f"File not found: {asc_path}")

    print(f"Ingestion complete. Total documents: {len(db.metadata_list)}")

if __name__ == "__main__":
    ingest_examples()
