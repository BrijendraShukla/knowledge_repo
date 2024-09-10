from django.http import HttpResponseRedirect, Http404
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from django.contrib import admin
from django import forms
from django.conf import settings
from .models import Tags, Industry, FileType, FileInformation
import os

class FileInformationAdminForm(forms.ModelForm):
    class Meta:
        model = FileInformation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tags.objects.all()
        self.fields['tags'].help_text = None
        self.fields['industry'].queryset = Industry.objects.all()
        self.fields['industry'].help_text = None

@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('id', 'industry')
    search_fields = ('industry',)

@admin.register(FileType)
class FileTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_type')
    search_fields = ('file_type',)

@admin.register(FileInformation)
class FileInformationAdmin(admin.ModelAdmin):
    form = FileInformationAdminForm
    list_display = ('id', 'name', 'file_type', 'created_at', 'modified_at', 'display_tags', 'display_industry', 'summary', 'download_file_link', 'view_file_link')
    search_fields = ('name', 'file_type')
    list_filter = ('created_at', 'modified_at', 'tags', 'industry')
    actions = ['download_file_action', 'view_file_action']

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])

    def display_industry(self, obj):
        return ", ".join([industry.industry for industry in obj.industry.all()])

    display_tags.short_description = 'Tags'
    display_industry.short_description = 'Industry'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["queryset"] = Tags.objects.all()
        if db_field.name == "industry":
            kwargs["queryset"] = Industry.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def download_file_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one file to download.")
            return
        file_info = queryset.first()
        return HttpResponseRedirect(f"/repository/download/{file_info.id}/")

    download_file_action.short_description = "Download selected file"

    def view_file_action(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one file to view.")
            return
        file_info = queryset.first()
        return HttpResponseRedirect(f"/repository/view-file/{file_info.id}/")

    view_file_action.short_description = "View selected file"

    def download_file_link(self, obj):
        return format_html(f'<a href="/repository/download/{obj.id}/" target="_blank">Download</a>')

    def view_file_link(self, obj):
        return format_html(f'<a href="/repository/view-file/{obj.id}/" target="_blank">View</a>')

    download_file_link.short_description = 'Download File'
    view_file_link.short_description = 'View File'
