from django.conf.urls import patterns, url
import views


urlpatterns = patterns('',
                       url(r'^index', views.index, name="modules list index page"),
                       url(r'^list/latest', views.get_tables, name="table list"),
                       url(r'^create', views.create_table, name="table create"),
                       url(r'^register', views.register_table, name="table register"),
                       url(r'^data/create', views.create, name="table create"),
                       url(r'^describe', views.describe_table, name="table describe"),
                       url(r'^file_list', views.file_browser_list, name="file browser list status"),
                       url(r'^file_preview', views.file_preview, name="file browser file preview"),
                       url(r'^log_table_list', views.log_table_list, name="table list status"),
                       url(r'^log_table_info', views.log_table_info, name="show table info"),
                       )