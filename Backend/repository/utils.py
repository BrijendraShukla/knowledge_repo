import os
import time
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
import fitz  # PyMuPDF
import docx
# import numpy as np
from rest_framework.pagination import PageNumberPagination
# from weaviate_service import add_document_to_weaviate, search_documents
import io
import re
from typing import List
import uuid  # private key (need to learn more about it)
import weaviate
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
from weaviate.classes.config import Configure, Property, DataType

# Set environment variables
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT")
nlp = spacy.load("en_core_web_sm")

# Initialize the AI model
llm = AzureChatOpenAI(
    # azure_deployment="RAGKR",
    # azure_deployment="RAG_KR_4o",
    # azure_deployment="RAG_KR_TextEmbedding_3_Large",
    azure_deployment="RAG_KR_4o_second",
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def process_response_content(response_content):
    """
    Extracts tags from the AI response content.
    Args:
        response_content (str): The content returned by the AI model.
    Returns:
        list: A list of extracted tags.
    """
    final_tags = re.findall(r'^\d+\.\s(.*?)$', response_content, re.M)
    return [tag.strip() for tag in final_tags]


def generate_tags_with_openai(query, unique_tags):
    """
    Generates relevant tags using the Azure OpenAI model.
    Args:
        query (str): The user's query.
        unique_tags (list): List of existing tags to match against.
    Returns:
        list: A list of matched tags from the database.
    """
    tags_str = ', '.join(unique_tags)
    
    # Use the Azure OpenAI model to generate tags based on the user's query
    # prompt = f"""
    # Based on the user query: "{query}", please select and list up to 5 most relevant tags that are directly related to the topic of the query.

    # Step 1: Determine if the query is meaningful and related to technology, programming, or professional topics.
    # - If the query is not meaningful (e.g., "more", "what is today", "have a dinner tonight") or is too vague (e.g., single words like "arc" without context), respond with:
    # "The query is not specific or relevant enough to assign meaningful tags."

    # Step 2: If the query is meaningful and relevant, select up to 5 most relevant tags that are directly related to the main topic of the query. The selected tags should be as specific and relevant as possible, even if they are not present in the provided tags list.

    # IMPORTANT GUIDELINES:
    # 1. The selected tags should be the most relevant and specific to the query, even if they are not in the provided list.
    # 2. Multi-word tags: Treat common technology terms as single tags even if they appear with spaces (e.g., "cloud computing", "artificial intelligence").
    # 3. Relevance: Select tags that are directly related to the main topic of the query.
    # 4. Specificity: Prioritize specific, topic-related tags over broad terms.
    # 5. Please try to understand spelling mistake and abbrevations a user can make in a query( like AI - artificial intelligence , Gen AI- Generative AI, etc.).
    # 6. If no tags are relevant to the query, respond with:
    # "No relevant tags found for this query."

    # Please structure your response in the following format:

    # 1. [Most Relevant Tag]
    # 2. [Second Most Relevant Tag]
    # 3. [Third Most Relevant Tag]
    # 4. [Fourth Most Relevant Tag]
    # 5. [Fifth Most Relevant Tag]

    # For non-meaningful or irrelevant queries:
    # "The query is not specific or relevant enough to assign meaningful tags."

    # For meaningful queries but no directly relevant tags:
    # "No relevant tags found for this query."
    
    # For non-meaningful or irrelevant queries:
    # "The query is not specific or relevant enough to assign meaningful tags."

    # For meaningful queries but no directly relevant tags in the list:
    # "No directly relevant tags found in the provided list for this query."
    
    # Tags List: {tags_str}.
    # """
    prompt = f"""
    Assess and tag the user query: "{query}" following these guidelines:
 
    Relevance Check:
    - Confirm if the query relates to technology, programming, or professional topics.
    - If vague or irrelevant (e.g., "more", "what is today", "arc"), respond:
      "The query lacks specificity or relevance for tagging."
 
    Tag Selection:
    - For relevant queries, identify up to 5 tags that directly pertain to the main topic.
    - Consider multi-word terms as single tags (e.g., "cloud computing").
    - Address abbreviations and common misspellings (e.g., "AI" for artificial intelligence).
 
    Selection Criteria:
    1. Choose tags that are most specific and directly relevant.
    2. If no appropriate tags are found, respond:
       "No relevant tags found for this query."
 
    Response Format:
    For valid queries:
      1. [Most Relevant Tag]
      2. [Second Most Relevant Tag]
      3. [Third Most Relevant Tag]
      4. [Fourth Most Relevant Tag]
      5. [Fifth Most Relevant Tag]
 
    For non-specific or irrelevant queries:
      "The query lacks specificity or relevance for tagging."
 
    For queries with no matching tags:
      "No relevant tags found for this query."
 
    Tags List: {tags_str}.
    """
    
    response = llm(prompt)
    # Extract the main content from the response
    response_content = response.content.strip()
    
    # Process the content to extract tags
    generated_tags = process_response_content(response_content)
    
    # Filter to ensure the returned tags actually exist in the database
    matched_tags = [tag for tag in generated_tags if tag in unique_tags]

    return matched_tags


def extract_tags_from_query(query, unique_tags):
    """
    Extracts tags from a query using the Azure OpenAI model.
    Args:
        query (str): The user's query.
        unique_tags (list): List of unique tags to match against.
    Returns:
        list: A list of matched tags.
    """
    matched_tags = generate_tags_with_openai(query,unique_tags)
    return list(matched_tags)




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
    """
    Converts PDF content to text.
    Args:
        pdf_file (file): The PDF file to convert.
    Returns:
        str: The extracted text content from the PDF.
    """
    data = pdf_file.read()
    doc = fitz.open(stream=data, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def convert_doc_to_txt(doc_file):
    """
    Converts DOC/DOCX content to text.
    Args:
        doc_file (file): The DOC/DOCX file to convert.
    Returns:
        str: The extracted text content from the DOC/DOCX file.
    """
    data = doc_file.read()
    doc = docx.Document(io.BytesIO(data))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def process_txt_file(txt_file):
    """
    Processes a TXT file.
    Args:
        txt_file (file): The TXT file to process.
    Returns:
        str: The content of the TXT file as a string.
    """
    content = txt_file.read()
    return content.decode('utf-8')

def convert_and_process_file(file):
    """
    Converts and processes a file based on its extension.
    Args:
        file (file): The file to convert and process.
    Returns:
        tuple: Extracted text, file type, and file name.
    """
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
    """
    Summarizes the document content and extracts industry type, tags, and summary.
    Args:
        text (str): The text content of the document.
    Returns:
        tuple: The identified industry type, cleaned tags, and summary.
    """
    # prompt = f"""
    # Analyze the following text and provide:

    # #Industry type:[Identify the most relevant industry from this list: {industries_list}.]
    # #Tags: Generate up to 10 highly relevant tags for this document, adhering to these strict rules:
    # 1. ONLY use words, phrases, or concepts that appear verbatim in the text or are directly implied by specific content in the text.
    # 2. Focus on key topics, themes, technologies, methodologies, frameworks, company names, product names, and technical terms found in the document.
    # 3. Prioritize specificity and relevance. Tags should be concise (1-3 words) and directly related to the document's content.
    # 4. Avoid any tags that are not explicitly supported by the text.
    # 5. If fewer than 10 relevant tags can be found in the text, only list those that are present.

    # List tags in order of relevance, separated by commas. Each tag MUST be traceable to specific content in the document.

    # #Summary: Provide a concise summary of the document's main points and purpose in exactly 300 characters, using only information present in the text.

    # Text: {text}
    # """
    
    prompt = f"""
    Analyze the following text and provide:

    #Industry type: From the list [{industries_list}], select the single most relevant industry that aligns with the core content, themes, or context of the text.
       - Ensure the selected industry accurately reflects the primary focus or domain of the text.
       
    #Tags: Generate up to 10 relevant tags based on the content of the document.
       - Only use terms explicitly mentioned or strongly implied within the text, such as:
         - Main topics
         - Technologies
         - Methodologies
         - Frameworks
         - Company or product names
         - Technical terms
       - Prioritize tags that are specific, concise (1-3 words), and directly related to the document.
       - Do not include tags unsupported by the text.
       - If fewer than 10 relevant tags exist, provide only the available ones.
       - List the tags in order of relevance, separated by commas.

    #Summary: Provide a clear, concise summary of the document's main points and purpose.
       - Use exactly 300 characters, based solely on information present in the text.

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



def chunk_text(text: str, chunk_size: int = 1000):
    """
    Splits text into smaller chunks.
    Args:
        text (str): The text to chunk.
        chunk_size (int): The size of each chunk.
    Returns:
        list: A list of text chunks.
    """
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def store_in_weaviate(document: DocumentResponse, full_text: str):
    """
    Stores a document in Weaviate.
    Args:
        document (DocumentResponse): The document metadata and content.
        full_text (str): The full text content of the document.
    """
    class_name = "Document"
    
    # Check if the class exists, if not create it
    if not client.collections.exists(class_name):
        try:
            client.collections.create(
                class_name,
                vectorizer_config=[
                    Configure.NamedVectors.text2vec_azure_openai(
                    name="title_vector",
                    source_properties=["title"],
                    base_url= "https://ragkr.openai.azure.com/",
                    resource_name="ragkr",
                    deployment_id="RAG_KR_TextEmbedding_3_Large",
                )],
                properties = [
                    Property(name="file_name", data_type=DataType.TEXT),
                    Property(name="file_type", data_type=DataType.TEXT),
                    Property(name="industry_type", data_type=DataType.TEXT_ARRAY),
                    Property(name="tags", data_type=DataType.TEXT_ARRAY),
                    Property(name="document_type", data_type=DataType.TEXT),
                    Property(name="summary", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT_ARRAY),
                    Property(name="created_at", data_type=DataType.DATE),
                    Property(name="modified_at", data_type=DataType.DATE)
                ]
            )
            # client.schema.create_class(class_obj)
        except Exception as e:
            print(f"Error creating Weaviate class: {str(e)}")
            raise

    # Extract tags from the dictionary
    cleaned_tags = [tag.strip('- ') for tag in document.get("tags", [])]

    # Chunk the full text
    text_chunks = chunk_text(full_text)
    # Prepare the data object
    current_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
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
        
        collection = client.collections.get(class_name)
        result = collection.data.insert(
            properties=data_object,
            uuid=document.get("uuid")
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
    """
    Extracts metadata and text from a PDF file.
    Args:
        file_path (str): The path to the PDF file.
    """
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
    """
    Custom pagination class for controlling page size.
    """
    page_size = 10  # Default page size
    page_size_query_param = 'page_size'  # Name of the query parameter to control page size
    max_page_size = 100  # Maximum allowed page size


def safe_remove(file_path):
    """
    Safely removes a file by retrying up to 5 times in case of PermissionError.
    Args:
        file_path (str): The path to the file to be removed.
    Returns:
        bool: True if the file was successfully removed, False otherwise.
    """
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
    """
    Fetches documents from PostgreSQL database using a list of UUIDs.
    Args:
        uuids (list): List of document UUIDs to fetch.
    Returns:
        list: A list of dictionaries containing document details.
    """
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

def extract_unique_tags_from_results(results):
    """
    Extracts a list of unique tags from a list of document results.
    Args:
        results (list): A list of document details.
    Returns:
        list: A list of unique tags.
    """
    unique_tags = set()  # Using a set to store unique tags
    for result in results:
        tags = result.get('tags', [])
        unique_tags.update(tags)  # Add tags to the set (duplicates are automatically removed)

    return list(unique_tags)  # Convert the set back to a list