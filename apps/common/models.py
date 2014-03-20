from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.generic import GenericForeignKey
from djangotoolbox.fields import ListField, SetField

###########          General models                  #################################################
class StaticFile(models.Model):
    """Any models of static files should inherit from this."""
    disk_space = models.IntegerField()
    uri = models.TextField()    
    
    #Abstract base class
    class Meta:
        abstract = True

        
class PromptSource(StaticFile):
    """A file with a header and prompt on each line"""
    num_prompts = models.IntegerField()
    
class Prompt(models.Model):
    """Generic prompt model"""
    source = models.ForeignKey(PromptSource)
    #Line number in the prompt source
    line_number = models.IntegerField()
    word_count = models.IntegerField()
    normalized_words = ListField(models.TextField())
    words = ListField(models.TextField())
    raw_text = models.TextField()
    
    #Abstract base class
    class Meta:
        abstract = True

    
class ResourceManagementPrompt(Prompt):
    """Prompts from the Resource Management Corpus"""
    rm_prompt_id = models.IntegerField()
    
            
class AudioSource(StaticFile):
    """Audio sources are the original audio files...of anything."""
    encoding = models.TextField()
    length_seconds = models.TimeField()
    sample_rate = models.FloatField()
    
    #Abstract base class
    class Meta:
        abstract = True

class ResourcesManagementAudioSource(AudioSource):
    speaker_id = models.TextField()
    
    
class ElicitationAudioRecording(AudioSource):
    """Downloaded from Vocaroo given a submitted assignment
    """
    worker_id = models.TextField()
    
    
class AudioClip(StaticFile):
    """Audio Clips are portions or the entirety of an audio source
        Option to be web accessible
    """
    #Ideally this would point to a generic Audio Source but I don't know how
    source_id = GenericForeignKey()
    http_url = models.URLField()
    length_seconds = models.TimeField()
    
    
class Transcription(Prompt):
    """The generic transcription class"""
    #assignment_id = models.ForeignKey(TranscriptionAssignment)
    audio_clip_id = models.ForeignKey(AudioClip)

    
###########          Queue models                  #################################################
class ModelNode(models.Model):
    """ModelNode for our ModelQueue
    """
    member = GenericForeignKey()
    priority = models.IntegerField()
    #Asynchronous processing of nodes just in case
    processing = models.DateTimeField()
    

class ObjQueue(models.Model):
    """A queue of objects
        When the number of nodes reaches max_size, take them out
            and submit the HIT if so desired
    """    
    max_size = models.IntegerField()
    queue = ListField(models.ForeignKey(ModelNode))
    
    #Abstract base class
    class Meta:
        abstract = True    
    
    
class AudioClipQueue(ObjQueue):
    """A queue of audio clips"""
    name = models.TextField("AudioClips")
    
    
class PromptQueue(ObjQueue):
    """A queue of prompts"""
    name = models.TextField("Prompts")
    
    
###########          Hit models                  #################################################
class MturkHit(models.Model):
    """Mturk hit"""
    hit_id = models.TextField()
    hit_type_id = models.TextField()
    
    #Abstract base class
    class Meta:
        abstract = True
    
class ElicitationHit(MturkHit):
    """The specific elicitation Hit class"""
    prompts = ListField(models.ForeignKey(ResourceManagementPrompt))
    
    
class TranscriptionHit(MturkHit):
    """The specific transcription Hit"""
    audio_clips = ListField(models.ForeignKey(AudioClip))
    


###########          Assignment models                  #################################################

class MturkAssignment(models.Model):
    """The generic assignment class
        Fields prefixed with amt cache their values from Amazon
        amt values should be static with respect to Amazon"""
    assignment_status = models.TextField()
    accept_time = models.DateTimeField()
    submit_time = models.DateTimeField()
    auto_approval_date = models.DateTimeField()
    worker_id = models.IntegerField()
    assignment_id = models.TextField()
    
    #Abstract base class
    class Meta:
        abstract = True

    
class CsaesrAssignment(MturkAssignment):   
    """The specific Csaesr assignments for this app"""
    state =  models.TextField()
    
    #Abstract base class
    class Meta:
        abstract = True


class TranscriptionAssignment(CsaesrAssignment):
    """The specific transcription assignment class"""
    transcriptions = SetField(models.ForeignKey(Transcription))
    hit_id = models.ForeignKey(TranscriptionHit)

    
class ElicitationAssignment(CsaesrAssignment):
    """The specific elicitation assignment class"""
    recordings = SetField(models.ForeignKey(ElicitationAudioRecording))
    
