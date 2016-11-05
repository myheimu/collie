from django.contrib.admin import site, ModelAdmin
from models import ProjectVersions


class ProjectVersionsAdmin(ModelAdmin):
    list_display = ('project_id', 'project_version', 'upload_user', 'upload_time')


site.register(ProjectVersions, ProjectVersionsAdmin)