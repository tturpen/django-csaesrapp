"""Define the statemap functions here"""
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
import datetime
class ElicitationStateMap(object):
    """The idea for the statemap is to provide a list of boolean functions that can be called
         on a model.
         The last function that returns True is the model state.
         Or else it is "New"
    """ 
    
    def __init__(self):
        self.state_map = {"prompt_sources": [PromptSource,PromptSource().map],
                      "prompts": [Prompt,Prompt().map],
                      "hits": [ElicitationHit,ElicitationHit().map],
                      "recording_sources" : [RecordingSource, RecordingSource().map],
                      "assignments" : [ElicitationAssignment,ElicitationAssignment().map],
                      "workers" : [Worker, Worker().map]
                      }
             
class Comparisons(object):
    def __init__(self):
        self.map = []
        
    def greater_than_zero(self,parameter,model):
        if hasattr(model,parameter):
            attribute = getattr(model,parameter)
            if type(attribute) == list:
                return len(attribute) > 0
            elif type(attribute) == int:
                return attribute > 0   
        return False     
    
    def equal_to_zero(self,parameter,model):
        return hasattr(model,parameter) and len(getattr(model,parameter)) == 0
    
    def alpha_numeric(self,parameter,model):
        return hasattr(model,parameter) and getattr(model,parameter).isalnum()
    
    def before_now(self,parameter,model):
        return hasattr(model,parameter) and getattr(model,parameter) < datetime.datetime.now()
  
#For all classes, order of the state map matters. For the first function that fails
#The previous function's value with be taken  
class PromptSource(Comparisons):
    def __init__(self):
        self.map = ["Listed"]
        
    def Listed(self,model):
        return self.greater_than_zero("prompt_count", model)
    
    
class RecordingSource(Comparisons):
    def __init__(self):
        self.map = ["Clipped"]
        
    def Clipped(self,model):
        return self.greater_than_zero("clips", model)

            
class Prompt(Comparisons):
    def __init__(self):
        self.map = ["Queued","Hit","Recorded"]
        
    def Queued(self,model):
        return self.greater_than_zero("inqueue", model)
        
    def Hit(self,model):
        return self.alpha_numeric("hit_id", model) and\
             self.greater_than_zero("hit_id", model)
             
    def Recorded(self,model):
        return self.greater_than_zero("recording_sources", model)
             
class ElicitationHit(Comparisons):
    def __init__(self):
        self.map = ["Submitted"]
        
    def Submitted(self,model):
        return self.greater_than_zero("submitted_assignments", model)
    
    
class ElicitationAssignment(Comparisons):
    def __init__(self):
        self.map = ["Submitted","Approved"]
        
    def Approved(self,model):
        return self.before_now("approval_time",model)
    
    def Submitted(self,model):
        return self.greater_than_zero("recordings",model)
    
class Worker(Comparisons):
    def __init__(self):
        self.map = ["Submitted","Approved","Denied","Blocked"]
        
    def Submitted(self,model):
        return self.greater_than_zero("submitted_assignments",model)
        
    def Approved(self,model):
        return self.greater_than_zero("approved_elicitation_assignments",model)
    
    def Denied(self,model):
        return self.greater_than_zero("denied_elicitation_assignments",model)
    
    def Blocked(self,model):
        return self.greater_than_zero("blocked_elicitation_assignments",model)