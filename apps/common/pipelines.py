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
import os
import datetime

from boto.mturk.connection import MTurkConnection, MTurkRequestError, ResultSet

from apps.mturk.handlers import AssignmentHandler, TurkerHandler, HitHandler
from apps.normalization.handlers import NormalizationHandler

class MturkPipeline(object):

    def __init__(self):
        aws_id = os.environ['AWS_ACCESS_KEY_ID']
        aws_k = os.environ['AWS_ACCESS_KEY']
        #HOST='mechanicalturk.amazonaws.com'
        HOST='mechanicalturk.sandbox.amazonaws.com'
        
        try:
            self.conn = MTurkConnection(aws_access_key_id=aws_id,\
                          aws_secret_access_key=aws_k,\
                          host=HOST)
        except Exception as e:
            print(e) 
        self.ah = AssignmentHandler(self.conn)
        self.th = TurkerHandler(self.conn)
        self.hh = HitHandler(self.conn)
        self.normalizer = NormalizationHandler()
        self.balance = self.conn.get_account_balance()[0].amount
        self.batch_cost = 70
        if self.balance > self.batch_cost:
            self.balance = self.batch_cost
        else:
            raise IOError
        self.cost_sensitive = True
        
    def approve_assignment_submitted_to_approved(self):
        """Approve all submitted assignments"""
        hits = self.conn.get_all_hits()
        for hit in hits:
            transcription_dicts = [{}]
            hit_id = hit.HITId
            if self.mh.get_artifact("elicitation_hits",{"_id": hit_id}):
                assignments = self.conn.get_assignments(hit_id)
                have_all_assignments = True
                assignment_ids = []
                for assignment in assignments:
                    assignment_id = assignment.AssignmentId
                    assignment_ids.append(assignment_id)  
                    if self.mh.get_artifact("elicitation_assignments",{"_id":assignment.AssignmentId,"state":"Submitted"}):
                        #WARNING: this Approves every assignment
                        self.conn.approve_assignment(assignment_id, "Thank you for completing this assignment!")
                        self.mh.update_artifact_by_id("elicitation_assignments", assignment_id, "approval_time", datetime.datetime.now())                        
                        
    def get_assignment_stats(self):
        effective_hourly_wage = self.effective_hourly_wage_for_approved_assignments(.25)                    
    
    def effective_hourly_wage_for_approved_assignments(self,reward_per_assignment):
        """Calculate the effective hourly wage for Approved Assignments"""        
        approved_assignments = self.mh.get_artifacts_by_state("elicitation_assignments","Approved")
        total = datetime.timedelta(0)
        count = 0
        for assignment in approved_assignments:
            accepted = datetime.datetime.strptime(assignment["AcceptTime"],"%Y-%m-%dT%H:%M:%SZ")
            submitted = datetime.datetime.strptime(assignment["SubmitTime"],"%Y-%m-%dT%H:%M:%SZ")
            total += submitted-accepted
            count += 1
            #self.mh.update_artifact_by_id("elicitation_assignments", assignment["_id"], "SubmitTime", completion_time)
        seconds_per_assignment = total.total_seconds()/count
        effective_hourly_wage = 60.0*60.0/seconds_per_assignment * reward_per_assignment
        print("Effective completion time(%s) *reward(%s) = %s"%(seconds_per_assignment,reward_per_assignment,effective_hourly_wage))
                        
    def recording_sources_generate_worker_sorted_html(self):
        sources = self.mh.get_all_artifacts("recording_sources")
        for source in sources:
            if not self.mh.get_artifact("workers", {"eid": source["worker_id"]}):
                pass
            
    def enqueue_prompts_and_generate_hits(self):
        prompts = self.mh.get_artifacts_by_state("prompts", "New")
        for prompt in prompts:
            self.mh.enqueue_prompt(prompt["_id"], 1, 5)
            prompt_queue = self.mh.get_prompt_queue()
            prompt_pairs = self.mh.get_prompt_pairs(prompt_queue)
            if prompt_pairs:
                hit_title = "Audio Elicitation"
                question_title = "Speak and Record your Voice" 
                keywords = "audio, elicitation, speech, recording"
                if self.cost_sensitive:
                    reward_per_clip = 0.05
                    max_assignments = 2
                    estimated_cost = self.hh.estimate_html_HIT_cost(prompt_pairs,reward_per_clip=reward_per_clip,\
                                                                    max_assignments=max_assignments)
                    prompts_in_hits = self.mh.prompts_already_in_hit(prompt_pairs)
                    if prompts_in_hits:
                        #If one or more clips are already in a HIT, remove it from the queue
                        self.mh.remove_artifact_from_queue(prompts_in_hits)
                    elif self.balance - estimated_cost >= 0:
                        #if we have enough money, create the HIT
                        response = self.hh.make_html_elicitation_HIT(prompt_pairs,hit_title,
                                                     question_title, keywords,max_assignments=max_assignments,reward_per_clip=reward_per_clip)
#                         response = self.hh.make_question_form_elicitation_HIT(prompt_pairs,hit_title,
#                                                      question_title, keywords)
                        self.balance = self.balance - estimated_cost
                        if type(response) == ResultSet and len(response) == 1 and response[0].IsValid:
                            response = response[0]
                            self.mh.remove_artifacts_from_queue("prompt_queue",prompt_queue)
                            prompt_ids = [w["prompt_id"] for w in prompt_queue]    
                            hit_id = response.HITId
                            hit_type_id = response.HITTypeId
                            self.mh.create_elicitation_hit_artifact(hit_id,hit_type_id,prompt_ids)  
                            self.mh.update_artifacts_by_id("prompts", prompt_ids, "hit_id", hit_id)      
                            self.logger.info("Successfully created HIT: %s"%hit_id)
                    else:
                        return True
                    
    def allhits_liveness(self):
        #allassignments = self.conn.get_assignments(hit_id)
        #first = self.ah.get_submitted_transcriptions(hit_id,str(clipid))

        hits = self.conn.get_all_hits()
        selection = raw_input("Remove all hits with no assignments?")
        if selection == "y":
            for hit in hits:
                hit_id = hit.HITId
                assignments = self.conn.get_assignments(hit_id)
                if len(assignments) == 0:
                    try:
                        self.conn.disable_hit(hit_id)
                        prompts = self.mh.get_artifact("elicitation_hits",{"_id": hit_id},"prompts")
                        self.mh.remove_elicitation_hit(hit_id)
                        if prompts:
                            self.mh.update_artifacts_state("prompts", prompts)
                        else:
                            pass
                    except MTurkRequestError as e:
                        raise e
            return True
        for hit in hits:
            hit_id = hit.HITId            
            print("HIT ID: %s"%hit_id)
            assignments = self.conn.get_assignments(hit_id)
            if len(assignments) == 0:
                if raw_input("Remove hit with no submitted assignments?(y/n)") == "y":
                    try:
                        self.conn.disable_hit(hit_id)
                        prompts = self.mh.get_artifact("elicitation_hits",{"_id": hit_id},"prompts")
                        self.mh.remove_elicitation_hit(hit_id)
                        if prompts:
                            self.mh.update_artifacts_state("prompts", prompts)
                        else:
                            pass
                    except MTurkRequestError as e:
                        raise e
            else:
                if raw_input("Remove hit with %s submitted assignments?(y/n)"%len(assignments)) == "y":
                    try:
                        self.conn.disable_hit(hit_id)
                    except MTurkRequestError as e:
                        raise e
