from django.contrib import admin
from apps.elicitation.models import ResourceManagementPrompt, PromptSource
from apps.elicitation.forms import PromptSourceForm, UploadFileForm

from django.contrib import admin
from django.template import RequestContext
from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse

from apps.elicitation import views
#from apps.elicitation.pipelines import ElicitationPipeline
#from apps.transcription.pipelines import TranscriptionPipeline

class PromptInline(admin.TabularInline):
    model = ResourceManagementPrompt

    
class ElicitationAdmin(admin.ModelAdmin):
#     def __init__(self):
#         #self.elicitation_pipeline_handler = ElicitationPipeline()
#         #self.transcription_pipeline_handler = TranscriptionPipeline()
#         pass
    promptsource_template = "elicitation:elicitation/promptsource.html"

# CUSTOMIZE ADMIN URLS HERE    
    def get_urls(self):
        urls = super(ElicitationAdmin,self).get_urls()
        my_urls = patterns('',                           
                           #url(r'^add/$',self.admin_site.admin_view(self.upload_file))                           
                           #url(r'^add/$',self.admin_site.admin_view(self.list))
                           url(r'^add/$',views.pslist)
                           #url(r'^add/$',views.upload_file),                           
                           #(r'^(?P<pk>\w+)/$', self.admin_site.admin_view(self.review)))
                           )
        return my_urls + urls
    
    def upload_file(self,request,args=None,kwargs=None):
        print "HERE"
        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                instance = PromptSourceForm(docfile=request.Files['file'])
                instance.save()
                return HttpResponseRedirect('/admin/')
        else:
            form = UploadFileForm()
        context = {"promptsources" : PromptSource.objects.all(),
                   'form': form}
        #return HttpResponseRedirect(reverse('polls:results', args=(p.id,)))    
        return render_to_response('elicitation/upload_promptsource.html', context,context_instance=RequestContext(request))
        #return render(request,'upload.html', {'form': form})
#         
#     def review(self, request, pk):
#         source = PromptSource.objects.get(pk=pk)
#         return render_to_response(self.promptsource_template,{
#                                                               'title': 'Review prompt source %s' % source.uri,
#                                                               'prompt_source' : source})
        

    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj: # obj is not None, so this is a change page
            kwargs['exclude'] = ['state', 'disk_space',]
        else: # obj is None, so this is an add page
            kwargs['fields'] = ['uri',]
            #kwargs['elicitation_pipeline_handler'] = self.elicitation_pipeline_handler
            #kwargs['transcription_pipeline_handler'] = self.elicitation_pipeline_handler
        return super(ElicitationAdmin, self).get_form(request, obj, **kwargs)
#     list_display = ("Source", "pub_date", "was_published_recently")
#     fieldsets = [
#                  (None, {'fields' : ['question']}),
#                  ('Date Information', {'fields': ['pub_date'], 'classes': ['collapse']})
#                  ]
    inlines = [PromptInline]
    #list_filter = ['pub_date']
    #search_fields = ['question']
        
admin.site.register(PromptSource,ElicitationAdmin)