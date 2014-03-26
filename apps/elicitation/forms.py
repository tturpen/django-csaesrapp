from django import forms
from apps.elicitation.models import PromptSource

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    sourcefile  = forms.FileField()
    
class PromptSourceForm(forms.ModelForm):
    class Meta:
        model = PromptSource
        #sourcefile = forms.FileField()
        fields = ["sourcefile","uri","prompt_count"]#"disk_space","uri","prompt_count"