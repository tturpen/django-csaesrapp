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

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404
from polls.models import Poll, Choice
from django.views import generic

#Data list view with iframe for hit below
#def datalistview(request):

def hit(request):
    #p = Poll.objects.get()
    #p = Poll.objects.filter(pub_date__year="2014")
    this_year = datetime.datetime.now().year
    this_years_polls = Poll.objects.filter(pub_date__year=this_year)
    template = loader.get_template('polls/index.html')
    context = RequestContext(request, {
                                       'latest_poll_list': this_years_polls
                                       })
    #return HttpResponse(template.render(context))
    return render(request,'polls/index.html',context)