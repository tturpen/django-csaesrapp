"""Data handlers for elicitation"""
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
from apps.common.handlers import ModelHandler
from apps.elicitation.models import Node
from apps.mturk.handlers import AssignmentHandler, TurkerHandler, HitHandler
from apps.elicitation.models import (ResourceManagementPrompt, 
                                    ElicitationAudioRecording,
                                    PromptSource,
                                    PromptQueue,
                                    ElicitationHit,
                                    ElicitationAssignment,
                                    Worker,)
from apps.common.pipelines import MturkPipeline
from apps.text.handlers import PromptHandler
from apps.normalization.handlers import NormalizationHandler
from apps.elicitation.statemaps import ElicitationStateMap


import logging
import os

class ElicitationModelHandler(ModelHandler):
    
    def __init__(self):
        ModelHandler.__init__(self)
        self.revive_queue_time = 5
        self.c["workers"] = Worker
        self.c["queue"]  = PromptQueue.objects.filter(max_size=5)
        if not self.c["queue"]:
            self.c["queue"] = PromptQueue(name="queue",max_size=5)
            self.c["queue"].save()
        self.c["prompt_sources"] = PromptSource
        self.c["prompts"] = ResourceManagementPrompt
        self.c["hits"] = ElicitationHit
        self.c["assignments"] = ElicitationAssignment.objects
 
        self.state_map = ElicitationStateMap().state_map
        self.logger = logging.getLogger("transcription_engine.mongodb_elicitation_handler")
        
    def remove_hit(self,model):        
        model.delete()
        
    def remove_hit_id_from_prompt_sources(self,hit_id):
        for prompt_source in self.c["prompt_sources"].objects.all():
            if hit_id in prompt_source.hit_list:
                prompt_source.hit_list.remove(hit_id)
        
    def enqueue_prompt(self,prompt,priority=1,max_queue_size=3,qname="queue"):
        """Queue the audio prompt."""        
        if PromptQueue.objects.filter(name=qname).count() > 0:
            q = PromptQueue.objects.get(name=qname)
        else:
            q = PromptQueue(name=qname,max_size=max_queue_size)
        search = {"member": prompt}
        document = {"member": prompt,
                      "priority": priority,
                      }        
        if not q.inqueue(prompt):
            node = Node(**document)
            node.save()
            q.enqueue(node)
            q.save()
        self.update_model("prompts",prompt,"inqueue",qname)
        self.logger.info("Queued prompt: %s "%prompt.pk)
        
    def get_current_queue(self,qname="queue"):
        q = PromptQueue.objects.get(name=qname)    
        q.revive_queue(self.revive_queue_time)
        return q.get_current_queue()
    
    def get_partial_queue(self,qname="queue",size=10):
        q = PromptQueue.objects.get(name=qname)
        q.revive_queue(self.revive_queue_time)
        return q.get_partial_queue(size)
    
    def prompts_already_in_hit(self,prompt_queue):
        prompts_in_hits = set()
        for hit in self.c["hits"].objects.all():
            for prompt in prompt_queue:
                if prompt in hit.prompts:
                    prompts_in_hits.add(prompt)
                if len(prompts_in_hits) == len(prompt_queue):
                    return prompts_in_hits
        return prompts_in_hits
        
    def remove_models_from_queue(self,prompt_queue,qname="queue"):
        q = PromptQueue.objects.get(name=qname)        
        for prompt in prompt_queue:
            q.dequeue(prompt)
        
    def get_prompt_source_prompts(self,prompt_source):
        return ResourceManagementPrompt.objects.filter(source_id=prompt_source.pk)
 
        

                