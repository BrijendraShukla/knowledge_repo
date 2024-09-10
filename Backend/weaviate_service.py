import json
import weaviate
import os
from typing import Dict, Any, List
from weaviate.gql.get import HybridFusion

# Weaviate client setup
client = weaviate.Client(
    url="http://127.0.0.1:8080",  # Replace with your Weaviate instance URL
    additional_headers={
        "X-OpenAI-Api-Key": os.getenv("AZURE_OPENAI_API_KEY")
    }
)
# Optional: Check the connection
if client.is_ready():
    print("Weaviate is ready!")
else:
    print("Weaviate is not ready.")

def ensure_schema_exists():
    class_name = "Document"
    if not client.schema.exists(class_name):
        class_obj = {
            "class": class_name,
            "vectorizer": "text2vec-openai",  # Assuming you're using OpenAI for vectorization
            "properties": [
                {"name": "document", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["object"]}
            ]
        }
        client.schema.create_class(class_obj)

def add_document_to_weaviate(document: str, metadata: Dict[str, Any]) -> bool:
    try:
        ensure_schema_exists()
        data_object = {
            "document": document,
            "metadata": metadata,
        }
        result = client.data_object.create(data_object, "Document")
        return True
    except Exception as e:
        print(f"Error adding document to Weaviate: {str(e)}")
        return False

def search_documents(query,top_k: int = 20, certainty: float = 0.7) -> List[Dict[str, Any]]:
    try:
        result = (
            client.query
            .get("Document")
            .with_additional(["id"])
            .with_bm25(
                query=query,
                properties=["summary","content","file_name","industry_type","tags"],
                # alpha=0.25,
                # fusion_type=HybridFusion.RELATIVE_SCORE,
            )
            .with_additional(["score", "explainScore"])
            .with_limit(top_k)
            .do()
        )
        # Check if the expected keys exist in the response
        if "data" in result and "Get" in result["data"] and "Document" in result["data"]["Get"]:
            print(json.dumps(result, indent=2))
            return result["data"]["Get"]["Document"]
        else:
            print("Unexpected response structure:", result)
            return []
    except Exception as e:
        print(f"Error searching documents in Weaviate: {str(e)}")
        return []


def update_document_in_weaviate(document_id: str, metadata: Dict[str, Any]) -> bool:
    class_name = "Document"
    try:
        client.data_object.update(
            class_name=class_name,
            uuid=document_id,
            data_object=metadata
        )
        return True
    except Exception as e:
        print(f"Error updating document in Weaviate: {str(e)}")
        return False


def delete_document_from_weaviate(document_id: str) -> bool:
    class_name = "Document"
    try:
        client.data_object.delete(
            class_name=class_name,
            uuid=document_id
        )
        return True
    except Exception as e:
        print(f"Error deleting document from Weaviate: {str(e)}")
        return False
