# -*- coding: UTF-8 -*-

from django.db import models
from django.contrib import admin

# Create your models here.
from django.db.models import Model


# 部门
class Department(Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "department"
admin.site.register(Department)


# 业务
class Service(Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'service'
admin.site.register(Service)


# 业务数据表
class Table(Model):
    name = models.CharField(max_length=255, unique=True)
    service = models.ForeignKey("Service")

    class Meta:
        db_table = 'table_table'
admin.site.register(Table)


# 已有业务表
class ExistedTable(Model):
    name = models.CharField(max_length=1024)  # 日志名
    uri = models.CharField(max_length=1024)  # 数据URI
    department = models.CharField(max_length=255)  # 日志所属部门
    service = models.CharField(max_length=255)  # 日志所属业务
    service_supervisor = models.CharField(max_length=255)  # 业务负责人
    supervisor = models.CharField(max_length=255)  # 日志负责人
    description = models.CharField(max_length=1024)  # 日志描述
    privacy_level = models.CharField(max_length=32)  # 日志权限：隐私级别（A/B/C）
    grant_user_list = models.CharField(max_length=1024)  # 日志权限：读权限用户列表（Public或指定kerberros帐号列表）
    deser_format = models.CharField(max_length=1024)  # 日志序列化格式
    definition = models.TextField(default="")
    created_by = models.CharField(max_length=255)  # 创建者
    created_time = models.DateTimeField(auto_now_add=True)
    modify_by = models.CharField(max_length=255)  # 最后的修改者
    modify_time = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(max_length=10, default=0)
    data_type = models.CharField(max_length=255, default='log-data')         # 数据类型
    update_time = models.IntegerField(max_length=10, default=0)  # 更新时间
    log_hold_time = models.IntegerField(max_length=10, default=1)  # 日志保留时间

    class Meta:
        db_table = 'existed_table'
admin.site.register(ExistedTable)


