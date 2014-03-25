from django.conf.urls import patterns, url, include
from apps.elicitation import urls as elicitationurls
from apps.elicitation import views

urlpatterns = patterns('',
                       url(r'^elicitation/$',include(elicitationurls)),
#                        url(r'^specifics/(?P<pk>\w+)/$',views.DetailView.as_view(),name='detail'),
#                        url(r'^(?P<pk>\w+)/results/$',views.ResultsView.as_view(),name='results'),
#                        url(r'^(?P<pk>\w+)/vote/$', views.vote,name='vote'),
                       )

