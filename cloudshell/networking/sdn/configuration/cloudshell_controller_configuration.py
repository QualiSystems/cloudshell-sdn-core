from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController
from cloudshell.shell.core.context_utils import get_attribute_by_name_wrapper, \
    get_decrypted_password_by_attribute_name_wrapper, get_resource_address

CONTROLLER_INIT_PARAMS = {'ip': get_resource_address,
                          'port': get_attribute_by_name_wrapper('Port'),
                          'username': get_attribute_by_name_wrapper('User'),
                          'password': get_decrypted_password_by_attribute_name_wrapper('Password'),
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
