from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.views.generic import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^$', RedirectView.as_view(url='/project/index', permanent=False), name='index'),
                       url(r'^index/$', RedirectView.as_view(url='/project/index', permanent=False), name='index'),
                       # account login/logout
                       # url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html',
                       #                                                      'redirect_field_name': 'next'}),
                       # url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/index/'}),
                       #et
                       url(r'^accounts/login/$', 'django_cas.views.login'),
                       url(r'^accounts/logout/$', 'django_cas.views.logout'),

                       url(r'^admin/', include(admin.site.urls)),


                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^module/', include('module.urls')),
                       url(r'^auth/', include('auth.urls')),
                       url(r'^profile/', include('profiles.urls')),
                       # url(r'^project/', include('project.urls', namespace='project')))
                       url(r'^project/', include('project.urls', namespace='project')),
                       url(r'^data/', include('data.urls', namespace='data')),
                       url(r'^table/', include('table.urls', namespace='table')))