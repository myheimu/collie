# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Department'
        db.create_table('department', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'table', ['Department'])

        # Adding model 'Service'
        db.create_table('service', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'table', ['Service'])

        # Adding model 'Table'
        db.create_table('table_table', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['table.Service'])),
        ))
        db.send_create_signal(u'table', ['Table'])

        # Adding model 'ExistedTable'
        db.create_table('existed_table', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('uri', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('department', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('service', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('service_supervisor', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('supervisor', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('privacy_level', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('grant_user_list', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('deser_format', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('definition', self.gf('django.db.models.fields.TextField')(default='')),
            ('created_by', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modify_by', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('modify_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0, max_length=10)),
            ('data_type', self.gf('django.db.models.fields.CharField')(default='log-data', max_length=255)),
            ('update_time', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=10)),
            ('log_hold_time', self.gf('django.db.models.fields.IntegerField')(default=1, max_length=10)),
        ))
        db.send_create_signal(u'table', ['ExistedTable'])


    def backwards(self, orm):
        # Deleting model 'Department'
        db.delete_table('department')

        # Deleting model 'Service'
        db.delete_table('service')

        # Deleting model 'Table'
        db.delete_table('table_table')

        # Deleting model 'ExistedTable'
        db.delete_table('existed_table')


    models = {
        u'table.department': {
            'Meta': {'object_name': 'Department', 'db_table': "'department'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'table.existedtable': {
            'Meta': {'object_name': 'ExistedTable', 'db_table': "'existed_table'"},
            'created_by': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_type': ('django.db.models.fields.CharField', [], {'default': "'log-data'", 'max_length': '255'}),
            'definition': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'deser_format': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'grant_user_list': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log_hold_time': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '10'}),
            'modify_by': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'modify_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'privacy_level': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'service': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'service_supervisor': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0', 'max_length': '10'}),
            'supervisor': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'update_time': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '10'}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'table.service': {
            'Meta': {'object_name': 'Service', 'db_table': "'service'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'table.table': {
            'Meta': {'object_name': 'Table'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['table.Service']"})
        }
    }

    complete_apps = ['table']