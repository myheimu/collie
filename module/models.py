import base64
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib import admin
import logging
from django.utils import timezone
from core.models import BlobField
from core.utils import get_uploaded_file_content, has_file
from settings import settings
from core.webhdfs import WebHdfs
from core.file_handler import checksum_file

logger = logging.getLogger("collie")


class Module(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, default='')
    wiki_link = models.CharField(max_length=1000, default='')
    created_by = models.CharField(max_length=100, default='')
    created_time = models.DateTimeField(auto_now_add=True)
    modify_by = models.CharField(max_length=100, default='')
    modify_time = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    status = models.SmallIntegerField(max_length=3, default=0)

    @classmethod
    def create(cls, name, description, wiki_link, created_by):
        module = cls(name=name,
                     description=description,
                     wiki_link=wiki_link,
                     created_by=created_by,
                     created_time=timezone.now(),
                     modify_by=created_by,
                     modify_time=timezone.now(),
                     is_public=False,
                     status=0)
        module.save()
        logger.debug("created module successfully, name %s, description %s", name, description)
        return module


class ModuleHdfsFiles(models.Model):
    name = models.CharField(max_length=1024)
    checksum = models.CharField(max_length=64, db_index=True)
    path = models.CharField(max_length=1024, default='')  # file name format: name_checksum

    class Meta:
        db_table = 'module_hdfsfiles'


class ModuleVersions(models.Model):
    module_id = models.IntegerField(max_length=10, db_index=True)
    type = models.CharField(max_length=100)
    comment = models.CharField(max_length=200, default='')
    file = BlobField()
    hdfs_file_id = models.IntegerField(max_length=10, default=0)
    file_name = models.CharField(max_length=100, default='')
    git_options = models.CharField(max_length=500, null=True)
    options = models.CharField(max_length=10000, default='')  # custom extended parameters
    created_by = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    refer_count = models.IntegerField(max_length=10, default=0)
    status = models.SmallIntegerField(max_length=3, default=0)

    @classmethod
    def create(cls, module_id, comment, version_type, file_name, git_options, keep_old_file, options, created_by):
        file_content = ""  # used by module save mode == DB
        hdfs_file_id = 0  # used by module save mode == HDFS

        if keep_old_file:
            module_version_latest = ModuleVersions.objects.filter(module_id=module_id, status=0).order_by("-id")[:1].get()

            if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_HDFS:
                hdfs_file_id = module_version_latest.hdfs_file_id
            else:
                file_content = module_version_latest.file
        elif has_file(file_name):
            if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_HDFS:
                uploaded_file_path = settings.MEDIA_PATH + file_name
                checksum = checksum_file(open(uploaded_file_path))
                webhdfs = WebHdfs()
                remote_file_path = settings.MODULE_HDFS_ROOT + file_name + "_" + checksum
                logger.info("hdfs copy from local %s to remote %s", uploaded_file_path, remote_file_path)
                webhdfs.copyFromLocal(uploaded_file_path, remote_file_path)
                module_file = ModuleHdfsFiles(name=file_name,
                                              checksum=checksum,
                                              path=remote_file_path)
                module_file.save()
                hdfs_file_id = module_file.id
            else:
                file_raw = get_uploaded_file_content(file_name)
                file_content = base64.b64encode("".join(file_raw))
        else:
            raise ObjectDoesNotExist

        logger.info('create version --')
        module_version = cls(module_id=module_id,
                             comment=comment,
                             type=version_type,
                             file=file_content,
                             hdfs_file_id=hdfs_file_id,
                             file_name=file_name,
                             git_options=git_options,
                             options=options,
                             created_by=created_by,
                             created_time=timezone.now())
        module_version.save()
        logger.info('create version ++')
        logger.debug("module version is created, id %s, type %s, file_name %s, git_options %s, options %s",
                     module_id, version_type, file_name, git_options, options)
        return module_version

    class Meta:
        db_table = 'module_versions'


class UserGit(models.Model):
    username = models.CharField(max_length=30, db_index=True)
    git_repository = models.CharField(max_length=200)

    class Meta:
        db_table = 'user_git'
        unique_together = ('username', 'git_repository')


class UserGitAdmin(admin.ModelAdmin):
    list_display = ('username', 'git_repository')
    search_fields = ('username', 'git_repository')
    list_filter = ('username', 'git_repository')

admin.site.register(UserGit, UserGitAdmin)