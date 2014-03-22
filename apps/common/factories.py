from apps.common.handlers import ModelHandler
import logging

class ModelFactory(object):
    def __init__(self):
        self.mh = ModelHandler()    
        self.logger = logging.getLogger("csaesr.apps.common_model_factory")
        
    def create_model(self,collection,search,document,update=True):
        """Check to see if the model exists given search,
            if not, create the model.
            if update, update the model"""
        model = self.mh.get_model(collection, search)
        if not model:
            model = self.mh.c[collection](**document)
            model.save()
            pk = model.pk
            self.logger.info("Created %s model(%s) "%(collection,pk))
        elif update:
            self.mh.update_model(model,document)
            pk = model.pk
        #self.update_model_state(collection, art_id)
        return model       
    
    
    def create_assignment_model(self,assignment,answers):
        """Create the assignment model with the transcription ids.
            AMTAssignmentStatus is the AMT assignment state.
            state is the engine lifecycle state."""
        assignment_id = assignment.AssignmentId
        document = {"assignment_id":assignment_id,
                     "AcceptTime": assignment.AcceptTime,
                     "AMTAssignmentStatus" : assignment.AssignmentStatus,
                     "AutoApprovalTime" : assignment.AutoApprovalTime,
                     "hit_id" : assignment.HITId,
                     "worker_id" : assignment.WorkerId,
                     "recordings" : answers}
        model = self.create_model("elicitation_assignments", {"assignment_id": assignment_id},document)        
        return model

        
    def create_worker_model(self,worker_id):
        document = {"worker_id": worker_id}
        model = self.create_model("workers",{"worker_id": worker_id},document)
        return model
    

    
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
