from django.conf.urls import patterns, url
import views


urlpatterns = patterns('',
                       url(r'^index', views.profile_index, name='profile index page'),
                       url(r'^nickname', views.profile_nickname, name='get user nickname'),
                       url(r'^kerberos', views.profile_kerberos, name='profile kerberos page'),
                       url(r'^groups', views.profile_groups_page, name='profile groups page'),
                       url(r'^principal', views.profile_principal, name='profile kerberos principal page'),
                       url(r'^group/verify', views.verify_group_name, name='verify group name'),
                       url(r'^group/create', views.create_group, name='create group'),
                       url(r'^group/join', views.join_group, name='apply to join group'),
                       url(r'^group/approve', views.approve_group, name='approve to join group'),
                       url(r'^group/deny', views.deny_group, name='deny to join group'),
                       url(r'^group/leave', views.leave_group, name='leave group'),
                       url(r'^upload_kerberos', views.profile_kerberos_upload, name='upload profile kerberos'),
                       url(r'^save_kerberos', views.profile_kerberos_save, name='save profile kerberos'),
                       url(r'^delete_kerberos', views.profile_kerberos_delete, name='delete profile kerberos'))