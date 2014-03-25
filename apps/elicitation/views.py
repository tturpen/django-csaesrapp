from django.views.generic import ListView
from apps.elicitation.models import PromptSource

from django.template import RequestContext

from django.shortcuts import render

class IndexView(ListView):
    template_name = 'apps/index.html'
    context_object_name = 'prompt_source_list'
    
    def get_queryset(self):
        """Return the five most recent published polls."""
        return PromptSource.objects.all()
    
def index(request):
    prompt_source_list = PromptSource.objects.all()
    context = RequestContext(request, {
                                       'prompt_source_list': prompt_source_list
                                       })
    #return HttpResponse(template.render(context))
    return render(request,'elicitation/index.html',context)
#class PromptSourceView(ListView):
    