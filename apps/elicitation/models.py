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

from apps.common.models import (AudioSource,
                                MturkHit,
                                CsaesrAssignment,
                                ObjQueue)
from djangotoolbox.fields import ListField, SetField

         
class PromptSource(models.Model):
    """A file with a header and prompt on each line"""
    disk_space = models.IntegerField()
    uri = models.TextField()    
    prompt_count = models.IntegerField()  
     
class ResourceManagementPrompt(models.Model):
    """Prompts from the Resource Management Corpus"""
    #Line number in the prompt source
    source = models.ForeignKey(PromptSource)
    line_number = models.IntegerField()
    rm_prompt_id = models.TextField()
    word_count = models.IntegerField()
    words = ListField(models.TextField())
    normalized_words = ListField(models.TextField())
    
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
    hit_id = models.ForeignKey(ElicitationHit)
    
class Worker(models.Model):
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
    
        
class PromptQueue(ObjQueue):
    """A queue of prompts"""
    name = models.TextField("Prompts")