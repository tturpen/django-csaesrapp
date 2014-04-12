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

from apps.common.handlers import ModelHandler
import logging

class ModelFactory(object):
    def __init__(self):

        self.mh = ModelHandler()    
        self.logger = logging.getLogger("csaesr.apps.common_model_factory")
        
    def create_model(self,collection,search,document,update=True):
        """Check to see if the model exists given search,
            if not, create the model.
            if update, update the model
            The only confusing part here is the ModelHandler holds the 
            Model names in 'c', ie self.mh.c['assignments'](**document)
            creates a new assignment object from the document."""
        model = self.mh.get_model(collection, search)
        if not model:
            model = self.mh.c[collection](**document)
            model.save()
            pk = model.pk
            self.logger.info("Created %s model(%s) "%(collection,pk))
        elif update:
            self.mh.update_model(collection,model,document=document)
        self.mh.update_model_state(collection, model)
        return model       
    
    
    def create_assignment_model(self,assignment,answers,hit_obj,zipcode=None):
        """Create the assignment model with the transcription ids.
            AMTAssignmentStatus is the AMT assignment state.
            state is the engine lifecycle state."""
        assignment_id = assignment.AssignmentId
        document = {"assignment_id":assignment_id,
                     "accept_time": assignment.AcceptTime,
                     "assignment_status" : assignment.AssignmentStatus,
                     "auto_approval_date" : assignment.AutoApprovalTime,
                     "submit_time": assignment.SubmitTime,
                     "hit" : hit_obj,
                     "worker_id" : assignment.WorkerId,
                     "recordings" : answers,}
        if zipcode:
            document["zipcode"] = zipcode
        model = self.create_model("assignments", {"assignment_id": assignment_id},document)        
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
