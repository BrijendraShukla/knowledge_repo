import json
import weaviate
import os
from typing import Dict, Any, List
from weaviate.classes.query import HybridFusion
from openai import AzureOpenAI
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from weaviate.classes.query import MetadataQuery

# Define the local and remote URLs
LOCAL_URL = "127.0.0.1"
REMOTE_URL = "172.31.75.108"

# Function to check if the app is running in a local environment
def is_local_environment():
    # You can define a custom logic to check if you're in a local environment.
    # For example, checking an environment variable like "ENV" or "LOCAL".
    return os.getenv("ENV") == "local"

# Set the appropriate URL based on the environment
client_url = LOCAL_URL if is_local_environment() else REMOTE_URL

try:
    # Initialize the Weaviate client with connection parameters and configuration settings
    client = weaviate.WeaviateClient(
        connection_params=ConnectionParams.from_params(
            # http_host="localhost",
            http_host=client_url,
            # http_host="172.18.82.230",#RDP
            http_port="8080",
            http_secure=False,
            # grpc_host="localhost",
            grpc_host=client_url,
            # grpc_host="172.18.82.230",#RDP
            grpc_port="50051",
            grpc_secure=False,
        ),
        additional_headers={
            "X-Azure-Api-Key": os.getenv("AZURE_OPENAI_API_KEY"),
        },
        additional_config=AdditionalConfig(
            timeout=Timeout(
                init=9999,  # Initialization timeout in seconds
                query=9999,  # Query timeout in seconds
                insert=9999  # Insert timeout in seconds
            )
        ),
        skip_init_checks=True
    )

    client.connect()

    # Check if the client is ready
    if client.is_ready():
        print("Weaviate is ready!")
    else:
        print("Weaviate is not ready.")

finally:
    print("Happy Coding")

def ensure_schema_exists():
    """
    Ensures that the schema for the 'Document' class exists in Weaviate.
    If it does not exist, creates a new schema with the required vectorizer and properties.
    """
    class_name = "Document"
    if not client.schema.exists(class_name):
        class_obj = {
            "class": class_name,
            "vectorizer": "text2vec-azure-openai",
            "moduleConfig": {
                "text2vec-azure-openai": {
                    "resourceName": os.getenv("AZURE_OPENAI_ENDPOINT").split('.')[0],
                    "deploymentId": "text-embedding-ada-002",
                    "modelVersion": "2",
                }
            },
            "properties": [
                {"name": "document", "dataType": ["text"]},
                {"name": "metadata", "dataType": ["object"]}
            ]
        }
        client.schema.create_class(class_obj)

def add_document_to_weaviate(document: str, metadata: Dict[str, Any]) -> bool:
    """
    Adds a document to Weaviate along with its metadata.

    Args:
        document (str): The text content of the document.
        metadata (Dict[str, Any]): Additional metadata related to the document.

    Returns:
        bool: True if the document was added successfully, False otherwise.
    """
    try:
        ensure_schema_exists()
        data_object = {
            "document": document,
            "metadata": metadata,
        }
        client.data_object.create(data_object, "Document")
        return True
    except Exception as e:
        print(f"Error adding document to Weaviate: {str(e)}")
        return False

# Initialize OpenAI client
openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def generate_vector_from_query(text: str) -> List[float]:
    """
    Generates an embedding vector from the provided text using Azure OpenAI.

    Args:
        text (str): The input text to generate the embedding from.

    Returns:
        List[float]: The generated embedding vector or an empty list on failure.
    """
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

def search_documents(query: str) -> List[Dict[str, Any]]:
    """
    Searches for documents in Weaviate that match the given query.

    Args:
        query (str): The search query to match documents against.

    Returns:
        List[Dict[str, Any]]: A list of documents that match the query with relevant metadata.
    """
    try:
        class_name = 'Document'
        collection = client.collections.get(class_name)

        # Perform the hybrid query without limiting the number of results
        response = collection.query.hybrid(
            query=query,
            limit=None,
            alpha=0.25,
            fusion_type=HybridFusion.RELATIVE_SCORE,
            return_metadata=MetadataQuery(score=True, explain_score=True),
            query_properties=["file_name", "industry_type", "tags", "document_type", "file_type", "content"],
        )

        results = []
        for obj in response.objects:
            if obj.metadata.score is not None and obj.metadata.score > 0.5:
                result = {
                    "score": obj.metadata.score,
                    "uuid": str(obj.uuid),
                    "file_name": obj.properties.get("file_name"),
                }
                results.append(result)
                print(f"Extracted Result: {result}")

        return results

    except Exception as e:
        print(f"Error searching documents in Weaviate: {str(e)}")
        return []

def update_document_in_weaviate(document_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Updates an existing document in Weaviate with new metadata.

    Args:
        document_id (str): The UUID of the document to update.
        metadata (Dict[str, Any]): The new metadata to associate with the document.

    Returns:
        bool: True if the document was updated successfully, False otherwise.
    """
    try:
        class_name = 'Document'
        collection = client.collections.get(class_name)
        collection.data.update(
            uuid=document_id,
            properties=metadata
        )
        return True
    except Exception as e:
        print(f"Error updating document in Weaviate: {str(e)}")
        return False

def delete_document_from_weaviate(document_id: str) -> bool:
    """
    Deletes a document from Weaviate using its UUID.

    Args:
        document_id (str): The UUID of the document to delete.

    Returns:
        bool: True if the document was deleted successfully, False otherwise.
    """
    try:
        class_name = 'Document'
        collection = client.collections.get(class_name)
        collection.data.delete_by_id(document_id)
        return True
    except Exception as e:
        print(f"Error deleting document from Weaviate: {str(e)}")
        return False
