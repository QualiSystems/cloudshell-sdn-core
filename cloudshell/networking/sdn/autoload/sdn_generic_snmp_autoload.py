__author__ = "Luiza Nacshon"
__copyright__ = ""
__license__ = ""
__version__ = "1.0.0"
__email__ = "luiza.n@quali.com"
__status__ = "Development"

import re
import inject
import random
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.networking.autoload.networking_autoload_resource_attributes import NetworkingStandardRootAttributes
from cloudshell.networking.sdn.configuration.cloudshell_controller_configuration import CONTROLLER_HANDLER
from cloudshell.shell.core.driver_context import AutoLoadAttribute
from cloudshell.networking.autoload.networking_autoload_resource_structure import Port, Module,Chassis
from cloudshell.networking.sdn.resolution.topology_resolution import SDNTopologyResolution

class SDNGenericSNMPAutoload():
    def __init__(self, controller_handler=None,logger=None, vendor='ODL-Hellium'):

        self._controller = controller_handler
        self.topology = SDNTopologyResolution(self.controller)


        self.port_list = []

        self.relative_path = {}
        self.resource_id = {}

        self.switches_list = []
        self.leaf_switches_list = []
        self.resources = list()
        self.attributes = list()

        self.vendor = vendor

        self._logger = logger
        self._excluded_models = []


    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = inject.instance('logger')
            except:
                raise Exception('SDNAutoload', 'Logger is none or empty')
        return self._logger


    @property
    def controller(self):
        if self._controller is None:
            try:
                self._controller = inject.instance(CONTROLLER_HANDLER)
            except:
                raise Exception('SDNAutoload', 'controller handler is none or empty')
        return self._controller



    def discover(self):
        """Load device structure and attributes: chassis, modules, submodules, ports, port-channels and power supplies

        :return: AutoLoadDetails object
        """

        self.logger.info('*'*10)
        self.logger.info('Starting SDN SNMP Process')
        self.get_controller_details()
        #self.get_controller_properies()
        self.get_leaf_switches_list()
        self.get_switches_ports_dict()
        self.build_relative_path()
        self.add_relative_paths()
        self._get_ports_attributes()
        self._get_switches_attributes()


        result = AutoLoadDetails(resources=self.resources, attributes=self.attributes)

        self.logger.info('*'*10)
        self.logger.info('Discover completed. The following Structure have been loaded:' +
                          '\nModel, Name, Relative Path, Uniqe Id')

        for resource in self.resources:
            self.logger.info('{0},\t\t{1},\t\t{2},\t\t{3}'.format(resource.model, resource.name,
                                                                   resource.relative_address, resource.unique_identifier))
        self.logger.info('------------------------------')
        for attribute in self.attributes:
            self.logger.info('{0},\t\t{1},\t\t{2}'.format(attribute.relative_address, attribute.attribute_name,
                                                           attribute.attribute_value))

        self.logger.info('*'*10)
        self.logger.info('SNMP discovery Completed')

        return result

    def get_controller_details(self):
        """Get root element attributes

        """

        self.logger.info('Load Controller Attributes:')
        result = {'system_name': '',
                  'vendor': self.vendor,
                  'location': '',
                  'contact': 'ODL',
                  'version': ''}


        root = NetworkingStandardRootAttributes(**result)

        #setattr(root,'mac_address', AutoLoadAttribute('', 'Mac Address', mac_address))

        self.attributes.extend(root.get_autoload_resource_attributes())
        self.logger.info('Load controller Attributes completed.')
    '''
    def get_controller_properies(self):

        self.logger.info('Start loading Controller properties')

        self.relative_path['controller'] = 0
        controller_details_map = {
            'chassis_model': '',
            'serial_number': '',
            'name': 'ODL Controller',
            'model': 'Generic ODL Controller'
        }

        relative_path = '{0}'.format(0)
        chassis_object = Chassis(relative_path='0', **controller_details_map)
        self._add_resource(chassis_object)

        self.logger.info('Load controller Attributes completed.')
    '''
    def get_leaf_switches_list(self):
        self.leaf_switches_list = self.topology.get_leaf_switches()

    def get_switches_ports_dict(self):
        self.port_list = self.topology.get_switches_ports()


    def uniqueid(self):
        seed = random.getrandbits(32)
        while True:
            yield seed
            seed += 1

    def build_relative_path(self):
        unique_sequence = self.uniqueid()
        for index, switch in enumerate(self.leaf_switches_list, start=1):
            self.resource_id[switch] = int(next(unique_sequence))
            self.relative_path[switch] = self.resource_id[switch]
        for dedicated_switch in self.port_list:
            for index, port in enumerate(self.port_list[dedicated_switch], start=1):
                self.resource_id[port] = int(next(unique_sequence))
                if self.resource_id.get(dedicated_switch) is not None:
                    self.relative_path[port] = self.resource_id.get(dedicated_switch)

    def add_relative_paths(self):

        port_list = self.port_list
        switches_list = self.leaf_switches_list

        #for switch in switches_list:
        #    self.relative_path[switch] = str(self.relative_path[switch]) + '/' + str(self.resource_id[switch])

        for dedicated_switch in port_list:
            for port in port_list[dedicated_switch]:
                if (self.relative_path.get(port)):
                    if not type(self.relative_path[port])==str:
                        self.relative_path[port] = str(self.relative_path[port]) + '/' + str(self.resource_id[port])

    def _get_ports_attributes(self):

        self.logger.info('Load Ports:')
        seen = list()
        for dedicated_switch in self.port_list:
            for port in self.port_list[dedicated_switch]:
                if "-" in port:

                    interface_name = port.split("-")[1]
                else:
                    interface_name = port

                if interface_name == '':
                    continue

                attribute_map = {'l2_protocol_type': 1,
                                 'mac': '',
                                 'mtu': 2,
                                 'bandwidth': int(self.port_list[dedicated_switch][port]['bandwidth']),
                                 'description': '',
                                 'adjacent': '',
                                 'duplex': 'Full', 'auto_negotiation': 'False'}
                if (self.relative_path.get(port) and port not in seen):
                    seen.append(port)
                    port_object = Port(name=interface_name, relative_path=self.relative_path[port], **attribute_map)
                    self._add_resource(port_object)
                    self.logger.info('Added ' + interface_name + ' Port')
        self.logger.info('Load port completed.')

    def _get_switches_attributes(self):

        self.logger.info('Start loading Switches')
        for switch in self.leaf_switches_list:
            switch_id = self.relative_path[switch]
            switch_index = self.resource_id[switch]
            #'module_model': '',
            #'version': '',
            #'serial_number': switch_index
            module_details_map = {

            }


            switch_name = 'SDN Switch {0}'.format(switch_index)
            model = 'OpenVSwitch'
            #switch = 'SDN Switch'
            switch_object = Module(name=switch_name, model=model, relative_path=switch_id, **module_details_map)
            self._add_resource(switch_object)

        self.logger.info('Load switches completed.')


    def _add_resource(self, resource):
        """Add object data to resources and attributes lists

        :param resource: object which contains all required data for certain resource
        """

        self.resources.append(resource.get_autoload_resource_details())
        self.attributes.extend(resource.get_autoload_resource_attributes())
