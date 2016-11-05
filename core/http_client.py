import cookielib
import json
import logging
import posixpath
import urllib
import urllib2
from django.utils.encoding import smart_str, iri_to_uri
from util.urllib2_kerberos import HTTPKerberosAuthHandler

__author__ = 'haibin'

LOG = logging.getLogger("collie")

class RestException(Exception):
  """
  Any error result from the Rest API is converted into this exception type.
  """
  def __init__(self, error):
    Exception.__init__(self, error)
    self._error = error
    self._code = None
    self._message = str(error)
    self._headers = {}

    # Get more information if urllib2.HTTPError.
    try:
      self._code = error.response.status_code
      self._headers = error.response.headers
      self._message = self._error.response.text
    except AttributeError:
      pass

  def __str__(self):
    res = self._message or ""
    if self._code is not None:
      res += " (error %s)" % self._code
    return res

  def get_parent_ex(self):
    if isinstance(self._error, Exception):
      return self._error
    return None

  @property
  def code(self):
    return self._code

  @property
  def message(self):
    return self._message


class WebHdfsException(RestException):
  def __init__(self, error):
    RestException.__init__(self, error)

    try:
      json_body = json.loads(self._message)['RemoteException']
      self.server_exc = json_body['exception']
      self._message = "%s: %s" % (self.server_exc, json_body['message'])
    except:
      # Don't mask the original exception
      self.server_exc = None


class HttpClientBase(object):
  """
  Basic HTTP client tailored for rest APIs.
  """
  def __init__(self, base_url, exc_class=None, logger=None):
    """
    @param base_url: The base url to the API.
    @param exc_class: An exception class to handle non-200 results.

    Creates an HTTP(S) client to connect to the Cloudera Manager API.
    """
    self._base_url = base_url.rstrip('/')
    self._exc_class = exc_class or RestException
    self._logger = logger or LOG
    self._headers = { }

    # Make a cookie processor
    cookiejar = cookielib.CookieJar()

    self._opener = urllib2.build_opener(
        urllib2.HTTPErrorProcessor(),
        urllib2.HTTPCookieProcessor(cookiejar))

  def set_kerberos_auth(self):
    """Set up kerberos auth for the client, based on the current ticket."""
    # self._session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
    authhandler = HTTPKerberosAuthHandler()
    self._opener.add_handler(authhandler)
    return self

  def set_headers(self, headers):
    """
    Add headers to the request
    @param headers: A dictionary with the key value pairs for the headers
    @return: The current object
    """
    self._headers = headers
    return self

  @property
  def base_url(self):
    return self._base_url

  @property
  def logger(self):
    return self._logger

  def _get_headers(self, headers):
    res = self._headers.copy()
    if headers:
      res.update(headers)
    return res

  def execute(self, http_method, path, params=None, data=None, headers=None):
    """
    Submit an HTTP request.
    @param http_method: GET, POST, PUT, DELETE
    @param path: The path of the resource. Unsafe characters will be quoted.
    @param params: Key-value parameter data.
    @param data: The data to attach to the body of the request.
    @param headers: The headers to set for this request.

    @return: The result of urllib2.urlopen()
    """
    # Prepare URL and params
    path = urllib.quote(smart_str(path))
    url = self._make_url(path, params)
    if http_method in ("GET", "DELETE"):
      if data is not None:
        self.logger.warn(
            "GET method does not pass any data. Path '%s'" % (path,))
        data = None

    # Setup the request
    request = urllib2.Request(url, data)
    # Hack/workaround because urllib2 only does GET and POST
    request.get_method = lambda: http_method

    headers = self._get_headers(headers)

    for k, v in headers.items():
      request.add_header(k, v)

    # Call it
    self.logger.debug("%s %s" % (http_method, url))
    try:
      return self._opener.open(request)
    except (urllib2.HTTPError, urllib2.URLError), ex:
      raise self._exc_class(ex)

  def _make_url(self, path, params):
    res = self._base_url
    if path:
      res += posixpath.normpath('/' + path.lstrip('/'))
    if params:
      param_str = urllib.urlencode(params)
      res += '?' + param_str
    return iri_to_uri(res)

class HTTPErrorProcessor(urllib2.HTTPErrorProcessor):
  """
  Python 2.4 only recognize 200 and 206 as success. It's broken. So we install
  the following processor to catch the bug.
  """
  def http_response(self, request, response):
    if 200 <= response.code < 300:
      return response
    return urllib2.HTTPErrorProcessor.http_response(self, request, response)

  https_response = http_response

class HttpClient(object):
  """
  Encapsulates a resource, and provides actions to invoke on it.
  """
  def __init__(self, client1, client2, relpath=""):
    """
    @param client: A Client object.
    @param relpath: The relative path of the resource.
    """
    self._client1 = client1
    self._client2 = client2
    self._client = self._client1
    self._path = relpath.strip('/')

  def _change_client(self):
    last_url = self._client.base_url
    if self._client.base_url == self._client1.base_url:
      self._client = self._client2
    else:
      self._client = self._client1
    print "change url %s to %s" % (last_url, self._client.base_url)

  @property
  def base_url(self):
    return self._client.base_url

  def _join_uri(self, relpath):
    if relpath is None:
      return self._path
    return self._path + posixpath.normpath('/' + relpath)

  def invoke(self, method, relpath=None, params=None, data=None, headers=None):
    """
    Invoke an API method.
    @return: Raw body or JSON dictionary (if response content type is JSON).
    """
    path = self._join_uri(relpath)
    resp = self._client.execute(method,
                                path,
                                params=params,
                                data=data,
                                headers=headers)
    try:
      body = resp.read()
    except Exception, ex:
      raise Exception("Command '%s %s' failed: %s" %
                      (method, path, ex))

    self._client.logger.debug(
        "%s Got response: %s%s" %
        (method, body[:32], len(body) > 32 and "..." or ""))

    # Is the response application/json?
    if len(body) != 0 and \
          resp.info().getmaintype() == "application" and \
          resp.info().getsubtype() == "json":
      try:
        json_dict = json.loads(body)
        return json_dict
      except Exception, ex:
        self._client.logger.exception('JSON decode error: %s' % (body,))
        raise ex
    else:
      return body


  def get(self, relpath=None, params=None, headers=None):
    """
    Invoke the GET method on a resource.
    @param relpath: Optional. A relative path to this resource's path.
    @param params: Key-value data.

    @return: A dictionary of the JSON result.
    """
    try:
        return self.invoke("GET", relpath, params, headers=headers)
    except Exception, ex:
        print "hit exception when get %s, ex: %s" % (relpath, ex)
        if "HTTP Error 403: Forbidden" in ex.message:
            self._change_client()
            return self.invoke("GET", relpath, params, headers=headers)
        if "Connection timed out" in ex.message:
            self._change_client()
            return self.invoke("GET", relpath, params, headers=headers)
        raise ex


  def delete(self, relpath=None, params=None):
    """
    Invoke the DELETE method on a resource.
    @param relpath: Optional. A relative path to this resource's path.
    @param params: Key-value data.

    @return: A dictionary of the JSON result.
    """
    try:
        return self.invoke("DELETE", relpath, params)
    except Exception, ex:
        print "hit exception when delete %s, ex: %s" % (relpath, ex)
        if "HTTP Error 403: Forbidden" in ex.message:
            self._change_client()
            return self.invoke("DELETE", relpath, params)
        if "Connection timed out" in ex.message:
            self._change_client()
            return self.invoke("DELETE", relpath, params)
        raise ex


  def post(self, relpath=None, params=None, data=None, contenttype=None):
    """
    Invoke the POST method on a resource.
    @param relpath: Optional. A relative path to this resource's path.
    @param params: Key-value data.
    @param data: Optional. Body of the request.
    @param contenttype: Optional.

    @return: A dictionary of the JSON result.
    """
    try:
        return self.invoke("POST", relpath, params, data, self._make_headers(contenttype))
    except Exception, ex:
        print "hit exception when post %s, ex: %s" % (relpath, ex)
        if "HTTP Error 403: Forbidden" in ex.message:
            self._change_client()
            return self.invoke("POST", relpath, params, data, self._make_headers(contenttype))
        if "Connection timed out" in ex.message:
            self._change_client()
            return self.invoke("POST", relpath, params, data, self._make_headers(contenttype))
        raise ex


  def put(self, relpath=None, params=None, data=None, contenttype=None):
    """
    Invoke the PUT method on a resource.
    @param relpath: Optional. A relative path to this resource's path.
    @param params: Key-value data.
    @param data: Optional. Body of the request.
    @param contenttype: Optional.

    @return: A dictionary of the JSON result.
    """
    try:
        return self.invoke("PUT", relpath, params, data,
                           self._make_headers(contenttype))
    except Exception, ex:
        print "hit exception when put %s, ex: %s" % (relpath, ex)
        if "HTTP Error 403: Forbidden" in ex.message:
            self._change_client()
            return self.invoke("PUT", relpath, params, data, self._make_headers(contenttype))
        if "Connection timed out" in ex.message:
            self._change_client()
            return self.invoke("PUT", relpath, params, data, self._make_headers(contenttype))
        raise ex


  def _make_headers(self, contenttype=None):
    if contenttype:
      return { 'Content-Type': contenttype }
    return None

