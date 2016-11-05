from django.conf import settings
import os

__author__ = 'haibin'


def has_file(file_name):
    return os.path.isfile(settings.MEDIA_PATH + file_name)


def get_uploaded_file_content(file_name):
    return get_file_content(settings.MEDIA_PATH + file_name)


def get_file_content(file_path):
    file_content = []
    with open(file_path, 'rb') as f:
        while 1:
            byte_s = f.read(1024 * 1024)
            if not byte_s:
                break
            byte_s_len = len(byte_s)
            file_content.append(byte_s)
            if byte_s_len < 1024 * 1024:
                break
    return file_content