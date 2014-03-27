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

class LineBasedAdapter(object):
    def __init__(self,header,delim,comment):
        self.header = header
        self.delim = delim
        self.comment = comment
        #constraint: expected return, function, value 
        self.constraints = [(False,self.startswith,self.comment)]
        
    def startswith(self,line,value):
        return line.startswith(value)
    
    def endswith(self,line,value):
        return line.startswith(value)
    
    def meets_constraints(self,line):
        for expected, func, value in self.constraints:
            if not func(value) == expected:
                return False
        return True
            
    def get_id_dict(self,lines,id_index=None):
        """Given the index of the indicator
            build a dictionary of that indicator given lines.
            If id_index is None, use the line number as the indicator"""
        d = {}
        if id_index:
            for line in lines:
                if self.meets_constraints(line):
                    pieces = lines.split(self.delim)
                    d[pieces[id_index]] = pieces[:id_index]+pieces[id_index:]
        else:
            for i, line in enumerate(lines):
                if self.meets_constraints(line):
                    pieces = lines.split(self.delim)
                    d[i] = line
        return d