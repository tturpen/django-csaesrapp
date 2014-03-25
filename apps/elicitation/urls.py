from django.conf.urls import patterns, url

from apps.elicitation import views

urlpatterns = patterns('',
                       url(r'^promptsource/$',views.index,name='index'),
#                        url(r'^specifics/(?P<pk>\w+)/$',views.DetailView.as_view(),name='detail'),
#                        url(r'^(?P<pk>\w+)/results/$',views.ResultsView.as_view(),name='results'),
#                        url(r'^(?P<pk>\w+)/vote/$', views.vote,name='vote'),
                       )

