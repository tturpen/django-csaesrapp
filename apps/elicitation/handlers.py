from apps.common.handlers import ModelHandler
from apps.common.models import PromptSource
from apps.mturk.handlers import AssignmentHandler, TurkerHandler, HitHandler
from apps.elicitation.models import (ResourceManagementPrompt, 
                                    ElicitationAudioRecording,
                                    PromptQueue,
                                    ElicitationHit,
                                    ElicitationAssignment)
from apps.common.handlers import PipelineHandler
from apps.text.handlers import PromptHandler
from apps.normalization.handlers import NormalizationHandler
from apps.filtering.handlers import StandardFilterHandler

import logging

class ElicitationModelHandler(ModelHandler):
    
    def __init__(self):
        ModelHandler.__init__(self)
        self.c["queue"] = PromptQueue.objects
        self.c["sources"] = PromptSource.objects
        self.c["prompts"] = ResourceManagementPrompt.objects
        self.c["hits"] = ElicitationHit.objects
        self.c["assignments"] = ElicitationAssignment.objects
 
        self.logger = logging.getLogger("transcription_engine.mongodb_elicitation_handler")
        

class ElicitationPipelineHandler(PipelineHandler):
    
    def __init__(self):
        PipelineHandler.__init__(self)
        self.mh = ElicitationModelHandler()
        self.ph = PromptHandler()
        self.filter = StandardFilterHandler(self.mh)
        self.logger = logging.getLogger("transcription_engine.elicitation_pipeline_handler")

    
