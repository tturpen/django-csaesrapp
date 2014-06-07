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

from apps.util.handlers import WerHandler
import shutil

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
        
    def approve_submitted_assignments_with_valid_recordings(self,
                                                            hit_id,
                                                            sequential_set_name,
                                                            dump_base=None):
        """Approve those assignments with some recording."""                             
        hit_dir = os.path.join(self.base_fal_elicitation_hit_dir,hit_id)
        dump_dir = os.path.join(dump_base,hit_id)
        try:
            os.makedirs(dump_dir)
        except Exception:
            pass
        for assignment in os.listdir(hit_dir):
            assignment_dir = os.path.join(hit_dir,assignment)
            if os.path.isdir(assignment_dir):
                recordings_dir = os.path.join(assignment_dir,self.recordings_tag)
                worker_recordings = []
                for recording in os.listdir(recordings_dir):
                    recording_path = os.path.join(recordings_dir,recording)
                    if not self.sox_handler.get_wav_audio_length(recording_path) > 0:
                        break
                    worker_recordings.append(recording_path)
                else:
                    try:
                        if dump_dir:
                            
                            for recording in worker_recordings:
                                fname = os.path.basename(recording)
                                shutil.copy(recording,os.path.join(dump_dir,fname))
                        self.conn.approve_assignment(assignment)
                    except MTurkRequestError:
                        pass

class FastAndLooseTranscriptionPipeline(MturkPipeline):
    
    def __init__(self,task_name):
        MturkPipeline.__init__(self)
        self.mh = ElicitationModelHandler()
        self.mf = ElicitationModelFactory()
        self.logger = logging.getLogger("csaesr_app.fal_trasncription_pipeline_handler")
        self.clips_tag = "recordings"
        self.NOT_PULLED_TAG = "NOT_PULLED"
        self.clip_dir = "/home/taylor/data/speech/spanish_hub4/spanish_hub4_excerpted/subset/"
        self.base_fal_transcription_hit_dir = os.path.join(settings.FAL_BASE_DIR,
                                                                "transcription",
                                                                task_name,
                                                                "hits")
        self.spanish_hub4_base_url = "http://www.cis.upenn.edu/~tturpen/wavs/hub4/subset/"
        self.transcriptions_tag = "transcriptions"
        
    def get_reference_transcriptions(self,d,clean=True,disfls=["{breath}"]):
        refs = {}
        for tr_fname in os.listdir(d):
            tr = open(os.path.join(d,tr_fname),'r').readlines()[0].strip()
            if clean:
                for disfl in disfls:
                    tr = tr.replace(disfl + " ","").replace(disfl,"")
                #tr = tr.decode("utf-8")
            refs[tr_fname.strip(".txt")] = tr
        return refs
    
    def get_stats(self,basedir,hit_id,ref_transcription_dir):
        worker_tdic = self.get_worker_transcriptions(basedir,hit_id)
        refs = self.get_reference_transcriptions(ref_transcription_dir)
        wer = WerHandler()
        all_wer = []
        alls_wer = []
        for worker in worker_tdic:
            transcriptions = worker_tdic[worker]
            for ref_wav, text in transcriptions:
                ref_name = ref_wav.strip(".wav")
                text = text.replace("\t"," ").strip()
                if not ref_name in refs:
                    print "Wav(%s) with unknown reference transcription" % ref_wav
                else:
                    ref = refs[ref_name].split(" ")
                    words = text.split(" ")
                    twer = 0.0 + wer.cer_wer(words,ref)
                    stwer = 0.0 + wer.cer_wer(words,ref,min_char_df=0)

                    all_wer.append(twer)
                    alls_wer.append(stwer)
                    print worker + "\t" + ref_name + "\t" + str(twer) + "\t" + text
                    
        print "Average soft WER: %s" % (sum(all_wer)/len(all_wer))
        print "Average strict WER: %s" % (sum(alls_wer)/len(alls_wer))


            
    def get_worker_transcriptions(self,basedir,hit_id):
        d = os.path.join(basedir,hit_id)
        transcriptions_tag = "transcriptions"
        transcriptions = {}#by worker
        for adir in os.listdir(d):
            tdir = os.path.join(d,adir,transcriptions_tag)
            if not os.path.isdir(tdir):
                raise Exception("AssignmentDir(%s) has no transcriptions"% adir)
            tfiles = os.listdir(tdir)
            for tfile in tfiles:
                worker_id, data = tfile.split("_")
                lines = open(os.path.join(tdir,tfile),'r').readlines()
                wav_and_tran_pairs = [line.split("\t") for line in lines]
                if worker_id in transcriptions:
                    transcriptions[worker_id].extend(wav_and_tran_pairs)
                else:
                    transcriptions[worker_id] = wav_and_tran_pairs
        return transcriptions
                    
    def have_assignment(self,assignment_dir):
        if os.path.isdir(assignment_dir):
            return "OK"
        return self.NOT_PULLED_TAG
        
    def get_audio_clip_pairs(self,base_dir,base_url,clip_count=None,encoding=".wav"):
        """Get audio clips from a directory and return their ids along with urls."""
        pairs = []
        if clip_count:
            for f in os.listdir(base_dir)[:clip_count+1]:
                pairs.append((base_url+f,f.strip(encoding)))
        else:
            for f in os.listdir(base_dir):
                pairs.append((base_url+f,f.strip(encoding)))
            
        return pairs
    
    def get_transcriptions(self,hit_id,OVERWRITE=True):
        aws_id = os.environ['AWS_ACCESS_KEY_ID']
        aws_k = os.environ['AWS_ACCESS_KEY']
                
        try:
            conn = MTurkConnection(aws_access_key_id=aws_id,\
                          aws_secret_access_key=aws_k,\
                          host=settings.MTURK_HOST)
            print "Connection HOST: %s" % settings.MTURK_HOST
        except Exception as e:
            print(e)        
        assignments = self.conn.get_assignments(hit_id,page_size=100)
        have_all_assignments = True
        assignment_ids = []
        assignment_count = 0
        sys.stdout.flush()
        hit_dir = os.path.join(self.base_fal_transcription_hit_dir,hit_id)
        for assignment in assignments:
            assignment_count += 1
            assignment_id = assignment.AssignmentId
            assignment_dir = os.path.join(hit_dir,assignment_id)
            assignment_ids.append(assignment_id)  
            assignment_status = self.have_assignment(assignment_dir)
            worker_id = assignment.WorkerId
            if assignment_status == self.NOT_PULLED_TAG or OVERWRITE:
                transcriptions_dir = os.path.join(assignment_dir,self.transcriptions_tag)
                try:
                    os.makedirs(transcriptions_dir)
                except Exception:
                    #path exists
                    pass
                recording_ids = []                
                wav_id_tag = "wav_fname"
                transcription_tag = "transcription_text"
                worker_id_tag = "worker_id"
                transcription_dict = self.ah.get_assignment_submitted_text_dict(assignment,wav_id_tag,transcription_tag)
                print("Trying to get transcription_dict(%s)"%transcription_dict)
                sys.stdout.flush()
                pairs = []
                for transcription in transcription_dict:
                    text = transcription[transcription_tag]
                    wav_fname = transcription[wav_id_tag]
                    #prompt = self.mf..get_fal_prompt("prompts",prompt_obj_id)
                    if not wav_fname: 
                        self.logger.info("Assignment(%s) with unknown %s(%s) skipped"%\
                                    (assignment_id,wav_id_tag,wav_fname))
                        break
                    pairs.append((wav_fname,text))
                    sys.stdout.flush()
                else:
                    fname = os.path.join(transcriptions_dir,worker_id + '_transcriptions')
                    open(fname,'w').write("\n".join(["\t".join(p) for p in pairs]))
                    pass
        
        
                    #prompt_words = self.mh.get_normalized_prompt_words(prompt)

    
    def submit_audio_hits(self):
        aws_id = os.environ['AWS_ACCESS_KEY_ID']
        aws_k = os.environ['AWS_ACCESS_KEY']
                
        try:
            conn = MTurkConnection(aws_access_key_id=aws_id,\
                          aws_secret_access_key=aws_k,\
                          host=settings.MTURK_HOST)
            print "Connection HOST: %s" % settings.MTURK_HOST
        except Exception as e:
            print(e) 
        page_size = 10.0
        clip_dir = "/home/taylor/data/speech/spanish_hub4/spanish_hub4_excerpted/subset/"
        hh = HitHandler(conn)
        hit_title = "Spanish Audio Transcription"
        question_title = "Write the Spanish words that are said in this clip." 
        keywords = "audio, transcription, Spanish, speech, recording"
        hit_description = "Write the Spanish words that are said."
        max_assignments = 2
        reward_per_clip = .02
        duration = 60*50
        one_month = timedelta(40)
        descriptions = ["The following audio clips are in Spanish.",
                        "Transcribe the audio clips by typing the words IN SPANISH.",
                        "Do not use abbreviations.",
                        "Do not translate.",
                        "Write numbers long-form, as in: 'ocho' NOT '8'.",
                        "Punctuation does not matter.",
                        "Hotkeys: press TAB to play the next clip."]
        audio_clip_tups = self.get_audio_clip_pairs(clip_dir,self.spanish_hub4_base_url)
        page_count = len(audio_clip_tups)/page_size
        print audio_clip_tups
        create_hits = raw_input("%s pages of %s clips for HOST: %s, est cost: %s create?(y/n)"\
                                % (page_count,len(audio_clip_tups),settings.MTURK_HOST,reward_per_clip * page_size * page_count * max_assignments))
        if create_hits == "y":
            q = []
            for audio_clip_tup in audio_clip_tups:
                if len(q) == page_size:
                    response = hh.make_html_spanish_transcription_HIT(q, 
                                                     hit_title, 
                                                     question_title, 
                                                     keywords=keywords,
                                                     duration=duration,
                                                     hit_description=hit_description,
                                                     max_assignments=max_assignments,
                                                     reward_per_clip=reward_per_clip,
                                                     lifetime=one_month,
                                                     descriptions=descriptions)                    
                    if response and len(response) > 0:
                        r = response[0]
                        print("HITId: %s"%r.HITId)
                        q = []
                else:
                    q.append(audio_clip_tup)
                if len(q) == page_size:
                    response = hh.make_html_spanish_transcription_HIT(q, 
                                                     hit_title, 
                                                     question_title, 
                                                     keywords=keywords,
                                                     duration=duration,
                                                     hit_description=hit_description,
                                                     max_assignments=max_assignments,
                                                     reward_per_clip=reward_per_clip,
                                                     lifetime=one_month,
                                                     descriptions=descriptions)                    
                    if response and len(response) > 0:
                        r = response[0]
                        print("HITId: %s"%r.HITId)
                        q = []
              
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
    set_info = {'hit_id': "3MZ3TAMYTLXUTG2VFERTUU4JKOTIRX",
                'set_name' : "3",
                'dump_dir' : '/home/taylor/data/csaesr/fal/elicitation/cmupronunciation/nonzerorecordings'}
    fal.approve_submitted_assignments_with_valid_recordings(set_info["hit_id"],
                                                            set_info['set_name'],
                                                            dump_base=set_info['dump_dir'])
    #fal.load_submitted_assignments_from_mturk(set_info["hit_id"],set_info['set_name'])
    
def do_transcription():
    fal = FastAndLooseTranscriptionPipeline("hub4transcription")
    hit_id = "3SCKNODZ0XQCPYT73G6FUL905B9N7Z"
    transcription_basedir = "/home/taylor/data/csaesr/fal/transcription/hub4transcription/hits/"
    ref_transcription_dir = "/home/taylor/data/speech/spanish_hub4/spanish_hub4_excerpted/trs"
    #fal.submit_audio_hits()
    #fal.allhits_liveness()
    #fal.get_transcriptions(hit_id)
    fal.get_stats(transcription_basedir,hit_id,ref_transcription_dir)
        
if __name__=="__main__":
    #run()
    #get_elicitation_data()
    do_transcription()
    pass
