import logging
import os
import posixpath
import random
import threading
import urlparse
# from django.utils.translation import ugettext as _
import errno
import time
from core import resource
from core.http_client import HttpClient, HttpClientBase, WebHdfsException
from core.webhdfs_types import WebHdfsStat
from settings import settings

__author__ = 'haibin'

# os.environ['KRB5CCNAME'] = "/tmp/krb5cc_1000"
LOG = logging.getLogger("collie")


def _(content):
    return content

def safe_octal(octal_value):
  """
  safe_octal(octal_value) -> octal value in string

  This correctly handles octal values specified as a string or as a numeric.
  """
  try:
    return oct(octal_value)
  except TypeError:
    return str(octal_value)


class Hdfs(object):
  """
  An abstract HDFS proxy
  """

  @staticmethod
  def basename(path):
    return posixpath.basename(path)

  @staticmethod
  def dirname(path):
    return posixpath.dirname(path)

  @staticmethod
  def split(path):
    return posixpath.split(path)

  @staticmethod
  def join(first, *comp_list):
    return posixpath.join(first, *comp_list)

  @staticmethod
  def abspath(path):
    return posixpath.abspath(path)

  @staticmethod
  def normpath(path):
    res = posixpath.normpath(path)
    # Python normpath() doesn't eliminate leading double slashes
    if res.startswith('//'):
      return res[1:]
    return res

  @staticmethod
  def urlsplit(url):
    """
    Take an HDFS path (hdfs://nn:port/foo) or just (/foo) and split it into
    the standard urlsplit's 5-tuple.
    """
    i = url.find('://')
    if i == -1:
      # Not found. Treat the entire argument as an HDFS path
      return ('hdfs', '', posixpath.normpath(url), '', '')
    schema = url[:i]
    if schema not in ('hdfs', 'viewfs'):
      # Default to standard for non-hdfs
      return urlparse.urlsplit(url)
    url = url[i+3:]
    i = url.find('/')
    if i == -1:
      # Everything is netloc. Assume path is root.
      return (schema, url, '/', '', '')
    netloc = url[:i]
    path = url[i:]
    return (schema, netloc, posixpath.normpath(path), '', '')

  def listdir_recursive(self, path, glob=None):
    """
    listdir_recursive(path, glob=None) -> [ entry names ]

    Get directory entry names without stats, recursively.
    """
    paths = [path]
    while paths:
      path = paths.pop()
      if self.isdir(path):
        hdfs_paths = self.listdir_stats(path, glob)
        paths[:0] = [x.path for x in hdfs_paths]
      yield path

  def create_home_dir(self, home_path=None):
    if home_path is None:
      home_path = self.get_home_dir()

    if not self.exists(home_path):
      user = self.user
      try:
        try:
          self.setuser(self.superuser)
          self.mkdir(home_path)
          self.chmod(home_path, 0755)
          self.chown(home_path, user, user)
        except IOError:
          msg = 'Failed to create home dir ("%s") as superuser %s' %\
                (home_path, self.superuser)
          LOG.exception(msg)
          raise
      finally:
        self.setuser(user)

  def copyFromLocal(self, local_src, remote_dst, mode=0755):
    remote_dst = remote_dst.endswith(posixpath.sep) and remote_dst[:-1] or remote_dst
    local_src = local_src.endswith(posixpath.sep) and local_src[:-1] or local_src

    if os.path.isdir(local_src):
      self._copy_dir(local_src, remote_dst, mode)
    else:
      (basename, filename) = os.path.split(local_src)
      self._copy_file(local_src, self.isdir(remote_dst) and self.join(remote_dst, filename) or remote_dst)

  def _copy_dir(self, local_dir, remote_dir, mode=0755):
    self.mkdir(remote_dir, mode=mode)

    for f in os.listdir(local_dir):
      local_src = os.path.join(local_dir, f)
      remote_dst = self.join(remote_dir, f)

      if os.path.isdir(local_src):
        self._copy_dir(local_src, remote_dst, mode)
      else:
        self._copy_file(local_src, remote_dst)

  def _copy_file(self, local_src, remote_dst, chunk_size=1024 * 1024 * 64):
    if os.path.isfile(local_src):
      if self.exists(remote_dst):
        LOG.info(_('%(remote_dst)s already exists. Skipping.') % {'remote_dst': remote_dst})
        return
      else:
        LOG.info(_('%(remote_dst)s does not exist. Trying to copy.') % {'remote_dst': remote_dst})

      src = file(local_src)
      try:
        try:
          self.create(remote_dst, permission=0755)
          chunk = src.read(chunk_size)
          while chunk:
            self.append(remote_dst, chunk)
            chunk = src.read(chunk_size)
          LOG.info(_('Copied %s -> %s.') % (local_src, remote_dst))
        except:
          LOG.error(_('Copying %s -> %s failed.') % (local_src, remote_dst))
          raise
      finally:
        src.close()
    else:
      LOG.info(_('Skipping %s (not a file).') % local_src)

  def copyToLocal(self, remote_src, local_dst, mode=0755):
      local_dst = local_dst.endswith(posixpath.sep) and local_dst[:-1] or local_dst
      remote_src = remote_src.endswith(posixpath.sep) and remote_src[:-1] or remote_src

      if self.isdir(remote_src):
          self._copy_to_local_dir(remote_src, remote_src, mode)
      else:
          (basename, filename) = self.split(remote_src)
          self._copy_to_local_file(remote_src, os.path.isdir(local_dst) and os.path.join(local_dst, filename) or local_dst)

  def _copy_to_local_dir(self, remote_dir, local_dir, mode=0755):
      os.makedirs(local_dir, mode=mode)

      for f in self.listdir_stats(remote_dir):
          file_name = f.name
          remote_src = self.join(remote_dir, f)
          local_dst = os.path.join(local_dir, f)

          if f.isDir():
              self._copy_to_local_dir(remote_src, local_dst, mode)
          else:
              self._copy_to_local_file(remote_src, local_dst)

  def _copy_to_local_file(self, remote_src, local_dst, chunk_size=1024 * 1024 * 64):
      if self.isfile(remote_src):
          if os.path.exists(local_dst):
              LOG.info(_('%(local_dst)s already exists. Skipping.') % {'local_dst': local_dst})
              return
          else:
              LOG.info(_('%(local_dst)s does not exist. Trying to copy.') % {'local_dst': local_dst})

          local_dst = open(local_dst, "wb+")
          offset = 0
          try:
              chunk = self.read(remote_src, offset, chunk_size)
              while chunk:
                  local_dst.write(chunk)
                  offset += chunk_size
                  chunk = self.read(remote_src, offset, chunk_size)
              LOG.info(_('Copied %s -> %s.') % (remote_src, local_dst))
          except:
              LOG.error(_('Copying %s -> %s failed.') % (remote_src, local_dst))
              raise
          finally:
              local_dst.close()
      else:
          LOG.info(_('Skipping %s (not exist).') % remote_src)

  def mktemp(self, subdir='', prefix='tmp', basedir=None):
    """
    mktemp(prefix) ->  <temp_dir or basedir>/<subdir>/prefix.<rand>
    Return a unique temporary filename with prefix in the cluster's temp dir.
    """
    RANDOM_BITS = 64

    base = self.join(basedir or self._temp_dir, subdir)
    if not self.isdir(base):
      self.mkdir(base)

    while True:
      name = prefix + '.' + str(random.getrandbits(RANDOM_BITS))
      candidate = self.join(base, name)
      if not self.exists(candidate):
        return candidate

  def mkswap(self, filename, subdir='', suffix='swp', basedir=None):
    """
    mkswap(filename, suffix) ->  <temp_dir or basedir>/<subdir>/filename.<suffix>
    Return a unique temporary filename with prefix in the cluster's temp dir.
    """
    RANDOM_BITS = 64

    base = self.join(basedir or self._temp_dir, subdir)
    if not self.isdir(base):
      self.mkdir(base)

    candidate = self.join(base, "%s.%s" % (filename, suffix))
    return candidate


  def exists(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'exists'})

  def do_as_user(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'do_as_user'})

  def create(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'exists'})

  def append(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'append'})

  def read(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'read'})

  def mkdir(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'mkdir'})

  def isdir(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'isdir'})

  def isfile(self):
      raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'isfile'})

  def listdir_stats(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'listdir_stats'})

  def remove(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'remove'})

  def rmdir(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'rmdir'})

  def rmtree(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'rmtree'})

  def __stand_by_url__(self):
    raise NotImplementedError(_("%(function)s has not been implemented.") % {'function': 'standy'})

class WebHdfs(Hdfs):
  """
  WebHdfs implements the filesystem interface via the WebHDFS rest protocol.
  """
  DEFAULT_USER = ''  # desktop.conf.DEFAULT_USER.get()        # This should be the user running Hue
  TRASH_CURRENT = 'Current'

  ## can check by visiting website http://10.201.10.237:11201/webhdfs/v1 or http://10.201.10.236:11201/webhdfs/v1
  ## above 2 urls are HA supported
  ## if failed, can try another one
  def __init__(self,
               url1=settings.WEBHDFS_URL_1,
               url2=settings.WEBHDFS_URL_2,
               # fs_defaultfs="hdfs://aptst-yukangle",
               fs_defaultfs="",
               logical_name=None,
               hdfs_superuser=None,
               # security_enabled=False,
               security_enabled=True,
               temp_dir="/tmp"):
    self._url1 = url1
    self._url2 = url2
    self._superuser = hdfs_superuser
    self._security_enabled = security_enabled
    self._temp_dir = temp_dir
    self._fs_defaultfs = fs_defaultfs
    self._logical_name = logical_name

    self._client1 = self._make_client(self._url1, self._security_enabled)
    self._client2 = self._make_client(self._url2, self._security_enabled)
    self._root = HttpClient(self._client1, self._client2)

    # To store user info
    self._thread_local = threading.local()

    LOG.debug("Initializing Hadoop WebHdfs: %s, %s (security: %s, superuser: %s)" %
              (self._url1, self._url2, self._security_enabled, self._superuser))

  @classmethod
  def from_config(cls, hdfs_config):
    fs_defaultfs = hdfs_config.FS_DEFAULTFS.get()
    return cls(# url=_get_service_url(hdfs_config),
               url=settings.WEBHDFS_URL,
               fs_defaultfs=fs_defaultfs,
               security_enabled=hdfs_config.SECURITY_ENABLED.get(),
               temp_dir=hdfs_config.TEMP_DIR.get())

  def __str__(self):
    return "WebHdfs at %s" % self._url

  def _make_client(self, url, security_enabled):
    client = HttpClientBase(
        url, exc_class=WebHdfsException, logger=LOG)
    if security_enabled:
      client.set_kerberos_auth()
    return client

  @property
  def uri(self):
    return self._url

  @property
  def logical_name(self):
    return self._logical_name

  @property
  def fs_defaultfs(self):
    return self._fs_defaultfs

  @property
  def security_enabled(self):
    return self._security_enabled

  @property
  def superuser(self):
    if self._superuser is None:
      try:
        # The owner of '/' is usually the superuser
        sb = self.stats('/')
        self._superuser = sb.user
      except Exception, ex:
        LOG.exception('Failed to determine superuser of %s: %s' % (self, ex))
        self._superuser = settings.WEBHDFS_SUPERUSER  # DEFAULT_HDFS_SUPERUSER

    return self._superuser

  @property
  def user(self):
    try:
      return self._thread_local.user
    except AttributeError:
      return WebHdfs.DEFAULT_USER

  @property
  def trash_path(self):
    return self.join(self.get_home_dir(), '.Trash')

  @property
  def current_trash_path(self):
    return self.join(self.trash_path, self.TRASH_CURRENT)

  def _getparams(self):
    return {
      # "user.name" : WebHdfs.DEFAULT_USER,
      # "doas" : self.user
      "user.name": settings.WEBHDFS_USERNAME,
      # "doas": settings.WEBHDFS_DOAS
    }

  def setuser(self, user):
    """Set a new user. Return the current user."""
    curr = self.user
    self._thread_local.user = user
    return curr

  def listdir_stats(self, path, glob=None):
    """
    listdir_stats(path, glob=None) -> [ WebHdfsStat ]

    Get directory listing with stats.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    if glob is not None:
      params['filter'] = glob
    params['op'] = 'LISTSTATUS'
    json = self._root.get(path, params)
    filestatus_list = json['FileStatuses']['FileStatus']
    # return filestatus_list
    return [ WebHdfsStat(st, path) for st in filestatus_list ]

  def read(self, path, offset, length, bufsize=None):
    """
    read(path, offset, length[, bufsize]) -> data

    Read data from a file.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'OPEN'
    params['offset'] = long(offset)
    params['length'] = long(length)
    if bufsize is not None:
      params['bufsize'] = bufsize
    try:
      return self._root.get(path, params)
    except WebHdfsException, ex:
      if "out of the range" in ex.message:
          return ""
      if "HTTP Error 403: Forbidden" in ex.message:
          return ""
      raise ex

  # TODO
  def read_line(self, path):
      return ""

  def listdir(self, path, glob=None):
    """
    listdir(path, glob=None) -> [ entry names ]

    Get directory entry names without stats.
    """
    dirents = self.listdir_stats(path, glob)
    return [Hdfs.basename(x.path) for x in dirents]

  def exists(self, path):
    return self._stats(path) is not None

  def _stats(self, path):
    """This version of stats returns None if the entry is not found"""
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'GETFILESTATUS'
    try:
      print params
      json = self._root.get(path, params)
      return WebHdfsStat(json['FileStatus'], path)
    except WebHdfsException, ex:
      LOG.exception('Failed to get stats of path %s: %s' % (path, ex))
      print ex
      print ex.message
      if ex.server_exc == 'FileNotFoundException' or ex.code == 404 or ex._error.code == 404:
        return None
      raise ex

  @staticmethod
  def urlsplit(url):
    return Hdfs.urlsplit(url)

  def get_hdfs_path(self, path):
    return posixpath.join(self.fs_defaultfs, path.lstrip('/'))

  def append(self, path, data):
    """
    append(path, data)

    Append data to a given file.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'APPEND'
    self._invoke_with_redirect('POST', path, params, data)

  def create(self, path, overwrite=False, blocksize=None,
             replication=None, permission=None, data=None):
    """
    create(path, overwrite=False, blocksize=None, replication=None, permission=None)

    Creates a file with the specified parameters.
    `permission' should be an octal integer or string.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'CREATE'
    params['overwrite'] = overwrite and 'true' or 'false'
    if blocksize is not None:
      params['blocksize'] = long(blocksize)
    if replication is not None:
      params['replication'] = int(replication)
    if permission is not None:
      params['permission'] = safe_octal(permission)

    self._invoke_with_redirect('PUT', path, params, data)

  def isdir(self, path):
    sb = self._stats(path)
    if sb is None:
      return False
    return sb.isDir

  def isfile(self, path):
    sb = self._stats(path)
    if sb is None:
      return False
    return not sb.isDir

  def _invoke_with_redirect(self, method, path, params=None, data=None):
    """
    Issue a request, and expect a redirect, and then submit the data to
    the redirected location. This is used for create, write, etc.

    Returns the response from the redirected request.
    """
    next_url = None
    try:
      # Do not pass data in the first leg.
      self._root.invoke(method, path, params)
    except WebHdfsException, ex:
      # This is expected. We get a 307 redirect.
      # The following call may throw.
      next_url = self._get_redirect_url(ex)

    if next_url is None:
      raise WebHdfsException(
        _("Failed to create '%s'. HDFS did not return a redirect") % path)

    # Now talk to the real thing. The redirect url already includes the params.
    client = self._make_client(next_url, self.security_enabled)
    headers = {'Content-Type': 'application/octet-stream'}
    return resource.Resource(client).invoke(method, data=data, headers=headers)

  def _get_redirect_url(self, webhdfs_ex):
    """Retrieve the redirect url from an exception object"""
    try:
      # The actual HttpError (307) is wrapped inside
      http_error = webhdfs_ex.get_parent_ex()
      if http_error is None:
        raise webhdfs_ex

      if http_error.code not in (301, 302, 303, 307):
      # if http_error.response.status_code not in (301, 302, 303, 307):
        LOG.error("Response is not a redirect: %s" % webhdfs_ex)
        raise webhdfs_ex
      return http_error.headers.dict['location']
      # return http_error.response.headers['location']
    except Exception, ex:
      LOG.error("Failed to read redirect from response: %s (%s)" %
                (webhdfs_ex, ex))
      raise webhdfs_ex

  def remove(self, path, skip_trash=False):
    """Delete a file."""
    if skip_trash:
      self._delete(path, recursive=False)
    else:
      self._trash(path, recursive=False)

  def rmdir(self, path, skip_trash=False):
    """Delete a directory."""
    self.remove(path, skip_trash)

  def rmtree(self, path, skip_trash=False):
    """Delete a tree recursively."""
    if skip_trash:
      self._delete(path, recursive=True)
    else:
      self._trash(path, recursive=True)

  def _delete(self, path, recursive=False):
    """
    _delete(path, recursive=False)

    Delete a file or directory.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'DELETE'
    params['recursive'] = recursive and 'true' or 'false'
    result = self._root.delete(path, params)
    # This part of the API is nonsense.
    # The lack of exception should indicate success.
    if not result['boolean']:
      raise IOError(_('Delete failed: %s') % path)

  def _trash(self, path, recursive=False):
    """
    _trash(path, recursive=False)

    Move a file or directory to trash.
    Will create a timestamped directory underneath /user/<username>/.Trash.

    Trash must be enabled for this to work.
    """
    if not self.exists(path):
      raise IOError(errno.ENOENT, _("File %s not found") % path)

    if not recursive and self.isdir(path):
      raise IOError(errno.EISDIR, _("File %s is a directory") % path)

    if path.startswith(self.trash_path):
      raise IOError(errno.EPERM, _("File %s is already trashed") % path)

    # Make path (with timestamp suffix if necessary)
    base_trash_path = self.join(self._ensure_current_trash_directory(), path[1:])
    trash_path = base_trash_path
    while self.exists(trash_path):
      trash_path = base_trash_path + str(time.time())

    # Move path to trash path
    self.mkdir(self.dirname(trash_path))
    self.rename(path, trash_path)

  '''
  def get_content_summary(self, path):
    """
    get_content_summary(path) -> WebHdfsContentSummary
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'GETCONTENTSUMMARY'
    json = self._root.get(path, params)
    return WebHdfsContentSummary(json['ContentSummary'])

  def stats(self, path):
    """
    stats(path) -> WebHdfsStat
    """
    res = self._stats(path)
    if res is not None:
      return res
    raise IOError(errno.ENOENT, _("File %s not found") % path)

  def _ensure_current_trash_directory(self):
    """Create trash directory for a user if it doesn't exist."""
    if self.exists(self.current_trash_path):
      self.mkdir(self.current_trash_path)
    return self.current_trash_path


  def restore(self, path):
    """
    restore(path)

    The root of ``path`` will be /users/<current user>/.Trash/<timestamp>.
    Removing the root from ``path`` will provide the original path.
    Ensure parent directories exist and rename path.
    """
    if not path.startswith(self.trash_path):
      raise IOError(errno.EPERM, _("File %s is not in trash") % path)

    # Build original path
    original_path = []
    split_path = self.split(path)
    while split_path[0] != self.trash_path:
      original_path.append(split_path[1])
      split_path = self.split(split_path[0])
    original_path.reverse()
    original_path = self.join(posixpath.sep, *original_path)

    # move to original path
    # the path could have been expunged.
    if self.exists(original_path):
      raise IOError(errno.EEXIST, _("Path %s already exists.") % str(smart_str(original_path)))
    self.rename(path, original_path)

  def purge_trash(self):
    """
    purge_trash()

    Purge all trash in users ``trash_path``
    """
    for timestamped_directory in self.listdir(self.trash_path):
      self.rmtree(self.join(self.trash_path, timestamped_directory), True)

  def mkdir(self, path, mode=None):
    """
    mkdir(path, mode=None)

    Creates a directory and any parent directory if necessary.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'MKDIRS'
    if mode is not None:
      params['permission'] = safe_octal(mode)
    success = self._root.put(path, params)
    if not success:
      raise IOError(_("Mkdir failed: %s") % path)

  def rename(self, old, new):
    """rename(old, new)"""
    old = Hdfs.normpath(old)
    if not new.startswith('/'):
      new = Hdfs.join(Hdfs.dirname(old), new)
    new = Hdfs.normpath(new)
    params = self._getparams()
    params['op'] = 'RENAME'
    # Encode `new' because it's in the params
    params['destination'] = smart_str(new)
    result = self._root.put(old, params)
    if not result['boolean']:
      raise IOError(_("Rename failed: %s -> %s") %
                    (str(smart_str(old)), str(smart_str(new))))

  def rename_star(self, old_dir, new_dir):
    """Equivalent to `mv old_dir/* new"""
    if not self.isdir(old_dir):
      raise IOError(errno.ENOTDIR, _("'%s' is not a directory") % old_dir)
    if not self.exists(new_dir):
      self.mkdir(new_dir)
    elif not self.isdir(new_dir):
      raise IOError(errno.ENOTDIR, _("'%s' is not a directory") % new_dir)
    ls = self.listdir(old_dir)
    for dirent in ls:
      self.rename(Hdfs.join(old_dir, dirent), Hdfs.join(new_dir, dirent))

  def chown(self, path, user=None, group=None, recursive=False):
    """chown(path, user=None, group=None, recursive=False)"""
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'SETOWNER'
    if user is not None:
      params['owner'] = user
    if group is not None:
      params['group'] = group
    if recursive:
      for xpath in self.listdir_recursive(path):
        self._root.put(xpath, params)
    else:
      self._root.put(path, params)


  def chmod(self, path, mode, recursive=False):
    """
    chmod(path, mode, recursive=False)

    `mode' should be an octal integer or string.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'SETPERMISSION'
    params['permission'] = safe_octal(mode)
    if recursive:
      for xpath in self.listdir_recursive(path):
        self._root.put(xpath, params)
    else:
      self._root.put(path, params)

  def get_home_dir(self):
    """get_home_dir() -> Home directory for the current user"""
    params = self._getparams()
    params['op'] = 'GETHOMEDIRECTORY'
    res = self._root.get(params=params)
    return res['Path']


  def read(self, path, offset, length, bufsize=None):
    """
    read(path, offset, length[, bufsize]) -> data

    Read data from a file.
    """
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'OPEN'
    params['offset'] = long(offset)
    params['length'] = long(length)
    if bufsize is not None:
      params['bufsize'] = bufsize
    try:
      return self._root.get(path, params)
    except WebHdfsException, ex:
      if "out of the range" in ex.message:
        return ""
      raise ex


  def open(self, path, mode='r'):
    """
    DEPRECATED!
    open(path, mode='r') -> File object

    This exists for legacy support and backwards compatibility only.
    Please use read().
    """
    return File(self, path, mode)


  # e.g. ACLSPEC = user:joe:rwx,user::rw-
  def modify_acl_entries(self, path, aclspec):
    path = Hdfs.normpath(path)
    params = self._getparams()
    params['op'] = 'MODIFYACLENTRIES'
    params['aclspec'] = aclspec
    return self._root.put(path, params)


  def remove_acl_entries(self, path, aclspec):
      path = Hdfs.normpath(path)
      params = self._getparams()
      params['op'] = 'REMOVEACLENTRIES'
      params['aclspec'] = aclspec
      return self._root.put(path, params)


  def remove_default_acl(self, path):
      path = Hdfs.normpath(path)
      params = self._getparams()
      params['op'] = 'REMOVEDEFAULTACL'
      return self._root.put(path, params)


  def remove_acl(self, path):
      path = Hdfs.normpath(path)
      params = self._getparams()
      params['op'] = 'REMOVEACL'
      return self._root.put(path, params)


  def set_acl(self, path, aclspec):
      path = Hdfs.normpath(path)
      params = self._getparams()
      params['op'] = 'SETACL'
      params['aclspec'] = aclspec
      return self._root.put(path, params)


  def get_acl_status(self, path):
      path = Hdfs.normpath(path)
      params = self._getparams()
      params['op'] = 'GETACLSTATUS'
      return self._root.get(path, params)


  def copyfile(self, src, dst, skip_header=False):
    sb = self._stats(src)
    if sb is None:
      raise IOError(errno.ENOENT, _("Copy src '%s' does not exist") % src)
    if sb.isDir:
      raise IOError(errno.INVAL, _("Copy src '%s' is a directory") % src)
    if self.isdir(dst):
      raise IOError(errno.INVAL, _("Copy dst '%s' is a directory") % dst)

    offset = 0

    while True:
      data = self.read(src, offset, UPLOAD_CHUNK_SIZE.get())
      if offset == 0:
        if skip_header:
          n = data.index('\n')
          if n > 0:
            data = data[n + 1:]
        self.create(dst,
                    overwrite=True,
                    blocksize=sb.blockSize,
                    replication=sb.replication,
                    permission=oct(stat.S_IMODE(sb.mode)),
                    data=data)

      if offset != 0:
        self.append(dst, data)

      cnt = len(data)
      if cnt < UPLOAD_CHUNK_SIZE.get():
        break

      offset += cnt


  def copy_remote_dir(self, source, destination, dir_mode=0755, owner=None):
    if owner is None:
      owner = self.DEFAULT_USER
    self.do_as_user(owner, self.mkdir, destination, mode=dir_mode)
    self.do_as_user(owner, self.chmod, destination, mode=dir_mode) # To remove after HDFS-3491

    for stat in self.listdir_stats(source):
      source_file = stat.path
      destination_file = posixpath.join(destination, stat.name)
      if stat.isDir:
        self.copy_remote_dir(source_file, destination_file, dir_mode, owner)
      else:
        self.do_as_user(owner, self.copyfile, source_file, destination_file)
        self.do_as_superuser(self.chown, destination_file, owner, owner)


  def copy(self, src, dest, recursive=False, dir_mode=0755, owner=None):
    """
    Copy file, or directory, in HDFS to another location in HDFS.

    ``src`` -- The directory, or file, to copy from.
    ``dest`` -- the directory, or file, to copy to.
            If 'dest' is a directory that exists, copy 'src' into dest.
            If 'dest' is a file that exists and 'src' is a file, overwrite dest.
            If 'dest' does not exist, create 'src' as 'dest'.
    ``recursive`` -- Recursively copy contents of 'src' to 'dest'.
                 This is required for directories.
    ``dir_mode`` and ``owner`` are used to define permissions on the newly
    copied files and directories.

    This method will overwrite any pre-existing files that collide with what is being copied.
    Copying a directory to a file is not allowed.
    """
    if owner is None:
      owner = self.user

    src = self.abspath(src)
    dest = self.abspath(dest)

    if not self.exists(src):
      raise IOError(errno.ENOENT, _("File not found: %s") % src)

    if self.isdir(src):
      # 'src' is directory.
      # Skip if not recursive copy and 'src' is directory.
      if not recursive:
        LOG.debug("Skipping contents of %s" % src)
        return None

      # If 'dest' is a directory change 'dest'
      # to include 'src' basename.
      # create 'dest' if it doesn't already exist.
      if self.exists(dest):
        if self.isdir(dest):
          dest = self.join(dest, self.basename(src))
        else:
          raise IOError(errno.EEXIST, _("Destination file %s exists and is not a directory.") % dest)
      self.do_as_user(owner, self.mkdir, dest)
      self.do_as_user(owner, self.chmod, dest, mode=dir_mode)

      # Copy files in 'src' directory to 'dest'.
      self.copy_remote_dir(src, dest, dir_mode, owner)
    else:
      # 'src' is a file.
      # If 'dest' is a directory, then copy 'src' into that directory.
      # Other wise, copy to 'dest'.
      if self.exists(dest) and self.isdir(dest):
        self.copyfile(src, self.join(dest, self.basename(src)))
      else:
        self.copyfile(src, dest)
'''

  def get_home_dir(self):
    """get_home_dir() -> Home directory for the current user"""
    params = self._getparams()
    params['op'] = 'GETHOMEDIRECTORY'
    res = self._root.get(params=params)
    return res['Path']

  def get_delegation_token(self, renewer):
    """get_delegation_token(user) -> Delegation token"""
    # Workaround for HDFS-3988
    if self._security_enabled:
      self.get_home_dir()

    params = self._getparams()
    params['op'] = 'GETDELEGATIONTOKEN'
    params['renewer'] = renewer
    res = self._root.get(params=params)
    return res['Token']['urlString']


  def do_as_user(self, username, fn, *args, **kwargs):
    prev_user = self.user
    try:
      self.setuser(username)
      return fn(*args, **kwargs)
    finally:
      self.setuser(prev_user)


  def do_as_superuser(self, fn, *args, **kwargs):
    return self.do_as_user(self.superuser, fn, *args, **kwargs)


  def do_recursively(self, fn, path, *args, **kwargs):
    for stat in self.listdir_stats(path):
      try:
        if stat.isDir:
          self.do_recursively(fn, stat.path, *args, **kwargs)
        fn(stat.path, *args, **kwargs)
      except Exception:
        pass


# how to put local file to hdfs location
webhdfs = WebHdfs()


### Run Django Console.. ###
# from core.webhdfs import test
# test()
###
def test():
    local_src_file = "/tmp/cars"
    if not os.path.exists(local_src_file):
        local_src = open(local_src_file, "wb+")
        local_src.write("bmw\nbenz")
        local_src.close()

    remote_dst_file = "/user/h_sns/cars"
    try:
        webhdfs.remove(remote_dst_file, skip_trash=True)
        print webhdfs.read(remote_dst_file, 0, 1000)
    except:
        print "\nno remote file existed\n"

    webhdfs.copyFromLocal("/tmp/cars", "/user/h_sns/")
    # how to get hdfs file to local location

    remote_file_content = webhdfs.read("/user/h_sns/cars", 0, 1000)
    print "remote content: \n%s\n" % remote_file_content

    local_dst_file = "/home/haibin/cars"
    try:
        os.remove(local_dst_file)
    except:
        print "\nno local file existed\n"

    webhdfs.copyToLocal("/user/h_sns/cars", "/home/haibin")
    local_dst = open(local_dst_file)
    chunk = local_dst.read(1024 * 1024)
    print "local content : \n%s" % chunk

if __name__ == "__main__":
    for i in range(0, 3):
        test()

