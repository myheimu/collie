##
# DO NOT RUN IT!!
##
import base64
from dircache import listdir
from genericpath import isfile
import os
from os.path import join
from django.core.exceptions import ObjectDoesNotExist
import time
from core.file_handler import checksum_file
from core.webhdfs import WebHdfs
from module.models import ModuleVersions, ModuleHdfsFiles


def test():
    print "hello world"


def migrate_dump_local():
    # get module versions from
    for version_id in range(0, 2000):
        try:
            module_version = ModuleVersions.objects.get(id=version_id)
            file_content = base64.b64decode(module_version.file)
            file_name = module_version.file_name

            base_path = "/home/work/data/collie/local_modules/" + str(version_id) + "/"
            local_path = base_path + file_name
            if not os.path.exists(base_path):
                os.mkdir(base_path)
            open(local_path, "wb+").write(file_content)

            print "%d is saving file to %s" % (version_id, local_path)
        except ObjectDoesNotExist:
            continue


def migrate_copy2_remote():
    result_file = open("/home/work/data/collie/local_modules/results.log", "wb+")
    webhdfs = WebHdfs()
    for version_id in range(0, 2000):
        try:
            base_path = "/home/work/data/collie/local_modules/" + str(version_id) + "/"
            files = [f for f in listdir(base_path) if isfile(join(base_path, f))]
            if len(files) <= 0:
                continue
            file_name = files[0]
            version_file = open(join(base_path, file_name), 'rb')
            checksum = checksum_file(version_file)
            file_name_new = file_name + "_" + checksum
            os.rename(join(base_path, file_name), join(base_path, file_name_new))
            remote_path = "/user/h_sns/collie/modules/"

            webhdfs.copyFromLocal(join(base_path, file_name_new), remote_path)
            result_file.write(str(version_id) + "\t" + remote_path + file_name_new + "\n")

            print "%d is saving to remote %s" % (version_id, remote_path + file_name_new)
        except IOError:
            continue
        except OSError:
            continue


def migrate_mysql():
    result_file = open("/home/work/data/collie/local_modules/results.log", "rb")
    for line in result_file.readlines():
        parts = line.split("\t")
        _items = parts[1].split("/")
        hdfs_file_path = parts[1]
        hdfs_file_name = _items[len(_items)-1]
        version_id = int(parts[0])
        file_name = hdfs_file_name[:-34]
        checksum = hdfs_file_name[-33:]

        module_hdfs_file = ModuleHdfsFiles(name=file_name,
                                           checksum=checksum,
                                           path=hdfs_file_path)
        module_hdfs_file.save()

        version = ModuleVersions.objects.get(id=version_id)
        version.hdfs_file_id = module_hdfs_file.id
        version.file = ""
        version.save()

        print "%d %s %s %s" % (version_id, file_name, checksum, hdfs_file_path)