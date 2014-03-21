"""Specific transcription pipeline handlers"""
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
import datetime
import time

from apps.transcription.models import (ResourceManagementAudioSource,
                                AudioClip,
                                Transcription,
                                AudioClipQueue,
                                TranscriptionHit,
                                TranscriptionAssignment,)

from apps.common.handlers import ModelHandler
import logging
import os

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
        