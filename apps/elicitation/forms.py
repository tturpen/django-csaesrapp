from django import forms
from apps.elicitation.models import PromptSource, ElicitationAudioRecording, ElicitationAssignment
from apps.common.widgets import SetFieldWidget
import sys


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
        if self.instance.pk:
            #print "widget help: " + str(help(self.fields['recordings'].widget))
            sys.stdout.flush()
            self.fields['recordings'].widget.choices = [(i,i) for i in self.instance.recordings]#objects.all() else None for i in ElicitationAudioRecording.objects.all()]
            #self.fields['recordings'].widget = SetFieldWidget
            self.fields['recordings'].initial = self.instance.recordings
            
    class Meta:
        model = ElicitationAssignment
        #widgets = {'recordings' : SetFieldWidget}

 
        