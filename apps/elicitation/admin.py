from django.contrib import admin
from apps.elicitation.models import ResourceManagementPrompt, PromptSource, ElicitationHit, PromptQueue, ElicitationAssignment 
from apps.elicitation.forms import PromptSourceForm, UploadFileForm, RMPromptForm
from apps.elicitation import views
from apps.elicitation.pipelines import ElicitationPipeline
from apps.elicitation.handlers import ElicitationModelHandler
from apps.elicitation.widgets import WordListEditorWidget, SetFieldWidget

from apps.common.fields import CseasrListField
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

from djangotoolbox.fields import SetField

import os

class PromptInline(admin.TabularInline):
    model = ResourceManagementPrompt
    
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["hit"]
    formfield_overrides = {
                           SetField : {'widget' : SetFieldWidget}
                           }
    
    
class QueueAdmin(admin.ModelAdmin):
    fieldsets = [
                 (None, {'fields': ['name']})
                 ]
    list_display = ["name"]
    

class HitAdmin(admin.ModelAdmin):
    pipeline = ElicitationPipeline()
    actions = ['remove_hit_from_mturk','get_hit_submitted_assignments']
    list_display = ["template_name","prompt_source_name","hit_id","hit_type_id","prompt_count","redundancy"]
    def remove_hit_from_mturk(self,request, queryset):        
        for hit_model in queryset:
            self.pipeline.remove_hit_from_mturk(hit_model)
            
    def get_hit_submitted_assignments(self,request, queryset):
        for hit in queryset:
            self.pipeline.load_submitted_assignments_from_mturk(hit)
            
    def prompt_count(self,obj):
        return len(obj.prompts)
            
    remove_hit_from_mturk.short_description = "Remove the hit from mturk"
            

class PromptAdmin(admin.ModelAdmin):
    form = RMPromptForm
    
class PromptSourceAdmin(admin.ModelAdmin):
    pipeline = ElicitationPipeline()    
    actions = ['create_hit_from_source','create_hit_from_partial_queue']
    fieldsets = [
                 (None, {'fields' : ['sourcefile']}),
                 ('Source File Information', {'fields': ['uri'], 'classes': ['collapse']})
                 ]
    list_display = ["sourcefile","uri","disk_space","state"]
    form = PromptSourceForm
    formfield_overrides = {
                           CseasrListField : {'widget' : WordListEditorWidget}
                           }
        #self.transcription_pipeline_handler = TranscriptionPipeline()        
        #promptsource_template = "elicitation:elicitation/promptsource.html"
        
        # CUSTOMIZE ADMIN URLS HERE    
    def get_urls(self):
        urls = super(PromptSourceAdmin,self).get_urls()
        my_urls = patterns('',                           
                           #url(r'^add/$',self.admin_site.admin_view(self.upload_file))                           
                           #url(r'^add/$',self.admin_site.admin_view(self.list))
                           url(r'^add/$',views.pslist),
                           #url(r'^(?P<pk>\w+)/$',views.prompt_source_view),
                           url(r'^promptsource/$',views.IndexView),
                           url(r'^(?P<pk>\w+)/load/$',self.load_promptsource),
                           #url(r'^add/$',views.upload_file),                           
                           #(r'^(?P<pk>\w+)/$', self.admin_site.admin_view(self.review)))
                           )
        return my_urls + urls

    def create_hit_from_partial_queue(self, request, queryset):
        """Check if the queue is full given the prompt_source"""
        if len(queryset) > 1:
            return
        prompt_source = list(queryset[:1])
        prompt_source = prompt_source[0]
        qname = prompt_source.uri
        self.pipeline.create_hit_from_partial_queue(prompt_source,qname,8)
        
    def create_hit_from_source(self, request, queryset):
        """Take a prompt source and create desired HITs."""
        if len(queryset) > 1:
            return
        prompt_source = list(queryset[:1])
        prompt_source = prompt_source[0]
        qname = prompt_source.uri
        if prompt_source:
            self.pipeline.create_hits_from_promptsource(prompt_source,qname)        
        
    create_hit_from_source.short_description = "Create most hits possible from promptsource"    
    
    
    def changelist_view(self, request, extra_context=None):        
        return super(PromptSourceAdmin,self).changelist_view(request,extra_context)
    
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
        return super(PromptSourceAdmin, self).get_form(request, obj, **kwargs)
#     list_display = ("Source", "pub_date", "was_published_recently")
#     fieldsets = [
#                  (None, {'fields' : ['question']}),
#                  ('Date Information', {'fields': ['pub_date'], 'classes': ['collapse']})
#                  ]
    inlines = [PromptInline]
    #list_filter = ['pub_date']
    #search_fields = ['question']

    
admin.site.register(PromptSource,PromptSourceAdmin)
admin.site.register(ElicitationHit,HitAdmin)
admin.site.register(PromptQueue,QueueAdmin)
admin.site.register(ResourceManagementPrompt,PromptAdmin)
admin.site.register(ElicitationAssignment,AssignmentAdmin)