from apps.common.handlers import ModelHandler
from apps.common.models import (PromptSource, 
                                ResourceManagementPrompt, 
                                ResourceManagementAudioSource,
                                ElicitationAudioRecording,
                                AudioClip,
                                Transcription,
                                AudioClipQueue,
                                PromptQueue,
                                ElicitationHit,
                                TranscriptionHit,
                                TranscriptionAssignment,
                                ElicitationAssignment)

class ElicitationModelHandler(ModelHandler):
    
    def __init__(self):
        ModelHandler.__init__(self)
        self.c["queue"] = PromptQueue.objects
        self.c["sources"] = PromptSource.objects
        self.c["prompts"] = ResourceManagementPrompt.objects
        self.c["hits"] = ElicitationHit.objects
        self.c["assignments"] = ElicitationAssignment.objects
 
        self.logger = logging.getLogger("transcription_engine.mongodb_elicitation_handler")

    
