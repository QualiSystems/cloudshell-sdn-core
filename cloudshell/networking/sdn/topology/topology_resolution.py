import json
import networkx as nx

import inject
from cloudshell.networking.sdn.configuration.cloudshell_controller_binding_keys import CONTROLLER_HANDLER

class SDNTopologyResolution(object):

    def __init__(self, controller_handler=None, logger=None):

        self._controller = controller_handler
        self.switches_list = []
        self.graph = None
        self.diGraph = None
        self.edges = None
        self.topology = None
        self.switches_ports = dict()


    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = inject.instance('logger')
            except:
                raise Exception('SDNRoutingResolution', 'Logger is none or empty')
        return self._logger


    @property
    def controller(self):
        if self._controller is None:
            try:

                self._controller = inject.instance(CONTROLLER_HANDLER)
            except:
                raise Exception('SDNRoutingResolution', 'controller handler is none or empty')
        return self._controller

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
        return self.lowest_centrality(nx.betweenness_centrality(self.graph, endpoints=True))


    def lowest_centrality(self,centrality_dict):
        cent_items = [(b, a) for (a, b) in centrality_dict.iteritems() if b == min(centrality_dict.values())]
        cent_items.sort()
        return tuple((cent_items))


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



if __name__=="__main__":
    from cloudshell.networking.sdn.controller.controller_connection_handler import SDNController
    CONTROLLER_INIT_PARAMS = {'ip': '192.168.42.203',
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
    c.get_switches_ports()
    print c.switches_ports









