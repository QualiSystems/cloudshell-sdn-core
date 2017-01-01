__author__ = "Luiza Nacshon"
__copyright__ = ""
__license__ = ""
__version__ = "1.0.0"
__email__ = "luiza.n@quali.com"
__status__ = "Development"

import json
import requests
import inject
from requests.auth import HTTPBasicAuth
from cloudshell.core.logger.qs_logger import get_qs_logger
Logger = get_qs_logger()
class SDNController(object):


    def __init__(self,ip,port,username,password,path,container,utl_prefix):


        self.attributes = {'ip':ip,
                      'port':port,
                      'username':username,
                      'password':password,
                      'path':path,
                      'container':container,
                      'utl_prefix':utl_prefix}

        self._base_url = None
        self.url = None
        self.auth = None
        self.build_credentials()

        self._logger = Logger



    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = inject.instance('logger')
            except:
                raise Exception('SDNRoutingResolution', 'Logger is none or empty')
        return self._logger

    def build_credentials(self):
        self.auth = HTTPBasicAuth(self.attributes['username'],self.attributes['password'])

    def get_query(self, northbound_api_component, query):
        data = dict()
        self._base_url = self.attributes['utl_prefix'] + self.attributes['ip'] + ':' + \
                         self.attributes['port'] + self.attributes['path']

        self.url = self._base_url + northbound_api_component + '/' + self.attributes['container'] + query

        response = requests.get(url=self.url, auth=self.auth)

        if response.status_code == 200:
            data = response.json()
            print data

        else:
            raise Exception('controller connection handler', 'query response is empty')

        return data


    def push_static_flow(self,switch_id,flow_name,flow_data):
        self._base_url = self.attributes['utl_prefix'] + self.attributes['ip'] + ':' + \
                         self.attributes['port'] + self.attributes['path']
        self.url = self._base_url + 'flowprogrammer/default/node/OF/' + switch_id + '/staticFlow/' + flow_name

        self.logger.info('Pushing To Controller {0}'.format(self.url))
        response = requests.put(url=self.url, data=json.dumps(flow_data), headers={'Content-Type': 'application/json'},auth=self.auth)

        self.logger.info('Push Status {0}'.format(response.status_code))
        if response.status_code == 400:
            raise Exception('controller connection handler', 'query response is empty')



        return response.content