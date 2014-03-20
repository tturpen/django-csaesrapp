from django.contrib import admin
from apps.common.models import PromptSource, Prompt

class PromptInline(admin.TabularInline):
    model = Prompt

    
class CsaesrAdmin(admin.ModelAdmin):
    list_display = ("Source", "pub_date", "was_published_recently")
    fieldsets = [
                 (None, {'fields' : ['question']}),
                 ('Date Information', {'fields': ['pub_date'], 'classes': ['collapse']})
                 ]
    inlines = [PromptInline]
    #list_filter = ['pub_date']
    #search_fields = ['question']
        
admin.site.register(PromptSource)