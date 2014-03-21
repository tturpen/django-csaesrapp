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

from boto.mturk.connection import MTurkConnection, MTurkRequestError, ResultSet
from apps.mturk.handlers import AssignmentHandler, TurkerHandler, HitHandler

#from handlers.MongoDB import MongoElicitationHandler

from apps.audio.exceptions import WavHandlerException

from apps.filtering.handlers import StandardFilterHandler
from shutil import copyfile

from apps.normalization.handlers import NormalizationHandler

from apps.common.models import Worker

from apps.common.exceptions import TooManyEntries
import logging
import os
import datetime

class ModelHandler(object):
    class Meta:
        abstract = True
        
    def __init__(self):
        self.queue_revive_time = 5 

        self.c = {}#dictionary of collections
        self.c["workers"] = self.db.workers
        #Initialize the state maps
        #self.c["state_maps"] = self.db.state_maps
        #self.initialize_state_map()        
 
        
    def get_model_by_id(self,collection,art_id,field=None,refine={}):
        if ObjectId.is_valid(art_id):
            return self.get_artifact(collection,{"_id":ObjectId(art_id)},field,refine)
        return self.get_artifact(collection,{"_id":art_id},field,refine)
    
    def get_models_by_state(self,collection,state,field=None,refine={}):
        return self.c[collection].find({"state":state})
    
    def get_models(self,collection,param,values,field=None,refine={}):
        return [self.get_artifact(collection,{param:val},field,refine) for val in values]
    
    def get_all_models(self,collection):
        return self.c[collection].find()
    
    def get_model(self,collection,search,field=None,refine={}):
        """Each model belongs to a collection in the database.""" 
        responses = self.c[collection].find(search,refine)\
                    if refine else self.c[collection].find(search)
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
    
    def revive_queue(self,queue_name):
        """If an audio clip in the queue has been processing for more than
            queue_revive_time seconds, free the clip by resetting processing"""
        non_none = self.c[queue_name].find({"processing": {"$ne" : None}})
        for artifact in non_none:
            if  time() - artifact["processing"] > self.queue_revive_time:
                self.c[queue_name].update({"_id":artifact["_id"]}, {"$set" : {"processing" : None}})  
        self.logger.info("Finished reviving database(%s) queue."%self.db_name)
        
    def init_artifact_set(self,collection,artifact_id,field,values):
        if not self.get_artifact_by_id(collection, artifact_id, field):
            if ObjectId.is_valid(artifact_id):
                self.c[collection].update({"_id":ObjectId(artifact_id)},{"$set":{field:values}})
            else:
                self.c[collection].update({"_id":artifact_id},{"$set":{field:values}})
    
    def remove_artifacts(self,collection,artifacts):
        """Given a list of artifacts, remove each one by _id"""
        for artifact in artifacts:
            self.c[collection].remove({"_id":artifact["_id"]})
    
    def remove_artifacts_by_id(self,collection,artifact_ids):
        """Given a list of artifacts, remove each one by _id"""
        for artifact_id in artifact_ids:
            self.c[collection].remove({"_id":artifact_id})
         
    def update_artifact_with_document(self,collection,artifact_id,document):   
        """Given a list of artifact ids, update each one's field to value"""
        self.c[collection].update({"_id":artifact_id}, document)
                    
    def update_artifact_by_id(self,collection,artifact_id,field=None,value=None,document=None):
        if document:
            #Careful, this replaces the document entirely
            if ObjectId.is_valid(artifact_id):
                self.c[collection].update({"_id":ObjectId(artifact_id)}, document)
            else:
                self.c[collection].update({"_id":artifact_id}, document)
            if field != "state":
                #Because updating the state calls this method
                self.update_artifact_state(collection, artifact_id)
        elif field and value:
            if ObjectId.is_valid(artifact_id):
                self.c[collection].update({"_id":ObjectId(artifact_id)}, {"$set" : {field:value}})
            else:
                self.c[collection].update({"_id":artifact_id}, {"$set" : {field:value}})
            if field != "state":
                #Because updating the state calls this method
                self.update_artifact_state(collection, artifact_id)          
        else:
            raise WrongParametersExecption
                
    def update_artifacts_by_id(self,collection,artifact_ids,field,value,document=None):
        """Given a list of artifact ids, update each one's field to value"""
        if type(artifact_ids) != list:
            self.logger.error("Error updating %s audio clip(%s)"%(collection,artifact_ids))
            raise IOError
        for artifact_id in artifact_ids:
            self.update_artifact_by_id(collection,artifact_id,field,value,document)

              
    
    def upsert_artifact(self,collection,search,document):
        """Artifacts that have external imposed unique IDs
            can be created with an upsert."""            
        self.c[collection].update(search,document,upsert = True)        
            
    def remove_artifacts_from_queue(self,queue_name,artifact_queue):
        """Remove the artifact_queue from the queue"""
        self.remove_artifacts(queue_name,artifact_queue)
        self.logger.info("Finished updating database(%s) queue."%self.db_name) 
        
    def get_collection_state_map(self,collection):
        return self.c["state_maps"].find({})[0][collection]
            
    def induce_artifact_state(self,collection,artifact_id):
        func_class, states = self.get_collection_state_map(collection)
        instance = getattr(Elicitation,func_class)()
        artifact = self.get_artifact_by_id(collection, artifact_id)
        prev_state = "New"
        for state in states:
            func = getattr(instance,state)
            res = func(artifact)
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
    
    def update_artifact_state(self,collection,artifact_id):
        """For ease of use, each class has an explicit state attribute value.
            However, states can always be determined by the state_map"""
        new_state = self.induce_artifact_state(collection,artifact_id)
        self.update_artifacts_by_id(collection,[artifact_id],"state",new_state)
        self.logger.info("Updated(%s) state for: %s to %s"%(collection,artifact_id,new_state))
        return True
    
    def create_artifact(self,collection,search,document,update=True):
        """Check to see if the artifact exists given search,
            create the artifact
            update the state by induction."""
        art_id = self.get_artifact(collection, search, "_id")
        if not art_id:
            self.c[collection].insert(document)
            art_id = self.get_artifact(collection, document,"_id")
            self.logger.info("Created %s artifact(%s) "%(collection,art_id))
        elif update:
            self.update_artifact_by_id(collection,art_id,document=document)
        self.update_artifact_state(collection, art_id)
        return art_id       
        
    def create_elicitation_hit_artifact(self,hit_id,hit_type_id,prompt_ids):
        if type(prompt_ids) != list:
            raise IOError
        document =  {"_id":hit_id,
                     "hit_type_id": hit_type_id,
                     "prompts" : prompt_ids}
        art_id = self.create_artifact("elicitation_hits",{"_id": hit_id},document)
        return art_id
    
    def create_assignment_artifact(self,assignment,answers):
        """Create the assignment document with the transcription ids.
            AMTAssignmentStatus is the AMT assignment state.
            state is the engine lifecycle state."""
        assignment_id = assignment.AssignmentId
        document = {"_id":assignment_id,
                     "AcceptTime": assignment.AcceptTime,
                     "AMTAssignmentStatus" : assignment.AssignmentStatus,
                     "AutoApprovalTime" : assignment.AutoApprovalTime,
                     "hit_id" : assignment.HITId,
                     "worker_id" : assignment.WorkerId,
                     "recordings" : answers}
        art_id = self.create_artifact("elicitation_assignments", {"_id": assignment_id},document)        
        return art_id
    
    def create_prompt_source_artifact(self,uri,disk_space,prompt_count):
        """Each audio source is automatically an audio clip,
            Therefore the reference transcription can be found
            by referencing the audio clip assigned to this source.
            For turkers, speaker id will be their worker id"""    
        search = {"uri" : uri,
                    "disk_space" : disk_space,
                    "prompt_count": prompt_count}    
        document = {"uri" : uri,
                    "disk_space" : disk_space,
                    "prompt_count": prompt_count} 
        #soft source checking
        art_id = self.create_artifact("prompt_sources", search, document)
        return art_id
        
    def create_worker_artifact(self,worker_id):
        document = {"eid": worker_id}
        art_id = self.create_artifact("workers",{"eid": worker_id},document)
        return art_id
    
    def create_prompt_artifact(self,source_id, words, normalized_words,line_number,rm_prompt_id,word_count):
        """A -1 endtime means to the end of the clip."""
        search = {"source_id" : source_id,
                    "line_number" : line_number,
                    "rm_prompt_id" : rm_prompt_id,
                    "word_count": word_count}
        document = {"source_id" : source_id,
                    "line_number" : line_number,
                    "rm_prompt_id" : rm_prompt_id,
                    "words" : words,
                    "normalized_words": normalized_words,
                    "word_count": word_count}
        art_id = self.create_artifact("prompts", search, document)
        return art_id
    
    def create_recording_source_artifact(self,prompt_id,recording_url,worker_id):
        """Use the recording handler to download the recording
            and create the artifact"""
        recording_uri = self.rh.download_vocaroo_recording(recording_url)
        search = {"recording_url" : recording_url}
        document = {"recording_url": recording_url,
                    "prompt_id": prompt_id,
                    "recording_uri": recording_uri,
                    "worker_id": worker_id}
        art_id = self.create_artifact("recording_sources", search, document)
        return art_id
        
    def add_item_to_artifact_set(self,collection,artifact_id,field,value):
        self.init_artifact_set(collection,artifact_id,field,[])
        if ObjectId.is_valid(artifact_id):
            self.c[collection].update({"_id":ObjectId(artifact_id)},{"$addToSet":{field: value}})
        else:
            self.c[collection].update({"_id":artifact_id},{"$addToSet":{field: value}})
        self.update_artifact_state(collection, artifact_id)
        
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
    
    def remove_elicitation_hit(self,hit_id):
        self.remove_artifacts_by_id("elicitation_hits", [hit_id])
                
    def get_prompt_pairs(self,prompt_queue):
        """Given the queue entries, return the id and text for the prompt
        """
        return [(self.get_artifact("prompts",{"_id":w["prompt_id"]},field="normalized_words"),w["prompt_id"]) for w in prompt_queue]
               
    def enqueue_prompt(self,prompt_id,priority=1,max_queue_size=3):
        """Queue the audio prompt."""        
        self.c["prompt_queue"].update({"prompt_id": prompt_id},
                             {"prompt_id": prompt_id,
                              "priority": priority,
                              "max_size": max_queue_size,
                              "processing" : None,
                              },
                             upsert = True)
        self.update_artifacts_by_id("prompts", [prompt_id], "inqueue", "prompt_queue")
        self.logger.info("Queued prompt: %s "%prompt_id)
        
    def get_prompt_queue(self):
        """Insert the audio clip by id into the queue.
            Get all the clips waiting in the queue and not being processed
            Find the largest queue that is full
            Update the queue and return the clips"""
        qname = "prompt_queue"          
        self.revive_queue("prompt_queue")
        queue = self.c[qname].find({"processing":None}).limit(MAX_QUEUE_VIEW)
        max_sizes = defaultdict(list)
        for prompt in queue:
            #For all the prompts
            priority = prompt["priority"]
            processing = prompt["processing"]
            max_size = int(prompt["max_size"])
            max_sizes[max_size].append(prompt)
        #Get the largest full queue
        max_q = self.get_max_queue(max_sizes)        
        for clip in max_q:
            t = time()
            self.c[qname].find_and_modify(query = {"_id":clip["_id"]},
                                                 update = { "$set" : {"processing":t}})
        return max_q

class PipelineHandler(object):

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
        self.batch_cost = 20
        if self.balance > self.batch_cost:
            self.balance = self.batch_cost
        else:
            raise IOError
        
    def load_PromptSource_RawToList(self,prompt_file_uri):
        """Create the prompt artifacts from the source."""        
        prompt_dict = self.ph.get_prompts(prompt_file_uri)        
        disk_space = os.stat(prompt_file_uri).st_size
        source_id = self.mh.create_prompt_source_artifact(prompt_file_uri, disk_space, len(prompt_dict))
        for key in prompt_dict:
            prompt, line_number = prompt_dict[key]
            normalized_prompt =  self.normalizer.rm_prompt_normalization(prompt)
            self.mh.create_prompt_artifact(source_id, prompt, normalized_prompt, line_number, key, len(prompt))       
            
    def load_assignment_hit_to_submitted(self):
        """Check all assignments for audio clip IDs.
            Update the audio clips.
            This is a non-destructive load of the assignments from MTurk"""
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
                    if self.mh.get_artifact("elicitation_assignments",{"_id":assignment.AssignmentId}):
                        #We create assignments here, so if we already have it, skip
                        #continue
                        pass
                    else:
                        have_all_assignments = False                                         
                    recording_ids = []                
                    prompt_id_tag = "prompt_id"
                    recording_url_tag = "recording_url"
                    worker_id_tag = "worker_id"
                    recording_dict = self.ah.get_assignment_submitted_text_dict(assignment,prompt_id_tag,recording_url_tag)
                    worker_oid = self.mh.create_worker_artifact(assignment.WorkerId)   
                    for recording in recording_dict:
                        if not self.mh.get_artifact_by_id("prompts",recording[prompt_id_tag]): 
                            self.logger.info("Assignment(%s) with unknown %s(%s) skipped"%\
                                        (assignment_id,prompt_id_tag,recording[prompt_id_tag]))
                            break                        
                        recording_id = self.mh.create_recording_source_artifact(recording[prompt_id_tag],
                                                                         recording[recording_url_tag],
                                                                         recording[worker_id_tag])
                        self.mh.add_item_to_artifact_set("prompts", recording[prompt_id_tag], "recording_sources",
                                                       recording_id)
                        recording_ids.append(recording_id)
                    else:
                        self.mh.create_assignment_artifact(assignment,
                                                       recording_ids)
                        self.mh.add_item_to_artifact_set("elicitation_hits", hit_id, "submitted_assignments", assignment_id)
                        self.mh.add_item_to_artifact_set("workers", worker_oid, "submitted_assignments", assignment_id)
                print("Elicitation HIT(%s) submitted assignments: %s "%(hit_id,assignment_ids))    

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
                if cost_sensitive:
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
            elif selection == "2":
                self.enqueue_prompts_and_generate_hits()
            elif selection == "3":
                self.load_assignment_hit_to_submitted()
            elif selection == "4":
                self.recording_sources_generate_worker_sorted_html()
            elif selection == "5":
                self.allhits_liveness()
            elif selection == "6":
                self.approve_assignment_submitted_to_approved()
            elif selection == "7":
                self.get_assignment_stats()
            else:
                selection = "12"
