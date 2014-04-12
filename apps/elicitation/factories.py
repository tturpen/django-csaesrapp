from apps.common.factories import ModelFactory
from apps.elicitation.handlers import ElicitationModelHandler
from apps.audio.handlers import RecordingHandler, WavHandler
import os
import sys


class ElicitationModelFactory(ModelFactory):
    def __init__(self):
        ModelFactory.__init__(self)
        self.mh = ElicitationModelHandler()
        self.rh = RecordingHandler()
        self.wh = WavHandler()
                
    def create_elicitation_hit_model(self,
                                     hit_id,
                                     hit_type_id,
                                     prompt_ids,
                                     prompt_source_name,
                                     template_name,
                                     redundancy):        
        if type(prompt_ids) != list:
            raise IOError
        search = {"hit_id":hit_id}
        document =  {"hit_id":hit_id,
                     "hit_type_id": hit_type_id,
                     "prompts" : prompt_ids,
                     "prompt_source_name": prompt_source_name,
                     "template_name": template_name,
                     "redundancy": redundancy}
        return self.create_model("hits",search,document)
    
    def create_word_prompt_model(self,source, words, normalized_words,line_number,prompt_id,word_count):
        """A -1 endtime means to the end of the clip."""
        search = {"source" : source,
                    "line_number" : line_number,
                    "prompt_id" : prompt_id,
                    "word_count": word_count}
        document = {"source" : source,
                    "line_number" : line_number,
                    "prompt_id" : prompt_id,
                    "words" : words,
                    "normalized_words": normalized_words,
                    "word_count": word_count}
        art_id = self.create_model("prompts", search, document,update=False)
        return art_id
    
    def create_prompt_source_model(self,prompt_file_uri, disk_space, prompt_count):
        """Create the prompt source model give the location on disk,
            size on disk
            and number of prompts"""
        search = {"uri" : prompt_file_uri,
                    "disk_space" : disk_space,
                    "prompt_count": prompt_count}    
        document = {"uri" : prompt_file_uri,
                    "disk_space" : disk_space,
                    "prompt_count": prompt_count} 
        model= self.create_model("prompt_sources", search, document)
        return model
    
    def create_recording_source_model(self,prompt,recording_url,worker=None,prompt_words=None):
        """Use the recording handler to download the recording
            and create the artifact"""
        recording_uri = self.rh.download_vocaroo_recording(recording_url,
                                                           worker_id=worker.worker_id,
                                                           prompt_words=prompt_words)
        if not recording_uri:
            print("Failed to retrieve url(%s)"%recording_url)
            return False
        disk_space = os.stat(recording_uri).st_size
        length_seconds = self.wh.get_audio_length(recording_uri)
        encoding = ".wav"
        sample_rate = -1
        
        search = {"recording_url" : recording_url}
        document = {"recording_url": recording_url,
                    "prompt": prompt,
                    "disk_space" : disk_space,
                    "uri" : recording_uri,
                    "worker_id": worker.worker_id,
                    "length_seconds": length_seconds,
                    "encoding" : encoding,
                    "sample_rate" : sample_rate,
                    "filename": os.path.basename(recording_uri)} 
        return self.create_model("recording_sources", search, document)
    
    