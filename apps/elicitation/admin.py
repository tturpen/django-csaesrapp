from django.contrib import admin
from apps.elicitation.models import ResourceManagementPrompt, PromptSource
from apps.elicitation.forms import PromptSourceForm, UploadFileForm
from apps.elicitation import views
from apps.elicitation.pipelines import ElicitationPipeline
from apps.elicitation.handlers import ElicitationModelHandler
#from apps.transcription.pipelines import TranscriptionPipeline


from django.contrib import admin
from django.template import RequestContext
from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

import os

class PromptInline(admin.TabularInline):
    model = ResourceManagementPrompt

    
class ElicitationAdmin(admin.ModelAdmin):
    pipeline = ElicitationPipeline()
    
    fieldsets = [
                 (None, {'fields' : ['sourcefile']}),
                 ('Source File Information', {'fields': ['uri'], 'classes': ['collapse']})
                 ]
    list_display = ["sourcefile","uri","disk_space","state"]
        #self.transcription_pipeline_handler = TranscriptionPipeline()        
        #promptsource_template = "elicitation:elicitation/promptsource.html"

# CUSTOMIZE ADMIN URLS HERE    
    def get_urls(self):
        urls = super(ElicitationAdmin,self).get_urls()
        my_urls = patterns('',                           
                           #url(r'^add/$',self.admin_site.admin_view(self.upload_file))                           
                           #url(r'^add/$',self.admin_site.admin_view(self.list))
                           url(r'^add/$',views.pslist),
                           url(r'^promptsource/$',views.IndexView),
                           url(r'^(?P<pk>\w+)/load/$',self.load_promptsource),
                           #url(r'^add/$',views.upload_file),                           
                           #(r'^(?P<pk>\w+)/$', self.admin_site.admin_view(self.review)))
                           )
        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        return super(ElicitationAdmin,self).changelist_view(request,extra_context)
    
    def load_promptsource(self,*args,**kwargs):
        if "pk" in kwargs:
            pk = str(kwargs["pk"])
        else:
            #Todo delete the model if load fails
            return HttpResponseRedirect('/admin/elicitation/promptsource/%s/loadfail/'%pk)
        
        try:
            ps = get_object_or_404(PromptSource,pk=pk)
            self.pipeline.load_PromptSource_RawToList(ps)
            #dont circumvent the model handler
            #admin should only have access to the pipeline eos
        except Exception:            
            raise
            return HttpResponseRedirect('/admin/elicitation/promptsource/%s/loadfail/'%pk)
            
        return HttpResponseRedirect('/admin/elicitation/promptsource/')
            

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