from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from django.conf.urls.static import static
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'csaesrapp.views.home', name='home'),
    # url(r'^csaesrapp/', include('csaesrapp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/$',include(admin.site.urls)),
    url(r'^admin/',include(admin.site.urls)),   
    url(r'^elicitation/', include('apps.admin.urls',namespace="admin")),
    #url(r'^admin/elicitation/', include('apps.elicitation',namespace="elicitation"))
    #url(r'^admin/', 'apps.admin'),
)# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)