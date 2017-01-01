from cloudshell.networking.sdn.flows.sdn_autoload_flow import SDNAutoloadFlow
from cloudshell.networking.sdn.autoload.sdn_generic_snmp_autoload import SDNGenericSNMPAutoload
from cloudshell.networking.devices.runners.autoload_runner import AutoloadRunner
from cloudshell.networking.sdn.commons import create_controller_handler
from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController



class SDNAutoloadRunner(AutoloadRunner):
    def __init__(self, logger, api, context, supported_os):
        super(SDNAutoloadRunner, self).__init__(logger, context, supported_os)
        self._logger = logger
        controller_params = create_controller_handler()
        controller_handler = SDNController(**controller_params)
        self._autoload_flow = SDNAutoloadFlow(controller_handler=controller_handler,\
                                              autoload_class=SDNGenericSNMPAutoload,
                                                logger=logger,
                                                resource_name=self._resource_name)


