# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Module'
        db.create_table(u'module_module', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('wiki_link', self.gf('django.db.models.fields.CharField')(default='', max_length=1000)),
            ('created_by', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modify_by', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('modify_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0, max_length=3)),
        ))
        db.send_create_signal(u'module', ['Module'])

        # Adding model 'ModuleHdfsFiles'
        db.create_table('module_hdfsfiles', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('checksum', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('path', self.gf('django.db.models.fields.CharField')(default='', max_length=1024)),
        ))
        db.send_create_signal(u'module', ['ModuleHdfsFiles'])

        # Adding model 'ModuleVersions'
        db.create_table('module_versions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('module_id', self.gf('django.db.models.fields.IntegerField')(max_length=10, db_index=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('comment', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('file', self.gf('core.models.BlobField')()),
            ('hdfs_file_id', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=10)),
            ('file_name', self.gf('django.db.models.fields.CharField')(default='', max_length=100)),
            ('git_options', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('options', self.gf('django.db.models.fields.CharField')(default='', max_length=10000)),
            ('created_by', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('refer_count', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=10)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0, max_length=3)),
        ))
        db.send_create_signal(u'module', ['ModuleVersions'])

        # Adding model 'UserGit'
        db.create_table('user_git', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('git_repository', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'module', ['UserGit'])

        # Adding unique constraint on 'UserGit', fields ['username', 'git_repository']
        db.create_unique('user_git', ['username', 'git_repository'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserGit', fields ['username', 'git_repository']
        db.delete_unique('user_git', ['username', 'git_repository'])

        # Deleting model 'Module'
        db.delete_table(u'module_module')

        # Deleting model 'ModuleHdfsFiles'
        db.delete_table('module_hdfsfiles')

        # Deleting model 'ModuleVersions'
        db.delete_table('module_versions')

        # Deleting model 'UserGit'
        db.delete_table('user_git')


    models = {
        u'module.module': {
            'Meta': {'object_name': 'Module'},
            'created_by': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modify_by': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'modify_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'wiki_link': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'})
        },
        u'module.modulehdfsfiles': {
            'Meta': {'object_name': 'ModuleHdfsFiles', 'db_table': "'module_hdfsfiles'"},
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'path': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024'})
        },
        u'module.moduleversions': {
            'Meta': {'object_name': 'ModuleVersions', 'db_table': "'module_versions'"},
            'comment': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('core.models.BlobField', [], {}),
            'file_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'git_options': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'hdfs_file_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module_id': ('django.db.models.fields.IntegerField', [], {'max_length': '10', 'db_index': 'True'}),
            'options': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10000'}),
            'refer_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '3'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'module.usergit': {
            'Meta': {'unique_together': "(('username', 'git_repository'),)", 'object_name': 'UserGit', 'db_table': "'user_git'"},
            'git_repository': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'})
        }
    }

    complete_apps = ['module']