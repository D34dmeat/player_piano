import json
import requests
from nose.tools import assert_equals

class ClientException(Exception):
    pass

class CRUD(object):
    def __init__(self, app_url="http://localhost:5000/api/"):
        self.app_url = app_url
        if not app_url.endswith("/"):
            self.app_url += "/"

    def post(self, query, data, check_status=True):
        r = requests.post(self.app_url + query,
                          data=json.dumps(data),
                          headers={'content-type': 'application/json'}
                  )
        if check_status:
            try:
                assert_equals(r.status_code, 201)
            except:
                raise ClientException(r.content.decode("utf-8"))
        return json.loads(r.content.decode("utf-8"))

    def get(self, query, check_status=True):
        r = requests.get(self.app_url + query,
                     headers={'content-type': 'application/json'}
                 )
        if check_status:
            try:
                assert_equals(r.status_code, 200)
            except:
                raise ClientException(r.content.decode("utf-8"))
        return json.loads(r.content.decode("utf-8"))

    def put(self, query, data, check_status=True):
        r = requests.put(self.app_url + query,
                         data=json.dumps(data),
                         headers={'content-type': 'application/json'}
                  )
        if check_status:
            try:
                assert_equals(r.status_code, 200)
            except:
                raise ClientException(r.content.decode("utf-8"))
        return json.loads(r.content.decode("utf-8"))

    def delete(self, query, check_status=True):
        r = requests.delete(self.app_url + query,
                      headers={'content-type': 'application/json'}
                  )
        if check_status:
            try:
                assert_equals(r.status_code, 204)
            except:
                raise ClientException(r.content.decode("utf-8"))
        return r.status_code == 204

