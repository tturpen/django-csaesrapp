from django.db import models
from django.utils import timezone

from djangotoolbox.fields import ListField
from djangotoolbox.fields.

class StaticFile(models.Model):
    """Any models of static files should inherit from this."""
    disk_space = models.IntegerField()
    uri = models.TextField()
    
    
class AudioSource(StaticFile):
    
class AudioClip():
    source_id = models.ForeignKey(AudioSource)
    http_url = models.URLField()
    length_time = models.FloatField()
    
class Transcription(models.Model):
    """The generic transcription class"""
    #assignment_id = models.ForeignKey(TranscriptionAssignment)
    audio_clip_id = models.ForeignKey(AudioClip)
    
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
    
class CsaesrAssignment(MturkAssignment):   
    """The specific Csaesr assignments for this app"""
    state =  models.TextField()

class TranscriptionAssignment(CsaesrAssignment):
    """The specific transcription assignment class"""
    transcriptions = SetField(models.ForeignKey(Transcription))
    
class ElicitationAssignment(CsaesrAssignment):
    """The specific elicitation assignment class"""
    recordings = 
    
