from django.db import models
from django.utils import timezone
from django.contrib.contenttypes import generic
from djangotoolbox.fields import ListField, SetField

class StateModel(models.Model):
    state = models.TextField()
    class Meta:
        abstract = True
    
###########          General models                  ################################################# 
class StaticFile(StateModel):
    """Any models of static files should inherit from this."""
    disk_space = models.IntegerField()
    uri = models.TextField()    
    
    #Abstract base class
    class Meta:
        abstract = True
        
class AudioSource(StaticFile):
    """Audio sources are the original audio files...of anything."""
    encoding = models.TextField()
    length_seconds = models.TimeField()
    sample_rate = models.FloatField()
    
    #Abstract base class
    class Meta:
        abstract = True
          
    
###########          Hit models                  #################################################
class MturkHit(StateModel):
    """Mturk hit"""
    hit_id = models.TextField()
    hit_type_id = models.TextField()
    
    #Abstract base class
    class Meta:
        abstract = True

###########          Assignment models                  #################################################

class MturkAssignment(StateModel):
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
    
    #Abstract base class
    class Meta:
        abstract = True
        
# class Worker(models.Model):
#     """The generic mturk worker model"""
#     #This can be any type of assignment
#     worker_id = models.TextField()
#     approved_assignments = SetField(models.ForeignKey(CsaesrAssignment))
# #     approved_assignments = ListField(GenericForeignKey('content_type','object_id'))
# #     denied_assignments = ListField(GenericForeignKey('content_type','object_id'))
# #     submitted_assignments = ListField(GenericForeignKey('content_type','object_id'))
    
