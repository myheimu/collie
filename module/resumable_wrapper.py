import logging
import math
from threading import Lock
import os
from settings import settings

logger = logging.getLogger("collie")


class ResumableWrapper(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ResumableWrapper, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    #
    # {
    #   "f_id_0": {"temp_file_path": "/home/.../xxx.temp", "file_name": "xxx", "chunk_size": 4, "uploaded": [0,1]}
    #   "f_id_1": {"temp_file_path": "/home/.../xxx.temp", "file_name": "xxx", "chunk_size": 4, "uploaded": [0,2]}
    #   ...
    # }
    #
    file_info_map = {}
    lock = Lock()

    def write(self, file_identifier, chunk_number, chunk_size, total_size, file_name, file_content):
        logger.debug("write file")
        self.lock.acquire()
        try:
            if chunk_number <= 0 or chunk_size < 0 or total_size < 0 or \
                    not file_identifier or not file_name:
                logger.error("file write info is valid")
                self.remove(file_identifier)
                return

            # write content
            temp_file_path = os.path.join(settings.MEDIA_PATH, file_name + ".temp")
            temp_file = open(temp_file_path, "a")
            temp_file.seek((chunk_number - 1) * chunk_size)
            logger.debug("writing %d content, chunk_size %d", len(file_content), chunk_size)
            temp_file.write(file_content)
            temp_file.flush()
            temp_file.close()

            # update map
            if file_identifier not in self.file_info_map:
                self.file_info_map[file_identifier] = {}
                self.file_info_map[file_identifier]["temp_file_path"] = temp_file_path
                self.file_info_map[file_identifier]["file_name"] = file_name
                self.file_info_map[file_identifier]["total_size"] = total_size
                self.file_info_map[file_identifier]["chunk_size"] = chunk_size
                self.file_info_map[file_identifier]["uploaded"] = []
            if chunk_number not in self.file_info_map[file_identifier]["uploaded"]:
                self.file_info_map[file_identifier]["uploaded"].append(chunk_number)
        finally:
            self.lock.release()
        return

    def is_finished(self, file_identifier):
        logger.debug("check is finished")
        self.lock.acquire()
        try:
            if file_identifier not in self.file_info_map:
                logger.debug("file identifier %s not in info map", file_identifier)
                return False

            total_size = self.file_info_map[file_identifier]["total_size"]
            chunk_size = self.file_info_map[file_identifier]["chunk_size"]
            pieces = int(math.ceil(float(total_size) / float(chunk_size)))
            for chunk_number in range(1, pieces):
                if chunk_number not in self.file_info_map[file_identifier]["uploaded"]:
                    logger.debug("file identifier %s, chunk number %d not in uploaded record, current uploaded %s",
                                 file_identifier, chunk_number, self.file_info_map[file_identifier]["uploaded"])
                    return False

            # rename when finish
            temp_file_path = self.file_info_map[file_identifier]["temp_file_path"]
            new_path = temp_file_path[:-5]  # len(".temp")
            os.rename(temp_file_path, new_path)
            logger.debug("file rename from %s to %s", temp_file_path, new_path)
        finally:
            self.lock.release()
        return True

    def is_uploaded(self, file_identifier, chunk_number):
        logger.debug("check is uploaded")
        self.lock.acquire()
        try:
            if file_identifier not in self.file_info_map:
                return False
            if chunk_number not in self.file_info_map[file_identifier]["uploaded"]:
                return False
        finally:
            self.lock.release()
        return True

    def remove(self, file_identifier):
        logger.debug("remove file_identifier")
        self.lock.acquire()
        try:
            if file_identifier in self.file_info_map:
                file_path = self.file_info_map[file_identifier]["temp_file_path"]
                if os.path.exists(file_path):
                    os.remove(file_path)
                del self.file_info_map[file_identifier]
        finally:
            self.lock.release()