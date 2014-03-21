"""Generic text handlers"""
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

from apps.text.exceptions import DuplicateSentenceIds

class WordSegmentationHandler(object):
    """Segement a sentence into a list of words."""
    def __init__(self,lang):
        self.lang = lang

    def get_word_list(self,sentence):
        if self.lang == "en":
            return sentence.split(" ")
        
class PromptHandler(object):
    def __init__(self):
        pass
    
    def get_prompts(self,prompt_file_uri,comment_char=";"):
        lines = open(prompt_file_uri).readlines()
        result = {}
        for i, line in enumerate(lines):
            if not line.startswith(";"):
                words = line.split(" ")
                sent_id = words[-1].strip().lstrip("(").strip(")")
                if sent_id in result:
                    raise DuplicateSentenceIds
                result[sent_id] = (words[:-1],i)
        return result