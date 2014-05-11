"""Elicitation pipelines"""
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
import logging
import os
import sys

from django.conf import settings

from boto.mturk.connection import ResultSet

from apps.common.pipelines import MturkPipeline
from apps.elicitation.handlers import ElicitationModelHandler, PromptHandler
from apps.elicitation.factories import ElicitationModelFactory
from apps.elicitation.adapters import ResourceManagementAdapter, CMUPronunciationAdapter

from apps.filtering.handlers import StandardFilterHandler
# from apps.elicitation.models import (ResourceManagementPrompt, 
#                                     ElicitationAudioRecording,
#                                     PromptQueue,
#                                     ElicitationHit,
#                                     ElicitationAssignment)

class ElicitationPipeline(MturkPipeline):
    
    def __init__(self):
        MturkPipeline.__init__(self)
        self.mh = ElicitationModelHandler()
        self.mf = ElicitationModelFactory()
        #self.rma = ResourceManagementAdapter()
        
        self.prompt_adapter = CMUPronunciationAdapter(wordlist_file=settings.WORD_FILTER_FILE)
        self.filter = StandardFilterHandler(self.mh)
        self.logger = logging.getLogger("csaesr_app.elicitation_pipeline_handler")
                
    def load_PromptSource_RawToList(self,source_model):
        """Create the prompts from the source."""        
        sourcefile = source_model.sourcefile
        uri = str(sourcefile)
        size = os.stat(uri).st_size   
        source_model.uri = uri
        source_model.disk_space = size
        
        lines = open(uri).readlines()        
        prompt_dict = self.prompt_adapter.get_id_dict(lines)    
        prompt_dict = self.prompt_adapter.post_proc_id_dict(prompt_dict)
        for key in prompt_dict:
            prompt, line_number = prompt_dict[key]
            normalized_prompt =  self.normalizer.rm_prompt_normalization(prompt)
            self.mf.create_word_prompt_model(source_model, prompt, normalized_prompt, line_number, key, len(prompt))
        source_model.prompt_count = len(prompt_dict)
        source_model.save()
        self.mh.update_model_state("prompt_sources", source_model)  
 
    def remove_hit_from_mturk(self,hit_model):
        """Disable the HIT via the mturk connection,
            remove the hit id from the promptsource hit list
            remove the hit from the database."""
        self.conn.disable_hit(hit_model.hit_id)
        self.mh.remove_hit_id_from_prompt_sources(hit_model.hit_id)
        self.mh.remove_hit(hit_model)
                
    def create_hits_from_promptsource(self,prompt_source,qname): 
        """Create the most HITs possible given the prompt source."""
        max_queue_size = 10
        prompt_priority = 1       
        self.mh.reset_queue(qname)
        prompts = self.mh.get_prompt_source_prompts(prompt_source)
        for prompt in prompts:
            self.mh.enqueue_prompt(prompt,prompt_priority, max_queue_size=max_queue_size,qname=qname)
            prompt_queue = self.mh.get_current_queue(qname=qname)
            if prompt_queue:
                print "got queue: %s"%qname
                sys.stdout.flush()
                self.create_hit_from_queue(prompt_queue,prompt_source,qname)
                
    def create_hit_from_partial_queue(self,prompt_source,qname,size):
        """Create a hit even if the queue is full, given size"""
        prompt_queue = self.mh.get_partial_queue(qname=qname,size=size)
        if prompt_queue:
            self.create_hit_from_queue(prompt_queue,prompt_source,qname)
        
    def create_hit_from_queue(self,prompt_queue,prompt_source,qname): 
        """Given a prompt queue (list of prompts),
            create the hit via the hit handler.
            TODO-tt move hit creation to hit factory."""
        prompt_pairs = self.mh.get_prompt_pairs_from_prompt_id(prompt_queue)
        template_name = "elicitation/cmuelicitationhit.html"
        if prompt_pairs:
            sys.stdout.flush()
            hit_title = "Audio Elicitation"
            question_title = "Speak and Record your Voice" 
            keywords = "audio, elicitation, speech, recording"
            hit_description = "Speak English prompts and record your voice."
            if self.cost_sensitive:
                reward_per_clip = 0.02
                max_assignments = 30
                estimated_cost = self.hh.estimate_html_HIT_cost(prompt_pairs,reward_per_clip=reward_per_clip,\
                                                                max_assignments=max_assignments)
                prompts_in_hits = self.mh.prompts_already_in_hit(prompt_pairs)
                if prompts_in_hits:
                    #If one or more clips are already in a HIT, remove it from the queue
                    self.mh.remove_models_from_queue(prompts_in_hits)
                elif self.balance - estimated_cost >= 0:
                    #if we have enough money, create the HIT
                    response = self.hh.make_html_elicitation_HIT(prompt_pairs,hit_title,
                                                 question_title, keywords,hit_description=hit_description,
                                                 max_assignments=max_assignments,
                                                 reward_per_clip=reward_per_clip,
                                                 template=template_name)
#                         response = self.hh.make_question_form_elicitation_HIT(prompt_pairs,hit_title,
#                                                      question_title, keywords)
                    self.balance = self.balance - estimated_cost
                    if type(response) == ResultSet and len(response) == 1 and response[0].IsValid:
                        response = response[0]
                        self.mh.remove_models_from_queue(prompt_queue,qname=qname)
                        prompt_ids = [w.pk for w in prompt_queue]    
                        hit_id = response.HITId
                        hit_type_id = response.HITTypeId
                        self.mf.create_elicitation_hit_model(hit_id,
                                                             hit_type_id,
                                                             prompt_ids,
                                                             prompt_source_name=prompt_source.uri,
                                                             template_name=template_name,
                                                             redundancy=max_assignments)
                        prompt_source.add_hit(hit_id)
                        self.mh.update_model_state("prompt_sources", prompt_source)
                        prompt_source.save()  
                        self.mh.update_models("prompts",prompt_queue, "hit_id", hit_id)      
                        self.logger.info("Successfully created HIT: %s"%hit_id)
                else:
                    return True

    def load_submitted_assignments_from_mturk(self,hit_obj):        
        hit_id = hit_obj.hit_id
        if self.mh.get_model("hits",{"hit_id": hit_id}):
            assignments = self.conn.get_assignments(hit_id,page_size=50)
            have_all_assignments = True
            assignment_ids = []
            assignment_count = 0
            sys.stdout.flush()
            for assignment in assignments:
                assignment_count += 1
                assignment_id = assignment.AssignmentId
                assignment_ids.append(assignment_id)  
                if self.mh.get_model("assignments",{"assignment_id":assignment.AssignmentId}):
                    #We create assignments here, so if we already have it, skip
                    continue
                    #pass
                else:
                    have_all_assignments = False                                         
                recording_ids = []                
                prompt_id_tag = "prompt_id"
                recording_url_tag = "recording_url"
                worker_id_tag = "worker_id"
                recording_dict = self.ah.get_assignment_submitted_text_dict(assignment,prompt_id_tag,recording_url_tag)
                worker = self.mf.create_worker_model(assignment.WorkerId)   
                print("Trying to get recording_dict(%s)"%recording_dict)
                sys.stdout.flush()
                for recording in recording_dict:
                    prompt_obj_id = self.prompt_adapter.get_prompt_id_from_assignment_answer_id(recording[prompt_id_tag])
                    if prompt_obj_id == "zipcode":
                        continue   
                    prompt = self.mh.get_model_by_id("prompts",prompt_obj_id)
                    if not prompt: 
                        self.logger.info("Assignment(%s) with unknown %s(%s) skipped"%\
                                    (assignment_id,prompt_id_tag,recording[prompt_id_tag]))
                        break
                    print("Trying to get prompt_id(%s)"%prompt_obj_id)
                    sys.stdout.flush()

   
                    #prompt_words = self.mh.get_normalized_prompt_words(prompt)
                    cmu_prompt_word = [prompt.prompt_id]
                    recording_obj = self.mf.create_recording_source_model(prompt,
                                                                     recording[recording_url_tag],
                                                                     worker=worker,
                                                                     prompt_words=cmu_prompt_word)
                    if recording_obj:
                        recording_ids.append(recording_obj.pk)
                    else:
                        recording_ids.append(None)
                else:
                    print("recording_ids(%s)"%recording_ids)
                    sys.stdout.flush()
                    self.mf.create_assignment_model(assignment, recording_ids,hit_obj)
#                     self.mh.add_item_to_artifact_set("elicitation_hits", hit_id, "submitted_assignments", assignment_id)
#                     self.mh.add_item_to_artifact_set("workers", worker_oid, "submitted_assignments", assignment_id)
            print("Elicitation HIT(%s) submitted assignments: %s "%(hit_id,assignment_ids))    
        print "Assignment Count: %s" % assignment_count

                       
    def run(self):
        prompt_file_uri = settings.PROMPT_FILE
        selection = 0
        #self.get_time_submitted_for_assignments()
        while selection != "12":
            selection = raw_input("""Prompt Source raw to Elicitations-Approved Pipeline:\n
                                     1: PromptSource-Load_RawToList: Load Resource Management 1 prompt source files to queueable prompts
                                     2: Prompt-ReferencedToHit: Queue all referenced prompts and create a HIT if the queue is full.
                                     3: Prompt-HitToAssignmentSubmitted: Check all submitted assignments for Elicitations.
                                     4: RecordingSources-GenerateWorkerSortedHtml: Check all submitted assignments for Elicitations.
                                     5: Review Current Hits
                                     6: ElicitationAssignment-SubmittedToApproved: Approve submitted assignments.
                                     7: Review Current Hits
                                     8: Worker liveness
                                     9: Account balance
                                     10: Worker stats
                                     11: Recalculate worker WER
                                     12: Exit
                                    """)
            if selection == "1":
                self.load_PromptSource_RawToList(prompt_file_uri)
            elif selection == "2":
                self.enqueue_prompts_and_generate_hits()
            elif selection == "3":
                self.check_hits_for_submitted_assignments()
#             elif selection == "4":
#                 self.recording_sources_generate_worker_sorted_html()
#             elif selection == "5":
#                 self.allhits_liveness()
#             elif selection == "6":
#                 self.approve_assignment_submitted_to_approved()
#             elif selection == "7":
#                 self.get_assignment_stats()
            else:
                selection = "12"
