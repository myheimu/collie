from django.conf.urls import patterns, url
import views


urlpatterns = patterns('',
                       url(r'^index', views.index, name='modules list index page'),
                       url(r'^manage', views.manage, name='module manage page'),
                       url(r'^permission', views.set_public, name='set module permission'),
                       url(r'^delete', views.delete, name='delete module'),
                       url(r'^latest', views.latest, name='get latest version of module'),
                       url(r'^version/new', views.new_version, name='create new version'),
                       url(r'^version/delete', views.delete_version, name='delete version'),
                       url(r'^version/download', views.download, name='download version'),
                       url(r'^upload', views.upload, name="upload file"),
                       url(r'^git/history', views.git_history, name="git history"),
                       url(r'^git/upload', views.git_upload, name="upload file from git"),
                       url(r'^git/build', views.git_build, name="get git build name"),
                       url(r'^save', views.save, name="save module"),
                       url(r'^detail', views.detail, name="get module detail"),
                       url(r'^owner/update', views.update_owner, name="update owner"),
                       url(r'^description/update', views.update_description, name="update description"),
                       url(r'^wiki_link/update', views.update_wiki_link, name="update wiki link"),
                       url(r'^version/detail', views.version_detail, name="get version detail"))