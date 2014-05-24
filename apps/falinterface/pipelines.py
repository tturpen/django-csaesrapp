"""This pipeline removes any need for the database backend 
but does not support that additional functionality"""
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

from boto.mturk.connection import ResultSet, MTurkConnection, MTurkRequestError

from apps.common.pipelines import MturkPipeline
from apps.audio.handlers import SoxHandler, RecordingHandler
from apps.elicitation.handlers import ElicitationModelHandler, PromptHandler
from apps.elicitation.factories import ElicitationModelFactory
from apps.elicitation.adapters import ResourceManagementAdapter, CMUPronunciationAdapter

from apps.filtering.handlers import StandardFilterHandler
from apps.mturk.handlers import HitHandler

from datetime import timedelta
# from apps.elicitation.models import (ResourceManagementPrompt, 
#                                     ElicitationAudioRecording,
#                                     PromptQueue,
#                                     ElicitationHit,
#                                     ElicitationAssignment)

class FastAndLooseElicitationPipeline(MturkPipeline):
    
    def __init__(self,task_name):
        MturkPipeline.__init__(self)
        self.mh = ElicitationModelHandler()
        self.mf = ElicitationModelFactory()
        self.sox_handler = SoxHandler()
        self.recording_handler = RecordingHandler()
        #self.rma = ResourceManagementAdapter()
        
        self.prompt_adapter = CMUPronunciationAdapter(wordlist_file=settings.WORD_FILTER_FILE)
        self.filter = StandardFilterHandler(self.mh)
        self.logger = logging.getLogger("csaesr_app.fal_elicitation_pipeline_handler")
        self.recordings_tag = "recordings"
        self.NOT_PULLED_TAG = "NOT_PULLED"
        self.base_fal_elicitation_hit_dir = os.path.join(settings.FAL_BASE_DIR,
                                                                "elicitation",
                                                                task_name,
                                                                "hits")
        
        
    def have_assignment(self,assignment_dir):
        if os.path.isdir(assignment_dir):
            return "OK"
        return self.NOT_PULLED_TAG
    
    def detailed_assignment_status(self,assignment_id):
        assignment_dir = os.path.join(self.base_fal_elicitation_assignment_dir,assignment_id)
        recordings_dir = os.path.join(assignment_dir,self.recordings_tag)
        if os.path.isdir(recordings_dir):
            for f in os.listdir(recordings_dir):
                self.sox_handler.get_wav_audio_length(os.path.join(recordings_dir,f))
        else:
            return "No recordings directory"
            
    def load_submitted_assignments_from_mturk(self,hit_id,sequential_set_name):
        """Load all assignments from mturk
            see which ones we've got
            pull the recordings we don't have from vocaroo."""   
                          
        assignments = self.conn.get_assignments(hit_id,page_size=100)
        have_all_assignments = True
        assignment_ids = []
        assignment_count = 0
        sys.stdout.flush()
        hit_dir = os.path.join(self.base_fal_elicitation_hit_dir,hit_id)
        for assignment in assignments:
            assignment_count += 1
            assignment_id = assignment.AssignmentId
            assignment_dir = os.path.join(hit_dir,assignment_id)
            assignment_ids.append(assignment_id)  
            assignment_status = self.have_assignment(assignment_dir)
            #worker_id = assignment.WorkerId
            if assignment_status == self.NOT_PULLED_TAG:
                recordings_dir = os.path.join(assignment_dir,self.recordings_tag)
                try:
                    os.makedirs(recordings_dir)
                except Exception:
                    #path exists
                    pass
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
                    #prompt = self.mf..get_fal_prompt("prompts",prompt_obj_id)
                    if not prompt_obj_id: 
                        self.logger.info("Assignment(%s) with unknown %s(%s) skipped"%\
                                    (assignment_id,prompt_id_tag,recording[prompt_id_tag]))
                        break
                    print("Trying to get prompt_id(%s)"%prompt_obj_id)
                    sys.stdout.flush()
        
        
                    #prompt_words = self.mh.get_normalized_prompt_words(prompt)
                    rec_result = self.recording_handler.download_vocaroo_recording(recording[recording_url_tag], 
                                                                      type="wav", 
                                                                      worker_id=recording["worker_id"], 
                                                                      prompt_name=sequential_set_name + str(prompt_obj_id),
                                                                      dest_dir=recordings_dir)
                else:
                    print("recording_ids(%s)"%recording_ids)
                    sys.stdout.flush()
            elif assignment_status == "NOT_OK":
                print self.detailed_assignment_status(assignment_id)
        #                     self.mh.add_item_to_artifact_set("elicitation_hits", hit_id, "submitted_assignments", assignment_id)
        #                     self.mh.add_item_to_artifact_set("workers", worker_oid, "submitted_assignments", assignment_id)
            print("Elicitation HIT(%s) submitted assignments: %s "%(hit_id,assignment_ids))    
        print "Assignment Count: %s" % assignment_count
        
    def approve_submitted_assignments_with_valid_recordings(self,hit_id,sequential_set_name):
        """Approve those assignments with some recording."""                             
        hit_dir = os.path.join(self.base_fal_elicitation_hit_dir,hit_id)
        for assignment in os.listdir(hit_dir):
            assignment_dir = os.path.join(hit_dir,assignment)
            if os.path.isdir(assignment_dir):
                recordings_dir = os.path.join(assignment_dir,self.recordings_tag)
                for recording in os.listdir(recordings_dir):
                    recording_path = os.path.join(recordings_dir,recording)
                    if self.sox_handler.get_wav_audio_length(recording_path):
                        pass
                    else:
                        break
                else:
                    print self.conn.approve_assignment(assignment)

class FastAndLooseTranscriptionPipeline(MturkPipeline):
    
    def __init__(self,task_name):
        MturkPipeline.__init__(self)
        self.mh = ElicitationModelHandler()
        self.mf = ElicitationModelFactory()
        self.logger = logging.getLogger("csaesr_app.fal_trasncription_pipeline_handler")
        self.clips_tag = "recordings"
        self.NOT_PULLED_TAG = "NOT_PULLED"
        self.clip_dir = "/home/taylor/data/speech/spanish_hub4/spanish_hub4_excerpted/subset/"
        self.spanish_hub4_base_url = "http://www.cis.upenn.edu/~tturpen/wavs/hub4/subset/"
        
    def get_audio_clip_pairs(self,base_dir,base_url,clip_count):
        """Get audio clips from a directory and return their ids along with urls."""
        pairs = []
        for f in os.listdir(base_dir)[:clip_count+1]:
            pairs.append((base_url+f,f))
        return pairs
    
    def submit_audio_hits(self):
        aws_id = os.environ['AWS_ACCESS_KEY_ID']
        aws_k = os.environ['AWS_ACCESS_KEY']
                
        try:
            conn = MTurkConnection(aws_access_key_id=aws_id,\
                          aws_secret_access_key=aws_k,\
                          host=settings.MTURK_HOST)
        except Exception as e:
            print(e) 
        clip_dir = "/home/taylor/data/speech/spanish_hub4/spanish_hub4_excerpted/subset/"
        hh = HitHandler(conn)
        hit_title = "Spanish Audio Transcription"
        question_title = "Speak and Record your Voice" 
        keywords = "audio, transcription, Spanish, speech, recording"
        hit_description = "Write the Spanish words that are said."
        max_assignments = 10
        reward_per_clip = .02
        duration = 60*50
        one_month = timedelta(40)
        descriptions = ["The following audio clips are in Spanish.",
                        "Transcribe the audio clip by typing the words that the person \
                        says in order.",
                        "Do not use abbreviations.",
                        "Write numbers long-form, as in: 'ocho' NOT '8'.",
                        "Punctuation does not matter.",
                        "Hotkeys: press Tab to play the next clip."]
        clip_count = 10
        audio_clip_tups = self.get_audio_clip_pairs(clip_dir,self.spanish_hub4_base_url,clip_count)
        print audio_clip_tups
        disable text input fool!
        response = hh.make_html_spanish_transcription_HIT(audio_clip_tups, 
                                                     hit_title, 
                                                     question_title, 
                                                     keywords=keywords,
                                                     duration=duration,
                                                     hit_description=hit_description,
                                                     max_assignments=max_assignments,
                                                     reward_per_clip=reward_per_clip,
                                                     lifetime=one_month,
                                                     descriptions=descriptions)
        if len(response) > 0:
            r = response[0]
            print("HITId: %s"%r.HITId)
              
    def allhits_liveness(self):
        #allassignments = self.conn.get_assignments(hit_id)
        #first = self.ah.get_submitted_transcriptions(hit_id,str(clipid))

        hits = self.conn.get_all_hits()
        print("CONN: ",self.conn.host)
        for hit in hits:
            hit_id = hit.HITId            
            print("HIT ID: %s"%hit_id)
            assignments = self.conn.get_assignments(hit_id)
            if len(assignments) == 0:
                if raw_input("Remove hit with no submitted assignments?(y/n)") == "y":
                    try:
                        self.conn.disable_hit(hit_id)
                    except MTurkRequestError as e:
                        raise e
            else:
                if raw_input("Remove hit with %s submitted assignments?(y/n)"%len(assignments)) == "y":
                    try:
                        self.conn.disable_hit(hit_id)
                    except MTurkRequestError as e:
                        raise e
                       
def get_elicitation_data():
    fal = FastAndLooseElicitationPipeline("cmupronunciation")
    set_info = {'hit_id': "3R16PJFTS31EY5QL45GSZH8MK6JK4W",
                'set_name' : "0"}
    #fal.approve_submitted_assignments_with_valid_recordings(set_info["hit_id"],set_info['set_name'])
    #fal.load_submitted_assignments_from_mturk(set_info["hit_id"],set_info['set_name'])
    
def run():
    fal = FastAndLooseTranscriptionPipeline("hub4transcription")
    fal.submit_audio_hits()
    #fal.allhits_liveness()
        
if __name__=="__main__":
    run()
