from apps.transcription.models import (ResourceManagementAudioSource,
                                AudioClip,
                                Transcription,
                                AudioClipQueue,
                                TranscriptionHit,
                                TranscriptionAssignment,)

from apps.common.handlers import ModelHandler
import logging

class TranscriptionModelHandler(ModelHandler):
    
    def __init__(self):
        ModelHandler.__init__(self)
        self.c["queue"] = AudioClipQueue.objects
        self.c["sources"] = ResourceManagementAudioSource.objects
        #Each question in a HIT has a prompt, even if it is an audio prompt
        self.c["prompts"] = AudioClip.objects
        self.c["answers"] = Transcription.objects
        self.c["hits"] = TranscriptionHit.objects
        self.c["assignments"] = TranscriptionAssignment.objects
 
        self.logger = logging.getLogger("csaesr.%s"%self.__name__)
        
        