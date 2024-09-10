from django import forms

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MultiFileUploadForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={'multiple': True}))
    summary = forms.CharField(widget=forms.Textarea(attrs={'multiple': True}))
    tags = forms.CharField(widget=forms.TextInput(attrs={'multiple': True}))
    industry = forms.CharField(widget=forms.TextInput(attrs={'multiple': True}))
    files = MultipleFileField(label='Select files', required=False)
    file_type = forms.CharField(widget=forms.TextInput(attrs={'multiple': True}))
    document_type = forms.CharField(widget=forms.TextInput(attrs={'multiple': True}))
