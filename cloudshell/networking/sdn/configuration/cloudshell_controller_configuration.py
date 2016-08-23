from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController
from cloudshell.networking.sdn.topology.topology_resolution import SDNTopologyResolution
from cloudshell.shell.core.context_utils import get_attribute_by_name_wrapper, get_resource_address,get_resource_port

CONTROLLER_INIT_PARAMS = {'ip': get_resource_address,
              'port': get_resource_port,
              'username': get_attribute_by_name_wrapper('User'),
              'password': get_attribute_by_name_wrapper('Password'),
              'path': '/controller/nb/v2/',
              'container': 'default',
              'utl_prefix': 'http://'}


def create_controller_handler():
    kwargs = {}
    for key, value in CONTROLLER_INIT_PARAMS.iteritems():
        if callable(value):
            kwargs[key] = value()
        else:
            kwargs[key] = value
    return SDNController(**kwargs)


CONTROLLER_HANDLER = create_controller_handler
TOPLOGY_HANDLER = SDNTopologyResolution
