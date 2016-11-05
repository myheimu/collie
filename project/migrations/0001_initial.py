# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Project'
        db.create_table(u'project_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('created_by', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modify_by', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('modify_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'project', ['Project'])

        # Adding model 'ProjectVersions'
        db.create_table('project_versions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('project_version', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('diagram', self.gf('django.db.models.fields.CharField')(default='', max_length=20000)),
            ('upload_user', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('upload_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('file_name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('hdfs_path', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
            ('md5', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('num_chunks', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'project', ['ProjectVersions'])

        # Adding model 'ProjectFiles'
        db.create_table('project_files', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project_id', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('project_version', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('chunk', self.gf('django.db.models.fields.IntegerField')()),
            ('file', self.gf('core.models.BlobField')()),
        ))
        db.send_create_signal(u'project', ['ProjectFiles'])

        # Adding model 'ExecutionFlows'
        db.create_table('execution_flows', (
            ('execution_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('schedule_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('node_id', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('project_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('project_version', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('flow_data', self.gf('core.models.BlobField')()),
            ('encoding_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('submit_user', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('submit_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'project', ['ExecutionFlows'])

        # Adding model 'ExecutionJobs'
        db.create_table('execution_jobs', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('execution_id', self.gf('django.db.models.fields.IntegerField')()),
            ('node_id', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('project_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('project_version', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('flow_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('job_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('end_time', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('input_params', self.gf('core.models.BlobField')()),
            ('output_params', self.gf('core.models.BlobField')()),
        ))
        db.send_create_signal(u'project', ['ExecutionJobs'])

        # Adding unique constraint on 'ExecutionJobs', fields ['execution_id', 'job_id']
        db.create_unique('execution_jobs', ['execution_id', 'job_id'])

        # Adding model 'FlowLogs'
        db.create_table('flow_logs', (
            ('execution_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node_id', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('encoding_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('start_byte', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('end_byte', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('upload_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('log', self.gf('core.models.BlobField')()),
        ))
        db.send_create_signal(u'project', ['FlowLogs'])

        # Adding model 'JobLogs'
        db.create_table('job_logs', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('execution_id', self.gf('django.db.models.fields.IntegerField')()),
            ('node_id', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('job_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('encoding_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('start_byte', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('end_byte', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('upload_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('log', self.gf('core.models.BlobField')()),
        ))
        db.send_create_signal(u'project', ['JobLogs'])

        # Adding unique constraint on 'JobLogs', fields ['execution_id', 'job_id']
        db.create_unique('job_logs', ['execution_id', 'job_id'])

        # Adding model 'Schedule'
        db.create_table('schedule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node_id', self.gf('django.db.models.fields.IntegerField')()),
            ('schedule_user', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('project_id', self.gf('django.db.models.fields.IntegerField')(max_length=10)),
            ('project_version', self.gf('django.db.models.fields.IntegerField')(max_length=10)),
            ('flow_id', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('flow_data', self.gf('core.models.BlobField')()),
            ('encoding_type', self.gf('django.db.models.fields.CharField')(default='PLAIN', max_length=16)),
            ('first_check_time', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('period', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('timezone', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('status', self.gf('django.db.models.fields.CharField')(default='READY', max_length=16)),
            ('create_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'project', ['Schedule'])

        # Adding unique constraint on 'Schedule', fields [u'id', 'project_id', 'project_version', 'flow_id']
        db.create_unique('schedule', [u'id', 'project_id', 'project_version', 'flow_id'])

        # Adding model 'Trigger'
        db.create_table('trigger', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='READY', max_length=16)),
            ('encoding_type', self.gf('django.db.models.fields.CharField')(default='PLAIN', max_length=16)),
            ('data', self.gf('core.models.BlobField')()),
            ('create_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('update_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'project', ['Trigger'])


    def backwards(self, orm):
        # Removing unique constraint on 'Schedule', fields [u'id', 'project_id', 'project_version', 'flow_id']
        db.delete_unique('schedule', [u'id', 'project_id', 'project_version', 'flow_id'])

        # Removing unique constraint on 'JobLogs', fields ['execution_id', 'job_id']
        db.delete_unique('job_logs', ['execution_id', 'job_id'])

        # Removing unique constraint on 'ExecutionJobs', fields ['execution_id', 'job_id']
        db.delete_unique('execution_jobs', ['execution_id', 'job_id'])

        # Deleting model 'Project'
        db.delete_table(u'project_project')

        # Deleting model 'ProjectVersions'
        db.delete_table('project_versions')

        # Deleting model 'ProjectFiles'
        db.delete_table('project_files')

        # Deleting model 'ExecutionFlows'
        db.delete_table('execution_flows')

        # Deleting model 'ExecutionJobs'
        db.delete_table('execution_jobs')

        # Deleting model 'FlowLogs'
        db.delete_table('flow_logs')

        # Deleting model 'JobLogs'
        db.delete_table('job_logs')

        # Deleting model 'Schedule'
        db.delete_table('schedule')

        # Deleting model 'Trigger'
        db.delete_table('trigger')


    models = {
        u'project.executionflows': {
            'Meta': {'object_name': 'ExecutionFlows', 'db_table': "'execution_flows'"},
            'encoding_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'execution_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'flow_data': ('core.models.BlobField', [], {}),
            'flow_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'node_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'project_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'project_version': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'schedule_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'submit_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'submit_user': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'project.executionjobs': {
            'Meta': {'unique_together': "(('execution_id', 'job_id'),)", 'object_name': 'ExecutionJobs', 'db_table': "'execution_jobs'"},
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'execution_id': ('django.db.models.fields.IntegerField', [], {}),
            'flow_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_params': ('core.models.BlobField', [], {}),
            'job_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'node_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'output_params': ('core.models.BlobField', [], {}),
            'project_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'project_version': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'project.flowlogs': {
            'Meta': {'object_name': 'FlowLogs', 'db_table': "'flow_logs'"},
            'encoding_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'end_byte': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'execution_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('core.models.BlobField', [], {}),
            'node_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'start_byte': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'project.joblogs': {
            'Meta': {'unique_together': "(('execution_id', 'job_id'),)", 'object_name': 'JobLogs', 'db_table': "'job_logs'"},
            'encoding_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'end_byte': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'execution_id': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'log': ('core.models.BlobField', [], {}),
            'node_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'start_byte': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'project.project': {
            'Meta': {'object_name': 'Project'},
            'created_by': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modify_by': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'modify_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        u'project.projectfiles': {
            'Meta': {'object_name': 'ProjectFiles', 'db_table': "'project_files'"},
            'chunk': ('django.db.models.fields.IntegerField', [], {}),
            'file': ('core.models.BlobField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'project_version': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'})
        },
        u'project.projectversions': {
            'Meta': {'object_name': 'ProjectVersions', 'db_table': "'project_versions'"},
            'diagram': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20000'}),
            'file_name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'file_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'hdfs_path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'num_chunks': ('django.db.models.fields.IntegerField', [], {}),
            'project_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'project_version': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'upload_user': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'project.schedule': {
            'Meta': {'unique_together': "(('id', 'project_id', 'project_version', 'flow_id'),)", 'object_name': 'Schedule', 'db_table': "'schedule'"},
            'create_time': ('django.db.models.fields.DateTimeField', [], {}),
            'encoding_type': ('django.db.models.fields.CharField', [], {'default': "'PLAIN'", 'max_length': '16'}),
            'first_check_time': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'flow_data': ('core.models.BlobField', [], {}),
            'flow_id': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node_id': ('django.db.models.fields.IntegerField', [], {}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'project_id': ('django.db.models.fields.IntegerField', [], {'max_length': '10'}),
            'project_version': ('django.db.models.fields.IntegerField', [], {'max_length': '10'}),
            'schedule_user': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'READY'", 'max_length': '16'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'project.trigger': {
            'Meta': {'object_name': 'Trigger', 'db_table': "'trigger'"},
            'create_time': ('django.db.models.fields.DateTimeField', [], {}),
            'data': ('core.models.BlobField', [], {}),
            'encoding_type': ('django.db.models.fields.CharField', [], {'default': "'PLAIN'", 'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'READY'", 'max_length': '16'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['project']