from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import FileInformationViewSet,FileInformationSearchView,TagViewSet, IndustryViewSet, FileTypeViewSet,upload_file, upload_multiple_files,FileDownloadView,view_file_content,UserFileInformationSearchView,QAview,fetch_all_records, delete_all_records,DocumentTypeViewSet,delete_class,create_weaviate_schema


router = DefaultRouter()
router.register("upload", FileInformationViewSet, basename="file_upload")
router.register('tags', TagViewSet, basename='tags')
router.register('industry', IndustryViewSet, basename='industry')
router.register('filetypes', FileTypeViewSet, basename='filetypes')
router.register('document_type', DocumentTypeViewSet, basename='document_type')
urlpatterns = [
    path("", include(router.urls)),
    path('search/', FileInformationSearchView.as_view(), name='document-search'),
    path('upload-file/', upload_file, name='upload_file'),
    path('upload-multiple-files/', upload_multiple_files, name='upload_multiple_files'),
    path('download/', FileDownloadView.as_view(), name='file-download'),
    path('view-file/<int:file_id>/', view_file_content, name='view_file_content'),
    path('get-user-files/', UserFileInformationSearchView.as_view(), name='user-file-information-search'),
    path('Q&A-search/', QAview, name='search-api'),
    path('fetch-all-records/', fetch_all_records, name='fetch_all_records'),
    path('delete-all-records/', delete_all_records, name='delete_all_records'),
    path('delete-class/<str:class_name>/', delete_class, name='delete_class-weaviate_schema'),
    path('create-weaviate-schema/', create_weaviate_schema, name='create_weaviate_schema'),
]
