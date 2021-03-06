# Copyright (C) 2014 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db import models
from collections import defaultdict

from apps.common.models import (AudioSource,
                                MturkHit,
                                CsaesrAssignment,
                                StateModel,)
from apps.common.fields import (CseasrListField,
                                CseasrSetField)

from apps.common.widgets import SetFieldWidget

#from apps.elicitation.pipelines.ElicitationPipeline import load_PromptSource_RawToList
from djangotoolbox.fields import ListField, SetField
from django.utils import timezone
         

    
class PromptSource(StateModel):
    """A file with a header and prompt on each line"""    
    sourcefile = models.FileField(upload_to='documents/%Y/%m/%d')    
    disk_space = models.IntegerField()
    uri = models.TextField()    
    prompt_count = models.IntegerField()  
    hit_list = CseasrListField()
    
    def __unicode__(self):
        return str(self.sourcefile)
    
    def add_hit(self,hit_id):
        self.hit_list.append(hit_id)
     
class ResourceManagementPrompt(StateModel):
    """Prompts from the Resource Management Corpus"""
    #Line number in the prompt source
    hit_id = models.TextField()
    source = models.ForeignKey(PromptSource)
    inqueue = models.TextField()
    line_number = models.IntegerField()
    prompt_id = models.TextField()
    word_count = models.IntegerField()
    words = CseasrListField(models.TextField())
    normalized_words = CseasrListField(models.TextField())
    
    def __unicode__(self):
        return str(self.prompt_id)
    
    
class ElicitationHit(MturkHit):
    """The specific elicitation Hit class"""
    #prompts = CseasrListField(models.ForeignKey(ResourceManagementPrompt))
    prompt_source_name = models.TextField()
    prompts = CseasrListField()
    
    def __unicode__(self):
        return self.prompt_source_name
    
class ElicitationAudioRecording(AudioSource):
    """Downloaded from Vocaroo given a submitted assignment
    """
    prompt = models.ForeignKey(ResourceManagementPrompt)
    worker_id = models.TextField()
    recording_url = models.TextField()
        
class ElicitationAssignment(CsaesrAssignment):
    """The specific elicitation assignment class"""
    recordings = CseasrSetField(models.ForeignKey(ElicitationAudioRecording))
    zipcode = models.TextField()
    hit = models.ForeignKey(ElicitationHit)
    
class Worker(StateModel):
    """The elicitation worker model.
        It was either have a different worker for elicitation and transcription
        or the same (common) worker and not know what assignments they submitted
        because each assignment and hit is different for transcription and elicitation.
        TODO-tt: Figure out how to have a SetField(GenericForeignKey), that would fix this
    """
    worker_id = models.TextField()
    approved_elicitation_assignments = SetField(models.ForeignKey(ElicitationAssignment))
    denied_elicitation_assignments = SetField(models.ForeignKey(ElicitationAssignment))
    submitted_elicitation_assignments = SetField(models.ForeignKey(ElicitationAssignment))
    blocked_elicitation_assignments = SetField(models.ForeignKey(ElicitationAssignment))
    

    
    
###########          Queue models                  #################################################
class Node(StateModel):
    """ModelNode for our ModelQueue
    """
    #TODO-tt Figure out how genericforeignkeys work...
    member = models.ForeignKey(ResourceManagementPrompt)
    priority = models.IntegerField()
    #Asynchronous processing of nodes just in case
    processing = models.DateTimeField(null=True)
    

class ObjQueue(StateModel):
    """A queue of objects
        When the number of nodes reaches max_size, take them out
            and submit the HIT if so desired        
    """    
    max_size = models.IntegerField()
    queue = CseasrListField()

    def reset(self):
        self.queue = CseasrListField()
        self.save()
        
    def enqueue(self,model_node):
        #self.queue.append(models.ForeignKey(model_node.pk))
        self.queue.append(model_node.pk)
        self.save()
        
    def dequeue(self,model_node):
        for node in self.queue:
            #Derefernce the node pk to ResourceManagementPrompt
            if Node.objects.get(pk=node).member == model_node:
                self.queue.remove(node)
        self.save()
    
    def inqueue(self,prompt):
        for node_id in self.queue:
            if node_id == prompt.pk:
                return True
        return False
    
    def get_partial_queue(self,count):
        """Get all the ModelNodes waiting in the queue and not being processed
            Find the largest queue that is full
            Update the queue and return the clips"""         
        response = []
        for node in self.queue:
            node_obj = Node.objects.get(pk=node)
            node_obj.processing = timezone.now()
            node_obj.save()
            response.append(node_obj.member)
            if len(response) == count:
                return response        
        
    def get_current_queue(self):
        """Get all the ModelNodes waiting in the queue and not being processed
            Find the largest queue that is full
            Update the queue and return the clips"""         
        response = []
        for node in self.queue:
            node_obj = Node.objects.get(pk=node)
            node_obj.processing = timezone.now()
            node_obj.save()
            response.append(node_obj.member)
            if len(response) == self.max_size:
                return response        
                     
    def revive_queue(self,revive_time):
        """If an audio clip in the queue has been processing for more than
            queue_revive_time seconds, free the clip by resetting processing"""
        for node in self.queue:
            processing = Node.objects.get(pk=node).processing
            if processing and timezone.now().replace(tzinfo=None) - processing > timezone.timedelta(revive_time):
                node.processing = None
                node.save()
        self.save()
    
    #Abstract base class
    class Meta:
        abstract = True    
            
class PromptQueue(ObjQueue):
    """A queue of prompts"""
    name = models.TextField("Prompts")
    
    def __unicode__(self):
        return self.name
    