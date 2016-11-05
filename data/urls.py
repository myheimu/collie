__author__ = 'haibin'

from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
                       url(r'^hello_world', views.hello_world, name="hello world"),
                       url(r'^user_profile', views.get_user_profile, name="get user profile"))