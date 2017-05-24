import os
import shutil
import inject
import json

from cloudshell.networking.sdn.configuration.cloudshell_controller_configuration import CONTROLLER_HANDLER
from cloudshell.networking.sdn.resolution.topology_resolution import SDNTopologyResolution


class InstallStaticFlows(object):
    def __init__(self, controller_handler=None, logger=None):

        self._controller = controller_handler
        self._logger = logger
        self.route_resolution = SDNTopologyResolution(self.controller, self._logger)

    @property
    def logger(self):
        if self._logger is None:
            self._logger = inject.instance('logger')
        return self._logger

    @property
    def controller(self):
        if self._controller is None:
            self._controller = inject.instance(CONTROLLER_HANDLER)

        return self._controller

    def initialize_folder(self):
        working_dir = os.path.dirname(os.path.abspath(__file__))
        if (os.path.isdir(working_dir + "/installed_flows")):

            shutil.rmtree(working_dir + "/installed_flows")
            os.makedirs(working_dir + "/installed_flows")
        else:
            os.makedirs(working_dir + "/installed_flows")

    def build_flow(self, nodeid, flowname, ethertype='', destip='', srcip='', ipcos='', ipprot='',
                   dst_port=None, outdstmac=None, vlan='', src_port=None, actions_list=list(), priority=500):
        newflow = dict()

        newflow['name'] = flowname
        newflow['installInHw'] = 'true'
        newflow['node'] = {u'id': nodeid, u'type': u'OF'}
        if (destip != ''): newflow['nwDst'] = destip
        if (srcip != ''): newflow['nwSrc'] = srcip
        if (ethertype != ''): newflow['etherType'] = ethertype
        if (ipcos != ''): newflow['tosBits'] = ipcos
        if (ipprot != ''): newflow['protocol'] = ipprot
        if (vlan != ''): newflow['vlanId'] = vlan
        if (src_port): newflow['ingressPort'] = src_port
        newflow['priority'] = priority
        node = dict()
        node['id'] = nodeid
        node['type'] = 'OF'
        newflow['node'] = node
        if (dst_port): actions_list.append('OUTPUT=%s' % str(dst_port))
        # if (outdstmac): actions_list.append('SET_DL_DST=%s'%str(outdstmac))
        newflow['actions'] = actions_list

        return newflow

    def static_flow_pusher(self, flow_name, switch_id, port):

        self.logger.info('*' * 10)
        self.logger.info('Start Pushing Static Flows')

        new_flow = self.build_flow(nodeid=switch_id, flowname=flow_name, src_port=port, ethertype="0x800",
                                   outdstmac='', actions_list=["CONTROLLER"], priority=650)
        self.logger.info('{0},\t\t{1},\t\t{2}'.format(switch_id, flow_name,
                                                      port))

        response = self.controller.push_static_flow(switch_id, flow_name, new_flow)
        self.save_installed_flow_into_file(switch_id, port)
        route, dst_switch, dst_port = self.return_path_if_path_exists(switch_id)
        if (len(route) > 0):
            self.send_route_to_ctrl(switch_id, port, dst_switch, dst_port, route)
        if (dst_switch != ''):
            switch_id = dst_switch
            port = dst_port
            route, dst_switch, dst_port = self.return_path_if_path_exists(switch_id)
            if (len(route) > 0):
                self.send_route_to_ctrl(switch_id, port, dst_switch, dst_port, route)
        return response

    def remove_static_files_folder(self):
        working_dir = os.path.dirname(os.path.abspath(__file__))
        installed_flows_folder = working_dir + "/installed_flows"
        if os.path.isdir(installed_flows_folder):
            shutil.rmtree(installed_flows_folder)

    def delete_static_flow(self, flow_name, switch_id, port):
        self.logger.info("Deleting flow {} for {}p{}...".format(flow_name, switch_id, port))
        self.controller.delete_flow(src_switch=switch_id, flow_name=flow_name)
        self.controller.delete_route(src_switch=switch_id, src_switch_port=port)
        self.logger.info("Flow {} for {}p{} was successfully deleted".format(flow_name, switch_id, port))

    def save_installed_flow_into_file(self, switch_id, port):

        working_dir = os.path.dirname(os.path.abspath(__file__))

        if not (os.path.isdir(working_dir + "/installed_flows")):
            os.makedirs(working_dir + "/installed_flows")

        filename = working_dir + "/installed_flows/flows.txt"
        # if not os.path.exists(filename):
        f = file(filename, "a+")
        f.write("%s,%s" % (switch_id, port) + "\n")
        f.close()

    def return_path_if_path_exists(self, switch_id):

        working_dir = os.path.dirname(os.path.abspath(__file__))
        filename = working_dir + "/installed_flows/flows.txt"
        lines = open(filename, 'r').readlines()

        for line in lines:
            splittedline = line.split(",")
            dst_switch = splittedline[0]
            dst_port = splittedline[1].strip("\n")
            if (dst_switch != switch_id):
                route = self.route_resolution.get_routing_path_between_two_endpoints(switch_id, dst_switch)
                if (len(route) > 0):
                    return route, dst_switch, dst_port
        return [], '', ''

    def send_route_to_ctrl(self, src_switch, src_switch_port, dst_switch, dst_switch_port, route):
        route_with_ports = self.route_resolution.compute_the_route_with_ports(src_switch, src_switch_port, dst_switch, \
                                                                              dst_switch_port, route)
        data_dict = dict()
        data_dict["route"] = {}
        for indx, switch in enumerate(route_with_ports):
            switchid = switch.split(":")[-1]
            switchid = int(switchid, 16)
            data_dict["route"].update({"switch" + str(indx): switchid})
            data_dict["route"].update({"port" + str(indx): '%s-%s' % (
            route_with_ports[switch]["in_port"], route_with_ports[switch]["out_port"])})

        self.controller.send_route_to_ctrl(src_switch=src_switch,
                                           src_switch_port=src_switch_port,
                                           data=json.dumps(data_dict))
