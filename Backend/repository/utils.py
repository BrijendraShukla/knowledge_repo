import os
import time
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
import fitz  # PyMuPDF
import docx
# import numpy as np
from langchain_openai import AzureChatOpenAI
from rest_framework.pagination import PageNumberPagination
# from weaviate_service import add_document_to_weaviate, search_documents
import io
import re
from typing import List
import uuid  # private key (need to learn more about it)
import weaviate
from openai import AzureOpenAI
import os
from weaviate_service import client
import time
import psutil
from datetime import datetime, timezone
from django.shortcuts import get_object_or_404
from .models import FileInformation, Tags
import spacy
from collections import Counter
from string import punctuation

# Set environment variables
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT")
nlp = spacy.load("en_core_web_sm")

# Initialize the AI model
llm = AzureChatOpenAI(
    # azure_deployment="RAGKR",
    azure_deployment="RAG_KR_4o",
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def process_response_content(response_content):
    # Extract all tags under "Final Selected Tags"
    final_tags_section = re.search(r'### Final Selected Tags:(.*?)$', response_content, re.S)
    
    if final_tags_section:
        # Find tags within this section
        final_tags = re.findall(r'\*\*(.*?)\*\*', final_tags_section.group(1))
        return final_tags
    else:
        return []
def generate_tags_with_openai(query):
    # Fetch all tags from the database
    all_tags = list(Tags.objects.values_list('name', flat=True))
    
    # Create a comma-separated string of all tags
    tags_str = ', '.join(all_tags)
    
    # Use the Azure OpenAI model to generate tags based on the user's query
    prompt = (
        f"Given the following tags from the database: {tags_str}. "
        f"First go with each and every tags within the list then select most accuract and justified tags which will define based on the user's query: '{query}', and then finally select only 5 tags from the selected list of most accuract tags."
        "If none of the tags are relevant, return 'No matching tags'."
    )
    response = llm(prompt)

    # Extract the main content from the response
    response_content = response.content.strip()
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",response_content)
    
    # Process the content to extract tags
    generated_tags = process_response_content(response_content)
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",generated_tags)
    
    # Filter to ensure the returned tags actually exist in the database
    matched_tags = [tag for tag in generated_tags if tag in all_tags]
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!111",matched_tags)

    return matched_tags


def get_hotwords(text):
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN'] 
    doc = nlp(text.lower()) 
    for token in doc:
        if(token.text in nlp.Defaults.stop_words or token.text in punctuation):
            continue
        if(token.pos_ in pos_tag):
            result.append(token.text)
    return result

def extract_tags_from_query(query):
    # Generate tags using Azure OpenAI, ensuring they match the database tags
    matched_tags = generate_tags_with_openai(query)
    return list(matched_tags)

openai_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-05-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_type: str
    industry_type: List[str]
    tags: List[str]
    summary: str
    document_type: str = "" 

class UploadResponse(BaseModel):
    documents: List[DocumentResponse]

def convert_pdf_to_txt(pdf_file):
    data = pdf_file.read()
    doc = fitz.open(stream=data, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def convert_doc_to_txt(doc_file):
    data = doc_file.read()
    doc = docx.Document(io.BytesIO(data))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def process_txt_file(txt_file):
    content = txt_file.read()
    return content.decode('utf-8')

def convert_and_process_file(file):
    file_extension = os.path.splitext(file.name)[1].lower()
    text = ""
    
    if file_extension == '.pdf':
        text = convert_pdf_to_txt(file)
        file_type = 'pdf'
    elif file_extension in ['.doc', '.docx']:
        text = convert_doc_to_txt(file)
        file_type = 'doc'
    elif file_extension == '.txt':
        text = process_txt_file(file)
        file_type = 'txt'
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return text, file_type, file.name

industries_list = [
    "Agriculture and Allied Industries", "Auto Components", "Automobiles", "Aviation", 
    "Ayush", "Banking", "Biotechnology", "Cement", "Chemicals", "Consumer Durables", 
    "Defence Manufacturing", "E-Commerce", "Education and Training", "Electric Vehicle", 
    "Electronics System Design & Manufacturing", "Engineering and Capital Goods", 
    "Financial Services", "FMCG", "Food Processing", "Gems and Jewellery", "Healthcare", 
    "Infrastructure", "Insurance", "IT & BPM", "Manufacturing", "Media and Entertainment", 
    "Medical Devices", "Metals and Mining", "MSME", "Oil and Gas", "Paper & Packaging", 
    "Pharmaceuticals", "Ports", "Power", "Railways", "Real Estate", "Renewable Energy", 
    "Retail", "Roads", "Science and Technology", "Services", "Steel", 
    "Telecommunications", "Textiles", "Tourism and Hospitality"
]

def summarize_document(text):
    prompt = f"""
    You are a helpful assistant who performs certain tasks on a document.
    Please analyze the following text and provide:
    #Industry type: [Find the most suitable industry type from the Text based on this list {industries_list}]
    #Tags: [Find the most relevant 10 metatags from the given Text separated by comma. Metatags are those keywords that will be used to help the user to find the relevant document based on these tags. Sequence the tags in order of their relevance.]
    #Summary: [Summary of the document content in 300 characters only and it should never exceed the character limit]

    Text: {text}
    """
    # Send the prompt to the AI model for summarization
    ai_msg = llm.invoke(prompt)
    
    response_text = ai_msg.content
    print("AI response:", response_text)  # Debug print
    
    # Use regex to extract industry type
    industry_type_match = re.search(r'#\s*Industry type:\s*(.*?)(?=\n#|\Z)', response_text, re.DOTALL)
    industry_type = industry_type_match.group(1).strip() if industry_type_match else ""

    # Use regex to extract tags
    tags_match = re.search(r'#\s*Tags:(.*?)(?=\n#|\Z)', response_text, re.DOTALL)
    if tags_match:
        # Split tags by commas or newlines, then strip and filter out empty tags
        tags = [tag.strip() for tag in re.split(r'[,\n]', tags_match.group(1)) if tag.strip()]
    else:
        tags = []

    # Use regex to extract summary
    summary_match = re.search(r'#\s*Summary:(.*?)(?=\Z)', response_text, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    print(f"Parsed values: industry_type={industry_type}, tags={tags}, summary={summary[:50]}...")
    cleaned_tags = [tag.strip('- ') for tag in tags]
    return industry_type, cleaned_tags, summary

def generate_embedding(text):
    try:
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

def chunk_text(text: str, chunk_size: int = 1000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def store_in_weaviate(document: DocumentResponse, full_text: str):
    class_name = "Document"
    
    # Check if the class exists, if not create it
    if not client.schema.exists(class_name):
        class_obj = {
            "class": class_name,
            "vectorizer": "text2vec-transformers",
            "properties": [
                {"name": "file_name", "dataType": ["string"]},
                {"name": "file_type", "dataType": ["string"]},
                {"name": "industry_type", "dataType": ["string[]"]},
                {"name": "tags", "dataType": ["string[]"]},
                {"name": "document_type", "dataType": ["string"]},
                {"name": "summary", "dataType": ["text"]},
                {"name": "content", "dataType": ["text[]"]},
                {"name": "created_at", "dataType": ["date"]},  
                {"name": "modified_at", "dataType": ["date"]},  
            ]
        }
        try:
            client.schema.create_class(class_obj)
        except Exception as e:
            print(f"Error creating Weaviate class: {str(e)}")
            raise

    # Extract tags from the dictionary
    cleaned_tags = [tag.strip('- ') for tag in document.get("tags", [])]

    # Chunk the full text
    text_chunks = chunk_text(full_text)
    # Prepare the data object
    current_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
    # data_object = {
    #     "file_name": document.get("name", ""),  # Use dictionary keys
    #     "file_type": document.get("file_type", ""),
    #     "industry_type": "".join(document.get("industry", [])),  # Convert list to string
    #     "tags": cleaned_tags,  # Use the cleaned tags
    #     "summary": document.get("summary", ""),
    #     "content": text_chunks,
    #     "created_at": datetime.now().isoformat(),  # Set created_at
    #     "modified_at": datetime.now().isoformat(),  # Set modified_at
    # }
    data_object = {
        "file_name": document.get("name", ""),
        "file_type": document.get("file_type", ""),
        "industry_type": document.get("industry", []), 
        "tags": cleaned_tags,
        "document_type": document.get("document_type", ""),
        "summary": document.get("summary", ""),
        "content": text_chunks,
        "created_at": current_time,
        "modified_at": current_time,
    }

    # Store the document in Weaviate
    try:
        result = client.data_object.create(
            class_name=class_name,  # Explicitly use class_name as a keyword argument
            data_object=data_object,
            uuid=document.get("uuid")  # Use .get() to avoid KeyError
        )
        print(f"Document '{document.get('name')}' (ID: {document.get('uuid')}) successfully stored in Weaviate.")
        print(f"Weaviate response: {result}")
    except Exception as e:
        print(f"Error storing document '{document.get('name')}' in Weaviate:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Data object: {data_object}")
        raise

def extract_data_from_pdf(file_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    meta = reader.metadata
    print("Total Pages: ", len(reader.pages))
    # All of the following could be None!
    print("Author: ", meta.author)
    print("Creator: ", meta.creator)
    print("Producer: ", meta.producer)
    print("Subject: ", meta.subject)
    print("Title: ", meta.title)
    for i in range(0, len(reader.pages)):
        print(i)
        page = reader.pages[i]
        print(page.extract_text())

class CustomPagination(PageNumberPagination):
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Name of the query parameter to control page size
    max_page_size = 100  # Maximum allowed page size


def safe_remove(file_path):
    for attempt in range(5):  # Retry up to 5 times
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except PermissionError:
            print(f"PermissionError: Retrying to delete {file_path} (attempt {attempt + 1})")
            time.sleep(1)  # Wait for 1 second before retrying
            
            # Try to close any open handles to the file
            for proc in psutil.process_iter(['pid', 'open_files']):
                try:
                    for file in proc.open_files():
                        if file.path == file_path:
                            proc.terminate()
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    
    print(f"Failed to delete {file_path} after 5 attempts")
    return False

def fetch_from_postgresql(uuids):
    results = []
    for uuid in uuids:
        document = get_object_or_404(FileInformation, uuid=uuid)
        results.append({
            'id': document.id,
            'uuid': document.uuid,
            'name': document.name,
            'file_type': document.file_type,
            'summary': document.summary,
            'document_type': document.document_type.document_type if document.document_type else None,  # Convert DocumentType to a string
            'tags': [tag.name for tag in document.tags.all()],
            'industry': [industry.industry for industry in document.industry.all()],
            'created_at': document.created_at,
            'modified_at': document.modified_at,
        })
    return results