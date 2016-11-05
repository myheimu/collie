##
# DO NOT RUN IT!!
##

# step 1: dump project files from mysql to local
import base64
from dircache import listdir
from genericpath import isdir, isfile
import os
from os.path import join
from django.core.exceptions import ObjectDoesNotExist
from core.file_handler import checksum_file
from core.webhdfs import WebHdfs
from project.models import ProjectFiles, Project, ProjectVersions


# 1st step:
# from project.migrate_project_files import dump_mysql2local
# dump_mysql2local()
def dump_mysql2local():
    path_prefix = "/home/work/data/collie/local_projects/"
    if not os.path.exists(path_prefix):
        os.mkdir(path_prefix)

    for file_id in range(100, 2800):
        print "processing file id %d" % file_id
        try:
            project_file = ProjectFiles.objects.get(id=file_id)
            project_id = project_file.project_id
            project_version = project_file.project_version
            file_content_b64 = project_file.file

            if len(file_content_b64) <= 0:
                continue

            project = Project.objects.get(id=project_id)
            project_name = project.name
            file_content = base64.b64decode(file_content_b64)

            file_folder = path_prefix + str(project_version) + "/"
            if not os.path.exists(file_folder):
                os.mkdir(file_folder)

            file_path = file_folder + project_name + ".zip"
            out_file = open(file_path, 'wb+')
            out_file.write(file_content)
            out_file.close()

            in_file = open(file_path, 'rb')
            checksum = checksum_file(in_file)
            file_new_path = file_path + '_' + checksum
            os.rename(file_path, file_new_path)

            print "copied to local, project name %s" % project_name
        except ObjectDoesNotExist:
            continue


# 2nd step
# from project.migrate_project_files import copy2remote
# copy2remote()
def copy2remote():
    webhdfs = WebHdfs()
    base_path = "/home/work/data/collie/local_projects/"
    dirs = [f for f in listdir(base_path) if isdir(join(base_path, f))]
    for dr in dirs:
        try:
            project_version = int(dr)
            print "processing version %d" % project_version

            project_file_path = join(base_path, dr)
            files = [f for f in listdir(project_file_path) if isfile(join(project_file_path, f))]

            if len(files) <= 0:
                continue

            if len(files) > 1:
                print "ERROR!!!"

            file_name = files[0]
            local_path = join(project_file_path, file_name)
            # local_path_new = join(project_file_path, str(project_version) + ".zip")
            # os.rename(local_path, local_path_new)

            remote_path = "/user/h_sns/collie/projects/"

            webhdfs.copyFromLocal(local_path, remote_path)
            print "local copied from %s to %s" % (local_path, remote_path)

            version = ProjectVersions.objects.filter(project_version=project_version)[:1].get()
            version.hdfs_path = join(remote_path, file_name)
            version.save()

            print "saved version %d, path %s" % (project_version, version.hdfs_path)
        except IOError:
            print "Error!!"
            continue
        except OSError:
            print "Error!!"
            continue