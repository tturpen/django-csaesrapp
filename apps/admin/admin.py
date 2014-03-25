from django.contrib import admin
from apps.elicitation.models import ResourceManagementPrompt, PromptSource
#from apps.elicitation.pipelines import ElicitationPipeline
#from apps.transcription.pipelines import TranscriptionPipeline

class PromptInline(admin.TabularInline):
    model = ResourceManagementPrompt

    
class CsaesrAdmin(admin.ModelAdmin):
#     def __init__(self):
#         #self.elicitation_pipeline_handler = ElicitationPipeline()
#         #self.transcription_pipeline_handler = TranscriptionPipeline()
#         pass
        
    def get_form(self, request, obj=None, **kwargs):
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj: # obj is not None, so this is a change page
            kwargs['exclude'] = ['state', 'disk_space',]
        else: # obj is None, so this is an add page
            kwargs['fields'] = ['uri',]
            #kwargs['elicitation_pipeline_handler'] = self.elicitation_pipeline_handler
            #kwargs['transcription_pipeline_handler'] = self.elicitation_pipeline_handler
        return super(CsaesrAdmin, self).get_form(request, obj, **kwargs)
#     list_display = ("Source", "pub_date", "was_published_recently")
#     fieldsets = [
#                  (None, {'fields' : ['question']}),
#                  ('Date Information', {'fields': ['pub_date'], 'classes': ['collapse']})
#                  ]
    inlines = [PromptInline]
    #list_filter = ['pub_date']
    #search_fields = ['question']
        
admin.site.register(PromptSource,CsaesrAdmin)