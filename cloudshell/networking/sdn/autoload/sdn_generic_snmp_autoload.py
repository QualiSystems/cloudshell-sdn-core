import re
import inject
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.networking.autoload.networking_autoload_resource_attributes import NetworkingStandardRootAttributes
from cloudshell.networking.sdn.configuration.cloudshell_controller_configuration import CONTROLLER_HANDLER
from cloudshell.shell.core.driver_context import AutoLoadAttribute
class SDNGenericSNMPAutoload():

    def __init__(self, controller_handler=None, logger=None, vendor='ODL-Hellium'):
        """Basic init with  handler and logger

        :param snmp_handler:
        :param logger:
        :return:
        """


        self._controller = controller_handler


        self.port_list = []

        self.relative_path = {}


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
        self.logger.info('Starting huawei SNMP discovery process')
        self.get_controller_properies()
        self.load_huawei_mib()
        self._get_device_details()
        self.snmp.load_mib(['HUAWEI-PORT-MIB'])
        self._load_snmp_objects_and_tables()


        if len(self.chassis_list) < 1:
            self.logger.error('Entity table error, no chassis found')
            return AutoLoadDetails(list(), list())

        for chassis in self.chassis_list:
            if chassis not in self.exclusion_list:
                chassis_id = self._get_resource_id(chassis)
                if chassis_id == '-1':
                    chassis_id = '0'
                self.relative_path[chassis] = chassis_id

        self._filter_lower_bay_containers()
        self.get_module_list()
        self.add_relative_paths()
        self._get_chassis_attributes(self.chassis_list)
        self._get_ports_attributes()
        self._get_module_attributes()
        self._get_power_ports()
        self._get_port_channels()

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



    def get_controller_properies(self):
        data =  self.controller.get_query('controllermanager','/properties')

        system_name = data['properties'].get('name')
        mac_address = data['properties'].get('macAddress')

        self.logger.info('Load Controller Attributes:')
        result = {'system_name': system_name,
                  'vendor': self.vendor,
                  'model': '',
                  'location': '',
                  'contact': 'ODL',
                  'version': ''}

        root = NetworkingStandardRootAttributes(**result)

        setattr(root,'mac_address', AutoLoadAttribute('', 'Mac Address', mac_address))

        self.attributes.extend(root.get_autoload_resource_attributes())
        self.logger.info('Load controller Attributes completed.')


    def get_edge_switches(self):pass
    def get_edge_switches_ports(self):pass



    def _filter_lower_bay_containers(self):

        upper_container = None
        lower_container = None
        containers = self.entity_mib_table.filter_by_column('Class', "container").sort_by_column('ParentRelPos').keys()
        for container in containers:
            vendor_type = self.snmp.get_property('ENTITY-MIB', 'entPhysicalVendorType', container)
            if 'uppermodulebay' in vendor_type.lower():
                upper_container = container
            if 'lowermodulebay' in vendor_type.lower():
                lower_container = container
        if lower_container and upper_container:
            child_upper_items_len = len(self.entity_mib_table.filter_by_column('ContainedIn', str(upper_container)
                                                                           ).sort_by_column('ParentRelPos').keys())
            child_lower_items = self.entity_mib_table.filter_by_column('ContainedIn', str(lower_container)
                                                                   ).sort_by_column('ParentRelPos').keys()
            for child in child_lower_items:
                self.entity_mib_table[child]['entPhysicalContainedIn'] = upper_container
                self.entity_mib_table[child]['entPhysicalParentRelPos'] = str(child_upper_items_len + int(
                    self.entity_mib_table[child]['entPhysicalParentRelPos']))



    def _add_resource(self, resource):
        """Add object data to resources and attributes lists

        :param resource: object which contains all required data for certain resource
        """

        self.resources.append(resource.get_autoload_resource_details())
        self.attributes.extend(resource.get_autoload_resource_attributes())





    def _filter_entity_table(self, raw_entity_table):
        """Filters out all elements if their parents, doesn't exist, or listed in self.exclusion_list

        :param raw_entity_table: entity table with unfiltered elements
        """

        elements = raw_entity_table.filter_by_column('ContainedIn').sort_by_column('ParentRelPos').keys()
        for element in reversed(elements):
            parent_id = int(self.entity_mib_table[element]['entPhysicalContainedIn'])

            if parent_id not in raw_entity_table or parent_id in self.exclusion_list:
                self.exclusion_list.append(element)


    def _get_device_details(self):
        """Get root element attributes

        """

        self.logger.info('Start loading Switch Attributes')
        result = {'system_name': self.sys_name,
                  'vendor': self.vendor,
                  'model': self._get_device_model(),
                  'location': self.sys_location,
                  'contact': self.sys_contact,
                  'version': ''}
        software_dscription = self.sys_descr
        print software_dscription
        match_version = re.search('Version\s+(?P<software_version>\S+)\S*\s+',
                                  software_dscription)
        if match_version:
            result['version'] = match_version.groupdict()['software_version'].replace(',', '')

        root = NetworkingStandardRootAttributes(**result)
        self.attributes.extend(root.get_autoload_resource_attributes())
        self.logger.info('Finished Loading Switch Attributes')



    def _get_device_model(self):
        """Get device model form snmp SNMPv2 mib

        :return: device model
        :rtype: str
        """

        result = ''
        match_name = re.search(r'::(?P<model>\S+$)', self.snmp_object_id)
        if match_name:
            result = match_name.groupdict()['model'].capitalize()
        return result


