from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from apps.admin import urls as adminurls
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'csaesrapp.views.home', name='home'),
    # url(r'^csaesrapp/', include('csaesrapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(adminurls)),
    #url(r'^admin/elicitation/', include('apps.elicitation',namespace="elicitation"))
    #url(r'^admin/', 'apps.admin'),
)
