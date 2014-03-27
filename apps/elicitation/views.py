from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render
from django.views.generic import ListView

from apps.elicitation.models import PromptSource
from apps.elicitation.forms import PromptSourceForm, UploadFileForm

#from apps.elicitation.pipelines.ElicitationPipeline import raw

class IndexView(ListView):
    template_name = 'elicitation/index.html'
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

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = PromptSourceForm(docfile=request.Files['file'])
            instance.save()
            return HttpResponseRedirect('/admin/')
    else:
        form = UploadFileForm()
    return render(request,'elicitation/upload_promptsource.html', {'form': form})

def pslist(request):
    # Handle file upload
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            #newsource = PromptSourceForm(sourcefile = request.FILES['sourcefile'])
            ps = PromptSource(sourcefile=request.FILES['sourcefile'],
                              disk_space=-1,
                              uri="-1",
                              prompt_count=-1)
            ps.save()
            # Redirect to the document list after POST
            #return HttpResponseRedirect(reverse('admin:apps.elicitation.views.pslist'))
            #return HttpResponseRedirect(reverse('admin:index',kwargs={}))
            return HttpResponseRedirect('/admin/elicitation/promptsource/%s/load/'%ps.pk)

    else:
        form = UploadFileForm() # A empty, unbound form

    # Load documents for the list page
    context = {"promptsources" : PromptSource.objects.all(),
               'form': form}
    # Render list page with the documents and the form
#     return render(request,
#         'elicitation/upload_promptsource.html',context,
#         #current_app="apps.elicitation",
#     )
    return render_to_response('elicitation/upload_promptsource.html',
                              context,
                              context_instance=RequestContext(request))
