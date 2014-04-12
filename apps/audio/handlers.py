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

from subprocess import call, check_output, CalledProcessError
from apps.audio.exceptions import WavHandlerException, DuplicateSentenceIds
from django.conf import settings
import os
import urllib2
from urllib2 import URLError

class WavHandler(object):
    """This class is for handling wav encoded files.""" 
    DEFAULT_SAMPLE_RATE = 16000
    SPH2PIPE_SYS_BINARY = settings.SPH2PIPE_BINARY

    def __init__(self):
        self.sox_handler = SoxHandler()
        
    def sph_to_wav(self,system_uri,wav_dir=None,out_uri=None):
        """Given an sph encoded audio file, convert it to wav."""
        if not wav_dir:
            wav_dir = os.path.dirname(system_uri)
        if not out_uri:
            out_uri = system_uri.strip(".sph") + ".wav"
            out_uri = os.path.basename(out_uri)
            out_uri = os.path.join(wav_dir,(out_uri))
        out_file = open(out_uri,"w")
        try:
            call([self.SPH2PIPE_SYS_BINARY,"-f", "wav",system_uri],stdout=out_file)
        except Exception:
            raise WavHandlerException
        out_file.close()
        
    def get_audio_length(self,system_uri,encoding=".wav"):
        if(encoding == ".wav"):
            return self.sox_handler.get_wav_audio_length(system_uri)
        
        
class SoxHandler(object):
    """This class is an interface to the Sox audio file handler"""
    SOXI_BINARY = "soxi"
    def get_wav_audio_length(self,system_uri):
        try:
            length = float(check_output([self.SOXI_BINARY,"-D",system_uri]))
            return length
        except CalledProcessError:
            return -1
        
    
class RecordingHandler(object):
    """Get files of recordings from urls"""
    def __init__(self):
        self.wav_base_url = "http://vocaroo.com/media_command.php?media=RECORDING_ID&command=download_wav"
        self.record_id_tag = "RECORDING_ID"
        self.recording_basedir = settings.RECORDING_DIR
        
    def download_vocaroo_recording(self,url,type="wav",worker_id=None,prompt_words=None):
        if type=="wav":
            remote_file_id = os.path.basename(url)
            download_url = self.wav_base_url.replace(self.record_id_tag,remote_file_id)
            download_url = download_url.replace(" ","")
            dest = os.path.join(self.recording_basedir,
                                os.path.basename(url)+\
                                "_"+worker_id+\
                                "_"+"_".join(prompt_words)+".wav")
            if not os.path.exists(dest):
                try:
                    response = urllib2.urlopen(download_url).read()
                    open(dest,"w").write(response)
                except URLError:
                    open("incorrectURLs.csv","a").write(worker_id+","+url+","+dest+","+prompt_words+"\n")
                    return False        
            return dest
