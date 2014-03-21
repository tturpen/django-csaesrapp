from django.db import models

from apps.common.models import (StaticFile,
                                WordPrompt,
                                AudioSource,
                                MturkHit,
                                CsaesrAssignment,
                                ObjQueue)
from djangotoolbox.fields import ListField, SetField

    
class ResourceManagementPrompt(WordPrompt):
    """Prompts from the Resource Management Corpus"""
    rm_prompt_id = models.IntegerField()
    
    
    
class ElicitationAudioRecording(AudioSource):
    """Downloaded from Vocaroo given a submitted assignment
    """
    worker_id = models.TextField()
    
class ElicitationHit(MturkHit):
    """The specific elicitation Hit class"""
    prompts = ListField(models.ForeignKey(ResourceManagementPrompt))
    
class ElicitationAssignment(CsaesrAssignment):
    """The specific elicitation assignment class"""
    recordings = SetField(models.ForeignKey(ElicitationAudioRecording))
    
        
class PromptQueue(ObjQueue):
    """A queue of prompts"""
    name = models.TextField("Prompts")