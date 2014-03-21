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
from apps.util.handlers import WerHandler
from apps.normalization.handlers import NormalizationHandler

import logging

class StandardFilterHandler(object):
    """The purpose of this class is to block or approve hypothesis transcriptions
        given any number of factors, WER being one of them.""" 
    WER_THRESHOLD = .66
    CER_THRESHOLD = 2
    
    def __init__(self,model_handler):
        self.mh = model_handler

        self.normalizer = NormalizationHandler()
        
        self.logger = logging.getLogger("transcription_engine.filter_standard")   
    
    def get_wer(self,reference,hypothesis):
        return WerHandler.cer_wer(hypothesis,reference)
        
    def cat(self,this,that):
        """If two subsequent words in this are in that,
            concatenate them."""
        for i, word in enumerate(this):
            if i < len(this)-1:
                if this[i] + this[i+1] in that:
                    this[i] = this[i] + this[i+1]
                    this.pop(i+1)
        return this
    
    def get_normalized_list(self,sent):
        """Normalize the sentence."""
        return self.normalizer.standard_normalization(sent)
    
    def approve_transcription(self,reference,hypothesis):
        #Full sentence to normalized list
        reference = self.get_normalized_list(reference)
        hypothesis = self.get_normalized_list(hypothesis)
        
        reference = self.cat(reference,hypothesis)
        hypothesis = self.cat(hypothesis,reference)        
                
        wer = self.get_wer(reference,hypothesis)        
        if wer <= self.WER_THRESHOLD:
            return True, wer
        else:
            return False, wer      
                 
    def approve_assignment(self,transcriptions):
        denied = []
        max_rej_wer = (0.0,0.0)
        total_wer = 0.0
        approved = True
        for transcription in transcriptions:
            #Normalize the transcription
            #self.mh.normalize_transcription
            reference_id = self.mh.get_artifact_by_id("audio_clips",transcription["audio_clip_id"],"reference_transcription_id")
            if reference_id:
                reference_transcription = self.mh.get_artifact("reference_transcriptions",
                                                               {"_id": reference_id},"transcription")
                hypothesis_transcription = transcription["transcription"]
                if reference_transcription:
                    #References are stored as a list of words
                    reference_transcription = " ".join(reference_transcription)
                    approval, wer = self.approve_transcription(reference_transcription,hypothesis_transcription)
                    total_wer += wer
                    if approval:
                        self.mh.update_transcription_state(transcription,"Confirmed")
                        self.logger.info("WER for transcription(%s) %d"%(transcription["transcription"],wer))                       
                    else:
                        denied.append((reference_transcription,hypothesis_transcription))
                        approved = False
                        
        average_wer = total_wer/len(transcriptions)
        return approved, average_wer
            
        

        
        