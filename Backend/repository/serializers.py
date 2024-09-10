# serializers.py
from rest_framework import serializers
from .models import FileInformation, Tags, Industry, FileType,DocumentType

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ['name']

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['industry']

class FileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileType
        fields = ['file_type']

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ['document_type']

class FileUploadSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), write_only=True)
    industry = serializers.ListField(child=serializers.CharField(), write_only=True)
    document_type = serializers.CharField(write_only=True)
    tags_output = TagSerializer(many=True, read_only=True, source='tags')
    industry_output = IndustrySerializer(many=True, read_only=True, source='industry')
    document_type_output = DocumentTypeSerializer(read_only=True, source='document_type')
    file_type = serializers.CharField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = FileInformation
        fields = ['id','uuid', 'name', 'file', 'file_type', 'summary', 'tags', 'tags_output', 'created_at', 'modified_at', 'industry', 'industry_output','document_type','document_type_output']

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        industry_data = validated_data.pop('industry', [])
        document_type_data = validated_data.pop('document_type', None)

        if document_type_data:
            document_type, created = DocumentType.objects.get_or_create(document_type=document_type_data)
            validated_data['document_type'] = document_type

        file_info = FileInformation.objects.create(**validated_data)

        for tag in tags_data:
            tag_obj, created = Tags.objects.get_or_create(name=tag)
            file_info.tags.add(tag_obj)

        for industry in industry_data:
            industry_obj, created = Industry.objects.get_or_create(industry=industry)
            file_info.industry.add(industry_obj)

        return file_info

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        industry_data = validated_data.pop('industry', [])
        document_type_data = validated_data.pop('document_type', None)

        instance = super().update(instance, validated_data)
        
        if tags_data:
            old_tags = set(instance.tags.all())
            new_tags = set(Tags.objects.get_or_create(name=tag)[0] for tag in tags_data)
            instance.tags.set(new_tags)
            
            # Delete old tags that are not associated with any other records
            for tag in old_tags - new_tags:
                if not tag.fileinformation_set.exists():
                    print(f"Deleting tag: {tag.name}")  # Debugging statement
                    tag.delete()

        if industry_data:
            instance.industry.clear()
            for industry in industry_data:
                industry_list = industry.split(',')
                for single_industry in industry_list:
                    industry_obj, created = Industry.objects.get_or_create(industry=single_industry.strip())
                    instance.industry.add(industry_obj)

        if document_type_data:
            document_type, created = DocumentType.objects.get_or_create(document_type=document_type_data)
            instance.document_type = document_type
            instance.save()
                
        return instance
