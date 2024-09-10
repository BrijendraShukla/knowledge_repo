# from django_filters import rest_framework as filters
from .models import FileInformation, Tags, Industry,DocumentType
from django_filters import rest_framework as django_filters

class FileInformationFilter(django_filters.FilterSet):
    date_range = django_filters.DateFromToRangeFilter(field_name='created_at',required=False)
    file_type = django_filters.CharFilter(field_name='file_type',required=False)
    tags = django_filters.CharFilter(method='filter_by_tags',required=False)
    industry = django_filters.CharFilter(method='filter_by_industry',required=False)
    document_type = django_filters.ModelChoiceFilter(
        field_name='document_type',  # Corrected field name
        queryset=DocumentType.objects.all(),
        to_field_name='document_type',
        required=False
    )

    class Meta:
        model = FileInformation
        fields = ['date_range', 'file_type', 'tags', 'industry','document_type']

    def filter_by_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__name__in=tags).distinct()
        return queryset

    def filter_by_industry(self, queryset, name, value):
        industries = self.request.query_params.getlist('industry')
        if industries:
            return queryset.filter(industry__industry__in=industries).distinct()
        return queryset
    
class UserFileInformationFilter(django_filters.FilterSet):
    date_range = django_filters.DateFromToRangeFilter(field_name='created_at', required=False)
    file_type = django_filters.CharFilter(field_name='file_type', required=False)
    industry = django_filters.ModelMultipleChoiceFilter(
        field_name='industry__industry', 
        queryset=Industry.objects.all(),
        to_field_name='industry',
        required=False
    )
    document_type = django_filters.ModelChoiceFilter(
        field_name='document_type',  # Corrected field name
        queryset=DocumentType.objects.all(),
        to_field_name='document_type',
        required=False
    )

    class Meta:
        model = FileInformation
        fields = ['date_range', 'file_type', 'industry','document_type']
