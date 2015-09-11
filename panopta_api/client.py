from httplib2 import Http
from os.path import join
from urllib import urlencode
from urlparse import urljoin
import json
import logging
import logging.handlers
import socket


class Client:
    LOG_INFO = logging.INFO
    LOG_DEBUG = logging.DEBUG

    def __init__(self,
                 token,
                 host='https://api2.panopta.com/',
                 version=2,
                 log_level=LOG_INFO,
                 log_path="."):

        self.token = token
        self.base_url = urljoin(host, 'v' + str(version))
        self.version = version
        self.log_level = log_level
        self.log_path = log_path
        self.headers = {
            'Authorization': 'ApiKey %s' % self.token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.logger = logging.getLogger('Panopta API')
        log_handler = logging.handlers.TimedRotatingFileHandler(join(self.log_path, "panopta_api.log"),
                                                                when='d',
                                                                interval=1,
                                                                backupCount=14)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)
        self.logger.setLevel(self.log_level)

    def _get_response(self, status_code, status_reason, content, headers):
        if not headers:
            headers = {"status": status_code}

        return {
            'status_code': status_code,
            'status_reason': status_reason,
            'response_data': content or {},
            'response_headers': headers
        }

    def _request(self, resource_uri, method, data, headers):
        resource_path = ("%s/%s" % (self.base_url, resource_uri.strip("/"))).strip("?")
        headers.update(self.headers)

        #-- Send request

        self.logger.info('%s %s' % (method, resource_path))

        try:
            client = Http(disable_ssl_certificate_validation=True)
            resp, content = client.request(uri=resource_path, method=method, body=data, headers=headers)
        except Exception, err:
            self.logger.error(str(err))
            return self._get_response("0", str(err), None, None)

        try: content = json.loads(content)
        except: content = {}

        #-- Log request

        try: data = json.loads(data)
        except: data = {}

        log_data = {
            'resource_path': resource_path,
            'method': method,
            'request_headers': headers,
            'request_data': data,
            'response_headers': resp,
            'response_body': content
        }
        self.logger.debug(json.dumps(log_data, indent=2, sort_keys=True))

        #-- Prepare result

        status_code = resp['status']
        if status_code in ['200', '201', '204']:
            status_reason = 'success'
        else:
            reason = resp.get('errormessage', None)
            if reason:
                status_reason = 'error: %s' % reason
            else:
                status_reason = 'error'

        return self._get_response(status_code, status_reason, content, resp)

    def get(self, resource_uri, query_params={}, headers={}):
        return self._request("%s?%s" % (resource_uri, urlencode(query_params)), "GET", None, headers)

    def post(self, resource_uri, request_data={}, headers={}):
        return self._request(resource_uri, "POST", json.dumps(request_data), headers)

    def put(self, resource_uri, request_data={}, headers={}):
        return self._request(resource_uri, "PUT", json.dumps(request_data), headers)

    def delete(self, resource_uri, headers={}):
        return self._request(resource_uri, "DELETE", None, headers)
