from django import forms
from apps.elicitation.models import PromptSource, ElicitationAudioRecording, ElicitationAssignment

class UploadFileForm(forms.Form):
    sourcefile  = forms.FileField()
    
class PromptSourceForm(forms.ModelForm):
    class Meta:
        model = PromptSource
        #sourcefile = forms.FileField()
        fields = ["sourcefile","uri","prompt_count"]#"disk_space","uri","prompt_count"
        
class RMPromptForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RMPromptForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['words'].widget.attrs['readonly'] = True

    def clean_sku(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.sku
        else:
            return self.cleaned_data['words']     
        
class ElicitationAssignmentForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super(ElicitationAssignmentForm,self).__init__(*args,**kwargs)
        self.fields['recordings'].widget.choices = [(i.pk, i) for i in ElicitationAudioRecording.objects.all()]
        if self.instance.pk:
            self.fields['recordings'].initial = self.instance.field
            
    class Meta:
        model = ElicitationAssignment
        
        