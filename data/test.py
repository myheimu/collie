import json
import urllib2

__author__ = 'haibin'

server_host = 'http://127.0.0.1:8000'
cookie_sessionid = 'sessionid=r1b5krf5r4vujhenbgz3e3ubuwbc24on'

if __name__ == "__main__":
    # test hello world api
    opener = urllib2.build_opener()
    req = urllib2.Request(server_host + "/data/hello_world")
    req.add_header('Cookie', cookie_sessionid)
    req_response = urllib2.urlopen(req).read()
    req_response = json.loads(req_response)
    print req_response

    # test user_profile
    opener = urllib2.build_opener()
    req = urllib2.Request(server_host + "/data/user_profile")
    req.add_header('Cookie', cookie_sessionid)
    req_response = urllib2.urlopen(req).read()
    req_response = json.loads(req_response)
    print req_response