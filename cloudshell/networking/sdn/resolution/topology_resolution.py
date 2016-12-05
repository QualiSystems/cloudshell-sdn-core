__author__ = "Luiza Nacshon"
__copyright__ = ""
__license__ = ""
__version__ = "1.0.0"
__email__ = "luiza.n@quali.com"
__status__ = "Development"



import networkx as nx

import inject

class SDNTopologyResolution(object):

    def __init__(self, controller_handler=None, logger=None):

        self.controller = controller_handler
        self.switches_list = []
        self.graph = None
        self.diGraph = None
        self.edges = None
        self.topology = None
        self.switches_ports = dict()
        self.connected_edges = dict()
        self.leaf_switches_list = []
        self.in_out_ports = dict()

        self.build_graph()


    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = inject.instance('logger')
            except:
                raise Exception('SDNRoutingResolution', 'Logger is none or empty')
        return self._logger


    def build_graph(self):
        self.graph = nx.Graph()
        self.diGraph = nx.DiGraph()

        self.get_topology()
        self.get_switches()
        self.get_edges()

        self.get_leaf_switches()

        nodeProperties = self.switches_list
        nodes = nodeProperties['nodeProperties']

        for node in nodes:
            self.graph.add_node(node['node']['id'])
            self.diGraph.add_node(node['node']['id'])
        self.build_edges_structure()

    def get_topology(self):
        self.topology = self.controller.get_query('topology', '')

    def get_switches(self):
        self.switches_list = self.controller.get_query('switchmanager', '/nodes')

    def get_edges(self):
        edgeProperties = self.topology
        self.edges = edgeProperties['edgeProperties']

        for edge in self.edges:
            e = (edge['edge']['headNodeConnector']['node']['id'], edge['edge']['tailNodeConnector']['node']['id'])
            self.graph.add_edge(*e)
            self.diGraph.add_edge(*e)

    def get_leaf_switches(self):
        leaf_switches_tuple = self.lowest_centrality(nx.betweenness_centrality(self.graph, endpoints=True))
        map(lambda x: self.leaf_switches_list.append(x[1]) if x[1] not in self.leaf_switches_list else False, leaf_switches_tuple)
        return self.leaf_switches_list



    def lowest_centrality(self,centrality_dict):
        cent_items = [(b, a) for (a, b) in centrality_dict.iteritems() if b == min(centrality_dict.values())]
        cent_items.sort()
        return cent_items



    def get_routing_path_between_two_endpoints(self,srcNode,dstNode):
        path = nx.dijkstra_path(self.graph, srcNode, dstNode)
        return path


    def get_switches_ports(self):
        for edge in self.edges:
            headedge_id = edge['edge']['headNodeConnector']['node']['id']
            tailedge_id = edge['edge']['tailNodeConnector']['node']['id']
            if(self.switches_ports.get(headedge_id)==None):
                self.switches_ports[headedge_id] = {}
            self.switches_ports[headedge_id][edge['properties']['name']['value']] = {'bandwidth':edge['properties']['bandwidth']['value']}
            if(self.switches_ports.get(tailedge_id)==None):
                self.switches_ports[tailedge_id] = {}
            self.switches_ports[tailedge_id][edge['properties']['name']['value']] = {'bandwidth':edge['properties']['bandwidth']['value']}
        return self.switches_ports


    def build_edges_structure(self):
        for edge in self.edges:
            headedge_id = edge['edge']['headNodeConnector']['node']['id']
            tailedge_id = edge['edge']['tailNodeConnector']['node']['id']
            if not (self.connected_edges.get(headedge_id)):
                self.connected_edges[headedge_id]={}
            self.connected_edges[headedge_id].update({tailedge_id:{"out_port":edge['edge']['headNodeConnector']['id'], \
                                                 "in_port":edge['edge']['tailNodeConnector']['id']}})


    def build_ports(self):

        for edge in self.edges:
            headedge_id = edge['edge']['headNodeConnector']['node']['id']
            tailedge_id = edge['edge']['tailNodeConnector']['node']['id']
            self.in_out_ports[headedge_id + "-" + tailedge_id] = edge['edge']['headNodeConnector']['id']




    def compute_the_route_with_ports(self,src_switch,src_switch_port,dst_switch,dst_switch_port,route):
        json_dict = dict()
        self.build_ports()

        route_len = len(route)
        head_to_tail=''

        for indx,switch in enumerate(route):
            if (self.connected_edges.get(switch)):
                for tailswitch in self.connected_edges[switch]:
                    if(indx+1<route_len):
                        if (tailswitch == route[indx + 1]):
                            if(indx!=0):
                                head_to_tail = route[indx-1] + "-"+ switch

                            if(src_switch==switch):

                                json_dict.update({switch:{"in_port":src_switch_port,"out_port": \
                                    self.connected_edges[switch][tailswitch]['out_port']}})

                            else:
                                json_dict.update({switch:{"in_port":self.in_out_ports[head_to_tail],"out_port": \
                                        self.connected_edges[switch][tailswitch]['out_port']}})
                    else:
                        if(dst_switch == switch):
                            json_dict.update({switch: {"in_port": self.in_out_ports[head_to_tail], "out_port": \
                                dst_switch_port}})
        return json_dict


    def return_route_with_ports(self,src_switch,src_switch_port,dst_switch,dst_switch_port,route):
        path = self.get_routing_path_between_two_endpoints(src_switch,dst_switch)
        path_with_ports = self.compute_the_route_with_ports(src_switch,src_switch_port,dst_switch,dst_switch_port,route)
        return path_with_ports



import random
def uniqueid():
    seed = random.getrandbits(32)
    while True:
       yield seed
       seed += 1

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
    c = SDNTopologyResolution(controller_handler=c_h)
    c.build_graph()
    print c.edges
    path = c.get_routing_path_between_two_endpoints("00:00:00:00:00:00:00:03", "00:00:00:00:00:00:00:02")
    ret = c.compute_the_route_with_ports("00:00:00:00:00:00:00:03",2,"00:00:00:00:00:00:00:02",1,path)
    print ret
    c.get_switches_ports()
    print c.switches_ports
    print c.get_leaf_switches()
    resource_id = dict()
    relative_path = dict()
    unique_sequence = uniqueid()
    for index,switch in enumerate(c.leaf_switches_list, start=1):
        resource_id[switch] = int(next(unique_sequence))
        relative_path[switch] = 0

    for dedicated_switch in c.switches_ports:
        for index,port in enumerate(c.switches_ports[dedicated_switch],start=1):
            resource_id[port] = int(next(unique_sequence))
            if resource_id.get(dedicated_switch) is not None:
                relative_path[port] = resource_id.get(dedicated_switch)









