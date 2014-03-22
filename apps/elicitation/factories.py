from apps.common.factories import ModelFactory
from apps.elicitation.handlers import ElicitationModelHandler
       
class ElicitationModelFactory(ModelFactory):
    def __init__(self):
        ModelFactory.__init__(self)
        self.mh = ElicitationModelHandler()
                
    def create_elicitation_hit_model(self,hit_id,hit_type_id,prompt_ids):        
        if type(prompt_ids) != list:
            raise IOError
        document =  {"hit_id":hit_id,
                     "hit_type_id": hit_type_id,
                     "prompts" : prompt_ids}
        return self.create_model("elicitation_hits",document)
    
    def create_word_prompt_model(self,source, words, normalized_words,line_number,rm_prompt_id,word_count):
        """A -1 endtime means to the end of the clip."""
        search = {"source" : source,
                    "line_number" : line_number,
                    "rm_prompt_id" : rm_prompt_id,
                    "word_count": word_count}
        document = {"source" : source,
                    "line_number" : line_number,
                    "rm_prompt_id" : rm_prompt_id,
                    "words" : words,
                    "normalized_words": normalized_words,
                    "word_count": word_count}
        art_id = self.create_model("prompts", search, document)
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