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
from django.forms import SelectMultiple as SelectMultipleWidget
from django.forms import Select as SelectWidget

import sys

class SetFieldWidget(SelectMultipleWidget):
#     def __init__(self, attrs=None):
#         # create choices for days, months, years
#         # example below, the rest snipped for brevity.
#         if attrs == None:
#             attrs = {'id' : 'fieldid', 'class' : 'setfield', 'label_tag' : 'labeltag'}
#         super(SelectMultipleWidget, self).__init__(attrs=attrs)
        
    def format_output(self,rendered_widgets):
        print "Formatting output for rendered_widgets(%s)" % rendered_widgets
        sys.stdout.flush()
        return u''.join(rendered_widgets)
    
    def decompress(self,value):
        print "Decompressing value(%s)" % value
        sys.stdout.flush()
        if value:
            return [w for w in value]
        else:
            return ["NO VALUE"]

    def value_from_datadict(self, data, files, name):
        print "Value from dict data:%s files:%s name:%s " % (data, files, name)
        sys.stdout.flush()
        piece_list = [
                      widget.value_from_datadict(data, files, name + "_%s" % i)
                      for i, widget in enumerate(self.widgets)
                     ]
        try:
            as_list = list(piece_list)
        except ValueError:
            return 'EMPTY VALUE'
        else:
            return str(as_list)