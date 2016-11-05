import logging
from django.contrib import admin
from django.db import models
from django.utils import timezone
from object_permissions import register
from core.models import BlobField


logger = logging.getLogger("collie")


class Project(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.CharField(max_length=100, default='')
    created_time = models.DateTimeField(auto_now_add=True)
    modify_by = models.CharField(max_length=100, default='')
    modify_time = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(default=0)  # 0: normal / -1: deleted

    @staticmethod
    def create(project_name, created_by):
        project = Project(name=project_name,
                          created_by=created_by,
                          created_time=timezone.now(),
                          modify_by=created_by,
                          modify_time=timezone.now(),
                          status=0)
        project.save()
        return project

    def __unicode__(self):
        return '%s' % self.name

# register permissions onto Project
PROJECT_PERM_OWNER = 'owner'
PROJECT_PERM_USER = 'operator'
register([PROJECT_PERM_OWNER, PROJECT_PERM_USER], Project)
admin.site.register(Project)


class ProjectVersions(models.Model):
    project_id = models.IntegerField(db_index=True)
    project_version = models.IntegerField(db_index=True)
    diagram = models.CharField(max_length=20000, default="")
    upload_user = models.CharField(max_length=64)
    upload_time = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=16)
    file_name = models.CharField(max_length=256)
    hdfs_path = models.CharField(max_length=1024, default="")
    md5 = models.CharField(max_length=16)
    num_chunks = models.IntegerField()

    class Meta:
        db_table = 'project_versions'
        # unique_together = ('project_id', 'project_version')

    def __unicode__(self):
        return '%d:%d:%s' % (self.project_id, self.project_version, self.file_name)


class ProjectFiles(models.Model):
    project_id = models.IntegerField(db_index=True)
    project_version = models.IntegerField(db_index=True)
    chunk = models.IntegerField()
    file = BlobField()

    class Meta:
        db_table = 'project_files'
        # unique_together = ('project_id', 'project_version')


class ExecutionFlows(models.Model):
    execution_id = models.AutoField(primary_key=True)
    schedule_id = models.IntegerField(default=0)
    node_id = models.PositiveSmallIntegerField()
    project_id = models.PositiveIntegerField(db_index=True)
    project_version = models.PositiveIntegerField()
    flow_id = models.CharField(max_length=255)
    flow_data = BlobField()
    encoding_type = models.CharField(max_length=16)
    status = models.CharField(max_length=32)
    submit_user = models.CharField(max_length=255)
    submit_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    update_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'execution_flows'

    @staticmethod
    def create(self, flow):
        '''@type: flows.Flow'''
        ExecutionFlows.objects.create(flow)


class ExecutionJobs(models.Model):
    execution_id = models.IntegerField()
    node_id = models.PositiveSmallIntegerField()
    project_id = models.PositiveIntegerField()
    project_version = models.PositiveIntegerField()
    flow_id = models.CharField(max_length=255)
    job_id = models.CharField(max_length=255)
    status = models.CharField(max_length=32)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    update_time = models.DateTimeField(auto_now_add=True)
    input_params = BlobField()
    output_params = BlobField()

    class Meta:
        db_table = 'execution_jobs'
        unique_together = ('execution_id', 'job_id')


class FlowLogs(models.Model):
    execution_id = models.AutoField(primary_key=True)
    node_id = models.PositiveSmallIntegerField()
    encoding_type = models.CharField(max_length=16)
    start_byte = models.PositiveIntegerField()
    end_byte = models.PositiveIntegerField()
    upload_time = models.DateTimeField(auto_now_add=True)
    log = BlobField()

    class Meta:
        db_table = 'flow_logs'


class JobLogs(models.Model):
    execution_id = models.IntegerField()
    node_id = models.PositiveSmallIntegerField()
    job_id = models.CharField(max_length=255)
    encoding_type = models.CharField(max_length=16)
    start_byte = models.PositiveIntegerField()
    end_byte = models.PositiveIntegerField()
    upload_time = models.DateTimeField(auto_now_add=True)
    log = BlobField()

    class Meta:
        db_table = 'job_logs'
        unique_together = ('execution_id', 'job_id')


class Schedule(models.Model):
    node_id = models.IntegerField()
    schedule_user = models.CharField(max_length=64)
    project_id = models.IntegerField(max_length=10)
    project_version = models.IntegerField(max_length=10)
    flow_id = models.CharField(max_length=128)
    flow_data = BlobField()
    encoding_type = models.CharField(max_length=16, default='PLAIN')
    first_check_time = models.CharField(max_length=32)
    period = models.CharField(max_length=32)
    timezone = models.CharField(max_length=32)
    status = models.CharField(max_length=16, default='READY')
    create_time = models.DateTimeField()
    update_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schedule'
        unique_together = ('id', 'project_id', 'project_version', 'flow_id')


class Trigger(models.Model):
    status = models.CharField(max_length=16, default="READY")
    encoding_type = models.CharField(max_length=16, default="PLAIN")
    data = BlobField()
    create_time = models.DateTimeField()
    update_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'trigger'