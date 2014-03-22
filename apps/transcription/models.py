"""Models for the transcription App"""
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
from django.db import models
from django.contrib.contenttypes.generic import GenericForeignKey

from apps.common.models import StaticFile, ObjQueue, MturkHit, CsaesrAssignment, AudioSource, StateModel
from apps.normalization.models import NormalizedWords

from djangotoolbox.fields import ListField, SetField


class ResourceManagementAudioSource(AudioSource):
    speaker_id = models.TextField()
    
    
class AudioClip(StaticFile):
    """Audio Clips are portions or the entirety of an audio source
        Option to be web accessible
    """
    #Ideally this would point to a generic Audio Source but I don't know how
    source_id = GenericForeignKey()
    http_url = models.URLField()
    length_seconds = models.TimeField()
    
    
class AudioClipQueue(ObjQueue):
    """A queue of audio clips"""
    name = models.TextField("AudioClips")
        
    
class TranscriptionHit(MturkHit):
    """The specific transcription Hit"""
    audio_clips = ListField(models.ForeignKey(AudioClip))
    
    
class Transcription(StateModel):
    """The generic transcription class"""
    word_count = models.IntegerField()
    normalized_words = models.ForeignKey(NormalizedWords)
    words = ListField(models.TextField())
    raw_text = models.TextField()
    #assignment_id = models.ForeignKey(TranscriptionAssignment)
    audio_clip_id = models.ForeignKey(AudioClip)
    
    
class TranscriptionAssignment(CsaesrAssignment):
    """The specific transcription assignment class"""
    transcriptions = SetField(models.ForeignKey(Transcription))
    hit_id = models.ForeignKey(TranscriptionHit)
    
class Worker(StateModel):
    """The elicitation worker model.
        It was either have a different worker for elicitation and transcription
        or the same (common) worker and not know what assignments they submitted
        because each assignment and hit is different for transcription and elicitation.
        TODO-tt: Figure out how to have a SetField(GenericForeignKey), that would fix this
    """
    worker_id = models.TextField()
    approved_transcription_assignments = SetField(models.ForeignKey(TranscriptionAssignment))
    denied_transcription_assignments = SetField(models.ForeignKey(TranscriptionAssignment))
    submitted_transcription_assignments = SetField(models.ForeignKey(TranscriptionAssignment))
    