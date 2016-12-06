__author__ = "Luiza Nacshon"
__copyright__ = ""
__license__ = ""
__version__ = "1.0.0"
__email__ = "luiza.n@quali.com"
__status__ = "Development"



from requests.auth import HTTPBasicAuth
import inject
import os
import shutil
from cloudshell.networking.sdn.configuration.cloudshell_controller_configuration import CONTROLLER_HANDLER
from cloudshell.core.logger.qs_logger import get_qs_logger
from cloudshell.networking.sdn.resolution.topology_resolution import SDNTopologyResolution
import json
import requests
Logger = get_qs_logger()
class InstallStaticFlows(object):

    def __init__(self, controller_handler=None, logger=None):

        self._controller = controller_handler
        self._logger = Logger
        self.route_resolution = SDNTopologyResolution(self._controller,self._logger)
        self.initialize_folder()



    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = Logger
            except:
                raise Exception('SDNRoutingResolution', 'Logger is none or empty')
        return self._logger

    @property
    def controller(self):
        if self._controller is None:
            try:
                self._controller = inject.instance(CONTROLLER_HANDLER)
            except:
                raise Exception('SDNAutoload', 'controller handler is none or empty')
        return self._controller


    def initialize_folder(self):
        working_dir = os.path.dirname(os.path.abspath(__file__))
        if (os.path.isdir(working_dir + "/installed_flows")):

            shutil.rmtree(working_dir + "/installed_flows")
            os.makedirs(working_dir + "/installed_flows")
        else:
            os.makedirs(working_dir + "/installed_flows")

    def build_flow(self,nodeid, flowname, ethertype='', destip='',srcip='', ipcos='', ipprot='',
                   dst_port=None, outdstmac=None, vlan='', src_port=None,actions_list=list(),priority=500):
        newflow = dict()

        newflow['name'] = flowname
        newflow['installInHw'] = 'true'
        newflow['node'] = {u'id': nodeid, u'type': u'OF'}
        if (destip != ''): newflow['nwDst'] = destip
        if (srcip!=''): newflow['nwSrc'] = srcip
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
        if(dst_port) : actions_list.append('OUTPUT=%s'%str(dst_port))
        #if (outdstmac): actions_list.append('SET_DL_DST=%s'%str(outdstmac))
        newflow['actions'] = actions_list

        return newflow




    def static_flow_pusher(self,flow_name, switch_id,port):

        self.logger.info('*'*10)
        self.logger.info('Start Pushing Static Flows')

        new_flow = self.build_flow(nodeid=switch_id, flowname=flow_name,src_port=port, ethertype="0x800",
                    outdstmac='',actions_list=["CONTROLLER"],priority=650)
        self.logger.info('{0},\t\t{1},\t\t{2}'.format(switch_id, flow_name,
                                                              port))

        response = self.controller.push_static_flow(switch_id,flow_name,new_flow)
        self.save_installed_flow_into_file(switch_id,port)
        route,dst_switch,dst_port = self.return_path_if_path_exists(switch_id)
        if (len(route)>0):
            self.send_route_to_ctrl(switch_id,port,dst_switch,dst_port,route)
        if(dst_switch!=''):
            switch_id = dst_switch
            port = dst_port
            route, dst_switch, dst_port = self.return_path_if_path_exists(switch_id)
            if (len(route) > 0):
                self.send_route_to_ctrl(switch_id,port,dst_switch,dst_port,route)
        return response

    def save_installed_flow_into_file(self,switch_id,port):

            working_dir = os.path.dirname(os.path.abspath(__file__))
            if (os.path.isdir(working_dir + "/installed_flows")):
                filename= working_dir + "/installed_flows/flows.txt"
                #if not os.path.exists(filename):
                f = file(filename, "a+")
                f.write("%s,%s"%(switch_id,port) + "\n")
                f.close()


    def return_path_if_path_exists(self,switch_id):

        working_dir = os.path.dirname(os.path.abspath(__file__))
        filename = working_dir + "/installed_flows/flows.txt"
        lines = open(filename, 'r').readlines()

        for line in lines:
            splittedline = line.split(",")
            dst_switch = splittedline[0]
            dst_port = splittedline[1].strip("\n")
            if(dst_switch!=switch_id):
                route = self.route_resolution.get_routing_path_between_two_endpoints(switch_id,dst_switch)
                if (len(route)>0):
                   return route,dst_switch,dst_port
        return [],'',''

    def send_route_to_ctrl(self,src_switch,src_switch_port,dst_switch,dst_switch_port,route):
        route_with_ports = self.route_resolution.compute_the_route_with_ports(src_switch,src_switch_port,dst_switch, \
                                                                              dst_switch_port,route)
        data_dict = dict()
        data_dict["route"] = {}
        for indx,switch in enumerate(route_with_ports):
            switchid = switch.split(":")[-1]
            switchid = int(switchid,16)
            data_dict["route"].update({"switch" + str(indx): switchid})
            data_dict["route"].update({"port" + str(indx): '%s-%s'%(route_with_ports[switch]["in_port"],route_with_ports[switch]["out_port"])})
        data = json.dumps(data_dict)
        _base_url = "http://192.168.42.173:8080/controller/nb/v2/myroutes/shellroute/sourcenode/%s/sourceport/%s/%s" % (
            src_switch,src_switch_port,data)
        response = requests.get(url=_base_url, headers={'Content-Type': 'application/json'},
                                auth=HTTPBasicAuth('admin', 'admin'))

if __name__=="__main__":
    from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController
    CONTROLLER_INIT_PARAMS = {'ip': '192.168.42.173',
                              'port': '8080',
                              'username': 'admin',
                              'password': 'admin',
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

    c_h = create_controller_handler()
    c = InstallStaticFlows(controller_handler=c_h)
    #res=c.route_resolution.compute_the_route_with_ports("00:00:00:00:00:00:00:02",1,"00:00:00:00:00:00:00:03", 2\
    #                                                    ,["00:00:00:00:00:00:00:03","00:00:00:00:00:00:00:01","00:00:00:00:00:00:00:02"])
    #print res
    c.static_flow_pusher("flo11", "00:00:00:00:00:00:00:02",1)
    c.static_flow_pusher("flo111", "00:00:00:00:00:00:00:03", 2)
    #c.save_installed_flow_into_file("00:00:00:00:00:00:00:01","10.0.0.1","10.0.0.22")
    #c.save_installed_flow_into_file("00:00:00:00:00:00:00:07", "10.0.0.1", "10.0.0.22")
    #r =  c.return_path_if_path_exists("00:00:00:00:00:00:00:07", "10.0.0.1", "10.0.0.22")
    #print r
    #c.static_flow_pusher("flo11", "00:00:00:00:00:00:00:02","00:00:00:00:00:00:01",3,'',"10.0.0.1","10.0.0.2","0x800",["CONTROLLER"],650)
    #c.static_flow_pusher("flo2221", "00:00:00:00:00:00:00:02", "00:00:00:00:00:00:02", '', '', '', '',"0x800", ["DROP"], 500)

    import json
    data = json.dumps({"input": "12"})
    _base_url = "http://192.168.42.173:8080/controller/nb/v2/myroutes/shellroute/sourcenode/1/sourceport/1/%s"%(data)


    import requests
    #
    from requests.auth import HTTPBasicAuth
    flow_data=c.build_flow(nodeid="00:00:00:00:00:00:00:02", flowname="foo",src_port=1, dst_port=1, ethertype="03993",
                              destip="111",srcip="111", outdstmac='',actions_list=["uuu"],priority=200)
    response = requests.get(url=_base_url, headers={'Content-Type': 'application/json'},auth=HTTPBasicAuth('admin','admin'))
    print response.content
    if response.status_code == 400:
        raise Exception('controller connection handler', 'query response is empty')



