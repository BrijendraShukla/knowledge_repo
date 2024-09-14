import json
import weaviate
import os
from typing import Dict, Any, List
from weaviate.gql.get import HybridFusion
from openai import AzureOpenAI

# Define the local and remote URLs
LOCAL_URL = "http://127.0.0.1:8080"
REMOTE_URL = "http://172.19.62.144:8080"

# Function to check if the app is running in a local environment
def is_local_environment():
    # You can define a custom logic to check if you're in a local environment.
    # For example, checking an environment variable like "ENV" or "LOCAL".
    return os.getenv("ENV") == "local"

# Set the appropriate URL based on the environment
client_url = LOCAL_URL if is_local_environment() else REMOTE_URL

client = weaviate.Client(
    url=client_url,
    additional_headers={
        "X-Azure-Api-Key": os.getenv("AZURE_OPENAI_API_KEY"),
        "X-Azure-Resource-Name": os.getenv("AZURE_OPENAI_ENDPOINT").split('.')[0]  # Extract resource name from endpoint
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
            "vectorizer": "text2vec-azure-openai",
            "moduleConfig": {
                "text2vec-azure-openai": {
                    "resourceName": os.getenv("AZURE_OPENAI_ENDPOINT").split('.')[0],
                    "deploymentId": "text-embedding-ada-002",  # Use your actual deployment ID for embeddings
                    "modelVersion": "2",  # Use "2" for text-embedding-ada-002
                }
            },
            "properties": [
                {"name": "document", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["object"]}
            ]
        }
        client.schema.create_class(class_obj)

# def ensure_schema_exists():
#     class_name = "Document"
#     if not client.schema.exists(class_name):
#         class_obj = {
#             "class": class_name,
#             "vectorizer": "text2vec-openai",  # Assuming you're using OpenAI for vectorization
#             "properties": [
#                 {"name": "document", "dataType": ["text"]},
#                 {"name": "metadata", "dataType": ["object"]}
#             ]
#             # "modelVersion": "3",
#         }
#         client.schema.create_class(class_obj)

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

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def generate_vector_from_query(text):
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
            # model = "text-embedding-3-large"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

def search_documents(query: str, top_k: int = 20, certainty: float = 0.7) -> List[Dict[str, Any]]:
    try:
        # Generate the vector for the query
        vector = generate_vector_from_query(query)
        result = (
            client.query
            .get("Document")
            .with_additional(["id"])
            .with_hybrid(
                query=query,
                vector=vector,
                properties=["summary", "content", "file_name", "industry_type", "tags"],
                alpha=0.35,  # Balance between BM25 and vector search
                fusion_type=HybridFusion.RELATIVE_SCORE
            )
            # .with_near_vector({
            #     "vector": vector
            # })
            # .with_additional(["distance"])
            .with_additional(["score", "explainScore"])
            .with_limit(top_k)
            .do()
        )
        # Check if the expected keys exist in the response
        if "data" in result and "Get" in result["data"] and "Document" in result["data"]["Get"]:
            documents = result["data"]["Get"]["Document"]
            filtered_documents = [
                doc for doc in documents if float(doc["_additional"]["score"]) >= 0.5
            ]
            
            # Print the filtered results
            print(json.dumps(filtered_documents, indent=2))
            return filtered_documents
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
