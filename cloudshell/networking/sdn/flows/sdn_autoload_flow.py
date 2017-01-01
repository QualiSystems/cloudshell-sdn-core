#!/usr/bin/python
# -*- coding: utf-8 -*-
from cloudshell.networking.devices.flows.action_flows import BaseFlow
from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController

class SDNAutoloadFlow(BaseFlow):
    def __init__(self, controller_handler, logger, resource_name, autoload_class):
        super(SDNAutoloadFlow, self).__init__(controller_handler, logger)
        self._resource_name = resource_name
        self._sdn_autoload_class = autoload_class


    def execute_flow(self, bool_enable_snmp, bool_disable_snmp, snmp_parameters, supported_os):
        """Facilitate SNMP autoload, enable and disable SNMP if needed.

        :param bool_enable_snmp: bool Enable SNMP Attribute
        :param bool_disable_snmp: bool Disable SNMP Attribute
        :param SNMPParameters snmp_parameters: snmp parameters class
        :param supported_os: supported os regexp
        :return: AutoloadDetails
        """
        result = self.run_autoload(snmp_parameters, supported_os)

        return result

    def run_autoload(self, controller_parameters, supported_os):
        """Executes device autoload discovery

        :param SNMPParameters snmp_parameters: snmp parameters class
        :param supported_os: supported os regexp
        :return: AutoloadDetails
        """

        controller_handler = SDNController()
        #QualiSnmp(snmp_parameters, self._logger)
        snmp_command_actions = self._sdn_autoload_class(controller_handler=controller_handler,
                                                          logger=self._logger,
                                                          supported_os=supported_os,
                                                          resource_name=self._resource_name)
        return snmp_command_actions.discover()
