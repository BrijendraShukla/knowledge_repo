import os
import zipfile
from django.http import StreamingHttpResponse, Http404, HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, generics, filters
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from mimetypes import guess_type
from pydantic import BaseModel
from typing import List
from django_filters import rest_framework as django_filters
from mimetypes import guess_type
from weaviate_service import search_documents, client,delete_document_from_weaviate,update_document_in_weaviate
from .models import FileInformation, Tags, Industry, FileType,DocumentType
from .filters import FileInformationFilter, UserFileInformationFilter
from .serializers import FileUploadSerializer, TagSerializer, IndustrySerializer, FileTypeSerializer,DocumentTypeSerializer
from .forms import MultiFileUploadForm
from .utils import convert_and_process_file, summarize_document, store_in_weaviate,CustomPagination,UploadResponse,DocumentResponse,safe_remove,fetch_from_postgresql,extract_unique_tags_from_results,extract_tags_from_query
import uuid
import json
import traceback
from django.core.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
from weaviate.classes.config import Configure, Property, DataType


class FileInformationViewSet(ModelViewSet):
    serializer_class = FileUploadSerializer
    queryset = FileInformation.objects.all()

    def create(self, request, *args, **kwargs):
        form = MultiFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            names = request.POST.getlist('name')
            summaries = request.POST.getlist('summary')
            tags_list = request.POST.getlist('tags')
            industries = request.POST.getlist('industry')
            file_type = request.POST.getlist('file_type')
            document_types = request.POST.getlist('document_type')

            if len(names) == len(summaries) == len(files) == len(file_type) == len(document_types):
                data_list = []
                for i in range(len(files)):
                    tags = tags_list[i].split(',') if i < len(tags_list) else []
                    industry = industries[i].split(',') if i < len(industries) else []
                    data_list.append({
                        'name': names[i],
                        'file': files[i],
                        'file_type': file_type[i],
                        'summary': summaries[i],
                        'tags': [tag.strip() for tag in tags],
                        'industry': [ind.strip() for ind in industry],
                        'document_type': document_types[i]
                    })

                serializer = self.get_serializer(data=data_list, many=True)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Mismatched data lengths for names, summaries, and files.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        instances = serializer.save()
        if not isinstance(instances, list):
            instances = [instances]

        response_data = []
        for instance in instances:
            text, file_type, file_name = convert_and_process_file(instance.file) 
            metadata = {
                        "name": instance.name,
                        "file_type": instance.file_type,
                        "summary": instance.summary,
                        "tags": [tag.name for tag in instance.tags.all()],
                        "industry": [industry.industry for industry in instance.industry.all()],
                        "uuid": str(instance.uuid),
                        "document_type": instance.document_type.document_type
                    }
            store_in_weaviate(metadata, text)
            response_data.append({
                'id': instance.id,
                'uuid':instance.uuid,
                'name': instance.name,
                'file': instance.file.url,
                'file_type': instance.file_type,
                'summary': instance.summary,
                'tags': [tag.name for tag in instance.tags.all()],
                'industry': [industry.industry for industry in instance.industry.all()],
                'created_at': instance.created_at,
                'modified_at': instance.modified_at,
                'document_type': instance.document_type.document_type,
            })

        return Response(response_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = get_object_or_404(FileInformation, pk=kwargs.get('pk'))
            file_path = instance.file.path

            if os.path.exists(file_path):
                if not safe_remove(file_path):
                    raise PermissionDenied("File could not be deleted due to permission issues.")

            # Ensure UUID is a string
            try:
                instance_id = str(instance.uuid)
            except ValueError:
                return Response({"error": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

            delete_document_from_weaviate(instance_id)

            instance.delete()
            return Response({"message": "Deleted Successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response({"error": "File Information does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as error:
            traceback.print_exc()
            return Response({"error": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            instance = get_object_or_404(FileInformation, pk=kwargs.get('pk'))
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            file_instance = serializer.save()

            if 'file' in request.FILES:
                old_file_path = instance.file.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                file_instance.file = request.FILES['file']
                file_instance.save()

            response_data = {
                'id': file_instance.id,
                'uuid': file_instance.uuid,
                'name': file_instance.name,
                'file': file_instance.file.url,
                'file_type': file_instance.file_type,
                'summary': file_instance.summary,
                'tags_output': [{'name': tag.name} for tag in file_instance.tags.all()],
                'industry_output': [{'industry': industry.industry} for industry in file_instance.industry.all()],
                'created_at': file_instance.created_at,
                'modified_at': file_instance.modified_at,
                'document_type': file_instance.document_type.document_type,
            }
            metadata = {
                "name": file_instance.name,
                "file_type": file_instance.file_type,
                "summary": file_instance.summary,
                "tags": [tag.name for tag in file_instance.tags.all()],
                "industry": [industry.industry for industry in file_instance.industry.all()],
                "uuid": str(file_instance.uuid),
                "document_type": file_instance.document_type.document_type,
            }
            update_document_in_weaviate(str(file_instance.uuid), metadata)
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Http404:
            return Response({"error": "FileInformation does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            traceback.print_exc()
            return Response({"error": "Something went wrong."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UserFileInformationSearchView(generics.ListAPIView):
    serializer_class = FileUploadSerializer
    filter_backends = [filters.SearchFilter, django_filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = UserFileInformationFilter
    search_fields = ['name', 'summary', 'tags__name', 'industry__industry', 'document_type__file_type']
    ordering_fields = ['created_at', 'name', 'modified_at']
    ordering = ['-modified_at']  # Order by modified_at in descending order by default
    pagination_class = CustomPagination  # Use the custom pagination class

    def get_queryset(self):
        queryset = FileInformation.objects.all().order_by('-modified_at')

        # Uncomment and modify this part once user logging is implemented
        # user = self.request.user
        # queryset = queryset.filter(created_by=user)

        return self.filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

class FileInformationSearchView(generics.ListAPIView):
    queryset = FileInformation.objects.all().order_by('created_at')
    serializer_class = FileUploadSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = FileInformationFilter
    search_fields = ['name', 'summary', 'tags__name', 'industry__industry','document_type__file_type']
    ordering_fields = ['created_at', 'name', 'modified_at']
    ordering = ['-modified_at']  # Order by modified_at in descending order by default
    pagination_class = CustomPagination  # Use the custom pagination class
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class TagViewSet(ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('name')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class IndustryViewSet(ModelViewSet):
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('industry')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class FileTypeViewSet(ModelViewSet):
    queryset = FileType.objects.all()
    serializer_class = FileTypeSerializer
    http_method_names = ['get']

class DocumentTypeViewSet(ModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('document_type')
        serializer = self.get_serializer(queryset, many=True)
        
        # Sort the list alphabetically and move "Other" to the end
        sorted_data = sorted(serializer.data, key=lambda x: x['document_type'].lower())
        other = next((item for item in sorted_data if item['document_type'].lower() == 'other'), None)
        if other:
            sorted_data.remove(other)
            sorted_data.append(other)
        
        return Response(sorted_data)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_multiple_files(request):
    try:
        files = request.FILES.getlist('files')
        results = []

        for file in files:
            # Ensure file is processed correctly and closed
            with file.open('rb') as f:
                text, file_type,file_name = convert_and_process_file(file)
                industry_type, tags, summary = summarize_document(text)
                document_type = request.data.get('document_type', '')

                doc_response = DocumentResponse(
                    id=str(uuid),  # Generate a unique id for each document
                    file_type=file_type,
                    file_name=file_name,
                    industry_type=[industry_type],
                    tags=tags,
                    summary=summary,
                    document_type=document_type
                )
                results.append(doc_response.dict())

        response = UploadResponse(documents=results)
        return JsonResponse(response.model_dump(), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    try:
        file = request.FILES['file']
        text, file_type,file_name = convert_and_process_file(file)
        industry_type, tags, summary = summarize_document(text)

        response = DocumentResponse(
            file_type=file_type,
            industry_type=industry_type,
            tags=tags,
            summary=summary
        )
        return JsonResponse(response.model_dump())
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def zip_files(file_paths):
    zip_file_path = os.path.join(settings.MEDIA_ROOT, 'documents.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for file_path in file_paths:
            zip_file.write(file_path, os.path.basename(file_path))
    return zip_file_path

class ZipFileDownloadView(APIView):
    def get(self, request):
        file_paths = request.GET.getlist('file_paths')

        if not file_paths:
            return Response({'error': 'No file paths provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            zip_file_path = zip_files(file_paths)
            response = StreamingHttpResponse(open(zip_file_path, 'rb'), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="documents.zip"'
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def serve_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            mime_type, _ = guess_type(file_path)
            response = HttpResponse(file, content_type=mime_type)
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    except FileNotFoundError:
        raise Http404("File does not exist")

class FileDownloadView(APIView):
    def post(self, request, *args, **kwargs):
        file_ids = request.data.get('file_ids', [])
        if not file_ids:
            return Response({"error": "No file ids provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        files = FileInformation.objects.filter(id__in=file_ids)
        
        if not files.exists():
            return Response({"error": "No files found for the given ids."}, status=status.HTTP_404_NOT_FOUND)

        if len(files) == 1:
            file_info = files.first()
            file_path = os.path.join(settings.MEDIA_ROOT, file_info.file.name)
            if not os.path.exists(file_path):
                raise Http404("File not found.")
            # Determine the file extension from the file name
            file_name = file_info.name
            file_extension = os.path.splitext(file_info.file.name)[1]  # Get file extension
            # Ensure the file name includes the extension
            full_file_name = f"{file_name}{file_extension}"
            # Create a streaming response with the file
            response = StreamingHttpResponse(open(file_path, 'rb'))
            # Set content disposition to attach file with original name and extension
            response['Content-Disposition'] = f'attachment; filename="{full_file_name}"'
            response['Content-Type'] = 'application/octet-stream'
            return response
        
        zip_file_path = os.path.join(settings.MEDIA_ROOT, 'temp.zip')
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for file_info in files:
                file_path = os.path.join(settings.MEDIA_ROOT, file_info.file.name)
                if os.path.exists(file_path):
                    zip_file.write(file_path, arcname=os.path.basename(file_path))

        def stream_file(path):
            with open(path, 'rb') as file:
                while chunk := file.read(8192):
                    yield chunk

        response = StreamingHttpResponse(stream_file(zip_file_path))
        response['Content-Type'] = 'application/zip'
        response['Content-Disposition'] = 'attachment; filename="KR_files.zip"'

        # Schedule file cleanup
        def cleanup_file(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")

        # Override close method to include cleanup
        original_close = response.close
        def close_response():
            original_close()
            cleanup_file(zip_file_path)
        response.close = close_response

        return response
    

def view_file_content(request, file_id):
    file_info = FileInformation.objects.filter(id=file_id).first()
    if not file_info:
        raise Http404("File not found.")
    
    # Get the full path to the file
    file_path = os.path.join(settings.MEDIA_ROOT, file_info.file.name)
    
    if not os.path.exists(file_path):
        raise Http404("File not found.")
    
    # Guess the content type of the file
    content_type, _ = guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Open the file and return its content
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{file_info.file.name}"'
        return response
    



@api_view(['GET'])
def QAview(request):
    query = request.query_params.get('query', '')
    if not query:
        return JsonResponse({'error': 'Query parameter is required'}, status=400)
    
    generate_tags = request.query_params.get('generate_tag', '').lower() == 'true'

    # Search in Weaviate
    search_results = search_documents(query)
    if not search_results:
        return JsonResponse({'error': 'No matching documents found'}, status=404)

    # Extract UUIDs from Weaviate search results
    uuids = [result['uuid'] for result in search_results]

    # Fetch records from PostgreSQL
    results = fetch_from_postgresql(uuids)
    # Extract unique tags from the results
    unique_tags = extract_unique_tags_from_results(results)
    nlp_tags = []
    if generate_tags:
        nlp_tags = extract_tags_from_query(query, unique_tags)
        
        # New condition: If no tags are generated, return an empty response
        if not nlp_tags:
            return JsonResponse({
                'count': 0,
                'total_pages': 0,
                'current_page': 1,
                'page_size': int(request.query_params.get('pageSize', 10)),
                'results': [],
                'tags': [],
            })

    # Get user-provided tags
    user_tags = request.query_params.getlist('tags', [])
    # Determine which tags to use for filtering
    tags_to_use = user_tags if user_tags else nlp_tags
    # Apply filters manually
    def filter_records(records, params, tags):
        filtered = records

        date_range_after = params.get('date_range_after', None)
        if date_range_after:
            date_range_after = datetime.strptime(date_range_after, '%Y-%m-%d').date()
            filtered = [record for record in filtered if record['created_at'].date() >= date_range_after]

        date_range_before = params.get('date_range_before', None)
        if date_range_before:
            date_range_before = datetime.strptime(date_range_before, '%Y-%m-%d').date()
            filtered = [record for record in filtered if record['created_at'].date() <= date_range_before]

        file_type = params.get('file_type', None)
        if file_type:
            filtered = [record for record in filtered if record['file_type'] == file_type]

        # Document type filter
        document_type = params.get('document_type', None)
        if document_type:
            filtered = [record for record in filtered if record['document_type'] == document_type]

        if tags:
            filtered = [
                record for record in filtered if any(
                    all(
                        keyword.lower() in ' '.join([record['name'], record['summary'], ','.join(record['tags']), ','.join(record['industry'])]).lower()
                        for keyword in tag.split()
                    )
                    for tag in tags
                )
            ]

        industry = params.getlist('industry', None)
        if industry:
            filtered = [
                record for record in filtered if any(
                    ind.lower() in [i.lower() for i in record['industry']] for ind in industry
                )
            ]

        return filtered

    filtered_records = filter_records(results, request.query_params, tags_to_use)

    # If no filtered records and GenerateTags is true, show all initial records
    # if not filtered_records and generate_tags:
    #     filtered_records = results

    # Apply pagination manually
    page_size = int(request.query_params.get('pageSize', 10))
    page_number = int(request.query_params.get('pageNumber', 1))
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    paginated_records = filtered_records[start_index:end_index]

    # Create pagination response
    response_data = {
        'count': len(filtered_records),
        'total_pages': (len(filtered_records) + page_size - 1) // page_size,
        'current_page': page_number,
        'page_size': page_size,
        'results': paginated_records,
        'tags': tags_to_use,  # Include the tags used for filtering in the response
    }

    return JsonResponse(response_data)

    # return JsonResponse(results, safe=False)

@api_view(['GET'])
def fetch_all_records(request):
    class_name = "Document"
    try:
        collection = client.collections.get(class_name)
        result = []
        for item in collection.iterator():
            result.append(item.uuid)
            
        return JsonResponse(result, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@api_view(['DELETE'])
def delete_all_records(request):
    class_name = "Document"
    try:
        collection = client.collections.get(class_name)
        for item in collection.iterator():
            collection.data.delete_by_id(item.uuid)
        
        
        return JsonResponse({'status': 'All records deleted'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    


@api_view(['DELETE'])
def delete_class(request, class_name):
    try:
        client.collections.delete(class_name)
        return Response({"message": f"Class '{class_name}' deleted successfully."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def create_weaviate_schema(request):
    class_name = "Document"
    
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
        
        return Response({"message": f"Class '{class_name}' created successfully."}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


