__author__ = "Luiza Nacshon"
__copyright__ = ""
__license__ = ""
__version__ = "1.0.0"
__email__ = "luiza.n@quali.com"
__status__ = "Development"

import json
import requests
from requests.auth import HTTPBasicAuth

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
        response = requests.put(url=self.url, data=json.dumps(flow_data), headers={'Content-Type': 'application/json'},auth=self.auth)


        if response.status_code != 201:
            raise Exception('controller connection handler', 'query response is empty')



