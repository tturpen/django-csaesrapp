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

from apps.common.exceptions import TooManyEntries, WrongFieldsExecption, ModelStateNotFoundError

from django.shortcuts import get_object_or_404
from django.utils import timezone

from shutil import copyfile
import logging
import os
import datetime
from collections import defaultdict

class ModelHandler(object):
    class Meta:
        abstract = True
        
    def __init__(self):
        self.queue_revive_time = 5 

        self.c = {}#dictionary of collections
        #Initialize the state maps
        #self.c["state_maps"] = self.db.state_maps
        #self.initialize_state_map()        
 
        
    def get_model_by_id(self,collection,pk,field=None,refine={}):
        m = get_object_or_404(self.c[collection],pk=pk)
        return m
        #return field in m and m[field] if field and m else m
#         return self.get_artifact(collection,{"pk":ObjectId(art_id)},field,refine)
#         return self.get_artifact(collection,{"_id":art_id},field,refine)
    
    def get_models_by_state(self,collection,state,field=None,refine={}):
        search = {"state":state}
        return self.c[collection].objects.filter(**search)
    
    def get_models(self,collection,param,values,field=None,refine={}):
        return [self.get_artifact(collection,{param:val},field,refine) for val in values]
    
    def get_all_models(self,collection):
        return self.c[collection].find()
    
    def get_model(self,collection,search,field=None,refine={}):
        """Each model belongs to a collection in the database.""" 
#         responses = self.c[collection].find(search,refine)\
#                     if refine else self.c[collection].find(search)
        responses = self.c[collection].objects.filter(**search)
        prev = False
        for response in responses:
            if prev:
                raise TooManyEntries("%sModelHandler.get_model."%self.__name__+collection)
            prev = response        
        return field in prev and prev[field] if field and prev else prev
    
    def get_max_queue(self,max_sizes):
        max_q = []
        for q in max_sizes:
            #For each q in each q size
            if len(max_sizes[q]) >= q:
                #if the q is full
                if q > len(max_q):
                    #if the q is bigger than the q with the most clips
                    max_q = max_sizes[q][:q]
        return max_q
    
    def models_already_in_hit(self,model_pairs):
        prompts_in_hits = []
        for pair in model_pairs:
            for hit in self.get_all_artifacts("%s_hits"%self.__name__):
                if pair in hit["prompts"]:
                    prompts_in_hits.append(pair[1])#Append the clip id
                    self.logger.info("Audio clip(%s) already in HIT(%s)"(pair[1],hit["_id"]))
        return prompts_in_hits
    
#     def init_artifact_set(self,collection,artifact_id,field,values):
#         if not self.get_artifact_by_id(collection, artifact_id, field):
#             if ObjectId.is_valid(artifact_id):
#                 self.c[collection].update({"_id":ObjectId(artifact_id)},{"$set":{field:values}})
#             else:
#                 self.c[collection].update({"_id":artifact_id},{"$set":{field:values}})
    
    def remove_artifacts(self,collection,artifacts):
        """Given a list of artifacts, remove each one by _id"""
        for artifact in artifacts:
            self.c[collection].remove({"_id":artifact["_id"]})
    
    def remove_artifacts_by_id(self,collection,artifact_ids):
        """Given a list of artifacts, remove each one by _id"""
        for artifact_id in artifact_ids:
            self.c[collection].remove({"_id":artifact_id})         
                    
    def update_model(self,collection,model,field=None,value=None,document=None):
        if document:
            #Just for structure, we deref document below
            pass                                
        elif field and value:
            document = {field: value}
        else:
            raise WrongFieldsExecption
        model.__dict__.update(document)
        #self.c[collection].objects.filter(pk=model.pk).update(**document)
        #saves
        self.update_model_state(collection, model)
        
    def update_models(self,collection,models,field=None,value=None,document=None):
        for model in models:
            self.update_model(collection,model,field,value,document)
                
#     def update_artifacts_by_id(self,collection,artifact_ids,field,value,document=None):
#         """Given a list of artifact ids, update each one's field to value"""
#         if type(artifact_ids) != list:
#             self.logger.error("Error updating %s audio clip(%s)"%(collection,artifact_ids))
#             raise IOError
#         for artifact_id in artifact_ids:
#             self.update_artifact_by_id(collection,artifact_id,field,value,document)

              
    
    def upsert_artifact(self,collection,search,document):
        """Artifacts that have external imposed unique IDs
            can be created with an upsert."""            
        self.c[collection].update(search,document,upsert = True)        
            
    def remove_artifacts_from_queue(self,queue_name,artifact_queue):
        """Remove the artifact_queue from the queue"""
        self.remove_artifacts(queue_name,artifact_queue)
        self.logger.info("Finished updating database(%s) queue."%self.db_name) 
            
    def induce_model_state(self,collection,model):
        """Call the functions from the statemap, given the collection class,
            on the model
            return the state
        """
        func_class, states = self.state_map[collection]
        instance = func_class()
        prev_state = "New"
        for state in states:
            func = getattr(instance,state)
            res = func(model)
            if not res:
                return prev_state
            prev_state = state
        return state
    
    def update_artifacts_state(self,collection,artifact_ids):
        for artifact_id in artifact_ids:
            self.update_artifact_state(collection, artifact_id)
        else:
            return True
        return False
    
    def update_model_state(self,collection,model):
        """For ease of use, each class has an explicit state attribute value.
            However, states can always be determined by the state_map"""
        new_state = self.induce_model_state(collection,model)
        if new_state:
            model.state = new_state
            model.save()
        else:
            raise ModelStateNotFoundError
        self.logger.info("Updated(%s) state for: %s to %s"%(collection,model,new_state))
        return True
    
        
#     def add_item_to_model_set(self,collection,model,field,value):
#         self.update_artifact_state(collection, artifact_id)
        
    def add_assignment_to_worker(self,worker_id,assignment_tup):
        self.c["workers"].update({"_id":worker_id},{"$addToSet":{"submitted_assignments": assignment_tup}})            
                                            
    def update_assignment_state(self,assignment,state):
        self.c["assignments"].update({"_id":assignment["_id"]},
                                {"$set":{"state":state}})       
        
    def update_elicitation_hit_state(self,hit_id):
        return self.update_artifact_state("elicitation_hits", hit_id)        
    
    def get_all_workers(self):
        return self.c["workers"].find({})
    
    def get_worker_assignments(self,worker):
        """Returns approved and denied assignments submitted by the worker."""
        approved = []
        denied = []
        for assignment in worker["submitted_assignments"]:
            assignment, average_wer = assignment
            a = self.get_artifact("assignments",{"_id":assignment,"state":"Approved"},"_id")
            d = self.get_artifact("assignments",{"_id":assignment,"state":"Denied"},"_id")
            if a: approved.append(a)
            elif d: denied.append(d)
        return approved, denied    
    
    def get_prompt_pairs(self,prompt_queue):
        """Given the queue entries, return the id and text for the prompt
        """
        return [(prompt.pk,prompt.normalized_words) for prompt in prompt_queue]
    
    def get_prompt_pairs_from_prompt_id(self,prompt_queue):
        """For now give them the words,
            which are stored in the index, instead of the
            pronunciations which are stored in 'words'
        """            
        return [(prompt.pk,[prompt.prompt_id]) for prompt in prompt_queue]

