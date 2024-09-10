from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

# Create your models here.

class Tags(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class Industry(models.Model):
    industry = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.industry

class FileType(models.Model):
    file_type = models.CharField(max_length=50)

    def __str__(self):
        return self.file_type

class DocumentType(models.Model):
    document_type = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.document_type

class FileInformation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(_("Name of File"), max_length=255)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=20, blank=True)
    summary = models.TextField()
    tags = models.ManyToManyField(Tags)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    industry = models.ManyToManyField(Industry)
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='file_informations')

    def save(self, *args, **kwargs):
        if not self.file_type:
            self.file_type = self.file.name.split('.')[-1].lower() if self.file.name else ''
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        tags = list(self.tags.all())  # Convert to list to avoid querying after deletion
        super().delete(*args, **kwargs)
        for tag in tags:
            if not tag.fileinformation_set.exists():
                print(f"Deleting tag: {tag.name}")  # Debugging statement
                tag.delete()
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-modified_at']  # Add default ordering here



