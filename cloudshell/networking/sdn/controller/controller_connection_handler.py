import json
import requests
from requests.auth import HTTPBasicAuth
from cloudshell.shell.core.context_utils import get_attribute_by_name_wrapper, get_resource_address, \
    get_decrypted_password_by_attribute_name_wrapper,get_resource_context_attribute,get_resource_port

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

    def build_connection(self, northbound_api_component, query):

        self.build_request_url(northbound_api_component, query)


    def build_request_url(self, northbound_api_component, query):

        self._base_url = self.attributes['utl_prefix'] + self.attributes['hostname'] + ':' + \
                         self.attributes['port'] + self.attributes['path']

        self.url = self._base_url + northbound_api_component + '/' + self.attributes['container'] + query

    def build_credentials(self):
        self.auth = HTTPBasicAuth(self.attributes['username'],self.attributes['password'])

