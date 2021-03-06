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
from apps.common.adapters import LineBasedAdapter

class ResourceManagementAdapter(LineBasedAdapter):
    def __init__(self):
        header = ""
        delim = " "
        comment = ";"        
        LineBasedAdapter.__init__(self,header,delim,comment,-1)
        self.id_proc = self.strip_parens
        
    def strip_parens(self,word):
        return word.strip().lstrip("(").strip(")")

        
class CMUPronunciationAdapter(LineBasedAdapter):
    """An adapter for the CMU Pronunciation dictionary"""
    def __init__(self,wordlist_file=None):
        header = ""
        delim = " "
        comment = ";;;"
        if wordlist_file:
            wordlist = open(wordlist_file).read().split("\n")
            wordlist = [w.strip() for w in wordlist]
            LineBasedAdapter.__init__(self, header, delim, comment,0,wordlist)
        else:
            LineBasedAdapter.__init__(self, header, delim, comment,0)
        self.constraints.extend([(False,self.endswith,"(1)"),
                                 (False,self.endswith,"(2)"),
                                 (False,self.endswith,"(3)"),
                                 (False,self.endswith,"(4)"),
                                 (False,self.endswith,"(5)"),
                                  ])
    
    def post_proc_id_dict(self,d):
        for key in d:
            d[key] = (d[key][0][1:], d[key][1])
        return d
        
    def get_prompt_id_from_assignment_answer_id(self,assignment_answer_id):
        if assignment_answer_id.count("0") == len(assignment_answer_id):
            #If there is only one recording, the number of zeros is the prompt id
            return len(assignment_answer_id) - 1
        return assignment_answer_id.lstrip("0")
        