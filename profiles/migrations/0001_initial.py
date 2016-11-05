# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'KerberosKeys'
        db.create_table('kerberos_keys', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('file', self.gf('core.models.BlobField')()),
        ))
        db.send_create_signal(u'profiles', ['KerberosKeys'])

        # Adding model 'CollieGroup'
        db.create_table('collie_group', (
            (u'group_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Group'], unique=True, primary_key=True)),
            ('admins', self.gf('django.db.models.fields.CharField')(default='', max_length=1000)),
        ))
        db.send_create_signal(u'profiles', ['CollieGroup'])

        # Adding model 'GroupRequest'
        db.create_table('group_request', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
        ))
        db.send_create_signal(u'profiles', ['GroupRequest'])

        # Adding unique constraint on 'GroupRequest', fields ['user', 'group']
        db.create_unique('group_request', ['user_id', 'group_id'])

        # Adding model 'Principal'
        db.create_table('kerberos_principal', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, db_index=True)),
            ('belong_to', self.gf('django.db.models.fields.SmallIntegerField')(max_length=4)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(max_length=4)),
        ))
        db.send_create_signal(u'profiles', ['Principal'])

        # Adding model 'PrincipalRequest'
        db.create_table('principal_request', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('principal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['profiles.Principal'])),
        ))
        db.send_create_signal(u'profiles', ['PrincipalRequest'])

        # Adding unique constraint on 'PrincipalRequest', fields ['user', 'principal']
        db.create_unique('principal_request', ['user_id', 'principal_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'PrincipalRequest', fields ['user', 'principal']
        db.delete_unique('principal_request', ['user_id', 'principal_id'])

        # Removing unique constraint on 'GroupRequest', fields ['user', 'group']
        db.delete_unique('group_request', ['user_id', 'group_id'])

        # Deleting model 'KerberosKeys'
        db.delete_table('kerberos_keys')

        # Deleting model 'CollieGroup'
        db.delete_table('collie_group')

        # Deleting model 'GroupRequest'
        db.delete_table('group_request')

        # Deleting model 'Principal'
        db.delete_table('kerberos_principal')

        # Deleting model 'PrincipalRequest'
        db.delete_table('principal_request')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'profiles.colliegroup': {
            'Meta': {'object_name': 'CollieGroup', 'db_table': "'collie_group'", '_ormbases': [u'auth.Group']},
            'admins': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            u'group_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.Group']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'profiles.grouprequest': {
            'Meta': {'unique_together': "(('user', 'group'),)", 'object_name': 'GroupRequest', 'db_table': "'group_request'"},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'profiles.kerberoskeys': {
            'Meta': {'object_name': 'KerberosKeys', 'db_table': "'kerberos_keys'"},
            'file': ('core.models.BlobField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'profiles.principal': {
            'Meta': {'object_name': 'Principal', 'db_table': "'kerberos_principal'"},
            'belong_to': ('django.db.models.fields.SmallIntegerField', [], {'max_length': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'max_length': '4'})
        },
        u'profiles.principalrequest': {
            'Meta': {'unique_together': "(('user', 'principal'),)", 'object_name': 'PrincipalRequest', 'db_table': "'principal_request'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'principal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['profiles.Principal']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['profiles']