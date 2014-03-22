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

from apps.common.pipelines import MturkPipeline
from apps.elicitation.handlers import ElicitationModelHandler, PromptHandler
from apps.elicitation.factories import ElicitationModelFactory
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
        self.ph = PromptHandler()
        self.filter = StandardFilterHandler(self.mh)
        self.logger = logging.getLogger("csaesr_app.elicitation_pipeline_handler")

    
    def load_PromptSource_RawToList(self,prompt_file_uri):
        """Create the prompt artifacts from the source."""        
        prompt_dict = self.ph.get_prompts(prompt_file_uri)        
        disk_space = os.stat(prompt_file_uri).st_size
        source_model = self.mf.create_prompt_source_model(prompt_file_uri, disk_space, len(prompt_dict))
        for key in prompt_dict:
            prompt, line_number = prompt_dict[key]
            normalized_prompt =  self.normalizer.rm_prompt_normalization(prompt)
            self.mf.create_word_prompt_model(source_model, prompt, normalized_prompt, line_number, key, len(prompt))       
 
#     def enqueue_prompts_and_generate_hits(self):
#         prompts = self.mh.get_models_by_state("prompts", "New")
#         for prompt in prompts:
#             self.mh.enqueue_prompt(prompt["_id"], 1, 5)
#             prompt_queue = self.mh.get_prompt_queue()
#             prompt_pairs = self.mh.get_prompt_pairs(prompt_queue)
#             if prompt_pairs:
#                 hit_title = "Audio Elicitation"
#                 question_title = "Speak and Record your Voice" 
#                 keywords = "audio, elicitation, speech, recording"
#                 if self.cost_sensitive:
#                     reward_per_clip = 0.05
#                     max_assignments = 2
#                     estimated_cost = self.hh.estimate_html_HIT_cost(prompt_pairs,reward_per_clip=reward_per_clip,\
#                                                                     max_assignments=max_assignments)
#                     prompts_in_hits = self.mh.prompts_already_in_hit(prompt_pairs)
#                     if prompts_in_hits:
#                         #If one or more clips are already in a HIT, remove it from the queue
#                         self.mh.remove_artifact_from_queue(prompts_in_hits)
#                     elif self.balance - estimated_cost >= 0:
#                         #if we have enough money, create the HIT
#                         response = self.hh.make_html_elicitation_HIT(prompt_pairs,hit_title,
#                                                      question_title, keywords,max_assignments=max_assignments,reward_per_clip=reward_per_clip)
# #                         response = self.hh.make_question_form_elicitation_HIT(prompt_pairs,hit_title,
# #                                                      question_title, keywords)
#                         self.balance = self.balance - estimated_cost
#                         if type(response) == ResultSet and len(response) == 1 and response[0].IsValid:
#                             response = response[0]
#                             self.mh.remove_artifacts_from_queue("prompt_queue",prompt_queue)
#                             prompt_ids = [w["prompt_id"] for w in prompt_queue]    
#                             hit_id = response.HITId
#                             hit_type_id = response.HITTypeId
#                             self.mh.create_elicitation_hit_artifact(hit_id,hit_type_id,prompt_ids)  
#                             self.mh.update_artifacts_by_id("prompts", prompt_ids, "hit_id", hit_id)      
#                             self.logger.info("Successfully created HIT: %s"%hit_id)
#                     else:
#                         return True
                       
    def run(self):
        #audio_file_dir = "/home/taylor/data/corpora/LDC/LDC93S3A/rm_comp/rm1_audio1/rm1/dep_trn"
        prompt_file_uri = "/home/taylor/data/corpora/LDC/LDC93S3A/rm_comp/rm1_audio1/rm1/doc/al_sents.snr"
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
#             elif selection == "2":
#                 self.enqueue_prompts_and_generate_hits()
#             elif selection == "3":
#                 self.load_assignment_hit_to_submitted()
#             elif selection == "4":
#                 self.recording_sources_generate_worker_sorted_html()
#             elif selection == "5":
#                 self.allhits_liveness()
#             elif selection == "6":
#                 self.approve_assignment_submitted_to_approved()
#             elif selection == "7":
#                 self.get_assignment_stats()
#             else:
#                 selection = "12"
